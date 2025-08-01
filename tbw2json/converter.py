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
    # Создаем копию, чтобы не изменять оригинальный объект soup
    tag_copy = BeautifulSoup(str(tag), 'html.parser')

    # Удаляем все спаны с примечаниями
    for note in tag_copy.find_all('span', class_='note'):
        note.decompose()
    # Удаляем все спаны с номерами параграфов
    for parno in tag_copy.find_all('span', class_='parno'):
        parno.decompose()

    # Получаем очищенный текст
    return tag_copy.get_text(strip=True)

def create_html_placeholder(tag):
    """
    Создает HTML-строку, в которой текстовое содержимое заменено на плейсхолдер '{}'.
    """
    # Создаем глубокую копию тега для манипуляций
    tag_copy = BeautifulSoup(str(tag), 'html.parser').find(tag.name)
    
    # Удаляем спан с номером параграфа, так как он не является частью структуры контента
    parno = tag_copy.find('span', class_='parno')
    if parno:
        parno.decompose()

    # Находим все текстовые узлы и заменяем их
    for child in tag_copy.find_all(text=True):
        if child.strip(): # Заменяем только непустые текстовые узлы
            child.replace_with('{}')
            
    # Возвращаем внешнюю HTML-структуру измененного тега
    return str(tag_copy)


def convert_sutta_html_to_json(html_filepath, output_dir="output"):
    """
    Анализирует HTML-файл сутты и преобразует его в три структурированных JSON-файла:
    1. Корневой текст на пали
    2. Текст перевода на английский
    3. HTML-структура с плейсхолдерами
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Обработка файла: {html_filepath}...")

    with open(html_filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # --- 1. Извлечение метаданных ---
    content_div = soup.select_one("#content")
    if not content_div:
        print(f"  [ОШИБКА] Не удалось найти div #content в файле {html_filepath}. Пропуск.")
        return

    # Извлекаем ID сутты (например, mn1, sn1.1)
    sutta_id = ""
    title_tag = content_div.find('h2') or content_div.find('h3')
    if title_tag and title_tag.text:
        # Используем регулярное выражение для поиска шаблонов типа SN1:1 или MN1
        match = re.match(r'([A-Z]+[0-9]+(?::\d+)?)', title_tag.get_text(strip=True))
        if match:
            sutta_id = match.group(1).lower().replace(':', '.')
    
    # Если ID не найден в заголовке, используем имя файла
    if not sutta_id:
        base_name = os.path.basename(html_filepath)
        sutta_id = os.path.splitext(base_name)[0]
        print(f"  [ПРЕДУПРЕЖДЕНИЕ] Не удалось найти ID сутты в заголовке. Используется имя файла: {sutta_id}")


    # Извлекаем информацию о переводчике
    translator = "sujato" # Значение по умолчанию
    translator_tag = soup.select_one("ul.translator li")
    if translator_tag and "bhikkhu bodhi" in translator_tag.text.lower():
        translator = "bodhi"
    elif translator_tag and "bhikkhu ñanamoli" in translator_tag.text.lower():
        translator = "nanomoli-bodhi"

    # --- 2. Инициализация структур данных ---
    pali_data = {}
    en_data = {}
    html_data = {}

    pali_content = content_div.select_one("div[lang='pi']")
    en_content = content_div.select_one("div[lang='en']")

    if not pali_content or not en_content:
        print(f"  [ОШИБКА] Не удалось найти div'ы с пали и английским текстом. Пропуск.")
        return

    # --- 3. Создаем карту параграфов на пали по их номерам ---
    pali_map_by_parno = {}
    pali_tags = pali_content.find_all(['p', 'h3', 'h4'], recursive=False)
    for tag in pali_tags:
        parno_span = tag.find('span', class_='parno')
        if parno_span:
            # Ключом является текст номера параграфа (например, '1', '2', '25')
            parno_key = parno_span.get_text(strip=True)
            pali_map_by_parno[parno_key] = tag

    # --- 4. Обрабатываем английский контент и создаем JSON-ключи ---
    chapter = 1
    section = 0
    
    en_tags = en_content.find_all(['p', 'h2', 'h3', 'h4'], recursive=False)

    for tag in en_tags:
        json_key = None
        parno_span = tag.find('span', class_='parno')
        
        if tag.name in ['h2']:
            # Новое крупное разделение сбрасывает счетчик глав
            match = re.search(r'\d+', tag.text)
            if match:
                chapter = int(match.group())
                section = 0
            continue # H2 не добавляется в JSON, используется только для нумерации

        if tag.name in ['h3', 'h4']:
            section += 1
            # Ключ для заголовка заканчивается на .0
            json_key = f"{sutta_id}:{chapter}.{section}.0"
            en_data[json_key] = tag.get_text(strip=True)
            # Заголовки могут отсутствовать в пали, поэтому мы их не сопоставляем
            pali_data[json_key] = "" 
            html_data[json_key] = f"<{tag.name}>{{}}</{tag.name}>"

        elif parno_span:
            parno_key = parno_span.get_text(strip=True)
            
            # Обрабатываем диапазоны стихов типа '1-3', беря первое число
            main_parno = re.match(r'(\d+)', parno_key)
            if main_parno:
                segment_num = int(main_parno.group(1))
                json_key = f"{sutta_id}:{chapter}.{section}.{segment_num}"

                # Добавляем данные в словари
                en_data[json_key] = clean_text_for_json(tag)
                html_data[json_key] = create_html_placeholder(tag)

                # Ищем соответствующий текст на пали в карте
                if parno_key in pali_map_by_parno:
                    pali_tag = pali_map_by_parno[parno_key]
                    pali_data[json_key] = clean_text_for_json(pali_tag)
                else:
                    pali_data[json_key] = "" # Соответствующий пали текст не найден

    # --- 5. Записываем JSON-файлы ---
    pali_filename = os.path.join(output_dir, f"{sutta_id}_root-pli-ms.json")
    en_filename = os.path.join(output_dir, f"{sutta_id}_translation-en-{translator}.json")
    html_filename = os.path.join(output_dir, f"{sutta_id}_html.json")

    with open(pali_filename, 'w', encoding='utf-8') as f:
        json.dump(pali_data, f, ensure_ascii=False, indent=2)

    with open(en_filename, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)
        
    with open(html_filename, 'w', encoding='utf-8') as f:
        json.dump(html_data, f, ensure_ascii=False, indent=2)

    print(f"  Успешно создано 3 JSON-файла в папке '{output_dir}'.")


# --- АВТОМАТИЧЕСКИЙ ЗАПУСК ДЛЯ ВСЕХ HTML-ФАЙЛОВ В ПАПКЕ ---
if __name__ == "__main__":
    # Автоматически находим все файлы с расширением .html в текущей папке
    html_files = glob.glob('*.html')

    if not html_files:
        print("В этой папке не найдены файлы .html. Пожалуйста, поместите сюда ваши HTML-файлы.")
    else:
        print(f"Найдено {len(html_files)} .html файлов для обработки.")
        
        # Обрабатываем каждый найденный файл
        for filepath in html_files:
            convert_sutta_html_to_json(filepath)
    
    print("\nОбработка завершена.")
