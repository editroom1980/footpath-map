# ARCHITECTURE — フットパスマップメーカー 設計書

対象：**v100**（`index.html` / `sw.js`）
読む人：このアプリを直す人（人間・AI どちらも）

`CLAUDE.md`（作業規約）→ 本書 → `HANDOFF_開発引き継ぎ書.md`（経緯と変更履歴）の順で読む。
**本書の 4章「絶対に守ること」だけは、作業前に必ず目を通すこと。**

---

## 1. 全体像

| | |
|---|---|
| 実体 | **単一ファイル `index.html`**（HTML + CSS + インラインJS、約5,900行）＋ `sw.js`（オフライン用・約120行） |
| 外部依存 | CDN(cdnjs)の **Leaflet 1.9.4** / **html2canvas 1.4.1** / **qrcodejs 1.0.0** の3本だけ |
| 外部サービス | 地図タイル（OSM・地理院・OpenTopoMap・CARTO）／経路 **OSRM公開デモ**／標高 **地理院API**／住所検索 Nominatim |
| 配信 | GitHub Pages（`editroom1980/footpath-map`）。push で自動公開 |
| 保存 | コース＝**localStorage**（約5MB）／写真＝**IndexedDB**／どちらも端末内のみ。サーバに何も送らない |
| 認証 | 無し。アカウント不要 |

同じ場所に置くファイル：`index.html` / `sw.js` / `manifest.json` / `version.json` / `sample.json` / アイコン4種。
配布用コースJSON（`?course=` で読む）も同じ場所に置く。

---

## 2. 画面と主要な状態

画面は2つだけ。DOMの表示切替で行き来する（ページ遷移はしない）。

- **S1 = 起動画面**（`#s1`）… 保存済みコース一覧・読み込み・バックアップ・新規作成
- **S2 = 地図画面**（`#s2`）… 作成/編集・表示切替・書き出し

主要なグローバル状態（`STATE` 区画にまとめる。新設時も必ずここへ）：

| 変数 | 中身 |
|---|---|
| `wps` | スポット（ウェイポイント）配列。`{id,type,name,desc,tel,dwell,lat,lng,photos[],labelDir,onRoute,marker}` |
| `vps` | 調整点（Via Point）配列。ルートの通り道を手で決めるための点 |
| `routeLine` / `_routeLineBase` | 画面上のルート線（**v117以降は切れ端の集まり**）/ **その素の座標**（データ準拠） |
| `routeCasing` | ルート線の下に敷く白い実線（v103）。**表示専用** |
| `routeDirs` | 進行方向の三角。**表示専用** |
| `_lastRouteCoords` | 実際に採用されたルート座標。**GPX・距離・高低差の出どころ** |
| `hitOverlays` | 区間ごとの当たり判定用の透明な線 |
| `courseInfo` / `currentCourseId` | 開いているコースの名称等 / そのID |
| `viewMode` | 閲覧モード（タップで写真・解説を出す） |
| `_dirty` | **保存していない変更があるか**（編集の共通入口 `saveSnapshot()` で立つ） |
| `_labelSizeIdx` / `_wpSizeIdx` / `_walkSpeedIdx` | 文字サイズ・○サイズ・歩く速さの段階（定数配列の添字） |

---

## 3. データの形

### コース1本（保存・書き出しの単位）
```
{ id, name, area, desc, center, zoom,
  wps:[{id,type,name,desc,tel,dwell,fitBefore,fitAfter,onRoute,lat,lng,labelDir,photos[]}],
  vps:[{id,segAfter,fitBefore,fitAfter,lat,lng,order}],
  customPaths:[{id,pts:[[lat,lng],…]}],      // 手描きの道
  routes:{ "lng,lat;lng,lat": [[lat,lng],…] }, // 区間ごとの道順（v119）。読み込み時に segCache へ戻す
  elevs: { "lat,lng": m },                     // 点ごとの標高（v127）。読み込み時に elevCache へ戻す。routes と共に計算後に静かに書き足される
  kokoroe: "この地域からのお願い",              // 歩く人の心得の地域の追記（v137）。標準の文は KOKOROE 定数
  info: { access, car, toilet, rest, season, notes, contact, diff }, // コースの情報（v139）。空欄は入れない。diff は手で選んだ★（1〜3）だけ
  vps[].guide: { kind:"turn"|"caution", dir, ctype, note, photos[] }, // 分岐・注意の案内（v141）。写真は idb: 参照
  stickers: true,                      // 写真のある印をシールで見せる（v142）。OFF のときは書かない
  theme: { preset, route, dash, width }, // 地図の色（v145）。標準のときは書かない。印の色は WT[].c を書き換えて一本化
  check: { walked:true, private:true },  // 配る前の確認の手の✓（v146）。無ければ書かない
  noEdit: true,                        // 他の人による改変を断る（v147）。配布ファイル（shared:true）にだけ効く。無ければ書かない
  shared: true,                        // 「リンクを作る」で書き出した配布ファイルの印（v147）。保存データには入れない
  // まわりの施設（v144）の出どころは OpenStreetMap・国土数値情報・地理院地図Vector・Wikidata・Wikipedia（v238）。Google Places/Maps の情報は規約で使えない（載せない・取りに行かない）
  // 発見（v143）はコースの保存データには入らない。端末の LS.finds = { [courseId]: [{id, lat, lng, word, by, at, photos[]}] }。送るファイルは {fpFinds:1, courseId, courseName, finds:[…写真は実体]}
  maxWpId, maxVpNum, savedAt, version }
```

### 消える前に知らせるための記録（コースとは別・端末ごと、v121）
`LS.backupAt`（最後に「すべて書き出す」をした日時）／`LS.saveCount`（その後の保存回数）／`LS.firstSaveAt`（最初の保存）。
`renderCourseList()` のたびに `backupStatus()` で 30日＝黄・60日＝赤 を判定して一覧に出す。
**保存の入口を足したら `_noteSaved()`、書き出しの入口を足したら `_noteBackup()` を呼ぶこと。**

### 写真の持ち方（v89以降）
- ブラウザ内の保存では `photos:['idb:p123abc', …]` の**参照**だけを持つ。実体は IndexedDB。
- **書き出し（JSON・共有リンク・バックアップ）では実体（data URI）を埋め込み直す**。
  → 配ったファイルは**1つで完結**する。この性質は絶対に壊さない。
- 表示は `_photoAttr()` で `data-photo` 属性にし、`_fillPhotoImgs()` が後から実体を流し込む。

### 保存先の分担
| 保存先 | 何を | 備考 |
|---|---|---|
| localStorage | コース本体・各種設定 | 上限約5MB。キーは **`LS` オブジェクトに集約**（ハードコード禁止） |
| IndexedDB (`footpath/photos`) | 写真の実体 | 使えない環境では自動的に「本体に埋め込む」従来動作に落ちる |
| Cache Storage | アプリ本体・地図タイル・CDN部品 | `sw.js` が管理（9章） |

---

## 4. 絶対に守ること（ここを壊すと過去の不具合が再発する）

1. **`_buildDisplayCoords()` は表示専用**。
   往復する区間だけを右へずらして「行き」と「帰り」を見分けられるようにする処理。
   **`_lastRouteCoords`・`hitOverlays`・高低差・保存データを一切変えてはならない。**
   往復が無ければ**素の座標をそのまま返す**（単線に余計なずれを掛けない）。
   ずらす向きは常に進行方向の**右法線**（行きと帰りが必ず反対側になり交差しない）。折返しは半円キャップ。
   間隔調整は **`OFF_GEO_M` 1か所**（上限 `OFF_MAX_PX`）。ズーム変更時は `_redrawRouteOffset`（zoomend）で再計算。

2. **書き出したファイルは自己完結**（写真の実体を含む）。参照 `idb:` を書き出してはならない。

3. **localStorage のキーは `LS` に集約**。増減・改名はそこだけ。

4. **ラベル（`bindTooltip`）をインラインで変えたら `tooltip.update()` を呼ぶ**。呼ばないと位置が古いままずれる。

5. **保存画像の○内文字は `line-height` で中央寄せ**（flex中央寄せは html2canvas がずらす）。

