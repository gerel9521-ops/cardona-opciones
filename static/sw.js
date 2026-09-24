/* Método Cardona — service worker (shell offline; API requiere red) */
const CACHE = "cardona-shell-v11-realtime-welcome";
const SHELL = [
  "/",
  "/static/styles.css?v=11",
  "/static/app.js?v=11",
  "/static/vendor/lightweight-charts.js?v=11",
  "/static/styles.css",
  "/static/app.js",
  "/static/vendor/lightweight-charts.js",
  "/static/manifest.webmanifest",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

function offlinePage() {
  return new Response(
    "<!DOCTYPE html><html lang=\"es-MX\"><head><meta charset=\"UTF-8\"/><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/><title>Método Cardona</title><style>body{font-family:system-ui,sans-serif;background:#0b1220;color:#e2e8f0;padding:24px;line-height:1.5}a{color:#60a5fa}</style></head><body><h1>Sin conexión al servidor</h1><p>La app no pudo cargar. Abre de nuevo el enlace que te envió Grok Bot, o en Safari: Ajustes del sitio → Borrar datos del sitio, y vuelve a entrar.</p></body></html>",
    { status: 503, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" } }
  );
}

function ensureResponse(res) {
  return res instanceof Response ? res : offlinePage();
}

function isNetworkFirst(url) {
  const p = url.pathname;
  if (p === "/" || p === "/index.html" || p === "/sw.js") return true;
  if (p === "/static/app.js" || p === "/static/styles.css") return true;
  if (p === "/static/vendor/lightweight-charts.js") return true;
  if (p.endsWith(".html") || p.endsWith("app.js") || p.endsWith("styles.css")) return true;
  return false;
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL).catch(() => undefined)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) return;
  if (event.request.method !== "GET") return;

  if (isNetworkFirst(url) || event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          if (res && res.ok && url.origin === self.location.origin) {
            const clone = res.clone();
            caches.open(CACHE).then((cache) => cache.put(event.request, clone)).catch(() => {});
          }
          return ensureResponse(res);
        })
        .catch(() =>
          caches.match(event.request).then((c) =>
            c || caches.match("/").then((root) => ensureResponse(root))
          )
        )
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const network = fetch(event.request)
        .then((res) => {
          if (res && res.ok && url.origin === self.location.origin) {
            const clone = res.clone();
            caches.open(CACHE).then((cache) => cache.put(event.request, clone)).catch(() => {});
          }
          return ensureResponse(res);
        })
        .catch(() => ensureResponse(cached));
      return cached || network;
    })
  );
});
