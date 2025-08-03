import os
import json
import glob
from bs4 import BeautifulSoup, NavigableString

def process_text(tag_list):
    """
    Обрабатывает список тегов, объединяет их текст и очищает.
    """
    if not tag_list:
        return ""

    combined_html_str = "".join(str(t) for t in tag_list)
    clean_tag = BeautifulSoup(combined_html_str, 'html.parser')

    # Удаляем остальные ненужные элементы
    for parno in clean_tag.find_all('span', class_='parno'):
        parno.decompose()
    for note in clean_tag.find_all('span', class_='note'):
        note.decompose()
    for brnum in clean_tag.find_all('span', class_='brnum'):
        brnum.decompose()  # Исправлено: было note.decompose()
    for lookup in clean_tag.find_all('span', class_='lookup'):
        lookup.decompose()  # Исправлено: было note.decompose()
    for item in clean_tag.find_all('span', class_='add'):
        item.decompose()
    for item in clean_tag.find_all('a', class_='pts_pn'):
        item.decompose()

    text = clean_tag.get_text('\n', strip=False)
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    return text

def get_html_structure(tag_list):
    """
    Генерирует HTML-структуру для списка тегов.
    """
    if not tag_list:
        return ""

    combined_html_str = "".join(str(t) for t in tag_list)
    tag_copy = BeautifulSoup(combined_html_str, 'html.parser')

    for text_node in tag_copy.find_all(string=True):
        if text_node.strip():
            text_node.replace_with('{}')

    for selector, class_name in [('span', 'note'), ('span', 'add'), ('a', 'pts_pn'), ('span', 'brnum'), ('span', 'lookup')]:
        for item in tag_copy.find_all(selector, class_=class_name):
            item.decompose()

    return str(tag_copy)


def get_text_length(tag):
    """
    Вычисляет длину текста в теге, игнорируя сноски.
    """
    if not tag or not hasattr(tag, 'name'):
        return 0

    node = BeautifulSoup(str(tag), 'html.parser')
    for note in node.find_all('span', class_='note'):
        note.decompose()

    if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr']:
        return 0.01

    return len(node.get_text(strip=True))

def quality(v):
    """
    Оценивает "качество" совпадения длин. Чем ближе к 1, тем лучше.
    """
    return 1 / v if v > 1 else v

def extraporlative_splice(en_tags, pi_tags):
    """
    Основной алгоритм балансировки.
    """
    if not en_tags or not pi_tags:
        return [ (en_tags, pi_tags) ]

    en_lengths = [get_text_length(tag) for tag in en_tags]
    pi_lengths = [get_text_length(tag) for tag in pi_tags]

    en_idx, pi_idx = 0, 0
    aligned_rows = []

    while en_idx < len(en_tags) and pi_idx < len(pi_tags):
        sum_en_remains = sum(en_lengths[en_idx:])
        sum_pi_remains = sum(pi_lengths[pi_idx:])

        if sum_pi_remains == 0:
            if sum_en_remains > 0:
                aligned_rows.append( (en_tags[en_idx:], pi_tags[pi_idx:]) )
            break

        overall_ratio = sum_en_remains / sum_pi_remains if sum_pi_remains > 0 else 0
        en_stack, pi_stack = [], []
        en_stack.append(en_idx)
        en_idx += 1
        pi_stack.append(pi_idx)
        pi_idx += 1

        while True:
            current_en_len = sum(en_lengths[i] for i in en_stack)
            current_pi_len = sum(pi_lengths[i] for i in pi_stack)

            if current_pi_len == 0: break
            
            ratio = (current_en_len / current_pi_len) / overall_ratio if overall_ratio > 0 and current_pi_len > 0 else 0
            best_quality = quality(ratio)
            improved = False
            
            if ratio > 1 and pi_idx < len(pi_tags):
                pi_stack.append(pi_idx)
                new_pi_len = sum(pi_lengths[i] for i in pi_stack)
                new_ratio = (current_en_len / new_pi_len) / overall_ratio if new_pi_len > 0 and overall_ratio > 0 else 0
                new_q = quality(new_ratio)
                if new_q > best_quality:
                    pi_idx += 1
                    improved = True
                else:
                    pi_stack.pop()
            elif ratio < 1 and en_idx < len(en_tags):
                en_stack.append(en_idx)
                new_en_len = sum(en_lengths[i] for i in en_stack)
                new_ratio = (new_en_len / current_pi_len) / overall_ratio if current_pi_len > 0 and overall_ratio > 0 else 0
                new_q = quality(new_ratio)
                if new_q > best_quality:
                    en_idx += 1
                    improved = True
                else:
                    en_stack.pop()
            
            if not improved:
                break
        
        final_en_tags = [en_tags[i] for i in en_stack]
        final_pi_tags = [pi_tags[i] for i in pi_stack]
        aligned_rows.append((final_en_tags, final_pi_tags))

    if en_idx < len(en_tags) or pi_idx < len(pi_tags):
        aligned_rows.append( (en_tags[en_idx:], pi_tags[pi_idx:]) )

    return aligned_rows

def process_sutta(html_filepath, output_dir="output"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Обработка файла: {html_filepath}...")
    with open(html_filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    content_div = soup.select_one("#content")
    if not content_div:
        print(f"  [ПРЕДУПРЕЖДЕНИЕ] Не найден div #content в файле {html_filepath}")
        return

    sutta_id = os.path.splitext(os.path.basename(html_filepath))[0]
    pali_data, en_data, html_data = {}, {}, {}

    en_content = content_div.select_one("div[lang='en']")
    pali_content = content_div.select_one("div[lang='pi']")

    if not en_content or not pali_content:
        print(f"  [ПРЕДУПРЕЖДЕНИЕ] Не найден контент на английском или пали в файле {html_filepath}")
        return

    def is_separator(tag):
        return tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr']

    def split_into_blocks(content_div):
        blocks = []
        current_block = []
        for tag in content_div.children:
            if isinstance(tag, NavigableString):
                continue
            if is_separator(tag):
                if current_block:
                    blocks.append(current_block)
                current_block = [tag]
            else:
                current_block.append(tag)
        if current_block:
            blocks.append(current_block)
        return blocks

    en_blocks = split_into_blocks(en_content)
    pi_blocks = split_into_blocks(pali_content)
    
    block_num = 1
    max_blocks = max(len(en_blocks), len(pi_blocks))
    for i in range(max_blocks):
        en_block = en_blocks[i] if i < len(en_blocks) else []
        pi_block = pi_blocks[i] if i < len(pi_blocks) else []

        aligned_rows = extraporlative_splice(en_block, pi_block)
        
        row_num = 1
        for en_tags, pi_tags in aligned_rows:
            if not en_tags and not pi_tags:
                continue
                
            key = f"{sutta_id}:{block_num}.{row_num}"
            en_data[key] = process_text(en_tags)
            pali_data[key] = process_text(pi_tags)
            html_data[key] = get_html_structure(en_tags)
            row_num += 1
        block_num += 1

    output_dir="output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
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
            try:
                process_sutta(filepath)
            except Exception as e:
                print(f"!!! КРИТИЧЕСКАЯ ОШИБКА при обработке файла {filepath}: {e}")
    print("\nОбработка завершена.")