6. **撮影用に変えた見た目は、必ず作り直して戻す**。
   `_captureMapCanvas()` の `finally` は `updateTooltip()` / `refreshIcons()` を呼んで**状態を作り直す**方式。
   保存値の巻き戻しはしない（v84でこの取り違えにより「調整点が消えたまま」になる不具合が出た）。

7. **`?course=` で読めるのは同じ場所の `.json` だけ**（`_safeCourseFile` が `../`・外部URL・`/`・`:` を拒否）。
   外部のデータを読み込ませない。

8. **版数は3か所そろえる**（10章）。

16. **画面の語と内部名は別**（v130）。画面は「スポット／調整点／手描きの道／手描き／道なりに引く／
    手描きの道に合わせる／閲覧モード」、コードと保存データは `wps/vps/customRoads/draw/manualMode/_snapOn_/viewMode` のまま。
    文言を足すときは画面の語を使い、内部名・キーは変えない（対応表は HANDOFF 2章）。
15. **種別の選び方は select（隠す）＋チップ**（v128）。`saveModal` は `#mType.value` を読むだけ、`_buildTypeOptions(wp)` が
    選べる種類を select に入れ、`_renderTypeChips()` はそれを読んで描く。種類の制限（スタート／ゴールは両端だけ）を
    足すときは `_buildTypeOptions` だけ直す。地図タップは `addWp(…,'course')` で即置く（選択画面を戻さない）。
14. **PCの道具は3群で、id は据え置き**（v126）。左の縦の道具＝`#tbar`（`btnWp/btnVia/btnUndo/btnRedo`）、右上＝`#pcTr`
    （`btnBaseMap`→`#popMap`、`btnLegend`→`#popLegend`）、下＝`#pcBl`（`btnElev`）、上バー＝`#hdr`（`btnView/btnMore`→`#popMore`）。
    どれも `#mapWrap` の上に浮かせているだけで、`#map` の外なので保存画像には写らない。状態の反映は `_syncPcPops()`
    が変数から描き直す（ボタンの見た目を直接いじらない）。閲覧中・共有リンク・埋め込み・スマホで隠す規則は `#tbar/#pcHint/#pcTr/#pcBl` を見る。
13. **「配る」の出口は `shareExit()` の呼び分けだけ**（v123）。画像・印刷用シート・リンク・GPX の中身を `#shareSheet` 側に
    複製しない。出口を足すときは `.ss-card` を1枚増やして `shareExit` に1行足す。「この地図に載る情報」は `renderShareInfo()`
    が開くたびに実データから数える（保存しない）。
12. **文字の無いボタンには必ず `aria-label`**（v122）。読み上げで「ボタン」としか聞こえないのを防ぐ。JSで作る雛形も同じ。
    検査が HTML・雛形・実画面の3か所で数えるので、付け忘れると落ちる。**ページ全体の拡大は止める**（v135・`user-scalable=no`
    ＋ `touch-action:manipulation`）。v122 で一度許したが、iPhone のホーム画面アプリで地図の外を二本指で触るとページごと拡大され、
    固定の帯やボタンが画面の外へ出た（オーナー報告）。文字の大きさはアプリ内の設定で変える。地図は `#map{touch-action:none}` で
    ピンチを Leaflet に渡す。
11. **閲覧中（`viewMode`）は編集の操作を一切受け付けない**（v120）。見た目は `body.viewing`（共有リンクは `body.viewonly` も）で
    隠し、動きは `onMapClick`／`openModal`／`undoLast`／`redoAction`／`clearAll`／一覧のドラッグの `if (viewMode) return;` と
    `_applyViewLock()`（印の `dragging.disable()`）で止める。**編集の入口を足したら、この門も足すこと。**
10. **共有リンク・保存データを開くとき、経路サーバも標高サーバも呼ばない**（v119・v127）。`routes` を `segCache` に、`elevs` を `elevCache` に戻してから
    道なり計算に入るので、計算はすべてキャッシュに当たる。**直線に逃げた結果（`fallback`）は覚えない・保存しない**
    （保存すると、サーバ復旧後も直線のまま固まる）。区間のキーは `_segKey()` の1か所で作る。
9. **スポットの色は `WT` の1か所だけ**。`.wp-tt-<種別>` のCSSは起動時に `_injectWpStyles()` が
   WTから作り、画像保存の色も WT から引く。**CSSや画像保存側に色を直書きしない**
   （v98以前は3か所に同じ色が書かれ、ビュースポットと駐車場が同色になっていた）。

---

## 5. 描画パイプライン（最重要）

```
スポット/調整点
   ↓ buildRoutedCoords()            区間ごとに 手描きの道→OSRM→直線 の順で座標を作る
   ↓ _despikeSeg()                  ほぼ180°の極小な折返し（ひげ）だけ除去。角は残す
_lastRouteCoords / _routeLineBase   ← ★これが「実データ」。GPX・距離・高低差はここから
   ↓ _buildDisplayCoords()          ★表示専用：往復区間だけ右へずらす
routeLine.setLatLngs(...)           ← 画面に出る赤い破線
   ├ routeCasing                    ★表示専用：同じ座標の白い実線を「下」に敷く（v103）
   └ routeDirs                      ★表示専用：切れ端のあいだに進行方向の三角（v117）
```

**表示専用（`routeCasing`）の約束**
- すべて `interactive:false`。当たり判定（`hitOverlays`）には**絶対に使わない**。
- 座標は必ず `_buildDisplayCoords()` の結果を共有する（別々に作るとずれる）。
- `removeLines()` で必ず消す。消し忘れると古い線が残る。
- **進行方向は「30pxごとの小さな三角」で示す**（v112、`routeDirs`／`_buildDirMarks`）。
  置き方は3つのきまり：①破線 `DIR_EVERY_DASHES` 本ごと ②スポットの手前に必ず1つ
  ③スポット手前の三角とその前の三角の間の破線が `DIR_MIN_DASHES` 本以下なら手前の「ふつうの三角」を飛ばす。
  **線そのものを「破線ちょうど n 本ぶん」の切れ端に分けて描く**（`routeLine` は複数の線の集まり）。
  切れ端ごとに破線が引き直されるので破線の長さがそろい、切れ端のあいだに三角が入る。
  1本の線に引いて上から消すやり方（v116）は、消した所の前後で破線が中途半端に切れるので使わない。
  スポットの位置は**線に下ろした足**で測る（往復ずらし表示では線がスポットから少しずれるため、頂点だけ見ると外す）。
  保存先と向きは**線に沿った距離**で決める（隣り合う点の角度で決めると、点が細かい
  OSRMのルートでは判定できない）。**スポットの○に近い位置は飛ばす**（○の下に入ると見えない）。
  表示専用の約束は `routeCasing` と同じ。
  経緯：v108 まばらな矢印 → v109 矢印の連なり → v110 取り下げ → v111 曲がり角だけ → v112 一定間隔。
  線に重ねる印は**塗りつぶした三角**が細い線の「>」より読みやすい。

- 当たり判定（`hitOverlays`）は**素の座標**で作る。ずらした線で作ると区間の取り違えが起きる。
- ズームを変えると見かけの間隔が変わるため、`zoomend` で表示座標だけ作り直す。

---

## 6. ルーティング

区間（スポット→スポット、間に調整点があればその区切り）ごとに、次の順で座標を決める：

1. **手描きの道**（手描きの道）が有効で、その区間に沿えるなら手描きの道を使う
2. それ以外は **`ROUTERS` の経路サーバ**（OSRM形式）へ問い合わせる
3. どれも失敗したら**直線**にし、`_warnRouteFallback()` で知らせる（30秒に1回まで）
4. 手動モード（両端の fit が false）は最初から直線

同じ区間の結果は `segCache` に貯めて再利用する。

### 経路サーバの待避（v93）
`ROUTERS` に**同じ形式(OSRM API)のサーバを並べて**おき、順に試す。

| 仕掛け | 定数 | 目的 |
|---|---|---|
| 予備サーバ | `ROUTERS`（公式デモ → FOSSGIS） | 1台止まっても道なりを維持する |
| 同時数の上限 | `ROUTER_MAX_PARALLEL=4` | 一斉に投げない。提供元への配慮と、**止まったサーバを1巡目で見切る**ため |
| サーバごとの休止 | `_routerDead[i]`（`ROUTER_COOLDOWN_MS`） | 止まっているサーバを区間ごとに試して待たされない |
| 全滅時の休止 | `_routerDeadUntil` | つながらない場所で操作が止まらない |

