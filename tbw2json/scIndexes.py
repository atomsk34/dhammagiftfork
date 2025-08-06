import json
import os
import re
import argparse
import csv
import glob

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
        
        # Ищем конечный индекс. end_id может быть частью строки в master_list.
        for i, item in enumerate(master_list):
            if i >= start_index:
                if item == end_id or end_id in item.split('-'):
                    end_index = i
                    break
        
        if end_index == -1:
            # Если end_id не найден, возможно, это одиночный файл
            return [start_id]

        return master_list[start_index : end_index + 1]
    except ValueError:
        # Если start_id не найден, это может быть нормально для некоторых диапазонов
        # Например, если tbw ID - это диапазон типа 'an1.188-197'
        if '-' in start_id:
             return [start_id]
        print(f"  - Предупреждение: Начальный ID '{start_id}' не найден в мастер-списке.")
        return []

def read_ranges_from_csv(filepath):
    """
    Читает диапазоны из CSV файла.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Пропускаем заголовок
            # Создаем список словарей, пропуская пустые строки
            return [{'sc': row[0], 'tbw': row[1], 'tbw_till_file': row[2]} for row in reader if row and row[0]]
    except FileNotFoundError:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Файл с диапазонами не найден: {filepath}")
        return None
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось прочитать файл с диапазонами: {e}")
        return None


def process_merge(mapping, master_tbw_ids, source_path, output_dir):
    """
    Основная функция для обработки карты слияния.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Создана директория: {output_dir}")

    for row in mapping:
        sc_id, start_tbw, end_tbw = row['sc'], row['tbw'], row['tbw_till_file']
        
        if not start_tbw:
            print(f"\n[!] ПРОПУСК: Пустой tbw ID для sc_id {sc_id}")
            continue

        if not end_tbw:
            end_tbw = start_tbw

        print(f"\n[+] Обработка SC ID: {sc_id} (диапазон tbw: {start_tbw} до {end_tbw})")
        
        tbw_ids_to_merge = get_ids_in_range(start_tbw, end_tbw, master_tbw_ids)
        
        if not tbw_ids_to_merge:
            print(f"  - ПРОПУСК: не удалось сформировать диапазон для {sc_id}.")
            continue

        print(f"  - Диапазон для объединения: с {tbw_ids_to_merge[0]} по {tbw_ids_to_merge[-1]}")

        # Словарь для хранения объединенных данных по типам файлов
        # e.g. {'root-pli-ms': {...}, 'translation-en-bodhi': {...}}
        merged_data_by_type = {}

        for tbw_id in tbw_ids_to_merge:
            # Извлекаем префикс (например, 'an', 'sn') для построения пути
            nikaya_match = re.match(r'([a-zA-Z]+)', tbw_id)
            if not nikaya_match:
                print(f"  - Предупреждение: не удалось определить никкайю для ID '{tbw_id}'. Пропускаем.")
                continue
            nikaya = nikaya_match.group(1)
            
            # Ищем все файлы, относящиеся к данному tbw_id
            search_pattern = os.path.join(source_path, nikaya, f"{tbw_id}_*.json")
            
            # Если в tbw_id есть тире, это уже диапазон, ищем файлы для него
            if '-' in tbw_id:
                search_pattern = os.path.join(source_path, nikaya, f"{tbw_id.replace('.', r'.')}_*.json")


            found_files = glob.glob(search_pattern)

            if not found_files:
                 # Попробуем поискать в корневой директории источника, если в подпапке не найдено
                 search_pattern_root = os.path.join(source_path, f"{tbw_id}_*.json")
                 found_files = glob.glob(search_pattern_root)


            for file_path in found_files:
                try:
                    # Извлекаем тип файла из имени (например, 'root-pli-ms')
                    filename = os.path.basename(file_path)
                    file_type_match = re.match(fr'{re.escape(tbw_id)}_(.+)\.json', filename)
                    if not file_type_match:
                        continue
                    
                    f_type = file_type_match.group(1)

                    # Инициализируем словарь для данного типа файла, если его еще нет
                    if f_type not in merged_data_by_type:
                        merged_data_by_type[f_type] = {}

                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        merged_data_by_type[f_type].update(data)

                except json.JSONDecodeError:
                    print(f"  - ОШИБКА: не удалось прочитать JSON из {file_path}")
                except Exception as e:
                    print(f"  - НЕИЗВЕСТНАЯ ОШИБКА при обработке файла {file_path}: {e}")

        # Сохраняем объединенные данные в файлы
        if not merged_data_by_type:
            print(f"  - Предупреждение: не найдено файлов для объединения для SC ID {sc_id}")
        
        for f_type, merged_data in merged_data_by_type.items():
            if merged_data:
                output_filename = f"{sc_id}_{f_type}.json"
                output_path = os.path.join(output_dir, output_filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(merged_data, f, ensure_ascii=False, indent=2)
                print(f"  - Сохранен: {output_path}")

def main():
    """
    Главная функция для запуска скрипта из командной строки.
    """
    parser = argparse.ArgumentParser(
        description="Объединяет JSON файлы на основе диапазонов из CSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--input-dir', 
        type=str, 
        default='.', 
        help="Путь к корневой папке с исходными JSON файлами."
    )
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default='merged_output',
        help="Папка для сохранения результатов."
    )
    parser.add_argument(
        '--ranges-file', 
        type=str, 
        default='ranges.csv',
        help="Путь к CSV файлу с диапазонами."
    )
    parser.add_argument(
        '--master-list', 
        type=str, 
        default='antbwID.txt',
        help="Путь к файлу с полным списком ID (например, antbwID.txt или sntbwID.txt)."
    )

    args = parser.parse_args()

    print("--- Запуск процесса объединения ---")
    print(f"Директория с исходниками: {args.input_dir}")
    print(f"Директория для результатов: {args.output_dir}")
    print(f"Файл с диапазонами: {args.ranges_file}")
    print(f"Файл с мастер-списком ID: {args.master_list}")
    print("---------------------------------")


    master_tbw_ids = load_tbw_master_list(args.master_list)
    if not master_tbw_ids:
        return

    mapping_table = read_ranges_from_csv(args.ranges_file)
    if not mapping_table:
        return

    process_merge(mapping_table, master_tbw_ids, args.input_dir, args.output_dir)
    print("\n--- Процесс завершен ---")


if __name__ == "__main__":
    main()