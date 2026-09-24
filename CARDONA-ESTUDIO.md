# Estudio Cardona — Gaps, LEAPS y texto propuesto (es-MX)

Documento de trabajo para profundizar la app educativa en `/workspace/cardona-opciones/`.
**No es asesoría financiera.** No inventa reglas SCR: lo no confirmado se marca **por confirmar**.

Última actualización: 2026-09-23 (America/Mexico_City).

---

## 1. Fuentes revisadas (públicas)

| Fuente | Qué aporta | LEAPS? |
|--------|------------|--------|
| Adaptaciones SlideShare *Seminario Creando Riqueza / Método Cardona* (2024–2025, FASH) | Reglas de oro SPY (prima 25–30, spot–strike 4–10), 0DTE / next-day ~15:50, RT, PM, canal, volumen | No aparece |
| Scribd *Estrategias para Comprar Opciones CALL y PUT* | Catálogo alineado a la app: PM-40H, CN, CF, RCB, gaps, 1V-R, RP-GAP, 4P, PF, earnings | No aparece |
| YouTube / cursos “Alejandro Cardona opciones” (páginas de venta, clips) | CALL sube / PUT baja, apalancamiento, contexto; sin checklist LEAPS | No confirmado |
| Comunidad (p. ej. r/OpcionesSCR) | Dudas de precios reales vs tabla 25–30; trades cortos | Sin regla LEAPS |
| Captura E*TRADE Gains & Losses (usuario) | CALL LEAPS ~ago-2026, SPY/QQQ + megacaps OTM | **Sí (evidencia de cartera)** |

**Conclusión:** el SCR público documentado en la app es **corto plazo** (minutos → ~3 semanas). Las LEAPS del usuario son un **horizonte adicional de estudio**, no una estrategia numerada SCR confirmada.

---

## 2. Gaps vs la app actual (antes de este estudio)

| # | Gap | Estado tras este trabajo |
|---|-----|---------------------------|
| 1 | `VIGENCIA-Y-PRIMAS.md` paraba en ~3 semanas; no hablaba de LEAPS | **Cubierto** (§3 / §3.1 + notas RCB/PF/3SEM) |
| 2 | `theory_content.PREMIUM_GUIDE` sin modo LEAPS | **Cubierto** |
| 3 | Reglas de oro no advertían que 4–10 / 0.25–0.30 son de **corto** | **Cubierto** |
| 4 | SPY tratado solo como CTX; evidencia de libro = SPY/QQQ **como trade** LEAPS | **Propuesto** (texto abajo; motor `suitable_leaps` pendiente) |
| 5 | 3SEM / PF / RCB no puenteaban a horizonte multi-mes | **Parcial** (notas en theory + vigencia) |
| 6 | Rankings / Opportunity sin flag LEAPS | **Pendiente** (no tocamos motor UI charts) |
| 7 | % OTM / meses mínimos LEAPS / take profit | **Por confirmar** |
| 8 | PUT LEAPS en techos | **Por confirmar** (no en captura) |
| 9 | AMD en watchlist / teoría primas (sí DIS/NVDA/META…) | **Pendiente menor** |
| 10 | Separar UI “setup días” vs “overlay LEAPS” | **Pendiente** |

---

## 3. Implicaciones LEAPS desde la captura

1. Tesis = **alcista multi-mes**, no golpe intradía.
2. Vehículo = **long CALL**, strikes **OTM/semi-OTM**, vencimiento **~1 año+**.
3. Núcleo = **SPY + QQQ**; satélites = megacaps tech (+ DIS).
4. Prima SCR intradía **no aplica**; liquidez sí importa.
5. Compatible con **espíritu** de: mirar SPY, no CALL en canal bajista sin RCB, setups de gran recorrido (3SEM/PF/RCB) — pero **no** con 1V-R / CN viernes / 0DTE.

---

## 4. Texto teórico propuesto por `code` (listo para merge)

Convención: bloques cortos en español educativo. Lo nuevo va en `notes` / `vigencia` / `premiums`.  
Ya mergeado en `theory_content.py` (parcial): **PREMIUM_GUIDE**, **RULES_OF_GOLD**, **3SEM**, **SPY-CTX**, **RCB**, **PF**.

### 1V-R
- Mantener vigencia intradía.
- Añadir avoid: «No usar LEAPS aquí; el edge es de apertura.»

### RP-GAP / 4P / HD / VRF-E / TF
- PUT cortos / contexto techo.
- Añadir: «PUT LEAPS en techo fuerte: **por confirmar**; la captura de estudio no muestra PUTs largos.»

### RT / PM-40H / CN / CF / GAP-NA / GAP-BA / VR-R
- Mantener horizontes cortos (horas–días).
- Añadir avoid: «No sustituir por LEAPS; si tras el rebote la tesis se vuelve multi-mes, eso es otro trade (3SEM/LEAPS), no el mismo setup.»