- 切り替わったときは利用者に伝える（黙って別サーバに変えない）。
- **サーバによってルート形状は少し変わる**（データ更新時期や設定の違い）。距離も数%変わりうる。
- 経路URLの直書きは **`ROUTERS` の1か所だけ**（なぞりのスナップも同じサーバを使う）。

> 公開デモは「1秒1回まで・非商用・予告なく停止しうる」と明記されている。
> v93 以前は**20区間を一斉に投げていた**（方針違反かつ、止まったサーバを毎区間試す原因）。

---

## 7. 保存と容量

- `setCourses(list)` は **保存できたら true / 書けなければ false**。
  `saveCourse()` はそれを見て、容量超過なら**警告を出して false を返す**（v81以前は黙って失敗していた）。
- `saveCourse()` は保存前に `_stashLivePhotos()` で写真を IndexedDB へ移す（**非同期**）。
- 起動時に `migratePhotosToIdb()` が既存コースを移行し、`gcPhotos()` が孤児写真を掃除する。
- 一覧画面に使用量を表示（`renderStorageInfo()`／3.5MB超で警告）。

### スタンプラリー（v100）
共有リンクで歩く人の記録。**閲覧モードのときだけ**働く（作る人の画面を汚さない）。
- `VISIT_RADIUS_M`(50m)以内に近づいたスポットに記録が付く（`_checkVisits`。現在地追従から呼ばれる）。
- 記録は `LS.visits` に **コースIDごと・その端末だけ**に保存。**コースの中身は変えない／どこにも送らない**。
- 訪問済みの○には右上にチェックが付き、画面右下に「スタンプ n / m」を表示（押すと全消去）。

### ラベルの自動配置（v99）
`autoPlaceLabels()` が密集したラベルを空いている向き（上→右→下→左）へ逃がす。
- **利用者が「上」以外を選んだラベルは動かさない**。既定(上)のものだけが自動配置の対象。
- 自動で決めた向きは `wp._autoDir`（**保存データには入れない**。`labelDir` は触らない）。
- スポットの○も障害物として扱い、ラベルで他のスポットを隠さない。
- 呼び出しは `scheduleAutoLabels()`（180msでまとめる）。ルート更新・ズーム・サイズ変更のあと。

### 現在地追従（v97）
`toggleFollowMode()` が `watchPosition` を始める。**電池を使うので、使うときだけON。**
- 一覧に戻る／ページを離れるときは必ず止める（`stopFollowMode`）。
- `FOLLOW_MIN_MOVE_M`(4m)以上動いたときだけ地図を寄せる（小刻みな揺れで暴れない）。
- **最初の1回だけ倍率を合わせ、以後は `panTo` だけ**。毎回 `setView` すると、
  利用者が全体を見ようと縮小しても引き戻してしまう。
- コース範囲外（`_inAllowedArea`）では地図を動かさない。

### 難易度（v95）
`DIFFICULTY`（距離と登りの上限）で3段階に分ける。**高低差が取れていないときは出さない**
（`_totalAscent()` が null なら `courseDifficulty()` も null）。サイドバーと印刷用シートに表示。
`_elevData` は**ルートを計算し直すたびに消える**ので、難易度も自然に出たり消えたりする。

---

## 8. 配布のしくみ

| 手段 | 実装 | 備考 |
|---|---|---|
| 共有リンク | `?course=ファイル名.json` | 同じ場所に置いたJSONを読み、**閲覧専用**で表示。見る人の端末には保存しない |
| 確認用リンク | `?view=<コースID>` | 自分の端末のみ（localStorage 参照） |
| 埋め込み | `?course=…&embed=1` | `body.embed` でヘッダ・サイドバー・編集UIを全部隠し、地図＋帯だけにする。帯には コース名・距離・「大きな地図で開く」（`embed` を外したURL） |
| 配る | `openShareSheet()` | 4つの出口（画像・印刷用シート・リンク・GPX）と「載る情報」を1枚に。出口は `shareExit()` が既存関数を呼ぶだけ（v123） |
| 印刷用シート | `openPrintSheet()` | 地図画像＋凡例・縮尺・方位・見どころ・スポット一覧・QR。`@media print` で **A4横**に印刷 |
| QRコード | `LS.shareLinks` に覚えた共有リンクを描画 | ライブラリが無ければQR欄ごと出さない |
| GPX 書き出し | `buildGpx()` | GPX1.1。`<trk>` は**実データ** `_lastRouteCoords`。なぞり端点(node)は除外 |
| GPX 読み込み | `parseGpx()` | `<wpt>`→スポット（`<type>` から種別も復元）。**`<wpt>` があるときは軌跡を取り込まない**（スポットからのルートと二重になり距離が約3倍に狂うため）。`<wpt>` が無い（歩いた記録）ときだけ、始点/終点をスタート・ゴールにし軌跡を手描きの道にする |
| バックアップ | `buildBackupData()` / `applyBackupData()` | 復元は同IDを上書き・無いものを追加（二重に増えない） |

閲覧専用のときは `body.viewonly` で編集UIを隠す（ツールバー・保存ボタン・並替ヒント・モバイルの編集シェルフ）。

> **GPXの限界**：GPXには**調整点(VP)を表す仕組みが無い**ため、書き出して読み戻すと**道順は引き直しになる**
> （実測：調整点17個のコースが 2.36km → 7.43km）。取り込み時にその旨を明示している。
> 道順をそのまま残す用途では **JSON** を使う。

> **手描きの道(customPaths)はコース単位ではなくアプリ全体で共有**（`LS.custompaths`）。
> `loadCourseData()` はコースに手描きの道が入っているときだけ上書きし、空なら現状維持＝消さない。

---

## 9. オフライン（`sw.js`）

共有リンクを開いた端末では、`_autoOfflineForLink()`（v135）がコース範囲のタイルを自動で持ち歩く（回線の種類・節約モード・埋め込みで見送り、コースごとに1回、`?offauto=0` で無効）。手動の「圏外用に保存」（`saveMapOffline`）はそのまま。

**方針は「古い版のまま固まらないこと」を最優先。**

| 対象 | 方式 | 理由 |
|---|---|---|
| アプリ本体（HTML/JSON/アイコン） | **ネット優先**。取れたら保存、取れないときだけ保存済みを返す | つながる限り必ず最新になる |
| 地図タイル | **キャッシュ優先**（上限1200枚・超過分は古い順に削除） | 同じ場所を何度も見るため。圏外対策 |
| CDNライブラリ | **キャッシュ優先** | URLに版が入っており中身が変わらない |
| 経路・標高 | 素通し | オフラインでは普通に失敗させる |

- インストール時に本体を先に確保する（初回表示の直後から圏外に耐える）。
- 画面の読み込みが圏外で失敗したら、保存済みの本体で開く（`?course=` 付きでも可）。
- `saveMapOffline()` がコース範囲のタイルを先読みする（現在の縮尺から2段階・最大600枚・6件ずつ）。
- **困ったときは `?nosw=1`** で登録とキャッシュを全消去できる。

---

## 10. 版の管理（出荷時に必ず）

**3か所を同じ値にそろえる。**

| 場所 | 例 |
|---|---|
| `index.html` の `APP_VERSION` | `'v100'` |
| `version.json` | `{"version":"v100"}` |
| `package.json` の `version` | `1.0.0` |

利用者側は `?v=` を手で書き換えなくてよい。アプリが `version.json` と自分の版を比べ、
違えば**一覧画面のときだけ**「新しい版があります／更新する」を出す
（地図画面で出すと操作ボタンに重なり、編集中の更新は未保存を失うため）。

---

## 11. 非同期の約束（呼ぶときは `await` すること）

`saveCourse` / `exportCourse` / `exportCourseData` / `exportAllCourses` / `applyBackupData` /
`loadCourseFromFile` / `openPrintSheet` / `saveMapAsImage` / `saveMapNoText` / `_captureMapCanvas` /
`_stashPhotos` / `_embedPhotos` / `_photoSrc` / `migratePhotosToIdb` / `gcPhotos` /
`checkForUpdate` / `setupOffline` / `saveMapOffline` / `runSelfCheck`

