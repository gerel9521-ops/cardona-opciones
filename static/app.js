const WATCHLIST = ["SPY","QQQ","AAPL","MSFT","NVDA","META","AMZN","TSLA","AMD","GOOGL","NFLX"];
const $ = (s) => document.querySelector(s);

/** Display names (professional Spanish). Prefer API name when present. */
const STRATEGY_NAMES = {
  "1V-R": "1ra Vela Roja",
  "RP-GAP": "Ruptura del Piso del GAP",
  "4P": "Modelo 4 pasos (verde-rojo rompe)",
  "HD": "Hanger en Diario",
  "VRF-E": "Vela Roja Final Envolvente del Día",
  "RT": "Ruptura del Techo",
  "PM-40H": "Promedio Móvil 40 Hora",
  "CN": "Caída Normal",
  "CF": "Caída Fuerte",
  "RCB": "Ruptura Canal Bajista",
  "GAP-NA": "GAP Normal al Alza",
  "GAP-BA": "GAP Bajista al Alza",
  "PF": "Piso Fuerte",
  "TF": "Techo Fuerte",
  "1GAP-A": "1er GAP al Alza",
  "3SEM": "Estrategia de las 3 semanas",
  "VR-R": "Verde-Rojo Rompe",
  "SPY-CTX": "Contexto SPY",
};

const YAHOO = {
  bg: "#ffffff",
  panel: "#ffffff",
  text: "#1a1a1a",
  muted: "#6b7280",
  grid: "rgba(0,0,0,0.06)",
  border: "#e5e7eb",
  up: "#26a69a",
  down: "#ef5350",
  wickUp: "#26a69a",
  wickDown: "#ef5350",
  pm20: "#2962ff",
  pm40: "#9c27b0",
  pm100: "#ff9800",
  pm200: "#e53935",
  volUp: "rgba(38,166,154,0.45)",
  volDown: "rgba(239,83,80,0.45)",
  crosshair: "rgba(55,65,81,0.45)",
};
/** Alias kept for any leftover references. */
const TC2000 = YAHOO;

let deferredInstallPrompt = null;
/** Last analysis payload — used by chart toggle without reload. */
let lastAnalysis = null;
let currentTf = "hourly";
/** Active Lightweight Charts hosts keyed by container id. */
const chartHosts = Object.create(null);
/** Live poll (~20s) while tab visible */
const LIVE_POLL_MS = 20000;
let livePollTimer = null;
let livePollInFlight = false;
let lastLiveTicker = null;

function strategyLabel(code, fallback) {
  if (fallback) return fallback;
  return STRATEGY_NAMES[code] || code || "Estrategia";
}

/** Null-safe text / HTML / class helpers — one missing node never aborts the rest. */
function setText(sel, text) {
  const el = typeof sel === "string" ? $(sel) : sel;
  if (!el) return;
  el.textContent = text == null ? "" : String(text);
}

function setHtml(sel, html) {
  const el = typeof sel === "string" ? $(sel) : sel;
  if (!el) return;
  el.innerHTML = html == null ? "" : String(html);
}

function setClass(sel, cls) {
  const el = typeof sel === "string" ? $(sel) : sel;
  if (!el) return;
  el.className = cls;
}

function setStatus(msg, kind) {
  const el = $("#status");
  if (!el) return;
  el.hidden = !msg;
  el.textContent = msg || "";
  el.className = "status" + (kind ? " " + kind : "");
}

function trendClass(t) {
  if (t === "alza") return "trend-alza";
  if (t === "baja") return "trend-baja";
  return "";
}

function zonaClass(z) {
  if (z === "cara") return "pill-cara";
  if (z === "barata") return "pill-barata";
  return "";
}

