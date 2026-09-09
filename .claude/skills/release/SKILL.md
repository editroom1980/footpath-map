---
name: release
description: フットパスマップメーカーを1版出荷する手順。index.html / sw.js を変更したとき、「リリースして」「公開して」「版を上げて」「push して」と言われたとき、または新機能・不具合修正を実装し終えたときに使う。版数の同期漏れ・テスト漏れ・引き継ぎ書の更新漏れを防ぐ。
---

# 出荷手順（1版 = 1機能または1不具合修正）

オーナーは非プログラマ。最優先は「**不具合を出さない・常に元に戻せる・検証できないことはしない**」。
この順番どおりに実施し、1つでも詰まったら止めて報告する。

## 1. 実装
- 差分は最小。定数は先頭の CONSTANTS に集約、状態は STATE 区画に用途コメント付きで追加。
- 触ると壊れやすい場所は `CLAUDE.md` を参照（特に `_buildDisplayCoords` は**表示専用**。
  `_lastRouteCoords`・`hitOverlays`・高低差・保存データを変えない）。

## 2. 版数を3か所そろえる（v92 以降は3か所ある）
```bash
grep -n "const APP_VERSION" index.html   # 'vNN' を1つ上げる
cat version.json                          # {"version":"vNN"} を同じ値に
grep '"version"' package.json             # 0.NN.0 に合わせる
```
**version.json のずれは利用者に「更新のお知らせ」を誤表示させる。** 回帰テストが一致を検査する。

## 3. 静的チェック
```bash
node -e "const fs=require('fs');const s=fs.readFileSync('index.html','utf8');const b=[...s.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]);new (require('vm').Script)(b.join('\n;\n'));console.log('JS構文OK')"
node --check sw.js
grep -c cdnjs index.html      # 4（leaflet css/js・html2canvas・qrcodejs）以外なら理由を説明する
grep -c "file:///" index.html # 0 であること
```

## 4. 回帰テスト（1項目でも FAIL なら出荷しない）
```bash
npm test
```
- 新機能を足したら**検査も足す**（`chk('静的'|'機能'|'オフライン', 説明, 条件, 詳細)`）。
- 非同期にした関数（`saveCourse` 等）は、テスト側も `await` に直す。
- オフライン検査はローカルHTTPを立てて実際に圏外にして確かめている。時間がかかっても待つ。

## 4-2. 見た目を変えたときは基準画像を作り直す
`tests/baseline/*.png` と画素で比べているため、**意図して見た目を変えた版では比較が不合格になる**。
```bash
rm tests/baseline/map_image.png tests/baseline/print_sheet.png && npm test
```
作り直したら**必ず画像を開いて目視確認**し、正しい見た目であることを確かめてからコミットする。
確認せずに作り直すと「壊れた見た目」が新しい基準になってしまう。

## 5. 実際に動かして確かめる
ローカル配信（`npm run serve` → http://localhost:8080/）を開き、
**変更した機能そのもの**を操作して確認する。テストが通っただけで「動く」と言わない。

## 6. 引き継ぎ書を更新
`HANDOFF_開発引き継ぎ書.md` の
- 冒頭の版数、「2. 現在の状態（vNN 実装済み）」、テスト項目数
- 「9. 変更履歴」に **何を・なぜ**（症状→原因→対処の順で）
- 解決した課題は「10. 未対応」で取り消し線にする

## 7. コミット（1版1コミット）
メッセージは日本語で、版数・変更点・**検証した内容**を書く。末尾に
`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`

## 8. 公開（オーナーの指示があるときだけ）
```bash
git push origin main
```
GitHub Pages は push で自動更新。1〜2分待って確認する：
```bash
curl -s https://editroom1980.github.io/footpath-map/index.html | grep -o "const APP_VERSION = '[^']*'"
curl -s https://editroom1980.github.io/footpath-map/version.json
```
v92 以降、利用者側の `?v=` 書き換えは不要（アプリが新版を検知して案内する）。

## 検証できないこと（正直に申告する）
- 保存画像・印刷紙面の最終的な見え方（html2canvas / ブラウザの印刷）
- 実機のタッチ操作の感触、GPSの実挙動、QRの印刷後の読み取りやすさ
これらは「確認していません。実機でお願いします」と明記する。**推測で「動きます」と言わない。**
