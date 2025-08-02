import os
import json
import glob
import re
from bs4 import BeautifulSoup

# --- КОНФИГУРАЦИЯ ---
# Путь к папке с вашими распарсенными файлами
PARSED_DATA_DIR = './output' 

# Базовый путь к данным SuttaCentral (первичный источник)
SC_DATA_BASE_DIR = '/var/www/html/suttacentral.net/sc-data/sc_bilara_data'

# Путь к папке с HTML-файлами для резервного поиска (фоллбэк)
FALLBACK_HTML_DIR = '/var/www/offline-data/theBuddhasWords/'

# Автор перевода для поиска в первичном источнике
TRANSLATION_AUTHOR = 'sujato'
# --- Конец конфигурации ---


def extract_titles(data_dict):
    """Извлекает из словаря все элементы с ключами, заканчивающимися на ':0.<цифра>'."""
    titles = {}
    if not data_dict:
        return titles
    for key, value in data_dict.items():
        if re.search(r":0\.\d+$", key):
            titles[key] = value
    return titles

def find_source_file(base_dir, filename_to_find):
    """Рекурсивно ищет файл внутри базовой директории."""
    if not os.path.isdir(base_dir):
        # Не выводим ошибку, если папка фоллбэка не существует, это ожидаемо
        if base_dir != FALLBACK_HTML_DIR:
             print(f"  [ОШИБКА КОНФИГУРАЦИИ] Директория не найдена: {base_dir}")
        return None
        
    search_pattern = os.path.join(base_dir, '**', filename_to_find)
    results = glob.glob(search_pattern, recursive=True)
    
    if not results:
        return None
    
    if len(results) > 1:
        print(f"  [ПРЕДУПРЕЖДЕНИЕ] Найдено несколько файлов для '{filename_to_find}'. Используется первый: {results[0]}")
    
    return results[0]

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

    pali_title_dir = os.path.join(SC_DATA_BASE_DIR, 'root/pli/ms/sutta')
    en_title_dir = os.path.join(SC_DATA_BASE_DIR, f'translation/en/{TRANSLATION_AUTHOR}/sutta')
    html_title_dir = os.path.join(SC_DATA_BASE_DIR, 'html/pli/ms/sutta')

    target_files = glob.glob(f'{PARSED_DATA_DIR}/**/*_root-pli-ms.json', recursive=True)

    if not target_files:
        print(f"Не найдено файлов '*_root-pli-ms.json' в директории '{PARSED_DATA_DIR}'.")
        return

    print(f"Найдено {len(target_files)} файлов для обработки.")
    
    successful_updates = 0
    failed_updates = 0

    for root_file_path in target_files:
        try:
            base_id = os.path.basename(root_file_path).replace('_root-pli-ms.json', '')
            print(f"\n--- Обработка: {base_id} ---")
            
            pali_titles, en_titles, html_titles = {}, {}, {}
            
            # --- ЭТАП 1: Первичный поиск в sc_bilara_data ---
            pali_source_filename = f'{base_id}_root-pli-ms.json'
            en_source_filename = f'{base_id}_translation-en-{TRANSLATION_AUTHOR}.json'
            html_source_filename = f'{base_id}_html.json'

            pali_title_path = find_source_file(pali_title_dir, pali_source_filename)
            en_title_path = find_source_file(en_title_dir, en_source_filename)
            html_title_path = find_source_file(html_title_dir, html_source_filename)

            if all([pali_title_path, en_title_path, html_title_path]):
                print("  Источник: sc_bilara_data (основной).")
                with open(pali_title_path, 'r', encoding='utf-8') as f:
                    pali_titles = extract_titles(json.load(f))
                with open(en_title_path, 'r', encoding='utf-8') as f:
                    en_titles = extract_titles(json.load(f))
                with open(html_title_path, 'r', encoding='utf-8') as f:
                    html_titles = extract_titles(json.load(f))
            else:
                # --- ЭТАП 2: Резервный поиск (фоллбэк) в theBuddhasWords ---
                print("  Источник: sc_bilara_data не найден. Запуск резервного поиска...")
                fallback_filename = f'{base_id}.html'
                fallback_path = find_source_file(FALLBACK_HTML_DIR, fallback_filename)

                if fallback_path:
                    print(f"  Источник: {FALLBACK_HTML_DIR} (резервный).")
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
                    print(f"  [ОШИБКА] Резервный файл '{fallback_filename}' также не найден.")
            
            # --- ОБНОВЛЕНИЕ ФАЙЛОВ ---
            if not en_titles and not pali_titles and not html_titles:
                print(f"  [ПРЕДУПРЕЖДЕНИЕ] Не найдено никаких заголовков для {base_id}. Файл пропущен.")
                failed_updates += 1
                continue

            translation_file_path = root_file_path.replace('_root-pli-ms.json', '_translation-en-bodhi.json')
            html_file_path = root_file_path.replace('_root-pli-ms.json', '_html.json')
            
            # Обновляем только те файлы, для которых нашлись заголовки
            for file_path, original_data, titles_to_add in [
                (root_file_path, None, pali_titles),
                (translation_file_path, None, en_titles),
                (html_file_path, None, html_titles)
            ]:
                if titles_to_add:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original_data = json.load(f)
                    
                    new_data = {**titles_to_add, **original_data}
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(new_data, f, ensure_ascii=False, indent=2)

            print(f"  [УСПЕХ] Файлы для {base_id} успешно обновлены.")
            successful_updates += 1

        except Exception as e:
            print(f"  [КРИТ. ОШИБКА] Произошла непредвиденная ошибка при обработке {root_file_path}: {e}")
            failed_updates += 1

    print("\n--- Обработка завершена ---")
    print(f"Успешно обновлено: {successful_updates}")
    print(f"Пропущено/ошибки: {failed_updates}")

if __name__ == "__main__":
    main()
