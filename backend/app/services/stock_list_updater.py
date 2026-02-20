"""
BIST Hisse Listesi Otomatik Güncelleyici (Servis)
===================================================
Backend başlatıldığında borsapy üzerinden tüm BIST endekslerini tarayarak
bist_stocks.json dosyasına eksik hisseleri ekler.
"""

import json
from pathlib import Path
from typing import List, Optional


def auto_update_stock_list() -> List[str]:
    """
    borsapy'den tüm BIST hisselerini çekip bist_stocks.json'a eksik olanları ekler.
    
    Returns:
        List[str]: Eklenen yeni sembol listesi
    """
    try:
        import borsapy as bp
        import pandas as pd
    except ImportError:
        print("[StockListUpdater] borsapy bulunamadı")
        return []
    
    stocks_path = Path(__file__).parent.parent / "data" / "bist_stocks.json"
    
    # Mevcut listeyi oku
    existing_data = {"stocks": [], "sectors": [], "indexes": []}
    existing_symbols = set()
    if stocks_path.exists():
        try:
            with open(stocks_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_symbols = {s["symbol"] for s in existing_data.get("stocks", [])}
        except Exception as e:
            print(f"[StockListUpdater] JSON okuma hatası: {e}")
            return []
    
    # borsapy'den tüm endekslerdeki hisseleri çek
    new_symbols = set()
    index_map = {}  # symbol -> [indexes]
    
    # XUTUM = Tüm BIST, en geniş endeks
    index_configs = [
        ("XUTUM", None),
        ("XU100", "BIST100"),
        ("XU050", None),
        ("XU030", "BIST30"),
        ("XKTUM", "KATILIM"),
    ]
    
    for idx_code, mapped_name in index_configs:
        try:
            idx = bp.Index(idx_code)
            symbols = idx.component_symbols
            if symbols:
                for sym in symbols:
                    sym = str(sym).upper().strip().replace(".IS", "")
                    if sym and len(sym) >= 2 and len(sym) <= 7:
                        new_symbols.add(sym)
                        if mapped_name:
                            if sym not in index_map:
                                index_map[sym] = []
                            index_map[sym].append(mapped_name)
        except Exception:
            pass
    
    # screen_stocks ile de dene (ek hisseler yakalansın)
    try:
        all_df = bp.screen_stocks()
        if all_df is not None and isinstance(all_df, pd.DataFrame) and not all_df.empty:
            for col_name in ["symbol", "Symbol", "Sembol", "sembol", "ticker", "Ticker"]:
                if col_name in all_df.columns:
                    for sym in all_df[col_name]:
                        sym = str(sym).upper().strip().replace(".IS", "")
                        if sym and len(sym) >= 2 and len(sym) <= 7:
                            new_symbols.add(sym)
                    break
    except Exception:
        pass
    
    # Eksik sembolleri bul ve ekle
    missing = sorted(new_symbols - existing_symbols)
    
    if not missing:
        return []
    
    added = []
    for sym in missing:
        name = sym
        sector = "Diğer"
        indexes = index_map.get(sym, [])
        
        # Sembol bilgisini çekmeyi dene (hızlı)
        try:
            ticker = bp.Ticker(sym)
            info = ticker.info
            if info and isinstance(info, dict):
                name = (info.get("longName") or info.get("shortName") 
                        or info.get("company_name") or sym)
                sector = info.get("sector") or info.get("industry") or "Diğer"
        except Exception:
            pass
        
        existing_data["stocks"].append({
            "symbol": sym,
            "name": name,
            "sector": sector,
            "indexes": list(set(indexes))
        })
        added.append(sym)
    
    if added:
        # Alfabetik sırala
        existing_data["stocks"].sort(key=lambda s: s["symbol"])
        
        # Kaydet
        try:
            with open(stocks_path, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=6)
        except Exception as e:
            print(f"[StockListUpdater] JSON yazma hatası: {e}")
            return []
    
    return added
