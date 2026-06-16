// ネットワーク優先戦略 - 常に最新を取得（失敗時も必ずResponseを返す）
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(keys => Promise.all(keys.map(k => caches.delete(k))))
    .then(() => self.clients.claim())
));
self.addEventListener('fetch', e => {
  e.respondWith((async () => {
    try {
      return await fetch(e.request);
    } catch (err) {
      let cached = null;
      try { cached = await caches.match(e.request); } catch (e2) {}
      return cached || new Response('オフライン: ネットワークに接続できませんでした。再接続して再読み込みしてください。', {
        status: 503,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' }
      });
    }
  })());
});
