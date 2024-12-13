const ASSETS = [
    "/", // The root page
    "/offline", // Offline fallback page
    "/browse_reviews", // Reviews browsing page
    "/static/css/style.css", // Custom CSS file
    "/static/js/main.js", // Main JS file for functionality
    "static/images/favicon.png", // Favicon image
    "https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.7/semantic.min.css", // Semantic UI CSS
    "https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.js", // Semantic UI JS
    "https://code.jquery.com/jquery-3.1.1.min.js", // jQuery library
    "https://fonts.gstatic.com/s/lato/v24/S6uyw4BMUTPHjx4wXiWtFCc.woff2" // Lato font (woff2 format)
];

// The name of the cache, which will be used to store assets in the cache storage.
// This is versioned to allow for easier cache invalidation when the assets change.
const CACHE_NAME = "offline-cache";

// Service Worker 'install' event handler
self.addEventListener("install", (event) => {
    // Prevent the default installation process from completing until the cache is populated.
    event.waitUntil(
        // Open or create a cache named 'CACHE_NAME'.
        caches.open(CACHE_NAME)
            .then((cache) => {
                // Add all the assets defined in the ASSETS array to the cache.
                return cache.addAll(ASSETS);
            })
            .then(() => {
                // After successfully caching, activate the service worker immediately.
                self.skipWaiting();
            })
            .catch((error) => {
                // If caching fails, log the error to the console.
                console.error("[Service Worker] Caching failed:", error);
            })
    );
});

// Service Worker 'activate' event handler
self.addEventListener("activate", (event) => {
    // Wait for the activation process to complete before handling any requests.
    event.waitUntil(
        // Get all the existing cache keys in the Cache Storage.
        caches.keys().then((cacheKeys) => {
            // Iterate over each cache and delete those that do not match the current CACHE_NAME.
            return Promise.all(
                cacheKeys.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        // If the cache is outdated, delete it.
                        console.log(`[Service Worker] Deleting old cache: ${cache}`);
                        return caches.delete(cache);
                    }
                })
            );
        }).then(() => {
            // After cache cleanup, claim control over all clients.
            self.clients.claim();
        })
    );
});

// Service Worker 'fetch' event handler - Intercepts all fetch requests made by the client
self.addEventListener("fetch", (event) => {
    // Respond with the network request or use the cache if the network fails
    event.respondWith(
        // Try to fetch the resource from the network
        fetch(event.request)
            .catch(() => {
                // If network request fails, attempt to serve from cache
                return caches.open(CACHE_NAME).then((cache) => {
                    // If the request is for a page (i.e., 'navigate' mode), handle accordingly
                    if (event.request.mode === "navigate") {
                        // If the user is trying to access the reviews page, serve it from the cache
                        if (event.request.url.endsWith("/browse_reviews")) {
                            return cache.match("/browse_reviews");
                        }
                        // If the user is trying to access the homepage, serve it from the cache
                        if (event.request.url.endsWith("/")) {
                            return cache.match("/");
                        }
                        // For other navigation requests, serve the offline fallback page
                        return cache.match("/offline");
                    }
                    // For non-navigate requests (e.g., static assets like images, scripts, etc.), serve them from the cache
                    return cache.match(event.request);
                });
            })
    );
});
