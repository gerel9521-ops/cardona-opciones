"""Fetch OHLCV + company info via yfinance for Método Cardona app."""
from __future__ import annotations

import time
from typing import Any, Optional

import pandas as pd
import yfinance as yf

# Short-lived cache so UI reloads don't hammer Yahoo crumb endpoints
_COMPANY_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_COMPANY_TTL_SEC = 600.0


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df


def fetch_ohlcv(
    ticker: str,
    interval: str = "1h",
    period: Optional[str] = None,
) -> pd.DataFrame:
    ticker = ticker.upper().strip()
    if not ticker:
        return pd.DataFrame()
    if period is None:
        if interval == "1h":
            period = "60d"
        elif interval in ("1wk", "1w"):
            period = "5y"
        else:
            period = "2y"
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if df is None or df.empty:
            df = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
                threads=False,
            )
        df = _flatten_columns(df)
        if df.empty:
            return pd.DataFrame()
        cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        df = df[cols].dropna(how="any")
        return df
    except Exception:
        return pd.DataFrame()


def fetch_pair(ticker: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    h = fetch_ohlcv(ticker, "1h", "60d")
    d = fetch_ohlcv(ticker, "1d", "2y")
    return h, d


def fetch_triple(ticker: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Hourly, daily and weekly OHLCV."""
    h = fetch_ohlcv(ticker, "1h", "60d")
    d = fetch_ohlcv(ticker, "1d", "2y")
    w = fetch_ohlcv(ticker, "1wk", "5y")
    return h, d, w


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
    # Prefer compact USD ticker labels ($4.96T) + Spanish long form
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

    # Layer sources: search + history meta work without crumb; info is best-effort
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
