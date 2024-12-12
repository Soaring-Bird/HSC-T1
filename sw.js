const CACHE_NAME = "site-cache-v1";
const ASSETS = [
    "/", // Home page
    "/static/css/style.css",
    "/static/js/main.js",
    "static/images/favicon.png",
    "/offline.html", // Offline fallback
    "https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.7/semantic.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.js",
    "https://code.jquery.com/jquery-3.1.1.min.js",
    "https://fonts.gstatic.com/s/lato/v24/S6uyw4BMUTPHjx4wXiWtFCc.woff2"
];

// Install event: Cache assets
self.addEventListener("install", (event) => {
    console.log("[Service Worker] Install event triggered.");
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log("[Service Worker] Caching assets:", ASSETS);
            return cache.addAll(ASSETS);
        }).catch((error) => {
            console.error("[Service Worker] Caching failed:", error);
        })
    );
    self.skipWaiting(); // Activate immediately
});

// Activate event: Clean up old caches
self.addEventListener("activate", (event) => {
    console.log("[Service Worker] Activate event triggered.");
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            console.log("[Service Worker] Existing caches:", cacheNames);
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log(`[Service Worker] Deleting old cache: ${cache}`);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim(); // Take control of open pages
});

// Fetch event: Serve from cache or network, with offline fallback
self.addEventListener("fetch", (event) => {
    console.log(`[Service Worker] Fetch event for: ${event.request.url}`);
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                console.log(`[Service Worker] Serving from cache: ${event.request.url}`);
                return cachedResponse;
            }
            console.log(`[Service Worker] Attempting network fetch: ${event.request.url}`);
            return fetch(event.request).then((networkResponse) => {
                // Cache the new response if successful
                return caches.open(CACHE_NAME).then((cache) => {
                    console.log(`[Service Worker] Caching new resource: ${event.request.url}`);
                    cache.put(event.request, networkResponse.clone());
                    return networkResponse;
                });
            });
        }).catch((error) => {
            console.error(`[Service Worker] Fetch failed for ${event.request.url}:`, error);
            // Serve offline fallback for navigation requests
            if (event.request.mode === "navigate") {
                console.log("[Service Worker] Serving offline fallback.");
                return caches.match("/offline.html");
            }
        })
    );
});
