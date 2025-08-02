# -*- coding: utf-8 -*-

import os
import json
import glob
from bs4 import BeautifulSoup

def process_text(tag):
    """Обрабатывает текст, сохраняя структуру"""
    if not tag:
        return ""
    
    # Создаем копию тега для безопасного изменения
    clean_tag = BeautifulSoup(str(tag), 'html.parser')
    
    # Удаляем примечания
    for note in clean_tag.find_all('span', class_='note'):
        note.decompose()
        
    # >>> НАЧАЛО ИЗМЕНЕНИЙ
    # Удаляем <span class="add">
    for item in clean_tag.find_all('span', class_='add'):
        item.decompose()
        
    # Удаляем <a class="pts_pn">
    for item in clean_tag.find_all('a', class_='pts_pn'):
        item.decompose()
    # <<< КОНЕЦ ИЗМЕНЕНИЙ
    
    # Получаем текст с сохранением переносов строк
    text = clean_tag.get_text('\n', strip=False)
    
    # Очищаем лишние пробелы, но сохраняем переносы строк
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    
    return text

def get_html_structure(tag):
    """Генерирует HTML-структуру с плейсхолдерами"""
    if not tag:
        return ""
    
    tag_copy = BeautifulSoup(str(tag), 'html.parser')
    
    # Заменяем текст на плейсхолдеры
    for text_node in tag_copy.find_all(text=True):
        if text_node.strip():
            text_node.replace_with('{}')
    
    # Удаляем примечания
    for note in tag_copy.find_all('span', class_='note'):
        note.decompose()

    # >>> НАЧАЛО ИЗМЕНЕНИЙ
    # Удаляем <span class="add">
    for item in tag_copy.find_all('span', class_='add'):
        item.decompose()
        
    # Удаляем <a class="pts_pn">
    for item in tag_copy.find_all('a', class_='pts_pn'):
        item.decompose()
    # <<< КОНЕЦ ИЗМЕНЕНИЙ
        
    return str(tag_copy)

def process_sutta(html_filepath, output_dir="output"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Обработка файла: {html_filepath}...")

    with open(html_filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    content_div = soup.select_one("#content")
    if not content_div:
        print("  [ОШИБКА] Не найден div #content")
        return

    sutta_id = os.path.splitext(os.path.basename(html_filepath))[0]

    # Инициализация данных
    pali_data = {}
    en_data = {}
    html_data = {}
    
    en_content = content_div.select_one("div[lang='en']")
    pali_content = content_div.select_one("div[lang='pi']")

    if not en_content or not pali_content:
        print("  [ОШИБКА] Не найден контент на английском или пали")
        return

    # Обрабатываем английский контент по блокам, разделенным <hr>
    en_blocks = []
    current_block = []
    
    for element in en_content.children:
        if element.name == 'hr':
            if current_block:
                en_blocks.append(current_block)
                current_block = []
        else:
            if element.name in ['p', 'div']:
                current_block.append(element)
    
    if current_block:
        en_blocks.append(current_block)

    # Обрабатываем палийский контент аналогично
    pali_blocks = []
    current_block = []
    
    for element in pali_content.children:
        if element.name == 'hr':
            if current_block:
                pali_blocks.append(current_block)
                current_block = []
        else:
            if element.name in ['p', 'div']:
                current_block.append(element)
    
    if current_block:
        pali_blocks.append(current_block)

    # Сопоставляем блоки
    for i, (en_block, pali_block) in enumerate(zip(en_blocks, pali_blocks), start=1):
        # Обрабатываем каждый абзац в блоке
        for j, (en_p, pali_p) in enumerate(zip(en_block, pali_block), start=1):
            key = f"{sutta_id}:{i}.{j}"
            
            # Обрабатываем текст
            en_data[key] = process_text(en_p)
            pali_data[key] = process_text(pali_p)
            
            # Генерируем HTML-структуру
            html_data[key] = get_html_structure(en_p)

    # Сохраняем файлы
    pali_filename = os.path.join(output_dir, f"{sutta_id}_root-pli-ms.json")
    en_filename = os.path.join(output_dir, f"{sutta_id}_translation-en-bodhi.json")
    html_filename = os.path.join(output_dir, f"{sutta_id}_html.json")

    with open(pali_filename, 'w', encoding='utf-8') as f:
        json.dump(pali_data, f, ensure_ascii=False, indent=2)

    with open(en_filename, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)
        
    with open(html_filename, 'w', encoding='utf-8') as f:
        json.dump(html_data, f, ensure_ascii=False, indent=2)

    print(f"  Файлы сохранены: {pali_filename}, {en_filename}, {html_filename}")

if __name__ == "__main__":
    html_files = glob.glob('*.html')
    
    if not html_files:
        print("HTML файлы не найдены в текущей директории.")
    else:
        print(f"Найдено {len(html_files)} HTML файлов для обработки.")
        for filepath in html_files:
            process_sutta(filepath)
        print("\nОбработка завершена.")
