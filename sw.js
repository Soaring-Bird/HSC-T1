const ASSETS = [
    "/",
    "/offline",
    "/browse_reviews",
    "/static/css/style.css",
    "/static/js/main.js",
    "static/images/favicon.png",
    "https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.7/semantic.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.js",
    "https://code.jquery.com/jquery-3.1.1.min.js",
    "https://fonts.gstatic.com/s/lato/v24/S6uyw4BMUTPHjx4wXiWtFCc.woff2"
];

const CACHE_NAME = "catalogue-assets-v1";

// Install event
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(ASSETS))
            .then(() => self.skipWaiting())
            .catch((error) => console.error("[Service Worker] Caching failed:", error))
    );
});

// Activate event
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((cacheKeys) => {
            return Promise.all(
                cacheKeys.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log(`[Service Worker] Deleting old cache: ${cache}`);
                        return caches.delete(cache);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event with offline fallback for specific pages
self.addEventListener("fetch", (event) => {
    event.respondWith(
        fetch(event.request)
            .catch(() => {
                return caches.open(CACHE_NAME).then((cache) => {
                    if (event.request.mode === "navigate") {
                        if (event.request.url.endsWith("/browse_reviews")) {
                            return cache.match("/browse_reviews");
                        }
                        if (event.request.url.endsWith("/")) {
                            return cache.match("/");
                        }
                        return cache.match("/offline");
                    }
                    return cache.match(event.request);
                });
            })
    );
});
