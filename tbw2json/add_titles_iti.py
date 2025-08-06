import os
import json
import glob
import re
from bs4 import BeautifulSoup

# --- КОНФИГУРАЦИЯ ---
# Путь к папке с вашими распарсенными файлами для ОБНОВЛЕНИЯ
PARSED_DATA_DIR = '.'

# Папка для сохранения обновленных файлов
OUTPUT_DIR = 'output'

# Базовый путь к данным SuttaCentral (первичный источник)
SC_DATA_BASE_DIR = '/var/www/html/suttacentral.net/sc-data/sc_bilara_data'

# Автор перевода для поиска в первичном источнике
# Используется для поиска файлов перевода, например, iti1_translation-en-sujato.json
TRANSLATION_AUTHOR = 'sujato'

# Путь к папке с HTML-файлами для резервного поиска (фоллбэк)
FALLBACK_HTML_DIR = '/var/www/offline-data/theBuddhasWords/kn/iti'
# --- Конец конфигурации ---

def extract_titles(data_dict):
    """Извлекает из словаря все элементы с ключами, заканчивающимися на ':0.<цифра>'."""
    titles = {}
    if not isinstance(data_dict, dict):
        return titles
    for key, value in data_dict.items():
        if re.search(r":0\.\d+$", key):
            titles[key] = value
    return titles

def get_source_files_map(base_dir, pattern, remove_str):
    """Сканирует директорию и создает словарь {base_id: file_path}."""
    if not os.path.isdir(base_dir):
        print(f"  [ОШИБКА КОНФИГУРАЦИИ] Директория не найдена: {base_dir}")
        return {}
    
    search_pattern = os.path.join(base_dir, '**', pattern)
    print(f"  Поиск файлов по шаблону: {search_pattern}")
    files = glob.glob(search_pattern, recursive=True)
    file_map = {}
    for f_path in files:
        base_id = os.path.basename(f_path).replace(remove_str, '')
        if base_id in file_map:
            print(f"  [ПРЕДУПРЕЖДЕНИЕ] Найден дубликат для base_id '{base_id}'. Используется: {f_path}")
        file_map[base_id] = f_path
    return file_map

def get_html_structure_for_tag(tag):
    """Генерирует HTML-структуру с плейсхолдером для одного тега."""
    if not tag:
        return ""
    tag_copy = BeautifulSoup(str(tag), 'html.parser')
    text_node = tag_copy.find(string=True)
    if text_node and text_node.strip():
        text_node.replace_with('{}')
    return str(tag_copy)