function escapeHtml(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function updateClock() {
  const now = new Date();
  const et = now.toLocaleString("es-MX", {
    timeZone: "America/New_York",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
  const mx = now.toLocaleString("es-MX", {
    timeZone: "America/Mexico_City",
    hour: "numeric",
    minute: "2-digit",
  });
  setText("#clock", `ET ${et} · CDMX ${mx}`);
}

function syncTickers(fromMobile) {
  const desk = $("#ticker");
  const mob = $("#ticker-mobile");
  if (!desk || !mob) return;
  if (fromMobile) desk.value = mob.value;
  else mob.value = desk.value;
}

function getTicker() {
  syncTickers(false);
  const desk = $("#ticker");
  return ((desk && desk.value) || "").trim().toUpperCase();
}

function renderChips() {
  const box = $("#chips");
  if (!box) return;
  box.innerHTML = "";
  WATCHLIST.forEach((t) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip";
    b.textContent = t;
    b.onclick = () => {
      const desk = $("#ticker");
      if (desk) desk.value = t;
      syncTickers(false);
      document.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
      b.classList.add("active");
      analyze();
    };
    box.appendChild(b);
  });
}

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  const a = $("#tab-analisis");
  const e = $("#tab-escaneo");
  const s = $("#tab-teoria");
  if (a) a.hidden = name !== "analisis";
  if (e) e.hidden = name !== "escaneo";
  if (s) s.hidden = name !== "teoria";
  if (name === "teoria") {
    ensureTheoryLoaded();
    // On mobile, show list when switching to tab
    const detail = $("#teoria-detail");
    const list = $("#teoria-list-pane");
    if (window.matchMedia("(max-width: 780px)").matches && detail && !detail.hidden && list) {
      /* keep detail if already open */
    }
  }
}

function formatMcap(co) {
  if (!co) return "—";
  if (co.market_cap) return co.market_cap;
  const raw = co.market_cap_raw;
  if (raw == null || !(Number(raw) > 0)) return "—";
  const n = Number(raw);
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T · ${(n / 1e12).toFixed(2)} billones USD`;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B · ${(n / 1e9).toFixed(2)} mil millones USD`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M · ${(n / 1e6).toFixed(2)} millones USD`;
  return `$${n.toLocaleString("es-MX")} USD`;
}

function seriesLen(series) {
  return (series && series.t && series.t.length) || 0;
}

function lastClose(series) {
  if (!series || !series.c || !series.c.length) return null;
  const c = series.c[series.c.length - 1];
  return c == null || Number.isNaN(Number(c)) ? null : Number(c);
}

function parseBarTime(t) {
  if (t == null) return null;
  if (typeof t === "number" && Number.isFinite(t)) {
    return t > 1e12 ? Math.floor(t / 1000) : Math.floor(t);
  }
  let s = String(t).trim();
  // Prefer date-only for daily/weekly (UTC midnight business day)
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    return s; // Lightweight Charts accepts YYYY-MM-DD business days
  }
  // Normalize "YYYY-MM-DD HH:MM:SS±HH:MM" → ISO
  if (!s.includes("T") && /^\d{4}-\d{2}-\d{2} /.test(s)) {
    s = s.replace(" ", "T");
  }
  // Already has offset or Z — do not append Z
  const hasTz = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(s);
  if (!hasTz) s += "Z";
  // Midnight bars (daily/weekly) → business day YYYY-MM-DD (Yahoo-like)
  const m = s.match(/^(\d{4}-\d{2}-\d{2})T0{1,2}:0{1,2}:0{1,2}/);
  if (m) return m[1];
  const ms = Date.parse(s);
  if (!Number.isFinite(ms)) return null;
  return Math.floor(ms / 1000);
}

function destroyChart(elId) {
  const host = chartHosts[elId];
  if (host) {
    try { host.ro && host.ro.disconnect(); } catch (_) { /* ignore */ }
    try { host.chart && host.chart.remove(); } catch (_) { /* ignore */ }
    delete chartHosts[elId];
  }
  const el = document.getElementById(elId);
  if (el) el.innerHTML = "";
}

function showChartMessage(elId, msg) {
  destroyChart(elId);
  const el = document.getElementById(elId);
  if (!el) return;
  el.innerHTML = `<p class="chart-error">${escapeHtml(msg)}</p>`;
}

function toCandleData(series) {
  const out = [];
  const n = seriesLen(series);
  let lastT = null;
  const sessions = (series && series.session) || [];
  for (let i = 0; i < n; i++) {
    const time = parseBarTime(series.t[i]);
    const open = Number(series.o[i]);
    const high = Number(series.h[i]);
    const low = Number(series.l[i]);
    const close = Number(series.c[i]);
    if (time == null || ![open, high, low, close].every(Number.isFinite)) continue;
    if (lastT != null && time <= lastT) continue; // LW charts require ascending unique times
    lastT = time;
    const sess = sessions[i] || "rth";
    out.push({ time, open, high, low, close, session: sess });
  }
  return out;
}

function toVolumeData(series, candles) {
  if (!series || !series.v) return [];
  const byT = new Map();
  const n = seriesLen(series);
  for (let i = 0; i < n; i++) {
    const time = parseBarTime(series.t[i]);
    const vol = Number(series.v[i]);
    const open = Number(series.o[i]);
    const close = Number(series.c[i]);
    if (time == null || !Number.isFinite(vol)) continue;
    const sess = (series.session && series.session[i]) || "rth";
    const ext = sess === "pre" || sess === "post" || sess === "closed";
    const up = ext ? "rgba(38,166,154,0.22)" : YAHOO.volUp;
    const down = ext ? "rgba(239,83,80,0.22)" : YAHOO.volDown;
    byT.set(time, {
      time,
      value: Math.max(0, vol),
      color: close >= open ? up : down,
    });
  }
  return candles.map((c) => byT.get(c.time) || { time: c.time, value: 0, color: YAHOO.volUp });
}

function toLineData(series, key, candles) {
  if (!series || !series[key]) return [];
  const byT = new Map();
  const n = seriesLen(series);
  for (let i = 0; i < n; i++) {
    const time = parseBarTime(series.t[i]);
    const v = series[key][i];
    if (time == null || v == null || !Number.isFinite(Number(v))) continue;
    byT.set(time, { time, value: Number(v) });
  }
  const out = [];
  candles.forEach((c) => {
    const pt = byT.get(c.time);
    if (pt) out.push(pt);
  });
  return out;
}

function plotYahooChart(elId, series, mas, opts) {
  opts = opts || {};
  const el = document.getElementById(elId);
  if (!el) return;

  if (!window.LightweightCharts || typeof window.LightweightCharts.createChart !== "function") {
    showChartMessage(elId, "No se pudo cargar Lightweight Charts. Recarga la página.");
    return;
  }
  if (!series || !series.t || !series.t.length) {
    showChartMessage(elId, "Sin datos de gráfica para esta temporalidad.");
    return;
  }

  const candles = toCandleData(series);
  if (!candles.length) {
    showChartMessage(elId, "Sin datos de gráfica válidos para mostrar.");
    return;
  }

  destroyChart(elId);
  el.innerHTML = "";
  el.classList.add("lw-host");

  const height = opts.height || 400;
  const chart = window.LightweightCharts.createChart(el, {
    width: el.clientWidth || el.parentElement?.clientWidth || 320,
    height,
    layout: {
      background: { color: YAHOO.bg },
      textColor: YAHOO.text,
      fontFamily: "Inter, system-ui, -apple-system, sans-serif",
      fontSize: 11,
    },
    grid: {
      vertLines: { color: YAHOO.grid },
      horzLines: { color: YAHOO.grid },
    },
    crosshair: {
      mode: window.LightweightCharts.CrosshairMode
        ? window.LightweightCharts.CrosshairMode.Normal
        : 0,
      vertLine: { color: YAHOO.crosshair, width: 1, style: 2, labelBackgroundColor: "#374151" },
      horzLine: { color: YAHOO.crosshair, width: 1, style: 2, labelBackgroundColor: "#374151" },
    },
    rightPriceScale: {
      borderColor: YAHOO.border,
      scaleMargins: { top: 0.08, bottom: 0.28 },
    },
    timeScale: {
      borderColor: YAHOO.border,
      timeVisible: opts.timeVisible !== false,
      secondsVisible: false,
      rightOffset: 4,
    },
    handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
    handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
  });

  const candleSeries = chart.addCandlestickSeries({
    upColor: YAHOO.up,
    downColor: YAHOO.down,
    borderUpColor: YAHOO.up,
    borderDownColor: YAHOO.down,
    wickUpColor: YAHOO.wickUp,
    wickDownColor: YAHOO.wickDown,
    priceLineVisible: true,
    lastValueVisible: true,
  });
  // Strip session before setData (LW only wants OHLCV)
  const candleData = candles.map(({ time, open, high, low, close }) => ({ time, open, high, low, close }));
  candleSeries.setData(candleData);

  // Subtle markers for extended-hours bars (Yahoo-like cue)
  try {
    if (typeof candleSeries.setMarkers === "function") {
      const markers = [];
      candles.forEach((c) => {
        if (c.session === "pre" || c.session === "post") {
          markers.push({
            time: c.time,
            position: "belowBar",
            color: c.session === "pre" ? "rgba(245,185,66,0.55)" : "rgba(167,139,250,0.55)",
            shape: "circle",
            size: 0.4,
          });
        }
      });
      // Cap markers to avoid clutter
      const step = Math.max(1, Math.floor(markers.length / 40));
      candleSeries.setMarkers(markers.filter((_, i) => i % step === 0).slice(-40));
    }
  } catch (_) { /* ignore */ }

  const volSeries = chart.addHistogramSeries({
    priceFormat: { type: "volume" },
    priceScaleId: "vol",
    lastValueVisible: false,
    priceLineVisible: false,
  });
  chart.priceScale("vol").applyOptions({
    scaleMargins: { top: 0.78, bottom: 0 },
    drawTicks: false,
    borderVisible: false,
  });
  volSeries.setData(toVolumeData(series, candles));

  const maSeries = {};
  (mas || []).forEach(([key, color, _label]) => {
    const line = toLineData(series, key, candles);
    if (!line.length) return;
    const s = chart.addLineSeries({
      color,
      lineWidth: 1.5,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });
    s.setData(line);
    maSeries[key] = s;
  });

  if (!opts.preserveTimeScale) {
    chart.timeScale().fitContent();
  }

  const ro = (typeof ResizeObserver !== "undefined")
    ? new ResizeObserver(() => {
        if (!el.isConnected) return;
        chart.applyOptions({ width: el.clientWidth || 320 });
      })
    : null;
  if (ro) ro.observe(el);

  chartHosts[elId] = { chart, ro, candleSeries, volSeries, maSeries, lastSeries: series };
}

function getCharts(data) {
  const c = (data && data.charts) || {};
  return {
    m15: c.m15 || data.series_15m || null,
    hourly: c.hourly || data.series_1h || null,
    daily: c.daily || data.series_1d || null,
    weekly: c.weekly || data.series_1wk || null,
    spy: c.spy_daily || data.series_spy_1d || null,
  };
}

const TF_META = {
  m15: {
    label: "15m",
    caption: "Intradía (15m) · horas extendidas · PM20 / PM40 · estilo Yahoo",
    mas: [
      ["PM20", YAHOO.pm20, "PM20"],
      ["PM40", YAHOO.pm40, "PM40"],
    ],
    timeVisible: true,
    apiTf: "15m",
  },
  hourly: {
    label: "1H",
    caption: "Horario (1h) · horas extendidas · PM20 / PM40 · estilo Yahoo",
    mas: [
      ["PM20", YAHOO.pm20, "PM20"],
      ["PM40", YAHOO.pm40, "PM40"],
    ],
    timeVisible: true,
    apiTf: "hourly",
  },
  daily: {
    label: "1D",
    caption: "Diario (1d) · última vela con precio extendido · PM20 / PM40 / PM100 / PM200",
    mas: [
      ["PM20", YAHOO.pm20, "PM20"],
      ["PM40", YAHOO.pm40, "PM40"],
      ["PM100", YAHOO.pm100, "PM100"],
      ["PM200", YAHOO.pm200, "PM200"],
    ],
    timeVisible: false,
    apiTf: "daily",
  },
  weekly: {
    label: "1W",
    caption: "Semanal (1wk) · PM20 / PM40",
    mas: [
      ["PM20", YAHOO.pm20, "PM20"],
      ["PM40", YAHOO.pm40, "PM40"],
    ],
    timeVisible: false,
    apiTf: "weekly",
  },
};

function setChartToggle(tf) {
  currentTf = tf;
  document.querySelectorAll(".chart-toggle-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.tf === tf);
  });
  const meta = TF_META[tf] || TF_META.hourly;
  setText("#chart-caption", meta.caption);
}

function renderMainChart(data, tf, opts) {
  if (!data) return;
  opts = opts || {};
  const charts = getCharts(data);
  const key = (tf === "weekly" || tf === "daily" || tf === "m15") ? tf : "hourly";
  const series = charts[key];
  const meta = TF_META[key] || TF_META.hourly;
  setChartToggle(key);

  const n = seriesLen(series);
  const ticker = data.ticker || "";
  const extNote = (key === "hourly" || key === "m15") ? " · pre/post" : "";
  const title = `${ticker} · ${meta.label}${extNote} · ${n} velas`;
  setText("#chart-title-label", title);
  updateLiveMeta(data);

  const isMobile = window.matchMedia("(max-width: 700px)").matches;
  // Soft-update last bar when host exists and preserveTimeScale
  if (opts.softUpdate && trySoftUpdateChart("chart-main", series, meta.mas)) {
    return;
  }
  plotYahooChart("chart-main", series, meta.mas, {
    height: isMobile ? 310 : 420,
    timeVisible: meta.timeVisible,
    preserveTimeScale: !!opts.preserveTimeScale,
  });
}

function updateLiveMeta(data) {
  const wrap = $("#chart-live-meta");
  if (!wrap) return;
  wrap.hidden = false;
  const sess = data.session || data.session_label || "";
  const label = data.session_label || sess || "—";
  const pill = $("#session-pill");
  if (pill) {
    pill.textContent = label;
    pill.className = "session-pill " + (data.session || "");
  }
  const updated = data.updated_at_local || "—";
  setText("#live-updated", "Actualizado " + updated);
}

function trySoftUpdateChart(elId, series, mas) {
  const host = chartHosts[elId];
  if (!host || !host.candleSeries || !series) return false;
  const candles = toCandleData(series);
  if (!candles.length) return false;
  try {
    const last = candles[candles.length - 1];
    host.candleSeries.update({
      time: last.time,
      open: last.open,
      high: last.high,
      low: last.low,
      close: last.close,
    });
    const vols = toVolumeData(series, [last]);
    if (vols.length && host.volSeries) host.volSeries.update(vols[0]);
    (mas || []).forEach(([key]) => {
      const line = toLineData(series, key, [last]);
      if (line.length && host.maSeries && host.maSeries[key]) {
        host.maSeries[key].update(line[0]);
      }
    });
    host.lastSeries = series;
    return true;
  } catch (err) {
    console.warn("softUpdate", err);
    return false;
  }
}

function pickBestOpportunity(data) {
  const tc = data.top_call;
  const tp = data.top_put;
  if (tc && tp) return Number(tc.score) >= Number(tp.score) ? tc : tp;
  return tc || tp || null;
}

function renderOppHero(data) {
  const hero = $("#opp-hero");
  const body = $("#opp-hero-body");
  if (!hero || !body) return;
  const best = pickBestOpportunity(data);
  hero.classList.remove("call-lean", "put-lean", "neutral-lean");
  if (!best) {
    hero.classList.add("neutral-lean");
    body.innerHTML = `<p class="muted">Sin oportunidad clara de compra CALL/PUT en este momento. Revisa tendencia, zona y contexto SPY.</p>
      <div class="opp-hero-bias">Sesgo sugerido: <strong>${escapeHtml(data.market_bias || "neutral")}</strong></div>`;
    return;
  }
  const lean = best.direction === "CALL" ? "call-lean" : "put-lean";
  hero.classList.add(lean);
  const name = strategyLabel(best.code, best.strategy);
  const reasons = (best.reasons || []).slice(0, 4).map((r) => `<li>${escapeHtml(r)}</li>`).join("");
  const biasNote = best.bias
    ? escapeHtml(best.bias)
    : `Sesgo ${escapeHtml(best.direction)} · mercado ${escapeHtml(data.market_bias || "neutral")}`;
  body.innerHTML = `
    <div class="opp-hero-main">
      <div>
        <span class="dir ${best.direction === "CALL" ? "call" : "put"}">${escapeHtml(best.direction)}</span>
        <span class="code-badge">${escapeHtml(best.code || "")}</span>
        <h3 class="opp-hero-title">${escapeHtml(name)}</h3>
        <div class="opp-hero-meta">Confianza ${escapeHtml(best.confidence || "—")} · ${escapeHtml(best.entry_time_hint || "vela final")}</div>
      </div>
      <div style="text-align:right">
        <div class="opp-hero-score">${best.score != null ? Math.round(best.score) : "—"}</div>
        <div class="opp-hero-meta">score</div>
      </div>
    </div>
    ${reasons ? `<ul class="opp-hero-reasons">${reasons}</ul>` : ""}
    <div class="opp-hero-bias">Sesgo sugerido: <strong>${biasNote}</strong></div>
  `;
}

function fillTopReasons(elId, opp) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.innerHTML = "";
  if (!opp) return;
  (opp.reasons || []).slice(0, 3).forEach((r) => {
    const li = document.createElement("li");
    li.textContent = r;
    el.appendChild(li);
  });
}

function biasClass(bias) {
  const b = (bias || "").toUpperCase();
  if (b === "CALL") return "bias-call";
  if (b === "PUT") return "bias-put";
  return "bias-neutral";
}

function renderForecast(data) {
  try {
    const fc = (data && data.forecast) || {};
    if (fc.disclaimer) setText("#forecast-disclaimer", fc.disclaimer);

    const short = fc.short || {};
    const long = fc.long || {};

    const sb = $("#fc-short-bias");
    setText(sb, short.bias || "—");
    setClass(sb, "forecast-bias " + biasClass(short.bias));
    setText("#fc-short-horizon", short.horizon || "1–5 días");
    setText("#fc-short-conf", short.confidence ? `Confianza ${short.confidence}` : "");
    setText("#fc-short-summary", short.summary || "Sin pronóstico corto disponible.");

    const lb = $("#fc-long-bias");
    setText(lb, long.bias || "—");
    setClass(lb, "forecast-bias " + biasClass(long.bias));
    setText("#fc-long-horizon", long.horizon || "semanas");
    setText("#fc-long-conf", long.confidence ? `Confianza ${long.confidence}` : "");
    setText("#fc-long-summary", long.summary || "Sin pronóstico largo disponible.");
  } catch (err) {
    console.warn("renderForecast:", err);
  }
}

function renderCompany(data) {
  try {
    const co = (data && data.company) || {};
    setText("#co-name", co.name || data.ticker || "—");
    setText("#co-sector", co.sector || "No disponible");
    setText("#co-industry", co.industry || "No disponible");
    setText("#co-exchange", co.exchange || "—");
    setText("#co-currency", co.currency || "—");
    setText("#co-mcap", formatMcap(co));
    const summary = co.summary
      || (co.sector || co.industry
        ? `Empresa del sector ${co.sector || "—"} / industria ${co.industry || "—"} (sin descripción larga en Yahoo Finance).`
        : "Sin descripción de negocio disponible para este ticker (Yahoo Finance).");
    setText("#co-summary", summary);
  } catch (err) {
    console.warn("renderCompany:", err);
  }
}

function renderOpportunities(opps) {
  const box = $("#opp-list");
  if (!box) return;
  box.innerHTML = "";
  if (!opps || !opps.length) {
    box.innerHTML = "<p class='empty-mini'>Sin setups activos en este momento. Prueba otro ticker o espera el cierre de vela.</p>";
    return;
  }
  opps.forEach((op) => {
    const div = document.createElement("div");
    div.className = "opp " + (op.direction === "CALL" ? "call" : "put");
    const name = strategyLabel(op.code, op.strategy);
    const reasons = (op.reasons || []).map((r) => `<li>${escapeHtml(r)}</li>`).join("");
    const warns = (op.warnings || []).length
      ? `<div class="warns">⚠ ${escapeHtml((op.warnings || []).join(" · "))}</div>`
      : "";
    const tag3 = op.suitable_3sem ? `<span class="tag-3sem">3 semanas</span>` : "";
    const strike = op.strike_hint
      ? `<div class="strike-hint">Strike: ${escapeHtml(op.strike_hint)}</div>`
      : "";
    div.innerHTML = `
      <div class="opp-head">
        <div>
          <span class="dir ${op.direction === "CALL" ? "call" : "put"}">${escapeHtml(op.direction || "")}</span>
          <span class="code-badge">${escapeHtml(op.code || "")}</span>
          ${tag3}
          <div class="opp-title">${escapeHtml(name)}</div>
        </div>
        <div style="text-align:right">
          <div class="score">${op.score != null ? Math.round(op.score) : "—"}</div>
          <div class="muted" style="font-size:.75rem">conf. ${escapeHtml(op.confidence || "—")} · ${escapeHtml(op.entry_time_hint || "")}</div>
        </div>
      </div>
      <ul>${reasons}</ul>
      ${strike}
      ${warns}
    `;
    box.appendChild(div);
  });
}

function renderAnalysis(data) {
  const empty = $("#empty");
  const analysis = $("#analysis");
  if (empty) empty.hidden = true;
  if (analysis) analysis.hidden = false;
  switchTab("analisis");
  lastAnalysis = data;

  if (!data || !data.ok) {
    setStatus((data && data.error) || "No se pudo analizar este ticker.", "err");
    return;
  }
  setStatus(`Análisis listo: ${data.ticker}`, "ok");

  try {
    const coName = (data.company && data.company.name) ? data.company.name : data.ticker;
    setText("#results-title", `${data.ticker} · ${coName}`);

    const upd = $("#updated-at");
    if (upd) {
      upd.textContent = data.updated_at_local
        ? `Última actualización: ${data.updated_at_local}`
        : `Última actualización: ${new Date().toLocaleString("es-MX", { timeZone: "America/Mexico_City" })} CDMX`;
    }

    const price = data.last_price != null ? Number(data.last_price).toFixed(2) : "—";
    setText("#sum-ticker", data.ticker);
    setText("#sum-price", price);

    const td = data.trend_detail || {};
    const t1 = $("#sum-t1h");
    setText(t1, data.trend_1h || "—");
    setClass(t1, "value " + trendClass(data.trend_1h));
    const t1r = $("#sum-t1h-rule");
    if (t1r) {
      const h = td.hourly || {};
      t1r.textContent = h.label || (h.rule ? `${h.rule} → ${h.trend || data.trend_1h || ""}` : "");
    }

    const t2 = $("#sum-t1d");
    setText(t2, data.trend_1d || "—");
    setClass(t2, "value " + trendClass(data.trend_1d));
    const t2r = $("#sum-t1d-rule");
    if (t2r) {
      const d = td.daily || {};
      t2r.textContent = d.label || (d.rule ? `${d.rule} → ${d.trend || data.trend_1d || ""}` : "");
    }

    const z = $("#sum-zona");
    setText(z, data.zona || "—");
    setClass(z, "value " + zonaClass(data.zona));

    const b = $("#sum-bias");
    setText(b, data.market_bias || "—");
    setClass(b, "value " + trendClass(
      data.market_bias === "alcista" ? "alza" : data.market_bias === "bajista" ? "baja" : ""
    ));
  } catch (err) {
    console.warn("renderAnalysis summary:", err);
  }

  try { renderOppHero(data); } catch (err) { console.warn("oppHero", err); }

  try {
    const tc = data.top_call;
    setText("#top-call-score", tc ? Math.round(tc.score) : "—");
    setText("#top-call-name", tc
      ? `${tc.code} · ${strategyLabel(tc.code, tc.strategy)}`
      : "Sin señal CALL");
    setText("#top-call-conf", tc
      ? `Confianza ${tc.confidence} · ${tc.entry_time_hint || ""}`
      : "");
    fillTopReasons("top-call-reasons", tc);

    const tp = data.top_put;
    setText("#top-put-score", tp ? Math.round(tp.score) : "—");
    setText("#top-put-name", tp
      ? `${tp.code} · ${strategyLabel(tp.code, tp.strategy)}`
      : "Sin señal PUT");
    setText("#top-put-conf", tp
      ? `Confianza ${tp.confidence} · ${tp.entry_time_hint || ""}`
      : "");
    fillTopReasons("top-put-reasons", tp);
  } catch (err) {
    console.warn("tops", err);
  }

  // Company + forecast early so they never get skipped by chart errors
  renderForecast(data);
  renderCompany(data);

  try {
    const spy = data.spy_context || {};
    setHtml("#spy-meta", `
      <strong>${escapeHtml(spy.attention || "Revisar SPY primero (~70% de la atención).")}</strong><br/>
      Zona SPY: <b class="${zonaClass(spy.zona)}">${escapeHtml(spy.zona || "—")}</b> ·
      Tendencia diaria: <b class="${trendClass(spy.trend_daily)}">${escapeHtml(spy.trend_daily || "—")}</b> ·
      Cae: <b>${spy.spy_cae ? "sí" : "no"}</b> ·
      Boost PUT: <b>${spy.boost_put ? "sí" : "no"}</b> ·
      Boost CALL: <b>${spy.boost_call ? "sí" : "no"}</b>
      <div>${(spy.reasons || []).map((r) => "• " + escapeHtml(r)).join("<br/>")}</div>
    `);
  } catch (err) {
    console.warn("spy meta", err);
  }


  try {
    currentTf = "hourly";
    renderMainChart(data, "hourly");
  } catch (err) {
    console.warn("main chart", err);
  }

  try { renderOpportunities(data.opportunities); } catch (err) { console.warn("opps", err); }

  try {
    const notes = [];
    if (data.earnings_note) notes.push(data.earnings_note);
    if (data.tna_tza_note) notes.push(data.tna_tza_note);
    if (data.warnings && data.warnings.length) notes.push(...data.warnings.slice(0, 3));
    setText("#extra-notes", notes.join(" · "));
  } catch (err) {
    console.warn("notes", err);
  }
}

async function analyze() {
  const ticker = getTicker();
  if (!ticker) return;
  const desk = $("#ticker");
  if (desk) desk.value = ticker;
  syncTickers(false);
  const btn = $("#btn-analyze");
  if (btn) btn.disabled = true;
  const mobBtn = $("#btn-analyze-mobile");
  if (mobBtn) mobBtn.disabled = true;
  setStatus(`Analizando ${ticker}…`, "");
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker, drop_forming: true }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Error de red");
    renderAnalysis(data);
  } catch (e) {
    setStatus("Error: " + String(e.message || e), "err");
  } finally {
    if (btn) btn.disabled = false;
    if (mobBtn) mobBtn.disabled = false;
  }
}

async function scan() {
  const btn = $("#btn-scan");
  if (btn) btn.disabled = true;
  setStatus("Escaneando watchlist…", "");
  switchTab("escaneo");
  try {
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ drop_forming: true }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Error");
    const rows = (data.ranked || []).map((r) => {
      const dir = (r.best_direction || "").toUpperCase();
      const dirCls = dir === "CALL" ? "scan-dir-call" : dir === "PUT" ? "scan-dir-put" : "scan-dir-none";
      const name = r.best_code
        ? `${r.best_code} · ${strategyLabel(r.best_code, r.best_strategy)}`
        : (r.error || "Sin señal");
      return `
      <tr data-ticker="${escapeHtml(r.ticker)}">
        <td><strong>${escapeHtml(r.ticker)}</strong></td>
        <td>$${r.last_price != null ? Number(r.last_price).toFixed(2) : "—"}</td>
        <td class="${dirCls}">${escapeHtml(dir || "—")}</td>
        <td>${r.best_score != null ? Math.round(r.best_score) : "—"}</td>
        <td>${escapeHtml(name)}</td>
      </tr>`;
    }).join("");
    const wrap = $("#scan-table-wrap");
    if (wrap) {
      wrap.innerHTML = `
        <table class="scan-table">
          <thead><tr><th>Ticker</th><th>Precio</th><th>Dir.</th><th>Score</th><th>Mejor setup</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>`;
      wrap.querySelectorAll("tr[data-ticker]").forEach((tr) => {
        tr.onclick = () => {
          const d = $("#ticker");
          if (d) d.value = tr.dataset.ticker;
          syncTickers(false);
          analyze();
        };
      });
    }
    setStatus(`Escaneo listo: ${data.count} tickers`, "ok");
  } catch (e) {
    setStatus("Error: " + String(e.message || e), "err");
  } finally {
    if (btn) btn.disabled = false;
  }
}

function directionBadge(dir) {
  const d = (dir || "").toUpperCase();
  if (d.includes("CALL") && d.includes("PUT")) {
    return { border: "ctx-border", badge: "both", label: "CALL / PUT" };
  }
  if (d === "CALL" || d.startsWith("CALL")) {
    return { border: "call-border", badge: "call", label: "CALL" };
  }
  if (d === "PUT" || d.startsWith("PUT")) {
    return { border: "put-border", badge: "put", label: "PUT" };
  }
  if (d === "CTX" || d.includes("CTX") || d.includes("CONTEXTO")) {
    return { border: "ctx-border", badge: "ctx", label: "CONTEXTO" };
  }
  return { border: "ctx-border", badge: "ctx", label: dir || "—" };
}

let theoryData = null;
let theoryFilter = "Todas";
let theoryQuery = "";
let theorySelectedCode = null;

async function ensureTheoryLoaded() {
  if (theoryData) {
    renderTheoryList();
    return;
  }
  await loadTheory();
}

async function loadTheory() {
  const grid = $("#teoria-grid");
  if (grid) grid.innerHTML = `<p class="muted">Cargando teoría…</p>`;
  try {
    const res = await fetch("/api/theory");
    if (!res.ok) throw new Error("HTTP " + res.status);
    theoryData = await res.json();
    renderRulesOfGold();
    renderTrendRules();
    renderTheoryList();
    setupTheoryControls();
  } catch (e) {
    setHtml("#teoria-grid", `<p class="muted">No se pudo cargar la teoría: ${escapeHtml(String(e))}</p>`);
  }
}

function renderRulesOfGold() {
  const ol = $("#rules-of-gold");
  if (!ol || !theoryData) return;
  ol.innerHTML = "";
  (theoryData.rules_of_gold || []).forEach((r) => {
    const li = document.createElement("li");
    li.textContent = r;
    ol.appendChild(li);
  });
}

function renderTrendRules() {
  const ul = $("#trend-rules-list");
  if (!ul || !theoryData) return;
  const tr = theoryData.trend_rules || {};
  ul.innerHTML = "";
  (tr.rules || []).forEach((r) => {
    const li = document.createElement("li");
    li.textContent = r;
    ul.appendChild(li);
  });
}

function techniqueMatchesFilter(t, filter) {
  const d = (t.direction || "").toUpperCase();
  const cat = (t.category || "").toUpperCase();
  const isCtx = cat === "CTX" || d === "CTX" || d.includes("|") || d.includes("CTX");
  if (filter === "Todas") return true;
  if (filter === "Contexto") return isCtx;
  if (filter === "CALL") return !isCtx && (d === "CALL" || cat === "CALL");
  if (filter === "PUT") return !isCtx && (d === "PUT" || cat === "PUT");
  return true;
}

function filteredTechniques() {
  if (!theoryData) return [];
  const q = theoryQuery.trim().toLowerCase();
  return (theoryData.techniques || []).filter((t) => {
    if (!techniqueMatchesFilter(t, theoryFilter)) return false;
    if (!q) return true;
    const hay = `${t.code} ${t.name} ${t.summary || ""}`.toLowerCase();
    return hay.includes(q);
  });
}

function renderTheoryList() {
  const grid = $("#teoria-grid");
  if (!grid) return;
  const items = filteredTechniques();
  grid.innerHTML = "";
  if (!items.length) {
    grid.innerHTML = `<p class="empty-mini">Ninguna técnica coincide con el filtro.</p>`;
    return;
  }
  items.forEach((s) => {
    const db = directionBadge(s.direction);
    const name = strategyLabel(s.code, s.name);
    const card = document.createElement("button");
    card.type = "button";
    card.className = "strat-card teoria-card " + db.border + (theorySelectedCode === s.code ? " selected" : "");
    card.setAttribute("aria-label", `Ver teoría de ${s.code}`);
    const tf = [s.timeframe, s.entry_time].filter(Boolean).join(" · ");
    card.innerHTML = `
      <div class="strat-meta">
        <span class="strat-code">${escapeHtml(s.code)}</span>
        <span class="strat-badge ${db.badge}">${escapeHtml(db.label)}</span>
        ${tf ? `<span class="strat-tf">${escapeHtml(tf)}</span>` : ""}
      </div>
      <h3>${escapeHtml(name)}</h3>
      <p class="sum">${escapeHtml(s.summary || "")}</p>
      <span class="teoria-card-cta">Ver teoría completa →</span>`;
    card.addEventListener("click", () => openTheoryDetail(s.code));
    grid.appendChild(card);
  });
}

function listItems(arr, ordered) {
  if (!arr || !arr.length) return "";
  const tag = ordered ? "ol" : "ul";
  return `<${tag} class="teoria-steps">${arr.map((x) => `<li>${escapeHtml(x)}</li>`).join("")}</${tag}>`;
}


const THEORY_CHART_ID = "theory-example-chart";

function renderTheoryExampleChart(example) {
  destroyChart(THEORY_CHART_ID);
  const el = document.getElementById(THEORY_CHART_ID);
  if (!el || !example || !example.series) return;
  if (!window.LightweightCharts || typeof window.LightweightCharts.createChart !== "function") {
    el.innerHTML = `<p class="chart-error">No se pudo cargar Lightweight Charts.</p>`;
    return;
  }
  const candles = toCandleData(example.series);
  if (!candles.length) {
    el.innerHTML = `<p class="chart-error">Sin datos de ejemplo para graficar.</p>`;
    return;
  }

  el.innerHTML = "";
  el.classList.add("lw-host", "theory-lw-host");
  const chart = window.LightweightCharts.createChart(el, {
    width: el.clientWidth || el.parentElement?.clientWidth || 320,
    height: 280,
    layout: {
      background: { color: YAHOO.bg },
      textColor: YAHOO.text,
      fontFamily: "Inter, system-ui, -apple-system, sans-serif",
      fontSize: 11,
    },
    grid: {
      vertLines: { color: YAHOO.grid },
      horzLines: { color: YAHOO.grid },
    },
    rightPriceScale: { borderColor: YAHOO.border, scaleMargins: { top: 0.1, bottom: 0.12 } },
    timeScale: { borderColor: YAHOO.border, timeVisible: true, secondsVisible: false, rightOffset: 2 },
    handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
    handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
  });
  const candleSeries = chart.addCandlestickSeries({
    upColor: YAHOO.up,
    downColor: YAHOO.down,
    borderUpColor: YAHOO.up,
    borderDownColor: YAHOO.down,
    wickUpColor: YAHOO.wickUp,
    wickDownColor: YAHOO.wickDown,
    priceLineVisible: false,
    lastValueVisible: false,
  });
  candleSeries.setData(candles);

  const markers = [];
  const legendBits = [];
  (example.annotations || []).forEach((a) => {
    if (!a) return;
    if (a.kind === "price_line" && Number.isFinite(Number(a.price))) {
      candleSeries.createPriceLine({
        price: Number(a.price),
        color: a.color || "#64748b",
        lineWidth: 2,
        lineStyle: 2,
        axisLabelVisible: true,
        title: a.label || "",
      });
      if (a.label) legendBits.push(a.label);
    } else if (a.kind === "marker") {
      let idx = Number(a.bar);
      if (!Number.isFinite(idx)) return;
      if (idx < 0) idx = candles.length + idx;
      if (idx < 0 || idx >= candles.length) return;
      const shape = a.shape === "arrowDown" ? "arrowDown"
        : a.shape === "circle" ? "circle"
        : a.shape === "square" ? "square"
        : "arrowUp";
      markers.push({
        time: candles[idx].time,
        position: a.position || (shape === "arrowDown" ? "aboveBar" : "belowBar"),
        color: a.color || "#22c55e",
        shape,
        text: a.text || "",
      });
      if (a.text) legendBits.push(a.text);
    } else if (a.kind === "legend" && a.text) {
      legendBits.push(a.text);
    }
  });
  if (markers.length && typeof candleSeries.setMarkers === "function") {
    candleSeries.setMarkers(markers);
  }
  chart.timeScale().fitContent();

  const ro = (typeof ResizeObserver !== "undefined")
    ? new ResizeObserver(() => {
        if (!el.isConnected) return;
        chart.applyOptions({ width: el.clientWidth || 320 });
      })
    : null;
  if (ro) ro.observe(el);
  chartHosts[THEORY_CHART_ID] = { chart, ro };

  const legendEl = document.getElementById("theory-example-legend");
  if (legendEl) {
    const uniq = [...new Set(legendBits.filter(Boolean))];
    legendEl.textContent = uniq.length ? uniq.join(" · ") : (example.title || "");
  }
}

function openTheoryDetail(code) {
  if (!theoryData) return;
  const t = (theoryData.techniques || []).find((x) => x.code === code);
  if (!t) return;
  theorySelectedCode = code;
  renderTheoryList();

  const db = directionBadge(t.direction);
  const name = strategyLabel(t.code, t.name);
  const body = $("#teoria-detail-body");
  const detail = $("#teoria-detail");
  const listPane = $("#teoria-list-pane");
  if (!body || !detail) return;

  const related = (t.related || [])
    .map((c) => `<button type="button" class="related-chip" data-code="${escapeHtml(c)}">${escapeHtml(c)}</button>`)
    .join("");

  const is3sem = t.code === "3SEM";
  const metaExtra = is3sem
    ? `<p class="teoria-meta-line teoria-meta-highlight"><strong>TF:</strong> Semanal (1wk) · <strong>Compra:</strong> ≈15:55 ET (5 min antes del cierre)</p>`
    : "";

  body.innerHTML = `
    <header class="teoria-detail-head${is3sem ? " teoria-3sem" : ""}">
      <div class="strat-meta">
        <span class="strat-code">${escapeHtml(t.code)}</span>
        <span class="strat-badge ${db.badge}">${escapeHtml(db.label)}</span>
        <span class="strat-tf">${escapeHtml(t.timeframe || "")}</span>
      </div>
      <h2>${escapeHtml(name)}</h2>
      <p class="teoria-meta-line"><strong>Entrada:</strong> ${escapeHtml(t.entry_time || "—")}</p>
      ${metaExtra}
      <p class="sum">${escapeHtml(t.summary || "")}</p>
    </header>

    <section class="teoria-section">
      <h3>Prerrequisitos</h3>
      ${listItems(t.prerequisites, false) || "<p class=\"muted\">Sin prerrequisitos listados.</p>"}
    </section>

    <section class="teoria-section">
      <h3>Pasos</h3>
      ${listItems(t.steps, true) || "<p class=\"muted\">Sin pasos listados.</p>"}
    </section>

    <section class="teoria-section">
      <h3>Qué dibujar</h3>
      ${listItems(t.what_to_draw, false) || "<p class=\"muted\">—</p>"}
    </section>

    <section class="teoria-section">
      <h3>Confirmaciones</h3>
      ${listItems(t.confirmations, false) || "<p class=\"muted\">—</p>"}
    </section>

    <section class="teoria-section">
      <h3>Qué NO hacer</h3>
      ${listItems(t.avoid, false) || "<p class=\"muted\">—</p>"}
    </section>

    <section class="teoria-section">
      <h3>Notas</h3>
      ${listItems(t.notes, false) || "<p class=\"muted\">—</p>"}
    </section>

    <section class="teoria-section vigencia-block">
      <h3>Vigencia</h3>
      <p>${escapeHtml(t.vigencia || "—")}</p>
      <h3>Primas / strike</h3>
      <p>${escapeHtml(t.premiums || "Según tabla del ticker.")}</p>
    </section>

    ${related ? `<section class="teoria-section"><h3>Relacionadas</h3><div class="related-row">${related}</div></section>` : ""}

    <section class="teoria-section theory-chart-section">
      <h3>Cómo se ve en gráfica</h3>
      <p class="theory-chart-edu">Ejemplo educativo (no es un ticker real)</p>
      <p class="muted theory-chart-tf">${escapeHtml((t.example_chart && (t.example_chart.timeframe_label || t.example_chart.title)) || t.timeframe || "")}</p>
      <div id="theory-example-chart" class="theory-example-chart" role="img" aria-label="Gráfica de ejemplo educativa"></div>
      <p id="theory-example-legend" class="theory-example-legend muted"></p>
    </section>

    <p class="hint muted mt">${escapeHtml((theoryData && theoryData.disclaimer) || "")}</p>
  `;

  body.querySelectorAll(".related-chip").forEach((btn) => {
    btn.addEventListener("click", () => openTheoryDetail(btn.dataset.code));
  });

  // Defer chart paint until container is in layout
  requestAnimationFrame(() => renderTheoryExampleChart(t.example_chart));

  detail.hidden = false;
  if (window.matchMedia("(max-width: 900px)").matches && listPane) {
    listPane.classList.add("teoria-list-hidden");
  }
  detail.scrollIntoView({ behavior: "smooth", block: "start" });
}

function closeTheoryDetail() {
  destroyChart(THEORY_CHART_ID);
  const detail = $("#teoria-detail");
  const listPane = $("#teoria-list-pane");
  if (detail) detail.hidden = true;
  if (listPane) listPane.classList.remove("teoria-list-hidden");
  theorySelectedCode = null;
  renderTheoryList();
}

let theoryControlsReady = false;
function setupTheoryControls() {
  if (theoryControlsReady) return;
  theoryControlsReady = true;
  document.querySelectorAll(".teoria-filters .filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      theoryFilter = btn.dataset.filter || "Todas";
      document.querySelectorAll(".teoria-filters .filter-btn").forEach((b) =>
        b.classList.toggle("active", b === btn)
      );
      renderTheoryList();
    });
  });
  const search = $("#teoria-search");
  if (search) {
    search.addEventListener("input", () => {
      theoryQuery = search.value || "";
      renderTheoryList();
    });
  }
  const back = $("#teoria-back");
  if (back) back.addEventListener("click", closeTheoryDetail);
}

/** @deprecated kept for compatibility — redirects to theory */
async function loadStrategies() {
  await loadTheory();
}

function isIos() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
}

function isStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;
}

function showInstallBanner(mode) {
  const banner = $("#install-banner");
  const hint = $("#install-hint");
  const btn = $("#btn-install");
  if (!banner || isStandalone()) return;
  if (localStorage.getItem("cardona-install-dismissed") === "1") return;
  banner.hidden = false;
  if (mode === "android" && deferredInstallPrompt) {
    if (hint) hint.textContent = "Toca Instalar para añadirla a la pantalla de inicio.";
    if (btn) btn.hidden = false;
  } else if (mode === "ios") {
    if (hint) hint.textContent = "En Safari: Compartir → «Añadir a pantalla de inicio».";
    if (btn) btn.hidden = true;
  } else {
    if (hint) hint.textContent = "En Chrome: menú ⋮ → «Instalar app».";
    if (btn) btn.hidden = true;
  }
}

function setupInstallPrompt() {
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    showInstallBanner("android");
  });

  const btn = $("#btn-install");
  if (btn) {
    btn.addEventListener("click", async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      try { await deferredInstallPrompt.userChoice; } catch (_) { /* ignore */ }
      deferredInstallPrompt = null;
      const banner = $("#install-banner");
      if (banner) banner.hidden = true;
    });
  }

  const dismiss = $("#btn-install-dismiss");
  if (dismiss) {
    dismiss.addEventListener("click", () => {
      const banner = $("#install-banner");
      if (banner) banner.hidden = true;
      localStorage.setItem("cardona-install-dismissed", "1");
    });
  }

  if (isStandalone()) return;
  if (isIos()) {
    showInstallBanner("ios");
  } else if (!deferredInstallPrompt) {
    setTimeout(() => {
      if (!deferredInstallPrompt && !isStandalone()) showInstallBanner("generic");
    }, 2500);
  }
}

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js?v=11", { scope: "/" }).catch((err) => {
      console.warn("SW no registrado:", err);
    });
  });
}

function setupChartToggle() {
  document.querySelectorAll(".chart-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", (ev) => {
      ev.preventDefault();
      const tf = btn.dataset.tf;
      if (!tf) return;
      if (!lastAnalysis) {
        setStatus("Analiza un ticker primero para cambiar la temporalidad.", "");
        return;
      }
      destroyChart("chart-main");
      renderMainChart(lastAnalysis, tf);
    });
  });
}

document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => switchTab(t.dataset.tab)));
const btnAnalyze = $("#btn-analyze");
if (btnAnalyze) btnAnalyze.addEventListener("click", analyze);
const btnScan = $("#btn-scan");
if (btnScan) btnScan.addEventListener("click", scan);
const tickerEl = $("#ticker");
if (tickerEl) {
  tickerEl.addEventListener("keydown", (e) => { if (e.key === "Enter") analyze(); });
  tickerEl.addEventListener("input", () => syncTickers(false));
}

const mobInput = $("#ticker-mobile");
const mobBtn = $("#btn-analyze-mobile");
if (mobInput) {
  if (tickerEl) mobInput.value = tickerEl.value;
  mobInput.addEventListener("input", () => syncTickers(true));
  mobInput.addEventListener("keydown", (e) => { if (e.key === "Enter") analyze(); });
}
if (mobBtn) mobBtn.addEventListener("click", analyze);

renderChips();
updateClock();
setInterval(updateClock, 1000);
loadStrategies();
setupInstallPrompt();
registerServiceWorker();
setupChartToggle();


/* ========== Live polling (~20s) ========== */
// LIVE_POLL_MS declared above

function tfToApi(tf) {
  if (tf === "m15") return "15m";
  if (tf === "daily") return "daily";
  if (tf === "weekly") return "weekly";
  return "hourly";
}

async function pollLiveChart() {
  if (livePollInFlight) return;
  if (document.visibilityState === "hidden") return;
  if (!lastAnalysis || !lastAnalysis.ticker) return;
  const ticker = lastAnalysis.ticker;
  const tf = currentTf || "hourly";
  const apiTf = tfToApi(tf);
  livePollInFlight = true;
  try {
    const res = await fetch("/api/chart/" + encodeURIComponent(ticker) + "?tf=" + encodeURIComponent(apiTf));
    if (!res.ok) return;
    const payload = await res.json();
    if (!payload || !payload.ok || !payload.series) return;
    lastAnalysis.charts = lastAnalysis.charts || {};
    const key = (tf === "m15" || tf === "daily" || tf === "weekly") ? tf : "hourly";
    lastAnalysis.charts[key] = payload.series;
    if (key === "hourly") lastAnalysis.series_1h = payload.series;
    if (key === "m15") lastAnalysis.series_15m = payload.series;
    if (key === "daily") lastAnalysis.series_1d = payload.series;
    if (key === "weekly") lastAnalysis.series_1wk = payload.series;
    lastAnalysis.session = payload.session;
    lastAnalysis.session_label = payload.session_label;
    lastAnalysis.updated_at_local = payload.updated_at_local;
    lastAnalysis.live = true;
    renderMainChart(lastAnalysis, tf, { softUpdate: true, preserveTimeScale: true });
  } catch (err) {
    console.warn("live poll", err);
  } finally {
    livePollInFlight = false;
  }
}

function setupLivePolling() {
  if (livePollTimer) clearInterval(livePollTimer);
  livePollTimer = setInterval(pollLiveChart, LIVE_POLL_MS);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") pollLiveChart();
  });
}

/* ========== Welcome splash: candlesticks spell WELCOME BILLIONAIRE ========== */
const WELCOME_GLYPHS = {
  W: ["1...1","1...1","1...1","1.1.1","11.11","1...1","1...1"],
  E: ["11111","1....","1....","1111.","1....","1....","11111"],
  L: ["1....","1....","1....","1....","1....","1....","11111"],
  C: ["11111","1....","1....","1....","1....","1....","11111"],
  O: [".111.","1...1","1...1","1...1","1...1","1...1",".111."],
  M: ["1...1","11.11","1.1.1","1...1","1...1","1...1","1...1"],
  B: ["1111.","1...1","1...1","1111.","1...1","1...1","1111."],
  I: ["11111","..1..","..1..","..1..","..1..","..1..","11111"],
  N: ["1...1","11..1","1.1.1","1..11","1...1","1...1","1...1"],
  A: [".111.","1...1","1...1","11111","1...1","1...1","1...1"],
  R: ["1111.","1...1","1...1","1111.","1.1..","1..1.","1...1"],
  " ": [".....",".....",".....",".....",".....",".....","....."]
};

function buildWelcomeColumns(text) {
  const cols = [];
  for (let i = 0; i < text.length; i++) {
    const glyph = WELCOME_GLYPHS[text[i]] || WELCOME_GLYPHS[" "];
    const width = glyph[0].length;
    for (let x = 0; x < width; x++) {
      const rows = [];
      for (let y = 0; y < 7; y++) rows.push(glyph[y][x] === "1");
      cols.push(rows);
    }
    if (i < text.length - 1) cols.push([false, false, false, false, false, false, false]);
  }
  return cols;
}

function runWelcomeSplash() {
  const splash = document.getElementById("welcome-splash");
  const canvas = document.getElementById("welcome-canvas");
  const skip = document.getElementById("welcome-skip");
  if (!splash || !canvas) return;

  const preferReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let done = false;
  const finish = function () {
    if (done) return;
    done = true;
    splash.classList.add("is-done");
    setTimeout(function () { try { splash.remove(); } catch (e) {} }, 600);
  };
  if (skip) skip.addEventListener("click", finish);
  setTimeout(finish, preferReduced ? 400 : 4200);

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const cssW = canvas.clientWidth || Math.min(960, window.innerWidth * 0.96);
  const cssH = canvas.clientHeight || Math.min(420, window.innerHeight * 0.55);
  canvas.width = Math.floor(cssW * dpr);
  canvas.height = Math.floor(cssH * dpr);
  const ctx = canvas.getContext("2d");
  if (!ctx) { finish(); return; }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const line1 = buildWelcomeColumns("WELCOME");
  const line2 = buildWelcomeColumns("BILLIONAIRE");
  const gapLines = 18;
  const totalCols = Math.max(line1.length, line2.length);
  const padX = 16;
  const padY = 20;
  const usableW = cssW - padX * 2;
  const usableH = cssH - padY * 2 - gapLines;
  const colW = usableW / totalCols;
  const rowH = (usableH / 2) / 7;
  const bodyW = Math.max(2, colW * 0.55);
  const wickW = Math.max(1, colW * 0.12);

  let seed = 42;
  const rnd = function () { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };

  const candles = [];
  const pushLine = function (cols, y0, basePrice) {
    cols.forEach(function (rows, ci) {
      rows.forEach(function (on, ri) {
        if (!on) return;
        const green = ((ci + ri) % 3) !== 1;
        const open = basePrice + (6 - ri) * 1.2 + (rnd() - 0.5) * 0.3;
        const close = open + (green ? 0.7 + rnd() * 0.5 : -(0.7 + rnd() * 0.5));
        const high = Math.max(open, close) + 0.25 + rnd() * 0.35;
        const low = Math.min(open, close) - 0.25 - rnd() * 0.35;
        candles.push({
          x: padX + ci * colW + colW / 2,
          yBase: y0,
          open: open, close: close, high: high, low: low,
          appearAt: (ci * 7 + ri) * 8
        });
      });
    });
  };
  pushLine(line1, padY, 100);
  pushLine(line2, padY + usableH / 2 + gapLines, 90);

  const priceToY = function (price, yBase) {
    const top = yBase;
    const bot = yBase + rowH * 7;
    return top + (108 - price) / (108 - 88) * (bot - top);
  };

  const start = performance.now();
  const draw = function (now) {
    if (done) return;
    const t = now - start;
    ctx.fillStyle = "#0a0f1a";
    ctx.fillRect(0, 0, cssW, cssH);
    ctx.strokeStyle = "rgba(148,163,184,0.06)";
    ctx.lineWidth = 1;
    for (let g = 1; g < 6; g++) {
      const y = (cssH / 6) * g;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(cssW, y); ctx.stroke();
    }
    candles.forEach(function (c) {
      const local = t - c.appearAt;
      if (local < 0) return;
      const alpha = Math.min(1, local / 280);
      const yO = priceToY(c.open, c.yBase);
      const yC = priceToY(c.close, c.yBase);
      const yH = priceToY(c.high, c.yBase);
      const yL = priceToY(c.low, c.yBase);
      const up = c.close >= c.open;
      const color = up
        ? ("rgba(38,166,154," + (0.25 + alpha * 0.75) + ")")
        : ("rgba(239,83,80," + (0.25 + alpha * 0.75) + ")");
      ctx.strokeStyle = color;
      ctx.lineWidth = wickW;
      ctx.beginPath();
      ctx.moveTo(c.x, yH);
      ctx.lineTo(c.x, yL);
      ctx.stroke();
      const top = Math.min(yO, yC);
      const h = Math.max(2, Math.abs(yC - yO));
      ctx.fillStyle = color;
      ctx.fillRect(c.x - bodyW / 2, top, bodyW, h);
    });
    if (t < 4000) requestAnimationFrame(draw);
  };
  if (preferReduced) {
    candles.forEach(function (c) { c.appearAt = 0; });
    draw(performance.now() + 500);
  } else {
    requestAnimationFrame(draw);
  }
}

setupLivePolling();
runWelcomeSplash();