> 特に `saveCourse()` は **true/false を返す Promise**。`if (saveCourse() === false)` と書くと必ず素通りする。

---

## 12. セクション地図（`index.html`・行番号は目安）

CONSTANTS(904) → STATE(968) → STORAGE(1015) → 版のお知らせ(1021) → オフライン(1077) → 写真ストア(1166)
→ SCREEN 1(1368) → GEOCODING(1493) → 背景地図(1505) → MAP INIT(1560) → 表示範囲の制限(1600)
→ 手描きの道(1667) → WAYPOINTS(2161) → タイプピッカー(2277) → VIA POINTS(2464) → VPメニュー(2584)
→ モバイルメニュー(2822) → GPS(2856) → なぞり描き(2897) → LONG PRESS(3242) → LINE DRAG(3259)
→ GEOMETRY(3333) → **POLYLINE(3501)** → OSRM(3651) → DISTANCE+TIME(3896) → WAYPOINT LIST(3967)
→ MODAL(4031) → HELP(4145) → IMAGE SAVE(4151) → 動作確認(4292) → 印刷用シート(4453)
→ MODE/UNDO/CLEAR(4591) → UNDO/REDO(4618) → VP→WP変換(4689) → 写真圧縮(4740) → 閲覧モード(4801)
→ 高低差(4921) → HELPERS

---

## 13. 不変条件とテストの対応

`footpath_regression.py`（**238項目**）が本書の条件を機械で見張っている。

| 本書の条件 | 対応する検査 |
|---|---|
| 4-1 表示専用のずらし | 実コース249点で自己交差≤1／往復なしは無変更／間隔が狭くならない／高ズームで地理基準が効く |
| 4-2 書き出しは自己完結 | 「保存後の本体に写真の実体が残らない」「参照から復元できる」 |
| 4-3 LSキー集約 | 「保存キーは LS に集約」「生キーの直書きが無い」 |
| 4-4 tooltip.update | 「ラベル位置再計算 tooltip.update を呼ぶ」 |
| 4-6 撮影後の後片付け | 「画像保存の後片付けが実行される」 |
| 4-7 共有リンクの安全 | 「同じ場所の.jsonだけ受け付ける」 |
| 4-8 版数の一致 | 「version.json と APP_VERSION が一致」 |
| 6章 経路サーバの待避 | 「止まったら予備へ切り替わる」「同時に投げすぎない」 |
| 9章 オフライン | ローカルHTTPを立て、実際に圏外にして「起動する」ことを確認（5項目） |
| 保存画像・印刷用シートの見た目 | 固定コースを描画し、基準画像と画素で比較（3項目・14章も参照） |

**新しい不変条件を作ったら、必ず検査も足す。** 足せない（＝機械で確かめられない）ものは、
そう明記して実機確認を促す。推測で「動きます」と言わない。

---

## 14. 見た目の比較検査（`tests/baseline/`）

固定コース（同じ座標・名前・種別・縮尺・**区間はすべて直線**）を描き、基準画像と画素で比べる。

- **地図タイルは比較しない**（提供元の絵が変わるため、検査時はタイル層を外す）。
- **経路サーバも使わない**（応答でルート形状が変わらないよう `fitBefore/fitAfter=false` で直線に固定）。
- 表示範囲は `_resetBounds()`→`_setAnchor()` で固定（地域名の検索結果に左右されない）。
- 撮る前に「**印が地図の中に入っているか**」を必ず確認する（空の基準画像を作らないため）。
- 文字の描かれ方はOSごとに違うので、**基準を作った環境（`tests/baseline/PLATFORM.txt`）でのみ比較**する。
- 意図して見た目を変えたときは、**基準画像を作り直し、内容を目視で確認してからコミットする**
  （`rm tests/baseline/*.png && npm test` で作り直せる）。

## 15. それでも機械で確かめられないこと

- 印刷した紙面の最終的な見え方（ブラウザの印刷）
- 実機のタッチ操作の感触、GPSの実挙動
- 印刷したQRの読み取りやすさ
- 地図タイル提供元の絵柄そのもの

これらは**実機確認が必要**。作業報告では必ずその旨を書く。

## 保存（v148→v170）
- 未保存フラグ `_dirty` を立てるのは `_markDirty()` だけ（`saveSnapshot()` と、スナップショットを取らない設定変更）。立てると `AUTOSAVE_MS` 後に `saveCourse({quiet:true})`。
- 保存できないとき（容量いっぱい）は `_saveState='error'` でボタンが赤くなり、`_dirty` は残る。閲覧中・コース名なし・`window.__noAutoSave`（検査）では予約しない。
- `_persistDerivedQuietly()`（道順・標高の静かな書き戻し）は `_dirty` が消えたあとにだけ働くので、自動保存と競合しない。

## 番号と種類（v155）
- `wp.type` は種類だけ（`spot`＝種類なし）。歩く順の番号は `_isNumbered(wp)`＝start/goal/node 以外で道順に入っている（`_onRouteOf`）もの。`courseNum` はその並び順。
- 印の中身は `_markInner(wp, px)`（S／G／数字／種類の絵 `TYPE_ICON`）。文字だけの場面は `_markTxt(wp)`。凡例・種類の選択は `_typeMarkHtml(type)`。
- 旧データの `type:'course'` は `_normType()` で `spot` に読み替える（`LEGACY_TYPE`）。保存は新しい名前で書く。

## 広域のすっきり表示（v159）
- `_declutter()`（zoomend・refreshIcons・表示切替から）：印を優先順に束ね（`_clusterN`／`_clusterHidden`）、調整点の表示を `_vpVisibleAt` で決める。`_clusterStickers` は同じ関数の旧名。
- `autoPlaceLabels()`：束ねて隠した印の名札は対象外。`_labelAllowedAt(wp, z)` は v168 から **`z >= DECL_LABEL_ALL_Z`（15）だけ**（種類・番号で分けない）。4方向に置けなくても隠さない（v168・一律）。表示の反映は `_syncLabelVis`。
- `_wpSize()` は `ZOOM_SCALE` の倍率を含む（v168：z17=1／z16=.8／z15=.65／z14=.55／.45）。番号の小丸・「+n」・シール（`_stickerSize`）・調整点（`_vpIcon`）・手描きの道の点も同じ `_zoomK()`。ズームの段が変わったら `refreshIcons()`（調整点も含む）＋全 `updateTooltip()`。

## まわりの施設の出どころ（v162）
- OpenStreetMap（Overpass）：`nwr["name"]` に除外条件を付けた1本の問い合わせ＋名前の無い実用物。種類分けは `_nbKindOf(tags)`。
- 国土数値情報：`data/ksj/index.json`（県コード・範囲・入っているデータ）→ `data/ksj/<pref>/<code>.json`（`items:[[lat,lng,name,sub],…]`）。`KSJ_KIND` で種類へ。変換は `tools/ksj_convert.py`。
- Wikipedia geosearch、名前検索時は Nominatim（bounded）。Google は使わない。
- **地理院地図Vector（国土地理院・v238）**：`GSI_VT_URL` の z16 タイル（Mapbox Vector Tile＝protobuf）を `_mvtParse` で自前解読（**外部ライブラリを増やさない**。点の記号と注記だけ・`symbol`／`label` レイヤのみ）。
  - `GSI_FT`＝地図記号（`ftCode 3231 神社` / `3232 寺院`。実地で OSM の shinto/buddhist と 30m 以内で一致することを確認済み）。名前は無いが**位置が正確**で、OSM に寺が 0 件の地域でも拾える。
  - `GSI_ANNO`＝注記の種類（`annoCtg`。661 神社／662・681 寺院／531・532 史跡／511 塔／534・870・820 公園／673 文化施設／880・881 役所／882 保健所／883 警察／884 消防／885 学校／886 病院／887 郵便局／888 会社／889 博物館／890 福祉／422 駅）。**地名（210・220・800）は施設ではないので採らない**。
  - 記号は `GSI_VT_LABEL_M`（150m）以内の**種類の合う注記**から名前をもらう。社と寺の取りちがえは `_nbSubNg` で止める。
  - タイルは 1 回 `GSI_VT_MAX_TILES`（12枚）まで。**出典「国土地理院『地理院地図Vector』」を説明に必ず入れる**（利用規約の条件）。z17 は空なので上げない。
