"""Fetch OHLCV + company info via yfinance for Método Cardona app.

Intraday fetches include extended hours (prepost=True). Short TTL cache keeps
charts near real-time without hammering Yahoo.
"""
from __future__ import annotations

import time
from datetime import datetime, time as dtime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

# Short-lived cache so UI reloads / live poll don't hammer Yahoo
_OHLCV_CACHE: dict[str, tuple[float, pd.DataFrame]] = {}
_COMPANY_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_COMPANY_TTL_SEC = 600.0

# Intraday (1h / 15m / 5m): <=15s so live poll stays fresh
_INTRADAY_TTL_SEC = 12.0
_DAILY_TTL_SEC = 60.0
_WEEKLY_TTL_SEC = 120.0

ET = ZoneInfo("America/New_York")
CDMX = ZoneInfo("America/Mexico_City")

# Regular session (US equities) in America/New_York
_RTH_OPEN = dtime(9, 30)
_RTH_CLOSE = dtime(16, 0)
# Extended hours roughly 4:00–9:30 pre, 16:00–20:00 post
_PRE_OPEN = dtime(4, 0)
_POST_CLOSE = dtime(20, 0)


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df


def _cache_key(ticker: str, interval: str, period: str, prepost: bool) -> str:
    return f"{ticker}|{interval}|{period}|pp={int(prepost)}"


def _ttl_for(interval: str) -> float:
    if interval in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"):
        return _INTRADAY_TTL_SEC
    if interval in ("1wk", "1w"):
        return _WEEKLY_TTL_SEC
    return _DAILY_TTL_SEC


def _is_intraday(interval: str) -> bool:
    return interval in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h")


def session_label_for_bar(ts) -> str:
    """Return 'pre' | 'rth' | 'post' | 'closed' for a bar timestamp."""
    try:
        if getattr(ts, "tzinfo", None) is None:
            # Assume ET if naive (yfinance sometimes returns naive)
            ts = pd.Timestamp(ts).tz_localize(ET)
        else:
            ts = pd.Timestamp(ts).tz_convert(ET)
    except Exception:
        return "rth"
    t = ts.timetz().replace(tzinfo=None) if hasattr(ts, "timetz") else ts.time()
    # weekday: Mon=0 .. Sun=6
    if ts.weekday() >= 5:
        return "closed"
    if _RTH_OPEN <= t < _RTH_CLOSE:
        return "rth"
    if _PRE_OPEN <= t < _RTH_OPEN:
        return "pre"
    if _RTH_CLOSE <= t < _POST_CLOSE:
        return "post"
    return "closed"