def main():
    """Основная функция скрипта."""
    print("Запуск скрипта для добавления заголовков...")

    # Создаем выходную директорию, если её нет
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Результаты будут сохранены в: {os.path.abspath(OUTPUT_DIR)}")

    # --- ЭТАП 1: Поиск всех исходных файлов ---
    print("\nСканирование исходных директорий...")
    
    # Определяем пути для поиска
    pali_dir = os.path.join(SC_DATA_BASE_DIR, 'root/pli/ms/sutta/kn/iti')
    en_dir = os.path.join(SC_DATA_BASE_DIR, f'translation/en/{TRANSLATION_AUTHOR}/sutta/kn/iti')
    html_dir = os.path.join(SC_DATA_BASE_DIR, 'html/pli/ms/sutta/kn/iti')

    pali_map = get_source_files_map(pali_dir, '*_root-pli-ms.json', '_root-pli-ms.json')
    en_map = get_source_files_map(en_dir, f'*_translation-en-{TRANSLATION_AUTHOR}.json', f'_translation-en-{TRANSLATION_AUTHOR}.json')
    html_map = get_source_files_map(html_dir, '*_html.json', '_html.json')
    
    print(f"Найдено {len(pali_map)} Pāli root файлов.")
    print(f"Найдено {len(en_map)} файлов перевода ({TRANSLATION_AUTHOR}).")
    print(f"Найдено {len(html_map)} HTML файлов.")

    # --- ЭТАП 2: Обработка целевых файлов ---
    target_files = glob.glob(f'{PARSED_DATA_DIR}/*_root-pli-ms.json')
    if not target_files:
        print(f"\nНе найдено файлов '*_root-pli-ms.json' в директории '{PARSED_DATA_DIR}'.")
        return

    print(f"\nНайдено {len(target_files)} файлов для обработки...")
    
    successful_updates = 0
    failed_updates = 0

    for root_file_path in target_files:
        try:
            base_name = os.path.basename(root_file_path)
            base_id = base_name.replace('_root-pli-ms.json', '')
            print(f"\n--- Обработка: {base_id} ---")
            
            pali_titles, en_titles, html_titles = {}, {}, {}
            
            pali_title_path = pali_map.get(base_id)
            en_title_path = en_map.get(base_id)
            html_title_path = html_map.get(base_id)

            if all([pali_title_path, en_title_path, html_title_path]):
                print(f"  Источник: sc_bilara_data (основной).")
                with open(pali_title_path, 'r', encoding='utf-8') as f:
                    pali_titles = extract_titles(json.load(f))
                with open(en_title_path, 'r', encoding='utf-8') as f:
                    en_titles = extract_titles(json.load(f))
                with open(html_title_path, 'r', encoding='utf-8') as f:
                    html_titles = extract_titles(json.load(f))
            else:
                print("  Источник: sc_bilara_data не найден или не полон. Запуск резервного поиска...")
                fallback_filename = f'{base_id}.html'
                
                # Рекурсивный поиск в фоллбэк директории
                search_pattern = os.path.join(FALLBACK_HTML_DIR, '**', fallback_filename)
                fallback_paths = glob.glob(search_pattern, recursive=True)
                
                if fallback_paths:
                    fallback_path = fallback_paths[0]
                    print(f"  Найден резервный файл: {fallback_path}")
                    with open(fallback_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                    
                    content_div = soup.select_one("#content")
                    if content_div:
                        h2 = content_div.find('h2')
                        h3 = content_div.find('h3')
                        
                        found_titles = []
                        if h2 and h2.get_text(strip=True):
                            found_titles.append({'tag': h2, 'text': h2.get_text(strip=True)})
                        if h3 and h3.get_text(strip=True):
                            found_titles.append({'tag': h3, 'text': h3.get_text(strip=True)})

                        for i, title_info in enumerate(found_titles, 1):
                            key = f"{base_id}:0.{i}"
                            en_titles[key] = title_info['text']
                            html_titles[key] = get_html_structure_for_tag(title_info['tag'])
                else:
                    print(f"  [ОШИБКА] Резервный файл не найден. Поиск по шаблону: {search_pattern}")

            if not en_titles and not pali_titles and not html_titles:
                print(f"  [ПРЕДУПРЕЖДЕНИЕ] Не найдено никаких заголовков для {base_id}. Файлы не будут изменены.")
                failed_updates += 1
                continue

            # --- ОБНОВЛЕНИЕ ФАЙЛОВ В ПАПКЕ output ---
            for suffix, titles_to_add in [
                ('_root-pli-ms.json', pali_titles),
                (f'_translation-en-{TRANSLATION_AUTHOR}.json', en_titles),
                ('_html.json', html_titles)
            ]:
                if titles_to_add:
                    original_file_path = os.path.join(PARSED_DATA_DIR, base_id + suffix)
                    output_file_path = os.path.join(OUTPUT_DIR, base_id + suffix)
                    
                    try:
                        with open(original_file_path, 'r', encoding='utf-8') as f:
                            original_data = json.load(f)
                        
                        new_data = {**titles_to_add, **original_data}
                        
                        with open(output_file_path, 'w', encoding='utf-8') as f:
                            json.dump(new_data, f, ensure_ascii=False, indent=2)
                            
                    except FileNotFoundError:
                        print(f"  [ПРЕДУПРЕЖДЕНИЕ] Исходный файл не найден, будет создан новый: {os.path.basename(output_file_path)}")
                        with open(output_file_path, 'w', encoding='utf-8') as f:
                            json.dump(titles_to_add, f, ensure_ascii=False, indent=2)
                    except json.JSONDecodeError:
                        print(f"  [ОШИБКА] Не удалось прочитать JSON из {os.path.basename(original_file_path)}. Создан новый файл только с заголовками.")
                        with open(output_file_path, 'w', encoding='utf-8') as f:
                            json.dump(titles_to_add, f, ensure_ascii=False, indent=2)


            print(f"  [УСПЕХ] Файлы для {base_id} успешно созданы/обновлены в папке '{OUTPUT_DIR}'.")
            successful_updates += 1

        except Exception as e:
            print(f"  [КРИТ. ОШИБКА] Произошла непредвиденная ошибка при обработке {root_file_path}: {e}")
            import traceback
            traceback.print_exc()
            failed_updates += 1

    print("\n--- Обработка завершена ---")
    print(f"Успешно обновлено/создано файлов (для каждого base_id): {successful_updates}")
    print(f"Пропущено/ошибки: {failed_updates}")

if __name__ == "__main__":
    main()
