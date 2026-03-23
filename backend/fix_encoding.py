import os
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    replacements = {
        'Ä±': 'ı', 'Ä°': 'İ', 'ÄŸ': 'ğ', 'Ä': 'Ğ', 'ÅŸ': 'ş', 'Åž': 'Ş',
        'Ã¶': 'ö', 'Ã–': 'Ö', 'Ã¼': 'ü', 'Ãœ': 'Ü', 'Ã§': 'ç', 'Ã‡': 'Ç',
        'ğŸ“¡': '📊', 'Ğ±': 'ı', 'â€œ': '"', 'â€\x9d': '"', 'â€™': "'"
    }

    for k, v in replacements.items():
        content = content.replace(k, v)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed encoding in {filepath}")

def walk_and_fix(start_path):
    for root, dirs, files in os.walk(start_path):
        for f in files:
            if f.endswith('.tsx') or f.endswith('.ts'):
                fix_file(os.path.join(root, f))

if __name__ == '__main__':
    walk_and_fix(r'C:\Users\kurha\Desktop\Hisse-Radar-main-main\frontend\src')
