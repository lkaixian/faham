/* Tulen service worker. Purpose: the pages and the offline safety tools (I already paid, Someone just called)
   must open with no signal. Rules:
   - Only same-origin GET requests for the app shell are cached.
   - /api/ and any cross-origin request (the backend, the LLM, fonts) are never touched, so no letter text,
     result or user data can end up in this cache.
   - Network first, cache as the fallback, so a new deploy is never hidden behind an old copy. */
const VERSION = "faham-shell-v1";
const SHELL = [
  "./", "index.html", "embed.html", "manifest.webmanifest",
  "assets/css/styles.css",
  "assets/js/config.js", "assets/js/data.js", "assets/js/i18n.js", "assets/js/app.js", "assets/js/safety.js", "assets/js/intro.js",
  "assets/img/tulen-wordmark-light.png", "assets/img/tulen-wordmark-dark.png", "assets/img/icon-192.png", "assets/img/icon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => Promise.all(SHELL.map((u) => c.add(u).catch(() => null)))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSION).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== "GET" || u.origin !== self.location.origin || u.pathname.includes("/api/")) return;
  e.respondWith(
    fetch(r).then((res) => {
      if (res.ok) { const copy = res.clone(); caches.open(VERSION).then((c) => c.put(r, copy)); }
      return res;
    }).catch(() => caches.match(r, { ignoreSearch: true }).then((hit) => hit || (r.mode === "navigate" ? caches.match("index.html") : Response.error())))
  );
});
