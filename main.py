"""
Método Cardona — Analizador de opciones CALL/PUT (educativo).
FastAPI backend + SPA estática (PWA móvil).
"""
from __future__ import annotations

import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from cardona_engine import (
    DEFAULT_WATCHLIST,
    STRATEGIES_CATALOG,
    add_mas,
    analyze_ticker,
    ensure_ohlcv,
    hourly_trend,
    rank_watchlist,
    trend_detail_weekly,
    _series_payload,
)
from data_fetcher import (
    fetch_company_info,
    fetch_intraday,
    fetch_ohlcv,
    fetch_pair,
    fetch_spy,
    fetch_triple,
    market_session_now,
    patch_daily_with_live,
)
from theory_content import get_theory_payload

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"
CDMX = ZoneInfo("America/Mexico_City")

app = FastAPI(
    title="Método Cardona — Opciones",
    description="Herramienta educativa de análisis CALL/PUT (no es asesoría financiera).",
    version="1.9.0",
)

app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


class AnalyzeRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=12)
    drop_forming: bool = True


class ScanRequest(BaseModel):
    tickers: Optional[list[str]] = None
    drop_forming: bool = True


def _now_stamps() -> dict[str, str]:
    now_utc = datetime.now(tz=ZoneInfo("UTC"))
    now_local = now_utc.astimezone(CDMX)
    sess = market_session_now()
    return {
        "updated_at": now_utc.isoformat().replace("+00:00", "Z"),
        "updated_at_local": now_local.strftime("%d/%m/%Y %H:%M:%S") + " CDMX",
        "session": sess.get("session", "closed"),
        "session_label": sess.get("session_label", "Cerrado"),
        "live": True,
    }


def _weekly_series(df_w) -> Optional[dict]:
    if df_w is None or getattr(df_w, "empty", True):
        return None
    w = ensure_ohlcv(df_w)
    if w.empty:
        return None
    w = add_mas(w, [20, 40])
    return _series_payload(w.tail(120), [20, 40])


def _bias_from_scores(
    top_call: Optional[dict],
    top_put: Optional[dict],
    trend: str,
    zona: str,
    *,
    short: bool,
) -> tuple[str, float]:
    """Return (CALL|PUT|neutral, confidence 0-1) from signals + trend/zone."""
    call_s = float((top_call or {}).get("score") or 0)
    put_s = float((top_put or {}).get("score") or 0)
    score = 0.0

    if call_s >= 55 and call_s >= put_s + 5:
        score += 1.2
    elif put_s >= 55 and put_s >= call_s + 5:
        score -= 1.2
    elif call_s >= 45 and call_s > put_s:
        score += 0.6
    elif put_s >= 45 and put_s > call_s:
        score -= 0.6

    if trend == "alza":
        score += 0.9 if short else 1.0
    elif trend == "baja":
        score -= 0.9 if short else 1.0

    if short:
        if zona == "barata":
            score += 0.35
        elif zona == "cara":
            score -= 0.35
    else:
        if zona == "barata":
            score += 0.55
        elif zona == "cara":
            score -= 0.55

    if score >= 0.85:
        bias = "CALL"
    elif score <= -0.85:
        bias = "PUT"
    else:
        bias = "neutral"

    conf = min(0.92, 0.35 + abs(score) * 0.22 + max(call_s, put_s) / 250.0)
    if bias == "neutral":
        conf = min(conf, 0.55)
    return bias, round(conf, 2)


def _conf_label(c: float) -> str:
    if c >= 0.72:
        return "alta"
    if c >= 0.52:
        return "media"
    return "baja"


