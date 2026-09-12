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
  customPaths:[{id,pts:[[lat,lng],…]}],      // 細道（手描きの道）
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
  // 周辺の情報（v144）は OpenStreetMap（Overpass）と Wikipedia だけ。Google Places/Maps の情報は規約で使えない（載せない・取りに行かない）
  // 発見（v143）はコースの保存データには入らない。端末の LS.finds = { [courseId]: [{id, lat, lng, word, by, at, photos[]}] }。送るファイルは {fpFinds:1, courseId, courseName, finds:[…写真は実体]}
  maxWpId, maxVpNum, savedAt, version }
```

### 消える前に知らせるための記録（コースとは別・端末ごと、v121）
`LS.backupAt`（最後に「すべて書き出す」をした日時）／`LS.saveCount`（その後の保存回数）／`LS.firstSaveAt`（最初の保存）。
`renderCourseList()` のたびに `backupStatus()` で 30日＝黄・60日＝赤 を判定して一覧に出す。
**保存の入口を足したら `_noteSaved()`、書き出しの入口を足したら `_noteBackup()` を呼ぶこと。**

### 写真の持ち方（v89以降）
- ブラウザ内の保存では `photos:['idb:p123abc', …]` の**参照**だけを持つ。実体は IndexedDB。
- **書き出し（JSON・配布リンク・バックアップ）では実体（data URI）を埋め込み直す**。
  → 配ったファイルは**1つで完結**する。この性質は絶対に壊さない。
- 表示は `_photoAttr()` で `data-photo` 属性にし、`_fillPhotoImgs()` が後から実体を流し込む。

### 保存先の分担
| 置き場所 | 何を | 備考 |
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

16. **画面の語と内部名は別**（v130）。画面は「スポット／通り道の点／自分で描いた道／指でなぞって描く／道に沿わせない／
    描いた道に吸い付く／歩く人の見え方」、コードと保存データは `wps/vps/customRoads/draw/manualMode/_snapOn_/viewMode` のまま。
    文言を足すときは画面の語を使い、内部名・キーは変えない（対応表は HANDOFF 2章）。
15. **種別の選び方は select（隠す）＋チップ**（v128）。`saveModal` は `#mType.value` を読むだけ、`_buildTypeOptions(wp)` が
    選べる種類を select に入れ、`_renderTypeChips()` はそれを読んで描く。種類の制限（スタート／ゴールは両端だけ）を
    足すときは `_buildTypeOptions` だけ直す。地図タップは `addWp(…,'course')` で即置く（選択画面を戻さない）。
14. **PCの道具は3群で、id は据え置き**（v126）。左の縦の道具＝`#tbar`（`btnWp/btnVia/btnUndo/btnRedo`）、右上＝`#pcTr`
    （`btnBaseMap`→`#popMap`、`btnLegend`→`#popLegend`）、下＝`#pcBl`（`btnElev`）、上バー＝`#hdr`（`btnView/btnMore`→`#popMore`）。
    どれも `#mapWrap` の上に浮かせているだけで、`#map` の外なので保存画像には写らない。状態の反映は `_syncPcPops()`
    が変数から描き直す（ボタンの見た目を直接いじらない）。閲覧中・配布リンク・埋め込み・スマホで隠す規則は `#tbar/#pcHint/#pcTr/#pcBl` を見る。
13. **「配る」の出口は `shareExit()` の呼び分けだけ**（v123）。画像・配布シート・リンク・GPX の中身を `#shareSheet` 側に
    複製しない。出口を足すときは `.ss-card` を1枚増やして `shareExit` に1行足す。「この地図に載る情報」は `renderShareInfo()`
    が開くたびに実データから数える（保存しない）。
12. **文字の無いボタンには必ず `aria-label`**（v122）。読み上げで「ボタン」としか聞こえないのを防ぐ。JSで作る雛形も同じ。
    検査が HTML・雛形・実画面の3か所で数えるので、付け忘れると落ちる。**ページ全体の拡大は止める**（v135・`user-scalable=no`
    ＋ `touch-action:manipulation`）。v122 で一度許したが、iPhone のホーム画面アプリで地図の外を二本指で触るとページごと拡大され、
    固定の帯やボタンが画面の外へ出た（オーナー報告）。文字の大きさはアプリ内の設定で変える。地図は `#map{touch-action:none}` で
    ピンチを Leaflet に渡す。
11. **閲覧中（`viewMode`）は編集の操作を一切受け付けない**（v120）。見た目は `body.viewing`（配布リンクは `body.viewonly` も）で
    隠し、動きは `onMapClick`／`openModal`／`undoLast`／`redoAction`／`clearAll`／一覧のドラッグの `if (viewMode) return;` と
    `_applyViewLock()`（印の `dragging.disable()`）で止める。**編集の入口を足したら、この門も足すこと。**
