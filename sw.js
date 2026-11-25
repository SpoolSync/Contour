// Offline support. Bump VERSION whenever the app files change so phones pick up the new copy.
const VERSION = "contour-2026-11-24-coaching";
const ASSETS = ["./", "index.html", "data/exercises.js", "data/foods.js", "data/cloud.js", "data/pixora-summary.js", "data/vault.js", "data/pixora-usage.js", "data/pixora-feedback.js", "vendor/firebase-app-compat.js", "vendor/firebase-auth-compat.js", "vendor/firebase-firestore-compat.js", "vendor/zxing/zxing-reader.js", "vendor/zxing/zxing_reader.wasm", "manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-180.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(VERSION).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("contour-") && k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;
  const fresh = fetch(req).then(res => { if (res.ok) caches.open(VERSION).then(c => c.put(req, res.clone())); return res; });
  // The page itself is fetched fresh when online so updates arrive; everything else is served from the cache first.
  if (req.mode === "navigate" || url.pathname.endsWith("index.html")) e.respondWith(fresh.catch(() => caches.match(req).then(r => r || caches.match("index.html"))));
  else e.respondWith(caches.match(req).then(r => r || fresh));
});