def build_forecast(analysis: dict[str, Any], trend_1wk: Optional[str] = None) -> dict[str, Any]:
    """Deterministic Spanish forecast from engine outputs (educativo)."""
    trend_h = analysis.get("trend_1h") or "lateral"
    trend_d = analysis.get("trend_1d") or "lateral"
    zona = analysis.get("zona") or "neutral"
    market_bias = analysis.get("market_bias") or "neutral"
    spy = analysis.get("spy_context") or {}
    top_call = analysis.get("top_call")
    top_put = analysis.get("top_put")
    ticker = analysis.get("ticker") or ""

    short_bias, short_conf = _bias_from_scores(top_call, top_put, trend_h, zona, short=True)
    # Align short bias lightly with market_bias when signals are weak
    if short_bias == "neutral":
        if market_bias == "alcista":
            short_bias = "CALL"
            short_conf = max(short_conf, 0.48)
        elif market_bias == "bajista":
            short_bias = "PUT"
            short_conf = max(short_conf, 0.48)

    long_trend = trend_1wk or trend_d
    long_bias, long_conf = _bias_from_scores(top_call, top_put, long_trend, zona, short=False)
    if spy.get("boost_put") and long_bias != "CALL":
        long_bias = "PUT"
        long_conf = min(0.9, long_conf + 0.08)
    elif spy.get("boost_call") and long_bias != "PUT":
        long_bias = "CALL"
        long_conf = min(0.9, long_conf + 0.06)

    # Short summary
    short_bits = [
        f"Tendencia horaria: {trend_h}.",
        f"Zona Cardona: {zona}.",
    ]
    if top_call and (not top_put or float(top_call.get("score") or 0) >= float(top_put.get("score") or 0)):
        short_bits.append(
            f"Mejor setup corto: CALL {top_call.get('code')} (score {top_call.get('score')})."
        )
    elif top_put:
        short_bits.append(
            f"Mejor setup corto: PUT {top_put.get('code')} (score {top_put.get('score')})."
        )
    else:
        short_bits.append("Sin setup CALL/PUT dominante en 1h en este momento.")
    short_bits.append(
        f"Sesgo educativo a 1–5 días: {short_bias} "
        f"(confianza {_conf_label(short_conf)}). No es recomendación de compra/venta."
    )

    # Long summary
    long_bits = [
        f"Tendencia diaria: {trend_d}" + (f"; semanal: {trend_1wk}." if trend_1wk else "."),
        f"Zona vs PM100/PM200: {zona}.",
    ]
    spy_z = spy.get("zona")
    if spy_z:
        long_bits.append(
            f"Contexto SPY: zona {spy_z}, tendencia {spy.get('trend_daily', '—')}"
            + (", boost PUT" if spy.get("boost_put") else "")
            + (", boost CALL" if spy.get("boost_call") else "")
            + "."
        )
    long_bits.append(
        f"Sesgo educativo a semanas: {long_bias} "
        f"(confianza {_conf_label(long_conf)}). Señales del método; no garantiza resultados."
    )
    if ticker:
        long_bits.append(f"Revisar {ticker} con SPY (~70% de atención) antes de cualquier setup.")

    return {
        "disclaimer": (
            "Pronóstico educativo basado en señales del Método Cardona "
            "(tendencias, zonas y setups). No es asesoría financiera ni garantía de resultados."
        ),
        "short": {
            "bias": short_bias,
            "horizon": "1–5 días",
            "summary": " ".join(short_bits),
            "confidence": _conf_label(short_conf),
            "confidence_score": short_conf,
            "inputs": {
                "trend_1h": trend_h,
                "zona": zona,
                "market_bias": market_bias,
                "top_call_score": (top_call or {}).get("score"),
                "top_put_score": (top_put or {}).get("score"),
            },
        },
        "long": {
            "bias": long_bias,
            "horizon": "semanas",
            "summary": " ".join(long_bits),
            "confidence": _conf_label(long_conf),
            "confidence_score": long_conf,
            "inputs": {
                "trend_1d": trend_d,
                "trend_1wk": trend_1wk,
                "zona": zona,
                "spy_zona": spy.get("zona"),
                "spy_boost_put": bool(spy.get("boost_put")),
                "spy_boost_call": bool(spy.get("boost_call")),
            },
        },
    }


