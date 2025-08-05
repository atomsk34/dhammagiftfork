import json
import os
import re
from collections import defaultdict

def process_and_split_json_files(directory):
    """
    Combines data from the main 'iti1-112' JSON files and directly splits them
    into the final individual chapter files in the specified directory,
    correctly handling chapter numbering based on sutta titles.
    """
    translation_filepath = os.path.join(directory, "iti1-112_translation-en-thanissaro.json")
    if not os.path.exists(translation_filepath):
        print(f"Error: Main translation file not found at {translation_filepath}")
        return

    # Build a map from the chapter number in the key to the actual sutta number(s)
    key_chapter_to_sutta_map = {}
    try:
        with open(translation_filepath, 'r', encoding='utf-8') as f:
            translation_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {translation_filepath}")
        return

    # Extract and sort title keys (e.g., "it:1.1", "it:2.1") to process in order
    title_keys = sorted(
        [k for k in translation_data if k.endswith('.1')],
        key=lambda k: int(k.split(':')[1].split('.')[0])
    )

    last_sutta_num = 0
    for key in title_keys:
        value = translation_data[key]
        try:
            _, chapter_and_verse = key.split(':', 1)
            key_chapter_str, _ = chapter_and_verse.split('.', 1)
            key_chapter = int(key_chapter_str)
            value_str = str(value)

            # Try to find a range like "10–13" or "10-13"
            range_match = re.match(r'^\s*(\d+)\s*[–-]\s*(\d+)', value_str)
            if range_match:
                start, end = map(int, range_match.groups())
                sutta_range = list(range(start, end + 1))
                key_chapter_to_sutta_map[key_chapter] = sutta_range
                last_sutta_num = end
            else:
                # Try to find a single number like "1"
                single_match = re.match(r'^\s*(\d+)', value_str)
                if single_match:
                    sutta_num = int(single_match.group(1))
                    key_chapter_to_sutta_map[key_chapter] = [sutta_num]
                    last_sutta_num = sutta_num
                else:
                    # If no number is found, assume it's the next one in sequence
                    last_sutta_num += 1
                    key_chapter_to_sutta_map[key_chapter] = [last_sutta_num]

        except (ValueError, IndexError) as e:
            print(f"Warning: Could not parse sutta number from key '{key}' with value '{value}'. Skipping. Error: {e}")
            continue

    input_files = [
        os.path.join(directory, "iti1-112_html.json"),
        os.path.join(directory, "iti1-112_root-pli-ms.json"),
        translation_filepath
    ]

    key_chapters_content = defaultdict(lambda: defaultdict(dict))

    def get_file_type(filename):
        """Extracts a type from the filename like 'iti1-112_html.json' -> 'html'"""
        base = os.path.basename(filename)
        parts = base.replace('.json', '').split('_')
        if len(parts) > 1:
            return "_".join(parts[1:])
        return parts[0]

    # Step 1: Read all data and group it by the key's chapter number
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"Warning: Input file not found at {file_path}. Skipping.")
            continue

        file_type = get_file_type(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {file_path}")
            continue

        for key, value in data.items():
            try:
                _, chapter_and_verse = key.split(':', 1)
                chapter_str, _ = chapter_and_verse.split('.', 1)
                key_chapter = int(chapter_str)
                key_chapters_content[key_chapter][file_type][key] = value
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse key '{key}' in {file_path}. Skipping. Error: {e}")
                continue

    # Step 2: Write final files using the key_chapter -> sutta mapping
    all_sutta_numbers = set()
    for key_chapter, sutta_numbers in sorted(key_chapter_to_sutta_map.items()):
        if key_chapter in key_chapters_content:
            for sutta_num in sutta_numbers:
                all_sutta_numbers.add(sutta_num)
                for file_type, content_data in key_chapters_content[key_chapter].items():
                    # Create a new dict for the output, replacing the key chapter with the correct sutta number
                    output_data = {}
                    for old_key, value_content in content_data.items():
                        parts = old_key.split(':')
                        verse_part = parts[1].split('.')[1]
                        new_key = f"it:{sutta_num}.{verse_part}"
                        output_data[new_key] = value_content

                    output_filename = f"iti{sutta_num}_{file_type}.json"
                    output_path = os.path.join(directory, output_filename)

                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, ensure_ascii=False, indent=2)
                    print(f"Created {output_filename}")

    # Final report
    print(f"\nSuccessfully generated files for {len(all_sutta_numbers)} suttas.")
    if len(all_sutta_numbers) != 112:
        print(f"Warning: Expected 112 suttas, but found {len(all_sutta_numbers)}.")
        # Find missing suttas
        expected_suttas = set(range(1, 113))
        missing = sorted(list(expected_suttas - all_sutta_numbers))
        if missing:
            print(f"Missing sutta numbers: {missing}")


if __name__ == "__main__":
    current_directory = os.getcwd()
    process_and_split_json_files(current_directory)
    print("\nProcessing complete.")
