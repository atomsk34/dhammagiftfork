# -*- coding: utf-8 -*-

import os
import json
import glob
from bs4 import BeautifulSoup

# Константы из JavaScript
SECTION_DIV_SELECTOR = ["hr", "hgroup", "h1", "h2", "h3", "h4", "h5", "h6", "div.glob"]
SECTION_DIV_HIDDEN_SELECTOR = ["hr"]
SPLICE_CLOSES = ["p", "blockquote", "div"]
SPLICE_OPENS = ["hgroup", "h1", "h2", "h3"]

def is_insignificant(element):
    """Определяет, является ли элемент незначительным для группировки"""
    if element.name != "p":
        return False
    
    text = element.get_text(strip=True)
    if len(text) < 80:
        return True
    if len(text) >= 200:
        return False
    
    sentence_enders = text.count('.') + text.count('!') + text.count('?') + text.count(':')
    return sentence_enders <= 1

def group_elements(elements):
    """Группирует элементы аналогично функции groupy в JavaScript"""
    out = []
    group = []
    
    for element in elements:
        if element.name in SPLICE_OPENS and any(e.name in SPLICE_CLOSES for e in group):
            if group:
                out.append(group)
                group = []
        
        group.append(element)
        
        if element.name in SPLICE_CLOSES and not is_insignificant(element):
            if group:
                out.append(group)
                group = []
    
    if group:
        out.append(group)
    
    return out

def array_split(elements, split_fn):
    """Разделяет массив на группы по условию, аналогично arraySplit в JavaScript"""
    out = []
    current = []
    
    for element in elements:
        if split_fn(element):
            if current:
                out.append(current)
                current = []
            out.append([element])
        else:
            current.append(element)
    
    if current:
        out.append(current)
    
    return out

def calculate_ratio(en_group, pi_group, en_lengths, pi_lengths, overall_ratio):
    """Вычисляет соотношение длин групп"""
    en_sum = sum(en_lengths[i] for i in en_group)
    pi_sum = sum(pi_lengths[i] for i in pi_group)
    
    if pi_sum == 0:
        return float('inf')
    
    return en_sum / (pi_sum * overall_ratio)

def get_text_length(element):
    """Вычисляет длину текста элемента, аналогично textLength в JavaScript"""
    if element.name in SECTION_DIV_SELECTOR:
        return 0.01
    
    # Создаем копию элемента для безопасного изменения
    element_copy = BeautifulSoup(str(element), 'html.parser')
    
    # Удаляем примечания
    for note in element_copy.find_all('span', class_='note'):
        note.decompose()
    
    # Удаляем дополнительные элементы
    for add in element_copy.find_all('span', class_='add'):
        add.decompose()
    for pts in element_copy.find_all('a', class_='pts_pn'):
        pts.decompose()
    
    return len(element_copy.get_text(strip=True))