- **Wikidata（CC0・v238）**：`WIKIDATA_SPARQL` に `wikibase:around`＋`VALUES ?type`（`WIKIDATA_TYPES`）。名前つきの社寺・城・博物館・公園・灯台。出典「Wikidata・CC0」。
- 候補の手直しは `_nbRefine`（v236→v238）：①祭り・行事を外す（`NEARBY_EVENT_RE`）②**出どころがあやふやなものだけ**種類を決め直す（`NEARBY_WEAK_TYPES`。国土数値情報の郵便局や地理院地図の注記は触らない）③名前の無い社寺は `NEARBY_NAME_M`（150m）以内の名前つきと**同じ場所とみなして 1 件にまとめる**。
- 種類の対応（v163）：`NEARBY_KINDS[].t` がこのアプリの種類。まわりの施設で拾える種類（飲食店・コンビニ・お店・神社・史跡・展望・公園・学校・公民館・病院・施設・トイレ・駐車場・バス停・地名・Wikipedia）は全部 `WT` に対応する種類がある。**取り込んだものを `other` に落とさない**（オーナー指示）。
- 名前から種類を見分ける `_guessType`／`NAME_TYPE_HINTS` は **v238 から「いちばん長く当てはまった言葉」が勝つ**（同じ長さなら表の上が勝つ）。「道の駅」＞「駅」、「ショッピングセンター」＞「センター」。**名前の途中で拾うと危ない語（山・川・岳）は `/山$/` のように終わりで見る**（山崎町・山崎インターチェンジが公園にならないように）。語を足すときはこの2点を守る。

## 画面を移るときの後片づけ（v239）
- **`_closeAllSheets()`**：画面を移るときに開いていた窓を全部閉じる。窓は増え続けるので**名前を並べない**——`close〜`／`hide〜` の引数なし関数を全部呼び、それでも残る `position:fixed` の `.show` を外す。`SHEET_KEEP` は閉じてはいけないもの（toast・更新バー・案内・圏外バッジ・`#s1`／`#s2`）。
  - **閉じる以外のこともする関数は `SHEET_CLOSE_SKIP` に入れる**（`closeA2hs`＝ホーム画面追加の案内を「見た」ことにする、`closeStartChooser`＝はじめかたを二度と出さなくする）。`close〜` を新しく作るときに副作用があるなら、必ずここに足すこと。
  - 呼ぶ場所：`_doBackToS1()`（一覧に戻る）・`newCourse()`・`loadCourseData()`（コースを開く）。
- **`_resetTools()`**：コースを開くたび、道具を「スポット」に戻し、閲覧モードを解除する（**共有リンクで開いたときだけ**`_viewParams().on` を見てそのまま）。
- 入力欄も持ち越さない：`openNewCourseSheet()` は名前・エリアを空に、`openNearbySheet()` は検索語を空にする。
- シートは `#s2` の中にあるので、一覧画面では「見えないだけ」で開いたまま残る。**閉じないとコースを開き直したときに出てくる**（v239 で直した不具合）。

## 閲覧モード（共有リンク）の後片づけ（v240）
- `initViewMode()` は `viewMode = true` に加えて **`body.viewonly`／`viewing`（埋め込みは `embed`）** を付ける。この class は編集の道具・保存・配る・**「✎ 編集モード」ボタン（`#mobileEditBack`）まで消す**。
- **付けたら外す場所が要る**。`_leaveShareView()`（`_doBackToS1()` の先頭で呼ぶ）が class を外し、`history.replaceState` で `#d=`／`#j=`／`?course=`／`?view=`／`?embed=` を URL から消す。
  - URL を消さないと `_viewParams().on` が真のままで、`_resetTools()` が「共有リンクで開いている最中」と誤判定し、**自分のコースを開いても閲覧モードから出られなくなる**（v240 で直した不具合）。
  - 共有リンクで開いている最中（`initViewMode()` → `loadCourseData()`）は `_viewParams().on` が真なので、閲覧モードのまま保たれる。

## 案内（チュートリアル）の段の進み方（v240）
- 画面が変わったときだけ切り替える（v235）。移り先は **その画面の「まだ通っていない次の段」**（`_gdNextFor(scr, _gdI + 1)`）。
  - **その画面の最初の段へ戻してはいけない**。地図→一覧で①まで巻き戻る（v240 で直した不具合）。
  - **うしろ方向へは自動で動かさない**＝行ったり来たりしない（v235 の不具合の再発防止）。
  - 例外は**窓**（`GD_BASE_SCR = ['list','map']` 以外＝ユーザーが自分で開いた窓）。窓は順番に関係なくその説明を出す。

## 案内（チュートリアル）の文は画面から読む（v239）
- GUIDE の `t`／`d`／`must` に**ボタン名を書き写さない**。`《b》` と書くと `_gdText()` がそのときの画面から実物の文字を読む。
  - `《b》`＝その段の `sel` が指すボタン／`《b:#id》`＝別のボタン／`《b|←》`＝文字が無い（絵だけの）ボタンや、まだ作られていない窓のボタンの言い方。
  - トーストは `_gdPlain()`（タグを外す）。
- **ボタンの文字を書き換えるコードを書かない**。`newCourse()` が `btn.textContent` で別名に変えていたため、案内と画面が食い違った（v239 で修正：`innerHTML` を控えて戻す）。読み込み中の表示など一時的に変えるときは、**必ず元の `innerHTML` を控えて戻す**こと。

## 印は勝手に動かない（v164）
- スポットの Leaflet マーカーは `draggable: wp.type === 'node'`。**node 以外を draggable にしない**（`_applyViewLock`／`_unlockAllMarkers` も node だけ戻す）。
- 動かす流れは `startMoveSpot()`（編集画面から）→ `_moveWp` にスポットを入れ、`#moveBar`・`#movePin`（画面の真ん中に固定した同じ印）を出し、元の印を薄くする → `onMapClick` の先頭で `_moveCommit(latlng)`、または「ここに置く」で `_moveHere()`（地図の中心）。置くときは `_snapCustom` → `saveSnapshot` → 座標更新 → `clearCache(); scheduleRouting()`。
- 途中でやめる入口：`_closeAllPopups`・`setMode`・`toggleViewMode`・Esc。新しい画面や道具を足すときは `_closeAllPopups()` を通せば自動的にやめる。

## はじめかた（v165）
- `#firstTip` は「3つの入口」。表示条件は `_syncStartChooser()` 1か所（スポット0・編集中・なぞり中でない・共有リンクでない・×で閉じていない）。`redrawList()` の先頭で呼ぶので、増減のたびに自動で出入りする。`_scDismissed` は `loadCourseData`／`newCourse` で戻す。
- まわりの施設はスポットが無いときも動く（`_nbAnchorBounds` と `_nbDistToCourse` が地図の中心へ落ちる）。

## 高低差のなぞりと勾配の色（v166）
- 標高の補間 `_elevAtD(dists, elevs, x)`、勾配 `_gradeAtD(dists, elevs, x)`（前後 `SCRUB_WIN_M` の平均）、位置つき `_elevPointAt(d)`（`_elevData._dists` にキャッシュ）。
- 帯と PC のグラフは描くたびに `_elevLayout.band/pc` に余白と幅を覚え、`_scrubAttach` の pointer イベントが x → 距離に直して `_scrubTo(d)`。描画関数の最後に `_scrubSvg` を足す（「いまここ」より上）。
- 面の色は `_gradeFills`（同じ色が続く区間は1つの path）。しきい値は `GRADE_MID`／`GRADE_STEEP`、色は `GRADE_COL` の1か所。

## 曲がり角（v167）
- `_tryRouter` が `steps=true` で取り、`co.cues = _cuesFromLegs(legs)` を座標配列に付けて返す。`getCachedRoute` のキャッシュ・ミス時だけ `_cueCache[key]` に入る（ヒット時は経路サーバを呼ばない＝v119 の不変条件）。
- 道順に沿った一覧は `_routeCues()`：今の道順の区間キー（`_routesInUse`）の曲がり角を `_lastRouteCoords` の最寄り頂点（`CUE_SNAP_M` 以内）に寄せ、`_routeCum` の累積距離で並べる。`_cueList` に（座標参照＋`_cueVer`）でキャッシュ。
- 出口は3つ：印刷用シート `_sheetCuesHtml`、歩く人の帯 `_nextCueInfo`（`renderNextBar` 内・分岐の案内が無いときだけ）、古いコース用 `fetchCuesNow`（編集画面のシートからだけ）。

