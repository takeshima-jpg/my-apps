// コックピット最小Service Worker（PWAインストール要件のためだけに存在する）
//
// 【重要・過去のSWキャッシュ事故の再発防止】
// - キャッシュは一切持たない「パススルーSW」。fetchは何もせずブラウザ既定＝常にネットワーク
// - スコープはこのファイルの置き場所＝ launcher/ 配下のみ。
//   iframeで読み込む各OS（../task-os/ 等）はスコープ外なので、このSWの影響を受けない
// - activate時に（過去に何か残っていても）このスコープのCacheStorageを全削除する
// - オフライン動作は狙わない（目的はホーム追加とstandalone表示のみ）

const SW_VERSION = 'cockpit-sw-v1';   // 更新時はこの版数を上げる（旧キャッシュはactivateで破棄）

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map(k => caches.delete(k)));   // 旧キャッシュを確実に破棄
    await self.clients.claim();
  })());
});

// 何もしない＝リクエストはすべてネットワークへ（キャッシュ事故を構造的に起こさない）
self.addEventListener('fetch', () => {});