### RCB *(ya mergeado parcial)*
```
Vigencia tipica SCR: 2+ dias (corto/semanal).
Si la ruptura cambia un canal de semanas/meses a alcista y SPY acompana,
valorar 3SEM; CALL LEAPS solo si la tesis es multi-mes (por confirmar vs SCR).
Nunca CALL dentro del canal sin ruptura.
```

### PF *(ya mergeado parcial)*
```
Setup SCR: CALL 3–5 dias tras piso PM100/PM200 + ruptura horaria.
Overlay de estudio: mismo contexto de piso en SPY/QQQ a veces se opera
con CALL LEAPS OTM (evidencia de cartera). Separar setup de dias vs overlay.
```

### 1GAP-A
```
Horizonte SCR 3–4 dias. No es LEAPS. Si el primer gap confirma un piso
multi-mes, el LEAPS seria un trade distinto (por confirmar).
```

### 3SEM *(ya mergeado parcial)*
```
Nucleo SCR: semanal + compra ~15:55 ET + vencimiento ~15–21 dias.
Puente: si el recorrido semanal es de meses y SPY/QQQ alcistas,
algunos traders estudian extender a LEAPS. No esta en el SCR publico.
```

### SPY-CTX *(ya mergeado parcial)*
```
Sigue siendo filtro #1 (~70% atencion).
Ademas: en libros de estudio tipo LEAPS, SPY/QQQ son el nucleo de las CALL,
no solo contexto. Corto plazo: prima 0.25–0.30 y spot-strike 4–10.
LEAPS: esos numeros no aplican.
```

### (Propuesto, sin code aún) LEAPS-CALL
```
code: LEAPS-CALL
name: CALL larga / LEAPS (estudio)
direction: CALL
timeframe: 1d + 1wk
category: CTX
entry_time: Sin ventana intradía obligatoria; alinear con tesis multi-mes
summary: Horizon overlay (por confirmar vs SCR). Long CALL con vencimiento
  lejano (a menudo >1 año) sobre SPY/QQQ/megacaps en sesgo alcista.
prerequisites:
  - PM diarias/semanales alcistas (p. ej. PM20>PM40; PM100>PM200 preferible)
  - SPY-CTX no en caida libre
  - No estar dentro de canal bajista sin RCB
  - Liquidez en el strike/vencimiento
steps:
  1. Confirmar tesis multi-mes en semanal/diario (SPY primero).
  2. Elegir subyacente liquido (SPY/QQQ o megacap).
  3. Elegir vencimiento LEAPS (meses–años; minimo exacto por confirmar).
  4. Strike OTM/semi-OTM segun tolerancia (% OTM por confirmar).
  5. No usar la tabla de prima intradía 0.25–0.30 como meta.
notes:
  - Evidencia: captura E*TRADE usuario (ago-2026 CALLs).
  - No documentado como estrategia numerada SCR publica.
  - Take profit / rolling: por confirmar.
vigencia: Meses a ~2 años (tipico LEAPS de mercado).
premiums: Alta vs 0DTE; filtrar por liquidez y spread, no por tabla SCR corta.
related: [SPY-CTX, 3SEM, PF, RCB]
```

---

## 5. Mejoras pequeñas ya aplicadas

- `VIGENCIA-Y-PRIMAS.md`: fila LEAPS en tabla; §3.1; notas 3SEM/RCB/PF; checklist.
- `theory_content.py`: PREMIUM_GUIDE, RULES_OF_GOLD, vigencia/premiums de 3SEM, SPY-CTX, RCB, PF.
- `CARDONA-TRADES-EJEMPLO.md`: ampliado.
- `main.py`: bump de versión de payload teórico.

## 6. Mejoras pendientes (no hechas aquí)

- Flag `suitable_leaps` / `strike_hint` LEAPS en `cardona_engine.py`.
- Entrada `LEAPS-CALL` en TECHNIQUES + chart sintético.
- Watchlist/primas: AMD explícito.
- UI: badge “horizonte LEAPS” sin tocar el chart superior SPY (otra tarea).

---

## 7. Top 5 gaps cubiertos o propuestos (resumen ejecutivo)

1. **Vigencia LEAPS documentada** (con etiqueta *por confirmar*) frente al corte en 3 semanas.
2. **Teoría/API**: guía de primas y reglas de oro distinguen corto vs LEAPS.
3. **Puente 3SEM/PF/RCB/SPY-CTX** hacia tesis multi-mes sin inventar regla SCR.
4. **Texto listo `LEAPS-CALL`** para merge futuro como técnica CTX.
5. **Captura de trades** expandida como evidencia (no como dogma).
