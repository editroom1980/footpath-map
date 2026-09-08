# CLAUDE.md — フットパスマップメーカー 作業規約

このファイルは Claude Code が自動で読み込みます。**作業前に必ず本ファイルと `HANDOFF_開発引き継ぎ書.md`・`ARCHITECTURE.md` を読むこと。**
オーナーは非プログラマです。**応答は日本語・簡潔・結論から。**

## プロジェクト
- フットパス（歩くコース）設計 Web アプリ。実体は **単一ファイル `index.html`**（HTML+CSS+インライン JS）。
- 外部依存は CDN の Leaflet 1.9.4 と html2canvas 1.4.1 のみ。GitHub Pages で配信（`https://editroom1980.github.io/footpath-map/`）。

## 最優先の原則
**「不具合を出さない・常に元に戻せる・検証できないことはしない」。** これに反する変更はしない。

## 絶対に守るルール
1. **勝手に push / デプロイしない。** 変更はブランチにコミットするに留め、**本番反映（main への反映）はオーナーの明示的な指示があるまで行わない**。GitHub Pages は push で即公開されるため。
2. **出荷前に回帰テストを全 PASS させる**（`npm test`）。1 項目でも FAIL なら出さない。新機能を足したら**テストも足す**。
3. **出力は CDN 版のまま**：`index.html` に `file://` パスや `leaflet-rotate` を混ぜない（ローカル検証用の差し替えはテスト時のみ・コミットしない）。
4. 変更ごとに **`APP_VERSION` を1つ上げる**。オーナーは公開後に URL の `?v=N` を同じ値へ上げてキャッシュ更新する。
5. **差分は最小**。定数は先頭の CONSTANTS に集約。状態は STATE 区画にまとめ用途コメントを付ける。
6. 検証できない箇所（html2canvas の保存画像、実機タッチ感）は**正直に申告し、実機確認を促す**。データ・スコア・URL を捏造しない。

## セットアップ（初回のみ）
```bash
npm install                 # devDeps: leaflet, html2canvas（file:// テスト用）
pip install playwright
python -m playwright install chromium
```

## よく使うコマンド
```bash
npm test          # 回帰テスト（footpath_regression.py, 全項目 PASS で終了コード0）
npm run serve     # ローカル配信（http://localhost:8080/）※ sample.json も配信される
```
テストは実コース（249点）を埋め込み済みで自己完結。Leaflet は `node_modules` を参照（`npm install` 済みが前提）。

## リリース手順（毎回）
1. 変更を実装（差分最小・CONSTANTS 集約）
2. `APP_VERSION` を更新
3. `npm test` で全 PASS を確認（新機能はテスト追加）
4. `index.html` に `file://`/`leaflet-rotate` が無いこと、波括弧の均衡、インライン JS の構文を確認
5. 変更内容を `HANDOFF_開発引き継ぎ書.md` の変更履歴に追記
6. ブランチにコミット（メッセージに版数と要点）。**push はオーナー指示を待つ**

## 触るときに壊しやすい所（詳細は ARCHITECTURE.md）
- **`_buildDisplayCoords`（往復ずらし表示）は“表示専用”**。当たり判定 `hitOverlays`・`_lastRouteCoords`・高低差・実データを絶対に変えない。往復間隔の調整は `OFF_GEO_M` 1か所。
- ラベルは `bindTooltip` 後にインライン変更したら **`tooltip.update()`** を呼ぶ（位置ずれ防止）。
- 保存画像の文字中心は flex ではなく **`line-height` 中央寄せ**（html2canvas 対策）。
- localStorage キーは **`LS` に集約**。ハードコードしない。

## 主要ドキュメント
- `HANDOFF_開発引き継ぎ書.md` … 全体像・変更履歴・未対応作業・検証環境
- `ARCHITECTURE.md` … 設計・描画パイプライン・不変条件
- `footpath_regression_README.md` … 回帰テストの内訳