10. **配布リンク・保存データを開くとき、経路サーバも標高サーバも呼ばない**（v119・v127）。`routes` を `segCache` に、`elevs` を `elevCache` に戻してから
    道なり計算に入るので、計算はすべてキャッシュに当たる。**直線に逃げた結果（`fallback`）は覚えない・保存しない**
    （保存すると、サーバ復旧後も直線のまま固まる）。区間のキーは `_segKey()` の1か所で作る。
9. **スポットの色は `WT` の1か所だけ**。`.wp-tt-<種別>` のCSSは起動時に `_injectWpStyles()` が
   WTから作り、画像保存の色も WT から引く。**CSSや画像保存側に色を直書きしない**
   （v98以前は3か所に同じ色が書かれ、ビュースポットと駐車場が同色になっていた）。

---

## 5. 描画パイプライン（最重要）

```
スポット/調整点
   ↓ buildRoutedCoords()            区間ごとに 細道→OSRM→直線 の順で座標を作る
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
  置き場所と向きは**線に沿った距離**で決める（隣り合う点の角度で決めると、点が細かい
  OSRMのルートでは判定できない）。**スポットの○に近い位置は飛ばす**（○の下に入ると見えない）。
  表示専用の約束は `routeCasing` と同じ。
  経緯：v108 まばらな矢印 → v109 矢印の連なり → v110 取り下げ → v111 曲がり角だけ → v112 一定間隔。
  線に重ねる印は**塗りつぶした三角**が細い線の「>」より読みやすい。

- 当たり判定（`hitOverlays`）は**素の座標**で作る。ずらした線で作ると区間の取り違えが起きる。
- ズームを変えると見かけの間隔が変わるため、`zoomend` で表示座標だけ作り直す。

---

## 6. ルーティング

区間（スポット→スポット、間に調整点があればその区切り）ごとに、次の順で座標を決める：

1. **細道**（手描きの道）が有効で、その区間に沿えるなら細道を使う
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
配布リンクで歩く人の記録。**閲覧モードのときだけ**働く（作る人の画面を汚さない）。
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
（`_totalAscent()` が null なら `courseDifficulty()` も null）。サイドバーと配布シートに表示。
`_elevData` は**ルートを計算し直すたびに消える**ので、難易度も自然に出たり消えたりする。

---

## 8. 配布のしくみ

| 手段 | 実装 | 備考 |
|---|---|---|
| 配布リンク | `?course=ファイル名.json` | 同じ場所に置いたJSONを読み、**閲覧専用**で表示。見る人の端末には保存しない |
| 確認用リンク | `?view=<コースID>` | 自分の端末のみ（localStorage 参照） |
| 埋め込み | `?course=…&embed=1` | `body.embed` でヘッダ・サイドバー・編集UIを全部隠し、地図＋帯だけにする。帯には コース名・距離・「大きな地図で開く」（`embed` を外したURL） |
| 配る | `openShareSheet()` | 4つの出口（画像・配布シート・リンク・GPX）と「載る情報」を1枚に。出口は `shareExit()` が既存関数を呼ぶだけ（v123） |
| 配布シート | `openPrintSheet()` | 地図画像＋凡例・縮尺・方位・見どころ・スポット一覧・QR。`@media print` で **A4横**に印刷 |
| QRコード | `LS.shareLinks` に覚えた配布リンクを描画 | ライブラリが無ければQR欄ごと出さない |
| GPX 書き出し | `buildGpx()` | GPX1.1。`<trk>` は**実データ** `_lastRouteCoords`。なぞり端点(node)は除外 |
| GPX 読み込み | `parseGpx()` | `<wpt>`→スポット（`<type>` から種別も復元）。**`<wpt>` があるときは軌跡を取り込まない**（スポットからのルートと二重になり距離が約3倍に狂うため）。`<wpt>` が無い（歩いた記録）ときだけ、始点/終点をスタート・ゴールにし軌跡を細道にする |
| バックアップ | `buildBackupData()` / `applyBackupData()` | 復元は同IDを上書き・無いものを追加（二重に増えない） |

閲覧専用のときは `body.viewonly` で編集UIを隠す（ツールバー・保存ボタン・並替ヒント・モバイルの編集シェルフ）。

> **GPXの限界**：GPXには**調整点(VP)を表す仕組みが無い**ため、書き出して読み戻すと**道順は引き直しになる**
> （実測：調整点17個のコースが 2.36km → 7.43km）。取り込み時にその旨を明示している。
> 道順をそのまま残す用途では **JSON** を使う。

> **細道(customPaths)はコース単位ではなくアプリ全体で共有**（`LS.custompaths`）。
> `loadCourseData()` はコースに細道が入っているときだけ上書きし、空なら現状維持＝消さない。

---

## 9. オフライン（`sw.js`）

配布リンクを開いた端末では、`_autoOfflineForLink()`（v135）がコース範囲のタイルを自動で持ち歩く（回線の種類・節約モード・埋め込みで見送り、コースごとに1回、`?offauto=0` で無効）。手動の「地図を持ち歩く」（`saveMapOffline`）はそのまま。

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
→ 細道(1667) → WAYPOINTS(2161) → タイプピッカー(2277) → VIA POINTS(2464) → VPメニュー(2584)
→ モバイルメニュー(2822) → GPS(2856) → なぞり描き(2897) → LONG PRESS(3242) → LINE DRAG(3259)
→ GEOMETRY(3333) → **POLYLINE(3501)** → OSRM(3651) → DISTANCE+TIME(3896) → WAYPOINT LIST(3967)
→ MODAL(4031) → HELP(4145) → IMAGE SAVE(4151) → 動作確認(4292) → 配布シート(4453)
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
| 4-7 配布リンクの安全 | 「同じ場所の.jsonだけ受け付ける」 |
| 4-8 版数の一致 | 「version.json と APP_VERSION が一致」 |
| 6章 経路サーバの待避 | 「止まったら予備へ切り替わる」「同時に投げすぎない」 |
| 9章 オフライン | ローカルHTTPを立て、実際に圏外にして「起動する」ことを確認（5項目） |
| 保存画像・配布シートの見た目 | 固定コースを描画し、基準画像と画素で比較（3項目・14章も参照） |

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
- `_declutter()`（zoomend・refreshIcons・表示切替から）：印を優先順に束ね（`_clusterN`／`_clusterHidden`）、通り道の点の表示を `_vpVisibleAt` で決める。`_clusterStickers` は同じ関数の旧名。
- `autoPlaceLabels()`：束ねて隠した印の名札は対象外。`_labelAllowedAt(wp, z)` は v168 から **`z >= DECL_LABEL_ALL_Z`（15）だけ**（種類・番号で分けない）。4方向に置けなくても隠さない（v168・一律）。表示の反映は `_syncLabelVis`。
- `_wpSize()` は `ZOOM_SCALE` の倍率を含む（v168：z17=1／z16=.8／z15=.65／z14=.55／.45）。番号の小丸・「+n」・シール（`_stickerSize`）・通り道の点（`_vpIcon`）・描いた道の点も同じ `_zoomK()`。ズームの段が変わったら `refreshIcons()`（通り道の点も含む）＋全 `updateTooltip()`。

## 周辺の情報の出どころ（v162）
- OpenStreetMap（Overpass）：`nwr["name"]` に除外条件を付けた1本の問い合わせ＋名前の無い実用物。種類分けは `_nbKindOf(tags)`。
- 国土数値情報：`data/ksj/index.json`（県コード・範囲・入っているデータ）→ `data/ksj/<pref>/<code>.json`（`items:[[lat,lng,name,sub],…]`）。`KSJ_KIND` で種類へ。変換は `tools/ksj_convert.py`。
- Wikipedia geosearch、名前検索時は Nominatim（bounded）。Google は使わない。
- 種類の対応（v163）：`NEARBY_KINDS[].t` がこのアプリの種類。周辺の情報で拾える種類（お店・神社・史跡・展望・公園・学校・公民館・病院・施設・トイレ・駐車場・バス停・地名・Wikipedia）は全部 `WT` に対応する種類がある。**取り込んだものを `other` に落とさない**（オーナー指示）。名前から種類を推定する `NAME_TYPE_HINTS` は先勝ちなので、「病院」（院＝寺院より先）「道の駅」（駅＝バス停より先）の順序に注意。

## 印は勝手に動かない（v164）
- スポットの Leaflet マーカーは `draggable: wp.type === 'node'`。**node 以外を draggable にしない**（`_applyViewLock`／`_unlockAllMarkers` も node だけ戻す）。
- 動かす流れは `startMoveSpot()`（編集画面から）→ `_moveWp` にスポットを入れ、`#moveBar`・`#movePin`（画面の真ん中に固定した同じ印）を出し、元の印を薄くする → `onMapClick` の先頭で `_moveCommit(latlng)`、または「ここに置く」で `_moveHere()`（地図の中心）。置くときは `_snapCustom` → `saveSnapshot` → 座標更新 → `clearCache(); scheduleRouting()`。
- 途中でやめる入口：`_closeAllPopups`・`setMode`・`toggleViewMode`・Esc。新しい画面や道具を足すときは `_closeAllPopups()` を通せば自動的にやめる。

