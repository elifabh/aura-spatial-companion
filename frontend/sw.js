/**
 * Aura Service Worker
 * Enables offline capability and caching for the PWA.
 */

const CACHE_NAME = 'aura-v1';
const ASSETS = [
    '/',
    '/index.html',
    '/css/styles.css',
    '/js/api.js',
    '/js/camera.js',
    '/js/chat.js',
    '/js/app.js',
    '/manifest.json',
];

// Install — cache core assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate — clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            )
        ).then(() => self.clients.claim())
    );
});

// Fetch — network first, cache fallback (for API), cache first (for assets)
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Don't cache API calls or camera streams
    if (url.pathname.startsWith('/api/') || event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(cached => cached || fetch(event.request))
            .catch(() => caches.match('/index.html'))
    );
});
