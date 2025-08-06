import os
import json
import re
from collections import defaultdict

def process_iti_json():
    """
    Processes all iti*.json files in the current directory,
    groups them by the iti number, and merges them into a single
    JSON file.
    """
    files = os.listdir('.')
    iti_data = defaultdict(dict)

    # This regex will extract the number from filenames like 'iti10_...' or 'iti110_...'
    file_regex = re.compile(r'iti(\d+(?:-\d+)?_.*\.json)')

    for f in files:
        match = file_regex.match(f)
        if not match:
            print(f"Skipping file (does not match expected format): {f}")
            continue

        iti_num = match.group(1)
        
        file_type = "unknown"
        if "html" in f:
            file_type = "html"
        elif "root-pli-ms" in f:
            file_type = "root-pli-ms"
        elif "translation-en-thanissaro" in f:
            file_type = "translation-en-thanissaro"

        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                iti_data[iti_num][file_type] = data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {f}: {e}")
        except Exception as e:
            print(f"Error processing file {f}: {e}")

    output_filename = 'iti_merged.json'
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(iti_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully processed {len(iti_data)} iti entries.")
        print(f"Merged data saved to {output_filename}")
    except Exception as e:
        print(f"Error writing output file {output_filename}: {e}")

if __name__ == '__main__':
    process_iti_json()
