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

// Listen for messages from the frontend to schedule notifications
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SCHEDULE_PUSH') {
        const { title, options, delayMs } = event.data;
        
        // Since Service Workers can't use setTimeout easily without keeping the SW alive,
        // we'll use a simple setTimeout. For a robust production app, the Push API is used.
        // For our simulated local push, this is perfect.
        setTimeout(() => {
            self.registration.showNotification(title, options);
        }, delayMs || 5000);
    }
});

// Handle clicking the notification
self.addEventListener('notificationclick', event => {
    event.notification.close(); // Close the notification

    // This looks to see if the current is already open and focuses if it is
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(windowClients => {
            const urlToOpen = event.notification.data ? event.notification.data.url : '/';
            
            // Check if there is already a window/tab open with the target URL
            for (let i = 0; i < windowClients.length; i++) {
                const client = windowClients[i];
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            
            // If not, open a new window/tab
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});