def extraporlative_splice(en_elements, pi_elements):
    """Основная функция для сопоставления английских и палийских элементов"""
    if not en_elements and not pi_elements:
        return []
    
    # Вычисляем длины текста для каждого элемента
    en_lengths = [get_text_length(e) for e in en_elements]
    pi_lengths = [get_text_length(e) for e in pi_elements]
    
    en_remains = sum(en_lengths)
    pi_remains = sum(pi_lengths)
    overall_ratio = en_remains / pi_remains if pi_remains > 0 else 1
    
    en_index = 0
    pi_index = 0
    result = []
    
    while True:
        en_done = en_index >= len(en_elements)
        pi_done = pi_index >= len(pi_elements)
        
        if en_done or pi_done:
            if en_done and not pi_done:
                result.append(([], pi_elements[pi_index:]))
            elif pi_done and not en_done:
                result.append((en_elements[en_index:], []))
            break
        
        # Обновляем общее соотношение
        current_en_remains = sum(en_lengths[en_index:])
        current_pi_remains = sum(pi_lengths[pi_index:])
        overall_ratio = current_en_remains / current_pi_remains if current_pi_remains > 0 else 1
        
        # Инициализация групп
        en_group = []
        pi_group = []
        
        # Пропускаем разделители секций
        while en_index < len(en_elements) and en_elements[en_index].name in SECTION_DIV_SELECTOR:
            en_group.append(en_index)
            en_index += 1
        
        while pi_index < len(pi_elements) and pi_elements[pi_index].name in SECTION_DIV_SELECTOR:
            pi_group.append(pi_index)
            pi_index += 1
        
        if en_index >= len(en_elements) or pi_index >= len(pi_elements):
            continue
        
        # Добавляем первые элементы в группы
        en_group.append(en_index)
        en_index += 1
        
        pi_group.append(pi_index)
        pi_index += 1
        
        # Вычисляем начальное соотношение
        ratio = calculate_ratio(en_group, pi_group, en_lengths, pi_lengths, overall_ratio)
        best_quality = min(ratio, 1/ratio) if ratio > 0 else 0
        
        # Пока английский текст длиннее
        while ratio > 1:
            if pi_index >= len(pi_elements) or pi_elements[pi_index].name in SECTION_DIV_SELECTOR:
                break
            
            pi_group.append(pi_index)
            pi_index += 1
            new_ratio = calculate_ratio(en_group, pi_group, en_lengths, pi_lengths, overall_ratio)
            new_quality = min(new_ratio, 1/new_ratio) if new_ratio > 0 else 0
            
            if new_quality < best_quality:
                pi_group.pop()
                pi_index -= 1
                break
            else:
                best_quality = new_quality
                ratio = new_ratio
        
        # Пока палийский текст длиннее
        while ratio < 1:
            if en_index >= len(en_elements) or en_elements[en_index].name in SECTION_DIV_SELECTOR:
                break
            
            en_group.append(en_index)
            en_index += 1
            new_ratio = calculate_ratio(en_group, pi_group, en_lengths, pi_lengths, overall_ratio)
            new_quality = min(new_ratio, 1/new_ratio) if new_ratio > 0 else 0
            
            if new_quality < best_quality:
                en_group.pop()
                en_index -= 1
                break
            else:
                best_quality = new_quality
                ratio = new_ratio
        
        # Добавляем найденные группы в результат
        result_en = [en_elements[i] for i in en_group]
        result_pi = [pi_elements[i] for i in pi_group]
        result.append((result_en, result_pi))
    
    return result

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

    # Получаем все дочерние элементы
    en_elements = [e for e in en_content.children if e.name is not None]
    pi_elements = [e for e in pali_content.children if e.name is not None]

    # Разделяем на секции по SECTION_DIV_SELECTOR
    en_sections = array_split(en_elements, lambda e: e.name in SECTION_DIV_SELECTOR)
    pi_sections = array_split(pi_elements, lambda e: e.name in SECTION_DIV_SELECTOR)

    # Обрабатываем каждую секцию
    section_num = 0
    for i in range(max(len(en_sections), len(pi_sections))):
        section_num += 1
        en_section = en_sections[i] if i < len(en_sections) else []
        pi_section = pi_sections[i] if i < len(pi_sections) else []
        
        # Применяем основной алгоритм сопоставления
        pairs = extraporlative_splice(en_section, pi_section)
        
        # Обрабатываем каждую пару
        for pair_num, (en_group, pi_group) in enumerate(pairs, 1):
            for j, (en_p, pi_p) in enumerate(zip(en_group, pi_group), 1):
                key = f"{sutta_id}:{section_num}.{pair_num}.{j}"
                
                # Обрабатываем текст
                en_data[key] = process_text(en_p)
                pali_data[key] = process_text(pi_p)
                
                # Генерируем HTML-структуру
                html_data[key] = get_html_structure(en_p)
            
            # Обрабатываем оставшиеся элементы, если группы разной длины
            if len(en_group) > len(pi_group):
                for j in range(len(pi_group), len(en_group)):
                    key = f"{sutta_id}:{section_num}.{pair_num}.{j+1}"
                    en_data[key] = process_text(en_group[j])
                    pali_data[key] = ""
                    html_data[key] = get_html_structure(en_group[j])
            elif len(pi_group) > len(en_group):
                for j in range(len(en_group), len(pi_group)):
                    key = f"{sutta_id}:{section_num}.{pair_num}.{j+1}"
                    en_data[key] = ""
                    pali_data[key] = process_text(pi_group[j])
                    html_data[key] = ""

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
