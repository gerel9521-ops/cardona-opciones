"""
Método Cardona — Motor completo de detección CALL/PUT.
Códigos oficiales (adaptación Frank Soto / Seminario Creando Riqueza).
Lógica determinista aproximada; herramienta educativa — no es asesoría financiera.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import math

import numpy as np
import pandas as pd


STRATEGIES_CATALOG: list[dict[str, Any]] = [
    {"code": "1V-R", "name": "1ra Vela Roja", "direction": "PUT", "timeframe": "1h",
     "entry_time": "Solo a las 10:00 ET (única excepción de apertura)",
     "summary": "Canal bajista, precio cerca/bajo PM40; primera vela roja horaria completada tras apertura NY → PUT a las 10am."},
    {"code": "RP-GAP", "name": "Ruptura del Piso del GAP", "direction": "PUT", "timeframe": "1h",
     "entry_time": "Desde las 11:00 ET",
     "summary": "Gap/vela verde de apertura; dibujar piso del gap (con mecha); vela roja rompe ese piso → PUT."},
    {"code": "4P", "name": "Modelo 4 pasos (verde-rojo rompe)", "direction": "PUT", "timeframe": "1h",
     "entry_time": "Desde las 11:00 ET",
     "summary": "Canal bajista en zona cara (cerca techo); verde borrada por roja(s) o hanger; piso del rebote; roja rompe piso → PUT."},
    {"code": "HD", "name": "Hanger en Diario", "direction": "PUT", "timeframe": "1d",
     "entry_time": "~2–3 días después del hanger",
     "summary": "Hombre colgado diario en zona cara; secuencia hanger → verde baja vol → roja → caída. PUT."},
    {"code": "VRF-E", "name": "Vela Roja Final Envolvente del Día", "direction": "PUT", "timeframe": "1d",
     "entry_time": "Cierre diario / siguiente apertura según confirmación",
     "summary": "Envolvente bajista diaria en zona cara/techo con alto volumen → PUT."},
    {"code": "RT", "name": "Ruptura del Techo", "direction": "CALL", "timeframe": "1h",
     "entry_time": "11:00–15:59 ET",
     "summary": "Caída con ≥2 rojas tocando/rompiendo PM20/PM40; martillo verde + vela verde con volumen rompe línea de techo → CALL."},
    {"code": "PM-40H", "name": "Promedio Móvil 40 Hora", "direction": "CALL", "timeframe": "1h",
     "entry_time": "11:00–15:59 ET",
     "summary": "Tendencia alcista (PM20>PM40); rojas rompen PM20 y tocan/rompen parcialmente PM40; verde final rompe PM20 otra vez → CALL (1–2 días)."},
    {"code": "CN", "name": "Caída Normal", "direction": "CALL", "timeframe": "1h",
     "entry_time": "Preferible 11:00–15:59 (esp. viernes)",
     "summary": "Caída ~$3–5 o <1.5%; 2–3 rojas rompen PM20 pero NO PM40; martillo + verde rompe techo de caída → CALL."},
    {"code": "CF", "name": "Caída Fuerte", "direction": "CALL", "timeframe": "1h",
     "entry_time": "11:00–15:59 ET",
     "summary": "Caída >$6 o >1.5%; rojas rompen PM20/PM40/PM100/PM200; martillo + verde rompe techo → CALL."},
    {"code": "RCB", "name": "Ruptura Canal Bajista (mejor CALL)", "direction": "CALL", "timeframe": "1h",
     "entry_time": "11:00–15:59 ET",
     "summary": "Canal bajista 1–4 meses; PM40>PM20 cruzado; martillo + verde con volumen rompe techo del canal → CALL. No comprar CALL dentro del canal sin ruptura."},
    {"code": "GAP-NA", "name": "GAP Normal al Alza", "direction": "CALL", "timeframe": "1h",
     "entry_time": "~11:00–12:00 ET",
     "summary": "Sesgo alcista previo; gap up verde 9:30 + verde/martillo 10am; vela 11am verde o roja alto vol → CALL ~11–12."},
    {"code": "GAP-BA", "name": "GAP Bajista al Alza", "direction": "CALL", "timeframe": "1h",
     "entry_time": "Tras confirmar 2ª/3ª vela (~11am)",
     "summary": "Cierre previo verde; abre abajo pero 1ª verde, 2ª (10am) DEBE ser verde, 3ª verde o alto vol → CALL (3–4 días en canal bajista)."},
    {"code": "PF", "name": "Piso Fuerte", "direction": "CALL", "timeframe": "1d + 1h",
     "entry_time": "Tras ruptura horaria del canal",
     "summary": "Diario toca PM100/PM200; en 1h rompe techo canal bajista; confirmar cerca PM40 diario → CALL 3–5 días."},
    {"code": "TF", "name": "Techo Fuerte", "direction": "PUT", "timeframe": "1d",
     "entry_time": "Contexto / con hanger o SPY",
     "summary": "Zona de techo caro: sesgo PUT / precaución en CALLs. Emparejar con hanger y reglas SPY."},
    {"code": "1GAP-A", "name": "1er GAP al Alza", "direction": "CALL", "timeframe": "1d + 1h",
     "entry_time": "Tras PF + gap; validar piso del gap y cierre",
     "summary": "Tras ruptura PF, primer gap verde al alza; piso del gap respetado; volumen; condiciones de cierre → CALL 3–4 días."},
    {"code": "3SEM", "name": "Estrategia de las 3 semanas", "direction": "CALL|PUT", "timeframe": "1wk (semanal)",
     "entry_time": "≈15:55 ET (≈5 min antes del cierre cash US)",
     "summary": "Setup de gran recorrido en gráfica SEMANAL (piso barato / techo caro / ruptura); compra ~15:55 ET; vencimiento ~3 semanas; CALL o PUT según zona."},
    {"code": "VR-R", "name": "Verde-Rojo Rompe (núcleo)", "direction": "PUT|CALL", "timeframe": "1h",
     "entry_time": "Según dirección (PUT desde 11am)",
     "summary": "Verdes borradas por rojas y roja rompe piso del rebote (PUT); inverso CALL cuando rojas borradas por verdes y verde rompe techo."},
    {"code": "SPY-CTX", "name": "Contexto SPY (prioridad)", "direction": "CTX", "timeframe": "1d",
     "entry_time": "Siempre primero (~70% atención)",
     "summary": "SPY zona cara + caída potencia PUTs; SPY piso/rebote potencia CALLs. Si SPY cae, todo cae."},
]

DEFAULT_WATCHLIST = [
    "SPY", "QQQ", "AAPL", "MSFT", "NVDA", "META", "AMZN", "TSLA", "AMD", "GOOGL", "NFLX",
]
VOLUME_REL_THRESHOLD = 1.15
EARNINGS_PREFERRED = {"TSLA", "AMZN", "META", "AAPL", "NFLX"}


def ensure_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    out = df.copy()
    rename = {}
    for c in out.columns:
        cl = str(c).lower()
        if cl in ("open", "high", "low", "close", "volume"):
            rename[c] = cl.title()
        elif cl == "adj close":
            rename[c] = "Adj Close"
    out = out.rename(columns=rename)
    for col in ("Open", "High", "Low", "Close"):
        if col not in out.columns:
            raise ValueError(f"Falta columna {col}")
    if "Volume" not in out.columns:
        out["Volume"] = 0.0
    return out.dropna(subset=["Open", "High", "Low", "Close"])


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def add_mas(df: pd.DataFrame, periods: list[int]) -> pd.DataFrame:
    out = df.copy()
    for p in periods:
        out[f"PM{p}"] = sma(out["Close"], p)
    out["VolMA20"] = out["Volume"].rolling(20, min_periods=5).mean()
    return out


def body(row) -> float:
    return abs(float(row["Close"]) - float(row["Open"]))


def lower_wick(row) -> float:
    return min(float(row["Open"]), float(row["Close"])) - float(row["Low"])


def upper_wick(row) -> float:
    return float(row["High"]) - max(float(row["Open"]), float(row["Close"]))


def is_green(row) -> bool:
    return float(row["Close"]) > float(row["Open"])


def is_red(row) -> bool:
    return float(row["Close"]) < float(row["Open"])


def is_hammer(row, ratio: float = 2.0) -> bool:
    b = body(row) or 1e-9
    return lower_wick(row) >= ratio * b and upper_wick(row) <= b * 1.2


def is_hanging_man(row, prior_up: bool) -> bool:
    return prior_up and is_hammer(row)


def is_bearish_engulfing(prev, cur) -> bool:
    if not (is_green(prev) and is_red(cur)):
        return False
    return float(cur["Open"]) >= float(prev["Close"]) and float(cur["Close"]) <= float(prev["Open"])


def pct_dist(a: float, b: float) -> float:
    if b == 0 or (isinstance(b, float) and math.isnan(b)):
        return 0.0
    return (a - b) / b * 100.0


def near_ma(price: float, ma: float, tol_pct: float = 0.6) -> bool:
    if ma is None or (isinstance(ma, float) and math.isnan(ma)) or ma == 0:
        return False
    return abs(pct_dist(price, ma)) <= tol_pct


def high_volume(row, vol_ma) -> bool:
    if vol_ma is None or (isinstance(vol_ma, float) and (math.isnan(vol_ma) or vol_ma <= 0)):
        return False
    return float(row["Volume"]) >= VOLUME_REL_THRESHOLD * float(vol_ma)


def _clamp(s: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, s))


def _confidence(score: float) -> str:
    if score >= 75:
        return "alta"
    if score >= 55:
        return "media"
    return "baja"


def et_hm(ts) -> Optional[tuple[int, int]]:
    try:
        t = pd.Timestamp(ts)
        if t.tzinfo is None:
            t = t.tz_localize("America/New_York")
        else:
            t = t.tz_convert("America/New_York")
        return int(t.hour), int(t.minute)
    except Exception:
        try:
            t = pd.Timestamp(ts)
            if t.tzinfo is None:
                t = t.tz_localize("UTC").tz_convert("America/New_York")
            else:
                t = t.tz_convert("America/New_York")
            return int(t.hour), int(t.minute)
        except Exception:
            return None


def et_weekday(ts) -> Optional[int]:
    try:
        t = pd.Timestamp(ts)
        if t.tzinfo is None:
            t = t.tz_localize("America/New_York")
        else:
            t = t.tz_convert("America/New_York")
        return int(t.weekday())
    except Exception:
        return None


def in_entry_window_11_1559(df_1h: pd.DataFrame, i: int = -1) -> bool:
    hm = et_hm(df_1h.index[i])
    if hm is None:
        return True
    h, m = hm
    return 11 <= h <= 15


def avoid_930_1059(df_1h: pd.DataFrame, i: int = -1) -> bool:
    hm = et_hm(df_1h.index[i])
    if hm is None:
        return False
    h, m = hm
    if h == 9 and m >= 30:
        return True
    return h == 10


def after_or_at_11(df_1h: pd.DataFrame, i: int = -1) -> bool:
    hm = et_hm(df_1h.index[i])
    if hm is None:
        return True
    return hm[0] >= 11


def _safe_float(x) -> Optional[float]:
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def ma_stack_trend(fast, slow, flat_pct: float = 0.0015) -> str:
    """Cardona MA stack: alza if fast > slow, baja if fast < slow, lateral if near-equal/NaN.

    Catalog ground truth: PM-40H alcista when PM20>PM40; RCB bajista when PM40>PM20.
    Daily structure: PM100>PM200 = alza; PM100<PM200 = baja.
    """
    f = _safe_float(fast)
    s = _safe_float(slow)
    if f is None or s is None or s == 0:
        return "lateral"
    if abs(f - s) / abs(s) < flat_pct:
        return "lateral"
    return "alza" if f > s else "baja"


def _ma_pair_detail(fast_name: str, slow_name: str, fast, slow, flat_pct: float = 0.0015) -> dict[str, Any]:
    f = _safe_float(fast)
    s = _safe_float(slow)
    trend = ma_stack_trend(f, s, flat_pct=flat_pct)
    if f is None or s is None:
        rule = f"{fast_name}?{slow_name}"
        cmp_s = "sin datos"
    elif trend == "lateral":
        rule = f"|{fast_name}-{slow_name}|/{slow_name}<0.15%"
        cmp_s = "≈"
    elif f > s:
        rule = f"{fast_name}>{slow_name}"
        cmp_s = ">"
    else:
        rule = f"{fast_name}<{slow_name}"
        cmp_s = "<"
    return {
        "trend": trend,
        "rule": rule,
        "comparison": cmp_s,
        fast_name.lower(): None if f is None else round(f, 4),
        slow_name.lower(): None if s is None else round(s, 4),
        "label": (
            "sin datos"
            if f is None or s is None
            else f"{fast_name} {f:.2f} {cmp_s} {slow_name} {s:.2f}"
        ),
    }


def hourly_trend(df: pd.DataFrame, lookback: int = 5) -> str:
    """Last-bar PM20 vs PM40 on the given frame (typically 1h). lookback kept for API compat."""
    _ = lookback
    if df is None or getattr(df, "empty", True) or "PM20" not in df.columns or "PM40" not in df.columns:
        return "lateral"
    row = df.iloc[-1]
    return ma_stack_trend(row.get("PM20"), row.get("PM40"))


def daily_trend(df: pd.DataFrame, lookback: int = 5) -> str:
    """Last-bar PM100 vs PM200 on daily (fallback PM20 vs PM40 if PM200 missing)."""
    _ = lookback
    if df is None or getattr(df, "empty", True):
        return "lateral"
    row = df.iloc[-1]
    pm100 = row.get("PM100") if "PM100" in df.columns else None
    pm200 = row.get("PM200") if "PM200" in df.columns else None
    if _safe_float(pm200) is not None and _safe_float(pm100) is not None:
        return ma_stack_trend(pm100, pm200)
    if "PM20" in df.columns and "PM40" in df.columns:
        return ma_stack_trend(row.get("PM20"), row.get("PM40"))
    return "lateral"


def trend_detail_hourly(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or getattr(df, "empty", True) or "PM20" not in df.columns or "PM40" not in df.columns:
        return _ma_pair_detail("PM20", "PM40", None, None)
    row = df.iloc[-1]
    return _ma_pair_detail("PM20", "PM40", row.get("PM20"), row.get("PM40"))


def trend_detail_daily(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or getattr(df, "empty", True):
        return _ma_pair_detail("PM100", "PM200", None, None)
    row = df.iloc[-1]
    pm100 = row.get("PM100") if "PM100" in df.columns else None
    pm200 = row.get("PM200") if "PM200" in df.columns else None
    if _safe_float(pm200) is not None and _safe_float(pm100) is not None:
        return _ma_pair_detail("PM100", "PM200", pm100, pm200)
    if "PM20" in df.columns and "PM40" in df.columns:
        d = _ma_pair_detail("PM20", "PM40", row.get("PM20"), row.get("PM40"))
        d["fallback"] = "PM20/PM40 (PM200 ausente)"
        return d
    return _ma_pair_detail("PM100", "PM200", None, None)


def trend_detail_weekly(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or getattr(df, "empty", True) or "PM20" not in df.columns or "PM40" not in df.columns:
        return _ma_pair_detail("PM20", "PM40", None, None)
    row = df.iloc[-1]
    return _ma_pair_detail("PM20", "PM40", row.get("PM20"), row.get("PM40"))


def zona_barata(df_1d: pd.DataFrame) -> bool:
    if df_1d.empty:
        return False
    row = df_1d.iloc[-1]
    price = float(row["Close"])
    for key in ("PM200", "PM100"):
        if key in row and not pd.isna(row[key]):
            if near_ma(price, float(row[key]), 1.8) or price <= float(row[key]) * 1.012:
                return True
    return False


def expensive_zone_metrics(price: float, pm40, pm100=None) -> dict:
    out = {"cara": False, "spot_pm40": None, "dist_pm100": None, "pm40_pm100": None, "reasons": []}
    if pm40 is None or (isinstance(pm40, float) and math.isnan(pm40)):
        return out
    pm40 = float(pm40)
    spot_pm40 = price - pm40
    out["spot_pm40"] = spot_pm40
    dist_pct = pct_dist(price, pm40)
    if spot_pm40 >= 20 or dist_pct >= 3.0:
        out["cara"] = True
        out["reasons"].append(f"Estirado sobre PM40 ({spot_pm40:.2f} USD / {dist_pct:.2f}%).")
    if pm100 is not None and not (isinstance(pm100, float) and math.isnan(pm100)):
        pm100 = float(pm100)
        dist100 = price - pm100
        out["dist_pm100"] = dist100
        out["pm40_pm100"] = pm40 - pm100
        if dist100 >= 40 or pct_dist(price, pm100) >= 8.0:
            out["cara"] = True
            out["reasons"].append(f"Lejos de PM100 ({dist100:.2f} USD).")
        if (pm40 - pm100) >= 25:
            out["cara"] = True
            out["reasons"].append("PM40−PM100 ≥ 25 (estructura cara).")
    return out


def zona_cara(df_1h: pd.DataFrame, df_1d: Optional[pd.DataFrame] = None) -> bool:
    if df_1h.empty or "PM40" not in df_1h.columns:
        return False
    row = df_1h.iloc[-1]
    price = float(row["Close"])
    pm100 = None
    if df_1d is not None and not df_1d.empty and "PM100" in df_1d.columns:
        v = df_1d.iloc[-1]["PM100"]
        pm100 = None if pd.isna(v) else float(v)
    return expensive_zone_metrics(price, row.get("PM40"), pm100)["cara"]


def linear_fit_line(values: np.ndarray) -> tuple[float, float]:
    x = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(x, values.astype(float), 1)
    return float(slope), float(intercept)


def channel_upper(df: pd.DataFrame, bars: int = 18) -> Optional[float]:
    if len(df) < bars:
        return None
    y = df["High"].tail(bars).values.astype(float)
    slope, intercept = linear_fit_line(y)
    return slope * (len(y) - 1) + intercept


def channel_lower(df: pd.DataFrame, bars: int = 14) -> Optional[float]:
    if len(df) < bars:
        return None
    y = df["Low"].tail(bars).values.astype(float)
    slope, intercept = linear_fit_line(y)
    return slope * (len(y) - 1) + intercept


def close_slope(df: pd.DataFrame, bars: int = 16) -> float:
    if len(df) < bars:
        return 0.0
    y = df["Close"].tail(bars).values.astype(float)
    slope, _ = linear_fit_line(y)
    return slope


def find_drop_swing(df: pd.DataFrame, lookback: int = 18) -> Optional[dict]:
    if len(df) < lookback + 2:
        return None
    window = df.iloc[-(lookback + 1): -1]
    n = len(window)
    if n < 6:
        return None
    highs = window["High"].values
    lows = window["Low"].values
    closes = window["Close"].values
    peak_end = max(3, n * 2 // 3)
    peak_i = int(np.argmax(highs[:peak_end]))
    if peak_i >= n - 2:
        return None
    trough_rel = int(np.argmin(lows[peak_i:]))
    trough_i = peak_i + trough_rel
    if trough_i >= n:
        return None
    peak_px = float(closes[peak_i])
    trough_px = float(closes[trough_i])
    drop_pct = abs(pct_dist(trough_px, peak_px)) if trough_px < peak_px else 0.0
    drop_usd = max(0.0, float(highs[peak_i]) - float(lows[trough_i]))
    ceiling = float(np.max(highs[peak_i: trough_i + 1]))
    reds = 0
    touch_pm20 = touch_pm40 = break_pm40 = False
    for j in range(peak_i, trough_i + 1):
        row = window.iloc[j]
        if is_red(row):
            reds += 1
        if "PM20" in window.columns and not pd.isna(row.get("PM20")):
            if float(row["Low"]) <= float(row["PM20"]):
                touch_pm20 = True
        if "PM40" in window.columns and not pd.isna(row.get("PM40")):
            if float(row["Low"]) <= float(row["PM40"]) * 1.002:
                touch_pm40 = True
            if float(row["Close"]) < float(row["PM40"]):
                break_pm40 = True
    return {
        "drop_pct": drop_pct, "drop_usd": drop_usd, "ceiling": ceiling, "reds": reds,
        "touch_pm20": touch_pm20, "touch_pm40": touch_pm40, "break_pm40": break_pm40,
        "peak_i": peak_i, "trough_i": trough_i, "n": n,
    }


def adapt_drop_thresholds(price: float) -> dict:
    return {"cn_usd_lo": 3.0, "cn_usd_hi": 5.0, "cn_pct_hi": 1.5, "cf_usd": 6.0, "cf_pct": 1.5, "price": price}


@dataclass
class Opportunity:
    code: str
    strategy: str
    direction: str
    score: float
    reasons: list[str] = field(default_factory=list)
    bias: str = ""
    confidence: str = "media"
    warnings: list[str] = field(default_factory=list)
    signal_time: Optional[str] = None
    entry_time_hint: str = ""
    suitable_3sem: bool = False
    strike_hint: Optional[str] = None
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["score"] = round(float(self.score), 1)
        return d


def _opp(**kwargs) -> Opportunity:
    score = _clamp(float(kwargs.pop("score")))
    return Opportunity(score=score, confidence=_confidence(score), **kwargs)


# ---- PUT detectors ----

def detect_1VR(df_1h: pd.DataFrame, trend: str) -> Optional[Opportunity]:
    if len(df_1h) < 45:
        return None
    signal_i = None
    for i in range(-1, max(-10, -len(df_1h)) - 1, -1):
        hm = et_hm(df_1h.index[i])
        if hm and hm[0] in (9, 10) and is_red(df_1h.iloc[i]):
            signal_i = i
    if signal_i is None:
        return None
    row = df_1h.iloc[signal_i]
    pm40 = row.get("PM40")
    if pm40 is None or pd.isna(pm40):
        return None
    price = float(row["Close"])
    pm40 = float(pm40)
    bearish = trend == "baja" or close_slope(df_1h.iloc[: len(df_1h) + signal_i + 1], 14) < 0
    near_below = price <= pm40 * 1.01
    if not (bearish or near_below):
        return None
    if not near_below and trend != "baja":
        return None
    score = 64.0
    reasons = [
        "Código 1V-R: primera vela roja horaria tras apertura de Nueva York.",
        "Precio cerca o por debajo de PM40 en contexto bajista / canal bajista.",
        "Única estrategia que se compra a las 10:00 ET (vela final).",
    ]
    if trend == "baja":
        score += 12
        reasons.append("Tendencia horaria bajista confirmada.")
    if price < pm40:
        score += 8
    if high_volume(row, row.get("VolMA20")):
        score += 6
        reasons.append("Volumen relativo elevado en la vela de apertura.")
    return _opp(
        code="1V-R", strategy="1ra Vela Roja", direction="PUT", score=score, reasons=reasons,
        bias="bajista", signal_time=str(df_1h.index[signal_i]), entry_time_hint="Solo 10:00 ET",
        warnings=["Excepción a la regla de no operar 9:30–10:59 ET."], meta={"time_sensitive": True},
    )


def detect_RP_GAP(df_1h: pd.DataFrame) -> Optional[Opportunity]:
    if len(df_1h) < 5:
        return None
    gap_i = None
    for i in range(len(df_1h) - 1, max(0, len(df_1h) - 12), -1):
        if i == 0:
            break
        cur, prev = df_1h.iloc[i], df_1h.iloc[i - 1]
        if float(cur["Open"]) > float(prev["High"]) * 0.9995:
            gap_i = i
            break
    if gap_i is None:
        return None
    gap = df_1h.iloc[gap_i]
    gap_floor = min(float(gap["Low"]), float(gap["Open"]))
    last = df_1h.iloc[-1]
    if not is_red(last) or float(last["Close"]) >= gap_floor:
        return None
    if len(df_1h) - 1 - gap_i > 10:
        return None
    score = 66.0 + min(14, abs(pct_dist(gap_floor, float(last["Close"]))) * 4)
    reasons = [
        "Código RP-GAP: gap / apertura verde detectada.",
        f"Piso del gap (con mecha) ≈ {gap_floor:.2f}.",
        "Vela roja rompe el piso del gap → sesgo PUT.",
        "Entrada preferible desde las 11:00 ET.",
    ]
    if not after_or_at_11(df_1h):
        score -= 8
        reasons.append("Aún temprano: preferir confirmación post-11:00 ET.")
    if high_volume(last, last.get("VolMA20")):
        score += 8
        reasons.append("Ruptura con volumen relativo alto.")
    return _opp(
        code="RP-GAP", strategy="Ruptura del Piso del GAP", direction="PUT", score=score,
        reasons=reasons, bias="bajista", signal_time=str(df_1h.index[-1]),
        entry_time_hint="Desde 11:00 ET", meta={"gap_floor": gap_floor},
    )


def detect_4P(df_1h: pd.DataFrame, caro: bool) -> Optional[Opportunity]:
    if len(df_1h) < 20:
        return None
    last = df_1h.iloc[-1]
    if not is_red(last):
        return None
    slope = close_slope(df_1h.iloc[:-1], 14)
    upper = channel_upper(df_1h.iloc[:-1], 14)
    near_ceil = upper is not None and float(last["High"]) >= upper * 0.992
    if slope > 0 and not caro and not near_ceil:
        return None
    erased = hanging = False
    if len(df_1h) >= 3:
        for a_i, b_i in ((-3, -2), (-2, -1)):
            a, b = df_1h.iloc[a_i], df_1h.iloc[b_i]
            if is_green(a) and is_red(b) and float(b["Close"]) <= float(a["Open"]):
                erased = True
        prior_up = float(df_1h.iloc[-4]["Close"]) < float(df_1h.iloc[-2]["Close"]) if len(df_1h) >= 4 else True
        if is_hanging_man(df_1h.iloc[-2], prior_up) or is_hanging_man(last, True):
            hanging = True
    bounce_floor = float(df_1h["Low"].iloc[-6:-1].min()) if len(df_1h) >= 7 else float(df_1h["Low"].iloc[-3])
    broke = float(last["Close"]) < bounce_floor
    if not broke:
        return None
    if not (erased or hanging or near_ceil or caro):
        return None
    score = 60.0
    reasons = [
        "Código 4P / VR-R: modelo 4 pasos — verde-rojo rompe.",
        "Contexto de canal bajista / zona cara cerca del techo.",
    ]
    if caro:
        score += 12
        reasons.append("Zona cara (estiramiento sobre PM40 / lejos de pisos).")
    if near_ceil:
        score += 8
        reasons.append("Cerca del techo del canal bajista.")
    if erased:
        score += 10
        reasons.append("Vela(s) verde(s) borrada(s) por roja(s).")
    if hanging:
        score += 8
        reasons.append("Hombre colgado (hanger) tras el rebote.")
    score += 12
    reasons.append(f"Roja rompe el piso del rebote (≈ {bounce_floor:.2f}).")
    if after_or_at_11(df_1h):
        score += 8
        reasons.append("Horario OK: ≥ 11:00 ET.")
    else:
        score -= 10
        reasons.append("Esperar ≥ 11:00 ET para comprar PUT.")
    if high_volume(last, last.get("VolMA20")):
        score += 6
    return _opp(
        code="4P", strategy="Modelo 4 pasos (verde-rojo rompe)", direction="PUT", score=score,
        reasons=reasons, bias="bajista", signal_time=str(df_1h.index[-1]),
        entry_time_hint="Desde 11:00 ET", suitable_3sem=caro and score >= 70,
    )


def detect_HD(df_1d: pd.DataFrame) -> Optional[Opportunity]:
    if len(df_1d) < 30 or "PM40" not in df_1d.columns:
        return None
    for offset in range(1, 6):
        if len(df_1d) < offset + 3:
            continue
        i = -offset
        row = df_1d.iloc[i]
        prior_up = float(df_1d.iloc[i - 2]["Close"]) < float(df_1d.iloc[i - 1]["Close"])
        if not is_hanging_man(row, prior_up) and not (is_hammer(row) and prior_up):
            continue
        price = float(row["Close"])
        pm40 = row.get("PM40")
        pm100 = row.get("PM100") if "PM100" in df_1d.columns else None
        metrics = expensive_zone_metrics(
            price,
            None if pm40 is None or pd.isna(pm40) else float(pm40),
            None if pm100 is None or pd.isna(pm100) else float(pm100),
        )
        if not metrics["cara"]:
            continue
        seq_bonus = 0
        reasons = [
            "Código HD: hanger (hombre colgado) en diario dentro de zona cara.",
            "Secuencia típica: hanger → verde de baja volatilidad → roja → caída (2–3 días).",
        ] + metrics["reasons"]
        if offset >= 2:
            after = df_1d.iloc[i + 1:]
            if len(after) >= 1 and is_green(after.iloc[0]):
                seq_bonus += 5
                reasons.append("Tras hanger apareció vela verde (posible trampa de baja vol).")
            if len(after) >= 2 and is_red(after.iloc[1]):
                seq_bonus += 10
                reasons.append("Confirmación con vela(s) roja(s) posteriores.")
            if is_red(df_1d.iloc[-1]):
                seq_bonus += 8
        score = 58.0 + seq_bonus + (10 if offset <= 3 else 0)
        return _opp(
            code="HD", strategy="Hanger en Diario", direction="PUT", score=_clamp(score),
            reasons=reasons, bias="bajista", signal_time=str(df_1d.index[i]),
            entry_time_hint="~2–3 días tras el hanger", suitable_3sem=True,
            strike_hint="ATM o ligeramente OTM; horizonte ~3 semanas si el techo es fuerte",
        )
    return None


def detect_VRF_E(df_1d: pd.DataFrame) -> Optional[Opportunity]:
    if len(df_1d) < 25:
        return None
    prev, cur = df_1d.iloc[-2], df_1d.iloc[-1]
    if not is_bearish_engulfing(prev, cur):
        return None
    price = float(cur["Close"])
    pm40 = cur.get("PM40") if "PM40" in df_1d.columns else None
    pm100 = cur.get("PM100") if "PM100" in df_1d.columns else None
    metrics = expensive_zone_metrics(
        price,
        None if pm40 is None or pd.isna(pm40) else float(pm40),
        None if pm100 is None or pd.isna(pm100) else float(pm100),
    )
    if not metrics["cara"]:
        hi20 = float(df_1d["High"].tail(20).max())
        if price < hi20 * 0.97:
            return None
        metrics["cara"] = True
        metrics["reasons"].append("Cerca de máximos recientes (techo).")
    score = 70.0
    reasons = [
        "Código VRF-E: envolvente bajista (roja final del día) en zona cara/techo.",
        "La roja envuelve el cuerpo de la vela previa verde.",
    ] + metrics["reasons"]
    if high_volume(cur, cur.get("VolMA20")):
        score += 12
        reasons.append("Alto volumen en la envolvente (confirmación).")
    else:
        score -= 5
        reasons.append("Volumen no destacado — confirmar con SPY.")
    return _opp(
        code="VRF-E", strategy="Vela Roja Final Envolvente del Día", direction="PUT", score=score,
        reasons=reasons, bias="bajista", signal_time=str(df_1d.index[-1]),
        entry_time_hint="Tras cierre diario / siguiente sesión", suitable_3sem=True,
    )


def detect_TF(df_1d: pd.DataFrame, df_1h: pd.DataFrame) -> Optional[Opportunity]:
    if df_1d.empty:
        return None
    caro = zona_cara(df_1h, df_1d) if not df_1h.empty else False
    last = df_1d.iloc[-1]
    price = float(last["Close"])
    pm40 = last.get("PM40") if "PM40" in df_1d.columns else None
    pm100 = last.get("PM100") if "PM100" in df_1d.columns else None
    metrics = expensive_zone_metrics(
        price,
        None if pm40 is None or pd.isna(pm40) else float(pm40),
        None if pm100 is None or pd.isna(pm100) else float(pm100),
    )
    if not (caro or metrics["cara"]):
        return None
    hi60 = float(df_1d["High"].tail(60).max()) if len(df_1d) >= 20 else price
    if price < hi60 * 0.96 and not metrics["cara"]:
        return None
    score = 52.0 + (15 if metrics["cara"] else 0)
    reasons = [
        "Código TF: techo fuerte / zona cara — sesgo PUT y precaución con CALLs.",
        "Emparejar con HD, VRF-E o contexto SPY zona cara.",
    ] + metrics["reasons"]
    return _opp(
        code="TF", strategy="Techo Fuerte", direction="PUT", score=score, reasons=reasons,
        bias="bajista", signal_time=str(df_1d.index[-1]),
        entry_time_hint="Contexto — combinar con hanger / SPY", suitable_3sem=True,
        strike_hint="Heurística 3 semanas: strikes ~5–7% OTM o según tabla de volatilidad",
    )


# ---- CALL detectors ----

def detect_RT(df_1h: pd.DataFrame) -> Optional[Opportunity]:
    if len(df_1h) < 40:
        return None
    drop = find_drop_swing(df_1h, 16)
    if not drop or drop["reds"] < 2:
        return None
    if not (drop["touch_pm20"] or drop["touch_pm40"]):
        return None
    last = df_1h.iloc[-1]
    prev = df_1h.iloc[-2]
    if not is_green(last) or float(last["Close"]) <= drop["ceiling"]:
        return None
    hammerish = is_hammer(prev) or is_hammer(last) or is_green(prev)
    score = 62.0
    reasons = [
        "Código RT: ruptura del techo tras caída.",
        f"≥2 velas rojas interactuaron con PM20/PM40 (rojas={drop['reds']}).",
        f"Verde rompe la línea de techo de la caída (≈ {drop['ceiling']:.2f}).",
    ]
    if hammerish:
        score += 10
        reasons.append("Martillo / vela verde previa de agotamiento.")
    if high_volume(last, last.get("VolMA20")):
        score += 10
        reasons.append("Vela de ruptura con volumen relativo alto.")
    if in_entry_window_11_1559(df_1h):
        score += 8
        reasons.append("Ventana 11:00–15:59 ET.")
    else:
        score -= 12
        reasons.append("Fuera de ventana 11:00–15:59 — reducir confianza.")
    return _opp(
        code="RT", strategy="Ruptura del Techo", direction="CALL", score=score, reasons=reasons,
        bias="alcista", signal_time=str(df_1h.index[-1]), entry_time_hint="11:00–15:59 ET",
    )


def detect_PM40H(df_1h: pd.DataFrame, trend: str) -> Optional[Opportunity]:
    if len(df_1h) < 50:
        return None
    last = df_1h.iloc[-1]
    if pd.isna(last.get("PM20")) or pd.isna(last.get("PM40")):
        return None
    pm20, pm40 = float(last["PM20"]), float(last["PM40"])
    if pm20 <= pm40 and trend != "alza":
        return None
    touched40 = broke20 = False
    for i in range(-8, -1):
        if abs(i) > len(df_1h):
            continue
        r = df_1h.iloc[i]
        if pd.isna(r.get("PM20")) or pd.isna(r.get("PM40")):
            continue
        if is_red(r) and float(r["Close"]) < float(r["PM20"]):
            broke20 = True
        if is_red(r) and float(r["Low"]) <= float(r["PM40"]) * 1.005:
            touched40 = True
    if not (broke20 and touched40):
        return None
    if not is_green(last) or float(last["Close"]) <= pm20:
        return None
    score = 68.0
    reasons = [
        "Código PM-40H: pullback a PM40 en tendencia (PM20 > PM40).",
        "Rojas rompieron PM20 y tocaron / rompieron parcialmente PM40.",
        "Vela verde final vuelve a cerrar sobre PM20 → CALL (rebote 1–2 días).",
    ]
    if near_ma(float(df_1h.iloc[-2]["Low"]), pm40, 1.2):
        score += 10
        reasons.append("Toque limpio de PM40 (piso fuerte en canal alcista).")
    if in_entry_window_11_1559(df_1h):
        score += 8
    else:
        score -= 10
        reasons.append("Preferir entrada 11:00–15:59 ET.")
    if high_volume(last, last.get("VolMA20")):
        score += 6
    return _opp(
        code="PM-40H", strategy="Promedio Móvil 40 Hora", direction="CALL", score=score,
        reasons=reasons, bias="alcista", signal_time=str(df_1h.index[-1]),
        entry_time_hint="11:00–15:59 ET",
    )


def detect_CN(df_1h: pd.DataFrame, trend: str) -> Optional[Opportunity]:
    if len(df_1h) < 40:
        return None
    if trend != "alza":
        last = df_1h.iloc[-1]
        if pd.isna(last.get("PM40")) or float(last["Close"]) < float(last["PM40"]):
            return None
    drop = find_drop_swing(df_1h, 14)
    if not drop:
        return None
    price = float(df_1h.iloc[-1]["Close"])
    thr = adapt_drop_thresholds(price)
    usd_ok = thr["cn_usd_lo"] <= drop["drop_usd"] <= thr["cn_usd_hi"] * 1.4
    pct_ok = 0.4 <= drop["drop_pct"] <= thr["cn_pct_hi"]
    if not (usd_ok or pct_ok):
        return None
    if drop["drop_pct"] > 1.5 and drop["drop_usd"] > 6:
        return None
    if drop["break_pm40"] and drop["drop_pct"] > 1.2:
        return None
    if drop["reds"] < 2:
        return None
    last = df_1h.iloc[-1]
    if not is_green(last) or float(last["Close"]) <= drop["ceiling"]:
        return None
    score = 64.0
    reasons = [
        "Código CN: caída normal (~$3–5 o <1.5%).",
        f"Magnitud ≈ {drop['drop_usd']:.2f} USD / {drop['drop_pct']:.2f}%.",
        "Rojas rompen PM20 pero no PM40 (o apenas lo tocan).",
        "Martillo/verde rompe techo de la caída → CALL.",
    ]
    if is_hammer(df_1h.iloc[-2]) or is_hammer(last):
        score += 8
        reasons.append("Martillo de agotamiento.")
    if et_weekday(df_1h.index[-1]) == 4:
        score += 6
        reasons.append("Viernes — contexto favorable para CN según método.")
    if in_entry_window_11_1559(df_1h):
        score += 6
    return _opp(
        code="CN", strategy="Caída Normal", direction="CALL", score=score, reasons=reasons,
        bias="alcista", signal_time=str(df_1h.index[-1]),
        entry_time_hint="11:00–15:59 ET (esp. viernes)",
    )


def detect_CF(df_1h: pd.DataFrame, df_1d: pd.DataFrame, trend: str) -> Optional[Opportunity]:
    if len(df_1h) < 40:
        return None
    drop = find_drop_swing(df_1h, 20)
    if not drop:
        return None
    price = float(df_1h.iloc[-1]["Close"])
    thr = adapt_drop_thresholds(price)
    if not (drop["drop_usd"] >= thr["cf_usd"] or drop["drop_pct"] >= thr["cf_pct"]):
        return None
    last = df_1h.iloc[-1]
    if not is_green(last) or float(last["Close"]) <= drop["ceiling"]:
        return None
    score = 70.0
    reasons = [
        "Código CF: caída fuerte (>$6 o >1.5%).",
        f"Magnitud ≈ {drop['drop_usd']:.2f} USD / {drop['drop_pct']:.2f}%.",
        "Verde rompe techo de la caída fuerte → CALL de rebote.",
    ]
    if not df_1d.empty:
        for key in ("PM20", "PM40", "PM100", "PM200"):
            if key in df_1d.columns and not pd.isna(df_1d.iloc[-1].get(key)):
                if float(df_1d["Low"].tail(5).min()) <= float(df_1d.iloc[-1][key]):
                    reasons.append(f"La caída tocó/rompió {key} en diario.")
                    score += 3
    if is_hammer(df_1h.iloc[-2]) or is_hammer(last):
        score += 8
        reasons.append("Martillo de capitulación.")
    if in_entry_window_11_1559(df_1h):
        score += 6
    if high_volume(last, last.get("VolMA20")):
        score += 6
    return _opp(
        code="CF", strategy="Caída Fuerte", direction="CALL", score=score, reasons=reasons,
        bias="alcista", signal_time=str(df_1h.index[-1]), entry_time_hint="11:00–15:59 ET",
        suitable_3sem=drop["drop_pct"] >= 3.0,
    )


def detect_RCB(df_1h: pd.DataFrame) -> Optional[Opportunity]:
    if len(df_1h) < 30:
        return None
    prior = df_1h.iloc[:-1]
    s1 = close_slope(prior, 20)
    s2 = close_slope(prior, 40 if len(prior) >= 40 else 20)
    if s1 >= 0 and s2 >= 0:
        return None
    upper = channel_upper(prior, bars=min(24, len(prior)))
    if upper is None:
        return None
    last = df_1h.iloc[-1]
    if not is_green(last) or float(last["Close"]) <= upper:
        return None
    score = 76.0
    reasons = [
        "Código RCB: ruptura del techo del canal bajista — mejor CALL del método.",
        f"Cierre verde sobre techo de canal (≈ {upper:.2f}).",
        "No comprar CALL dentro del canal bajista sin esta ruptura.",
    ]
    if not pd.isna(last.get("PM20")) and not pd.isna(last.get("PM40")):
        if float(last["PM40"]) > float(last["PM20"]):
            score += 6
            reasons.append("Estructura previa PM40 > PM20 (canal bajista).")
        elif float(last["Close"]) > float(last["PM20"]):
            score += 4
            reasons.append("Cierre también recupera PM20.")
    if is_hammer(df_1h.iloc[-2]) or is_green(df_1h.iloc[-2]):
        score += 6
        reasons.append("Martillo / verde previo de base.")
    if high_volume(last, last.get("VolMA20")):
        score += 10
        reasons.append("Volumen alto en la ruptura.")
    if in_entry_window_11_1559(df_1h):
        score += 6
    else:
        score -= 10
    return _opp(
        code="RCB", strategy="Ruptura Canal Bajista (mejor CALL)", direction="CALL", score=score,
        reasons=reasons, bias="alcista", signal_time=str(df_1h.index[-1]),
        entry_time_hint="11:00–15:59 ET", suitable_3sem=True,
        strike_hint="Movimiento grande esperado — evaluar Estrategia 3 semanas",
        meta={"channel_upper": upper},
    )


def detect_GAP_NA(df_1h: pd.DataFrame) -> Optional[Opportunity]:
    if len(df_1h) < 8:
        return None
    gap_i = None
    for i in range(len(df_1h) - 1, max(1, len(df_1h) - 10), -1):
        if float(df_1h.iloc[i]["Open"]) > float(df_1h.iloc[i - 1]["High"]) * 0.999:
            gap_i = i
            break
    if gap_i is None:
        return None
    prev = df_1h.iloc[gap_i - 1]
    if not is_green(prev) and hourly_trend(df_1h.iloc[:gap_i]) != "alza":
        return None
    c0 = df_1h.iloc[gap_i]
    if not is_green(c0):
        return None
    if gap_i + 1 >= len(df_1h):
        return None
    c1 = df_1h.iloc[gap_i + 1]
    if not (is_green(c1) or is_hammer(c1)):
        return None
    score = 63.0
    reasons = [
        "Código GAP-NA: gap normal al alza con sesgo alcista previo.",
        "Vela 9:30 verde de gap + 10am verde/martillo.",
    ]
    if gap_i + 2 < len(df_1h):
        c2 = df_1h.iloc[gap_i + 2]
        if is_green(c2) or (is_red(c2) and high_volume(c2, c2.get("VolMA20"))):
            score += 12
            reasons.append("Vela ~11am confirma (verde o roja de alto vol).")
        else:
            score -= 5
    if close_slope(df_1h.iloc[:gap_i], 20) < 0:
        upper = channel_upper(df_1h.iloc[:gap_i], 16)
        if upper and float(c0["Close"]) < upper * 0.98:
            score -= 15
            reasons.append("Inestable: gap dentro de canal bajista profundo (lejos del techo).")
        else:
            reasons.append("Gap cerca del techo de canal bajista — más aceptable.")
    return _opp(
        code="GAP-NA", strategy="GAP Normal al Alza", direction="CALL", score=score,
        reasons=reasons, bias="alcista",
        signal_time=str(df_1h.index[min(gap_i + 2, len(df_1h) - 1)]),
        entry_time_hint="~11:00–12:00 ET",
    )


def detect_GAP_BA(df_1h: pd.DataFrame) -> Optional[Opportunity]:
    if len(df_1h) < 8:
        return None
    gap_i = None
    for i in range(len(df_1h) - 1, max(1, len(df_1h) - 10), -1):
        cur, prev = df_1h.iloc[i], df_1h.iloc[i - 1]
        if float(cur["Open"]) < float(prev["Close"]) and is_green(cur):
            gap_i = i
            break
    if gap_i is None:
        return None
    prev = df_1h.iloc[gap_i - 1]
    c0 = df_1h.iloc[gap_i]
    if not is_green(c0) or gap_i + 1 >= len(df_1h):
        return None
    c1 = df_1h.iloc[gap_i + 1]
    if not is_green(c1):
        return None
    score = 67.0
    reasons = [
        "Código GAP-BA: abre abajo (gap bajista) pero compra agresiva.",
        "1ª vela verde y 2ª (10am) VERDE (obligatoria).",
    ]
    if not is_green(prev):
        score -= 8
        reasons.append("Cierre previo no era verde — GAP-BA imperfecto (precaución).")
    else:
        reasons.append("Cierre previo verde (condición ideal).")
    if gap_i + 2 < len(df_1h):
        c2 = df_1h.iloc[gap_i + 2]
        if is_green(c2) or high_volume(c2, c2.get("VolMA20")):
            score += 12
            reasons.append("3ª vela (~11am) verde o de alto volumen — confirmación.")
        else:
            score -= 6
            reasons.append("3ª vela débil — precaución.")
    if close_slope(df_1h.iloc[:gap_i], 18) < 0:
        score += 6
        reasons.append("Dentro de canal bajista: GAP-BA puede durar 3–4 días.")
        reasons.append("Inestable si ocurre en el techo de un canal alcista.")
    return _opp(
        code="GAP-BA", strategy="GAP Bajista al Alza", direction="CALL", score=score,
        reasons=reasons, bias="alcista",
        signal_time=str(df_1h.index[min(gap_i + 2, len(df_1h) - 1)]),
        entry_time_hint="Tras 2ª/3ª vela (~11am)",
    )


def detect_PF(df_1h: pd.DataFrame, df_1d: pd.DataFrame) -> Optional[Opportunity]:
    if df_1d.empty or len(df_1h) < 30:
        return None
    approached = near200 = near100 = False
    for i in range(-12, 0):
        if abs(i) > len(df_1d):
            continue
        r = df_1d.iloc[i]
        for key, flag in (("PM200", "200"), ("PM100", "100")):
            if key in r and not pd.isna(r[key]):
                if float(r["Low"]) <= float(r[key]) * 1.02:
                    approached = True
                    if flag == "200":
                        near200 = True
                    else:
                        near100 = True
    if not (approached or zona_barata(df_1d)):
        return None
    dlast = df_1d.iloc[-1]
    rev = is_hammer(dlast) or is_green(dlast)
    upper = channel_upper(df_1h.iloc[:-1], 16)
    last = df_1h.iloc[-1]
    if upper is None or not is_green(last) or float(last["Close"]) <= upper:
        return None
    score = 72.0
    reasons = [
        "Código PF: piso fuerte diario (PM100/PM200) + ruptura horaria de canal bajista.",
        "CALL típico de 3–5 días si se confirma.",
    ]
    if near200:
        score += 14
        reasons.append("Boost: cercanía/toque de PM200.")
        reasons.append("Si rojas rompen PM200 con fuerza, vigilar caída multi-mes.")
    elif near100:
        score += 8
        reasons.append("Toque de PM100.")
    if rev:
        score += 6
        reasons.append("Reversión diaria (martillo/verde).")
    if "PM40" in dlast and not pd.isna(dlast["PM40"]) and near_ma(float(dlast["Close"]), float(dlast["PM40"]), 2.5):
        score += 6
        reasons.append("Precio diario cerca de PM40 (confirmación).")
    if high_volume(last, last.get("VolMA20")):
        score += 6
    return _opp(
        code="PF", strategy="Piso Fuerte", direction="CALL", score=score, reasons=reasons,
        bias="alcista", signal_time=str(df_1h.index[-1]), entry_time_hint="Tras ruptura horaria",
        suitable_3sem=True, strike_hint="Piso fuerte — candidato a Estrategia 3 semanas",
    )


def detect_1GAP_A(df_1h: pd.DataFrame, df_1d: pd.DataFrame) -> Optional[Opportunity]:
    if df_1d.empty or len(df_1h) < 5:
        return None
    base = None
    try:
        base = detect_PF(df_1h, df_1d)
    except Exception:
        base = None
    if not (base or zona_barata(df_1d)):
        return None
    gap_i = None
    for i in range(len(df_1h) - 1, max(1, len(df_1h) - 8), -1):
        if float(df_1h.iloc[i]["Open"]) > float(df_1h.iloc[i - 1]["High"]):
            gap_i = i
            break
    if gap_i is None and len(df_1d) >= 2:
        if float(df_1d.iloc[-1]["Open"]) > float(df_1d.iloc[-2]["High"]):
            gap_i = len(df_1h) - 1
    if gap_i is None:
        return None
    gap = df_1h.iloc[gap_i]
    if not is_green(gap):
        return None
    gap_floor = min(float(gap["Low"]), float(gap["Open"]))
    respected = True
    for j in range(gap_i + 1, len(df_1h)):
        if float(df_1h.iloc[j]["Low"]) < gap_floor * 0.997:
            respected = False
            break
    last = df_1h.iloc[-1]
    score = 74.0 if base else 66.0
    reasons = [
        "Código 1GAP-A: primer gap al alza tras contexto de piso fuerte.",
        f"Piso del gap ≈ {gap_floor:.2f} (incluye mecha).",
        "Suele impulsarse 3–4 días si el piso se respeta.",
    ]
    if respected:
        score += 10
        reasons.append("El precio respetó el piso del gap durante la sesión.")
    else:
        score -= 20
        reasons.append("Piso del gap vulnerado — setup inválido o debilitado.")
        if score < 45:
            return None
    if high_volume(gap, gap.get("VolMA20")) or high_volume(last, last.get("VolMA20")):
        score += 8
        reasons.append("Vela con volumen relativo alto.")
    if base:
        reasons.append("Combinado con señal PF activa.")
    return _opp(
        code="1GAP-A", strategy="1er GAP al Alza", direction="CALL", score=score, reasons=reasons,
        bias="alcista", signal_time=str(df_1h.index[-1]),
        entry_time_hint="Validar piso del gap y cierre del día", suitable_3sem=True,
        meta={"gap_floor": gap_floor},
    )


def detect_VR_R_call(df_1h: pd.DataFrame) -> Optional[Opportunity]:
    if len(df_1h) < 12:
        return None
    last = df_1h.iloc[-1]
    if not is_green(last):
        return None
    erased = False
    if len(df_1h) >= 3:
        for a_i, b_i in ((-3, -2), (-2, -1)):
            a, b = df_1h.iloc[a_i], df_1h.iloc[b_i]
            if is_red(a) and is_green(b) and float(b["Close"]) >= float(a["Open"]):
                erased = True
    drop = find_drop_swing(df_1h, 12)
    if not erased or not drop:
        return None
    if float(last["Close"]) <= drop["ceiling"]:
        return None
    score = 61.0
    reasons = [
        "Código VR-R (inverso CALL): rojas borradas por verdes.",
        "Verde rompe el techo de la caída (espejo del 4 pasos PUT).",
    ]
    if high_volume(last, last.get("VolMA20")):
        score += 8
    if in_entry_window_11_1559(df_1h):
        score += 6
    return _opp(
        code="VR-R", strategy="Verde-Rojo Rompe (inverso CALL)", direction="CALL", score=score,
        reasons=reasons, bias="alcista", signal_time=str(df_1h.index[-1]),
        entry_time_hint="11:00–15:59 ET",
    )


def suggest_3sem(opps: list[Opportunity], zona: str, ticker: str) -> list[Opportunity]:
    hint_c = "CALL: strike cerca ATM o ~2–5% OTM; horizonte ~3 semanas"
    hint_p = "PUT: strike cerca ATM o ~2–5% OTM; horizonte ~3 semanas"
    for op in opps:
        if op.suitable_3sem or (
            zona in ("barata", "cara") and op.score >= 68 and op.code in (
                "PF", "RCB", "CF", "HD", "VRF-E", "TF", "1GAP-A", "4P"
            )
        ):
            op.suitable_3sem = True
            if not op.strike_hint:
                op.strike_hint = hint_c if op.direction == "CALL" else hint_p
            if not any("3 semanas" in r for r in op.reasons):
                op.reasons.append(
                    "Candidato Estrategia 3 semanas (piso/techo/ruptura con movimiento esperado)."
                )
    return opps


def earnings_bias_note(ticker: str, zona: str, trend_d: str) -> Optional[str]:
    t = ticker.upper()
    pref = t in EARNINGS_PREFERRED
    if zona == "barata" and trend_d in ("baja", "lateral"):
        msg = "Filtro earnings (heurístico): viene de caída + zona piso → sesgo CALL; strikes ~5–7% alejados; mirar volumen."
        if pref:
            msg += f" {t} está en nombres preferidos (TSLA/AMZN/META/AAPL/NFLX; NFLX mejor post-earnings)."
        return msg
    if zona == "cara" and trend_d in ("alza", "lateral"):
        msg = "Filtro earnings (heurístico): viene de subida + zona techo → sesgo PUT; strikes ~5–7%; volumen."
        if pref:
            msg += f" {t} en watchlist earnings Cardona."
        return msg
    return None


def spy_context(df_spy_1d: pd.DataFrame, df_spy_1h: Optional[pd.DataFrame] = None) -> dict:
    info = {
        "spy_zona_cara": False, "spy_zona_barata": False, "spy_cae": False,
        "boost_put": False, "boost_call": False, "reasons": [],
        "trend_daily": "lateral", "zona": "neutral",
        "attention": "Revisar SPY primero (~70% del análisis).",
    }
    if df_spy_1d is None or df_spy_1d.empty:
        info["reasons"].append("Sin datos SPY.")
        return info
    info["trend_daily"] = daily_trend(df_spy_1d)
    last = df_spy_1d.iloc[-1]
    price = float(last["Close"])
    pm40 = last.get("PM40") if "PM40" in df_spy_1d.columns else None
    pm100 = last.get("PM100") if "PM100" in df_spy_1d.columns else None
    metrics = expensive_zone_metrics(
        price,
        None if pm40 is None or pd.isna(pm40) else float(pm40),
        None if pm100 is None or pd.isna(pm100) else float(pm100),
    )
    barata = zona_barata(df_spy_1d)
    caro = metrics["cara"]
    if df_spy_1h is not None and not df_spy_1h.empty and zona_cara(df_spy_1h, df_spy_1d):
        caro = True
    info["spy_zona_cara"] = caro
    info["spy_zona_barata"] = barata
    info["zona"] = "cara" if caro else ("barata" if barata else "neutral")
    info["reasons"].extend(metrics["reasons"])
    cae = False
    if is_red(last):
        cae = True
        info["reasons"].append("SPY diario: vela roja.")
    if len(df_spy_1d) >= 3:
        prior_up = float(df_spy_1d.iloc[-3]["Close"]) < float(df_spy_1d.iloc[-2]["Close"])
        if is_hanging_man(last, prior_up) or is_hanging_man(df_spy_1d.iloc[-2], True):
            cae = True
            info["reasons"].append("SPY: hanger en zona de estiramiento.")
    if df_spy_1h is not None and len(df_spy_1h) >= 5 and hourly_trend(df_spy_1h) == "baja":
        cae = True
        info["reasons"].append("SPY 1h en tendencia bajista.")
    info["spy_cae"] = cae
    info["boost_put"] = caro and cae
    info["boost_call"] = barata and (
        is_green(last) or (df_spy_1h is not None and hourly_trend(df_spy_1h) == "alza")
    )
    if info["boost_put"]:
        info["reasons"].append("Si SPY cae, todo cae — boost PUT en el universo.")
    if info["boost_call"]:
        info["reasons"].append("SPY en piso / rebote — boost relativo a CALLs.")
    return info


def apply_golden_rules(opps: list[Opportunity], df_1h: pd.DataFrame) -> list[Opportunity]:
    forbidden = avoid_930_1059(df_1h) if not df_1h.empty else False
    out = []
    for op in opps:
        warnings = list(op.warnings)
        score = op.score
        if forbidden and op.code != "1V-R":
            score = _clamp(score - 25)
            warnings.append("Regla de oro: evitar 9:30–10:59 ET excepto 1V-R (score −25).")
        warnings.append("Solo velas completadas (vela final) — no operar la vela en formación.")
        op.score = score
        op.confidence = _confidence(score)
        op.warnings = warnings
        out.append(op)
    return out


def prepare_frames(df_1h: pd.DataFrame, df_1d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    h = ensure_ohlcv(df_1h)
    d = ensure_ohlcv(df_1d)
    if not h.empty:
        h = add_mas(h, [20, 40])
    if not d.empty:
        d = add_mas(d, [20, 40, 100, 200])
    return h, d


def _series_payload(df: pd.DataFrame, mas: list[int]) -> dict:
    payload = {
        "t": [str(i) for i in df.index],
        "o": [float(x) for x in df["Open"]],
        "h": [float(x) for x in df["High"]],
        "l": [float(x) for x in df["Low"]],
        "c": [float(x) for x in df["Close"]],
        "v": [float(x) for x in df["Volume"]],
    }
    for p in mas:
        col = f"PM{p}"
        if col in df.columns:
            payload[col] = [None if pd.isna(x) else float(x) for x in df[col]]
    return payload


def analyze_ticker(
    ticker: str,
    df_1h: pd.DataFrame,
    df_1d: pd.DataFrame,
    df_spy_1h: Optional[pd.DataFrame] = None,
    df_spy_1d: Optional[pd.DataFrame] = None,
    drop_forming: bool = True,
) -> dict[str, Any]:
    ticker = (ticker or "").upper().strip()
    result: dict[str, Any] = {
        "ticker": ticker, "ok": True, "error": None,
        "trend_1h": "lateral", "trend_1d": "lateral", "zona": "neutral",
        "opportunities": [], "top_call": None, "top_put": None,
        "market_bias": "neutral", "spy_context": {}, "warnings": [],
        "last_price": None, "earnings_note": None,
        "tna_tza_note": "Opcional: TNA (3x bull small-cap) / TZA (3x bear) correlacionan con riesgo; solo contexto, no señal primaria.",
        "strategies_catalog": STRATEGIES_CATALOG,
    }
    try:
        h, d = prepare_frames(df_1h, df_1d)
        if h.empty or len(h) < 50:
            result["ok"] = False
            result["error"] = f"Datos horarios insuficientes para {ticker}."
            return result
        if drop_forming and len(h) > 50:
            h = h.iloc[:-1].copy()

        spy_h = spy_d = None
        if df_spy_1h is not None and not df_spy_1h.empty:
            spy_h, _ = prepare_frames(df_spy_1h, pd.DataFrame())
            if drop_forming and len(spy_h) > 50:
                spy_h = spy_h.iloc[:-1].copy()
        if df_spy_1d is not None and not df_spy_1d.empty:
            _, spy_d = prepare_frames(pd.DataFrame(), df_spy_1d)
        elif ticker == "SPY":
            spy_d, spy_h = d, h

        trend_h = hourly_trend(h)
        trend_d = daily_trend(d) if not d.empty else "lateral"
        detail_h = trend_detail_hourly(h)
        detail_d = trend_detail_daily(d) if not d.empty else trend_detail_daily(pd.DataFrame())
        caro = zona_cara(h, d if not d.empty else None)
        barata = zona_barata(d) if not d.empty else False
        zona = "cara" if caro else ("barata" if barata else "neutral")
        result.update(
            trend_1h=trend_h,
            trend_1d=trend_d,
            zona=zona,
            last_price=float(h.iloc[-1]["Close"]),
            trend_detail={"hourly": detail_h, "daily": detail_d},
        )

        spy_ctx = spy_context(spy_d if spy_d is not None else pd.DataFrame(), spy_h)
        result["spy_context"] = spy_ctx

        opps: list[Opportunity] = []
        detectors = [
            lambda: detect_1VR(h, trend_h),
            lambda: detect_RP_GAP(h),
            lambda: detect_4P(h, caro),
            lambda: detect_HD(d) if not d.empty else None,
            lambda: detect_VRF_E(d) if not d.empty else None,
            lambda: detect_TF(d, h) if not d.empty else None,
            lambda: detect_RT(h),
            lambda: detect_PM40H(h, trend_h),
            lambda: detect_CN(h, trend_h),
            lambda: detect_CF(h, d, trend_h),
            lambda: detect_RCB(h),
            lambda: detect_GAP_NA(h),
            lambda: detect_GAP_BA(h),
            lambda: detect_PF(h, d) if not d.empty else None,
            lambda: detect_1GAP_A(h, d) if not d.empty else None,
            lambda: detect_VR_R_call(h),
        ]
        for det in detectors:
            try:
                op = det()
                if op is not None:
                    opps.append(op)
            except Exception as e:
                result["warnings"].append(f"Detector omitido: {e}")

        if spy_ctx.get("boost_put"):
            for op in opps:
                if op.direction == "PUT":
                    op.score = _clamp(op.score + 12)
                    op.reasons.append("Boost SPY: zona cara + cayendo («si SPY cae, todo cae»).")
                    op.confidence = _confidence(op.score)
        if spy_ctx.get("boost_call"):
            for op in opps:
                if op.direction == "CALL":
                    op.score = _clamp(op.score + 8)
                    op.reasons.append("Boost SPY: piso / rebote — favorecen CALLs.")
                    op.confidence = _confidence(op.score)

        opps = apply_golden_rules(opps, h)
        opps = suggest_3sem(opps, zona, ticker)
        enote = earnings_bias_note(ticker, zona, trend_d)
        if enote:
            result["earnings_note"] = enote
            result["warnings"].append(enote)

        by_code: dict[str, Opportunity] = {}
        for op in opps:
            key = f"{op.code}:{op.direction}"
            if key not in by_code or op.score > by_code[key].score:
                by_code[key] = op
        opps = sorted(by_code.values(), key=lambda o: o.score, reverse=True)

        calls = [o for o in opps if o.direction == "CALL"]
        puts = [o for o in opps if o.direction == "PUT"]
        result["opportunities"] = [o.to_dict() for o in opps]
        result["top_call"] = calls[0].to_dict() if calls else None
        result["top_put"] = puts[0].to_dict() if puts else None

        bias = 0.0
        if trend_h == "alza":
            bias += 1
        if trend_h == "baja":
            bias -= 1
        if trend_d == "alza":
            bias += 1
        if trend_d == "baja":
            bias -= 1
        if spy_ctx.get("boost_put"):
            bias -= 1.2
        if spy_ctx.get("boost_call"):
            bias += 0.8
        result["market_bias"] = "alcista" if bias >= 1.5 else "bajista" if bias <= -1.5 else "neutral"

        result["series_1h"] = _series_payload(h.tail(90), [20, 40])
        result["series_1d"] = _series_payload(d.tail(200), [20, 40, 100, 200]) if not d.empty else None
        result["series_spy_1d"] = (
            _series_payload(spy_d.tail(200), [20, 40, 100, 200])
            if spy_d is not None and not spy_d.empty
            else (result["series_1d"] if ticker == "SPY" else None)
        )
    except Exception as e:
        result["ok"] = False
        result["error"] = f"Error analizando {ticker}: {e}"
    return result


def rank_watchlist(results: list[dict]) -> list[dict]:
    ranked = []
    for r in results:
        if not r.get("ok"):
            ranked.append({**r, "best_score": 0, "best_direction": None, "best_strategy": None})
            continue
        opps = r.get("opportunities") or []
        base = {
            "ticker": r.get("ticker"), "ok": True,
            "trend_1h": r.get("trend_1h"), "trend_1d": r.get("trend_1d"),
            "zona": r.get("zona"), "market_bias": r.get("market_bias"),
            "last_price": r.get("last_price"), "top_call": r.get("top_call"),
            "top_put": r.get("top_put"), "error": None,
        }
        if not opps:
            ranked.append({**base, "best_score": 0, "best_direction": None, "best_strategy": None, "opportunities_count": 0})
            continue
        best = opps[0]
        ranked.append({
            **base,
            "best_score": best["score"],
            "best_direction": best["direction"],
            "best_strategy": best["strategy"],
            "best_code": best.get("code"),
            "opportunities_count": len(opps),
        })
    ranked.sort(key=lambda x: x.get("best_score") or 0, reverse=True)
    return ranked
