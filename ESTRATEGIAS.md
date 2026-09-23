# Método Cardona — Catálogo completo de estrategias

Herramienta educativa. **No es asesoría financiera.** Implementación cuantitativa aproximada de conceptos del Seminario Creando Riqueza / adaptaciones (Frank Soto). Se opera sobre **opciones CALL/PUT de acciones**, no opciones binarias.

Horarios en **America/New_York (ET)**. Preferir siempre **velas finales** (completadas).

---

## Reglas de oro

1. **Evitar 9:30–10:59 ET** excepto la estrategia **1V-R** (PUT a las 10:00).
2. Solo señales sobre **vela final** — nunca la que se está formando.
3. **Mirar SPY primero** (~70% de la atención). Si SPY cae, todo cae.
4. Confirmar con **volumen** relativo cuando la estrategia lo indique.
5. No comprar CALL **dentro** de un canal bajista sin **RCB** (ruptura del techo).

---

## PUT

### 1V-R — 1ra Vela Roja
- **Dirección:** PUT
- **Timeframe:** HORA (1h)
- **Entrada:** Solo **10:00 ET** (única excepción de apertura)
- **Prerrequisitos:** Canal / sesgo bajista; precio cerca o bajo PM40.
- **Pasos:**
  1. Confirmar contexto bajista horario (precio bajo/cerca PM40).
  2. Esperar la primera vela roja horaria de la sesión NY (9:30–10:00).
  3. Cuando esa vela esté **final**, comprar PUT a las 10:00.
- **Notas:** No usar otras estrategias en la ventana 9:30–10:59.

### RP-GAP — Ruptura del Piso del GAP
- **Dirección:** PUT · **TF:** 1h · **Entrada:** desde **11:00 ET**
- **Pasos:**
  1. Detectar gap / apertura verde.
  2. Dibujar piso del gap **incluyendo mecha** (mínimo entre Low y Open del gap).
  3. Esperar vela roja que cierre bajo ese piso.
  4. Comprar PUT desde las 11am.

### 4P — Modelo 4 pasos (verde-rojo rompe)
- **Dirección:** PUT · **TF:** 1h · **Entrada:** desde **11:00 ET**
- **Prerrequisitos:** Canal bajista; zona cara (cerca del techo del canal).
- **Pasos:**
  1. Precio en zona cara / cerca techo.
  2. Verde(s) borrada(s) por roja(s) **o** hanger.
  3. Dibujar piso del rebote alcista corto.
  4. Roja rompe ese piso → PUT.
- **Notas:** Núcleo del patrón **VR-R**.

### HD — Hanger en Diario
- **Dirección:** PUT · **TF:** Diario · **Entrada:** ~**2–3 días** después
- **Zona cara (heurística SPY-scale):** spot−PM40 ≥ 20; dist PM100 ≥ 40; PM40−PM100 ≥ 25 (o % relativo en otros tickers).
- **Secuencia:** hanger → verde baja vol → roja → caída.

### VRF-E — Vela Roja Final Envolvente del Día
- **Dirección:** PUT · **TF:** Diario
- Envolvente bajista en zona cara/techo con **alto volumen** → PUT.

### TF — Techo Fuerte
- Contexto de techo caro: sesgo PUT / precaución en CALLs. Combinar con HD, VRF-E y SPY.

---

## CALL

### RT — Ruptura del Techo
- **TF:** 1h · **Entrada:** **11:00–15:59 ET**
- Tras una caída: ≥2 rojas tocan/rompen PM20/PM40; martillo verde + verde con volumen rompe la **línea de techo** de la caída → CALL.

### PM-40H — Promedio Móvil 40 Hora
- Tendencia alcista (PM20 > PM40 en paralelo). Rojas rompen PM20 y tocan/rompen parcialmente PM40. Verde final vuelve a romper PM20 (11–15:59) → CALL (rebote 1–2 días). En canal alcista, PM40 es piso fuerte.

### CN — Caída Normal
- Caída ~**$3–5** o **<1.5%** (adaptar % en acciones más baratas). 2–3 rojas rompen PM20 pero **no** PM40. Martillo + verde rompe techo → CALL (especialmente viernes).

### CF — Caída Fuerte
- Caída **>$6** o **>1.5%**. Rojas pueden romper PM20/PM40/PM100/PM200. Martillo + verde rompe techo → CALL.

### RCB — Ruptura Canal Bajista (mejor CALL)
- Canal bajista (semanas/meses). PM40 > PM20 cruzado. Martillo + verde con volumen rompe **techo del canal** (11–15:59) → CALL.
- **Regla:** no comprar CALL dentro del canal bajista sin esta ruptura.

### GAP-NA — GAP Normal al Alza
- Sesgo alcista previo. Gap up verde 9:30 + verde/martillo 10am. Vela 11am verde o roja de alto vol. Comprar CALL ~**11–12**. Inestable en canal bajista profundo lejos del techo.

### GAP-BA — GAP Bajista al Alza
- Cierre previo verde. Abre **abajo**, pero 1ª vela verde y 2ª (10am) **DEBE** ser verde; 3ª (11am) verde o alto vol → CALL. Puede durar 3–4 días en canal bajista. Inestable en techo de canal alcista. GAP-BA imperfecto = precaución.

### PF — Piso Fuerte
- Diario toca/cerca PM100/PM200 en la caída. En HORA (parece canal bajista) verde rompe techo del canal. Confirmar diario cerca PM40 → CALL 3–5 días. Si rojas rompen PM200 con fuerza, vigilar caída multi-mes.

### 1GAP-A — 1er GAP al Alza
- Tras ruptura PF, primer gap verde al alza. Respetar piso del gap (con mecha), vela con volumen, validar cierre → CALL a menudo 3–4 días.

### VR-R (inverso CALL)
- Rojas borradas por verdes; verde rompe techo de la caída → CALL (espejo del 4P).

---

## Otras

### 3SEM — Estrategia de las 3 semanas
- **Timeframe principal:** gráfica **semanal** (velas semanales) para juzgar el setup / gran recorrido. Confirmar con diario/contexto si hace falta; la regla operativa de la app es: **se ve en semanal**.
- **Entrada:** comprar la opción **≈5 minutos antes del cierre** del mercado cash US (**≈15:55 ET**; cierre 16:00 ET). Regla operativa del método en la app.
- **Cuándo:** piso muy barato, techo caro, o ruptura clara de canal → CALL o PUT según zona.
- **Vencimiento** ~3 semanas (15–21 días). Strike heurístico cerca ATM / ~2–5% OTM (o ~5–7% en earnings). En la UI se marca `suitable_3sem` y `strike_hint`.

### Filtro Earnings
- CALL si viene de caída + zona piso; PUT si viene de subida + zona techo.
- Strikes ~5–7% alejados; volumen. Nombres preferidos: TSLA, AMZN, META, AAPL, NFLX (NFLX mejor post-earnings).

### SPY-CTX
- Siempre primero. Zona cara + caída → boost PUT. Piso/rebote → boost CALL.

### TNA / TZA (opcional)
- Solo contexto de riesgo (3x bull/bear small-cap). No son señal primaria del método.

---

## Limitaciones de esta implementación

- Canales y “líneas de techo/piso” se aproximan con **regresión lineal** y swings (no dibujo discrecional a mano).
- Umbrales USD de SPY se adaptan por **porcentaje** en otros tickers.
- Datos de Yahoo Finance pueden tener **retraso** y gaps de sesión.
- Volumen relativo vs media 20 barras (umbral ~1.15×).