## ルート調整（v169→v178）
- 調整点（`vps`）は**見えない・引きずれない**。案内（`vp.guide`）を付けた点だけ `_vpVisibleAt` が true。表示の反映は `_applyVpVis`。`viaVisible` は常に true のまま（手描きの道の点＝node の表示に使う）。
- 「ルート調整」（`mode==='via'`）では `_syncMapDrag()` が地図のドラッグを止める。地図の容器の `pointerdown` を `_initLineHold` が受け、`_nearRoute`（線から `LINE_HIT_PX` 以内）なら `_hold` を作る → 動いたら `_holdGrab` で点を作り（既にある点は `LINE_GRAB_PX` でつかむ）`_holdMove` で動かし、`_holdEnd` で `_snapCustom`→順序の取り直し→`clearCache(); scheduleRouting()`。動かさず `LINE_HOLD_MS` 押さえて離すと `showViaCtxMenu`。
- 当たり判定の線（`hitOverlays`）は `interactive:false`。旧 `onSegmentHitDown` は使っていない（残してある）。
- **順番（`order`）はつかんだ場所で決めて、引っぱった先で決め直さない**（v177）。`_vpPosAlong` は「今の道順」への射影なので、遠くへ動かした点で計算すると前後が入れ替わり、道順が行ったり来たりする。
- 引っぱり終わりに `_sweepOldVps(vp, grab)` が、つかんだ場所から引っぱった距離ぶん（`LINE_SWEEP_MIN_M`〜`LINE_SWEEP_MAX_M`）の中にある同じ区間の古い点を外す（案内付きは残す）。
- 広域（`z < ROUTE_SOLID_Z`）は `_routeDash()` が null、`_drawRouteBody` が切れ端と三角を作らない＝実線。

## 保存のきまり（v170）
- **自動保存はしない**。`_markDirty()` は `_dirty` を立てて保存ボタンの表示を変えるだけ。保存の入口は「保存」ボタン（`saveCourse()`）と `_askSaveBack()`（一覧に戻るとき）の2つだけ。
- `_persistDerivedQuietly()`（道順・標高のキャッシュ）は今までどおり `_dirty` が false のときだけ書く＝利用者の編集を勝手に保存はしない。

## 地図の描き直し（v173）
- `zoomend`／`moveend` は `_scheduleViewUpdate(zoomed)` だけを呼ぶ。実際の処理は `_applyViewUpdate` で 1 フレームに 1 回。**ここに処理を足すときは、拡大縮小のときだけ要るものか、動かしたときも要るものかを分けて入れる**。
- `_buildDisplayCoords` は `_dispMemo`（道順の配列・ズーム・線の太さ）で結果を使い回す。往復ずらしの中身を変えたら `_dispMemo = null;` を忘れない。

## 調整点の出し入れ（v178）
- `_vpEditing()`（`mode==='via'` かつ編集中）が true の間だけ、調整点が見えて `dragging` が有効になる。切り替えは `_syncVpEdit()`（`setMode` から呼ぶ）→ 各点の `_syncVpIcon` と `_applyVpVis`。
- 点を1つ作る道は `_makeVpOnRoute(lat, lng, snap)` の1本だけ（線のタップ `_viaTapAdd` と、線の引っぱり `_holdGrab` の両方がここを通る）。順番（`order`）はここで決めたものを後から変えない。

## 配るリンク（v184）
- 2通り：**リンクの中に入れる**（`#d=`／`#j=`・`_makeDataLink`／`_courseFromHash`・写真なし・保存先不要）と、**ファイルを置く**（`?course=ファイル名.json`・写真つき・QRコードはこちら）。
- `_viewParams()` が `location.hash` を見て `data` を返し、`initViewMode()` が最初に処理する。ハッシュはサーバに送られないので、静的配信でもそのまま動く。
- リンクに入れる中身は `_courseForLink()`（写真と stickers を外し `shared:true` を付ける）。長さの上限の目安は `LINK_DATA_MAX`。

## みんなのマップ（v185）
- サーバ無し。アプリと同じ場所の `library.json`（`LIBRARY_URL`）を `fetch` して並べるだけ。1件は `{name, area, by, at, d}` で、`d` は v184 のリンクの中身（写真なし・deflate＋base64url）。
- 開くときは `location.href = _shareBaseUrl() + '#d=' + d`＝配るリンクと同じ入口を通す（読み込みの道を1本にする）。
- 出すときは `_libHowTo()` が1行を組み立ててクリップボードへ入れ、`_ghEditUrl(LIBRARY_URL)`（GitHub の編集画面）を開く。人手で貼り付けて保存する運用。

## みんなの箱（v199→v200）＝ 誰でも・ボタンひとつ・すぐ反映
- **箱**＝合言葉のいらない共同の置き場。設定は `box.json`（`kind:'textdb'` 既定／`'firebase'`／`'off'`）。無ければ `BOX_DEFAULT`。
- 置き方は**中身と一覧を分ける**：中身＝`<箱の名前>-<ID>`（`{d:"配るリンクの中身"}`）、一覧＝`<箱の名前>`（`{courses:[{id,name,area,by,at,allowEdit}]}`）。一覧が小さいままなので毎回読める。
- 出す＝`_pubOut()` → `_boxPublish()`：**先に中身、あとで一覧**（一覧に載っている＝必ず開ける）。textdb は「読んで足して書き戻す」、firebase は行ごとに `PUT`（追記のみのルールが書ける）。
- 書き込みは `Content-Type: text/plain`（ブラウザの事前問い合わせを起こさない）。読み書きとも 12 秒で打ち切り。
- **箱は誰でも上書きできる**前提で作る：`_boxNorm()` が名前・長さ・重複を必ず通し、`LS.boxMine` に自分の投稿を控えて一覧から消えていたら戻す（自己修復）。
- **永久保存**：`.github/workflows/box_mirror.yml`（10分ごと）が `tools/box_mirror.py` を回し、箱→`library/box-<ID>.json` に写して箱から外す。写したあとはアプリが `boxId` で気づき、**保存先のぶんだけ**を出す（`_libLoad` の `moved`）。
- 不変条件：箱に出すのは**写真を外した配るリンクの中身**だけ（`_courseForLink`）。箱が落ちても `library/` に写ったぶんは残る。

## みんなのマップ（v185→v197）
- 一覧：`_libLoad()` が ① 保存先が GitHub Pages なら `_libScanDir()` で **`library/` と一番上の両方**を GitHub の一覧 API で読み、中身は同じ場所（`library/<名>.json` / `<名>.json`）から取る ② だめなら `library.json`（`{courses:[…]}`）。
  - 1 件の形は 2 通り：アプリが作った `{name, area, by, at, allowEdit, d}`（`d`＝配るリンクの中身）と、**「書き出す」で作ったコースのファイルそのもの**（`{name, wps:[…]}`。`file:'<保存先での道>'` を持ち、`?course=<道>` で開く＝写真も出る）。
  - `LIB_SKIP`＝一番上にある**コースでない `.json`**（`version.json`・`package.json` など）。読みにいかない。
  - `_safeCourseFile()` が受けるのは**同じ場所の `.json` だけ**：`library/` の 1 階層だけ許し、`..`・`/`・`\`・`: ? # % < > " | *`・先頭の `.` を弾く。ファイル名の日本語は可（v197）。
- 出す：`openPublishSheet()` →（名前・見た人にできること）→ `_pubGo()` が `_ghPutFile(path, text, message)` で **GitHub の contents API に PUT**（v193）。合言葉は `LS.ghToken`（この端末のみ）。GitHub の `/new/main?value=…` 方式は中身が大きいと GitHub 側がエラーになるので**使わない**。合言葉を使わない道は `_pubByFile()`（ファイル保存＋アップロード画面）とコピー。
- 「見るだけ」は `_courseForLink(course, {allowEdit:false})` が `noEdit:true` を入れる＝受け取った側の `_isLockedShare` が効く。

