# 回帰テストの内訳（footpath_regression.py）

`npm test` で実行。静的チェック（文字列の有無）→ 機能チェック（Playwright Chromium・file://・390×812）→ オフライン（ローカル配信＋サービスワーカー）→ WebKit → 見た目（基準画像との比較）の順に走り、全項目 PASS で終了コード 0。

- 静的：`static_checks()`。定数・関数・文言の存在を `src` から確かめる
- 機能：`functional_checks()`。実コースを埋め込んだページで操作を再現し、DOM と状態を確かめる
- オフライン：`offline_checks()`。`http.server` で配信し、サービスワーカーが働くこと・配布リンクが圏外で開くことを見る
- 見た目：`visual_checks()`。`tests/baseline/map_image.png`・`print_sheet.png` と比べる（作り直すときはファイルを消して `npm test`）

## WebKit の検査（v146）
`webkit_checks()`：Playwright の WebKit（iPhone の Safari と同じエンジン）で、配布リンク（`?course=sample.json`）と編集画面を 390×812 で開き、画面からはみ出す部品が無いこと・歩く人の帯が出ること・メニューが収まることを確かめる。ローカル配信（http.server）を使う。WebKit が入っていない環境（`python -m playwright install webkit` 未実施）では「見送り」として PASS 扱いにし、CI では入れて走らせる。
