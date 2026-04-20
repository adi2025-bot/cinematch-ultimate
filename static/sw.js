// CineMatch Service Worker — Offline caching
const CACHE_NAME = 'cinematch-v3';
const PRECACHE = ['/', '/static/style.css?v=3', '/static/app.js?v=3'];

self.addEventListener('install', e => {
    e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(PRECACHE)));
    self.skipWaiting();
});

self.addEventListener('activate', e => {
    e.waitUntil(caches.keys().then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    )));
    self.clients.claim();
});

self.addEventListener('fetch', e => {
    if (e.request.method !== 'GET') return;
    
    const url = new URL(e.request.url);
    
    // API Caching: Stale-While-Revalidate (great for offline functionality)
    if (url.pathname.includes('/api/')) {
        e.respondWith(
            caches.open(CACHE_NAME).then(cache => {
                return cache.match(e.request).then(cachedResponse => {
                    const fetchedResponse = fetch(e.request).then(networkResponse => {
                        cache.put(e.request, networkResponse.clone());
                        return networkResponse;
                    }).catch(() => {});
                    
                    return cachedResponse || fetchedResponse;
                });
            })
        );
        return;
    }

    // Static Assets & Others: Network First, fallback to cache
    e.respondWith(
        fetch(e.request).then(res => {
            const clone = res.clone();
            caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
            return res;
        }).catch(() => caches.match(e.request))
    );
});