## はじめかた（v165）
- `#firstTip` は「3つの入口」。表示条件は `_syncStartChooser()` 1か所（スポット0・編集中・なぞり中でない・配布リンクでない・×で閉じていない）。`redrawList()` の先頭で呼ぶので、増減のたびに自動で出入りする。`_scDismissed` は `loadCourseData`／`newCourse` で戻す。
- 周辺の情報はスポットが無いときも動く（`_nbAnchorBounds` と `_nbDistToCourse` が地図の中心へ落ちる）。

## 高低差のなぞりと勾配の色（v166）
- 標高の補間 `_elevAtD(dists, elevs, x)`、勾配 `_gradeAtD(dists, elevs, x)`（前後 `SCRUB_WIN_M` の平均）、位置つき `_elevPointAt(d)`（`_elevData._dists` にキャッシュ）。
- 帯と PC のグラフは描くたびに `_elevLayout.band/pc` に余白と幅を覚え、`_scrubAttach` の pointer イベントが x → 距離に直して `_scrubTo(d)`。描画関数の最後に `_scrubSvg` を足す（「いまここ」より上）。
- 面の色は `_gradeFills`（同じ色が続く区間は1つの path）。しきい値は `GRADE_MID`／`GRADE_STEEP`、色は `GRADE_COL` の1か所。