def enrich_analysis(result: dict[str, Any], df_weekly=None, company: Optional[dict] = None) -> dict[str, Any]:
    """Attach timestamps, company, charts.weekly and forecast to analyze payload."""
    result = dict(result)
    result.update(_now_stamps())
    result["company"] = company or {
        "name": result.get("ticker"),
        "sector": None,
        "industry": None,
        "summary": None,
        "exchange": None,
        "currency": None,
        "market_cap": None,
    }

    series_w = _weekly_series(df_weekly)
    trend_1wk = None
    detail_w = None
    if df_weekly is not None and not getattr(df_weekly, "empty", True):
        try:
            w = add_mas(ensure_ohlcv(df_weekly), [20, 40])
            if len(w) >= 5:
                trend_1wk = hourly_trend(w)  # PM20 vs PM40 on weekly frame
                detail_w = trend_detail_weekly(w)
        except Exception:
            trend_1wk = None
            detail_w = None
    result["trend_1wk"] = trend_1wk

    td = dict(result.get("trend_detail") or {})
    if detail_w is not None:
        td["weekly"] = detail_w
    elif "weekly" not in td:
        td["weekly"] = trend_detail_weekly(None)
    result["trend_detail"] = td

    # 15m extended-hours series for finer live chart (signals still use 1h RTH)
    series_15m = None
    try:
        ticker = result.get("ticker") or ""
        if ticker:
            df15 = fetch_intraday(ticker, "15m")
            if df15 is not None and not getattr(df15, "empty", True):
                frame15 = add_mas(ensure_ohlcv(df15), [20, 40])
                series_15m = _series_payload(frame15.tail(180), [20, 40])
    except Exception:
        series_15m = None

    result["charts"] = {
        "m15": series_15m,
        "hourly": result.get("series_1h"),
        "daily": result.get("series_1d"),
        "weekly": series_w,
        "spy_daily": result.get("series_spy_1d"),
    }
    result["series_15m"] = series_15m
    result["series_1wk"] = series_w
    result["extended_hours"] = True
    result["forecast"] = build_forecast(result, trend_1wk=trend_1wk)
    return result


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = STATIC / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>Falta static/index.html</h1>", status_code=500)
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/sw.js")
def service_worker():
    """Serve SW at root so scope covers the whole app."""
    sw_path = STATIC / "sw.js"
    if not sw_path.exists():
        raise HTTPException(404, "Service worker no encontrado")
    return Response(
        content=sw_path.read_text(encoding="utf-8"),
        media_type="application/javascript; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Service-Worker-Allowed": "/",
        },
    )


