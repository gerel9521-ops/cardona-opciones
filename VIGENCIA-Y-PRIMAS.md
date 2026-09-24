# Vigencia, prima y spot-strike — Método Cardona (detalle)

Documento educativo basado en adaptaciones del Seminario Creando Riqueza / Método Cardona.
No es asesoría financiera. Los montos de prima cambian con la volatilidad del mercado; la tabla es una **guía de referencia**, no un precio fijo eterno.

---

## 1. Primero: qué significa 0.25, 0.80, 2.00 y “25–30 dólares”

En opciones sobre acciones de EE.UU. (Interactive Brokers, etc.):

| Lo que ves en pantalla | Significado | Costo real del contrato |
|------------------------|-------------|-------------------------|
| Prima / Ask **0.25** | 0.25 USD **por acción** | **0.25 × 100 = 25 USD** por contrato |
| Prima **0.80** | 0.80 por acción | **80 USD** por contrato |
| Prima **2.00** o **2.50** | 2.00–2.50 por acción | **200–250 USD** por contrato |

Por eso en el material aparecen dos formas de decir lo mismo:

- En la **tabla por ticker**: `COSTO/COST (Ask/Bid) $0.25–$0.30` (cotización por acción).
- En las **reglas de oro (SPY)**: “el precio de compra de mayor rentabilidad debe estar entre **25 y 30 dólares**” = el **contrato** (0.25–0.30 × 100).

**Resumen de tu duda:**  
Sí: **0.20–0.80 en pantalla ≈ 20–80 USD reales** por contrato.  
**2.00 en pantalla ≈ 200 USD** por contrato.  
No son “centavos sueltos”: cada contrato controla 100 acciones.

### Por qué unas acciones van a 0.20–0.80 y otras a ~2.00

No es capricho. La prima depende de:

1. **Precio del subyacente** (acción cara → opciones más caras a la misma distancia %).
2. **Volatilidad implícita** (TSLA, NFLX, MRNA suelen tener IV alta → prima más cara).
3. **Distancia spot–strike** (más lejos del dinero = más barata, pero menos probabilidad).
4. **Días a vencimiento** (más días = más valor temporal = más cara).
5. **Liquidez** (SPY/QQQ tienen muchas strikes baratos y líquidos).

La tabla Cardona **sugiere un rango de prima “trabajable”** por ticker para que, con el movimiento típico que busca la estrategia, la rentabilidad % sea alta sin pagar de más.

---

## 2. Tabla de criterios de compra (referencia del método)

| # | Ticker | Prima Ask/Bid objetivo | ≈ USD por contrato | Volumen vela (ref.) | Distancia spot–strike |
|---|--------|------------------------|--------------------|---------------------|------------------------|
| 1 | SPY | 0.25–0.30 | 25–30 | 20M | ~10 (regla general SPY: 4–10) |
| 2 | QQQ | 0.25–0.30 | 25–30 | 20M | ~10 |
| 3 | GOOG | 0.25–0.30 | 25–30 | 10M | 7–8 |
| 4 | META | 0.45–0.80 | 45–80 | 3M | 20–25 |
| 5 | AAPL | 0.45–0.80 | 45–80 | 20–25M | 2–4 |
| 6 | AMZN | 0.60–0.80 | 60–80 | 16M | 7–8 |
| 7 | NVDA | 0.60–0.80 | 60–80 | 120M | 6–9 |
| 8 | TNA | 0.60–0.80 | 60–80 | 2M | 8–13 |
| 9 | GLD | 0.60–0.80 | 60–80 | 2M | 2–4 |
| 10 | CVX | 0.60–0.80 | 60–80 | 2M | 3–5 |
| 11 | XOM | 0.60–0.80 | 60–80 | 4M | 3–5 |
| 12 | MRNA | ~1.00 | ~100 | 2M | 12–15 |
| 13 | NFLX | 1.50–2.50 | 150–250 | 1M | 12–15 |
| 14 | TSLA | ~2.50 | ~250 | 15M | 8–10 |
| 15 | SLV | 0.10–0.20 | 10–20 | 10M | 1–2 |
| 16 | USO | 0.10–0.20 | 10–20 | 1M | 2–3 |
| 17 | BAC | 0.10–0.20 | 10–20 | 10M | 1–2 |
| 18 | DIS | 0.10–0.20 | 10–20 | 10M | 1–2 |

