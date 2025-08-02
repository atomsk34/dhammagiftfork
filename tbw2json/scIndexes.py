import json
import os
import re

def load_tbw_master_list(filepath):
    """
    Загружает полный, упорядоченный список идентификаторов tbw из файла.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.read().splitlines() if line and not line.startswith('.')]
    except FileNotFoundError:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Файл с мастер-списком ID не найден: {filepath}")
        return None

def get_ids_in_range(start_id, end_id, master_list):
    """
    Возвращает все ID из мастер-списка между start_id и end_id.
    """
    try:
        start_index = master_list.index(start_id)
        end_index = -1
        
        for i, item in enumerate(master_list):
            if i >= start_index:
                if item == end_id or end_id in item.split('-'):
                    end_index = i
                    break
        
        if end_index == -1:
            return [start_id]

        return master_list[start_index : end_index + 1]
    except ValueError:
        print(f"  - Предупреждение: Начальный ID '{start_id}' не найден в мастер-списке.")
        return []

def process_merge(mapping, master_tbw_ids, source_path, output_dir):
    """
    Основная функция для обработки карты слияния.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_types = ['root-pli-ms', 'translation-en-bodhi', 'html']

    for row in mapping:
        sc_id, start_tbw, end_tbw = row['sc'], row['tbw'], row['tbw_till_file']
        
        if not end_tbw:
            end_tbw = start_tbw

        print(f"\n[+] Обработка SC ID: {sc_id}")
        
        tbw_ids_to_merge = get_ids_in_range(start_tbw, end_tbw, master_tbw_ids)
        
        if not tbw_ids_to_merge:
            print(f"  - ПРОПУСК: не удалось сформировать диапазон для {sc_id}.")
            continue

        print(f"  - Диапазон для объединения: с {tbw_ids_to_merge[0]} по {tbw_ids_to_merge[-1]}")

        for f_type in file_types:
            merged_data = {}
            for tbw_id in tbw_ids_to_merge:
                
                # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
                # Упрощенная логика поиска файла. Теперь ищет в одной папке.
                file_path = os.path.join(source_path, f"{tbw_id}_{f_type}.json")
                
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                            merged_data.update(data)
                        except json.JSONDecodeError:
                            print(f"  - ОШИБКА: не удалось прочитать JSON из {file_path}")
            
            if merged_data:
                output_path = os.path.join(output_dir, f"{sc_id}_{f_type}.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(merged_data, f, ensure_ascii=False, indent=2)
                print(f"  - Сохранен: {output_path}")

# --- НАСТРОЙКИ И ЗАПУСК ---
if __name__ == "__main__":
    # 1. Укажите путь к файлу с полным списком ID.
    MASTER_ID_LIST_FILE = 'antbwID.txt'
    
    # 2. Укажите путь к ПАПКЕ, где лежат ВСЕ исходные JSON файлы.
    # Например, если файлы в 'an/an1/', укажите этот путь.
    SOURCE_JSON_PATH = './'  # ИЗМЕНИТЕ ЭТОТ ПУТЬ
    
    # 3. Папка для сохранения результатов.
    OUTPUT_DIR = 'merged_output'

    # 4. Вставьте сюда вашу карту сопоставления.
    mapping_table = [
        {'sc': 'an1.1-10', 'tbw': 'an1.1', 'tbw_till_file': 'an1.10'},
        {'sc': 'an1.11-20', 'tbw': 'an1.11', 'tbw_till_file': 'an1.20'},
        {'sc': 'an1.21-30', 'tbw': 'an1.21', 'tbw_till_file': 'an1.30'},
        {'sc': 'an1.31-40', 'tbw': 'an1.31', 'tbw_till_file': 'an1.40'},
        {'sc': 'an1.41-50', 'tbw': 'an1.41', 'tbw_till_file': 'an1.50'},
        {'sc': 'an1.51-60', 'tbw': 'an1.51', 'tbw_till_file': 'an1.60'},
        {'sc': 'an1.61-70', 'tbw': 'an1.61', 'tbw_till_file': 'an1.70'},
        {'sc': 'an1.71-81', 'tbw': 'an1.71', 'tbw_till_file': 'an1.81'},
        {'sc': 'an1.82-97', 'tbw': 'an1.82', 'tbw_till_file': 'an1.84-97'},
        {'sc': 'an1.98-139', 'tbw': 'an1.98', 'tbw_till_file': 'an1.131-139'},
        {'sc': 'an1.140-149', 'tbw': 'an1.140', 'tbw_till_file': 'an1.141-149'},
        {'sc': 'an1.150-169', 'tbw': 'an1.150', 'tbw_till_file': 'an1.161-169'},
        {'sc': 'an1.170-187', 'tbw': 'an1.170', 'tbw_till_file': 'an1.187'},
        {'sc': 'an1.188-197', 'tbw': 'an1.188-197', 'tbw_till_file': ''},
        {'sc': 'an1.198-208', 'tbw': 'an1.198-208', 'tbw_till_file': ''},
        {'sc': 'an1.209-218', 'tbw': 'an1.209-218', 'tbw_till_file': ''},
        {'sc': 'an1.219-234', 'tbw': 'an1.219-234', 'tbw_till_file': ''},
        {'sc': 'an1.235-247', 'tbw': 'an1.235-247', 'tbw_till_file': ''},
    ]

    # --- Запуск процесса ---
    master_tbw_ids = load_tbw_master_list(MASTER_ID_LIST_FILE)
    if master_tbw_ids:
        process_merge(mapping_table, master_tbw_ids, SOURCE_JSON_PATH, OUTPUT_DIR)
