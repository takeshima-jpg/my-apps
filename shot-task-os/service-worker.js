// ネットワーク優先戦略 - 常に最新を取得（HTTPキャッシュも無視）
// SW_VERSION: 更新時にこの値を変えると確実に更新サイクルが走る
const SW_VERSION = '2026-06-18-2';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil((async () => {
  const keys = await caches.keys();
  await Promise.all(keys.map(k => caches.delete(k)));
  await self.clients.claim();
  // 新SW有効化時、開いている既存タブを最新コードへ自動リロード
  try {
    const wins = await self.clients.matchAll({ type: 'window' });
    for (const c of wins) { c.navigate(c.url); }
  } catch (e) {}
})()));
self.addEventListener('fetch', e => {
  const req = e.request;
  const isDoc = req.mode === 'navigate' || req.destination === 'document';
  e.respondWith((async () => {
    try {
      // HTML本体は常にHTTPキャッシュを無視してオリジンから最新取得
      return await fetch(req, isDoc ? { cache: 'reload' } : undefined);
    } catch (err) {
      let cached = null;
      try { cached = await caches.match(req); } catch (e2) {}
      return cached || new Response('オフライン: ネットワークに接続できませんでした。再接続して再読み込みしてください。', {
        status: 503,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' }
      });
    }
  })());
});
