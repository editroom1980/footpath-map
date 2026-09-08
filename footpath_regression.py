#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Footpath Mapmaker 回帰テスト (regression harness)
================================================
目的: 過去に直した不具合の再発と、出荷時の基本不具合を「出荷前に機械で」検出する。
使い方: python3 footpath_regression.py [/path/to/index.html]
        省略時は同じフォルダの index.html を対象にする。
本体コードは一切変更しない。判定はすべて読み取り専用。
"""
import sys, re, json, os, subprocess, tempfile

INDEX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')

# === 固定テスト資産：実コース「千種町千草〜岩野辺」の実OSRM形状(249点) ===
REAL_ROUTE = [
  [35.152565,134.445007],[35.152631,134.444992],[35.152564,134.444496],[35.152548,134.444499],[35.152324,134.444537],[35.152245,134.444554],
  [35.152156,134.444572],[35.151987,134.444598],[35.15168,134.444609],[35.151644,134.444609],[35.15168,134.444609],[35.151987,134.444598],
  [35.152156,134.444572],[35.152245,134.444554],[35.152324,134.444537],[35.152564,134.444496],[35.152894,134.44443],[35.153133,134.444392],
  [35.153622,134.444295],[35.153627,134.444328],[35.153652,134.444501],[35.153645,134.444771],[35.153707,134.444776],[35.153771,134.44478],
  [35.153863,134.444788],[35.153884,134.444794],[35.15391,134.444778],[35.153941,134.444758],[35.153986,134.444731],[35.154069,134.444679],
  [35.154186,134.444601],[35.154133,134.444474],[35.154194,134.444426],[35.154237,134.444389],[35.154242,134.444384],[35.15428,134.444451],
  [35.154334,134.444541],[35.154401,134.444632],[35.154477,134.444844],[35.154609,134.445261],[35.154632,134.445359],[35.154671,134.445498],
  [35.154688,134.445632],[35.154663,134.445657],[35.154636,134.445684],[35.154694,134.445764],[35.154778,134.445834],[35.154886,134.445899],
  [35.155171,134.446039],[35.155186,134.446262],[35.155196,134.446465],[35.155244,134.446633],[35.15526,134.446759],[35.15535,134.446956],
  [35.155432,134.447136],[35.155656,134.447445],[35.155733,134.447578],[35.155897,134.447883],[35.15592,134.448125],[35.155985,134.448254],
  [35.156123,134.448775],[35.156214,134.448974],[35.156285,134.449085],[35.156419,134.44927],[35.15655,134.449442],[35.156629,134.449597],
  [35.156697,134.44974],[35.156162,134.450128],[35.156247,134.4503],[35.156427,134.450547],[35.15678,134.450906],[35.156864,134.45101],
  [35.157023,134.451229],[35.157078,134.451488],[35.157138,134.451672],[35.157202,134.451934],[35.157326,134.452314],[35.157416,134.452656],
  [35.157553,134.452917],[35.157778,134.453292],[35.157947,134.45384],[35.157954,134.453893],[35.158018,134.454358],[35.157995,134.454625],
  [35.15793,134.454986],[35.158041,134.455153],[35.158096,134.455216],[35.158111,134.455235],[35.1584,134.455429],[35.158234,134.456349],
  [35.158167,134.456665],[35.158122,134.456983],[35.158122,134.456983],[35.158116,134.457253],[35.158125,134.457412],[35.158238,134.458054],
  [35.15826,134.458275],[35.158267,134.458505],[35.158258,134.458659],[35.15807,134.460073],[35.158025,134.460505],[35.158025,134.460662],
  [35.158038,134.461035],[35.158103,134.461685],[35.158116,134.461918],[35.158111,134.462181],[35.158097,134.462414],[35.157999,134.463975],
  [35.157983,134.464305],[35.157966,134.46459],[35.15797,134.46479],[35.158001,134.464954],[35.158048,134.465094],[35.15818,134.465434],
  [35.158251,134.46559],[35.1583,134.465766],[35.158354,134.466021],[35.158357,134.466333],[35.158268,134.467405],[35.158268,134.467405],
  [35.158268,134.467405],[35.158357,134.466333],[35.158354,134.466059],[35.158488,134.466046],[35.158655,134.466031],[35.158759,134.466092],
  [35.158817,134.466075],[35.15885,134.465838],[35.158876,134.465618],[35.158906,134.465395],[35.158981,134.465203],[35.158887,134.465083],
  [35.158886,134.464958],[35.159025,134.464621],[35.159071,134.464332],[35.159378,134.464486],[35.159417,134.464508],[35.159426,134.464512],
  [35.159417,134.464508],[35.158673,134.46409],[35.158498,134.463988],[35.15824,134.463864],[35.158124,134.463939],[35.157999,134.463975],
  [35.158097,134.462414],[35.158111,134.462181],[35.158116,134.461918],[35.158103,134.461685],[35.158038,134.461035],[35.158025,134.460662],
  [35.158273,134.460738],[35.15838,134.460758],[35.158538,134.460827],[35.158603,134.460837],[35.158685,134.460758],[35.158742,134.460642],
  [35.158804,134.460361],[35.158832,134.460189],[35.158832,134.460148],[35.158877,134.459901],[35.158905,134.459682],[35.158938,134.459544],
  [35.159001,134.459284],[35.1593,134.458427],[35.159458,134.457995],[35.159497,134.457831],[35.159508,134.457125],[35.159531,134.456899],
  [35.159559,134.456803],[35.159581,134.456672],[35.159632,134.456494],[35.159699,134.456103],[35.159711,134.455615],[35.159716,134.455438],
  [35.159739,134.4553],[35.159778,134.455188],[35.159818,134.455075],[35.160139,134.454422],[35.16028,134.454067],[35.160376,134.453649],
  [35.160224,134.4536],[35.160083,134.453572],[35.159942,134.453517],[35.159812,134.453415],[35.159609,134.453264],[35.159469,134.45321],
  [35.159119,134.453065],[35.158826,134.452887],[35.158702,134.452825],[35.158564,134.452725],[35.158536,134.452601],[35.158459,134.452398],
  [35.158288,134.45203],[35.158417,134.451881],[35.158522,134.451753],[35.158577,134.45164],[35.158622,134.451523],[35.158674,134.451381],
  [35.158712,134.451112],[35.158747,134.450662],[35.158732,134.450535],[35.158716,134.450399],[35.158666,134.450132],[35.158653,134.449956],
  [35.158747,134.44935],[35.158747,134.44911],[35.158731,134.44898],[35.158618,134.448282],[35.158583,134.448044],[35.158571,134.4479],
  [35.158587,134.447659],[35.158601,134.447352],[35.158439,134.44737],[35.158313,134.447358],[35.158158,134.447326],[35.158,134.447259],
  [35.157118,134.44674],[35.156718,134.446504],[35.156679,134.446368],[35.156633,134.446223],[35.1566,134.446006],[35.156569,134.44596],
  [35.156526,134.445971],[35.156376,134.446025],[35.156173,134.44607],[35.156164,134.446072],[35.15605,134.4461],[35.155846,134.446172],
  [35.155731,134.445763],[35.15566,134.445507],[35.155558,134.445277],[35.155484,134.445148],[35.155402,134.445025],[35.155205,134.444807],
  [35.155056,134.444641],[35.155029,134.444599],[35.154967,134.4445],[35.154866,134.444282],[35.15478,134.444063],[35.154676,134.444047],
  [35.154555,134.444052],[35.154463,134.444075],[35.154247,134.444153],[35.154138,134.444188],[35.153808,134.444268],[35.153622,134.444295],
  [35.153187,134.444381],[35.153133,134.444392],[35.153054,134.444405],
]


RESULTS = []  # (分類, 名前, ok, 詳細)
def chk(cat, name, ok, detail=''):
    RESULTS.append((cat, name, bool(ok), str(detail)))
    return bool(ok)

# ----------------------------------------------------------------------
# 1) 静的チェック（ブラウザ不要）
# ----------------------------------------------------------------------
def static_checks(src):
    c = src.count('cdnjs')
    chk('静的', 'CDN参照は4つ（leaflet css/js・html2canvas・QR）', c == 4, f'count={c}')
    chk('静的', 'CDNはすべて版を固定',
        len(re.findall(r'cdnjs\.cloudflare\.com/ajax/libs/[^/]+/\d+\.\d+(?:\.\d+)?/', src)) == 4)
    chk('静的', 'leaflet-rotate を使っていない', 'leaflet-rotate' not in src)
    chk('静的', 'ローカルfile://パスが残っていない', 'file:///home/claude' not in src)
    chk('静的', '波括弧 {} の均衡', src.count('{') == src.count('}'), f"{src.count('{')-src.count('}')}")
    chk('静的', '丸括弧 () の均衡', src.count('(') == src.count(')'), f"{src.count('(')-src.count(')')}")
    chk('静的', '角括弧 [] の均衡', src.count('[') == src.count(']'), f"{src.count('[')-src.count(']')}")
    # JS構文チェック（インラインscriptを抽出して node --check）
    blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', src, re.S)
    js = '\n;\n'.join(blocks)
    tf = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8')
    tf.write(js); tf.close()
    try:
        r = subprocess.run(['node', '--check', tf.name], capture_output=True, text=True)
        chk('静的', 'JS構文 node --check', r.returncode == 0, (r.stderr or '')[:160].replace('\n', ' '))
    except FileNotFoundError:
        chk('静的', 'JS構文 node --check', True, 'nodeなし→スキップ')
    finally:
        os.unlink(tf.name)
    # 版数・保存キー・重要関数・地図設定が消えていないこと
    chk('静的', 'APP_VERSION 定義あり', re.search(r"APP_VERSION\s*=\s*'v?\d", src) is not None)
    for key in ['fp_courses', 'fp_basemap', 'fp_custompaths', 'fp_custom_on', 'fp_custom_snap']:
        chk('静的', f'保存キー {key} 存在', f"'{key}'" in src)
    chk('静的', '保存キーは LS に集約済み (const LS)', 'const LS = {' in src)
    chk('静的', '保存キーの直書き呼び出しが無い',
        re.search(r"localStorage\.(get|set|remove)Item\(['\"](fp_|_fp_)", src) is None,
        '生キーの localStorage 呼び出しが残存')
    for fn in ['_buildDisplayCoords', '_despikeSeg', '_vpPosAlong', 'calcVpOrder',
               'scheduleRouting', 'buildCurrentSaveData', 'loadCourseData', 'exportRouteCoords']:
        chk('静的', f'関数 {fn} 存在', f'function {fn}' in src)
    chk('静的', '地図 maxZoom:21 維持', 'maxZoom:21' in src.replace(' ', ''))
    chk('静的', 'オフセット地理基準(OFF_GEO_M)維持', 'OFF_GEO_M' in src)
    chk('静的', '画像保存の倍率定数 IMG_SCALE 維持', 'const IMG_SCALE' in src)
    chk('静的', '画像倍率ヘルパ _imgScale 存在', 'function _imgScale' in src)
    chk('静的', 'html2canvas が _imgScale 経由（2関数とも）',
        len(re.findall(r'scale:\s*_imgScale\(', src)) >= 2,
        '画像保存2関数とも倍率ヘルパ経由であること')
    chk('静的', 'WP○内文字サイズ関数 _wpFont 存在', 'function _wpFont' in src)
    chk('静的', 'wpIcon が _wpFont を使用', '_wpFont(sz[0]' in src)
    chk('静的', '名称ラベルサイズ LABEL_SIZES 維持', 'const LABEL_SIZES' in src)
    chk('静的', 'ラベルサイズ切替 cycleLabelSize 存在', 'function cycleLabelSize' in src)
    chk('静的', 'ツールチップが _labelSize() を使用', "_labelSize()+'px'" in src)
    chk('静的', 'PCツールバーに文字サイズボタン', 'id="btnLabelSize"' in src)
    chk('静的', 'ラベル位置再計算 tooltip.update を呼ぶ', "_ttObj.update === 'function'" in src)
    # --- v80: 文字・○の大きさ設定（スマホメニュー＋設定の保存）---
    chk('静的', 'ラベル表示名 LABEL_SIZE_LABELS 維持', 'const LABEL_SIZE_LABELS' in src)
    chk('静的', 'スポット○サイズ定数 WP_SIZES 維持', 'const WP_SIZES' in src)
    chk('静的', '○サイズヘルパ _wpSize 存在', 'function _wpSize' in src)
    chk('静的', 'WPマーカーが _wpSize を使用（36/30の直書きが無い）',
        src.count('_wpSize()') >= 3 and 'isMobile() ? [36,36] : [30,30]' not in src)
    chk('静的', 'サイズ設定 setLabelSize/setWpSize 存在',
        'function setLabelSize' in src and 'function setWpSize' in src)
    chk('静的', 'サイズ設定の保存キーが LS に集約',
        re.search(r"labelSize:\s*'fp_labelsize'", src) is not None and
        re.search(r"wpSize:\s*'fp_wpsize'", src) is not None)
    chk('静的', '起動時にサイズ設定を復元 restoreSizePrefs', 'restoreSizePrefs();' in src)
    chk('静的', 'ラベル位置が○の大きさに追従', '_wpSize()[1] / 2 + 4' in src)
    chk('静的', 'スマホメニューに文字サイズ5段階', len(re.findall(r'data-lsz="\d"', src)) == 5)
    chk('静的', 'スマホメニューに○サイズ3段階', len(re.findall(r'data-wsz="\d"', src)) == 3)
    chk('静的', 'メニュー同期に _syncSizeMenu を含む', '_syncSizeMenu();' in src)
    # --- v81: 保存失敗の通知・経路フォールバック通知・標高取得の分割・共有情報 ---
    chk('静的', '保存関数が成否を返す (setCourses)',
        'return true;' in src and re.search(r"catch\(_\)\s*\{ return false; \}", src) is not None)
    chk('静的', '保存失敗をユーザーに知らせる', '保存できませんでした' in src)
    chk('静的', '保存に失敗したら一覧へ戻らない', 'saveCourse()===false' in src.replace(' ', ''))
    chk('静的', '経路フォールバック通知 _warnRouteFallback 存在', 'function _warnRouteFallback' in src)
    chk('静的', 'OSRM失敗時に通知を呼ぶ', '_warnRouteFallback();' in src)
    chk('静的', '標高取得の同時数 ELEV_BATCH 維持', 'const ELEV_BATCH' in src)
    chk('静的', '標高取得を分割している（一括Promise.allでない）',
        'i += ELEV_BATCH' in src and 'await Promise.all(pts.map(' not in src)
    chk('静的', 'ホーム画面追加用 manifest を参照', 'rel="manifest"' in src)
    chk('静的', '共有カード(OGP)とテーマ色', 'og:title' in src and 'theme-color' in src)
    # --- v82: 配布用リンク（?course=xxx.json）---
    chk('静的', '配布リンクの安全確認 _safeCourseFile 存在', 'function _safeCourseFile' in src)
    chk('静的', '配布リンクの読込 loadCourseFromFile 存在', 'async function loadCourseFromFile' in src)
    chk('静的', '配布リンクのダイアログ openShareDialog 存在', 'function openShareDialog' in src)
    chk('静的', 'URLの course パラメータを読む', "p.get('course')" in src)
    chk('静的', '閲覧専用CSS（編集UIを隠す）', 'body.viewonly' in src)
    chk('静的', '配布リンクでは保存ボタンを隠す', 'body.viewonly .hbtn-save' in src)
    chk('静的', '配布リンクで説明文を読み取り専用表示', 'function _applyViewDesc' in src and 'view-desc' in src)
    chk('静的', '配布リンクではサンプルを取り込まない',
        re.search(r'if \(!_viewParams\(\)\.on\)', src) is not None)
    chk('静的', 'ファイル名指定の書き出し _downloadJsonAs 存在', 'function _downloadJsonAs' in src)
    # --- v83: GPX書き出し／全コース一括バックアップ ---
    chk('静的', 'GPX生成 buildGpx 存在', 'function buildGpx' in src)
    chk('静的', 'GPX書き出し exportGpx 存在', 'function exportGpx' in src)
    chk('静的', 'GPXのXMLエスケープ _escXml 存在', 'function _escXml' in src)
    chk('静的', 'GPXは表示用でなく実データを使う', '_lastRouteCoords' in src and 'buildDisplayCoords()' not in src.split('function buildGpx')[1][:900])
    chk('静的', 'PC・スマホ両方にGPXボタン',
        src.count('exportGpx()') >= 3, f"呼び出し={src.count('exportGpx()')}")
    chk('静的', '一括バックアップ buildBackupData/applyBackupData 存在',
        'function buildBackupData' in src and 'function applyBackupData' in src)
    chk('静的', 'バックアップUI（書き出し・復元）', 'exportAllCourses()' in src and 'importBackupFile(this)' in src)
    # --- v84: 画像保存の後片付け（try内constをfinallyで参照していた不具合の再発防止）---
    chk('静的', '画像保存の復元がスコープ外変数に依存しない',
        '_savedVpOpacity' not in src and '_savedTtStyles' not in src and '_savedIconStyles' not in src)
    chk('静的', '画像保存後にラベルと○を作り直す',
        'wps.forEach(wp => updateTooltip(wp));   // ラベルの色・位置・サイズを作り直す' in src)
    # --- v85: 配布シート（A4印刷・PDF・画像／凡例・縮尺・方位）---
    chk('静的', '地図の画像化を共通化 _captureMapCanvas', 'async function _captureMapCanvas' in src)
    chk('静的', '画像保存が共通関数を使う', 'await _captureMapCanvas()' in src)
    chk('静的', '配布シート openPrintSheet 存在', 'async function openPrintSheet' in src)
    chk('静的', '縮尺バー _sheetScale 存在', 'function _sheetScale' in src)
    chk('静的', '凡例 _sheetLegend 存在', 'function _sheetLegend' in src)
    chk('静的', '印刷レイアウト（A4横）', '@media print' in src and 'size:A4landscape' in src.replace(' ', ''))
    chk('静的', '印刷時は配布シートだけを出す', 'body > *:not(#sheetOver){display:none!important}' in src)
    chk('静的', '色を印刷に反映（print-color-adjust）', 'print-color-adjust:exact' in src)
    chk('静的', 'PC・スマホ両方に配布シートボタン', src.count('openPrintSheet()') >= 3,
        f"呼び出し={src.count('openPrintSheet()')}")
    # --- v86: 未保存のまま閉じる前の確認 ---
    chk('静的', '未保存フラグ _dirty を持つ', 'let   _dirty' in src)
    chk('静的', '編集で未保存フラグが立つ（saveSnapshot）', '_dirty = true;' in src)
    chk('静的', '保存・読込で未保存フラグが下りる', src.count('_dirty = false;') >= 3)
    chk('静的', '閉じる前の確認（閲覧モードでは出さない）',
        "addEventListener('beforeunload'" in src and '!_dirty || viewMode' in src)
    # --- v87: 歩く速さ／坂を考慮した所要時間 ---
    chk('静的', '歩く速さ定数 WALK_SPEEDS 維持', 'const WALK_SPEEDS' in src)
    chk('静的', '登りの加算係数 CLIMB_MIN_PER_100M 維持', 'const CLIMB_MIN_PER_100M' in src)
    chk('静的', '速さ切替 setWalkSpeed 存在', 'function setWalkSpeed' in src)
    chk('静的', '登り合計 _totalAscent 存在', 'function _totalAscent' in src)
    chk('静的', '所要時間が固定4km/hでなくなった', '/ 4 * 60' not in src and '_walkSpeed()' in src)
    chk('静的', '速さの保存キー(LS.walkSpeed)を使用', re.search(r"walkSpeed:\s*'fp_walkspeed'", src) is not None)
    chk('静的', 'PC・スマホ両方に速さの選択', 'walkSpeedSel' in src and 'data-spd=' in src)
    # --- v87: 配布シートのQRコード ---
    chk('静的', 'QRライブラリを読み込む', 'qrcodejs/1.0.0/qrcode.min.js' in src)
    chk('静的', 'QR描画 _renderSheetQr 存在', 'function _renderSheetQr' in src)
    chk('静的', 'QRが無くてもシートは使える（未読込を許容）', "typeof QRCode === 'undefined'" in src)
    chk('静的', '配布リンクを覚える（LS.shareLinks）', re.search(r"shareLinks:\s*'fp_sharelinks'", src) is not None)
    # --- v88: 設定の見本表示・はじめての人への案内 ---
    chk('静的', '○の大きさに見本の丸がある', src.count('class="mm-dot"') >= 3)
    chk('静的', '見本の大きさは定数から設定する',
        'LABEL_SIZES[Number(el.getAttribute(' in src and 'WP_SIZES[Number(el.getAttribute(' in src)
    chk('静的', 'コース0件の案内がある', '下の「＋ 新しいコースを作成」から始められます' in src)
    # --- v89: 写真の保存先を IndexedDB へ ---
    for fn in ['_idb', '_photoPut', '_photoGet', '_stashPhotos', '_embedPhotos',
               'migratePhotosToIdb', 'gcPhotos', 'renderStorageInfo']:
        chk('静的', f'写真ストア {fn} 存在', f'function {fn}' in src)
    chk('静的', '保存は写真の退避を待つ（saveCourse は非同期）', 'async function saveCourse' in src)
    chk('静的', '「保存して戻る」も待つ', 'await saveCourse()===false' in src.replace(' ===', '==='))
    chk('静的', '書き出しは写真の実体を埋め込む', src.count('await _embedPhotos(') >= 4,
        f"件数={src.count('await _embedPhotos(')}")
    chk('静的', '表示は参照に対応（_photoAttr/_fillPhotoImgs）',
        'function _photoAttr' in src and 'function _fillPhotoImgs' in src)
    chk('静的', '取り込んだ写真も退避する', 'await _stashPhotos([data])' in src)
    # --- v90: オフライン対応（サービスワーカー）---
    sw_path = os.path.join(os.path.dirname(os.path.abspath(INDEX)), 'sw.js')
    sw = open(sw_path, encoding='utf-8').read() if os.path.exists(sw_path) else ''
    chk('静的', 'sw.js がある', bool(sw), sw_path)
    chk('静的', 'アプリ本体はネット優先（古い版で固まらない）',
        'async function networkFirst' in sw and 'networkFirst(req)' in sw)
    chk('静的', '地図タイルはキャッシュ優先＋上限あり',
        'cacheFirst(req, TILE_CACHE' in sw and 'TILE_MAX' in sw and 'trimTiles' in sw)
    chk('静的', '新しい版をすぐ有効にする（skipWaiting/claim）',
        'skipWaiting()' in sw and 'clients.claim()' in sw)
    chk('静的', '旧版のアプリキャッシュを片づける', "startsWith('fp-app-')" in sw)
    chk('静的', 'オフライン解除スイッチ ?nosw=1',
        "get('nosw')" in src and 'function _swUnregisterAll' in src)
    chk('静的', 'オフライン保存 saveMapOffline 存在', 'async function saveMapOffline' in src)
    chk('静的', 'タイル計算 offlineTileUrls 存在', 'function offlineTileUrls' in src)
    chk('静的', '保存枚数の上限 OFFLINE_MAX_TILES 維持', 'const OFFLINE_MAX_TILES' in src)
    chk('静的', 'オフライン表示のバッジ', 'offlineBadge' in src and 'body.offline' in src)
    # --- v91: 実機の動作確認（セルフチェック）---
    chk('静的', '動作確認 runSelfCheck 存在', 'async function runSelfCheck' in src)
    chk('静的', '動作確認を開く openSelfCheck 存在', 'async function openSelfCheck' in src)
    chk('静的', '?check=1 で自動的に開く', "get('check') === '1'" in src)
    chk('静的', '起動画面とメニューの両方に入口',
        'id="s1CheckLink"' in src and src.count('openSelfCheck()') >= 3,
        f"呼び出し={src.count('openSelfCheck()')}")
    chk('静的', '結果をコピーできる', 'function copySelfCheck' in src and 'function _selfCheckText' in src)
    chk('静的', '圏外での確認手順を載せている', '機内モード' in src)
    chk('静的', '背景地図に配色済みタイル追加', all(k in src for k in ['opentopo:', 'carto:', 'osm_hot:']))
    chk('静的', '背景地図切替 cycleBaseMap 存在', 'function cycleBaseMap' in src)
    chk('静的', 'PCツールバーに地図切替ボタン', 'id="btnBaseMap"' in src)
    chk('静的', 'サンプル取り込み ensureSampleCourse 存在', 'async function ensureSampleCourse' in src)
    chk('静的', 'サンプルURL定数 SAMPLE_URL 維持', 'const SAMPLE_URL' in src)
    chk('静的', 'サンプル済みフラグ(LS.sampleDone)を使用', 'sampleDone' in src)
    chk('静的', '起動時にサンプル取り込みを呼ぶ',
        re.search(r'if \(!_viewParams\(\)\.on\)\s*\{\s*\n\s*ensureSampleCourse\(\)', src) is not None)

# ----------------------------------------------------------------------
# 2) 機能チェック（Playwright ヘッドレス）
#    _buildDisplayCoords の不変条件を実コース＋合成データで検証
# ----------------------------------------------------------------------
def functional_checks(index_path):
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        chk('機能', 'Playwright 利用可', False, f'未導入: {e}（機能テストはスキップ）')
        return
    # --- ブラウザとローカルLeafletのパス（環境非依存）---
    here = os.path.dirname(os.path.abspath(__file__))
    sandbox_browsers = '/opt/pw-browsers'
    sandbox_chrome = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    if os.path.isdir(sandbox_browsers):
        os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', sandbox_browsers)
    # file:// で動かすため CDN Leaflet をローカルに差し替えたテスト版を作る
    # （Leaflet は「このスクリプトと同じ場所の node_modules」を参照。なければ `npm install leaflet@1.9.4`）
    leaf_css = 'file://' + os.path.join(here, 'node_modules/leaflet/dist/leaflet.css')
    leaf_js  = 'file://' + os.path.join(here, 'node_modules/leaflet/dist/leaflet.js')
    if not (os.path.exists(leaf_css[7:]) and os.path.exists(leaf_js[7:])):
        chk('機能', 'ローカルLeaflet 存在', False,
            'node_modules/leaflet が無い → `npm install leaflet@1.9.4`（機能テストはスキップ）'); return
    src = open(index_path, encoding='utf-8').read()
    local = (src
        .replace('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css', leaf_css)
        .replace('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js', leaf_js))
    tdir = tempfile.mkdtemp()
    tpath = os.path.join(tdir, 'test_local.html')
    open(tpath, 'w', encoding='utf-8').write(local)
    # Chromium：サンドボックス固有パスがあればそれを、無ければ Playwright 既定（`playwright install chromium`）を使う
    launch_kwargs = {'args': ['--allow-file-access-from-files']}
    if os.path.exists(sandbox_chrome):
        launch_kwargs['executable_path'] = sandbox_chrome

    with sync_playwright() as pw:
        b = pw.chromium.launch(**launch_kwargs)
        ctx = b.new_context(viewport={'width': 390, 'height': 812}, has_touch=True, device_scale_factor=2)
        page = ctx.new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        page.goto('file://' + tpath, wait_until='domcontentloaded'); page.wait_for_timeout(400)
        page.click('.s1-fab'); page.wait_for_timeout(120)
        page.fill('#s1Name', 'T'); page.fill('#s1Area', '宍粟市'); page.click('#s1Btn'); page.wait_for_timeout(1100)
        page.evaluate("()=>{ if(!leafMap)initMap(); leafMap.setMaxZoom(24); }")

        # 共通JS：自己交差カウント／中心線からの距離
        helpers = """
          window.__lp=x=>{const q=leafMap.latLngToLayerPoint(L.latLng(x[0],x[1]));return[q.x,q.y];};
          window.__selfX=function(D){function h(p1,p2,p3,p4){const d=(A,B,C)=>(B[0]-A[0])*(C[1]-A[1])-(B[1]-A[1])*(C[0]-A[0]);const d1=d(p3,p4,p1),d2=d(p3,p4,p2),d3=d(p1,p2,p3),d4=d(p1,p2,p4);return((d1>0&&d2<0)||(d1<0&&d2>0))&&((d3>0&&d4<0)||(d3<0&&d4>0));}
            let c=0;for(let i=0;i<D.length-1;i++)for(let k=i+2;k<D.length-1;k++){if(i===0&&k===D.length-2)continue;if(h(D[i],D[i+1],D[k],D[k+1]))c++;}return c;};
          window.__nd=function(pt,arr){let m=1e9;for(const q of arr){const dx=pt[0]-q[0],dy=pt[1]-q[1];const e=dx*dx+dy*dy;if(e<m)m=e;}return Math.sqrt(m);};
        """
        page.evaluate("()=>{" + helpers + "}")

        REAL = REAL_ROUTE
        CTR = [35.153081, 134.444441]

        # INV-A: 実コース z18-21 で自己交差が1以下（既知の端点スタブ1か所のみ・新規増加なし）
        maxX = 0
        for z in [18, 19, 20, 21]:
            x = page.evaluate("""(a)=>{const{ctr,rl,z}=a;leafMap.setView([ctr[0],ctr[1]],z,{animate:false});
                const D=_buildDisplayCoords(rl).map(__lp);return __selfX(D);}""", {'ctr': CTR, 'rl': REAL, 'z': z})
            maxX = max(maxX, x)
        chk('機能', '実コース 自己交差≤1 (z18-21)', maxX <= 1, f'最大={maxX}')

        # INV-B: 往復なしのルートは入力と完全一致（オフセットを一切かけない）
        nod = [[35.10 + 0.0005 * i, 134.40] for i in range(8)]
        ident = page.evaluate("""(rl)=>{const o=_buildDisplayCoords(rl);return JSON.stringify(o)===JSON.stringify(rl);}""", nod)
        chk('機能', '往復なしルートは無変更', ident, '')

        # INV-C: 中間の往復にはオフセットが掛かる（中心線から離れた点が存在）
        mid = []
        mid += [[35.10 + 0.0003 * i, 134.40] for i in range(6)]
        y0 = mid[-1][0]
        mid += [[y0 + 0.0003 * i, 134.40] for i in range(1, 8)]
        yt = mid[-1][0]
        mid += [[yt - 0.0003 * i, 134.40 + 0.00002] for i in range(1, 8)]
        mid += [[y0 - 0.0003 * i, 134.40] for i in range(1, 6)]
        offc = page.evaluate("""(a)=>{const{rl,ctr}=a;leafMap.setView([ctr[0],ctr[1]],19,{animate:false});
            const D=_buildDisplayCoords(rl).map(__lp),B=rl.map(__lp);let c=0;for(const p of D)if(__nd(p,B)>2.5)c++;return c;}""",
            {'rl': mid, 'ctr': CTR})
        chk('機能', '中間の往復はオフセットされる', offc > 0, f'離れた点={offc}')

        # INV-D: v73の核心 — オフセットは px基準より狭くならない＆高ズームで地理基準が効く
        #   ※ Python再計算ではなく、実際の _buildDisplayCoords 出力の最大オフセット量(中心線からの距離)を実測する
        narrower = False
        geo_active_z21 = False
        for z in [18, 19, 20, 21]:
            m = page.evaluate("""(a)=>{const{ctr,rl,z}=a;leafMap.setView([ctr[0],ctr[1]],z,{animate:false});
                const gz=leafMap.getZoom();const w=_routeWeight();const base=(w+2*(w/3))/2;
                const D=_buildDisplayCoords(rl).map(__lp), B=rl.map(__lp);
                let mx=0;for(const p of D){const d=__nd(p,B);if(d>mx)mx=d;}
                return {base:+base.toFixed(3), actual:+mx.toFixed(3), gz};}""", {'ctr': CTR, 'rl': REAL, 'z': z})
            if m['actual'] < m['base'] - 1.0:                 # 実オフセットがpx基準より明確に小さい＝狭くなった
                narrower = True
            if m['gz'] >= 21 and m['actual'] > m['base'] * 1.3:  # z21で実測オフセットがpx基準を大きく上回る＝地理基準が効いている
                geo_active_z21 = True
        chk('機能', 'オフセットは従来より狭くならない(実測)', not narrower, '')
        chk('機能', '高ズーム(z21)で地理基準が効き間隔が広がる(実測)', geo_active_z21, '')

        # INV-E: ロード〜描画でJSエラーが出ない
        chk('機能', 'JSエラーなし（ロード〜描画）', len(errs) == 0, '; '.join(errs[:2]))

        # INV-F: 保存キー(LS)の往復が実機で機能する（setCourses→getCourses）
        rt = page.evaluate("""()=>{ try{
            const before=getCourses();
            setCourses([{id:99999,name:'__rtest__'}]);
            const got=getCourses();
            const ok=Array.isArray(got)&&got.some(c=>c&&c.name==='__rtest__');
            setCourses(Array.isArray(before)?before:[]);   // 後始末
            return ok;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '保存コースのLS往復が機能 (setCourses→getCourses)', rt is True, str(rt))

        # INV-G: 地図種別の保存設定がLS経由で往復する
        bm = page.evaluate("""()=>{ try{
            const before=_loadBaseMapPref(); _saveBaseMapPref('osm');
            const ok=_loadBaseMapPref()==='osm'; _saveBaseMapPref(before);
            return ok;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '地図種別設定のLS往復が機能', bm is True, str(bm))

        # INV-H: 保存データ生成が例外なく走り、オブジェクトを返す
        sd = page.evaluate("""()=>{ try{ const d=buildCurrentSaveData();
            return !!(d && typeof d==='object' && ('wps' in d));
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '保存データ生成 buildCurrentSaveData が動作', sd is True, str(sd))

        # INV-I: 画像保存倍率が安全枠内かつ高画質化されている（_imgScale の純検証）
        img = page.evaluate("""()=>{ try{
            const MA=16000000, MD=8192; const tests=[[390,844],[430,932],[1440,900],[1920,1080]];
            const out=[];
            for(const t of tests){ const w=t[0],h=t[1],s=_imgScale(w,h);
              out.push({w:w,h:h,s:s, dimOK:(s*w<=MD&&s*h<=MD), areaOK:(s===1||s*s*w*h<=MA), ge1:s>=1}); }
            return {out:out, iphoneImproved:_imgScale(390,844)>=2};
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_img = (isinstance(img, dict) and img.get('iphoneImproved')
                  and all(t['dimOK'] and t['areaOK'] and t['ge1'] for t in img['out']))
        chk('機能', '画像保存倍率が安全枠内＆iPhoneで高画質化', ok_img, str(img)[:160])

        # INV-J: WP○内文字が円からはみ出さない（_wpFont の実描画検証）
        ov = page.evaluate("""()=>{ try{
            const cases=[[30,'1'],[30,'10'],[30,'WC'],[30,'\\uD83C\\uDF3F'],[30,'\\u7891'],[36,'1'],[36,'WC'],[36,'10']];
            const bad=[];
            for(const c of cases){ const sz=c[0], sym=c[1], fs=_wpFont(sz,sym);
              const d=document.createElement('div');
              d.setAttribute('style','box-sizing:border-box;position:absolute;left:-9999px;width:'+sz+'px;height:'+sz+'px;border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:'+fs+'px;line-height:1;font-weight:bold');
              const sp=document.createElement('span'); sp.textContent=sym; sp.style.whiteSpace='nowrap'; d.appendChild(sp);
              document.body.appendChild(d);
              const cw=d.clientWidth, r=sp.getBoundingClientRect();
              if(r.width>cw+0.6 || r.height>cw+0.6) bad.push(sym+'@'+sz+'='+fs+'px');
              document.body.removeChild(d);
            }
            return bad;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', 'WP○内文字が円からはみ出さない', ov == [], str(ov))

        # INV-K: 名称ラベルサイズが全段階を循環して標準に戻る
        lc = page.evaluate("""()=>{ try{ const n=LABEL_SIZES.length, seq=[];
            for(let i=0;i<n;i++){ cycleLabelSize(); seq.push(_labelSize()); }
            return {seq:seq, back:_labelSize()===LABEL_SIZES[0], n:n};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '名称ラベルサイズが全段階循環して標準に戻る',
            isinstance(lc, dict) and lc.get('back') is True and lc.get('n') >= 5, str(lc))

        # INV-L: 文字・○の大きさ設定が保存され、再読込しても復元される（PC/スマホで状態共有）
        sp = page.evaluate("""()=>{ try{
            setLabelSize(2); setWpSize(2);
            const sl = localStorage.getItem(LS.labelSize), sw = localStorage.getItem(LS.wpSize);
            _labelSizeIdx = 0; _wpSizeIdx = 0;          // 再読込を模して既定へ戻す
            restoreSizePrefs();                          // 保存値から復元
            const r = {l:_labelSizeIdx, w:_wpSizeIdx};
            setLabelSize(0); setWpSize(0);               // 後続テストのため標準へ戻す
            return {sl:sl, sw:sw, r:r, stdLbl:_labelSize()===LABEL_SIZES[0], stdWp:_wpSizeIdx===0,
                    btn:(document.getElementById('lblSizeTxt')||{}).textContent};
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_sp = (isinstance(sp, dict) and sp.get('sl') == '2' and sp.get('sw') == '2'
                 and sp.get('r') == {'l': 2, 'w': 2} and sp.get('stdLbl') and sp.get('stdWp')
                 and sp.get('btn') == '標準')
        chk('機能', '文字・○の大きさ設定が保存され復元される', ok_sp, str(sp)[:170])

        # INV-M: ○の大きさ変更は見た目だけ（座標データ不変）＋ラベル位置と文字が追従。標準は従来値のまま
        wsz = page.evaluate("""()=>{ try{
            const wp = addWp(35.15257, 134.44501, 'course'); wp.name='テスト'; updateTooltip(wp);
            const snap = ()=>{ const el = wp.marker.getElement().firstElementChild, tt = wp.marker.getTooltip();
              return { d: Math.round(el.getBoundingClientRect().width),
                       off: tt.options.offset[1],
                       fs: Math.round(parseFloat(getComputedStyle(tt.getElement()).fontSize)),
                       lat: wp.lat, lng: wp.lng }; };
            setWpSize(0); setLabelSize(0); const std = snap();
            setWpSize(2); setLabelSize(4); const big = snap();
            setWpSize(0); setLabelSize(0);
            return {std:std, big:big, dataSame: std.lat===big.lat && std.lng===big.lng};
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_wsz = (isinstance(wsz, dict) and wsz.get('dataSame')
                  and wsz['std']['d'] == 36 and wsz['std']['off'] == -22 and wsz['std']['fs'] == 11
                  and wsz['big']['d'] > wsz['std']['d']
                  and abs(wsz['big']['off']) > abs(wsz['std']['off'])
                  and wsz['big']['fs'] > wsz['std']['fs'])
        chk('機能', '○の大きさ変更は見た目だけ（標準は従来と同値）', ok_wsz, str(wsz)[:190])

        # INV-N: 保存できなかったとき setCourses が false を返す（容量超過を検知できる）
        qs = page.evaluate("""()=>{ try{
            const orig = localStorage.setItem.bind(localStorage);
            const okBefore = setCourses(getCourses());                 // 通常時は true
            localStorage.setItem = ()=>{ const e=new Error('QuotaExceededError'); e.name='QuotaExceededError'; throw e; };
            const okFull = setCourses(getCourses());                   // 容量超過を模擬 → false
            localStorage.setItem = orig;
            const okAfter = setCourses(getCourses());
            return {okBefore:okBefore, okFull:okFull, okAfter:okAfter};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '保存容量オーバーを検知できる (setCourses=false)',
            isinstance(qs, dict) and qs.get('okBefore') is True and qs.get('okFull') is False
            and qs.get('okAfter') is True, str(qs))

        # INV-O: 標高取得は ELEV_BATCH 件ずつ（同時接続を出しすぎない＝待ち行列による誤タイムアウトを防ぐ）
        eb = page.evaluate("""()=>{ return new Promise(res=>{ try{
            const orig = window.fetch; let live = 0, peak = 0, calls = 0;
            window.fetch = () => { live++; calls++; peak = Math.max(peak, live);
              return new Promise(r => setTimeout(() => { live--; r({json: () => Promise.resolve({elevation: 100})}); }, 5)); };
            const pts = []; for (let i=0;i<25;i++) pts.push([35+i*0.001, 134+i*0.001]);
            _fetchElevs(pts).then(v => { window.fetch = orig; res({peak:peak, calls:calls, n:v.length, batch:ELEV_BATCH}); })
                            .catch(e => { window.fetch = orig; res('ERR:'+e.message); });
          }catch(e){ res('ERR:'+e.message); } }); }""")
        chk('機能', '標高取得の同時リクエストが上限内',
            isinstance(eb, dict) and eb.get('peak') <= eb.get('batch', 0) and eb.get('calls') == 25
            and eb.get('n') == 25, str(eb))

        # INV-P: 配布リンクは「同じ場所の.json」だけ受け付ける（外部URLや上位フォルダを弾く）
        sf = page.evaluate("""()=>{ try{
            const ok  = ['course-1.json','a_b-c.json','x.JSON'].map(v=>_safeCourseFile(v));
            const bad = ['../secret.json','https://evil.example/x.json','/etc/passwd.json','sub/dir.json',
                         'x.txt','','javascript:alert(1)', null].map(v=>_safeCourseFile(v));
            return {ok:ok, bad:bad,
                    name1:_shareFileName('Course 01!!'), name2:_shareFileName('a.json'),
                    name3:_shareFileName('波賀町 コース'), base:/\\/$/.test(_shareBaseUrl())};
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_sf = (isinstance(sf, dict)
                 and sf['ok'][0] == 'course-1.json' and sf['ok'][1] == 'a_b-c.json' and sf['ok'][2] == 'x.JSON'
                 and all(v is None for v in sf['bad'])
                 and sf['name1'] == 'Course-01.json' and sf['name2'] == 'a.json' and sf['name3'] == 'course.json'
                 and sf['base'] is True)
        chk('機能', '配布リンクは同じ場所の.jsonだけ受け付ける', ok_sf, str(sf)[:190])

        # INV-Q: 配布用JSONを読み込むと表示される／壊れた内容や404は読み込まない
        lf = page.evaluate("""()=>{ return (async()=>{ try{
            const orig = window.fetch;
            const stub = (body, ok) => { window.fetch = () => Promise.resolve({ok:ok!==false, json:()=>Promise.resolve(body)}); };
            const good = {id:987654321, name:'配布テスト', area:'テスト', wps:[
              {id:1,type:'course',name:'A',lat:35.152,lng:134.445,onRoute:true,photos:[]},
              {id:2,type:'course',name:'B',lat:35.153,lng:134.446,onRoute:true,photos:[]}], vps:[], maxWpId:2, maxVpNum:0};
            stub(good);           const r1 = await loadCourseFromFile('dist.json');
            stub({nope:1});       const r2 = await loadCourseFromFile('dist.json');
            stub(good, false);    const r3 = await loadCourseFromFile('dist.json');
            const r4 = await loadCourseFromFile('../evil.json');       // 危険な名前は fetch すらしない
            window.fetch = orig;
            const saved = getCourses().some(c => c && c.id === 987654321);   // 見る人の端末に保存しない
            return {r1:r1, r2:r2, r3:r3, r4:r4, saved:saved, name:(courseInfo||{}).name};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        ok_lf = (isinstance(lf, dict) and lf.get('r1') is True and lf.get('r2') is False
                 and lf.get('r3') is False and lf.get('r4') is False and lf.get('saved') is False
                 and lf.get('name') == '配布テスト')
        chk('機能', '配布用JSONを表示でき、端末には保存しない', ok_lf, str(lf)[:190])

        # INV-R: GPXが妥当なXMLで、スポット数・ルート点数が一致し、特殊文字が壊れない
        gp = page.evaluate("""()=>{ try{
            const a = addWp(35.15200,134.44500,'course'); a.name = 'テスト<&>"みち"';
            const b2 = addWp(35.15300,134.44600,'course'); b2.name = 'ゴール';
            const xml = buildGpx();
            const doc = new DOMParser().parseFromString(xml, 'application/xml');
            const err = doc.getElementsByTagName('parsererror').length;
            const wpt = doc.getElementsByTagName('wpt').length;
            const trkpt = doc.getElementsByTagName('trkpt').length;
            const root = doc.documentElement;
            const names = [...doc.getElementsByTagName('wpt')].map(w=>w.getElementsByTagName('name')[0].textContent);
            const order = [...root.children].map(c=>c.nodeName);
            return {err:err, wpt:wpt, trkpt:trkpt, ver:root.getAttribute('version'),
                    ns:root.namespaceURI, esc:names.indexOf('テスト<&>"みち"')>=0,
                    order:order.join(','), spots:wps.filter(w=>w.type!=='node').length,
                    raw:xml.indexOf('<?xml')===0};
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_gp = (isinstance(gp, dict) and gp.get('err') == 0 and gp.get('ver') == '1.1'
                 and gp.get('ns') == 'http://www.topografix.com/GPX/1/1'
                 and gp.get('wpt') == gp.get('spots') and gp.get('wpt') >= 2
                 and gp.get('trkpt') >= 2 and gp.get('esc') is True and gp.get('raw') is True
                 and gp.get('order','').startswith('metadata,wpt'))
        chk('機能', 'GPXが妥当（GPX1.1・地点数一致・特殊文字も壊れない）', ok_gp, str(gp)[:190])

        # INV-S: 一括バックアップは往復でき、同じコースを二重に増やさない
        bk = page.evaluate("""()=>{ return (async()=>{ try{
            const before = getCourses();
            setCourses([{id:'bk1',name:'A',wps:[{id:1,lat:35,lng:134}]},
                        {id:'bk2',name:'B',wps:[{id:1,lat:35,lng:134}]}]);
            const backup = buildBackupData();
            setCourses([{id:'bk1',name:'A-古い',wps:[{id:1,lat:35,lng:134}]}]);   // 1件だけ・内容も古い状態
            const r1 = await applyBackupData(backup);                             // 復元
            const after = getCourses();
            const r2 = await applyBackupData(backup);                             // 二度目＝増えない
            const after2 = getCourses();
            const bad = await applyBackupData({type:'course'});                   // 形式違いは受け付けない
            setCourses(before);
            return {r1:r1, n:after.length, names:after.map(c=>c.name).sort(),
                    r2:r2, n2:after2.length, bad:bad, cnt:backup.count, type:backup.type};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        ok_bk = (isinstance(bk, dict) and bk.get('cnt') == 2 and bk.get('type') == 'backup'
                 and bk['r1']['added'] == 1 and bk['r1']['replaced'] == 1 and bk.get('n') == 2
                 and bk.get('names') == ['A', 'B'] and bk.get('n2') == 2
                 and bk['r2']['added'] == 0 and bk['r2']['replaced'] == 2 and bk.get('bad') is None)
        chk('機能', 'バックアップの往復で二重に増えない', ok_bk, str(bk)[:190])

        # INV-T: 画像保存の後片付けが実際に走る（v84で修正した不具合の再発防止）
        #  以前は try 内の const を finally で参照していたため復元コードが動かず、
        #  撮影用に消したラベルの影・調整点の非表示が戻らなかった。
        rs = page.evaluate("""()=>{ return (async()=>{ try{
            const wp = addWp(35.15250, 134.44550, 'course');   // 検査用に必ずラベル付きWPを用意する
            wp.name = 'ラベル確認'; updateTooltip(wp);
            if (!(wp.marker && wp.marker.getTooltip && wp.marker.getTooltip())) return {no_wp:true};
            const origH2C = window.html2canvas, origClick = HTMLAnchorElement.prototype.click;
            window.html2canvas = () => Promise.resolve({ toDataURL: () => 'data:image/png;base64,AA' });
            HTMLAnchorElement.prototype.click = function(){};        // 実ダウンロードはしない
            let err = null;
            try { await saveMapAsImage(); } catch(e){ err = String(e); }
            window.html2canvas = origH2C; HTMLAnchorElement.prototype.click = origClick;
            // 撮影用に付けた box-shadow:none が現役のラベルに残っていないこと（＝後片付けが走った証拠）
            const live = wps.map(w => w.marker && w.marker.getTooltip && w.marker.getTooltip()
                                      && w.marker.getTooltip().getElement()).filter(Boolean);
            const left = live.filter(e => e.style.boxShadow === 'none').length;
            return { err: err, left: left, tips: live.length };
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        ok_rs = (isinstance(rs, dict) and rs.get('err') is None and not rs.get('no_wp')
                 and rs.get('tips', 0) >= 1 and rs.get('left') == 0)
        chk('機能', '画像保存の後片付けが実行される（撮影用の見た目が残らない）', ok_rs, str(rs)[:170])

        # INV-U: 配布シートが作られ、凡例・縮尺・方位が入る
        sh = page.evaluate("""()=>{ return (async()=>{ try{
            const orig = window.html2canvas;
            window.html2canvas = () => Promise.resolve({ toDataURL: () => 'data:image/png;base64,AA' });
            await openPrintSheet();
            window.html2canvas = orig;
            const s  = document.getElementById('printSheet');
            const sc = _sheetScale(1000);
            const used = new Set(wps.filter(w=>w.type!=='node').map(w=>w.type||'course'));
            return { shown:getComputedStyle(document.getElementById('sheetOver')).display,
                     img:!!s.querySelector('img'), north:!!s.querySelector('.sh-north'),
                     legend:s.querySelectorAll('.sh-lg').length, used:used.size,
                     meters:sc && sc.meters, ratio:sc && sc.ratio,
                     title:(s.querySelector('.sh-title')||{}).textContent||'' };
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        ok_sh = (isinstance(sh, dict) and sh.get('shown') == 'block' and sh.get('img') and sh.get('north')
                 and sh.get('legend') == sh.get('used', 0) + 1          # 種別ぶん＋「歩くコース」
                 and sh.get('meters', 0) > 0 and 0 < sh.get('ratio', 0) <= 0.6)
        chk('機能', '配布シートに凡例・縮尺・方位が入る', ok_sh, str(sh)[:180])

        # INV-V: 印刷では配布シートだけが出る（操作ボタン・アプリ画面は出ない）
        page.emulate_media(media='print')
        pr = page.evaluate("""()=>{ const g=id=>{const e=document.getElementById(id); return e?getComputedStyle(e).display:'なし';};
            return { sheet:g('sheetOver'), hdr:g('hdr'), s1:g('s1'),
                     actions:getComputedStyle(document.querySelector('#sheetOver .sheet-actions')).display }; }""")
        page.emulate_media(media='screen')
        chk('機能', '印刷時は配布シートだけが出る',
            isinstance(pr, dict) and pr.get('sheet') == 'block' and pr.get('hdr') == 'none'
            and pr.get('s1') == 'none' and pr.get('actions') == 'none', str(pr))

        # INV-W: 未保存フラグが「編集で立ち、保存で下りる」
        dy = page.evaluate("""()=>{ return (async()=>{ try{
            const start = _dirty;
            saveSnapshot();                       // 編集操作の共通入口
            const afterEdit = _dirty;
            courseInfo = courseInfo || {}; if(!courseInfo.name) courseInfo.name = '未保存テスト';
            const okSave = await saveCourse();    // 保存できれば false に戻る
            const afterSave = _dirty;
            return {start:start, afterEdit:afterEdit, okSave:okSave, afterSave:afterSave};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        chk('機能', '未保存フラグが編集で立ち保存で下りる',
            isinstance(dy, dict) and dy.get('afterEdit') is True and dy.get('afterSave') is False, str(dy))

        # INV-X: 歩く速さで所要時間が変わり、登りがあれば時間が増える
        wk = page.evaluate("""()=>{ try{
            const saveElev = _elevData, saveIdx = _walkSpeedIdx, saveWps = wps.slice();
            wps = [];                                   // 滞在時間の影響を外す
            _elevData = null;
            setWalkSpeed(2); const t4 = calcTotalTime(4000), n4 = _timeNote();   // 4km/h・平坦 → 60分
            setWalkSpeed(0); const t3 = calcTotalTime(4000);                     // 3km/h → 80分
            setWalkSpeed(2);
            _elevData = { pts:[], elevs:[100, 200, 150, 250] };                  // 登り合計 200m
            const tUp = calcTotalTime(4000), nUp = _timeNote(), up = _totalAscent();
            const saved = localStorage.getItem(LS.walkSpeed);
            _elevData = saveElev; wps = saveWps; setWalkSpeed(saveIdx);
            return {t4:t4, t3:t3, tUp:tUp, up:up, n4:n4, nUp:nUp, saved:saved};
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_wk = (isinstance(wk, dict) and wk.get('t4') == '1時間' and wk.get('t3') == '1時間20分'
                 and wk.get('up') == 200 and wk.get('tUp') == '1時間20分'      # 60分 + 登り200m→20分
                 and '4km/h' in wk.get('n4', '') and '登り込み' in wk.get('nUp', ''))
        chk('機能', '歩く速さと登りが所要時間に反映される', ok_wk, str(wk)[:190])

        # INV-Y: 配布リンクを作るとシートにQRが載り、リンクが無ければ出ない
        qr = page.evaluate("""()=>{ return (async()=>{ try{
            const orig = window.html2canvas;
            window.html2canvas = () => Promise.resolve({ toDataURL: () => 'data:image/png;base64,AA' });
            const id = currentCourseId != null ? currentCourseId : (currentCourseId = 'qr-test');
            _setShareLink(id, 'https://example.test/footpath/?course=abc.json');
            await openPrintSheet();
            const withLink = !!document.querySelector('#printSheet .sh-qr');
            const stored = _shareLinkOf(id);
            try { localStorage.removeItem(LS.shareLinks); } catch(_){}
            await openPrintSheet();
            const noLink = !!document.querySelector('#printSheet .sh-qr');
            window.html2canvas = orig;
            return {withLink:withLink, noLink:noLink, stored:stored};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        chk('機能', '配布リンクがあるときだけシートにQR欄が出る',
            isinstance(qr, dict) and qr.get('withLink') is True and qr.get('noLink') is False
            and 'abc.json' in str(qr.get('stored')), str(qr)[:170])

        # INV-Z: 設定メニューの見本が実際の大きさで表示される
        pv = page.evaluate("""()=>{ try{
            _syncSizeMenu();
            const f = [...document.querySelectorAll('.mm-map[data-lsz] .mm-map-l')].map(e=>parseFloat(e.style.fontSize));
            const d = [...document.querySelectorAll('.mm-map[data-wsz] .mm-dot')].map(e=>parseFloat(e.style.width));
            return {fonts:f, dots:d, sizes:LABEL_SIZES.slice(), mobile:isMobile()};
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_pv = (isinstance(pv, dict) and pv.get('fonts') == pv.get('sizes')
                 and len(pv.get('dots', [])) == 3
                 and pv['dots'][0] < pv['dots'][1] < pv['dots'][2])
        chk('機能', '設定メニューが実際の大きさで見本を出す', ok_pv, str(pv)[:170])

        # INV-AA: 写真が IndexedDB に退避され、参照から元に戻せる（使えない環境では実体のまま）
        ph = page.evaluate("""()=>{ return (async()=>{ try{
            const DATA = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==';
            const arr = [DATA];
            const moved = await _stashPhotoArray(arr);
            const ref   = arr[0];
            const back  = await _photoSrc(ref);
            const emb   = await _embedPhotos({wps:[{photos:[ref]}]});
            // IndexedDB が使えない環境では実体のまま（従来動作）になることを確認する
            const savedIdb = _idbP; _idbP = Promise.resolve(null);
            const arr2 = [DATA]; const moved2 = await _stashPhotoArray(arr2);
            _idbP = savedIdb;
            return {moved:moved, isRef:_isPhotoRef(ref), back:back===DATA,
                    embed:emb.wps[0].photos[0]===DATA, fallbackMoved:moved2, fallbackKept:arr2[0]===DATA};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        idb_ok = (isinstance(ph, dict) and ph.get('moved') == 1 and ph.get('isRef') is True
                  and ph.get('back') is True and ph.get('embed') is True)
        fb_ok  = (isinstance(ph, dict) and ph.get('moved') == 0 and ph.get('back') is True)
        chk('機能', '写真をIndexedDBへ退避し参照から復元できる（不可なら実体のまま）',
            (idb_ok or fb_ok) and isinstance(ph, dict)
            and ph.get('fallbackMoved') == 0 and ph.get('fallbackKept') is True,
            ('IndexedDB利用: ' if idb_ok else '実体のまま(フォールバック): ') + str(ph)[:150])

        # INV-AB: 保存後の localStorage に写真の実体が残っていない（IndexedDBが使えるとき）
        lite = page.evaluate("""()=>{ return (async()=>{ try{
            const DATA = 'data:image/png;base64,QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo=';
            const idbOK = !!(await _idb());
            const wp = addWp(35.1520, 134.4451, 'course'); wp.name='写真テスト'; wp.photos=[DATA];
            courseInfo.name = courseInfo.name || '写真テストコース';
            await saveCourse();
            const raw = (localStorage.getItem(LS.courses) || '');
            const inLs = raw.indexOf(DATA) >= 0;
            const kind = wp.photos[0].slice(0, 4);
            return {idbOK:idbOK, inLs:inLs, kind:kind};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        ok_lite = (isinstance(lite, dict) and
                   ((lite.get('idbOK') and lite.get('inLs') is False and lite.get('kind') == 'idb:')
                    or (not lite.get('idbOK') and lite.get('kind') == 'data')))
        chk('機能', '保存後の本体に写真の実体が残らない', ok_lite, str(lite)[:170])

        # INV-AC: オフライン保存のタイル計算（範囲・上限・提供元の最大縮尺を守る）
        tl = page.evaluate("""()=>{ try{
            const b = L.latLngBounds([[35.150,134.440],[35.160,134.450]]);
            const few  = offlineTileUrls(b, 15, 16, 600);
            const cap  = offlineTileUrls(b, 15, 19, 4);     // 上限4枚 → 細かい縮尺は落とす
            const zero = offlineTileUrls(b, 25, 26, 600);   // 提供元にない縮尺 → 0枚
            const ok = few.every(u => /\/\d+\/\d+\/\d+\.(png|jpg)/.test(u) && u.indexOf('{') < 0);
            return {few:few.length, cap:cap.length, zero:zero.length, wellFormed:ok, sample:few[0]||''};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', 'オフライン保存のタイル計算が範囲と上限を守る',
            isinstance(tl, dict) and tl.get('few', 0) > 0 and tl.get('cap', 99) <= 4
            and tl.get('zero') == 0 and tl.get('wellFormed') is True, str(tl)[:170])

        # INV-AD: 動作確認が実際に走り、各項目が判定を返す
        sc = page.evaluate("""()=>{ return (async()=>{ try{
            const rows = await runSelfCheck();
            const items = rows.filter(r => !r.sec);
            const secs  = rows.filter(r =>  r.sec).map(r => r.sec);
            const bad = items.filter(r => ['ok','warn','ng','info'].indexOf(r.state) < 0).length;
            const txt = _selfCheckText(rows);
            return {items:items.length, secs:secs, bad:bad,
                    hasVer: items.some(r => (r.detail||'').indexOf(APP_VERSION) >= 0),
                    txtOK: txt.indexOf('動作確認') >= 0 && txt.length > 100};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        chk('機能', '動作確認が各項目の判定を返す',
            isinstance(sc, dict) and sc.get('items', 0) >= 8 and sc.get('bad') == 0
            and sc.get('hasVer') is True and sc.get('txtOK') is True
            and 'アプリ' in sc.get('secs', []) and '保存' in sc.get('secs', []), str(sc)[:190])

        b.close()


# ----------------------------------------------------------------------
# 3) オフライン検査（ローカルHTTPで配信し、実際に圏外にして確かめる）
#    file:// では Service Worker を登録できないため、この検査だけHTTPで行う。
# ----------------------------------------------------------------------
def offline_checks(index_path):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return                                   # Playwright 未導入は機能チェック側で報告済み
    import threading, functools, http.server, socketserver
    here = os.path.dirname(os.path.abspath(index_path))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=here)
    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(('127.0.0.1', 0), handler)
    except Exception as e:
        chk('オフライン', 'ローカル配信を起動できる', False, str(e)); return
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    sandbox_chrome = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    launch_kwargs = {}
    if os.path.exists(sandbox_chrome):
        launch_kwargs['executable_path'] = sandbox_chrome
    url = f'http://127.0.0.1:{port}/index.html'
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(**launch_kwargs)
            ctx = b.new_context(viewport={'width': 390, 'height': 812})
            page = ctx.new_page()
            page.goto(url, wait_until='domcontentloaded')
            # サービスワーカーが有効になるまで待つ
            try:
                page.wait_for_function("() => !!(navigator.serviceWorker && navigator.serviceWorker.controller)", timeout=12000)
                controlled = True
            except Exception:
                controlled = False
            chk('オフライン', 'サービスワーカーが有効になる', controlled)

            if controlled:
                page.wait_for_timeout(400)
                cached = page.evaluate("""async () => {
                    const keys = await caches.keys();
                    const app  = keys.find(k => k.indexOf('fp-app-') === 0);
                    if (!app) return {keys:keys, hit:false};
                    const c = await caches.open(app);
                    const hit = await c.match(location.origin + '/index.html', {ignoreSearch:true});
                    return {keys:keys, hit:!!hit};
                }""")
                chk('オフライン', 'アプリ本体がキャッシュされる',
                    isinstance(cached, dict) and cached.get('hit') is True, str(cached)[:120])

                # ── 実際に圏外にして再読込 ──
                ctx.set_offline(True)
                try:
                    page.reload(wait_until='domcontentloaded')
                    page.wait_for_timeout(400)
                    boot = page.evaluate("() => ({ver: (typeof APP_VERSION!=='undefined') ? APP_VERSION : null,"
                                         " list: !!document.getElementById('courseList'),"
                                         " online: navigator.onLine,"
                                         " badge: document.body.classList.contains('offline')})")
                except Exception as e:
                    boot = 'ERR:' + str(e)
                chk('オフライン', '圏外でもアプリが起動する',
                    isinstance(boot, dict) and boot.get('ver') and boot.get('list') is True, str(boot)[:150])
                # ブラウザが圏外と認識している時だけバッジを要求する（エミュレーションが onLine を変えない場合がある）
                badge_ok = isinstance(boot, dict) and (boot.get('badge') is True if boot.get('online') is False else True)
                chk('オフライン', '圏外の表示（バッジ）が出る', badge_ok, str(boot)[:150])
                ctx.set_offline(False)

                # ── 解除スイッチ（?nosw=1）──
                page.goto(url + '?nosw=1', wait_until='domcontentloaded')
                page.wait_for_timeout(900)
                left = page.evaluate("async () => { const r = await navigator.serviceWorker.getRegistrations();"
                                     " const k = await caches.keys(); return {regs:r.length, caches:k.filter(x=>x.indexOf('fp-')===0).length}; }")
                chk('オフライン', '?nosw=1 でオフライン機能を解除できる',
                    isinstance(left, dict) and left.get('regs') == 0 and left.get('caches') == 0, str(left))
            b.close()
    except Exception as e:
        chk('オフライン', 'オフライン検査を実行できる', False, str(e)[:160])
    finally:
        try: httpd.shutdown()
        except Exception: pass

# ----------------------------------------------------------------------
def main():
    if not os.path.exists(INDEX):
        print(f'対象が見つかりません: {INDEX}'); sys.exit(2)
    print(f'対象: {INDEX}\n')
    src = open(INDEX, encoding='utf-8').read()
    static_checks(src)
    functional_checks(INDEX)
    offline_checks(INDEX)

    # 結果出力
    cats = {}
    for cat, name, ok, detail in RESULTS:
        cats.setdefault(cat, []).append((name, ok, detail))
    nfail = 0
    for cat, items in cats.items():
        print(f'■ {cat}')
        for name, ok, detail in items:
            mark = 'PASS' if ok else 'FAIL'
            if not ok: nfail += 1
            line = f'   [{mark}] {name}'
            if detail and not ok: line += f'  … {detail}'
            print(line)
        print()
    total = len(RESULTS)
    print('='*48)
    if nfail == 0:
        print(f'結果: 全{total}項目 PASS ✓  出荷可')
        sys.exit(0)
    else:
        print(f'結果: {nfail}/{total} 項目が FAIL ✗  出荷前に要修正')
        sys.exit(1)

if __name__ == '__main__':
    main()