@app.get("/manifest.webmanifest")
def manifest_root():
    path = STATIC / "manifest.webmanifest"
    if not path.exists():
        raise HTTPException(404, "Manifest no encontrado")
    return FileResponse(
        path,
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/api/health")
def health():
    sess = market_session_now()
    return {
        "status": "ok",
        "app": "cardona-opciones",
        "strategies": len(STRATEGIES_CATALOG),
        "pwa": True,
        "version": "1.9.0-realtime-welcome",
        "realtime": True,
        "extended_hours": True,
        "session": sess.get("session"),
        "session_label": sess.get("session_label"),
    }


@app.get("/api/watchlist")
def watchlist():
    return {"watchlist": DEFAULT_WATCHLIST}


@app.get("/api/strategies")
def strategies():
    return {"strategies": STRATEGIES_CATALOG, "count": len(STRATEGIES_CATALOG)}


@app.get("/api/theory")
def theory():
    """Full educational theory for all Cardona techniques (es-MX)."""
    return get_theory_payload()



@app.get("/api/chart/{ticker}")
def api_chart(
    ticker: str,
    tf: str = Query("hourly", description="hourly|15m|5m|daily|weekly"),
):
    """Lightweight live chart series with extended hours (for polling)."""
    ticker = ticker.upper().strip()
    if not ticker.replace(".", "").isalnum():
        raise HTTPException(400, "Ticker inválido.")
    tf = (tf or "hourly").lower().strip()
    try:
        stamps = _now_stamps()
        if tf in ("15m", "5m"):
            df = fetch_intraday(ticker, tf)
            if df.empty:
                return {"ok": False, "ticker": ticker, "error": "Sin datos", "series": None, **stamps}
            from cardona_engine import add_mas, ensure_ohlcv, _series_payload
            frame = add_mas(ensure_ohlcv(df), [20, 40])
            series = _series_payload(frame.tail(180), [20, 40])
            return {
                "ok": True,
                "ticker": ticker,
                "tf": tf,
                "interval": tf,
                "extended_hours": True,
                "series": series,
                "mas": [20, 40],
                **stamps,
            }
        if tf == "weekly":
            df = fetch_ohlcv(ticker, "1wk", "5y", prepost=False)
            from cardona_engine import add_mas, ensure_ohlcv, _series_payload
            frame = add_mas(ensure_ohlcv(df), [20, 40])
            series = _series_payload(frame.tail(120), [20, 40]) if not frame.empty else None
            return {
                "ok": bool(series),
                "ticker": ticker,
                "tf": "weekly",
                "interval": "1wk",
                "extended_hours": False,
                "series": series,
                "mas": [20, 40],
                **stamps,
            }
        if tf == "daily":
            d = fetch_ohlcv(ticker, "1d", "2y", prepost=False)
            # Patch last bar with latest extended/intraday price
            intra = fetch_intraday(ticker, "15m")
            if not d.empty and not intra.empty:
                d = patch_daily_with_live(d, intra)
            from cardona_engine import add_mas, ensure_ohlcv, _series_payload
            frame = add_mas(ensure_ohlcv(d), [20, 40, 100, 200])
            series = _series_payload(frame.tail(200), [20, 40, 100, 200]) if not frame.empty else None
            return {
                "ok": bool(series),
                "ticker": ticker,
                "tf": "daily",
                "interval": "1d",
                "extended_hours": True,
                "series": series,
                "mas": [20, 40, 100, 200],
                **stamps,
            }
        # hourly default — 1h with prepost
        h = fetch_ohlcv(ticker, "1h", "60d", prepost=True)
        from cardona_engine import add_mas, ensure_ohlcv, _series_payload
        frame = add_mas(ensure_ohlcv(h), [20, 40])
        series = _series_payload(frame.tail(120), [20, 40]) if not frame.empty else None
        return {
            "ok": bool(series),
            "ticker": ticker,
            "tf": "hourly",
            "interval": "1h",
            "extended_hours": True,
            "series": series,
            "mas": [20, 40],
            **stamps,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Error gráfica: {e}") from e


@app.post("/api/analyze")
def api_analyze(body: AnalyzeRequest):
    ticker = body.ticker.upper().strip()
    if not ticker.replace(".", "").isalnum():
        raise HTTPException(400, "Ticker inválido.")
    try:
        spy_h, spy_d = fetch_spy()
        h, d, w = fetch_triple(ticker)
        company = fetch_company_info(ticker)
        if h.empty:
            out = {
                "ok": False,
                "ticker": ticker,
                "error": f"No se encontraron datos para «{ticker}». Verifica el símbolo.",
                "opportunities": [],
                "strategies_catalog": STRATEGIES_CATALOG,
                "company": company,
                "charts": {"m15": None, "hourly": None, "daily": None, "weekly": None, "spy_daily": None},
                "forecast": None,
            }
            out.update(_now_stamps())
            return out
        result = analyze_ticker(ticker, h, d, spy_h, spy_d, drop_forming=body.drop_forming)
        return enrich_analysis(result, df_weekly=w, company=company)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Error interno: {e}") from e


@app.get("/api/analyze/{ticker}")
def api_analyze_get(ticker: str, drop_forming: bool = Query(True)):
    return api_analyze(AnalyzeRequest(ticker=ticker, drop_forming=drop_forming))


@app.post("/api/scan")
def api_scan(body: ScanRequest):
    tickers = body.tickers or DEFAULT_WATCHLIST
    tickers = [t.upper().strip() for t in tickers if t and t.strip()]
    tickers = list(dict.fromkeys(tickers))[:15]
    try:
        spy_h, spy_d = fetch_spy()
        results = []
        for t in tickers:
            try:
                h, d = fetch_pair(t)
                if h.empty:
                    results.append({"ok": False, "ticker": t, "error": f"Sin datos para {t}", "opportunities": []})
                    continue
                results.append(analyze_ticker(t, h, d, spy_h, spy_d, drop_forming=body.drop_forming))
            except Exception as e:
                results.append({"ok": False, "ticker": t, "error": str(e), "opportunities": []})
        ranked = rank_watchlist(results)
        by_ticker = {r["ticker"]: r for r in results}
        for item in ranked:
            full = by_ticker.get(item["ticker"], {})
            item["opportunities"] = full.get("opportunities", [])
            item["spy_context"] = full.get("spy_context", {})
        out = {
            "ok": True,
            "ranked": ranked,
            "spy_context": next((r.get("spy_context") for r in results if r.get("spy_context")), {}),
            "count": len(ranked),
            "strategies_catalog": STRATEGIES_CATALOG,
        }
        out.update(_now_stamps())
        return out
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Error en escaneo: {e}") from e


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=False)