def filter_regular_session(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only regular-trading-hours bars (for Cardona signals / MAs)."""
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    mask = []
    for idx in df.index:
        mask.append(session_label_for_bar(idx) == "rth")
    out = df.loc[mask].copy()
    return out


def annotate_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """Add Session column: pre / rth / post / closed."""
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    out = df.copy()
    out["Session"] = [session_label_for_bar(i) for i in out.index]
    return out


def market_session_now() -> dict[str, str]:
    """Current US equity session label for UI (es-MX)."""
    now_et = datetime.now(tz=ET)
    now_cdmx = now_et.astimezone(CDMX)
    label_key = session_label_for_bar(now_et)
    labels = {
        "pre": "Pre-market",
        "rth": "Mercado abierto",
        "post": "After hours",
        "closed": "Cerrado",
    }
    return {
        "session": label_key,
        "session_label": labels.get(label_key, "Cerrado"),
        "now_et": now_et.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "now_cdmx": now_cdmx.strftime("%d/%m/%Y %H:%M:%S") + " CDMX",
        "now_cdmx_short": now_cdmx.strftime("%H:%M:%S") + " CDMX",
    }


def fetch_ohlcv(
    ticker: str,
    interval: str = "1h",
    period: Optional[str] = None,
    *,
    prepost: Optional[bool] = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    ticker = ticker.upper().strip()
    if not ticker:
        return pd.DataFrame()
    if period is None:
        if interval in ("5m", "15m"):
            period = "10d"
        elif interval == "1h":
            period = "60d"
        elif interval in ("1wk", "1w"):
            period = "5y"
        else:
            period = "2y"
    if prepost is None:
        prepost = _is_intraday(interval)

    key = _cache_key(ticker, interval, period, bool(prepost))
    now = time.time()
    if use_cache:
        hit = _OHLCV_CACHE.get(key)
        if hit and (now - hit[0]) < _ttl_for(interval):
            return hit[1].copy()

    try:
        t = yf.Ticker(ticker)
        kwargs: dict[str, Any] = {
            "period": period,
            "interval": interval,
            "auto_adjust": True,
        }
        if prepost and _is_intraday(interval):
            kwargs["prepost"] = True
        df = t.history(**kwargs)
        if df is None or df.empty:
            dl_kwargs = dict(
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
                threads=False,
            )
            if prepost and _is_intraday(interval):
                dl_kwargs["prepost"] = True
            df = yf.download(ticker, **dl_kwargs)
        df = _flatten_columns(df)
        if df.empty:
            return pd.DataFrame()
        cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        df = df[cols].dropna(how="any")
        df = annotate_sessions(df)
        _OHLCV_CACHE[key] = (now, df.copy())
        return df
    except Exception:
        return pd.DataFrame()


def fetch_pair(ticker: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    h = fetch_ohlcv(ticker, "1h", "60d", prepost=True)
    d = fetch_ohlcv(ticker, "1d", "2y", prepost=False)
    return h, d


def fetch_triple(ticker: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Hourly (w/ extended), daily and weekly OHLCV."""
    h = fetch_ohlcv(ticker, "1h", "60d", prepost=True)
    d = fetch_ohlcv(ticker, "1d", "2y", prepost=False)
    w = fetch_ohlcv(ticker, "1wk", "5y", prepost=False)
    return h, d, w


def fetch_intraday(ticker: str, interval: str = "15m") -> pd.DataFrame:
    """Finer intraday with extended hours (5m or 15m)."""
    if interval not in ("5m", "15m", "1h"):
        interval = "15m"
    period = "10d" if interval in ("5m", "15m") else "60d"
    return fetch_ohlcv(ticker, interval, period, prepost=True)


def patch_daily_with_live(df_daily: pd.DataFrame, df_intra: pd.DataFrame) -> pd.DataFrame:
    """Update last daily bar OHLC with latest extended-hours price when available."""
    if df_daily is None or df_daily.empty or df_intra is None or df_intra.empty:
        return df_daily
    out = df_daily.copy()
    last_i = df_intra.iloc[-1]
    last_price = float(last_i["Close"])
    # Mutate last daily row to reflect live / extended last
    idx = out.index[-1]
    row = out.loc[idx]
    high = max(float(row["High"]), last_price, float(last_i["High"]))
    low = min(float(row["Low"]), last_price, float(last_i["Low"]))
    out.loc[idx, "Close"] = last_price
    out.loc[idx, "High"] = high
    out.loc[idx, "Low"] = low
    return out


def fetch_spy() -> tuple[pd.DataFrame, pd.DataFrame]:
    return fetch_pair("SPY")


def _fmt_market_cap(val: Any) -> Optional[str]:
    """Format market cap for es-MX UI (billón = 1e12)."""
    try:
        n = float(val)
    except (TypeError, ValueError):
        return None
    if n != n or n <= 0:  # NaN or non-positive
        return None
    abs_n = abs(n)
    if abs_n >= 1e12:
        return f"${n / 1e12:.2f}T · {n / 1e12:.2f} billones USD"
    if abs_n >= 1e9:
        return f"${n / 1e9:.2f}B · {n / 1e9:.2f} mil millones USD"
    if abs_n >= 1e6:
        return f"${n / 1e6:.2f}M · {n / 1e6:.2f} millones USD"
    return f"${n:,.0f} USD"


def _empty_company(ticker: str) -> dict[str, Any]:
    return {
        "name": ticker or None,
        "sector": None,
        "industry": None,
        "summary": None,
        "exchange": None,
        "currency": None,
        "market_cap": None,
        "market_cap_raw": None,
        "website": None,
        "country": None,
        "quote_type": None,
    }


def _from_search(ticker: str) -> dict[str, Any]:
    """Yahoo Search often works when quoteSummary crumb is blocked."""
    out: dict[str, Any] = {}
    try:
        s = yf.Search(ticker, max_results=8)
        quotes = getattr(s, "quotes", None) or []
        hit = None
        for q in quotes:
            if str(q.get("symbol") or "").upper() == ticker.upper():
                hit = q
                break
        if hit is None and quotes:
            hit = quotes[0]
        if not hit:
            return out
        out["name"] = hit.get("longname") or hit.get("shortname")
        out["sector"] = hit.get("sector") or hit.get("sectorDisp")
        out["industry"] = hit.get("industry") or hit.get("industryDisp")
        out["exchange"] = hit.get("exchDisp") or hit.get("exchange")
        out["quote_type"] = hit.get("quoteType") or hit.get("typeDisp")
    except Exception:
        pass
    return out


def _from_history_meta(ticker: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        t = yf.Ticker(ticker)
        meta = {}
        if hasattr(t, "get_history_metadata"):
            meta = t.get_history_metadata() or {}
        elif hasattr(t, "history_metadata"):
            meta = t.history_metadata or {}
        if not isinstance(meta, dict):
            return out
        out["name"] = meta.get("longName") or meta.get("shortName")
        out["exchange"] = meta.get("fullExchangeName") or meta.get("exchangeName")
        out["currency"] = meta.get("currency")
        out["quote_type"] = meta.get("instrumentType")
    except Exception:
        pass
    return out


def _from_fast_info(ticker: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        fi = yf.Ticker(ticker).fast_info
        out["currency"] = getattr(fi, "currency", None)
        out["exchange"] = getattr(fi, "exchange", None)
        out["market_cap_raw"] = getattr(fi, "market_cap", None) or getattr(fi, "marketCap", None)
    except Exception:
        pass
    return out


def _from_info_best_effort(ticker: str) -> dict[str, Any]:
    """May fail with Invalid Crumb — still try for longBusinessSummary."""
    out: dict[str, Any] = {}
    info: dict = {}
    try:
        t = yf.Ticker(ticker)
        try:
            info = t.get_info() or {}
        except Exception:
            info = {}
        if not info:
            try:
                info = t.info or {}
            except Exception:
                info = {}
    except Exception:
        info = {}
    if not isinstance(info, dict) or not info:
        return out
    out["name"] = info.get("longName") or info.get("shortName") or info.get("displayName")
    out["sector"] = info.get("sector") or info.get("category")
    out["industry"] = info.get("industry") or info.get("industryDisp")
    summary = info.get("longBusinessSummary") or info.get("description")
    if isinstance(summary, str):
        summary = summary.strip() or None
        if summary and len(summary) > 720:
            summary = summary[:717].rstrip() + "…"
    else:
        summary = None
    out["summary"] = summary
    out["exchange"] = info.get("fullExchangeName") or info.get("exchange")
    out["currency"] = info.get("currency") or info.get("financialCurrency")
    out["market_cap_raw"] = info.get("marketCap") or info.get("enterpriseValue")
    out["website"] = info.get("website")
    out["country"] = info.get("country")
    out["quote_type"] = info.get("quoteType")
    return out


def fetch_company_info(ticker: str) -> dict[str, Any]:
    """Company / stock description with crumb-failure resilient fallbacks."""
    ticker = ticker.upper().strip()
    empty = _empty_company(ticker)
    if not ticker:
        return empty

    now = time.time()
    cached = _COMPANY_CACHE.get(ticker)
    if cached and (now - cached[0]) < _COMPANY_TTL_SEC:
        return dict(cached[1])

    search = _from_search(ticker)
    meta = _from_history_meta(ticker)
    fast = _from_fast_info(ticker)
    info = _from_info_best_effort(ticker)

    raw_cap = (
        info.get("market_cap_raw")
        or fast.get("market_cap_raw")
    )
    try:
        raw_cap_num = float(raw_cap) if raw_cap is not None else None
        if raw_cap_num is not None and (raw_cap_num != raw_cap_num or raw_cap_num <= 0):
            raw_cap_num = None
    except (TypeError, ValueError):
        raw_cap_num = None

    name = (
        info.get("name")
        or meta.get("name")
        or search.get("name")
        or ticker
    )
    sector = info.get("sector") or search.get("sector")
    industry = info.get("industry") or search.get("industry")
    exchange = (
        info.get("exchange")
        or meta.get("exchange")
        or search.get("exchange")
        or fast.get("exchange")
    )
    currency = info.get("currency") or meta.get("currency") or fast.get("currency")
    summary = info.get("summary")
    if not summary and (sector or industry):
        bits = [f"Sector: {sector}" if sector else None, f"Industria: {industry}" if industry else None]
        bits = [b for b in bits if b]
        summary = (
            f"{name} — {', '.join(bits)}. "
            "Descripción larga no disponible temporalmente (Yahoo Finance)."
        )

    result = {
        "name": name,
        "sector": sector,
        "industry": industry,
        "summary": summary,
        "exchange": exchange,
        "currency": currency,
        "market_cap": _fmt_market_cap(raw_cap_num),
        "market_cap_raw": int(raw_cap_num) if raw_cap_num is not None else None,
        "website": info.get("website"),
        "country": info.get("country"),
        "quote_type": info.get("quote_type") or meta.get("quote_type") or search.get("quote_type"),
    }
    _COMPANY_CACHE[ticker] = (now, dict(result))
    return result