## ポイントの表示（v241）
- ボタンは2つで中身は同じ：スマホ `#mobilePtsBtn`（右の列）／PC `#btnPts`（右上）。どちらも `data-pts` を持ち、`_ptInit()`（`initMap` から）が `_ptBindHold` を付ける。**タップ＝`ptCycle()`、長押し（`PT_HOLD_MS`）・右クリック＝`openPtSheet()`**。長押しのあとに来る click は切り替えにしない（`held`）。
- 状態は2つ：`_ptLevel`（0=すべて／1=コースに入っているもの＝`_onRouteOf`／2=線だけ。**保存しない・コースを開くと `_resetTools` → `_ptReset` で 0**）と `_ptHideTypes`（種類ごとに隠す。**`LS.ptHideTypes` に端末ごと**）。見えるかどうかは `_ptShown(w)` の1か所で決める。
- **隠すのは2か所だけ**：`_declutter()` が束ねる前に `_ptShown` で外す（`show(w,false)`＝opacity 0・押せない・名札も隠す。隠した印は「+n」に数えない）／`_applyVpVis()` が「線だけ」のとき分岐・注意の案内の印を隠す（ルート調整中の点は道具なので出す）。反映は `_ptApply()`（`_declutter`＋名札の置き直し＋ボタンの見た目＋開いている画面）。
- **表示だけの約束**：この区画から `_markDirty`／`saveSnapshot`／`clearCache`／`scheduleRouting` を呼ばない（静的検査で見張る）。データ・道順・番号・当たり判定は変わらない。画像保存・印刷用シートの地図は画面と同じ見え方になる（`_captureMapCanvas` がトーストで知らせる）。
- 新しい印が見せ方のせいで見えないときは `_ptRevealNew(list)`（スポットを置く・まわりの施設の取り込み・調整点をスポットに・周回にする）。レベルのせいなら「すべて」に戻し、種類の設定のせいならそう言うだけ（設定は勝手に変えない）。**印を作る入口を足したら、ここも呼ぶこと。**
- 長押しで開いた直後は、指を離したときの「タップ」が開いたばかりの画面の外側に当たる。`_ptGuardUntil`（指を離すまで＋0.45秒）の間は外側を押しても閉じない。
- 印の `pointer-events` を戻すコード（`_setMarkersClickable(true)` など）は、`_clusterHidden` の印を押せる状態にしないこと（隠した印が見えないまま押せてしまう）。

## 並べ替えの画面（v241）
- 並べるのは `_roTargets()`＝**コースに入っているものだけ**（立ち寄り先・取り込んだ施設は道順に関係しない）。戻すのは `_roApplyOrder(from, to)`：**コース外の印の席はそのまま**、コースの印の席だけを新しい順で埋める。
- 見出し（題名＋「閉じる」）は `position:sticky; top:-8px`（窓の上の余白ぶん）で貼り付け、下まで流しても右上の隅に残る。ポイントの表示の画面は見出しを流れない側に置き、中身（`.pt-body`）だけが流れる。

## みんなのマップの写真（v242）
- 出す：`_sharePhotos()` が写真を 640px・画質0.6 に作り直す（1スポット最大 `PHOTO_MAX_PER_SPOT`・全部で `SHARE_PH_TOTAL` 字まで。入りきらない枚数は `over` で知らせる）→ `_phChunks()` で `SHARE_PH_CHUNK`（約70万字）ずつに分け → `_boxPublish()` が `<箱>-<ID>-ph`、`-ph1`、`-ph2`…に置く（1つずつ1回やり直す）。一覧の行の `ph` は**置けた数**（v202〜241 の 1/true は「1つ」）。`_boxNorm` はこの数を消さない。
- 見る：`_libOpenBox()` が `_boxPhUrls()` で全部の在りかを `_sharePhSet()` に渡し、開き直したあと `_applySharePhotos()` が同時に取って `_phMerge()` でつなぐ。保存先に写したコースは `ph` が `library/box-<ID>-photos.json`（1つにまとめたファイル）。
- 写す：アプリ（`_boxMirror`・作者の端末）も道具（`tools/box_mirror.py`・GitHub の定期実行）も、**分けて置いた全部を読めたときだけ**写す（1つでも欠けたら今回は写さない＝写真を落とさない）。写したら箱の写真は全部空にする。道具の `_url()` とアプリの `_boxUrl()` は**同じ場所を作ること**（v241 まで道具だけ写真の場所を作れず、写真が一度も写っていなかった）。
- 補う：`_backfill_photos()` が、`library/` にあって写真の無い `box-<ID>.json` に、箱に残っている写真を写す（調べたら `phChecked`）。
- 作者の端末（合言葉あり）から出したときも `_boxMirror([entry])` を通す（写真なしの写しを別に作らない）。
- 配るリンクの `icon` は実物（data URI）を入れる（`_makeDataLink`）。`idb:` のままだと他の端末では出ない。

## 重くしないための約束（v243）
- **`window.innerWidth` などの配置に関わる値をループの中で読まない**。読むとブラウザは画面の配置を計算し直す（直前に見た目を書き換えていると毎回）。`isMobile()` は1回の処理の間だけ答えを使い回す（`_isMobC`。`setTimeout(0)` と `resize` で捨てる）。新しく画面の大きさを使う関数を作るときも、ループの外で1回だけ求めること。
- **写真（data URI・数万〜数十万字）に `indexOf` を使わない**。先頭を見るなら `startsWith`。`_isPhotoRef` は印を描くたびに呼ばれる。
- **印1つの出来上がりごとに全部をやり直さない**。シールの出来上がりは `_declutterSoon()`（まとめて1回）。
- 測り方：`scratchpad` の `perf_local.py` のように、CPU を4倍遅くして（`Emulation.setCPUThrottlingRate`）コースを開き、50ms を超える処理（longtask）の最長と合計を見る。WebKit は longtask が無いので setInterval の止まりで測る。

## 閉じられない画面を作らない約束（v244）
- **新しい窓（`window.open`）で同じアプリの画面や写真を開かない**。ホーム画面から開いたアプリには「戻る」も「タブを閉じる」も無く、出られなくなる。写真は `openFullPhoto`（アプリの中の `#photoView`）、同じアプリの画面は `_openInApp(url)`（ホーム画面のアプリではその場で開く）。外のサイトはアプリ内ブラウザに「完了」があるので `window.open` でよい。
- **閉じるボタンはいつも見える所に置く**。中身が長い窓は、下のボタンの段を貼り付ける（`.fsh > .ds-row` などの sticky）か、上の右隅に「閉じる」を貼り付ける（並べ替え・ポイントの表示・リンクを作る・動作確認・新しいコース）。上端はノッチ（`--sat`）より下。
- **閉じる関数には名前を付ける**（`close〜`・引数なし）。画面を移るとき `_closeAllSheets()` が全部呼ぶので、名前が無い窓は残る（v244 のリンクを作る窓）。
- 新しい窓を足したら、`scratchpad/app/audit_close.py` の一覧に加えて点検する（回帰テストにも主な窓の押して閉じる検査がある）。

## 上の帯と右の列（v245）
- スマホの上の段は「戻る」だけ。保存・公開・現在地（追いかける）は右の列のアイコン（v247）。右の列は「戻る」と同じ高さ（`max(8px, var(--sat))`）から1列に並べる。ボタンを足すときは、横向きの低い画面（667×375・812×375：ホームバー21px）で下の棚に重ならないかを回帰テストの WebKit の検査で確かめる（足りなければ `max-height:380px` の決まりで見た目を小さくする。押せる範囲は .tap::after で 44px）。
- 保存の状態は `_setSaveState` が PC の上バー（文字）と右の列（名前＝aria-label・色）の両方に出す。右の列の保存の絵は書き換えない。
- 現在地はスマホでは「追いかける」（`toggleFollowMode`）だけ。PC は「現在地」（`gotoCurrentLocation`）。範囲外の知らせはどちらも出す。
- 閲覧モードの「次のスポット」の帯（`#nextBar`）は「戻る」と右の列の間に、左右同じすきまで真ん中に出す（v248。横向きは幅 440px まで `margin:0 auto`）。右の列は帯の下へ下げず、「戻る」と同じ高さから。スタンプはスマホでは右の列のアイコン（`#mobileStampBtn`・v249）で、札 `#stampBar` は PC だけ（右下）。
- 横向き（`orientation: landscape and max-height: 500px`）も帯は「戻る」と右の列の間の真ん中。幅の広い横向きでは PC 向けの `#nextBar`（左上・幅 380px）が効くので、横向きの区画で必ず上書きする。
- 上に固定する部品を足したら、帯と重ならないか回帰テストの WebKit の検査（縦・狭い横向き・広い横向き）で確かめる。

