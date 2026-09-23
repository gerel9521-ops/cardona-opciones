# Método Cardona — Analizador de opciones CALL/PUT

Aplicación web educativa en español (es-MX) que analiza oportunidades de **opciones sobre acciones** (CALL/PUT) según conceptos del Método Cardona / Seminario Creando Riqueza.

> **No son opciones binarias.** No es asesoría financiera. No garantiza resultados.

## Cómo ejecutar

```bash
cd /workspace/cardona-opciones
python3 -m venv .venv          # si aún no existe
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8765
```

Abre: **http://127.0.0.1:8765**

## Estructura

- `cardona_engine.py` — motor determinista (todas las estrategias con códigos)
- `data_fetcher.py` — OHLCV vía `yfinance` (1h + 1d + SPY)
- `main.py` — FastAPI
- `static/` — SPA (HTML/CSS/JS + Plotly)
- `ESTRATEGIAS.md` — catálogo paso a paso

## Estrategias implementadas

**PUT:** 1V-R, RP-GAP, 4P, HD, VRF-E, TF  
**CALL:** RT, PM-40H, CN, CF, RCB, GAP-NA, GAP-BA, PF, 1GAP-A, VR-R (inverso)  
**Otras:** 3SEM, SPY-CTX, filtro earnings, notas TNA/TZA

## Limitaciones

- Datos de Yahoo pueden tener retraso / huecos.
- Canales y techos/pisos se aproximan con regresión y swings (no dibujo manual).
- Umbrales en USD (estilo SPY) se adaptan por % en otros tickers.