## 曲がり角（v167）
- `_tryRouter` が `steps=true` で取り、`co.cues = _cuesFromLegs(legs)` を座標配列に付けて返す。`getCachedRoute` のキャッシュ・ミス時だけ `_cueCache[key]` に入る（ヒット時は経路サーバを呼ばない＝v119 の不変条件）。
- 道順に沿った一覧は `_routeCues()`：今の道順の区間キー（`_routesInUse`）の曲がり角を `_lastRouteCoords` の最寄り頂点（`CUE_SNAP_M` 以内）に寄せ、`_routeCum` の累積距離で並べる。`_cueList` に（座標参照＋`_cueVer`）でキャッシュ。
- 出口は3つ：配布シート `_sheetCuesHtml`、歩く人の帯 `_nextCueInfo`（`renderNextBar` 内・分岐の案内が無いときだけ）、古いコース用 `fetchCuesNow`（編集画面のシートからだけ）。

## 道を変更（v169→v178）
- 通り道の点（`vps`）は**見えない・引きずれない**。案内（`vp.guide`）を付けた点だけ `_vpVisibleAt` が true。表示の反映は `_applyVpVis`。`viaVisible` は常に true のまま（描いた道の点＝node の表示に使う）。
- 「道を変更」（`mode==='via'`）では `_syncMapDrag()` が地図のドラッグを止める。地図の容器の `pointerdown` を `_initLineHold` が受け、`_nearRoute`（線から `LINE_HIT_PX` 以内）なら `_hold` を作る → 動いたら `_holdGrab` で点を作り（既にある点は `LINE_GRAB_PX` でつかむ）`_holdMove` で動かし、`_holdEnd` で `_snapCustom`→順序の取り直し→`clearCache(); scheduleRouting()`。動かさず `LINE_HOLD_MS` 押さえて離すと `showViaCtxMenu`。
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

## 変更点の出し入れ（v178）
- `_vpEditing()`（`mode==='via'` かつ編集中）が true の間だけ、通り道の点が見えて `dragging` が有効になる。切り替えは `_syncVpEdit()`（`setMode` から呼ぶ）→ 各点の `_syncVpIcon` と `_applyVpVis`。
- 点を1つ作る道は `_makeVpOnRoute(lat, lng, snap)` の1本だけ（線のタップ `_viaTapAdd` と、線の引っぱり `_holdGrab` の両方がここを通る）。順番（`order`）はここで決めたものを後から変えない。

## 配るリンク（v184）
- 2通り：**リンクの中に入れる**（`#d=`／`#j=`・`_makeDataLink`／`_courseFromHash`・写真なし・置き場所不要）と、**ファイルを置く**（`?course=ファイル名.json`・写真つき・QRコードはこちら）。
- `_viewParams()` が `location.hash` を見て `data` を返し、`initViewMode()` が最初に処理する。ハッシュはサーバに送られないので、静的配信でもそのまま動く。
- リンクに入れる中身は `_courseForLink()`（写真と stickers を外し `shared:true` を付ける）。長さの上限の目安は `LINK_DATA_MAX`。