**Regla SPY (regla de oro #9):**  
- Distancia spot–strike ideal **≥ 4 y ≤ 10** USD. Fuera de eso, “no es rentable” según el método.  
- Si distancia **&lt; 4**: alerta de efecto contrario (en techo no sube / en piso no cae).  
- Prima contrato ideal **25–30 USD** (cotización 0.25–0.30) para máxima rentabilidad en el estilo intradía/corto.

**Nota de realismo (comunidad SCR):** con precios actuales de SPY/acciones, strikes muy cercanos (2–3 USD) a veces cuestan **mucho más** que 25–30 USD por contrato. Entonces hay que elegir: o pagar más (más ITM/ATM), o alejarse del strike (más barato, menos probabilidad). La tabla es un **objetivo**, no una ley física.

**Montos por trade** mencionados en reglas: del orden de **50–100 USD** de riesgo/inversión por operación (escala de aprendizaje), y “no salirse” si se cumplieron las reglas.

---

## 3. Cómo elegir la vigencia (expiración)

El método usa sobre todo **corto plazo**. La vigencia no es “una sola para todas”: depende del **horizonte del movimiento** que promete cada estrategia.

### Modos de vigencia del material SCR (núcleo corto plazo)

| Modo | Qué es | Cuándo |
|------|--------|--------|
| **Mismo día (0DTE)** | Expira hoy | SPY: máxima velocidad de rentabilidad. Preferible si la estrategia aparece **antes del mediodía**. |
| **De un día para otro** | Expira mañana | SPY: si la señal **no** aparece antes de las 12:00; comprar ~**15:50** para el día siguiente (después del mediodía el precio de la 0DTE “cambia y queda solo el paso spot–strike”). |
| **Corto (2–5 días) / semanal** | Expira en pocos días o el viernes siguiente | Estrategias cuyo efecto dura varios días (piso fuerte, GAP-BA, hanger, etc.). |
| **3 semanas** | ~15–21 días | Solo cuando el setup es de **gran recorrido** (piso muy barato, techo muy caro, ruptura clara). |
| **LEAPS / largo (meses–años)** | Vencimiento lejano (a menudo >1 año; p. ej. agosto del año siguiente) | **No es una estrategia numerada del SCR público.** Surge como horizonte de **tesis alcista sostenida** (índices + megacaps). Ver §3.1. **Por confirmar** con material oficial Cardona. |

**Ventana de compra (hora del día):**  
- General: **11:00–15:59 ET** con vela final.  
- SPY/QQQ: hasta ~**16:14**.  
- Única excepción temprana: **1V-R a las 10:00**.


### 3.1 Modo LEAPS / CALL larga (evidencia de cartera + lectura educativa)

> **Estado:** el material público SCR (adaptaciones SlideShare / resúmenes de estrategias CALL-PUT) enseña sobre todo **corto plazo** (0DTE → ~3 semanas). **No** aparece una regla publicada que diga “usar LEAPS”.  
> Lo que sigue combina: (a) definición estándar de LEAPS, (b) captura E*TRADE de trades exitosos del usuario (CALL LEAPS ~ago-2026 en SPY/QQQ/tech), (c) cómo encajaría con el **sesgo** del método (SPY primero, tendencia alcista, no CALL dentro de canal bajista sin RCB).  
> Todo lo marcado **por confirmar** no debe enseñarse como dogma Cardona.

**Qué es una LEAPS (definición de mercado, no SCR):**  
opción cotizada con vencimiento lejano (típicamente **más de un año**). Sigue siendo CALL o PUT; cambia el horizonte y el peso del valor temporal.

**Patrón observado en la captura de Gains & Losses (estudio):**
- Casi todo **CALL** (no PUT en esa foto).
- Vencimiento **LEAPS** ~ **agosto 2026**.
- Núcleo **SPY** (muchas strikes ~754–782) y **QQQ** (~721), más **AMD / META / MSFT / NVDA / DIS**.
- Strikes **OTM / semi-OTM** ambiciosos (no ATM profundo).
- Tamaños grandes en índices; menores en single names.
- **No** es el libro de weeklies/0DTE de esa foto.

**Implicaciones educativas (cómo usarlo junto al método, sin inventar reglas):**
1. Si la tesis es **tendencia alcista de meses** (PM diarias/semanales alcistas, SPY-CTX a favor, sin canal bajista sin romper), una CALL larga puede ser el vehículo — **por confirmar** si Cardona lo enseña explícitamente.
2. Las reglas de **prima 0.25–0.30 (SPY intradía)** **no aplican** a LEAPS: se paga mucho más valor temporal; el objetivo deja de ser “máxima rentabilidad intradía” y pasa a ser **exposición direccional con tiempo**.
3. Distancia spot–strike de **4–10 USD en SPY** es regla de **corto**; en LEAPS OTM la distancia puede ser **mucho mayor** (la captura muestra strikes cientos de puntos arriba en SPY a precios actuales). **% OTM típico: por confirmar.**
4. Encaje natural con setups de **gran recorrido** ya en la app: **3SEM**, **PF**, **RCB**, contexto **SPY-CTX** alcista — no con **1V-R**, **CN** viernes→lunes, ni 0DTE.
5. Gestión: toma de ganancias parciales, rolling y % OTM exacto → **por confirmar** con más material / más capturas.

**Qué NO hacer (educativo):**
- Sustituir un setup intradía (1V-R, RT, CN) por LEAPS “porque sí”.
- Comprar CALL LEAPS **dentro** de canal bajista sin **RCB** (sigue la regla de oro).
- Esperar que la tabla de primas cortas (0.25–0.30) describa el costo de una LEAPS.

---

## 4. Vigencia y lógica de prima **por estrategia**

Para cada una: dirección, vigencia típica, por qué esa vigencia, y qué prima/spot–strike usar (siempre filtrando por la tabla del ticker).

### PUT

#### 1V-R — 1ra Vela Roja
- **Vigencia típica:** mismo día o muy corto (movimiento intradía / sesión).
- **Por qué:** es un golpe de apertura en canal bajista; el edge es inmediato.
- **Hora:** 10:00 ET.
- **Prima:** según tabla del ticker; en SPY apuntar 0.25–0.30 / contrato 25–30 si es posible.
- **Strike:** distancia de la tabla (SPY 4–10).

#### RP-GAP — Ruptura del piso del GAP
- **Vigencia:** intradía a 1–2 días (a menudo se realiza en la misma sesión tras las 11:00).
- **Por qué:** el fallo del gap alcista suele resolverse rápido.
- **Hora:** desde 11:00.
- **Prima/strike:** tabla del ticker.

#### 4P — Modelo 4 pasos / verde-rojo rompe
- **Vigencia:** intradía a 1–3 días.
- **Por qué:** continuación bajista dentro del canal tras borrar el rebote.
- **Hora:** desde 11:00; evitar zona de piso del canal (peor probabilidad).
- **Prima/strike:** tabla.

#### HANGER-D — Hanger en diario
- **Vigencia:** **2–3 días** (PUT “en largo” corto).
- **Por qué:** la secuencia hanger → verde floja → roja → caída tarda unos días.
- **Prima:** puede valer la pena un poco más de valor temporal (no 0DTE agónica si el setup es de 2–3 días).
- **Strike:** no tan OTM que “no llegue” en 2–3 días; usar distancia de tabla.

#### VRE — Vela roja envolvente diaria
- **Vigencia:** 1–3 días (similar a señales diarias de techo).
- **Prima/strike:** tabla; contexto zona cara.

### CALL

#### RT — Ruptura del techo
- **Vigencia:** intradía a **1–3 días** (tras caída fuerte a menudo 1–3 días de alza).
- **Hora:** 11:00–15:59.
- **Prima/strike:** tabla + volumen en la vela de entrada.

#### PM-40H — Promedio móvil 40 hora
- **Vigencia:** **1–2 días** (rebote de resistencia explícito en el material).
- **Prima:** corto plazo; no hace falta 3 semanas.
- **Strike:** cerca, según tabla (AAPL 2–4, SPY 4–10, etc.).

#### CN — Caída normal
- **Vigencia:** intradía / **fin de semana → lunes** (muy citada en viernes; a menudo gap alcista el lunes).
- **Prima:** 0DTE o next-day según hora; si es viernes tarde, lógica “para el lunes”.
- **Strike:** tabla.

#### CF — Caída fuerte
- **Vigencia:** **1–3 días** de rebote típico.
- **Prima:** puede usarse vencimiento de pocos días (no solo minutos).
- **Strike:** tabla; movimiento esperado mayor que en CN.

#### RCB — Ruptura canal bajista (“mejor CALL”)
- **Vigencia:** **2+ días** (ej. AAPL “probable subida × 2 días”; a veces más si cambia de canal).
- **Prima:** corto/semanal; el recorrido puede ser mayor → no tan OTM.
- **Strike:** tabla, preferir strikes que capturen 2–3 días de movimiento.
- **Nota LEAPS (por confirmar):** si la ruptura cambia el canal de **semanas/meses** a alcista y el contexto SPY acompaña, el horizonte “corto” puede quedar corto; valorar 3SEM o, en tesis multi-mes, CALL larga — sin abandonar la regla de **no CALL dentro del canal** sin ruptura.

#### GAP-NA — GAP normal al alza
- **Vigencia:** 
  - Si compras en cierre previo para vender en apertura (premarket): **noche / next open** (a veces se vende a la apertura).
  - Si confirmas a las 11:00: intradía a **varios días** (en canal bajista cerca del techo: 4–6 días mencionados).
- **Hora de compra típica:** ~11:00–12:00 cuando se confirma en sesión.
- **Prima/strike:** tabla; AMZN/NFLX muy citados como efectivos.

#### GAP-BA — GAP bajista al alza
- **Vigencia:** **3–4 días** en canal bajista; **1–2 días** si estás en techo de canal alcista (más inestable).
- **Prima:** conviene vencimiento que cubra 3–4 días, no solo 0DTE si entras a las 11:00 del día 1.
- **Strike:** tabla.

#### PF — Piso fuerte
- **Vigencia:** **3–5 días** (oportunidad cada ~3–4 meses).
- **Prima:** vencimiento semanal o ~1 semana; el movimiento no es de minutos.
- **Strike:** no demasiado OTM; el alza puede ser fuerte pero hay que darle tiempo.
- **Alerta:** si rompen PM200 con fuerza → posible caída larga (meses) → no forzar CALL.
- **Nota LEAPS (por confirmar):** un piso fuerte en SPY/QQQ con PM100/PM200 respetados es el tipo de contexto donde una cartera de estudio usó CALL LEAPS; el SCR público habla de **días**, no de años. Separar el **setup PF (días)** del **overlay LEAPS (meses)**.

#### 1GAP-A — 1er GAP al alza
- **Vigencia:** **3–4 días** típicos.
- **Prima/strike:** como PF; confirmar respeto del piso del gap.

#### TF — Techo fuerte
- **No es compra CALL**; es **contexto** para PUT / precaución.
- Vigencia alineada al PUT que dispare (hanger 2–3 días, etc.).

### Especiales

#### 3 semanas (3SEM / 3S)
- **Timeframe:** gráfica **semanal** (regla operativa del método en la app: el setup se juzga en semanal; confirmar con diario si hace falta).
- **Hora de compra:** **≈15:55 ET** (≈5 minutos antes del cierre cash US a las 16:00 ET).
- **Vigencia:** ~**3 semanas** (15–21 días).
- **Cuándo:** setup de gran recorrido (piso muy barato, techo muy caro, ruptura clara) → CALL o PUT según zona.
- **Strike:** buscar quedar cerca / ITM según tabla de volatilidad a 3 semanas (notas de alumnos: idea de strike “cerca”; en SPY se menciona magnitud grande tipo ±200 en materiales de estudio — **adaptar** al precio actual del activo).
- **Prima:** será **más cara** que 0DTE (más tiempo). Aquí 0.25–0.30 de SPY intradía **no aplica** igual; se paga más valor temporal a cambio de aguantar el movimiento.
- **Puente a LEAPS (estudio / por confirmar):** si el setup semanal es de **meses** (no solo 3 semanas) y SPY/QQQ + megacaps están en sesgo alcista claro, algunos traders extienden el vencimiento a **LEAPS** en lugar de ~21 días. Eso **no** está documentado como regla SCR pública; es una lectura de cartera (ver §3.1 y `CARDONA-TRADES-EJEMPLO.md`).

#### Earnings
- Vigencia: a menudo **corto post-reporte** o el ciclo del evento; strikes ~**5–7%** en notas de alumnos.
- Primas se inflan por IV de earnings → caro; gestionar expectativa.

---

## 5. Cómo combinar vigencia + prima en la práctica (checklist)

1. Identifica la **estrategia** y su **horizonte** (horas / 1–2 días / 3–5 días / 3 semanas / LEAPS solo si la tesis es multi-mes — por confirmar).
2. Elige **expiración ≥ ese horizonte** (si el efecto es 3–4 días, no uses solo 0DTE a las 15:00).
3. Mira la **tabla del ticker** (prima objetivo y spot–strike).
4. En la cadena de opciones, busca un contrato que:
   - esté cerca del **spot–strike** de la tabla,
   - tenga prima **en o cerca** del rango Ask/Bid,
   - tenga liquidez (spread bid–ask estrecho).
5. Si hoy la prima ATM sale a 300–700 USD y tu presupuesto es 50–100, **no fuerces**: o reduces tamaño, o eliges otro ticker más barato (SPY/QQQ/BAC…), o aceptas más OTM conscientemente (peor probabilidad).
6. Confirma **volumen de la vela de entrada** y **SPY** primero.

---

## 6. Métodos de inversión (% capital / metas) — del material

En tendencia bajista / alcista el material muestra tablas de % de inversión vs % meta de ganancia (escalonado, ~8 opciones promedio). Idea: no meter todo el capital en una sola prima; escalar metas (30%, 60%, 100%+). Usar la calculadora/Excel del método si la tienes.

---

## 7. Advertencia importante

Los rangos 0.25–0.30 (SPY) y 2.50 (TSLA) son **objetivos históricos del material de estudio**. Con SPY a precios actuales y volatilidad distinta, es normal que no encuentres exactamente esos números cerca del dinero. El principio se mantiene:

- **Prima baja relativa** + **strike alcanzable en el horizonte de la estrategia** + **setup claro** = lo que el método busca para “mayor rentabilidad”.
- Multiplicar siempre mentalmente **× 100** para saber cuánto sales de la cuenta.
