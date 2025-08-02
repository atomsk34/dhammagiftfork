#!/usr/bin/env python3
import os
import json
import re
from bs4 import BeautifulSoup, NavigableString
from collections import defaultdict

# Конфигурация (проверьте эти пути!)
SC_DATA_ROOT = "/var/www/html/suttacentral.net/sc-data/sc_bilara_data/root/pli/ms/sutta"
TBW_DATA_ROOT = "/var/www/offline-data/theBuddhasWords"
OUTPUT_DIR = "/var/www/offline-data/tbw2json/workdir/output"

def process_text(tag_list):
    """Очистка и обработка текста"""
    if not tag_list:
        return ""
    
    soup = BeautifulSoup("".join(str(tag) for tag in tag_list), 'html.parser')
    
    # Удаление ненужных элементов
    for cls in ['parno', 'note', 'add', 'pts_pn']:
        for el in soup.find_all(class_=cls):
            el.decompose()
    
    text = soup.get_text('\n')
    return '\n'.join(line.strip() for line in text.split('\n') if line.strip())

def get_sc_structure():
    """Получение структуры SuttaCentral"""
    sc_files = defaultdict(list)
    
    for root, _, files in os.walk(SC_DATA_ROOT):
        for file in files:
            if file.endswith("_root-pli-ms.json"):
                parts = file.split('_')[0].split('.')
                if len(parts) >= 2:
                    nikaya = parts[0]
                    sc_files[nikaya].append(parts[1])
    
    return sc_files

def get_tbw_files():
    """Получение всех файлов TBW с их номерами"""
    tbw_files = defaultdict(dict)
    
    for nikaya in os.listdir(TBW_DATA_ROOT):
        nikaya_dir = os.path.join(TBW_DATA_ROOT, nikaya)
        if os.path.isdir(nikaya_dir):
            for file in os.listdir(nikaya_dir):
                if file.endswith('.html'):
                    # Извлекаем номер из имени файла
                    match = re.search(r'\.(\d+)(?:-(\d+))?\.', file)
                    if match:
                        start = int(match.group(1))
                        end = int(match.group(2)) if match.group(2) else start
                        tbw_files[nikaya][(start, end)] = file
    
    return tbw_files

def find_matching_tbw(nikaya, sc_range, tbw_files):
    """Поиск файлов TBW, соответствующих диапазону SC"""
    # Парсим диапазон SC
    sc_parts = re.split(r'[-_]', sc_range)
    sc_start = int(sc_parts[0]) if sc_parts[0].isdigit() else 0
    sc_end = int(sc_parts[1]) if len(sc_parts) > 1 and sc_parts[1].isdigit() else sc_start
    
    matches = []
    
    # Проверяем все файлы TBW для этой никаи
    for (tbw_start, tbw_end), filename in tbw_files.get(nikaya, {}).items():
        # Проверяем пересечение диапазонов
        if not (tbw_end < sc_start or tbw_start > sc_end):
            matches.append((filename, max(tbw_start, sc_start), min(tbw_end, sc_end)))
    
    return matches

def process_html_file(filepath):
    """Обработка одного HTML-файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        content = soup.find('div', id='content')
        if not content:
            return None, None, None
        
        en = content.find('div', lang='en')
        pi = content.find('div', lang='pi')
        
        if not en or not pi:
            return None, None, None
        
        # Обработка текста
        pi_text = process_text(list(pi.children))
        en_text = process_text(list(en.children))
        
        return pi_text, en_text, "<div>{}</div>"
    
    except Exception as e:
        print(f"Ошибка обработки {filepath}: {e}")
        return None, None, None

def process_nikaya_range(nikaya, sc_range, tbw_files):
    """Обработка одного диапазона SC"""
    matches = find_matching_tbw(nikaya, sc_range, tbw_files)
    if not matches:
        print(f"  Нет файлов TBW для {nikaya}.{sc_range}")
        return None, None, None
    
    pi_parts = []
    en_parts = []
    html_parts = []
    
    for filename, start, end in matches:
        filepath = os.path.join(TBW_DATA_ROOT, nikaya, filename)
        pi_text, en_text, html = process_html_file(filepath)
        
        if pi_text and en_text:
            pi_parts.append(pi_text)
            en_parts.append(en_text)
            html_parts.append(html)
    
    if not pi_parts:
        return None, None, None
    
    # Формируем данные в формате SC
    sc_key = f"{nikaya}.{sc_range}:1.1"
    return (
        {sc_key: "\n\n".join(pi_parts)},
        {sc_key: "\n\n".join(en_parts)},
        {sc_key: "\n".join(html_parts)}
    )

def save_results(nikaya, sc_range, pi_data, en_data, html_data):
    """Сохранение результатов"""
    if not pi_data or not en_data or not html_data:
        return
    
    os.makedirs(os.path.join(OUTPUT_DIR, nikaya), exist_ok=True)
    
    base_name = os.path.join(OUTPUT_DIR, nikaya, f"{nikaya}.{sc_range}")
    
    with open(f"{base_name}_root-pli-ms.json", 'w', encoding='utf-8') as f:
        json.dump(pi_data, f, ensure_ascii=False, indent=2)
    
    with open(f"{base_name}_translation-en-bodhi.json", 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)
    
    with open(f"{base_name}_html.json", 'w', encoding='utf-8') as f:
        json.dump(html_data, f, ensure_ascii=False, indent=2)
    
    print(f"  Сохранено: {base_name}_*.json")

def main():
    print("Обработка TBW для SuttaCentral...")
    
    # Получаем структуры данных
    sc_ranges = get_sc_structure()
    tbw_files = get_tbw_files()
    
    # Обрабатываем каждый диапазон
    for nikaya, ranges in sc_ranges.items():
        print(f"\nНикая: {nikaya}")
        for sc_range in ranges:
            print(f"  Диапазон: {sc_range}")
            
            pi_data, en_data, html_data = process_nikaya_range(nikaya, sc_range, tbw_files)
            save_results(nikaya, sc_range, pi_data, en_data, html_data)
    
    print("\nГотово!")

if __name__ == "__main__":
    main()
