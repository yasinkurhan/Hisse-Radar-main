"""
HisseRadar - Profesyonel Grafik Formasyonlari Tanima Robotu
============================================================
Matriks / MatriksIQ / Bloomberg benzeri 30+ formasyon tespiti.

Kategoriler:
  1. Klasik Formasyonlar (Flag, Triangle, H&S, Double, Channel, Wedge)
  2. Gelismis Formasyonlar (Triple, Cup&Handle, Rectangle, Rounding, Broadening)
  3. Bosluk Formasyonlari (Gap Up/Down, Island Reversal, Exhaustion Gap)
  4. Harmonik Formasyonlar (Gartley, Butterfly, Bat, Crab, ABCD)
  5. Fibonacci Analizi (Retracement, Extension, Pivot seviyeleri)
  6. Destek / Direnc Tespiti
  7. Hacim Bazli Formasyonlar (Volume Climax, Accumulation/Distribution)
  8. Mum Cubuk Formasyonlari (Engulfing, Doji, Hammer, Star, vb.)
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy.signal import argrelextrema
import pandas as pd
import math


class ChartPatternDetector:
    """Profesyonel grafik formasyon tespiti robotu"""

    PATTERN_CATEGORIES = {
        "classic": "Klasik Formasyonlar",
        "advanced": "Gelismis Formasyonlar",
        "gap": "Bosluk Formasyonlari",
        "harmonic": "Harmonik Formasyonlar",
        "fibonacci": "Fibonacci Analizi",
        "support_resistance": "Destek / Direnc",
        "volume": "Hacim Formasyonlari",
        "candlestick": "Mum Cubuk Formasyonlari",
    }

    def __init__(self):
        self.min_pattern_length = 10

    # ================================================================
    #  ANA TESPIT FONSIYONU
    # ================================================================
    def detect_all_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df is None or len(df) < self.min_pattern_length:
            return {"patterns": [], "summary": "Yetersiz veri", "support_resistance": {}, "fibonacci": {}}

        # --- Normalize kolonlar ------------------------------------------
        col_map = {}
        for c in df.columns:
            cl = c.lower()
            if cl in ("open", "high", "low", "close", "volume"):
                col_map[c] = cl.capitalize()
        if col_map:
            df = df.rename(columns=col_map)

        close = df["Close"].values.astype(float)
        high  = df["High"].values.astype(float)
        low   = df["Low"].values.astype(float)
        opn   = df["Open"].values.astype(float) if "Open" in df.columns else close.copy()
        vol   = df["Volume"].values.astype(float) if "Volume" in df.columns else np.ones(len(close))

        pivots_high = self._find_pivots(high, np.greater, order=5)
        pivots_low  = self._find_pivots(low, np.less, order=5)
        fine_high = self._find_pivots(high, np.greater, order=3)
        fine_low  = self._find_pivots(low, np.less, order=3)

        patterns: List[Dict] = []

        # === 1) KLASIK FORMASYONLAR =====================================
        patterns += self._detect_flag(close, high, low, vol)
        patterns += self._detect_pennant(close, high, low, vol)
        patterns += self._detect_triangles(close, pivots_high, pivots_low)
        patterns += self._detect_head_and_shoulders(close, pivots_high, pivots_low)
        patterns += self._detect_double_patterns(close, pivots_high, pivots_low)
        ch = self._detect_channel(close, high, low)
        if ch:
            patterns.append(ch)
        w = self._detect_wedge(close, pivots_high, pivots_low)
        if w:
            patterns.append(w)

        # === 2) GELISMIS FORMASYONLAR ===================================
        patterns += self._detect_triple_patterns(close, pivots_high, pivots_low)
        cup = self._detect_cup_and_handle(close, pivots_high, pivots_low)
        if cup:
            patterns.append(cup)
        rect = self._detect_rectangle(close, high, low)
        if rect:
            patterns.append(rect)
        rnd = self._detect_rounding(close, pivots_low)
        if rnd:
            patterns.append(rnd)
        brd = self._detect_broadening(close, pivots_high, pivots_low)
        if brd:
            patterns.append(brd)

        # === 3) BOSLUK FORMASYONLARI =====================================
        patterns += self._detect_gaps(opn, close, high, low, vol)

        # === 4) HARMONIK FORMASYONLAR ====================================
        patterns += self._detect_harmonic_patterns(close, fine_high, fine_low)

        # === 5) FIBONACCI ANALIZI ========================================
        fib = self._calculate_fibonacci(close, high, low)

        # === 6) DESTEK / DIRENC ==========================================
        sr = self._detect_support_resistance(close, high, low, pivots_high, pivots_low)

        # === 7) HACIM FORMASYONLARI ======================================
        patterns += self._detect_volume_patterns(close, vol)

        # === 8) MUM CUBUK FORMASYONLARI ==================================
        patterns += self._detect_candlestick_patterns(opn, close, high, low)

        # Guven skorlarini yuvarla
        for p in patterns:
            p["confidence"] = round(min(98, max(30, p.get("confidence", 50))), 1)

        # Guven skoruna gore sirala
        patterns.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return {
            "patterns": patterns,
            "pattern_count": len(patterns),
            "summary": self._generate_summary(patterns),
            "support_resistance": sr,
            "fibonacci": fib,
        }

    # ================================================================
    #  ORTAK YARDIMCI FONKSIYONLAR
    # ================================================================
    @staticmethod
    def _find_pivots(prices: np.ndarray, comparator, order: int = 5) -> List[int]:
        idx = argrelextrema(prices, comparator, order=order)[0]
        return idx.tolist()

    @staticmethod
    def _trend_slope(indices: List[int], prices: np.ndarray) -> float:
        if len(indices) < 2:
            return 0.0
        x = np.array(indices, dtype=float)
        y = np.array([prices[i] for i in indices], dtype=float)
        return float(np.polyfit(x, y, 1)[0])

    @staticmethod
    def _pct(a: float, b: float) -> float:
        if b == 0:
            return 0.0
        return abs(a - b) / b * 100.0

    def _make(self, typ, name, direction, confidence, price, desc, signal,
              start, end, category="classic", **extra) -> Dict:
        d = {
            "type": typ,
            "name": name,
            "direction": direction,
            "confidence": confidence,
            "current_price": float(price),
            "description": desc,
            "signal": signal,
            "start_index": int(start),
            "end_index": int(end),
            "category": category,
        }
        d.update({k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in extra.items()})
        return d
    # ================================================================
    #  1) KLASIK FORMASYONLAR
    # ================================================================
    def _detect_flag(self, close, high, low, vol) -> List[Dict]:
        patterns = []
        window = 20
        if len(close) < window + 10:
            return patterns
        prev_move = close[-window] - close[-window - 10]
        prev_pct = (prev_move / close[-window - 10]) * 100
        if abs(prev_pct) < 5:
            return patterns
        last_h = high[-10:].max()
        last_l = low[-10:].min()
        cons = (last_h - last_l) / last_l * 100
        if 1.5 < cons < 5:
            d = "yukselis" if prev_pct > 0 else "dusus"
            target = close[-1] + prev_move
            vol_confirm = float(np.mean(vol[-10:])) < float(np.mean(vol[-20:-10])) * 0.8
            conf = min(95, 68 + abs(prev_pct) + (8 if vol_confirm else 0))
            patterns.append(self._make(
                "flag", f"Bayrak ({d.title()})", d, conf, close[-1],
                f"{d.title()} bayrak formasyonu. Direk: %{abs(prev_pct):.1f}. "
                f"{'Hacim onayli.' if vol_confirm else ''}",
                "Al" if d == "yukselis" else "Sat",
                len(close) - window, len(close) - 1,
                target_price=target,
                target_change=(target - close[-1]) / close[-1] * 100,
            ))
        return patterns

    def _detect_pennant(self, close, high, low, vol) -> List[Dict]:
        """Flama (Pennant) - bayrak benzeri ama ucgenimsi daralan konsolidasyon"""
        patterns = []
        if len(close) < 30:
            return patterns
        prev_move = close[-20] - close[-30]
        prev_pct = (prev_move / close[-30]) * 100
        if abs(prev_pct) < 4:
            return patterns
        highs = high[-12:]
        lows = low[-12:]
        range_start = highs[0] - lows[0]
        range_end = highs[-1] - lows[-1]
        if range_end < range_start * 0.6:
            d = "yukselis" if prev_pct > 0 else "dusus"
            target = close[-1] + prev_move
            patterns.append(self._make(
                "pennant", f"Flama ({d.title()})", d, min(88, 65 + abs(prev_pct)),
                close[-1],
                f"Dar ucgen seklinde flama. Kirilim yonunde devam beklenir.",
                "Al" if d == "yukselis" else "Sat",
                len(close) - 30, len(close) - 1, category="classic",
                target_price=target,
                target_change=(target - close[-1]) / close[-1] * 100,
            ))
        return patterns

    def _detect_triangles(self, close, pivot_highs, pivot_lows) -> List[Dict]:
        patterns = []
        n = len(close)
        rh = [i for i in pivot_highs if i >= n - 40]
        rl = [i for i in pivot_lows if i >= n - 40]
        if len(rh) < 2 or len(rl) < 2:
            return patterns
        ht = self._trend_slope(rh, close)
        lt = self._trend_slope(rl, close)
        ptype = dir_ = None
        conf = 50
        if abs(ht) < 0.5 and lt > 0.5:
            ptype, dir_, conf = "ascending_triangle", "yukselis", min(85, 60 + lt * 10)
        elif abs(lt) < 0.5 and ht < -0.5:
            ptype, dir_, conf = "descending_triangle", "dusus", min(85, 60 + abs(ht) * 10)
        elif abs(ht + lt) < 0.3 and ht < 0 and lt > 0:
            ptype, dir_, conf = "symmetrical_triangle", "belirsiz", 65
        if ptype:
            base = abs(close[rh[0]] - close[rl[0]])
            target = close[-1] + base if dir_ == "yukselis" else close[-1] - base
            sig = "Bekle" if dir_ == "belirsiz" else ("Al" if dir_ == "yukselis" else "Sat")
            patterns.append(self._make(
                ptype, f"Ucgen ({dir_.title()})", dir_, conf, close[-1],
                f"{dir_.title()} ucgen formasyonu. Taban genisligi: {base:.2f} TL",
                sig, min(rh + rl), n - 1,
                target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
            ))
        return patterns

    def _detect_head_and_shoulders(self, close, pivot_highs, pivot_lows) -> List[Dict]:
        patterns = []
        n = len(close)
        rh = [i for i in pivot_highs if i >= n - 60]
        if len(rh) >= 3:
            last3 = rh[-3:]
            hp = [close[i] for i in last3]
            if hp[1] > hp[0] and hp[1] > hp[2]:
                sd = self._pct(hp[0], hp[2])
                if sd < 5:
                    nl_idx = [i for i in pivot_lows if last3[0] < i < last3[2]]
                    nl = np.mean([close[i] for i in nl_idx]) if len(nl_idx) >= 1 else min(close[last3[0]:last3[2]])
                    h2n = hp[1] - nl
                    target = nl - h2n
                    patterns.append(self._make(
                        "head_and_shoulders", "Bas-Omuz", "dusus",
                        min(92, 75 + (5 - sd) * 3), close[-1],
                        f"Bas: {hp[1]:.2f} TL, Omuzlar: {hp[0]:.2f}/{hp[2]:.2f} TL. Boyun: {nl:.2f} TL",
                        "Sat", last3[0], n - 1,
                        neckline=nl, target_price=target,
                        target_change=(target - close[-1]) / close[-1] * 100,
                    ))
        rl = [i for i in pivot_lows if i >= n - 60]
        if len(rl) >= 3:
            last3 = rl[-3:]
            lp = [close[i] for i in last3]
            if lp[1] < lp[0] and lp[1] < lp[2]:
                sd = self._pct(lp[0], lp[2])
                if sd < 5:
                    nl_idx = [i for i in pivot_highs if last3[0] < i < last3[2]]
                    nl = np.mean([close[i] for i in nl_idx]) if len(nl_idx) >= 1 else max(close[last3[0]:last3[2]])
                    h2n = nl - lp[1]
                    target = nl + h2n
                    patterns.append(self._make(
                        "inverse_head_and_shoulders", "Ters Bas-Omuz", "yukselis",
                        min(92, 75 + (5 - sd) * 3), close[-1],
                        f"Dip: {lp[1]:.2f} TL, Omuzlar: {lp[0]:.2f}/{lp[2]:.2f} TL. Boyun: {nl:.2f} TL",
                        "Al", last3[0], n - 1,
                        neckline=nl, target_price=target,
                        target_change=(target - close[-1]) / close[-1] * 100,
                    ))
        return patterns

    def _detect_double_patterns(self, close, pivot_highs, pivot_lows) -> List[Dict]:
        patterns = []
        n = len(close)
        rh = [i for i in pivot_highs if i >= n - 50]
        if len(rh) >= 2:
            l2 = rh[-2:]
            hp = [close[i] for i in l2]
            d = self._pct(hp[0], hp[1])
            if d < 3:
                trough = min(close[l2[0]:l2[1]+1])
                target = trough - (hp[0] - trough)
                patterns.append(self._make(
                    "double_top", "Ikili Tepe", "dusus",
                    min(88, 70 + (3 - d) * 6), close[-1],
                    f"Tepe: {hp[0]:.2f}/{hp[1]:.2f} TL. Fark: %{d:.1f}. Boyun: {trough:.2f} TL",
                    "Sat", l2[0], n - 1,
                    neckline=trough, target_price=target,
                    target_change=(target - close[-1]) / close[-1] * 100,
                ))
        rl = [i for i in pivot_lows if i >= n - 50]
        if len(rl) >= 2:
            l2 = rl[-2:]
            lp = [close[i] for i in l2]
            d = self._pct(lp[0], lp[1])
            if d < 3:
                peak = max(close[l2[0]:l2[1]+1])
                target = peak + (peak - lp[0])
                patterns.append(self._make(
                    "double_bottom", "Ikili Dip", "yukselis",
                    min(88, 70 + (3 - d) * 6), close[-1],
                    f"Dip: {lp[0]:.2f}/{lp[1]:.2f} TL. Fark: %{d:.1f}. Boyun: {peak:.2f} TL",
                    "Al", l2[0], n - 1,
                    neckline=peak, target_price=target,
                    target_change=(target - close[-1]) / close[-1] * 100,
                ))
        return patterns

    def _detect_channel(self, close, high, low) -> Optional[Dict]:
        if len(close) < 30:
            return None
        w = 30
        x = np.arange(w)
        hc = np.polyfit(x, high[-w:], 1)
        lc = np.polyfit(x, low[-w:], 1)
        if abs(hc[0] - lc[0]) / (abs(hc[0]) + 1e-10) < 0.3:
            d = "yukselis" if hc[0] > 0 else ("dusus" if hc[0] < 0 else "yatay")
            return self._make(
                "channel", f"Kanal ({d.title()})", d, 72, close[-1],
                f"Paralel kanal. Egim: {hc[0]:.3f}",
                "Izle", len(close) - w, len(close) - 1,
                upper_channel=np.polyval(hc, w - 1),
                lower_channel=np.polyval(lc, w - 1),
            )
        return None

    def _detect_wedge(self, close, pivot_highs, pivot_lows) -> Optional[Dict]:
        n = len(close)
        rh = [i for i in pivot_highs if i >= n - 40]
        rl = [i for i in pivot_lows if i >= n - 40]
        if len(rh) < 2 or len(rl) < 2:
            return None
        ht = self._trend_slope(rh, close)
        lt = self._trend_slope(rl, close)
        if (ht > 0 and lt > 0 and lt > ht) or (ht < 0 and lt < 0 and lt < ht):
            wt = "yukselen" if ht > 0 else "dusen"
            sd = "dusus" if wt == "yukselen" else "yukselis"
            return self._make(
                "wedge", f"Kama ({wt.title()})", sd, 75, close[-1],
                f"{wt.title()} kama. Ust egim: {ht:.3f}, Alt egim: {lt:.3f}",
                "Al" if sd == "yukselis" else "Sat",
                min(rh + rl), n - 1,
            )
        return None
    # ================================================================
    #  2) GELISMIS FORMASYONLAR
    # ================================================================
    def _detect_triple_patterns(self, close, pivot_highs, pivot_lows) -> List[Dict]:
        """Uclu Tepe / Uclu Dip"""
        patterns = []
        n = len(close)
        rh = [i for i in pivot_highs if i >= n - 70]
        if len(rh) >= 3:
            last3 = rh[-3:]
            hp = [close[i] for i in last3]
            diffs = [self._pct(hp[0], hp[1]), self._pct(hp[1], hp[2]), self._pct(hp[0], hp[2])]
            if all(d < 3 for d in diffs):
                trough = min(close[last3[0]:last3[2]+1])
                target = trough - (np.mean(hp) - trough)
                patterns.append(self._make(
                    "triple_top", "Uclu Tepe", "dusus",
                    min(93, 78 + (3 - max(diffs)) * 5), close[-1],
                    f"3 yakin zirve: {hp[0]:.2f}/{hp[1]:.2f}/{hp[2]:.2f} TL. Guclu direnc.",
                    "Sat", last3[0], n - 1, category="advanced",
                    neckline=trough, target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
                ))
        rl = [i for i in pivot_lows if i >= n - 70]
        if len(rl) >= 3:
            last3 = rl[-3:]
            lp = [close[i] for i in last3]
            diffs = [self._pct(lp[0], lp[1]), self._pct(lp[1], lp[2]), self._pct(lp[0], lp[2])]
            if all(d < 3 for d in diffs):
                peak = max(close[last3[0]:last3[2]+1])
                target = peak + (peak - np.mean(lp))
                patterns.append(self._make(
                    "triple_bottom", "Uclu Dip", "yukselis",
                    min(93, 78 + (3 - max(diffs)) * 5), close[-1],
                    f"3 yakin dip: {lp[0]:.2f}/{lp[1]:.2f}/{lp[2]:.2f} TL. Guclu destek.",
                    "Al", last3[0], n - 1, category="advanced",
                    neckline=peak, target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
                ))
        return patterns

    def _detect_cup_and_handle(self, close, pivot_highs, pivot_lows) -> Optional[Dict]:
        """Fincan ve Kulp (Cup & Handle) formasyonu"""
        n = len(close)
        if n < 40:
            return None
        rl = [i for i in pivot_lows if i >= n - 60]
        rh = [i for i in pivot_highs if i >= n - 60]
        if len(rl) < 1 or len(rh) < 2:
            return None
        if len(rh) >= 2 and len(rl) >= 1:
            cup_left = rh[-2]
            cup_right = rh[-1]
            cup_bottom_candidates = [i for i in rl if cup_left < i < cup_right]
            if not cup_bottom_candidates:
                return None
            cup_bottom = min(cup_bottom_candidates, key=lambda i: close[i])
            left_price = close[cup_left]
            right_price = close[cup_right]
            bottom_price = close[cup_bottom]
            lip_diff = self._pct(left_price, right_price)
            if lip_diff > 8:
                return None
            depth = (left_price - bottom_price) / left_price * 100
            if 10 < depth < 35:
                handle_depth = (right_price - close[-1]) / right_price * 100
                if 0 < handle_depth < depth * 0.5:
                    target = right_price + (right_price - bottom_price)
                    return self._make(
                        "cup_and_handle", "Fincan ve Kulp", "yukselis",
                        min(90, 72 + (35 - depth) * 0.5), close[-1],
                        f"Fincan derinligi: %{depth:.1f}. Kulp: %{handle_depth:.1f}. "
                        f"Dudak: {left_price:.2f}/{right_price:.2f} TL",
                        "Al", cup_left, n - 1, category="advanced",
                        target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
                    )
        return None

    def _detect_rectangle(self, close, high, low) -> Optional[Dict]:
        """Dikdortgen (Rectangle) formasyonu - yatay kanal"""
        if len(close) < 25:
            return None
        w = 25
        rh = high[-w:]
        rl = low[-w:]
        top = np.percentile(rh, 90)
        bottom = np.percentile(rl, 10)
        range_pct = (top - bottom) / bottom * 100
        if 2 < range_pct < 8:
            touches_top = sum(1 for h in rh if abs(h - top) / top < 0.01)
            touches_bot = sum(1 for l in rl if abs(l - bottom) / bottom < 0.01)
            if touches_top >= 2 and touches_bot >= 2:
                pos = (close[-1] - bottom) / (top - bottom)
                d = "yukselis" if pos > 0.6 else ("dusus" if pos < 0.4 else "belirsiz")
                target = top + (top - bottom) if d == "yukselis" else bottom - (top - bottom)
                return self._make(
                    "rectangle", "Dikdortgen", d, 68, close[-1],
                    f"Yatay kanal {bottom:.2f} - {top:.2f} TL. Aralik: %{range_pct:.1f}",
                    "Al" if d == "yukselis" else ("Sat" if d == "dusus" else "Bekle"),
                    len(close) - w, len(close) - 1, category="advanced",
                    upper_channel=top, lower_channel=bottom,
                    target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
                )
        return None

    def _detect_rounding(self, close, pivot_lows) -> Optional[Dict]:
        """Yuvarlanan Dip (Rounding Bottom) formasyonu"""
        n = len(close)
        if n < 50:
            return None
        w = 50
        seg = close[-w:]
        mid = w // 2
        left_avg = np.mean(seg[:15])
        mid_avg = np.mean(seg[mid - 7:mid + 7])
        right_avg = np.mean(seg[-15:])
        if mid_avg < left_avg * 0.97 and mid_avg < right_avg * 0.97:
            if right_avg >= left_avg * 0.95:
                depth = (left_avg - mid_avg) / left_avg * 100
                if 3 < depth < 25:
                    target = right_avg + (right_avg - mid_avg)
                    return self._make(
                        "rounding_bottom", "Yuvarlanan Dip", "yukselis",
                        min(80, 60 + depth), close[-1],
                        f"U seklinde yumusak dip. Derinlik: %{depth:.1f}",
                        "Al", n - w, n - 1, category="advanced",
                        target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
                    )
        return None

    def _detect_broadening(self, close, pivot_highs, pivot_lows) -> Optional[Dict]:
        """Genisleyen Formasyon (Broadening / Megaphone)"""
        n = len(close)
        rh = [i for i in pivot_highs if i >= n - 40]
        rl = [i for i in pivot_lows if i >= n - 40]
        if len(rh) < 2 or len(rl) < 2:
            return None
        ht = self._trend_slope(rh, close)
        lt = self._trend_slope(rl, close)
        if ht > 0 and lt < 0:
            return self._make(
                "broadening", "Genisleyen Formasyon", "belirsiz", 62, close[-1],
                f"Megafon seklinde genisleyen kanal. Volatilite artisi.",
                "Izle", min(rh + rl), n - 1, category="advanced",
            )
        return None
    # ================================================================
    #  3) BOSLUK FORMASYONLARI
    # ================================================================
    def _detect_gaps(self, opn, close, high, low, vol) -> List[Dict]:
        patterns = []
        n = len(close)
        if n < 5:
            return patterns

        for i in range(max(1, n - 5), n):
            gap_up = low[i] > high[i - 1]
            gap_down = high[i] < low[i - 1]
            if not gap_up and not gap_down:
                continue
            gap_size_pct = 0
            if gap_up:
                gap_size_pct = (low[i] - high[i - 1]) / high[i - 1] * 100
            else:
                gap_size_pct = (low[i - 1] - high[i]) / low[i - 1] * 100

            if abs(gap_size_pct) < 1:
                continue

            vol_spike = vol[i] > np.mean(vol[max(0, i - 20):i]) * 1.5 if i >= 2 else False
            trend_up = close[i] > np.mean(close[max(0, i - 20):i]) if i >= 5 else True

            if gap_up:
                if vol_spike and trend_up:
                    gtype, gname = "breakaway_gap_up", "Koparma Boslugu (Yukari)"
                    desc = f"Guclu hacimle yukari bosluk. Yeni trendin baslangici olabilir."
                    sig = "Al"
                elif not vol_spike:
                    gtype, gname = "common_gap_up", "Yaygin Bosluk (Yukari)"
                    desc = f"Normal piyasa acilis boslugu. Genelde kapanir."
                    sig = "Izle"
                else:
                    gtype, gname = "runaway_gap_up", "Kacis Boslugu (Yukari)"
                    desc = f"Trend ortasinda guclu bosluk. Trend devami beklenir."
                    sig = "Al"
                direction = "yukselis"
            else:
                if vol_spike and not trend_up:
                    gtype, gname = "breakaway_gap_down", "Koparma Boslugu (Asagi)"
                    desc = f"Guclu hacimle asagi bosluk. Dusus trendi baslangici."
                    sig = "Sat"
                elif not vol_spike:
                    gtype, gname = "common_gap_down", "Yaygin Bosluk (Asagi)"
                    desc = f"Normal dusus boslugu. Genelde kapanir."
                    sig = "Izle"
                else:
                    gtype, gname = "runaway_gap_down", "Kacis Boslugu (Asagi)"
                    desc = f"Dusus trendinde guclu bosluk. Dusus devami beklenir."
                    sig = "Sat"
                direction = "dusus"

            patterns.append(self._make(
                gtype, gname, direction,
                min(88, 55 + abs(gap_size_pct) * 5 + (10 if vol_spike else 0)),
                close[-1],
                f"{desc} Bosluk: %{gap_size_pct:.2f}",
                sig, i - 1, i, category="gap",
                gap_size=gap_size_pct,
            ))

        # Ada Donusu (Island Reversal)
        if n >= 10:
            for i in range(n - 8, n - 2):
                if i < 1:
                    continue
                gap1_up = low[i] > high[i - 1]
                gap1_down = high[i] < low[i - 1]
                if not gap1_up and not gap1_down:
                    continue
                for j in range(i + 2, min(i + 7, n)):
                    gap2_up = low[j] > high[j - 1]
                    gap2_down = high[j] < low[j - 1]
                    if gap1_up and gap2_down:
                        patterns.append(self._make(
                            "island_reversal_top", "Ada Donusu (Tepe)", "dusus",
                            80, close[-1],
                            f"Yukari boslukla ayrilmis fiyat adasi sonrasi asagi bosluk. Guclu donus sinyali.",
                            "Sat", i - 1, j, category="gap",
                        ))
                        break
                    elif gap1_down and gap2_up:
                        patterns.append(self._make(
                            "island_reversal_bottom", "Ada Donusu (Dip)", "yukselis",
                            80, close[-1],
                            f"Asagi boslukla ayrilmis fiyat adasi sonrasi yukari bosluk. Guclu donus sinyali.",
                            "Al", i - 1, j, category="gap",
                        ))
                        break
        return patterns
    # ================================================================
    #  4) HARMONIK FORMASYONLAR
    # ================================================================
    def _detect_harmonic_patterns(self, close, fine_highs, fine_lows) -> List[Dict]:
        """Harmonik formasyonlar: ABCD, Gartley, Butterfly, Bat, Crab"""
        patterns = []
        n = len(close)
        if n < 20:
            return patterns

        all_pivots = []
        for idx in fine_highs:
            all_pivots.append((idx, close[idx], "H"))
        for idx in fine_lows:
            all_pivots.append((idx, close[idx], "L"))
        all_pivots.sort(key=lambda x: x[0])

        recent = all_pivots[-8:] if len(all_pivots) >= 5 else all_pivots
        if len(recent) < 5:
            return patterns

        for i in range(len(recent) - 4):
            X, A, B, C, D = recent[i:i + 5]
            xa = abs(A[1] - X[1])
            ab = abs(B[1] - A[1])
            bc = abs(C[1] - B[1])
            cd = abs(D[1] - C[1])

            if xa == 0 or ab == 0 or bc == 0:
                continue

            ab_xa = ab / xa
            bc_ab = bc / ab
            cd_bc = cd / bc

            bullish = D[2] == "L"

            # Gartley (222 Gartley)
            if 0.58 <= ab_xa <= 0.68 and 0.38 <= bc_ab <= 0.88 and 1.13 <= cd_bc <= 1.62:
                direction = "yukselis" if bullish else "dusus"
                target = D[1] + (0.786 * xa if bullish else -0.786 * xa)
                patterns.append(self._make(
                    "gartley", f"Gartley ({direction.title()})", direction, 82, close[-1],
                    f"Harmonik Gartley. AB/XA: {ab_xa:.2f}, BC/AB: {bc_ab:.2f}, CD/BC: {cd_bc:.2f}",
                    "Al" if bullish else "Sat", X[0], D[0], category="harmonic",
                    target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
                ))
                continue

            # Butterfly (Kelebek)
            if 0.73 <= ab_xa <= 0.83 and 0.38 <= bc_ab <= 0.88 and 1.62 <= cd_bc <= 2.62:
                direction = "yukselis" if bullish else "dusus"
                target = D[1] + (0.618 * xa if bullish else -0.618 * xa)
                patterns.append(self._make(
                    "butterfly", f"Kelebek ({direction.title()})", direction, 78, close[-1],
                    f"Harmonik Kelebek. AB/XA: {ab_xa:.2f}, BC/AB: {bc_ab:.2f}",
                    "Al" if bullish else "Sat", X[0], D[0], category="harmonic",
                    target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
                ))
                continue

            # Bat (Yarasa)
            if 0.38 <= ab_xa <= 0.50 and 0.38 <= bc_ab <= 0.88 and 1.62 <= cd_bc <= 2.62:
                direction = "yukselis" if bullish else "dusus"
                target = D[1] + (0.886 * xa if bullish else -0.886 * xa)
                patterns.append(self._make(
                    "bat", f"Yarasa ({direction.title()})", direction, 76, close[-1],
                    f"Harmonik Yarasa. AB/XA: {ab_xa:.2f}, BC/AB: {bc_ab:.2f}",
                    "Al" if bullish else "Sat", X[0], D[0], category="harmonic",
                    target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
                ))
                continue

            # Crab (Yengec)
            if 0.38 <= ab_xa <= 0.62 and 0.38 <= bc_ab <= 0.88 and 2.62 <= cd_bc <= 3.62:
                direction = "yukselis" if bullish else "dusus"
                target = D[1] + (0.618 * xa if bullish else -0.618 * xa)
                patterns.append(self._make(
                    "crab", f"Yengec ({direction.title()})", direction, 74, close[-1],
                    f"Harmonik Yengec. AB/XA: {ab_xa:.2f}, CD/BC: {cd_bc:.2f}",
                    "Al" if bullish else "Sat", X[0], D[0], category="harmonic",
                    target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
                ))
                continue

        # ABCD Paterni (4 nokta)
        if len(recent) >= 4:
            for i in range(len(recent) - 3):
                A, B, C, D = recent[i:i + 4]
                ab = abs(B[1] - A[1])
                bc = abs(C[1] - B[1])
                cd = abs(D[1] - C[1])
                if ab == 0 or bc == 0:
                    continue
                bc_ab_r = bc / ab
                cd_bc_r = cd / bc
                if 0.55 <= bc_ab_r <= 0.75 and 1.13 <= cd_bc_r <= 1.75:
                    bullish = D[2] == "L"
                    direction = "yukselis" if bullish else "dusus"
                    target = D[1] + (ab * 0.618 if bullish else -ab * 0.618)
                    patterns.append(self._make(
                        "abcd", f"ABCD ({direction.title()})", direction, 70, close[-1],
                        f"ABCD harmonik. BC/AB: {bc_ab_r:.2f}, CD/BC: {cd_bc_r:.2f}",
                        "Al" if bullish else "Sat", A[0], D[0], category="harmonic",
                        target_price=target, target_change=(target - close[-1]) / close[-1] * 100,
                    ))

        return patterns
    # ================================================================
    #  5) FIBONACCI ANALIZI
    # ================================================================
    def _calculate_fibonacci(self, close, high, low) -> Dict[str, Any]:
        """Fibonacci retracement ve extension seviyeleri"""
        n = len(close)
        if n < 20:
            return {}
        w = min(60, n)
        seg_high = high[-w:]
        seg_low = low[-w:]
        swing_h = float(seg_high.max())
        swing_l = float(seg_low.min())
        diff = swing_h - swing_l

        current = float(close[-1])
        mid = (swing_h + swing_l) / 2
        trend = "yukselis" if current > mid else "dusus"

        fib_levels = {}
        retracement_ratios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        extension_ratios = [1.272, 1.618, 2.0, 2.618]

        if trend == "yukselis":
            for r in retracement_ratios:
                fib_levels[f"ret_{r}"] = {"ratio": r, "price": round(swing_h - diff * r, 2), "label": f"%{r*100:.1f}"}
            for r in extension_ratios:
                fib_levels[f"ext_{r}"] = {"ratio": r, "price": round(swing_l + diff * r, 2), "label": f"%{r*100:.1f} Ext"}
        else:
            for r in retracement_ratios:
                fib_levels[f"ret_{r}"] = {"ratio": r, "price": round(swing_l + diff * r, 2), "label": f"%{r*100:.1f}"}
            for r in extension_ratios:
                fib_levels[f"ext_{r}"] = {"ratio": r, "price": round(swing_h - diff * r, 2), "label": f"%{r*100:.1f} Ext"}

        closest = min(fib_levels.values(), key=lambda x: abs(x["price"] - current))

        return {
            "swing_high": swing_h,
            "swing_low": swing_l,
            "trend": trend,
            "current_price": current,
            "closest_level": closest,
            "levels": fib_levels,
        }

    # ================================================================
    #  6) DESTEK / DIRENC TESPITI
    # ================================================================
    def _detect_support_resistance(self, close, high, low, pivot_highs, pivot_lows) -> Dict[str, Any]:
        n = len(close)
        current = float(close[-1])

        resistance_levels = []
        support_levels = []

        for i in pivot_highs:
            price = float(high[i])
            touches = sum(1 for h in high if abs(h - price) / price < 0.015)
            resistance_levels.append({"price": round(price, 2), "strength": touches, "index": int(i)})

        for i in pivot_lows:
            price = float(low[i])
            touches = sum(1 for l in low if abs(l - price) / price < 0.015)
            support_levels.append({"price": round(price, 2), "strength": touches, "index": int(i)})

        resistance_levels = self._merge_levels(resistance_levels)
        support_levels = self._merge_levels(support_levels)

        resistance_levels.sort(key=lambda x: x["strength"], reverse=True)
        support_levels.sort(key=lambda x: x["strength"], reverse=True)

        resistances = [r for r in resistance_levels if r["price"] > current][:5]
        supports = [s for s in support_levels if s["price"] < current][:5]

        nearest_resistance = min(resistances, key=lambda x: x["price"]) if resistances else None
        nearest_support = max(supports, key=lambda x: x["price"]) if supports else None

        return {
            "current_price": current,
            "resistances": resistances,
            "supports": supports,
            "nearest_resistance": nearest_resistance,
            "nearest_support": nearest_support,
        }

    @staticmethod
    def _merge_levels(levels: List[Dict], threshold: float = 0.02) -> List[Dict]:
        if not levels:
            return []
        levels.sort(key=lambda x: x["price"])
        merged = [levels[0]]
        for lv in levels[1:]:
            if abs(lv["price"] - merged[-1]["price"]) / merged[-1]["price"] < threshold:
                merged[-1]["strength"] += lv["strength"]
                merged[-1]["price"] = (merged[-1]["price"] + lv["price"]) / 2
            else:
                merged.append(lv)
        return merged
    # ================================================================
    #  7) HACIM FORMASYONLARI
    # ================================================================
    def _detect_volume_patterns(self, close, vol) -> List[Dict]:
        patterns = []
        n = len(close)
        if n < 20:
            return patterns

        avg_vol = np.mean(vol[-20:])
        last_vol = vol[-1]

        # Volume Climax (Hacim Zirvesi)
        if last_vol > avg_vol * 3:
            price_change = (close[-1] - close[-2]) / close[-2] * 100
            d = "yukselis" if price_change > 0 else "dusus"
            patterns.append(self._make(
                "volume_climax", "Hacim Zirvesi", d,
                min(85, 65 + (last_vol / avg_vol) * 3), close[-1],
                f"Ortalama hacmin {last_vol/avg_vol:.1f}x kati! Fiyat degisimi: %{price_change:.2f}. "
                f"Trend sonu veya guclu devam olabilir.",
                "Izle", n - 2, n - 1, category="volume",
                volume_ratio=last_vol / avg_vol,
            ))

        # Accumulation / Distribution (Biriktirme-Dagitim)
        if n >= 15:
            recent_close = close[-15:]
            recent_vol = vol[-15:]
            price_trend = (recent_close[-1] - recent_close[0]) / recent_close[0] * 100
            vol_trend = (np.mean(recent_vol[-5:]) - np.mean(recent_vol[:5])) / np.mean(recent_vol[:5]) * 100

            if price_trend < -2 and vol_trend > 20:
                patterns.append(self._make(
                    "accumulation", "Biriktirme Sinyali", "yukselis", 65, close[-1],
                    f"Dusen fiyat + artan hacim: Akilli para biriktirme yapiyor olabilir.",
                    "Al", n - 15, n - 1, category="volume",
                ))
            elif price_trend > 2 and vol_trend < -20:
                patterns.append(self._make(
                    "distribution", "Dagitim Sinyali", "dusus", 65, close[-1],
                    f"Yukselen fiyat + azalan hacim: Dagitim sinyali.",
                    "Sat", n - 15, n - 1, category="volume",
                ))

        # Volume Dry-Up (Hacim Kurumasi)
        if n >= 10:
            last5_vol = np.mean(vol[-5:])
            prev_vol = np.mean(vol[-15:-5]) if n >= 15 else avg_vol
            if prev_vol > 0 and last5_vol < prev_vol * 0.4:
                patterns.append(self._make(
                    "volume_dryup", "Hacim Kurumasi", "belirsiz", 60, close[-1],
                    f"Son 5 bar hacmi onceki doneme gore %{(1-last5_vol/prev_vol)*100:.0f} dustu. "
                    f"Guclu bir kirilim hazirligi olabilir.",
                    "Bekle", n - 5, n - 1, category="volume",
                ))

        return patterns
    # ================================================================
    #  8) MUM CUBUK FORMASYONLARI
    # ================================================================
    def _detect_candlestick_patterns(self, opn, close, high, low) -> List[Dict]:
        patterns = []
        n = len(close)
        if n < 3:
            return patterns

        for i in range(max(2, n - 3), n):
            body = close[i] - opn[i]
            body_abs = abs(body)
            upper_shadow = high[i] - max(opn[i], close[i])
            lower_shadow = min(opn[i], close[i]) - low[i]
            total_range = high[i] - low[i]
            if total_range == 0:
                continue
            body_ratio = body_abs / total_range
            prev_body = close[i - 1] - opn[i - 1] if i > 0 else 0

            # --- Doji ---
            if body_ratio < 0.1:
                doji_type = "Standart Doji"
                if upper_shadow > body_abs * 3 and lower_shadow < body_abs:
                    doji_type = "Mezar Tasi Doji"
                elif lower_shadow > body_abs * 3 and upper_shadow < body_abs:
                    doji_type = "Yusufcuk Doji"
                elif upper_shadow > body_abs * 2 and lower_shadow > body_abs * 2:
                    doji_type = "Uzun Bacakli Doji"
                patterns.append(self._make(
                    "doji", doji_type, "belirsiz", 60, close[-1],
                    f"Kararsizlik sinyali. Alici-satici dengesi. Trend donusunun habercisi olabilir.",
                    "Bekle", i, i, category="candlestick",
                ))

            # --- Cekic (Hammer) / Asili Adam ---
            elif lower_shadow > body_abs * 2 and upper_shadow < body_abs * 0.5 and body_abs > 0:
                is_downtrend = close[i] < np.mean(close[max(0, i - 10):i]) if i >= 5 else False
                if is_downtrend:
                    patterns.append(self._make(
                        "hammer", "Cekic", "yukselis", 72, close[-1],
                        f"Alt golge govdenin {lower_shadow/body_abs:.1f}x kati. "
                        f"Dusus trendinde dip sinyali.",
                        "Al", i, i, category="candlestick",
                    ))
                else:
                    patterns.append(self._make(
                        "hanging_man", "Asili Adam", "dusus", 68, close[-1],
                        f"Uzun alt golge. Yukselis trendinde zirve uyarisi.",
                        "Sat", i, i, category="candlestick",
                    ))

            # --- Ters Cekic / Kayan Yildiz ---
            elif upper_shadow > body_abs * 2 and lower_shadow < body_abs * 0.5 and body_abs > 0:
                is_uptrend = close[i] > np.mean(close[max(0, i - 10):i]) if i >= 5 else False
                if is_uptrend:
                    patterns.append(self._make(
                        "shooting_star", "Kayan Yildiz", "dusus", 72, close[-1],
                        f"Ust golge govdenin {upper_shadow/body_abs:.1f}x kati. "
                        f"Yukselis trendinde satis baskisi.",
                        "Sat", i, i, category="candlestick",
                    ))
                else:
                    patterns.append(self._make(
                        "inverted_hammer", "Ters Cekic", "yukselis", 68, close[-1],
                        f"Uzun ust golge. Dusus trendinde alim ilgisi sinyali.",
                        "Al", i, i, category="candlestick",
                    ))

            # --- Marubozu (govde hakim, golge yok) ---
            elif body_ratio > 0.85:
                if body > 0:
                    patterns.append(self._make(
                        "bullish_marubozu", "Yukselis Marubozu", "yukselis", 75, close[-1],
                        f"Neredeyse golgesiz guclu yukselis mumu. Alici dominasyonu.",
                        "Al", i, i, category="candlestick",
                    ))
                else:
                    patterns.append(self._make(
                        "bearish_marubozu", "Dusus Marubozu", "dusus", 75, close[-1],
                        f"Neredeyse golgesiz guclu dusus mumu. Satici dominasyonu.",
                        "Sat", i, i, category="candlestick",
                    ))

            # --- Engulfing (Yutan Formasyon) --- 2 mum
            if i >= 1:
                prev_body_abs = abs(prev_body)
                if body_abs > prev_body_abs * 1.3:
                    if body > 0 and prev_body < 0:
                        if opn[i] <= close[i - 1] and close[i] >= opn[i - 1]:
                            patterns.append(self._make(
                                "bullish_engulfing", "Yukselis Yutan", "yukselis", 78, close[-1],
                                f"Yesil mum onceki kirmiziyi tamamen yutuyor. Guclu donus sinyali.",
                                "Al", i - 1, i, category="candlestick",
                            ))
                    elif body < 0 and prev_body > 0:
                        if opn[i] >= close[i - 1] and close[i] <= opn[i - 1]:
                            patterns.append(self._make(
                                "bearish_engulfing", "Dusus Yutan", "dusus", 78, close[-1],
                                f"Kirmizi mum onceki yesili tamamen yutuyor. Guclu dusus sinyali.",
                                "Sat", i - 1, i, category="candlestick",
                            ))

            # --- Morning Star / Evening Star --- 3 mum
            if i >= 2:
                body_1 = close[i - 2] - opn[i - 2]
                body_2 = close[i - 1] - opn[i - 1]
                body_3 = body
                body_2_abs = abs(body_2)
                range_1 = high[i - 2] - low[i - 2]

                if range_1 > 0:
                    if body_1 < 0 and abs(body_1) > range_1 * 0.5 and body_2_abs < abs(body_1) * 0.3 and body_3 > 0 and body_3 > abs(body_1) * 0.5:
                        patterns.append(self._make(
                            "morning_star", "Sabah Yildizi", "yukselis", 82, close[-1],
                            f"Klasik 3 mumlu donus formasyonu. Guclu yukselis sinyali.",
                            "Al", i - 2, i, category="candlestick",
                        ))
                    elif body_1 > 0 and body_1 > range_1 * 0.5 and body_2_abs < body_1 * 0.3 and body_3 < 0 and abs(body_3) > body_1 * 0.5:
                        patterns.append(self._make(
                            "evening_star", "Aksam Yildizi", "dusus", 82, close[-1],
                            f"Klasik 3 mumlu zirve formasyonu. Guclu dusus sinyali.",
                            "Sat", i - 2, i, category="candlestick",
                        ))

            # --- Three White Soldiers / Three Black Crows --- (3 mum)
            if i >= 2:
                b1 = close[i - 2] - opn[i - 2]
                b2 = close[i - 1] - opn[i - 1]
                b3 = body
                if b1 > 0 and b2 > 0 and b3 > 0 and close[i - 1] > close[i - 2] and close[i] > close[i - 1]:
                    patterns.append(self._make(
                        "three_white_soldiers", "Uc Beyaz Asker", "yukselis", 80, close[-1],
                        f"Ardisik 3 guclu yukselis mumu. Guclu alim baskisi.",
                        "Al", i - 2, i, category="candlestick",
                    ))
                elif b1 < 0 and b2 < 0 and b3 < 0 and close[i - 1] < close[i - 2] and close[i] < close[i - 1]:
                    patterns.append(self._make(
                        "three_black_crows", "Uc Kara Karga", "dusus", 80, close[-1],
                        f"Ardisik 3 guclu dusus mumu. Guclu satis baskisi.",
                        "Sat", i - 2, i, category="candlestick",
                    ))

            # --- Harami (Icsel Bar) ---
            if i >= 1 and body_abs > 0:
                prev_high_body = max(opn[i - 1], close[i - 1])
                prev_low_body = min(opn[i - 1], close[i - 1])
                curr_high_body = max(opn[i], close[i])
                curr_low_body = min(opn[i], close[i])
                if curr_high_body < prev_high_body and curr_low_body > prev_low_body:
                    if body > 0 and prev_body < 0:
                        patterns.append(self._make(
                            "bullish_harami", "Yukselis Harami", "yukselis", 65, close[-1],
                            f"Onceki mum icinde kucuk yesil mum. Kararsizlik sonrasi donus.",
                            "Al", i - 1, i, category="candlestick",
                        ))
                    elif body < 0 and prev_body > 0:
                        patterns.append(self._make(
                            "bearish_harami", "Dusus Harami", "dusus", 65, close[-1],
                            f"Onceki mum icinde kucuk kirmizi mum. Kararsizlik sonrasi dusus.",
                            "Sat", i - 1, i, category="candlestick",
                        ))

            # --- Tweezer Top / Bottom (Cimbiz) ---
            if i >= 1:
                if abs(high[i] - high[i - 1]) / high[i] < 0.003:
                    if prev_body > 0 and body < 0:
                        patterns.append(self._make(
                            "tweezer_top", "Cimbiz Tepe", "dusus", 68, close[-1],
                            f"Iki mumun tepesi ayni seviyede. Direnc teyidi.",
                            "Sat", i - 1, i, category="candlestick",
                        ))
                if abs(low[i] - low[i - 1]) / low[i] < 0.003:
                    if prev_body < 0 and body > 0:
                        patterns.append(self._make(
                            "tweezer_bottom", "Cimbiz Dip", "yukselis", 68, close[-1],
                            f"Iki mumun dibi ayni seviyede. Destek teyidi.",
                            "Al", i - 1, i, category="candlestick",
                        ))

        return patterns

    # ================================================================
    #  OZET
    # ================================================================
    def _generate_summary(self, patterns: List[Dict]) -> str:
        if not patterns:
            return "Belirgin formasyon tespit edilmedi."
        al = sum(1 for p in patterns if p.get("signal") == "Al")
        sat = sum(1 for p in patterns if p.get("signal") == "Sat")
        categories = set(p.get("category", "classic") for p in patterns)
        cat_names = [self.PATTERN_CATEGORIES.get(c, c) for c in categories]
        base = f"{len(patterns)} formasyon tespit edildi ({', '.join(cat_names)})."
        if al > sat:
            return f"{base} Agirlikli ALIS sinyali ({al} al / {sat} sat)."
        elif sat > al:
            return f"{base} Agirlikli SATIS sinyali ({sat} sat / {al} al)."
        return f"{base} Karma sinyal ({al} al / {sat} sat)."