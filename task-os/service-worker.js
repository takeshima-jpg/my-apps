const CACHE_NAME = 'task-os-v6';
const ASSETS = [
  './index.html',
  './manifest.json'
];

// インストール：コアファイルをキャッシュ
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

// アクティベート：古いキャッシュを削除
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// フェッチ：キャッシュ優先、なければネットワーク
self.addEventListener('fetch', e => {
  // 各OSのiframe（../routine-os/ 等）はキャッシュしない
  if (e.request.url.includes('../')) return;
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
