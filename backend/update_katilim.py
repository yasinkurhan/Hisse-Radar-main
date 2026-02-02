#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIST Katılım Endeksi Güncelleme Scripti
Katılım 30 ve Katılım 50 endeks bileşenlerini günceller
"""

import json
import os

# JSON dosyasını oku
json_path = 'app/data/bist_stocks.json'

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

stocks = data.get('stocks', [])

# BIST Katılım 30 - Güncel resmi liste (Ocak 2025)
# Faizsiz finans prensiplerine uygun şirketler
# Bankalar, sigorta, faizli işlem yapan kurumlar HARİÇ
KATILIM_30 = {
    'ASELS',  # Aselsan - Savunma
    'THYAO',  # THY - Havacılık
    'BIMAS',  # BİM - Perakende
    'TUPRS',  # Tüpraş - Enerji
    'EREGL',  # Erdemir - Demir-Çelik
    'FROTO',  # Ford Otosan - Otomotiv
    'TOASO',  # Tofaş - Otomotiv
    'SISE',   # Şişecam - Cam
    'ENKAI',  # Enka - İnşaat
    'TCELL',  # Turkcell - Telekom
    'TTKOM',  # Türk Telekom - Telekom
    'ARCLK',  # Arçelik - Beyaz Eşya
    'PGSUS',  # Pegasus - Havacılık
    'MGROS',  # Migros - Perakende
    'DOAS',   # Doğuş Otomotiv - Otomotiv
    'GUBRF',  # Gübre Fabrikaları - Kimya
    'PETKM',  # Petkim - Petrokimya
    'TAVHL',  # TAV - Havalimanı
    'EKGYO',  # Emlak Konut GYO - GYO
    'SOKM',   # Şok Market - Perakende
    'KRDMD',  # Kardemir - Demir-Çelik
    'ULKER',  # Ülker - Gıda
    'TTRAK',  # Türk Traktör - Makine
    'CCOLA',  # Coca-Cola İçecek - İçecek
    'VESTL',  # Vestel - Elektronik
    'OTKAR',  # Otokar - Otomotiv
    'AYGAZ',  # Aygaz - Enerji
    'BRSAN',  # Borusan - Çelik Boru
    'MAGEN',  # Margun Enerji - Enerji
    'AKSEN',  # Aksa Enerji - Enerji
}

# BIST Katılım 50 - Katılım 30 + 20 ek hisse
KATILIM_50_EXTRA = {
    'ASTOR',  # Astor Enerji - Enerji
    'AKSA',   # Aksa - Tekstil
    'ALFAS',  # Alfa Solar - Enerji
    'OYAKC',  # Oyak Çimento - Çimento
    'CWENE',  # CW Enerji - Enerji
    'GESAN',  # Girişim Elektrik - Enerji
    'EGEEN',  # Ege Endüstri - Makine
    'MPARK',  # MLP Sağlık - Sağlık
    'SASA',   # Sasa Polyester - Kimya
    'TABGD',  # Tab Gıda - Gıda
    'MAVI',   # Mavi - Tekstil
    'TMSN',   # Tümosan - Makine
    'TATGD',  # Tat Gıda - Gıda
    'YEOTK',  # Yeo Teknoloji - Enerji
    'KONTR',  # Kontrolmatik - Teknoloji
    'KCAER',  # Kocaer Çelik - Çelik
    'ODAS',   # ODAŞ Elektrik - Enerji
    'ZOREN',  # Zorlu Enerji - Enerji
    'CIMSA',  # Çimsa - Çimento
    'ENJSA',  # Enerjisa - Enerji
}

KATILIM_50 = KATILIM_30 | KATILIM_50_EXTRA

# Ek katılım uyumlu hisseler (daha geniş havuz)
# Bu hisseler faiz oranları ve sektör kriterleri açısından katılım fonlarına uygun
KATILIM_UYUMLU_EK = {
    'BANVT',  # Banvit - Gıda
    'BRISA',  # Brisa - Lastik
    'BOSSA',  # Bossa - Tekstil
    'DEVA',   # Deva - İlaç
    'ECILC',  # Eczacıbaşı İlaç - İlaç
    'ERBOS',  # Erbosan - Çelik
    'GOODY',  # Goodyear - Lastik
    'GOLTS',  # Göltaş - Çimento
    'KARTN',  # Kartonsan - Kağıt
    'KORDS',  # Kordsa - Tekstil
    'NETAS',  # Netaş - Teknoloji
    'CEMTS',  # Çemtaş - Çelik
    'BUCIM',  # Bursa Çimento - Çimento
    'BAGFS',  # Bağfaş - Gübre
    'ASUZU',  # Anadolu Isuzu - Otomotiv
    'ARZUM',  # Arzum - Küçük Ev Aletleri
    'KONYA',  # Konya Çimento - Çimento
    'KLMSN',  # Klimasan - Soğutma
    'LMKDC',  # Limak Doğu Anadolu - Enerji
    'SARKY',  # Sarkuysan - Kablo
    'KARSN',  # Karsan - Otomotiv
    'CRFSA',  # CarrefourSA - Perakende
    'TRGYO',  # Torunlar GYO - GYO
    'PRKME',  # Park Elektrik - Madencilik
    'DITAS',  # Ditaş - Otomotiv Yan San.
    'EGSER',  # Ege Seramik - Seramik
    'INDES',  # İndeks Bilgisayar - Teknoloji
    'LOGO',   # Logo Yazılım - Teknoloji
    'MTRKS',  # Matriks - Teknoloji
    'PRZMA',  # Prizma - Teknoloji
    'FONET',  # Fonet Bilgi - Teknoloji
    'PAPIL',  # Papilon - Teknoloji
    'ARDYZ',  # ARD Bilişim - Teknoloji
    'PASEU',  # Pasifik Eurasia - Lojistik
    'TLMAN',  # Trabzon Liman - Lojistik
    'CLEBI',  # Çelebi - Lojistik (holding değil, havacılık hizmetleri)
}

# Tüm katılım uyumlu hisseler
TUM_KATILIM_UYUMLU = KATILIM_50 | KATILIM_UYUMLU_EK

# Katılım endeksinde OLMAMASI gerekenler
# Bankalar (faiz geliri var)
# Sigorta şirketleri (faiz geliri var)
# Alkol, tütün, kumar şirketleri
KATILIM_HARIC = {
    # Bankalar
    'AKBNK', 'GARAN', 'HALKB', 'ISCTR', 'VAKBN', 'YKBNK', 'TSKB', 'SKBNK',
    'ALBRK',  # Katılım bankası bile olsa banka
    'ICBCT',  # ICBC Turkey Bank
    
    # Sigorta Şirketleri
    'AGESA', 'ANHYT', 'AKGRT', 'ANSGR', 'TURSG', 'RAYSG', 'GUSGR',
    'ULUUN',  # Sigorta
    
    # Holdinglerin bir kısmı (banka/sigorta yoğunluklu)
    'SAHOL',  # Sabancı (banka ağırlıklı)
    'KCHOL',  # Koç (banka/sigorta var ama ağırlıklı değil, tartışmalı)
    'TKFEN',  # Tekfen (inşaat ağırlıklı, katılıma uygun olabilir)
    
    # Alkol üreticileri
    'AEFES',  # Anadolu Efes - Bira
    'TBORG',  # Tuborg
    
    # Faktoring/Leasing
    'KTLEV',  # Katılımevim - Finansal kiralama
    
    # GYO'lar genellikle katılıma uygun değil (faizli borç oranına göre değişir)
    # Ama EKGYO gibi bazıları kabul ediliyor
}

# Mevcut durumu kontrol et
mevcut_katilim = [s['symbol'] for s in stocks if 'KATILIM' in str(s.get('indexes', [])).upper()]
mevcut_symbols = {s['symbol'] for s in stocks}

print("=" * 60)
print("BIST KATILIM ENDEKSİ GÜNCELLEME")
print("=" * 60)
print(f"\nMevcut Katılım işaretli hisse sayısı: {len(mevcut_katilim)}")
print(f"Yeni Katılım 30 sayısı: {len(KATILIM_30)}")
print(f"Yeni Katılım 50 sayısı: {len(KATILIM_50)}")
print(f"Toplam Katılım Uyumlu sayısı: {len(TUM_KATILIM_UYUMLU)}")

# Veritabanında var olan katılım uyumlu hisseler
var_olan_katilim = TUM_KATILIM_UYUMLU & mevcut_symbols
print(f"\nVeritabanında bulunan Katılım uyumlu: {len(var_olan_katilim)}")

# Çıkarılacak hisseler (yanlış işaretlenmiş)
cikarilacak = set(mevcut_katilim) - TUM_KATILIM_UYUMLU
print(f"\nÇıkarılacak (yanlış işaretli) hisse sayısı: {len(cikarilacak)}")
if cikarilacak:
    print("Çıkarılacaklar:")
    for s in sorted(cikarilacak):
        stock = next((st for st in stocks if st['symbol'] == s), None)
        if stock:
            print(f"  - {s}: {stock.get('name', 'N/A')} ({stock.get('sector', 'N/A')})")

# Eklenecek hisseler
eklenecek = var_olan_katilim - set(mevcut_katilim)
print(f"\nEklenecek hisse sayısı: {len(eklenecek)}")
if eklenecek:
    print("Eklenecekler:")
    for s in sorted(eklenecek):
        print(f"  - {s}")

# Güncelleme yap
print("\n" + "=" * 60)
print("GÜNCELLEME YAPILIYOR...")
print("=" * 60)

guncellenen = 0
for stock in stocks:
    symbol = stock['symbol']
    indexes = stock.get('indexes', [])
    
    # Mevcut index'leri set olarak al
    if isinstance(indexes, list):
        indexes_set = set(indexes)
    else:
        indexes_set = set()
    
    # Katılım uyumlu ise ekle
    if symbol in var_olan_katilim:
        if 'KATILIM' not in indexes_set:
            indexes_set.add('KATILIM')
            guncellenen += 1
    # Katılım uyumlu değilse çıkar
    elif 'KATILIM' in indexes_set:
        indexes_set.discard('KATILIM')
        guncellenen += 1
    
    # Katılım 30 ise işaretle
    if symbol in KATILIM_30:
        indexes_set.add('KATILIM30')
    else:
        indexes_set.discard('KATILIM30')
    
    # Katılım 50 ise işaretle
    if symbol in KATILIM_50:
        indexes_set.add('KATILIM50')
    else:
        indexes_set.discard('KATILIM50')
    
    stock['indexes'] = sorted(list(indexes_set))

print(f"\nGüncellenen hisse sayısı: {guncellenen}")

# Dosyaya kaydet
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n✓ Güncelleme tamamlandı: {json_path}")

# Son durumu göster
son_katilim = [s['symbol'] for s in stocks if 'KATILIM' in str(s.get('indexes', []))]
son_k30 = [s['symbol'] for s in stocks if 'KATILIM30' in str(s.get('indexes', []))]
son_k50 = [s['symbol'] for s in stocks if 'KATILIM50' in str(s.get('indexes', []))]

print(f"\nSON DURUM:")
print(f"  - Toplam Katılım Uyumlu: {len(son_katilim)}")
print(f"  - Katılım 30: {len(son_k30)}")
print(f"  - Katılım 50: {len(son_k50)}")
print(f"\nKatılım 30 hisseleri: {sorted(son_k30)}")
