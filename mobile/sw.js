// ProctorAI Service Worker — v1.0.0
const CACHE_NAME = 'proctorai-v1';
const STATIC_ASSETS = [
    './',
    './index.html',
    './manifest.json',
    './css/design-system.css',
    './css/components.css',
    './css/pages.css',
    './js/state.js',
    './js/api.js',
    './js/mock.js',
    './js/app.js',
    './js/components/toast.js',
    './js/components/modal.js',
    './js/components/nav.js',
    './js/components/card.js',
    './js/components/chart.js',
    './js/components/camera-feed.js',
    './js/pages/login.js',
    './js/pages/student.js',
    './js/pages/exam-session.js',
    './js/pages/proctor.js',
    './js/pages/admin.js',
    './assets/icons/favicon.svg'
];

// Install — cache static assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
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

// Fetch — cache-first for static, network-first for API
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Network-first for API calls
    if (url.pathname.startsWith('/auth') || 
        url.pathname.startsWith('/exams') || 
        url.pathname.startsWith('/sessions')) {
        event.respondWith(
            fetch(event.request)
                .catch(() => caches.match(event.request))
        );
        return;
    }

    // Cache-first for static assets
    event.respondWith(
        caches.match(event.request)
            .then(cached => cached || fetch(event.request).then(response => {
                // Cache new successful responses
                if (response.status === 200) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return response;
            }))
            .catch(() => {
                // Offline fallback for navigation requests
                if (event.request.mode === 'navigate') {
                    return caches.match('./index.html');
                }
            })
    );
});

// Background sync for queued violation reports
self.addEventListener('sync', event => {
    if (event.tag === 'sync-violations') {
        event.waitUntil(syncViolations());
    }
});

async function syncViolations() {
    // Future: sync queued violation reports when back online
    console.log('[SW] Syncing queued violations...');
}
