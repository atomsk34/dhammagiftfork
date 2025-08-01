# -*- coding: utf-8 -*-

import os
import json
import re
import glob
from bs4 import BeautifulSoup, NavigableString

def clean_text_for_json(tag):
    """
    Очищает текстовое содержимое тега, удаляя спаны с примечаниями и номерами параграфов.
    """
    if not tag: return ""
    tag_copy = BeautifulSoup(str(tag), 'html.parser')
    for note in tag_copy.find_all('span', class_='note'):
        note.decompose()
    for parno in tag_copy.find_all('span', class_='parno'):
        parno.decompose()
    return tag_copy.get_text(strip=True)

def create_html_placeholder(tag):
    """
    Создает HTML-строку, в которой текстовое содержимое заменено на плейсхолдер '{}'.
    """
    if not tag: return ""
    tag_copy = BeautifulSoup(str(tag), 'html.parser').find(tag.name, recursive=False)
    if not tag_copy: return str(tag)
    
    parno = tag_copy.find('span', class_='parno')
    if parno:
        parno.decompose()
        
    text_nodes = tag_copy.find_all(text=True, recursive=True)
    for child in text_nodes:
        if child.strip() and not isinstance(child, NavigableString) and child.parent.name not in ['style', 'script']:
             child.replace_with('{}')
            
    return str(tag_copy)


def get_translator_code(text):
    """
    Определяет стандартизированный код переводчика из текста с указанием авторства.
    """
    text_lower = text.lower()
    if "ñanamoli" in text_lower and "bodhi" in text_lower:
        return "nanomoli-bodhi"
    elif "bodhi" in text_lower:
        return "bodhi"
    elif "sujato" in text_lower:
        return "sujato-walton"
    elif "thanissaro" in text_lower:
        return "thanissaro"
    elif "walshe" in text_lower:
        return "walshe"
    elif "ānandajoti" in text_lower:
        return "anandajoti"
    elif "buddharakkhita" in text_lower:
        return "buddharakkhita"
    elif "kelly" in text_lower and "sawyer" in text_lower:
        return "kelly-sawyer-yareham"
    else:
        return "unknown"

def get_content_blocks(content_div):
    """
    Группирует теги в блоки. Блок начинается с тега с номером 'parno'.
    """
    blocks = {}
    current_block_key = None
    # Добавляем h2 в запрос, чтобы правильно обрабатывать файлы с несколькими суттами
    content_tags_query = ['p', 'h2', 'h3', 'h4', 'blockquote', 'hr']
    
    if not content_div:
        return blocks
        
    for tag in content_div.find_all(content_tags_query, recursive=False):
        if tag.name == 'hr':
            continue
            
        parno_span = tag.find('span', class_='parno')
        if parno_span:
            current_block_key = parno_span.get_text(strip=True)
            if current_block_key not in blocks:
                blocks[current_block_key] = []
            blocks[current_block_key].append(tag)
        elif current_block_key:
            blocks[current_block_key].append(tag)
    return blocks

def convert_sutta_html_to_json(html_filepath, output_dir="output"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Обработка файла: {html_filepath}...")

    with open(html_filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    content_div = soup.select_one("#content")
    if not content_div:
        print(f"  [ОШИБКА] Не удалось найти #content в {html_filepath}. Пропуск.")
        return

    sutta_id = ""
    title_tag = content_div.find('h2') or content_div.find('h3')
    if title_tag and title_tag.text:
        match = re.match(r'([a-zA-Z]+[0-9]+[:.]\d+)', title_tag.get_text(strip=True))
        if match:
            sutta_id = match.group(1).lower().replace(':', '.')
    
    if not sutta_id and title_tag and title_tag.text:
         match = re.match(r'([a-zA-Z]+[0-9]+)', title_tag.get_text(strip=True))
         if match:
            sutta_id = match.group(1).lower()

    if not sutta_id:
        base_name = os.path.basename(html_filepath)
        sutta_id = os.path.splitext(base_name)[0]
        print(f"  [ПРЕДУПРЕЖДЕНИЕ] ID сутты не найден в заголовке. Используется имя файла: {sutta_id}")
    
    translator_code = "unknown"
    translator_tag = soup.select_one("ul.translator li")
    if translator_tag:
        translator_code = get_translator_code(translator_tag.text)

    pali_data = {}
    en_data = {}
    html_data = {}

    # --- ИСПРАВЛЕННАЯ ЛОГИКА ПОИСКА КОНТЕНТА ---
    # Ищем языковые блоки в любом месте внутри #content
    en_content_div = soup.select_one("#content div[lang='en']")
    pali_content_div = soup.select_one("#content div[lang='pi']")

    # Проверяем, найдены ли блоки, прежде чем продолжить
    if not en_content_div or not pali_content_div:
        print(f"  [ПРЕДУПРЕЖДЕНИЕ] Не найдены контентные блоки (div lang='en/pi') в файле {html_filepath}. Файлы не созданы.")
        return
    # ---------------------------------------------

    en_blocks = get_content_blocks(en_content_div)
    pali_blocks = get_content_blocks(pali_content_div)
    
    for parno, en_tag_list in en_blocks.items():
        clean_parno = parno.replace('v', '')
        if parno in pali_blocks:
            pali_tag_list = pali_blocks[parno]
            for i in range(len(en_tag_list)):
                json_key = f"{sutta_id}:{clean_parno}.{i+1}"
                en_tag = en_tag_list[i]
                pali_tag = pali_tag_list[i] if i < len(pali_tag_list) else None

                en_data[json_key] = clean_text_for_json(en_tag)
                html_data[json_key] = create_html_placeholder(en_tag)
                pali_data[json_key] = clean_text_for_json(pali_tag)

    if not (pali_data or en_data or html_data):
        print(f"  [ПРЕДУПРЕЖДЕНИЕ] Не найдено контента для обработки в {html_filepath}. Файлы не созданы.")
        return

    pali_filename = os.path.join(output_dir, f"{sutta_id}_root-pli-ms.json")
    en_filename = os.path.join(output_dir, f"{sutta_id}_translation-en-{translator_code}.json")
    html_filename = os.path.join(output_dir, f"{sutta_id}_html.json")

    with open(pali_filename, 'w', encoding='utf-8') as f:
        json.dump(pali_data, f, ensure_ascii=False, indent=2, sort_keys=True)
    with open(en_filename, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2, sort_keys=True)
    with open(html_filename, 'w', encoding='utf-8') as f:
        json.dump(html_data, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"  Успешно создано 3 JSON-файла для {sutta_id} в папке '{output_dir}'.")

if __name__ == "__main__":
    html_files = glob.glob('*.html')
    if not html_files:
        print("В этой папке не найдены файлы .html.")
    else:
        print(f"Найдено {len(html_files)} .html файлов для обработки.")
        for filepath in html_files:
            try:
                convert_sutta_html_to_json(filepath)
            except Exception as e:
                print(f"  [КРИТИЧЕСКАЯ ОШИБКА] При обработке файла {filepath} произошла ошибка: {e}")
    print("\nОбработка завершена.")