## ノッチ（ステータスバー）の下（v161・v245）
- 地図はノッチの下まで出す（`viewport-fit=cover`＋`black-translucent`）。押す部品は `--sat` ぶん下げる。**ノッチ部分を無地の帯で塗って隠さない**（オーナー指示。v161 と v245 で2回言われている）。
- `--sat0`＝ノッチそのものの高さ（`env(safe-area-inset-top)`）。`--sat`＝押す部品を置き始める高さ＝ノッチ＋36pt・少なくとも 98pt（ノッチが無ければ 0）。iOS 27 のぼかし（上から約 95pt）にかからないため（v246）。上に固定する部品を足すときは必ず `--sat` を使う。ページの大きさの計算には `--sat0` を使う。
- iOS 27 のホーム画面のアプリでは、ノッチの下（上から約 100pt）に iOS がぼかしを重ねる。ページから消す設定は無い（WebKit `WKWebView _shouldHideTopScrollPocket`：上の帯の色で置き換えて消せるのは、ページがノッチの下に描いていないときだけ）。ぼかしの色はページの地の色（`html,body` の background）に寄る。

## スタンプラリー（v100→v250）
- 押す仕組み：閲覧モードで位置が入ったとき（➤ 追いかける）、`VISIT_RADIUS_M`（10m・v251）以内の**コースに含まれるスポット**（`_courseSpots()`＝S・番号・G）に記録（`_visits`・この端末の `LS.visits` だけ）。次のスポット・到着・カードのフリックも `_courseSpots()`。作る人の画面で全部のスポットが要るところは `_allSpots()`。
- 見せ方（v250）：スタンプの絵は `_stampSvg`（枠 `STAMP_FRAMES`×色 `STAMP_INKS` を歩く順で回す・真ん中は `_stampKanji`）。押した瞬間 `_stampFx`（順番待ち `_stampFxQ`）、全部そろったら最後のあとに `_stampDoneFx`（完歩之印 `_stampSealSvg`・紙吹雪）。スタンプ帳 `openStampSheet`。記念の1枚は `_goalSeal`。
- 演出は `.st-fx`／`.st-done` を body に足して出す（`close〜` 関数があるので画面を移ると消える）。検査で `_checkVisits` を呼んだら、後の検査の画面を覆わないよう `closeStampFx()`・`closeStampDone()` で片づける。

## わたしの写真（v253）
- 歩いた人の写真は `LS.myPhotos`（{コースのキー: [{id, wp, at, nm, cv?, put?}]}。キーは `_myKey()`＝コースID、無ければ 'n:'+コース名）に一覧、写真そのものは IndexedDB（`id`＝長辺1600、`'mt:'+id`＝小さい見本360）。`gcPhotos` は両方を残す。
- 入れる：`myCam(wpId, pick)` → 隠した input（`#myCam` は capture／`#myPick` は multiple）→ `_myAdd` → `compressImageTo` → `_myAddData(full, wpId, quiet)`。検査は `_myAddData` を直接呼ぶ。input の `click()` は押したその場で呼ぶ（あとから呼ぶと iPhone は開かない）。
- 見る：カード `_myCardHtml`、スタンプ帳の枠 `.sb-myph`、アルバム `openMyAlbum`、全画面 `openMyStory(i)`（`_myStoryShow`・`_myStoryTick`（rAF）・`_myStoryPause`・`_myStoryGo`）。保存 `_myStorySave`（`navigator.share({files})`、できなければダウンロード）、消す `_myStoryDel`。
- カードの写真の入れ替え：`_vipCoverPick` → `#myCover` → `_vipCoverAdd`／全画面の `_myStoryCover`。歩く人（`body.viewonly`）は印 `cv`（`_myCoverOf`）でカードに出すだけ（コースのデータは変えない）。自分のコースは `_vipCoverCourse` で `wp.photos` の先頭に入れる（前の写真は残す。写真は `restoreSnapshot` の対象外＝取り消しで戻らないので、消さない）。
- `compressImage(file)` は引数1つのまま（`toAdd.map(compressImage)` から呼ばれる。引数を足すと map の番号が大きさになる）。大きさを選ぶのは `compressImageTo(file, px, q)`。
- `.tap{position:relative}` は CSS の後ろの方にある。`.tap` を付けた部品を `position:absolute` にするときは選び方を強くする（例 `.vip-photos .vip-more`）。

## スポットの解説を名前から探す（v252）
- `_descLookup(名前, 緯度, 経度, force)` → `_descFind`：ウィキペディアの地理検索（`_descGeoList`・約5km四方ごとに1回）で名前が同じ近くの記事 → 名前で検索（同じ名前で、座標が `DESC_NEAR_M` 以内か本文に `_descAreaWords()` の市町村名）→ ウィキデータ（座標が近いもの）。ネットは `_descGet` の1か所（検査で差し替える）。
- 説明の扱いは `_descKind`（empty／note＝取り込みのメモ「（情報：…）」／own＝書いてある説明）と `_descMerge`。own は上書きしない。
- まとめて入れるのは `descFillAll(manual)`。自動は `_descDoneGet/_descDoneSet`（コース・スポット・名前ごとに1回）。結果は `LS.descCache` に覚える。
- v254：`_descFind` の順は ①地理検索の近い同じ名前の記事 ②同じ名前の記事（近い／本文に市町村名）③文化遺産オンライン（`DESC_JPS`＝ジャパンサーチ・`database === 'bunka'`・3km 以内・`DESC_MAIN_RE` で主屋などを先に・解説文は CC BY）④ウィキデータ ⑤ウィキペディアの本文の文（`_descSentences`・`_descSentenceOk`＝一覧の1行は使わない）。
- `_descAreaWords` は都道府県を除く（県の名前だけでは確かめない）。`_descFreshNote` は名前を付けた地理院の記号の古いメモを直す。`DESC_VER` を覚えた結果の鍵と「自動で探した」印に入れる（探し方を変えたら上げる）。
- v255：説明の種類に `found`（名前から探して入れた解説＝出典の行 `DESC_SRC_RE` がある）を足した。まとめて探す `descFillAll` は empty／note だけを探し、found と own は飛ばす。重なった解説は `_descDedupe`、探し直すときは `_descStripFound` で外してから入れる。`descFillAll` は `DESC_WORKERS`（2）並べて、コースのスポット（`_stampOrder`）から先に探し、`_descProg` で「n / m」を出す（`#toastBox` の `.toast.sticky`＝数えず消さない）。閲覧モードでは止めない（コースを替えたら止める）。
- v256：地域の解説集 `data/desc/`（`DESC_LOCAL_INDEX`＝県ごとの範囲 → 県のファイル）。`_descFind` の最初（⓪）に `_descLocal` で読み、名前（`aka` も）が同じで `DESC_LOCAL_M`（300m）以内のものを使う。出典の行は「（出典：地域の解説集（src））」で `DESC_SRC_RE` に含める。地理院の記号のメモ（`DESC_GSI_NOTE_RE`）に解説を入れるときは種類の1行を外す。項目を足すときは、確かめた事実だけを自分の言葉で書き、src・u・at を必ず付ける（静的検査が見る）。
- 新しい版の確認 `watchVersion` は起動時に加えて、`visibilitychange`（表に戻った）・`pageshow`（persisted）でも `_watchVersionSoon` から呼ぶ（`UPD_RECHECK_MS`＝5分に1回まで）。
- 正規表現の後ろ読み（`(?<=`・`(?<!`）は使わない。古い iPhone（iOS 16.3 まで）ではインラインの JS 全体が読み込めず、アプリが動かなくなる（静的検査あり）。

