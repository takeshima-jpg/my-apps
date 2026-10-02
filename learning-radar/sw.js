// 学びレーダー Service Worker
// - ネットワーク優先（HTML本体はHTTPキャッシュも無視して常に最新を取得）
// - オフライン時の代替として index.html と manifest.json だけを保持する
// - 【過去のSWキャッシュ事故の再発防止】版が変わったら自分の古いキャッシュを消す。
//   他OSのキャッシュ・他オリジン（Drive API等）のリクエストには触らない
// SW_VERSION: 更新時にこの値を変えると確実に更新サイクルが走る
const SW_VERSION = '2026-10-02-3';
const CACHE_PREFIX = 'learning-radar-';
const CACHE = CACHE_PREFIX + SW_VERSION;
const KEEP = ['./index.html', './manifest.json'];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(KEEP.map(u => new Request(u, { cache: 'reload' }))))
      .catch(() => {})
  );
});

self.addEventListener('activate', e => e.waitUntil((async () => {
  const keys = await caches.keys();
  await Promise.all(keys.filter(k => k.startsWith(CACHE_PREFIX) && k !== CACHE).map(k => caches.delete(k)));
  await self.clients.claim();
})()));

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;            // Drive API 等はそのままネットワークへ
  const isDoc = req.mode === 'navigate' || req.destination === 'document';
  const isManifest = /\/manifest\.json$/.test(url.pathname);
  if (!isDoc && !isManifest) return;                           // アイコン等は保持しない（ブラウザ既定）
  const key = isDoc ? './index.html' : './manifest.json';
  e.respondWith((async () => {
    try {
      const res = await fetch(req, isDoc ? { cache: 'reload' } : undefined);
      if (res && res.ok) { const c = await caches.open(CACHE); c.put(key, res.clone()); }
      return res;
    } catch (err) {
      let hit = null;
      try { hit = await (await caches.open(CACHE)).match(key); } catch (e2) {}
      return hit || new Response('オフライン: ネットワークに接続できませんでした。再接続して再読み込みしてください。', {
        status: 503,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' }
      });
    }
  })());
});
