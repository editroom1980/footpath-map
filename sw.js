/* フットパスマップメーカー — オフライン用サービスワーカー
   ------------------------------------------------------------------
   方針（「古い版のまま固まる」事故を避けることを最優先にしている）
   ・アプリ本体（HTML/JSON/アイコン）＝ネット優先。つながる時は必ず最新を取りに行き、
     取れたぶんをキャッシュへ。つながらない時だけキャッシュを返す。
   ・地図タイル＝キャッシュ優先（歩きながら同じ場所を何度も見るため）。
     上限を決めて、超えたら古いものから消す。
   ・CDNライブラリ＝版が URL に入っていて中身が変わらないのでキャッシュ優先。
   ・困ったときは アプリのURLに ?nosw=1 を付けて開くと、この仕組みを丸ごと解除できる。
   ------------------------------------------------------------------ */
const SW_VERSION = 'v1';
const APP_CACHE  = 'fp-app-' + SW_VERSION;   // アプリ本体（版ごとに作り直す）
const TILE_CACHE = 'fp-tiles-v1';            // 地図タイル（版をまたいで使い回す）
const LIB_CACHE  = 'fp-lib-v1';              // CDNライブラリ
const TILE_MAX   = 1200;                     // 保存するタイルの上限（超えたら古い順に削除）

const TILE_HOSTS = [
  'tile.openstreetmap.org',
  'tile.openstreetmap.fr',
  'basemaps.cartocdn.com',
  'tile.opentopomap.org',
  'cyberjapandata.gsi.go.jp',
];

// 最初の表示はサービスワーカーがまだ動いていないため、この場で本体を確保しておく
// （これをしないと「一度も圏外テストに耐えられない」状態になる）
const APP_SHELL = ['./', './index.html', './manifest.json', './icon-192.png', './apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    try {
      const c = await caches.open(APP_CACHE);
      await Promise.all(APP_SHELL.map(u => c.add(u).catch(() => {})));   // 1つ失敗しても他は保存する
    } catch (_) {}
    await self.skipWaiting();                // 新しい版をすぐ有効にする
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    // 旧版のアプリキャッシュだけ捨てる（タイルとライブラリは残す）
    await Promise.all(keys.filter(k => k.startsWith('fp-app-') && k !== APP_CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

function isTile(url) {
  return TILE_HOSTS.some(h => url.hostname === h || url.hostname.endsWith('.' + h));
}
function isLib(url) {
  return url.hostname === 'cdnjs.cloudflare.com';
}

// タイルの保存数が上限を超えたら、古いもの（先に入れたもの）から削る
async function trimTiles(cache) {
  const keys = await cache.keys();
  if (keys.length <= TILE_MAX) return;
  const over = keys.length - TILE_MAX;
  for (let i = 0; i < over; i++) await cache.delete(keys[i]);
}

async function cacheFirst(req, cacheName, trim) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req);
  if (hit) return hit;
  try {
    const res = await fetch(req);
    if (res && res.ok) { await cache.put(req, res.clone()); if (trim) trimTiles(cache); }
    return res;
  } catch (_) {
    return hit || Response.error();
  }
}

// ネット優先。取れたら保存し、取れなければ保存済みを返す（クエリ ?v= の違いは無視して探す）
async function networkFirst(req) {
  const cache = await caches.open(APP_CACHE);
  try {
    const res = await fetch(req);
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  } catch (_) {
    const hit = await cache.match(req, { ignoreSearch: true });
    if (hit) return hit;
    // 画面の読み込み（?course=... なども含む）は、保存してある本体で開く
    if (req.mode === 'navigate') {
      const shell = await cache.match('./index.html', { ignoreSearch: true });
      if (shell) return shell;
    }
    throw new Error('offline and not cached');
  }
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;                 // 保存や送信は素通し
  let url;
  try { url = new URL(req.url); } catch (_) { return; }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;

  if (isTile(url))                     { e.respondWith(cacheFirst(req, TILE_CACHE, true));  return; }
  if (isLib(url))                      { e.respondWith(cacheFirst(req, LIB_CACHE, false));  return; }
  if (url.origin === self.location.origin) { e.respondWith(networkFirst(req));              return; }
  // それ以外（経路計算・標高など）は素通し＝オフラインでは普通に失敗する
});

// アプリ側からの指示：保存済みタイルの数を返す／タイルを丸ごと消す
self.addEventListener('message', e => {
  const msg = e.data || {};
  if (msg.type === 'tileCount') {
    e.waitUntil((async () => {
      const cache = await caches.open(TILE_CACHE);
      const keys = await cache.keys();
      (e.source || {}).postMessage && e.source.postMessage({ type: 'tileCount', count: keys.length });
    })());
  }
  if (msg.type === 'clearTiles') {
    e.waitUntil((async () => {
      await caches.delete(TILE_CACHE);
      (e.source || {}).postMessage && e.source.postMessage({ type: 'tilesCleared' });
    })());
  }
});
