import re

with open('app/services/analysis_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# _analyze_single_stock fonksiyonunu bul ve güncelle
new_lines = []
in_function = False
func_indent = ""

for i, line in enumerate(lines):
    if 'def _analyze_single_stock' in line:
        in_function = True
        func_indent = line[:len(line) - len(line.lstrip())]
        # Yeni fonksiyon başlangıcı
        new_lines.append(f'{func_indent}def _analyze_single_stock(self, symbol: str, period: str = "3mo", interval: str = "1d", retries: int = 2) -> Optional[Dict[str, Any]]:\n')
        new_lines.append(f'{func_indent}    """Tek hisse analizi - retry mekanizmasi ile"""\n')
        new_lines.append(f'{func_indent}    import time\n')
        new_lines.append(f'{func_indent}    for attempt in range(retries):\n')
        continue
    
    if in_function:
        # try: satırı
        if line.strip() == 'try:':
            new_lines.append(f'{func_indent}        try:\n')
            continue
        # except satırı - fonksiyon sonu
        if line.strip().startswith('except') and 'Exception' in line:
            new_lines.append(f'{func_indent}        except Exception as e:\n')
            new_lines.append(f'{func_indent}            if attempt < retries - 1:\n')
            new_lines.append(f'{func_indent}                time.sleep(0.3)\n')
            new_lines.append(f'{func_indent}                continue\n')
            new_lines.append(f'{func_indent}            return None\n')
            new_lines.append(f'{func_indent}    return None\n')
            in_function = False
            continue
        # return None satırını atla
        if line.strip() == 'return None' and in_function:
            continue
        # Diğer satırları 4 boşluk içeri al (for döngüsü için)
        if line.strip() and not line.strip().startswith('#'):
            # Mevcut indent'i hesapla
            current_indent = len(line) - len(line.lstrip())
            if current_indent >= len(func_indent) + 4:
                # 4 boşluk ekle
                new_lines.append(' ' * 4 + line)
                continue
    
    new_lines.append(line)

with open('app/services/analysis_service.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Güncellendi!")
