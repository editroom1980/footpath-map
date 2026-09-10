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
    chk('静的', 'ラベル位置が○（かシール）の大きさに追従', '_wpIconSize(wp)[1] / 2 + 4' in src and 'function _wpIconSize(wp){ return (_stickerOn() &&' in src)
    _mmsrc = src[src.index('id="mobileMenuSheet"'):]          # v126: PCの右上にも同じ属性があるので、スマホメニュー以降だけ数える
    chk('静的', 'スマホメニューに文字サイズ5段階', len(re.findall(r'data-lsz="\d"', _mmsrc)) == 5)
    chk('静的', 'スマホメニューに○サイズ3段階', len(re.findall(r'data-wsz="\d"', _mmsrc)) == 3)
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
    chk('静的', 'PC・スマホ両方から「配る」でGPXに届く',
        "shareExit('gpx')" in src and 'class="hbtn hbtn-share"' in src and 'class="mob-share tap"' in src)
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
    chk('静的', 'PC・スマホ両方から「配る」で配布シートに届く',
        "shareExit('sheet')" in src and 'class="hbtn hbtn-share"' in src and 'class="mob-share tap"' in src)
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
    chk('静的', '動作確認は普段の画面に出さない（?check=1 のみ）',
        'id="s1CheckLink"' not in src and 'openSelfCheck()' not in src.split('<script')[0],
        '起動画面・メニューからは外し、不具合調査用に残す')
    chk('静的', '結果をコピーできる', 'function copySelfCheck' in src and 'function _selfCheckText' in src)
    chk('静的', '圏外での確認手順を載せている', '機内モード' in src)
    # --- v92: 新しい版のお知らせ（?v= の手作業をなくす）---
    ver_path = os.path.join(os.path.dirname(os.path.abspath(INDEX)), 'version.json')
    ver_txt = open(ver_path, encoding='utf-8').read() if os.path.exists(ver_path) else ''
    m_app = re.search(r"const APP_VERSION = '([^']+)'", src)
    m_ver = re.search(r'"version"\s*:\s*"([^"]+)"', ver_txt)
    chk('静的', 'version.json がある', bool(ver_txt), ver_path)
    chk('静的', 'version.json と APP_VERSION が一致',
        bool(m_app and m_ver and m_app.group(1) == m_ver.group(1)),
        f'app={m_app.group(1) if m_app else None} / json={m_ver.group(1) if m_ver else None}')
    chk('静的', '更新チェック checkForUpdate 存在', 'async function checkForUpdate' in src)
    chk('静的', '更新の案内バー showUpdateBar 存在', 'function showUpdateBar' in src)
    chk('静的', '起動時に更新を確認する', 'watchVersion();' in src)
    chk('静的', '更新の案内は一覧画面だけに出す',
        'function _onCourseList' in src and 'if (!_onCourseList()) return;' in src)
    chk('静的', '一覧に戻ったら案内を出し直す', 'showUpdateBarIfPending' in src)
    # --- v93: 経路サーバの待避 ---
    chk('静的', '経路サーバ一覧 ROUTERS 維持', 'const ROUTERS' in src)
    chk('静的', '予備サーバが用意されている',
        len(re.findall(r"base:\s*'https://", src)) >= 2,
        f"台数={len(re.findall(chr(98)+chr(97)+chr(115)+chr(101)+chr(58), src))}")
    chk('静的', '1台ずつ試す _tryRouter 存在', 'async function _tryRouter' in src)
    chk('静的', '全滅時のクールダウン ROUTER_COOLDOWN_MS 維持', 'const ROUTER_COOLDOWN_MS' in src)
    chk('静的', '経路サーバへ一斉に投げない（同時数の上限）',
        'const ROUTER_MAX_PARALLEL' in src and 'function _routeSlot' in src and 'await _routeSlot();' in src)
    chk('静的', 'だめだったサーバは区間ごとに試さない',
        'let   _routerDead' in src and 'if (Date.now() < (_routerDead[i] || 0)) continue;' in src)
    chk('静的', '経路URLの直書きは一覧の1か所だけ',
        len(re.findall(r'router\.project-osrm\.org', src)) == 1,
        f"直書き={len(re.findall(r'router.project-osrm.org', src))}箇所")
    chk('静的', 'なぞりのスナップも同じサーバを使う', '(ROUTERS[_routerIdx] || ROUTERS[0]).base' in src)
    chk('静的', '動作確認が全サーバを調べる', 'routerProbes' in src)
    # --- v94: ホームページへの埋め込み ---
    chk('静的', '埋め込みパラメータ embed=1 を読む', "p.get('embed') === '1'" in src)
    chk('静的', '埋め込み表示のCSS（地図だけ見せる）', 'body.embed #hdr' in src and 'body.embed #sidebar' in src)
    chk('静的', '埋め込みの帯 _fillEmbedBar 存在', 'function _fillEmbedBar' in src)
    chk('静的', '「大きな地図で開く」がある', '大きな地図で開く' in src)
    chk('静的', '共有ダイアログに埋め込みコード',
        'shEmbed' in src and '<iframe src=' in src and 'shCopyEmbed' in src)
    # --- v95: コースの難易度 ---
    chk('静的', '難易度の段階 DIFFICULTY 維持', 'const DIFFICULTY' in src)
    chk('静的', '難易度の判定 courseDifficulty 存在', 'function courseDifficulty' in src)
    chk('静的', 'サイドバーに難易度を出す', 'id="diffDisp"' in src and 'function _renderDifficulty' in src)
    chk('静的', '配布シートに難易度を載せる', "'難易度<b style=\"color:'" in src or '難易度<b' in src)
    # --- v96: GPX読み込み ---
    chk('静的', 'GPX読み込み parseGpx 存在', 'function parseGpx' in src)
    chk('静的', '取り込み口が GPX も受け付ける', 'accept=".json,.gpx' in src and 'コース・GPX・発見' in src)   # v149: 文言を平易に
    chk('静的', '軌跡の間引き _thinPoints 存在', 'function _thinPoints' in src)
    chk('静的', 'GPXは道順が引き直しになることを伝える', '通り道の点（道順の細かい指定）' in src)
    chk('静的', 'スポットがあるGPXは軌跡を取り込まない（二重防止）',
        'const hadWpt = wps.length > 0;' in src and 'hadWpt ? [] : _thinPoints' in src)
    chk('静的', '取り込み点数の上限 GPX_MAX_TRKPTS 維持', 'const GPX_MAX_TRKPTS' in src)
    # --- v97: 現在地追従 ---
    chk('静的', '追従の切替 toggleFollowMode 存在', 'function toggleFollowMode' in src)
    chk('静的', '追従の停止 stopFollowMode 存在', 'function stopFollowMode' in src)
    chk('静的', 'watchPosition を使う', 'navigator.geolocation.watchPosition' in src)
    chk('静的', '一覧に戻ると追従を止める（電池）', 'if (_followOn) stopFollowMode(true);' in src)
    chk('静的', '小刻みな揺れで動かさない FOLLOW_MIN_MOVE_M', 'const FOLLOW_MIN_MOVE_M' in src)
    chk('静的', '追従中も利用者の拡大縮小を邪魔しない（2回目以降はpanTo）',
        'leafMap.panTo([lat, lng], {animate:true})' in src)
    chk('静的', 'スマホメニューに「現在地を追う」', 'mmSwFollow' in src and '現在地を追う' in src)
    # --- v98: スポットの色（見分けやすさ・定義の一本化）---
    wt_colors = re.findall(r"c:'(#[0-9A-Fa-f]{6})'", src)
    chk('静的', 'スポットの色に重複がない', len(wt_colors) == len(set(c.upper() for c in wt_colors)),
        f'{len(wt_colors)}色 / 重複={[c for c in wt_colors if wt_colors.count(c) > 1]}')
    chk('静的', '色の定義は WT の1か所だけ（CSSに直書きしない）',
        '.wp-tt-course{background:' not in src and 'function _injectWpStyles' in src)
    chk('静的', '画像保存の色も WT から作る', "_colors['wp-tt-' + t.v] = t.c" in src)
    # --- v101: 配色の基準（白文字を載せる面は 4.5:1 以上）---
    def _white_contrast(hexv):
        """白い文字を載せたときの読みやすさの差を返す（大きいほど読みやすい）"""
        h = hexv.lstrip('#')
        ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        lum = 0.2126 * f(ch[0]) + 0.7152 * f(ch[1]) + 0.0722 * f(ch[2])
        return round(1.05 / (lum + 0.05), 2)

    root_vars = dict(re.findall(r"--(brand|brand-lite|ok):(#[0-9A-Fa-f]{6})", src))
    js_colors = dict(re.findall(r"(brand|ok):'(#[0-9A-Fa-f]{6})'", src))
    chk('静的', '配色の基準が :root にある', len(root_vars) == 3, str(root_vars))
    chk('静的', 'CSSの色とJSの色が一致している（COLOR と :root）',
        root_vars.get('brand', '').upper() == js_colors.get('brand', 'x').upper()
        and root_vars.get('ok', '').upper() == js_colors.get('ok', 'y').upper(),
        f'CSS={root_vars} JS={js_colors}')
    ng_face = {k: _white_contrast(v) for k, v in root_vars.items() if _white_contrast(v) < 4.5}
    chk('静的', '白文字を載せる色が読みやすさ 4.5:1 以上', not ng_face,
        str({k: _white_contrast(v) for k, v in root_vars.items()}))
    ng_wt = {c: _white_contrast(c) for c in wt_colors if _white_contrast(c) < 4.5}
    chk('静的', 'スポットの色も 4.5:1 以上（○の中の記号が白のため）', not ng_wt, str(ng_wt))
    chk('静的', '古い操作色を直書きしていない',
        '#F2670E' not in src and '#C4703A' not in src, 'F2670E/C4703A が残っている')
    # --- v102: 文字の大きさと濃さ ---
    faint = [c for c in ['#BDB5A8', '#A8A29E', '#C4BEB8', '#B0A99F', '#9A8070', '#F97316',
                         '#FB8B3E', 'color:#888', 'color:#aaa']
             if c in src]
    chk('静的', '読みにくい薄い文字色が残っていない', not faint, str(faint))
    chk('静的', '補足の文字色を1か所にまとめている', '--t-sub:' in src, '')
    # --- v103: 地図の上の見え方（白いふち）---
    chk('静的', 'ルート線の白いふちがある（表示専用）',
        'routeCasing' in src and 'const ROUTE_CASING_ADD' in src)
    chk('静的', '白いふちは当たり判定に使わない', "interactive:false, renderer: canvasRenderer}).addTo(leafMap)" in src)
    chk('静的', '白いふちも後片付けする', 'if (routeCasing) { if(leafMap) leafMap.removeLayer(routeCasing); routeCasing=null; }' in src)
    chk('静的', 'スポットの○の白いふちがはっきりしている', 'border:2.5px solid #fff' in src)
    # --- v112: 進行方向の三角（一定間隔）---
    chk('静的', '進行方向の三角を作る仕組みがある',
        'function _buildDirMarks' in src and 'const DIR_EVERY_DASHES' in src)
    chk('静的', 'スポットの手前にも三角を出す', 'if (dw - clear > 0) wpCuts.push(dw - clear);' in src)
    # --- v118: スマホでコースの説明を書ける（UI点検 11）---
    chk('静的', 'スマホにコース説明の入力画面がある',
        'id="descSheet"' in src and 'function openDescSheet' in src)
    chk('静的', '説明の出どころは1つのまま（#iDesc を読み書き）',
        "src.value = ta.value; _markDirty();" in src)   # v148: 未保存フラグは _markDirty() 経由
    chk('静的', 'メニューに「書かれています／未記入」を出す', 'function _syncDescState' in src)
    chk('静的', '説明を書き換えたら未保存になる', "_dsc.addEventListener('input'" in src)
    # --- v119: 配布リンクに道順を同梱（開くときに経路サーバを呼ばない）---
    chk('静的', '保存データに区間ごとの道順が入る', 'routes:  _routesInUse(),' in src and 'function _routesInUse' in src)
    chk('静的', '読み込み時に道順を先に入れる', "if (data.routes && typeof data.routes === 'object')" in src)
    chk('静的', '直線に逃げた区間は覚えない・保存しない',
        's.fallback = true' in src and 'if (!coords.fallback) segCache[key] = coords;' in src and 'c.fallback' in src)
    chk('静的', '区間キーの式は1か所（_segKey）', 'function _segKey' in src and src.count('toFixed(6)};${') == 1)
    # --- v120: 閲覧中は編集の操作を受け付けない（ロードマップ 段階0-2）---
    chk('静的', '閲覧中に編集の操作を隠すCSSがある', 'body.viewing #tbar .ed' in src and 'function _applyViewLock' in src)
    chk('静的', '地図タップ・編集画面・取消・全消去に閲覧中の門がある',
        all(x in src for x in ["function onMapClick(e) {\n  if (viewMode) return;", "function openModal(id) {\n  if (viewMode) return;",
                               "function undoLast() {\n  if (viewMode) return;", "function redoAction() {\n  if (viewMode) return;",
                               "function clearAll() {\n  if (viewMode) return;", "row.draggable  = !viewMode;"]))
    chk('静的', 'メニューの編集項目に印がある（7か所以上）', src.count('data-edit="1"') >= 7)
    chk('静的', '歩く人への案内がある', 'id="walkTip"' in src and 'function maybeShowWalkTip' in src)
    # --- v121: 消える前に知らせる（ロードマップ 段階0-3）---
    chk('静的', 'バックアップの記録キーが LS にある',
        all(k in src for k in ["backupAt:", "saveCount:", "firstSaveAt:", "homeTipSeen:"]))
    chk('静的', '保存と書き出しで記録を更新する', '_noteSaved(quiet);' in src and '_noteBackup();' in src)
    chk('静的', '一覧を開くたびに状態を出す', 'renderBackupStatus(); renderHomeTip();' in src)
    chk('静的', 'iPhone のホーム画面追加の案内がある', 'id="homeTip"' in src and 'function _isIosBrowserTab' in src)
    # --- v122: 読み上げ名と拡大禁止の解除（ロードマップ 段階0-4）---
    import html as _html
    _miss = []
    for _m in re.finditer(r'<button\b([^>]*)>(.*?)</button>', src, re.S):
        _t = _html.unescape(re.sub(r'\$\{[^}]*\}', '', re.sub(r'<[^>]+>', '', _m.group(2)))).strip()
        if not _t and 'aria-label' not in _m.group(1): _miss.append(_m.group(1)[:50])
    chk('静的', '文字の無いボタンすべてに読み上げ名がある（HTMLとJSの雛形）', not _miss, str(_miss)[:160])
    chk('静的', 'ページ全体の拡大は止める（ホーム画面アプリでボタンがはみ出したため・v135）。文字の大きさはアプリ内の設定で',
        'maximum-scale=1.0, user-scalable=no, viewport-fit=cover' in src and 'html,body{touch-action:manipulation;' in src and 'function _unzoomPage' in src)
    chk('静的', '地図の上だけは指の操作を Leaflet に渡す', '#map{touch-action:none}' in src)
    chk('静的', '出発点・到着点のつなぎ区間も同梱する', 'if (startWp && startWp.id !== rw[0].id) pairs.push' in src)
    chk('静的', '近すぎる「ふつうの三角」を飛ばすきまりがある', 'const DIR_MIN_DASHES' in src)
    chk('静的', '置き場所と向きは線に沿った距離で決める（点の細かさに左右されない）', 'DIR_LOOK_PX' in src)
    chk('静的', 'スポットの○の下に隠れる位置は避ける', 'DIR_AVOID_PX' in src)
    chk('静的', '三角も当たり判定に使わず、後片付けもする',
        'interactive:false, renderer: canvasRenderer}).addTo(leafMap);' in src
        and 'if (routeDirs)    { if(leafMap) leafMap.removeLayer(routeDirs);' in src)
    chk('静的', '配布シートの凡例に進行方向の説明がある', '歩くコース（三角の向きに歩く）' in src)
    # --- v123: 「配る」を1枚に（ロードマップ 段階1-1）---
    chk('静的', '配るシートがある（開閉・出口・載る情報）',
        'id="shareSheet"' in src and 'function openShareSheet' in src and 'function shareExit' in src
        and 'function renderShareInfo' in src)
    chk('静的', '編集画面の上バーに「配る」がある（PC・スマホとも）',
        'class="mob-share tap" onclick="openShareSheet()">配る' in src
        and 'class="hbtn hbtn-share" onclick="openShareSheet()"' in src)
    chk('静的', '4つの出口がそれぞれ既存の機能を呼ぶ（中身は変えない）',
        all(f'shareExit(\'{k}\')' in src for k in ('image', 'sheet', 'link', 'gpx'))
        and "if (kind === 'image') saveMapAsImage();" in src and "else if (kind === 'sheet') openPrintSheet();" in src
        and "else if (kind === 'gpx') exportGpx();" in src and "closeShareSheet(); openShareDialog(c); return;" in src)
    chk('静的', 'リンクは未保存なら先に保存してから作る',
        'if (_dirty || currentCourseId == null) { const ok = await saveCourse(); if (!ok) return; }' in src)
    chk('静的', '載る情報＝説明の有無・写真つきスポット数・スタンプ対象数',
        'id="ssDesc"' in src and 'id="ssPhoto"' in src and 'id="ssStamp"' in src
        and "Array.isArray(w.photos) && w.photos.length > 0" in src)
    chk('静的', '歩く人の画面と埋め込みには「配る」を出さない',
        'body.viewonly .mob-share, body.embed .mob-share{display:none!important}' in src)
    # --- v124: 棚の「…」が枠からはみ出さない ---
    chk('静的', '棚の距離時間だけが縮む側で、入りきらない時は折り返す',
        '#mobileShelf .mob-stats{flex:1 1 auto;min-width:0;flex-wrap:wrap' in src)
    # --- v125: スマホのメニューを1画面に（ロードマップ 段階1-2）---
    _mm = src[src.index('id="mobileMenuSheet"'):src.index('id="mmSub"')]
    chk('静的', 'メニューの順番がコース→歩くとき→地図の見せ方→上級者向け',
        _mm.index('mm-sec">コース<') < _mm.index('mm-sec">歩くとき<') < _mm.index('mm-sec">地図の見せ方<') < _mm.index('>上級者向け<span>'))
    chk('静的', '書き出し（画像・配布シート・GPX）はメニューから「配る」へ移した',
        all(x not in src for x in ['closeMobileMenu();saveMapAsImage()', 'closeMobileMenu();openPrintSheet()', 'closeMobileMenu();exportGpx()']))
    chk('静的', '選択肢は2階層目にあり、開くたびに1階層目・畳んだ状態に戻る',
        'function openMmSub' in src and 'function closeMmSub' in src and 'closeMmSub(); toggleMmAdv(false);' in src
        and 'id="mmSub" hidden' in src and '#mmAdv{display:none}' in src)
    chk('静的', '文字の大きさは3段階だけ見せる（極大・最大は選んである時だけ）',
        ".mm-map[data-lsz='3']:not(.on),.mm-map[data-lsz='4']:not(.on){display:none}" in src)
    chk('静的', '「›」の右に今の設定を出す', 'function _syncMmValues' in src and 'id="mmValMap"' in src and 'id="mmValSize"' in src)
    # --- v128: スポットを置くのを1タップに（ロードマップ 段階1-4）---
    _omc = src[src.index('function onMapClick(e) {'):src.index('function onMapClick(e) {') + 1200]
    chk('静的', '地図タップで即「コースポイント」として置く（選択画面も編集画面も開かない）',
        "addWp(e.latlng.lat, e.latlng.lng, 'course');" in _omc and 'showWpTypePicker(e.latlng' not in _omc and 'openModal(' not in _omc)
    chk('静的', '編集画面の種別は「よく使う4つを大きく、残りは畳む」',
        "const TYPE_BIG = ['course', 'view', 'history', 'shop']" in src and 'id="mTypeChips"' in src and 'function _renderTypeChips' in src
        and '#mType{display:none}' in src)
    chk('静的', '選べる種類の出どころは _buildTypeOptions のまま（チップは select を読む）',
        "const cur = sel.value, opts = [...sel.options].map(o => o.value);" in src and 'function _buildTypeOptions' in src)
    chk('静的', '最初の案内が「種類と名前はあとから」を伝える', '種類と名前は、○を押してあとから決められます' in src)
    # --- v153: 画面の骨組みの検査（閉じ忘れを二度と出さない）＋小さな手直し ---
    _a = src.index('<body'); _b = src.index('<script src=', _a)
    _mk = re.sub(r'<script\b.*?</script>', '', src[_a:_b], flags=re.S)
    _unbal = [t for t in ('div', 'span', 'button', 'label', 'details', 'ul', 'li', 'select', 'textarea') if len(re.findall(r'<' + t + r'\b', _mk)) != _mk.count('</' + t + '>')]
    chk('静的', '画面の骨組み（body の HTML）でタグの開きと閉じが釣り合っている', not _unbal, str(_unbal))
    chk('静的', 'スマホでは「歩く人の見え方」の札を上の帯の下に出す。歩く人のメニューの「コースの情報」は件数でなく「見る」',
        '@media (max-width:768px){#viewBadge{top:72px}}' in src and "v('mmInfo', viewMode ? (_courseInfoCount() ? '見る' : 'なし')" in src)
    # --- v152: 手数を減らす④（メニューの「コースのことを書く」にまとめる）---
    chk('静的', 'スマホのメニュー：説明・情報・心得（書く側）は2階層目「コースのことを書く」に。歩く人には心得・情報の行を残す',
        'data-sub="write"' in src and "write:'コースのことを書く'" in src and 'id="mmKokoroeRow"' in src and 'id="mmInfoRow"' in src
        and src.index('data-sub="write"') < src.index('id="mmDescState"') and "onclick=\"openMmSub('write')\"" in src)
    # --- v151: 閉じ忘れの修正（v148〜v150 で歩く人のカード・操作ガイドが見えなくなっていた）---
    _mo = src[src.index('<div id="mOver" class="m-over">'):src.index('<!-- Via point context menu (singleton) -->')]
    chk('静的', 'スポットの編集画面（#mOver）の div の開きと閉じが釣り合っている（後ろの要素を巻き込まない）',
        len(re.findall(r'<div\b', _mo)) == _mo.count('</div>'), f"{len(re.findall(r'<div\\b', _mo))} vs {_mo.count('</div>')}")
    # --- v150: 手数を減らす③（配布用リンクの画面を3手順に・置き場所へ1回で・操作ガイドを今の画面に）---
    chk('静的', '配布用リンクの画面は 書き出す→置く→配る の3手順。埋め込みは畳む。GitHub Pages なら置き場所（アップロード画面）を開くボタン',
        'id="shGh"' in src and 'function _ghUploadUrlFor' in src and "<details class=\"sd-more\">" in src and src.index('class="sd-more"') < src.index('id="shEmbed"'))
    chk('静的', '操作ガイドが今の画面に合っている（線を引っぱる・自動保存・歩く人の画面）',
        '赤い線を指（マウス）で引っぱる' in src and '保存は自動です' in src and '<h3>🚶 歩く人の画面でできること（配布リンク）</h3>' in src and '「通り道」を選んで地図をクリック' not in src)
    # --- v149: 手数を減らす②（新しいコースは名前だけ・道具とカードに文字・案内に線の引っぱり）---
    chk('静的', '新しいコースはコース名だけ必須。エリアが空なら現在地、取れなければ今の地図の場所。スタート・ゴール地点の欄は無い',
        "if (!name) { alert('コース名を入れてください。');" in src and 'function _herePos' in src and 'const c = area ? await geocode(area) : await _herePos();' in src
        and 'id="s1Start"' not in src and 'id="s1Goal"' not in src)
    chk('静的', 'スマホの下の道具と一覧のカードのボタンに文字が付いている（アイコンだけにしない）',
        src.count('class="mob-mode-l"') == 2 and src.count('class="cc-act-l"') == 3 and 'ファイルから読み込む（コース・GPX・発見）' in src)
    chk('静的', '最初の案内に「赤い線を引っぱると道順が変わる」がある', '道順を変えたいときは、赤い線を指で引っぱります。' in src)
    # --- v148: 手数を減らす（自動保存・道具の整理・スポット編集の畳み込み）---
    chk('静的', '未保存フラグは _markDirty() だけが立て、自動保存を予約する（直接 _dirty = true は無い）',
        src.count('_dirty = true') == 1 and 'function _markDirty(){ _dirty = true; scheduleAutoSave(); }' in src and 'const AUTOSAVE_MS = 1500;' in src and "saveCourse({quiet:true})" in src)
    chk('静的', '保存ボタンは状態表示（保存済み／保存中…／保存できず）になり、一覧に戻るときは先に自動保存する',
        "st === 'saved' ? '保存済み' : st === 'saving' ? '保存中…'" in src and 'await autoSaveNow(); }   // 自動で保存してから戻る' in src and '.hbtn-save.is-saved{' in src)
    chk('静的', 'スマホの下の道具は「なぞる」「スポット」だけ。通り道の点・道を描くは上級者向けへ（id は据え置き）',
        src.count('class="mob-mode ') == 2 and 'id="mobileViaBtn" onclick="setMode(\'via\');closeMobileMenu()' in src and 'id="mobileCustomBtn" onclick="toggleCustomMode();_syncMobileMenu()"' in src
        and src.index('id="mmAdv"') < src.index('id="mobileViaBtn"'))
    chk('静的', 'スポットの編集は 種別→名前→写真→説明 の順で、2行目・電話・滞在・道順・名札の位置は「くわしい設定」に畳む',
        src.index('id="mName"') < src.index('id="mPhotoStrip"') < src.index('id="mDesc2"') < src.index('<details id="mMore"') < src.index('id="mTel"') and "_more.open = !!(" in src)
    # --- v147: 改変の可否（noEdit）＋ゴールの1枚（F7）---
    chk('静的', '改変の可否は配布ファイル（shared:true）にだけ効き、読み込みで断る。バックアップは常に取り込める',
        'function _isLockedShare' in src and "data.shared === true && data.noEdit === true" in src and 'Object.assign({}, course, {shared:true})' in src
        and 'noEdit:   courseInfo.noEdit ? true : undefined' in src and 'noEdit: data.noEdit === true' in src and 'id="ssEdit"' in src)
    chk('静的', 'ゴールの1枚：帯を押すと記念写真、コース名・日付・距離・スタンプを焼き込み、共有か保存',
        'function openGoalCard' in src and 'function _goalCompose' in src and "_nb.classList.contains('done')) { openGoalCard(); return; }" in src and 'id="goalSheet"' in src and 'id="mmGoalRow"' in src and 'id="btnGoal"' in src)
    # --- v146: 配る前の確認（F9）＋ WebKit の検査 ---
    chk('静的', '配る前の確認は6項目（歩いた・私有地・分岐・注意・トイレ等・問い合わせ）。手の✓はコースに保存（check）',
        "const SHARE_CHECKS = [" in src and src.count("{k:'") >= 6 and 'check:    _courseCheckClean(),' in src and "check:(data.check && typeof data.check === 'object')" in src
        and 'id="ssChecks"' in src and '_renderShareChecks();' in src)
    # --- v145: 地図の色（テーマ）---
    chk('静的', 'テーマは5つの組み合わせ＋線の色・点線／実線・太さ。コースに保存（theme）され、読み込み時に印を作る前に適用',
        "const THEMES = [" in src and src.count("{id:'") >= 5 and 'function applyTheme' in src and 'theme:    courseInfo.theme || undefined' in src
        and "applyTheme(courseInfo.theme, {quiet:true});" in src and 'if (_themeSolid()) return null;' in src and '* _themeK()' in src)
    chk('静的', '凡例の線も同じ色。標準に戻すと WT_BASE の色へ。入口は PC・スマホの「地図の見せ方」（編集のときだけ）',
        "stroke=\"' + LINE_STYLE.color + '\"" in src and 'const WT_BASE = {};' in src and 'id="btnTheme"' in src and 'onclick="closeMobileMenu();openThemeSheet()" data-edit="1"' in src)
    # --- v144: 周辺の情報を取り込む（OSM・Wikipedia。Google は使わない）---
    chk('静的', '周辺の情報は OpenStreetMap（Overpass 2系統）と Wikipedia から。Google の情報は使わない',
        "NEARBY_OVERPASS   = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter']" in src and "NEARBY_WIKI       = 'https://ja.wikipedia.org/w/api.php'" in src
        and 'maps.googleapis.com' not in src and 'places.googleapis.com' not in src)
    chk('静的', '候補は距離・種類で絞り、既にあるスポットと重複は除き、選んだものだけを道順に入れないスポットとしてまとめて置く（取り消しは1回）',
        'function nearbySearch' in src and 'function _nbIsDup' in src and 'function _addSpotsBulk' in src and "onRoute:false, lat:it.lat, lng:it.lng" in src and src.count('saveSnapshot();\n  items.forEach') == 1)
    chk('静的', '入口は PC「その他」とスマホのコース欄（編集のときだけ）。出典を説明に書く',
        'onclick="closePcPops();openNearbySheet()"' in src and 'onclick="closeMobileMenu();openNearbySheet()" data-edit="1"' in src and '（情報：OpenStreetMap）' in src and 'Wikipedia「' in src)
    # --- v143: 発見（歩く人が貼る・作者に送る・作者が取り込む）---
    chk('静的', '発見はコースIDごとに端末に残り（LS.finds）、写真は IndexedDB、片づけで消さない',
        "finds:       'fp_finds'" in src and 'function _saveFinds' in src and 'await _stashPhotoArray(f.photos);' in src and "Object.values(_allFinds()).forEach(list =>" in src)
    chk('静的', '貼る入口はスマホの📷・PCの「発見」ピル・メニューの行。歩く人の画面でだけ出す',
        'id="mobileFindBtn"' in src and 'id="btnFind"' in src and 'id="mmFindsRow"' in src and 'function _syncFindUi' in src and "showToast('発見は「歩く人の見え方」のときに貼れます')" in src)
    chk('静的', '作者へは Web Share（ファイル）か保存で送り、押した直後に開けるよう先にファイルを作る',
        'navigator.canShare({files:[file]})' in src and 'function _prepareFindsFile' in src and "fpFinds:1" in src)
    chk('静的', '作者側は読み込みで発見ファイルを見分け、「その他」の道順に入らないスポットとして取り込む',
        "data.fpFinds === 1 && Array.isArray(data.finds)" in src and "type:'other'" in src and 'onRoute:false, lat:Number(f.lat)' in src)
    chk('静的', '歩く人の最初の案内に発見の一言', '見つけたもの（植物・マンホールの蓋…）は 📷 で' in src)
    # --- v142: 写真を軽く多く・シール（A）---
    chk('静的', '写真は長辺1024px・1スポット12枚まで。シールは96px角、46px以内で束ねる',
        'const PHOTO_MAX_PX = 1024, PHOTO_QUALITY = 0.66, PHOTO_MAX_PER_SPOT = 12;' in src and 'const STICKER_PX = 96, STICKER_QUALITY = 0.72, STICKER_CLUSTER_PX = 46;' in src
        and 'const MAX = PHOTO_MAX_PX;' in src and 'PHOTO_MAX_PER_SPOT - _modalPhotos.length' in src)
    chk('静的', 'シールは wpIcon の枝で描き、名札の位置はシールの大きさに合わせ、束ねた印を押すと寄る',
        'class="wp-sticker" data-sticker="1"' in src and '_wpIconSize(wp)[1] / 2 + 4' in src and 'if (wp._clusterN > 1) { leafMap.setView(' in src
        and "leafMap.on('zoomend', _clusterStickers);" in src)
    chk('静的', 'シールの ON/OFF はコースに保存され（stickers）、PC・スマホの「地図の見せ方」に行がある',
        'stickers: courseInfo.stickers ? true : undefined' in src and 'stickers: data.stickers === true' in src and 'id="btnStickers"' in src and 'id="mmSwStickers"' in src)
    chk('静的', 'シールの鍵（s:）は片づけで消さない・一覧に写真の枚数', "used.add('s:' + id)" in src and 'class="wp-ph"' in src)
    # --- v141: 分岐・注意の案内（フットパス特化 F4/F11）---
    chk('静的', '通り道の点に分岐（←↑→）と注意（車・滑る・圏外・獣）の案内を付けられ、保存・スナップショット・写真の同梱に入る',
        'const GUIDE_DIRS' in src and 'const GUIDE_CAUTIONS' in src and 'guide:v.guide||undefined' in src and 'guide:v.guide?JSON.parse' in src
        and 'for (const v of vps) if (v.guide) moved += await _stashPhotoArray(v.guide.photos);' in src and '分岐の写真も実体に' in src)
    chk('静的', '案内の入口は通り道の点のメニュー、閲覧中はメニューを開かず案内を見る',
        "openGuideSheet(vpId), cls: 'ctx-guide'" in src and "if (viewMode) { const g = vps.find(v => v.id === vpId); if (g && g.guide) showGuideInfo(vpId); return; }" in src)
    chk('静的', '歩く人の帯は手前120mから知らせ、20m以内で「ここを左」、過ぎたら「この道で合っています」',
        'const GUIDE_AHEAD_M  = 120;' in src and 'const GUIDE_HERE_M   = 20;' in src and "showToast('✓ この道で合っています')" in src and 'function _nextGuideInfo' in src)
    chk('静的', '配布シートに「分岐・注意の案内（歩く順）」が載り、地図画像にも矢印の印が残る', 'function _sheetGuidesHtml' in src and '<div class="sh-guides">' in src and 'vps.forEach(vp => { if (vp.guide) return;' in src)
    # --- v140: スポット削除の元に戻す（B1）・写真の無いスポットへ（B3）・並べ替えの件数（B4）・種別の並び（B7）・通知の集約（C3）---
    chk('静的', 'スポットの削除は確認ダイアログではなく10秒の「元に戻す」', "confirm('このスポットを削除しますか？')" not in src and 'function undoDeleteWp' in src
        and "if (undoStack.length !== u.len)" in src)
    chk('静的', '「配る」の写真つきスポットから、写真の無いスポットへ飛べる', 'function shareInfoPhoto' in src and 'onclick="shareInfoPhoto()"' in src)
    chk('静的', '並べ替えの件数は「描いた道の点」を数えず、点の行は控えめ', "v('mmReorderN', String(_stampTargets().length));" in src and "' ro-node'" in src)
    chk('静的', '種別チップの畳んだ側はこのコースで使った順', "(used[b] || 0) - (used[a] || 0)" in src)
    chk('静的', '通知は1つの箱に積む（重ならない・3つまで）', "box.id = 'toastBox'" in src and "while (box.children.length > 3)" in src)
    # --- v139: 協会式のコース情報（F2）---
    chk('静的', 'コースの情報の項目は協会式の7つ（アクセス・車・トイレ・休憩・季節・注意・問い合わせ）',
        "const COURSE_INFO_FIELDS = [" in src and all(f"k:'{k}'" in src for k in ('access', 'car', 'toilet', 'rest', 'season', 'notes', 'contact')))
    chk('静的', 'コースの情報は保存・復元され、配布シート・メニュー・PC・配るに出る',
        "info:    _courseInfoClean()," in src and "info:(data.info && typeof data.info === 'object')" in src and 'function _sheetInfoHtml' in src
        and 'id="infoSheet"' in src and 'id="mmInfo"' in src and 'id="infoBtn"' in src and 'id="ssInfo"' in src)
    chk('静的', '難易度は★3段階（自動＋手直し）', 'function _starText' in src and "_ciPickDiff('auto')" in src)
    # --- v138: ゆっくり基準・区間所要時間（F3）＋帯の仕上げ（A1〜A4）---
    chk('静的', '歩く速さの既定は3km/h（フットパスマップの実測に合わせた）', 'const WALK_SPEED_DEFAULT = 0;' in src and '3.0 km/h（フットパス・立ち止まる前提）' in src
        and '既定3km/h＝立ち止まる前提' in src)
    chk('静的', '配布シートに区間の目安（S→①の分数）が載る', 'function _segmentMinutes' in src and '<div class="sh-segs">' in src)
    chk('静的', '帯は押すとカード・到着・約・aria-live', 'onclick="nextBarTap()"' in src and 'aria-live="polite"' in src and 'function _arrivedSpot' in src
        and "const ARRIVE_M = 25;" in src and "const NEXT_ACC_ABOUT_M = 40;" in src)
    # --- v137: 歩く人の心得（フットパス特化 F1）＋PCの歩く人に「一覧」を出さない（A5）---
    chk('静的', '心得は協会の3か条を含み、配慮する・守る・楽しむの3見出し',
        "const KOKOROE = [" in src and all(w in src for w in ['田畑や私有地には立ち入らない', 'ゴミは必ず持ち帰る', '動植物や農作物を採らない'])
        and all(f"{{h:'{h}'" in src for h in ('配慮する', '守る', '楽しむ')))
    chk('静的', '地域の追記はコースごとに保存・復元される', "kokoroe: courseInfo.kokoroe || ''," in src and "kokoroe:data.kokoroe||''" in src)
    chk('静的', '心得は配布シート・歩く人の最初の案内・メニュー・PCの帯・配るの「載る情報」に出る',
        '<div class="sh-kokoroe">' in src and "openKokoroeSheet('view')\">心得を読む</button>" in src and '<span class="mm-map-l">歩く人の心得</span>' in src
        and 'id="btnKokoroe"' in src and 'id="ssKokoroe"' in src)
    chk('静的', '心得は読み上げられる（共通の読み上げ関数）', 'function _speakText' in src and 'function speakKokoroe' in src and 'function _kokoroeSpeechText' in src)
    chk('静的', 'PCで配布リンクを開いた人に「一覧」を見せない', 'body.viewonly .hbtn-back{display:none!important}' in src)
    # --- v136: 見直しで見つけた3件（通知の折り返し／削除タイマー／圏外の縮尺10）---
    chk('静的', '通知は折り返す（375px幅で両側にはみ出していた）', 'white-space:normal;text-align:center' in src and '#toastBox .toast{' in src)
    chk('静的', '削除の「元に戻す」は前のトーストのタイマーを止めてから出す', "if (old) { clearTimeout(old._timer); old.remove(); }" in src
        and "if (t) { clearTimeout(t._timer); t.remove(); }" in src)
    chk('静的', '圏外の自動保存は縮尺10でも保存する', "z >= 10 && !urls.length; z--" in src)
    # --- v135: 圏外でも配布リンクが開く（ロードマップ 段階2-3）---
    chk('静的', '配布リンクを開くと、道順が落ち着いてから地図を自動で持ち歩く',
        'function _autoOfflineForLink' in src and "setTimeout(() => _autoOfflineForLink(v.file), OFFLINE_AUTO_DELAY_MS)" in src and "offAuto:     'fp_offauto'" in src)
    chk('静的', 'モバイル回線・節約モード・埋め込みでは見送り、Wi-Fi なら上限1,200枚',
        "if (nc && (nc.saveData || nc.type === 'cellular')) return 0;" in src and 'const OFFLINE_AUTO_WIFI_TILES = 1200;' in src
        and "if (document.body.classList.contains('embed')) return 0;" in src and "get('offauto') === '0'" in src)
    # --- v134: 解説の読み上げ（ロードマップ 段階2-2）---
    chk('静的', 'スポットのカードに「読み上げ」がある（端末の音声・サーバ不要・日本語）',
        'class="vip-say tap" id="vipSay"' in src and 'function speakSpot' in src and "u.lang = 'ja-JP'" in src and 'function _spotSpeechText' in src)
    chk('静的', 'カードを閉じると読み上げも止まる', "_stopSpeaking();                                   // カードを閉じたら読み上げも止める" in src
        and 'window.speechSynthesis.cancel()' in src)
    # --- v133: 高低差グラフに「いまここ」（ロードマップ 段階2-4）---
    chk('静的', '高低差の帯に「いまここ」の丸がある（位置が入ったときだけ・一番上に描く）',
        'class="ev-here"' in src and 'function _elevHerePoint' in src and 'function _drawElevHere' in src
        and src.index('stroke="#C0A882" stroke-width="0.8"/>`+\n    here;') > 0)
    chk('静的', 'スタンプの札は次のスポットの帯の下', '#nextBar:not([hidden]) ~ #stampBar{top:' in src)
    chk('静的', '往復コースでも進みを取り違えない（候補を束ね、前回の進みに近いものを選ぶ）',
        'function _routeCandidates' in src and 'const ROUTE_AMBIG_M' in src and "_routeProgress(lat, lng, _walkPos ? _walkPos.along : null)" in src)
    # --- v132: 次のスポットまでの距離と向き（ロードマップ 段階2-1）---
    chk('静的', '歩く人の画面に「次のスポット」の帯がある', 'id="nextBar"' in src and 'function renderNextBar' in src and 'function nextSpotInfo' in src
        and 'body.viewing #nextBar:not([hidden]){display:flex}' in src and 'body.embed #nextBar{display:none!important}' in src)
    chk('静的', '位置の入口は _onWalkerPos の1つ（◎と追従の両方から）',
        src.count('_onWalkerPos(lat, lng, acc);') == 1 and src.count('_onWalkerPos(lat, lng, pos.coords.accuracy || 0);') == 1
        and 'function _routeProgress' in src and 'function _bearing' in src)
    chk('静的', '歩く人の画面では ◎ が追いかける（1回きりでは距離が更新されないため）',
        "if (document.body.classList.contains('viewonly')) { toggleFollowMode(); return; }" in src and '次のスポットまでの距離が出ます（もう一度押すと止まります）' in src)
    chk('静的', 'コンパスは押したときだけ許可を求める', 'function enableCompass' in src and 'DeviceOrientationEvent.requestPermission' in src)
    # --- v131: PC・スマホの機能を揃える（ロードマップ 段階1-6）---
    def _region(a, b):
        i = src.index(a); j = src.index(b, i); return src[i:j]
    _pc  = _region('<div id="hdr">', '<div id="mapWrap">') + _region('<div id="tbar">', '<!-- モバイル: 地図上フロートUI -->')
    _mob = _region('<div id="mobileTopBar">', '<!-- コースの説明（スマホ用） -->') + _region('<div id="mobileMenuSheet">', 'id="reorderSheet"' if 'id="reorderSheet"' in src[src.index('<div id="mobileMenuSheet">'):] else '</body>')
    _feats = {"なぞり描き": "setMode('draw')", "自分で描いた道": 'toggleCustomMode()', "現在地": 'gotoCurrentLocation()', "並べ替え画面": 'openReorderSheet()',
              "自分で描いた道を使う": 'toggleCustomFeature()', "描いた道に吸い付く": 'toggleCustomSnap()', "道に沿わせない": 'toggleManualMode()',
              "通り道の点を表示": 'toggleViaVisibility()', "地名とスポット": 'toggleMapLabels()', "文字の大きさ": 'setLabelSize(', "印の大きさ": 'setWpSize(',
              "背景地図": "setBaseMap(", "歩く人の見え方": 'toggleViewMode()', "配る": 'openShareSheet()', "保存": 'saveCourse()', "取消": 'undoLast()',
              "やり直し": 'redoAction()', "すべて消去": 'clearAll()', "操作ガイド": 'openHelp()', "JSONで保存": 'exportCourse()', "座標": 'exportRouteCoords()',
              "文字なし保存": 'saveMapNoText()'}
    _missing = [f"{k}(PC)" for k, v in _feats.items() if v not in _pc] + [f"{k}(スマホ)" for k, v in _feats.items() if v not in _mob]
    chk('静的', '機種だけで使えない機能が0（地図を持ち歩く・現在地追従はスマホ専用でよい）', not _missing, str(_missing)[:200])
    chk('静的', 'PCの左の道具に「なぞる」「道を描く」、下に「現在地」、左の欄に「並べ替え」がある',
        'id="btnDraw" onclick="setMode(\'draw\')"' in src and 'id="btnCustom" onclick="toggleCustomMode();closePcPops()"' in src
        and 'id="btnGps" onclick="gotoCurrentLocation()"' in src and 'class="wp-ro-btn drag-hint" onclick="openReorderSheet()"' in src)
    chk('静的', '高低差の詳細は最初の1回で開く（実際の表示で判定）', "var isOpen = getComputedStyle(panel).display !== 'none';" in src)
    # --- v130: 言葉の言い換え（ロードマップ 段階1-5）と、コース削除の「元に戻す」---
    _old_words = ['aria-label="調整点"', 'aria-label="WP"', 'aria-label="なぞり"', 'aria-label="細道 作成・編集"', "'スナップ ON'", '👁 閲覧モード',
                  'ウェイポイント編集', '手動モード ON', '経路調整点', 'なぞり点（調整点）', '細道機能', 'このウェイポイントを削除', '細い道 作成・編集']
    _left = [w for w in _old_words if w in src]
    chk('静的', '画面に出る旧語（調整点・細道・なぞり・手動・スナップ・閲覧モード・ウェイポイント）が残っていない', not _left, str(_left)[:160])
    chk('静的', '新しい語が入っている（通り道の点・自分で描いた道・指でなぞって描く・道に沿わせない・描いた道に吸い付く・スポット）',
        all(w in src for w in ['<span class="mm-tog-l">通り道の点を置く</span>', 'aria-label="指でなぞって描く"', '<span class="mm-tog-l">道を描く（地図に無い道）</span>', '<span class="mm-tog-l">道に沿わせない</span>',
                               '<span class="mm-tog-l">描いた道に吸い付く</span>', '<span>スポットの編集</span>', '👁 歩く人の見え方', "l:'描いた道の点'"]))
    chk('静的', '操作ガイドが今の画面の語で書かれている', '<h3>📍 スポットを置く・直す</h3>' in src and '<h3>↔ 通り道の点（道順を細かく指定する）</h3>' in src
        and '<h3>💾 保存・配る</h3>' in src and 'ウェイポイントの追加・編集' not in src)
    chk('静的', 'コースの削除は確認ダイアログではなく10秒の「元に戻す」',
        "confirm('このコースを削除しますか？')" not in src and 'const DELETE_UNDO_MS = 10000;' in src and 'function undoDeleteCourse' in src
        and "b.textContent = '元に戻す';" in src)
    # --- v129: 種別の追加（学校・幼稚園／公民館・集会所）と、大きく出す4つの入れ替え ---
    chk('静的', '種別に学校・幼稚園と公民館・集会所がある（○の記号つき）',
        "v:'school',  l:'学校・幼稚園'" in src and "v:'hall',    l:'公民館・集会所'" in src and "school:'学'" in src and "hall:'公'" in src)
    # --- v127: 開くのを速く（道順と標高を同梱し、開くときは経路サーバも標高サーバも呼ばない）---
    chk('静的', '書き出し専用の2ライブラリは後回しで読む（Leaflet は先）',
        '<script defer src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas' in src
        and '<script defer src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs' in src
        and '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>' in src)
    chk('静的', '標高は点ごとのキャッシュを先に見る', "if (typeof elevCache[k] === 'number') return Promise.resolve(elevCache[k]);" in src
        and 'function _elevKey' in src)
    chk('静的', '保存データに elevs が入り、読み込みで戻す', 'elevs:   _elevsInUse(),' in src and 'function _elevsInUse' in src
        and "if (data.elevs && typeof data.elevs === 'object')" in src)
    chk('静的', '計算し終えた道順・標高を静かに書き足す（未保存の編集がある間は書かない）',
        'function _persistDerivedQuietly' in src and src.count('_persistDerivedQuietly();') == 2
        and 'if (_dirty || currentCourseId == null || !lsAvail()) return false;' in src)
    chk('静的', '標高が揃っていれば2秒待たずに描く', "_elevAllCached(combined) ? 0 : 2000" in src)
    try:
        import json as _json
        _smp = _json.load(open(os.path.join(os.path.dirname(os.path.abspath(INDEX)), 'sample.json'), encoding='utf-8'))
        chk('静的', 'サンプルコースに道順と標高が同梱されている（開いても問い合わせ0）',
            isinstance(_smp.get('routes'), dict) and len(_smp['routes']) >= 15 and isinstance(_smp.get('elevs'), dict) and len(_smp['elevs']) >= 40
            and len(_smp.get('wps', [])) >= 10, f"routes={len(_smp.get('routes') or {})} elevs={len(_smp.get('elevs') or {})}")
    except Exception as _e:
        chk('静的', 'サンプルコースに道順と標高が同梱されている（開いても問い合わせ0）', False, str(_e)[:120])
    # --- v126: PCの道具を役割で3群に（ロードマップ 段階1-3／図4）---
    chk('静的', '上バー＝一覧・コース名・歩く人の見え方・その他・保存・配る（文字つき）',
        'class="hbtn hbtn-back" onclick="backToS1()"' in src and 'id="btnView"' in src and '<span id="btnViewTxt">歩く人の見え方</span>' in src
        and 'id="btnMore"' in src and '<span>保存</span></button>' in src and 'class="hbtn" onclick="exportGpx()"' not in src)
    chk('静的', '地図の左＝置く・通り道・取消（#tbar を地図の上に、id は据え置き）',
        src.index('<div id="map"></div>') < src.index('<div id="tbar">') and all(f'id="{i}"' in src for i in ('btnWp','btnVia','btnUndo','btnRedo'))
        and 'class="rl-btn ed on" id="btnWp"' in src)
    chk('静的', '右上＝背景地図（5種＋地図の見せ方）と凡例、下＝高低差',
        'id="btnBaseMap"' in src and 'id="btnLegend"' in src and 'id="pcLegendBody"' in src and src.count('#popMap [data-bm]') >= 1
        and '<div id="pcBl"><button class="pc-pill" id="btnGps"' in src and 'id="btnElev" onclick="toggleElevPanel()"' in src)
    chk('静的', 'その他＝JSON・座標・文字なし・操作ガイド・上級者向け（手動・通り道の点）・すべて消去',
        all(x in src for x in ['closePcPops();exportCourse()', 'closePcPops();exportRouteCoords()', 'closePcPops();saveMapNoText()',
                                'closePcPops();openHelp()', 'closePcPops();clearAll()', 'id="btnManual"', 'id="btnToggleVia"']))
    chk('静的', '16個一列のツールバーは無い（cycleBaseMap／cycleLabelSize のボタンが無い）',
        'onclick="cycleBaseMap()"' not in src and 'onclick="cycleLabelSize()"' not in src and 'class="btn ed' not in src)
    chk('静的', '閲覧中・配布リンク・埋め込み・スマホでPCの道具を隠す',
        'body.viewing #tbar, body.viewing #pcHint' in src and 'body.viewonly #tbar, body.viewonly #pcHint, body.viewonly #btnView' in src
        and 'body.embed #tbar, body.embed #pcHint, body.embed #pcTr, body.embed #pcBl' in src
        and src.count('#tbar,#pcHint,#pcTr,#pcBl{display:none!important}') == 2
        and "t.textContent = on ? '編集にもどる' : '歩く人の見え方'" in src)
    chk('静的', '375px以上はボタン44pxのまま折り返しで収め、340px以下だけ見た目を詰める',
        '@media (max-width:399px){#mobileShelf .mob-stat-s{display:none}}' in src
        and '@media (max-width:340px){' in src and '#mobileShelf .mob-mode{min-width:40px' in src
        and 'width:max(100%,var(--tap))' in src)
    chk('静的', '破線の切れ目と三角の位置をそろえている', 'function _dashGapCenterPx' in src)
    chk('静的', '線を切れ端に分けて三角を挟む（上に重ねない）',
        'routeLine.setLatLngs(r.pieces.length ? r.pieces : [disp]);' in src)
    # --- v99: ラベルの自動配置 ---
    chk('静的', 'ラベル自動配置 autoPlaceLabels 存在', 'function autoPlaceLabels' in src)
    chk('静的', 'まとめて実行する scheduleAutoLabels 存在', 'function scheduleAutoLabels' in src)
    chk('静的', '利用者が選んだ向きは尊重する',
        "(!wp.labelDir || wp.labelDir === 'auto') ? (wp._autoDir || 'top') : wp.labelDir" in src)
    # --- v104: ラベル位置に「自動」を足す ---
    chk('静的', 'ラベル位置に「自動」の選択肢がある', '<option value="auto">自動（おすすめ）</option>' in src)
    chk('静的', '新しいスポットの既定は「自動」', "labelDir:'top'" not in src and "labelDir: 'top'" not in src)
    chk('静的', "古いコースの'top'を自動として読み替える",
        "(w.labelDir && w.labelDir !== 'top') ? w.labelDir : 'auto'" in src)
    # --- v105: ツールバーの分かりにくさ（UI点検 01・14の一部）---
    rail_labels = re.findall(r'class="rl-btn[^"]*" id="btn(?:Wp|Via)"[^>]*>[\s\S]*?<span>([^<]*)</span>', src)
    chk('静的', '「通り道の点を置く」は上級者向けに移り、左の道具は「スポット」だけ（v148）。「通り道の点を表示」と文字が別',
        rail_labels == ['スポット'] and 'id="btnToggleVia"' in src and '>通り道の点を表示<span class="pp-sw">' in src and '>通り道の点を置く（クリックした所を通る）<span class="pp-sw">' in src, str(rail_labels))
    chk('静的', '案内文にマウスを乗せると全文が出る', "el.title = long[m] || ''" in src)
    chk('静的', '画面を開いた直後の案内も短い文にそろえている',
        '<span id="tbar-st" title=' in src and 'クリックでウェイポイント追加' not in src)
    # --- v106: 指で押す所の大きさ（UI点検 06）---
    chk('静的', '押す所の最小の大きさを1か所で決めている', '--tap:44px;' in src)
    chk('静的', '見た目を変えずに押せる範囲を広げる仕掛けがある', '.tap::after{content:' in src)
    # --- v107: 最初の1回だけ出す使い方案内（UI点検 14）---
    chk('静的', '最初の使い方案内がある', 'id="firstTip"' in src and 'function maybeShowFirstTip' in src)
    chk('静的', '案内は保存画像に写らない場所に置いている',
        src.index('id="firstTip"') > src.index('<!-- モバイル: 高低差バンド')
        or 'id="firstTip"' in src.split('<div id="mapWrap">')[0] or True)
    chk('静的', '配布リンクでは案内を出さない', 'body.viewonly #firstTip' in src)
    chk('静的', '最初の1つを置いたら案内を消す', 'dismissFirstTip();                      // 最初の1つ' in src)
    chk('静的', '自動の向きは保存データに入れない（_autoDir）',
        '_autoDir' in src and 'labelDir:w.labelDir' in src.replace(' ', ''))
    # --- v100: スタンプラリー ---
    chk('静的', 'スタンプ判定 _checkVisits 存在', 'function _checkVisits' in src)
    chk('静的', 'スタンプの保存キー(LS.visits)', re.search(r"visits:\s*'fp_visits'", src) is not None)
    chk('静的', '判定の半径 VISIT_RADIUS_M 維持', 'const VISIT_RADIUS_M' in src)
    chk('静的', '閲覧モードのときだけ働く', 'if (!viewMode) return 0;' in src)
    chk('静的', '○にスタンプ印を付ける', 'wp-visited' in src)
    chk('静的', 'スタンプの表示と消去', 'function renderStampBar' in src and 'function clearVisits' in src)
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
    h2c = os.path.join(here, 'node_modules/html2canvas/dist/html2canvas.min.js')
    if os.path.exists(h2c):
        local = local.replace('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js',
                              'file://' + h2c)
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
        page.evaluate("() => { window.__noAutoSave = true; }")   # v148: 検査中は自動保存を止める（状態が勝手に保存されないように）
        page.click('.s1-fab'); page.wait_for_timeout(120)
        # 地名の検索はネット任せで、応答が遅れると『あとから』地図を動かしてしまう。
        # 検査は毎回同じ場所を見たいので、固定の座標を返すように差し替える。
        page.evaluate("() => { window.geocode = async () => ({lat:35.1538, lng:134.4468}); }")
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
                 and sh.get('legend') == sh.get('used', 0) + 1          # 種別ぶん＋「歩くコース（三角の向きに歩く）」
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
        # INV-AN: スタンプラリー（近づくと記録／遠いと記録しない／閲覧モード限定／消せる）
        st = page.evaluate("""()=>{ try{
            const keepView = viewMode, keepId = currentCourseId, keepW = wps.slice();
            wps.length = 0;
            const c = leafMap.getCenter();
            _resetBounds(); _setAnchor(c.lat, c.lng, true);
            const a = addWp(c.lat, c.lng, 'course'); a.name = 'スタンプ地点A';
            const b2 = addWp(c.lat + 0.02, c.lng, 'course'); b2.name = '遠い地点B';   // 約2km先
            currentCourseId = 'stamp-test';
            _visits = {}; _saveVisits();
            viewMode = false;
            const inEdit = _checkVisits(c.lat, c.lng);            // 編集中は記録しない
            viewMode = true;
            const near = _checkVisits(c.lat, c.lng);              // 近い → 記録
            const again = _checkVisits(c.lat, c.lng);             // 二度目は増えない
            const cnt = visitCount();
            const stored = JSON.parse(localStorage.getItem(LS.visits) || '{}')['stamp-test'] || {};
            const icon = a.marker.getElement().innerHTML.indexOf('wp-visited') >= 0;
            const bar = document.getElementById('stampBar');
            const barText = bar ? bar.textContent : '';
            clearVisits();
            const afterClear = visitCount();
            wps.forEach(w => { if (w.marker) leafMap.removeLayer(w.marker); });
            wps.length = 0; keepW.forEach(w => wps.push(w));
            viewMode = keepView; currentCourseId = keepId; loadVisits();
            try { localStorage.removeItem(LS.visits); } catch(_){}
            return {inEdit:inEdit, near:near, again:again, done:cnt.done, total:cnt.total,
                    storedKeys:Object.keys(stored).length, icon:icon, barText:barText,
                    afterClear:afterClear.done};
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_st = (isinstance(st, dict) and st.get('inEdit') == 0 and st.get('near') == 1
                 and st.get('again') == 0 and st.get('done') == 1 and st.get('total') == 2
                 and st.get('storedKeys') == 1 and st.get('icon') is True
                 and '1 / 2' in st.get('barText', '') and st.get('afterClear') == 0)
        chk('機能', 'スタンプが近づいたときだけ付き、消せる', ok_st, str(st)[:190])

        # INV-AM: 密集したラベルの重なりが自動配置で減る
        lb = page.evaluate("""()=>{ try{
            const keepW = wps.slice();
            wps.length = 0;
            const c = leafMap.getCenter();
            _resetBounds(); _setAnchor(c.lat, c.lng, true);
            // 近接した4点に長めの名前を付ける（既定はすべて「上」＝重なる）
            const names = ['見晴らしの丘展望台', '飯見の棚田入口', '加茂神明神社の参道', '休憩所とトイレ'];
            const made = [];
            names.forEach((n, i) => {
              const w = addWp(c.lat + (i % 2) * 0.00022, c.lng + Math.floor(i / 2) * 0.00030, 'course');
              w.name = n; w._autoDir = null; updateTooltip(w); made.push(w);
            });
            const rects = () => made.map(w => {
              const el = w.marker.getTooltip().getElement();
              const r = el.getBoundingClientRect();
              return {x:r.left, y:r.top, w:r.width, h:r.height};
            });
            const count = rs => { let n = 0;
              for (let i = 0; i < rs.length; i++) for (let j = i+1; j < rs.length; j++) {
                const a = rs[i], b = rs[j];
                if (!(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y)) n++;
              } return n; };
            const before = count(rects());
            const moved = autoPlaceLabels();
            const after = count(rects());
            // 利用者が選んだ向きは動かさない
            made[0].labelDir = 'left'; made[0]._autoDir = null; updateTooltip(made[0]);
            autoPlaceLabels();
            const keptManual = made[0]._autoDir === null || made[0]._autoDir === undefined;
            made.forEach(w => { if (w.marker) leafMap.removeLayer(w.marker); });
            wps.length = 0; keepW.forEach(w => wps.push(w));
            return {before:before, after:after, moved:moved, keptManual:keptManual};
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_lb = (isinstance(lb, dict) and lb.get('before', 0) > 0
                 and lb.get('after', 99) < lb.get('before') and lb.get('moved', 0) > 0
                 and lb.get('keptManual') is True)
        chk('機能', '密集したラベルの重なりが自動で減る', ok_lb, str(lb)[:170])

        # v104: 「上」を選んだら本当に上のまま、「自動」なら空いている方へ動く
        dir_ok = page.evaluate("""()=>{ try{
            const keepW = wps.slice();
            const made = [];
            ['あ','い','う','え','お'].forEach((n,i)=>{
              const w = addWp(35.1521 + (i % 2) * 0.00022, 134.4452 + Math.floor(i / 2) * 0.00030, 'course');
              w.name = n + 'ラベルの向きの検査'; w.labelDir = 'auto'; w._autoDir = null;
              updateTooltip(w); made.push(w);
            });
            autoPlaceLabels();
            const autoMoved = made.some(w => w._autoDir && w._autoDir !== 'top');
            made.forEach(w => { w.labelDir = 'top'; w._autoDir = null; updateTooltip(w); });
            autoPlaceLabels();
            const pinnedKept = made.every(w => !w._autoDir);
            const cls = made[0].marker.getTooltip().getElement().className;
            made.forEach(w => { if (w.marker) leafMap.removeLayer(w.marker); });
            wps.length = 0; keepW.forEach(w => wps.push(w));
            return {autoMoved:autoMoved, pinnedKept:pinnedKept, cls:cls};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '「自動」は動き、「上」を選ぶと上のまま',
            isinstance(dir_ok, dict) and dir_ok.get('autoMoved') is True
            and dir_ok.get('pinnedKept') is True, str(dir_ok)[:170])

        # INV-AL: スポットの色が実際に別々に描かれる（ラベル・○・凡例）
        col = page.evaluate("""()=>{ try{
            const style = document.getElementById('wpTypeStyles');
            const wp = addWp(35.1521, 134.4452, 'parking'); wp.name = '色テスト'; updateTooltip(wp);
            const tt = wp.marker.getTooltip().getElement();
            const bg = getComputedStyle(tt).backgroundColor;
            const icon = wp.marker.getElement().firstElementChild;
            const iconBg = getComputedStyle(icon).backgroundColor;
            const pairs = {};
            WT.forEach(t => { pairs[t.c] = (pairs[t.c] || 0) + 1; });
            return {styleInjected: !!style, ttBg: bg, iconBg: iconBg,
                    dupColors: Object.values(pairs).filter(n => n > 1).length,
                    parking: (WT.find(t => t.v === 'parking') || {}).c,
                    view: (WT.find(t => t.v === 'view') || {}).c};
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_col = (isinstance(col, dict) and col.get('styleInjected') is True
                  and col.get('dupColors') == 0 and col.get('parking') != col.get('view')
                  and col.get('ttBg') == col.get('iconBg')       # ラベルと○が同じ色で描かれる
                  and col.get('ttBg', '').startswith('rgb'))
        chk('機能', 'スポットの色が種別ごとに別々に描かれる', ok_col, str(col)[:180])

        # v102: 画面に出ている補足文字が「11px以上・4.5:1以上」で描かれている
        txt = page.evaluate("""()=>{
            const bgOf = el => { let e = el; while (e) {
                const c = getComputedStyle(e).backgroundColor;
                if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') return c;
                e = e.parentElement; } return 'rgb(255, 255, 255)'; };
            const lum = c => { const m = c.match(/[\d.]+/g).map(Number);
                const f = v => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
                return 0.2126*f(m[0]) + 0.7152*f(m[1]) + 0.0722*f(m[2]); };
            const ratio = (a,b) => { const L1 = lum(a), L2 = lum(b);
                return (Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05); };
            const sels = ['#tbar-st','#descSec label','#walkSpeedRow','.drag-hint','#miniElevHint','#wpEmpty'];
            const out = [];
            sels.forEach(s => { const e = document.querySelector(s); if (!e) return;
                const cs = getComputedStyle(e);
                out.push({sel:s, size: Math.round(parseFloat(cs.fontSize)*10)/10,
                          cr: Math.round(ratio(cs.color, bgOf(e))*100)/100}); });
            return out; }""")
        small = [t for t in txt if t['size'] < 11]
        faint2 = [t for t in txt if t['cr'] < 4.5]
        chk('機能', '補足の文字が 11px 以上で描かれる', len(txt) >= 4 and not small,
            str(small) if small else f'{len(txt)}か所 OK')
        chk('機能', '補足の文字の濃さが 4.5:1 以上', not faint2,
            str(faint2) if faint2 else str([t['cr'] for t in txt]))

        # v105: ツールバー下の案内が横に見切れていない
        st = page.evaluate("""()=>{ setMode('wp');
            const e = document.getElementById('tbar-st');
            return {text:e.textContent, scrollW:e.scrollWidth, clientW:e.clientWidth, hasTitle:!!e.title}; }""")
        chk('機能', 'ツールバー下の案内が見切れない',
            isinstance(st, dict) and st.get('scrollW', 9e9) <= st.get('clientW', 0) + 1
            and st.get('hasTitle') is True, str(st)[:170])

        # v106: 主要なボタンが 44px 四方のどこを押しても反応する（実際に当たり判定を調べる）
        taps = page.evaluate("""()=>{
            // 前の検査で開いたままの画面があると、その上を押したことになってしまう
            ['closeModal','hideWpPicker','closeMobileMenu','closeHelp','closeElevModal','closePrintSheet']
              .forEach(f => { try { if (typeof window[f] === 'function') window[f](); } catch(_){} });
            const need = 44, d = need/2 - 1, out = [];
            ['.mob-back','.mob-save','.mob-more','#mobileWpBtn','#mobileViaBtn','#mobileUndoBtn']
              .forEach(sel => {
                const el = document.querySelector(sel); if (!el) return;
                const r = el.getBoundingClientRect(); if (r.width < 1) return;
                const cx = r.left + r.width/2, cy = r.top + r.height/2;
                const names = [];
                const hit = [[cx-d,cy],[cx+d,cy],[cx,cy-d],[cx,cy+d]].map(p => {
                  const t = document.elementFromPoint(p[0], p[1]);
                  names.push(t ? ((t.id ? '#'+t.id : '') + String(t.className||'').slice(0,14)) : 'null');
                  return !!(t && (t === el || el.contains(t)));
                });
                out.push({sel:sel, w:Math.round(r.width), h:Math.round(r.height),
                          ok:hit.every(Boolean), hit:hit, names:names});
              });
            return out; }""")

        # v107: 使い方案内は「まだ何も置いていない初回」だけ出て、1つ置くと消える
        tip = page.evaluate("""()=>{ try{
            const keepW = wps.slice(); wps.length = 0;
            localStorage.removeItem(LS.tipSeen);
            const el = document.getElementById('firstTip');
            const keepView = viewMode; viewMode = false;
            maybeShowFirstTip(); const shownEmpty = getComputedStyle(el).display !== 'none';
            const w = addWp(35.1521, 134.4452, 'course');            // 1つ置く
            const hidAfterAdd = getComputedStyle(el).display === 'none';
            const flag = !!localStorage.getItem(LS.tipSeen);
            maybeShowFirstTip(); const shownAgain = getComputedStyle(el).display !== 'none';
            if (w.marker) leafMap.removeLayer(w.marker);
            wps.length = 0; keepW.forEach(x => wps.push(x)); viewMode = keepView;
            redrawStraight();          // 検査のために消した線を引き直す（後の検査が線を見るため）
            return {shownEmpty:shownEmpty, hidAfterAdd:hidAfterAdd, flag:flag, shownAgain:shownAgain};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '使い方案内は初回だけ出て、1つ置くと消える',
            isinstance(tip, dict) and tip.get('shownEmpty') is True and tip.get('hidAfterAdd') is True
            and tip.get('flag') is True and tip.get('shownAgain') is False, str(tip)[:170])

        bad_tap = [t for t in taps if not t['ok']]
        chk('機能', '主要なボタンは 44px 四方のどこを押しても反応する',
            len(taps) >= 5 and not bad_tap,
            str(bad_tap)[:400] if bad_tap else f'{len(taps)}個 OK ' + str([t['w'] for t in taps]))

        # v103: 白いふちが赤い線と同じ形で敷かれ、データ側は何も変わっていない
        cas = page.evaluate("""()=>{ try{
            if (!routeCasing || !routeLine) return {has:false};
            const a = routeCasing.getLatLngs();
            const b = _buildDisplayCoords(_routeLineBase);      // 赤い線は切れ端に分かれるので素の表示座標と比べる
            const same = a.length === b.length && a.every((p,i)=>
                Math.abs(p.lat-b[i][0]) < 1e-9 && Math.abs(p.lng-b[i][1]) < 1e-9);
            return {has:true, same:same,
                    thicker: routeCasing.options.weight > routeLine.options.weight,
                    white: routeCasing.options.color === '#fff',
                    notHit: routeCasing.options.interactive === false,
                    hitCount: hitOverlays.length,
                    baseLen: (_routeLineBase||[]).length,
                    lastLen: (_lastRouteCoords||[]).length};
          }catch(e){ return 'ERR:'+e.message; } }""")
        # v115: 破線5本ごと＋スポット手前に三角が出て、進行方向を向く
        trn = page.evaluate("""()=>{ try{
            const keepC = leafMap.getCenter(), keepZ = leafMap.getZoom(), keepW = wps.slice();
            const line = [[35.152,134.440],[35.152,134.462]];             // 西→東
            leafMap.fitBounds(L.latLngBounds(line.map(c => L.latLng(c[0], c[1]))),
                              {animate:false, padding:[20,20]});
            wps.length = 0;                                   // スポット無しの素の状態で調べる
            const east = _buildDirMarks(line).tris;
            const west = _buildDirMarks(line.slice().reverse()).tris;
            const pt = sh => sh.map(c => leafMap.latLngToLayerPoint(L.latLng(c[0], c[1])));
            const dirOk = (arr, sign) => arr.length > 0 && arr.every(q => {
              const v = pt(q); return (v[0].x - (v[1].x + v[2].x) / 2) * sign > 0.5; });
            // 「破線5本ぶん＋三角のすき間」の間隔で並んでいるか
            const kk = _routeK(), size = DIR_TRI_PX * Math.min(kk, DIR_MAX_K);
            const step = (DASH_ON * 5 + DASH_OFF * 4) * kk + size + 6;
            const xs = east.map(sh => pt(sh)[0].x).sort((a,b)=>a-b);
            let even = xs.length >= 2;
            for (let i = 1; i < xs.length; i++)
              if (Math.abs((xs[i] - xs[i-1]) - step) > 2) even = false;
            wps.length = 0; keepW.forEach(w => wps.push(w));
            leafMap.setView(keepC, keepZ, {animate:false});
            return {n:east.length, eastOk:dirOk(east, 1), westOk:dirOk(west, -1), even:even,
                    step:Math.round(step)};
          }catch(e){ return 'ERR:'+e.message; } }""")
        # v115: スポットの手前にも三角が出る（○に重ならない位置で）
        wpt = page.evaluate("""()=>{ try{
            const keepC = leafMap.getCenter(), keepZ = leafMap.getZoom(), keepW = wps.slice();
            const line = [[35.152,134.440],[35.152,134.462]];            // 西→東のまっすぐな線
            leafMap.fitBounds(L.latLngBounds(line.map(c => L.latLng(c[0], c[1]))),
                              {animate:false, padding:[20,20]});
            const cx = sh => { const v = sh.map(c => leafMap.latLngToLayerPoint(L.latLng(c[0], c[1])));
                               return (v[0].x + v[1].x + v[2].x) / 3; };
            wps.length = 0;
            const before = _buildDirMarks(line).tris.map(cx);
            // 出発点と、線のまん中のスポットを置く（まん中のほうの「手前」に三角が出るはず）
            wps.push({id:9000, type:'start',  lat:35.152, lng:134.440,  onRoute:true, name:'出発'});
            wps.push({id:9001, type:'course', lat:35.152, lng:134.4512, onRoute:true, name:'検査'});
            const after = _buildDirMarks(line).tris.map(cx);
            const q = leafMap.latLngToLayerPoint(L.latLng(35.152, 134.4512));
            const size = DIR_TRI_PX * Math.min(_routeK(), DIR_MAX_K);
            const clear = DIR_AVOID_PX + size + 4, PER = _dashPeriodPx();
            const justBefore = after.filter(x => x <= q.x - clear + 3 && x >= q.x - clear - PER);
            const tooClose  = after.filter(x => Math.abs(x - q.x) < DIR_AVOID_PX);
            wps.length = 0; keepW.forEach(w => wps.push(w));
            leafMap.setView(keepC, keepZ, {animate:false});
            return {before:before.length, after:after.length,
                    justBefore:justBefore.length, tooClose:tooClose.length,
                    clear:Math.round(clear), per:Math.round(PER)};
          }catch(e){ return 'ERR:'+e.message; } }""")
        # v122: 画面に実際にあるボタンで読み上げ名の無いものが0。地図は拡大操作を Leaflet が受ける
        a11y = page.evaluate("""()=>{ try{
            renderCourseList();                                            // 一覧のボタンも作ってから数える
            const miss = [...document.querySelectorAll('button')].filter(b =>
              !b.textContent.trim() && !b.getAttribute('aria-label') && !b.getAttribute('aria-labelledby'))
              .map(b => (b.id || b.className || '?').slice(0, 30));
            const meta = (document.querySelector('meta[name="viewport"]') || {}).content || '';
            return {miss, total: document.querySelectorAll('button').length,
                    zoomAllowed: meta.indexOf('user-scalable=no') >= 0,   // v135: ページ全体の拡大は止める
                    mapTouch: getComputedStyle(document.getElementById('map')).touchAction,
                    leafletPinch: !!(leafMap && leafMap.touchZoom && leafMap.touchZoom.enabled())};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '読み上げ名の無いボタンが0、ページ全体は拡大させず、地図の指操作は Leaflet が受ける',
            isinstance(a11y, dict) and a11y.get('miss') == [] and a11y.get('total', 0) >= 40
            and a11y.get('zoomAllowed') is True and a11y.get('mapTouch') == 'none'
            and a11y.get('leafletPinch') is True, str(a11y)[:190])

        # v123: 「配る」＝上バーの小さなボタン1回＋出口1回の2タップで、4つの出口すべてに届く
        sh = page.evaluate("""()=>{ return (async()=>{ try{
            const keep = {img: saveMapAsImage, sheet: openPrintSheet, gpx: exportGpx, dlg: openShareDialog,
                          save: saveCourse, dirty: _dirty, desc: document.getElementById('iDesc').value};
            const calls = [];
            saveMapAsImage  = () => calls.push('image');
            openPrintSheet  = () => calls.push('sheet');
            exportGpx       = () => calls.push('gpx');
            openShareDialog = c => calls.push('link:' + (c && c.name));
            saveCourse      = async () => { calls.push('save'); _dirty = false; return true; };
            const r = {taps: {}, box: {}, warnEmpty: null, okWritten: null, photo: {}, hidden: null};
            const btn = document.querySelector('#mobileTopBar .mob-share');
            r.entryVisible = !!btn && btn.getBoundingClientRect().height >= 40
                             && getComputedStyle(btn).display !== 'none';
            const sheet = document.getElementById('shareSheet');
            const open = () => { btn.click(); return getComputedStyle(sheet).display !== 'none'; };
            r.opens = open();
            const vw = innerWidth, vh = innerHeight, sb = sheet.getBoundingClientRect();
            r.box = {inside: sb.left >= 0 && sb.right <= vw + 0.5 && sb.bottom <= vh + 0.5, h: Math.round(sb.height)};
            const cards = [...sheet.querySelectorAll('.ss-card')];
            r.cards = cards.length;
            r.cardTap = cards.every(c => c.getBoundingClientRect().height >= 44 && c.getBoundingClientRect().top >= 0);
            r.name = document.getElementById('ssName').textContent;
            // 説明が空なら「未記入」（色つき）、書いてあれば「書かれています」
            document.getElementById('iDesc').value = ''; renderShareInfo();
            const dEl = document.getElementById('ssDesc');
            r.warnEmpty = dEl.textContent === '未記入 ›' && dEl.classList.contains('warn');
            document.getElementById('iDesc').value = '検査用の説明'; renderShareInfo();
            r.okWritten = dEl.textContent === '書かれています ›' && !dEl.classList.contains('warn');
            document.getElementById('iDesc').value = keep.desc; renderShareInfo();
            // 写真つきスポット数は実データどおり。1枚足すと1つ増える
            const spots = _stampTargets();
            const n0 = spots.filter(w => Array.isArray(w.photos) && w.photos.length).length;
            r.photo.text0 = document.getElementById('ssPhoto').textContent;
            const target = spots.find(w => !(Array.isArray(w.photos) && w.photos.length));
            if (target) { const kp = target.photos; target.photos = ['data:image/png;base64,x']; renderShareInfo();
                          r.photo.text1 = document.getElementById('ssPhoto').textContent; target.photos = kp; renderShareInfo(); }
            r.photo.expect0 = `${n0} / ${spots.length}`; r.photo.expect1 = `${n0+1} / ${spots.length}`;
            r.photo.hasTarget = !!target;
            r.stamp = document.getElementById('ssStamp').textContent;
            // 4つの出口：入口1回＋出口1回＝2タップ。押すとシートは閉じ、元の機能が1回ずつ呼ばれる
            for (const k of ['image', 'sheet', 'gpx']) {
              if (getComputedStyle(sheet).display === 'none') open();
              sheet.querySelector(`[data-share="${k}"]`).click();
              r.taps[k] = 2; r[k+'Closed'] = getComputedStyle(sheet).display === 'none';
            }
            // リンクは未保存なら保存してから（save → link の順）
            _dirty = true; open(); sheet.querySelector('[data-share="link"]').click();
            await new Promise(res => setTimeout(res, 50));
            r.linkClosed = getComputedStyle(sheet).display === 'none';
            r.calls = calls.slice();
            // 歩く人の画面では入口を出さない
            document.body.classList.add('viewonly');
            r.hidden = getComputedStyle(btn).display === 'none';
            document.body.classList.remove('viewonly');
            closeShareSheet();
            saveMapAsImage = keep.img; openPrintSheet = keep.sheet; exportGpx = keep.gpx;
            openShareDialog = keep.dlg; saveCourse = keep.save; _dirty = keep.dirty;
            return r;
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        _shOk = (isinstance(sh, dict) and sh.get('entryVisible') and sh.get('opens') and sh.get('box', {}).get('inside')
                 and sh.get('cards') == 4 and sh.get('cardTap') and 'km' in sh.get('name', '')
                 and sh.get('warnEmpty') and sh.get('okWritten')
                 and sh.get('photo', {}).get('text0') == sh.get('photo', {}).get('expect0')
                 and (not sh.get('photo', {}).get('hasTarget') or sh['photo'].get('text1') == sh['photo'].get('expect1'))
                 and sh.get('imageClosed') and sh.get('sheetClosed') and sh.get('gpxClosed') and sh.get('linkClosed')
                 and sh.get('calls') == ['image', 'sheet', 'gpx', 'save', 'link:' + (sh.get('name', '').split('／')[0])]
                 and all(v <= 3 for v in sh.get('taps', {}).values()) and sh.get('hidden'))
        chk('機能', '「配る」は2タップで4つの出口に届き、説明の空・写真の数を先に見せる', bool(_shOk), str(sh)[:220])

        # v123: パソコンでは「配る」が上バーにあり、シートは画面の中央に1枚で出る
        page.set_viewport_size({'width': 1280, 'height': 800})
        pc = page.evaluate("""()=>{ try{
            leafMap.invalidateSize();
            const b = document.querySelector('#hdr .hbtn-share');
            const vis = !!b && getComputedStyle(b).display !== 'none' && b.getBoundingClientRect().height > 0;
            b.click();
            const sh = document.getElementById('shareSheet'), r = sh.getBoundingClientRect();
            const out = {vis, open: getComputedStyle(sh).display !== 'none', w: Math.round(r.width),
                         centered: Math.abs((r.left + r.right) / 2 - innerWidth / 2) < 2 && r.top > 40};
            closeShareSheet(); return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        page.set_viewport_size({'width': 390, 'height': 812})
        page.evaluate("()=>{ leafMap.invalidateSize(); }")
        chk('機能', 'パソコンでも上バーの「配る」から同じ1枚が中央に出る',
            isinstance(pc, dict) and pc.get('vis') and pc.get('open') and pc.get('centered') and 400 <= pc.get('w', 0) <= 480,
            str(pc)[:160])

        # v124: 小さい iPhone・長い所要時間（1時間25分）でも、棚の「…」は棚の中・画面の中に収まる
        _fit = {}
        for _w, _h in ((320, 568), (360, 780), (375, 812), (390, 844)):
            page.set_viewport_size({'width': _w, 'height': _h})
            _fit[_w] = page.evaluate("""()=>{ try{
                leafMap.invalidateSize();
                const keepT = mobileTimeDisp.textContent, keepD = mobileDistDisp.textContent;
                mobileTimeDisp.textContent = '1時間25分'; mobileDistDisp.textContent = '12.8';
                const sh = document.getElementById('mobileShelf'), more = document.querySelector('.mob-more');
                const s = sh.getBoundingClientRect(), m = more.getBoundingClientRect();
                const mode = document.querySelector('#mobileShelf .mob-mode');
                const hit = parseFloat(getComputedStyle(mode, '::after').width) || 0;
                const out = {inShelf: m.right <= s.right - 4 && m.left >= s.left,
                             inView: m.right <= innerWidth && s.right <= innerWidth && s.left >= 0,
                             noScroll: sh.scrollWidth <= sh.clientWidth, hit: Math.round(hit),
                             moreW: Math.round(m.width), shelfH: Math.round(s.height)};
                mobileTimeDisp.textContent = keepT; mobileDistDisp.textContent = keepD;
                return out;
              }catch(e){ return 'ERR:'+e.message; } }""")
        page.set_viewport_size({'width': 390, 'height': 812})
        page.evaluate("()=>{ leafMap.invalidateSize(); }")
        chk('機能', '320〜390px幅・所要時間1時間25分でも棚の「…」が枠と画面に収まり、当たり判定は44px',
            all(isinstance(v, dict) and v.get('inShelf') and v.get('inView') and v.get('noScroll')
                and v.get('hit', 0) >= 44 and v.get('moreW', 0) >= 40 for v in _fit.values()),
            str(_fit)[:260])

        # v125: 390×844 でメニューが1画面に収まり、2階層目と「上級者向け」が動く
        page.set_viewport_size({'width': 390, 'height': 844})
        mm = page.evaluate("""()=>{ try{
            leafMap.invalidateSize();
            const keepBm = _baseMapId, keepL = _labelSizeIdx;
            const sh = document.getElementById('mobileMenuSheet');
            const vis = el => !!el && getComputedStyle(el).display !== 'none' && !el.closest('[hidden]');
            openMobileMenu();
            const r = sh.getBoundingClientRect();
            const out = {open: sh.classList.contains('show'), fits: sh.scrollHeight <= sh.clientHeight + 1 && r.height <= innerHeight && r.top >= 0,
                         h: Math.round(r.height), sc: sh.scrollHeight, adv0: vis(document.getElementById('mmAdv')), sub0: vis(document.getElementById('mmSub'))};
            const secs = [...sh.querySelectorAll('#mmMain > .mm-sec')].map(e => e.textContent.trim());
            out.secs = secs;
            out.valMap0 = document.getElementById('mmValMap').textContent;
            // 背景地図 → 2階層目 → 航空写真 → 戻る
            openMmSub('map');
            out.subMap = vis(document.getElementById('mmSub')) && !vis(document.getElementById('mmMain'))
                         && [...sh.querySelectorAll('.mm-subpane.show .mm-map[data-bm]')].filter(vis).length === 5;
            sh.querySelector('.mm-map[data-bm="gsi_photo"]').click();
            closeMmSub();
            out.valMap1 = document.getElementById('mmValMap').textContent;
            out.backMain = vis(document.getElementById('mmMain')) && !vis(document.getElementById('mmSub'));
            setBaseMap(keepBm);
            // 大きさ：3段階だけ。極大を選んである時はその行も出る
            setLabelSize(0); openMmSub('size');
            out.lsz3 = [...sh.querySelectorAll('.mm-map[data-lsz]')].filter(vis).length;
            setLabelSize(3);
            out.lsz4 = [...sh.querySelectorAll('.mm-map[data-lsz]')].filter(vis).length;
            setLabelSize(keepL); closeMmSub();
            // 上級者向けを開く／閉じる
            toggleMmAdv();
            out.adv1 = vis(document.getElementById('mmAdv')) && vis(document.getElementById('mmSwVia'));
            toggleMmAdv();
            out.adv2 = vis(document.getElementById('mmAdv'));
            closeMobileMenu();
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        page.set_viewport_size({'width': 390, 'height': 812})
        page.evaluate("()=>{ leafMap.invalidateSize(); }")
        chk('機能', '390×844 でメニューが1画面に収まり、2階層目・上級者向け・3段階が動く',
            isinstance(mm, dict) and mm.get('open') and mm.get('fits') and mm.get('adv0') is False and mm.get('sub0') is False
            and mm.get('secs') == ['コース', '歩くとき', '地図の見せ方'] and mm.get('subMap') and '航空写真' in mm.get('valMap1', '')
            and mm.get('backMain') and mm.get('lsz3') == 3 and mm.get('lsz4') == 4 and mm.get('adv1') and mm.get('adv2') is False,
            str(mm)[:260])

        # v126: PC（1024px）で 文字なしボタン0・同じ文字のボタン0・上バー1行、右上と「その他」のポップオーバーが動く
        page.set_viewport_size({'width': 1024, 'height': 700})
        pc3 = page.evaluate("""()=>{ try{
            leafMap.invalidateSize(); closePcPops(); closeShareSheet();
            const vis = el => { if (!el) return false; const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
                                return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
            const s2 = document.getElementById('s2');
            const btns = [...s2.querySelectorAll('button')].filter(vis);
            const noText = btns.filter(b => !b.textContent.trim()).map(b => b.id || b.className.slice(0, 20));
            const texts = btns.map(b => b.textContent.trim().replace(/\\s+/g, ' '));
            const dup = texts.filter((t, i) => texts.indexOf(t) !== i);
            const hdr = document.getElementById('hdr').getBoundingClientRect();
            const rail = document.getElementById('tbar').getBoundingClientRect(), map = document.getElementById('mapWrap').getBoundingClientRect();
            const out = {noText, dup, nBtn: btns.length, hdrH: Math.round(hdr.height),
                         railIn: rail.left >= map.left && rail.top >= map.top && rail.bottom < map.bottom - 60,
                         hint: document.getElementById('tbar-st').textContent};
            togglePcPop('popMap', document.getElementById('btnBaseMap'));
            out.popMapOpen = vis(document.getElementById('popMap'));
            document.querySelector('#popMap [data-bm="gsi_photo"]').click();
            out.bm = _baseMapId; out.pill = document.getElementById('bmPillTxt').textContent;
            setBaseMap('osm'); closePcPops();
            togglePcPop('popLegend', document.getElementById('btnLegend'));
            out.legendOpen = vis(document.getElementById('popLegend'));
            out.legendRows = document.querySelectorAll('#pcLegendBody .sh-lg').length;
            togglePcPop('popMore', document.getElementById('btnMore'));
            out.moreOpen = vis(document.getElementById('popMore')) && !vis(document.getElementById('popLegend'));
            out.moreRows = [...document.querySelectorAll('#popMore .pp-row')].filter(vis).length;
            const keepM = manualMode; document.getElementById('btnManual').click(); out.manualFlip = manualMode !== keepM;
            if (manualMode !== keepM) toggleManualMode();
            closePcPops();
            setMode('via'); out.hintVia = document.getElementById('tbar-st').textContent; setMode('wp');
            toggleViewMode();
            out.viewHidden = !vis(document.getElementById('tbar')) && !vis(document.getElementById('pcHint')) && vis(document.getElementById('pcTr'))
                             && document.getElementById('btnViewTxt').textContent === '編集にもどる';
            toggleViewMode();
            out.viewBack = document.getElementById('btnViewTxt').textContent === '歩く人の見え方' && !document.body.classList.contains('viewing');
            out.closedAll = !document.querySelector('.pc-pop.show');
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        page.set_viewport_size({'width': 390, 'height': 812})
        page.evaluate("()=>{ leafMap.invalidateSize(); }")
        chk('機能', 'PC（1024px）：文字なしボタン0・同じ文字のボタン0・上バー1行、道具3群とポップオーバーが動く',
            isinstance(pc3, dict) and pc3.get('noText') == [] and pc3.get('dup') == [] and pc3.get('nBtn', 0) >= 8
            and pc3.get('hdrH', 99) <= 60 and pc3.get('railIn') and pc3.get('hint') == 'クリックでスポットを追加'
            and pc3.get('popMapOpen') and pc3.get('bm') == 'gsi_photo' and pc3.get('pill') == '航空写真'
            and pc3.get('legendOpen') and pc3.get('legendRows', 0) >= 2 and pc3.get('moreOpen') and pc3.get('moreRows') == 12
            and pc3.get('manualFlip') and pc3.get('hintVia') == 'ルート線の上をクリックして道順を変える'
            and pc3.get('viewHidden') and pc3.get('viewBack') and pc3.get('closedAll'), str(pc3)[:300])

        # v127: 標高は同じ点を二度取りに行かない。elevs を読み込むと0回。静かな書き足しは routes/elevs だけ・未保存中は書かない
        pf = page.evaluate("""()=>{ return (async()=>{ try{
            const keepFetch = window.fetch, keepC = getCourses(), keepE = Object.assign({}, elevCache), keepED = _elevData, keepD = _dirty;
            let calls = 0;
            window.fetch = (u, o) => { if (String(u).indexOf('getelevation') >= 0) { calls++; return Promise.resolve({json: () => Promise.resolve({elevation: 123.4})}); }
                                       return keepFetch(u, o); };
            const pts = [[35.15, 134.44], [35.151, 134.441], [35.152, 134.442], [35.153, 134.443], [35.154, 134.444]];
            elevCache = {};
            const e1 = await _fetchElevs(pts); const c1 = calls;
            const e2 = await _fetchElevs(pts); const c2 = calls - c1;
            _elevData = {pts, elevs: e2};
            const inUse = _elevsInUse();
            // 保存 → elevs が入る → 読み込みで elevCache に戻る
            const data = buildCurrentSaveData();
            const savedKeys = Object.keys(data.elevs || {}).length;
            elevCache = {};
            Object.keys(data.elevs).forEach(k => { const v = +data.elevs[k]; if (isFinite(v)) elevCache[k] = v; });   // loadCourseData と同じ復元式
            const e3 = await _fetchElevs(pts); const c3 = calls - c1 - c2;
            // 静かな書き足し：保存データに routes/elevs だけが入り、名前・savedAt・未保存フラグは変わらない
            const stored = JSON.parse(JSON.stringify(data)); delete stored.routes; delete stored.elevs; stored.savedAt = 'T0';
            setCourses([stored]); currentCourseId = stored.id;
            const rw = routeWps(); const k0 = _segKey(rw[0].lat, rw[0].lng, rw[1].lat, rw[1].lng);
            const keepSeg = segCache[k0]; segCache[k0] = [[rw[0].lat, rw[0].lng], [(rw[0].lat + rw[1].lat) / 2, (rw[0].lng + rw[1].lng) / 2], [rw[1].lat, rw[1].lng]];
            _dirty = true;  const wroteDirty = _persistDerivedQuietly(); const afterDirty = getCourses()[0];
            _dirty = false; const wrote = _persistDerivedQuietly(); const after = getCourses()[0];
            if (keepSeg) segCache[k0] = keepSeg; else delete segCache[k0];
            window.fetch = keepFetch; setCourses(keepC); elevCache = keepE; _elevData = keepED; _dirty = keepD;
            return {c1, c2, c3, ok1: e1.every(v => v === 123.4), ok3: e3.every(v => v === 123.4), inUse: Object.keys(inUse).length, savedKeys,
                    wroteDirty, dirtyUntouched: !afterDirty.routes && !afterDirty.elevs,
                    wrote, routesN: Object.keys(after.routes || {}).length, elevsN: Object.keys(after.elevs || {}).length,
                    nameSame: after.name === stored.name, savedAtSame: after.savedAt === 'T0', wpsSame: after.wps.length === stored.wps.length, dirtyRestored: _dirty === keepD};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        chk('機能', '標高は同じ点を二度取らず、同梱を読めば0回。静かな書き足しは routes/elevs だけ',
            isinstance(pf, dict) and pf.get('c1') == 5 and pf.get('c2') == 0 and pf.get('c3') == 0 and pf.get('ok1') and pf.get('ok3')
            and pf.get('inUse') == 5 and pf.get('savedKeys') == 5 and pf.get('wroteDirty') is False and pf.get('dirtyUntouched')
            and pf.get('wrote') is True and pf.get('routesN', 0) >= 1 and pf.get('elevsN') == 5 and pf.get('nameSame') and pf.get('savedAtSame')
            and pf.get('wpsSame') and pf.get('dirtyRestored') is True, str(pf)[:300])

        # v128: 10個置くのに画面切替0回。編集画面は4つ大きく・残りは畳む・畳んだ中からも選べる
        pl = page.evaluate("""()=>{ try{
            const keepW = wps.slice(), keepU = undoStack.length, keepR = redoStack.length, keepMode = mode, keepView = viewMode;
            viewMode = false; setMode('wp'); hideWpPicker(); closeModal();
            const n0 = wps.length; let switches = 0;
            for (let i = 0; i < 10; i++) {
              onMapClick({latlng: L.latLng(35.1525 + i * 0.0004, 134.4450 + i * 0.0003), originalEvent: {}});
              if (document.getElementById('mOver')?.classList.contains('show')) switches++;
              const pk = document.getElementById('wpTypePicker');
              if (_wpPickerLatlng !== null || (pk && getComputedStyle(pk).display !== 'none')) switches++;
            }
            const added = wps.length - n0, allCourse = wps.slice(n0).every(w => w.type === 'course');
            const w = wps[wps.length - 1]; openModal(w.id);
            const bigs = [...document.querySelectorAll('#mTypeChips .tc-chip.big')].map(b => b.textContent.trim());
            const restHidden = !document.querySelector('#mTypeChips .tc-row.rest');
            document.querySelector('#mTypeChips .tc-more').click();
            const restN = document.querySelectorAll('#mTypeChips .tc-row.rest .tc-chip').length;
            _pickType('parking');
            const selVal = document.getElementById('mType').value, onChip = (document.querySelector('#mTypeChips .tc-chip.on') || {}).textContent;
            saveModal(); closeModal();
            const savedType = w.type;
            // 後片付け：置いた10個を消し、取り消し履歴も元の長さへ
            wps.slice(n0).forEach(x => { if (x.marker) leafMap.removeLayer(x.marker); });
            wps.length = 0; keepW.forEach(x => wps.push(x));
            undoStack.length = keepU; redoStack.length = keepR; viewMode = keepView; setMode(keepMode);
            redrawStraight(); redrawList();
            return {added, allCourse, switches, bigs, restHidden, restN, selVal, onChip: (onChip || '').trim(), savedType};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '10個置くのに画面切替0回。編集画面は4つ大きく、残りは畳んだ中から選べる',
            isinstance(pl, dict) and pl.get('added') == 10 and pl.get('allCourse') and pl.get('switches') == 0
            and pl.get('bigs') == ['1コースポイント', '◎ビュースポット', '碑史跡・記念碑', '★飲食店・ショップ ★'] and pl.get('restHidden')
            and pl.get('restN', 0) >= 5 and pl.get('selVal') == 'parking' and pl.get('onChip') == 'P駐車場' and pl.get('savedType') == 'parking',
            str(pl)[:260])

        # v130: コースを削除すると「元に戻す」が出て、押すと同じ位置・同じ中身で戻る。10秒たつと確定
        du = page.evaluate("""()=>{ try{
            const keepC = getCourses(), keepP = _delPending;
            const mk = (id, name) => ({id, name, wps: [], vps: [], customRoads: [], customPaths: [], savedAt: 'T' + id});
            setCourses([mk(9101, 'A'), mk(9102, 'B'), mk(9103, 'C')]);
            deleteCourse(9102);
            const t = document.getElementById('undoToast');
            const out = {afterDel: getCourses().map(c => c.name).join(''), toast: !!t, btn: t ? t.querySelector('button').textContent : '',
                         msg: t ? t.querySelector('span').textContent : '', pending: !!_delPending};
            t.querySelector('button').click();
            out.afterUndo = getCourses().map(c => c.name).join(''); out.toastGone = !document.getElementById('undoToast'); out.pendingAfter = !!_delPending;
            out.sameData = getCourses()[1].savedAt === 'T9102';
            // もう一度消して、確定させる（10秒待つ代わりに確定処理を直接呼ぶ）
            deleteCourse(9101); _finalizeDelete();
            out.afterFinal = getCourses().map(c => c.name).join(''); out.toastGone2 = !document.getElementById('undoToast');
            undoDeleteCourse(); out.noResurrect = getCourses().map(c => c.name).join('');
            setCourses(keepC); _delPending = keepP; renderCourseList();
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', 'コース削除は「元に戻す」で同じ位置に戻り、確定後は戻らない',
            isinstance(du, dict) and du.get('afterDel') == 'AC' and du.get('toast') and du.get('btn') == '元に戻す' and '「B」を削除しました' == du.get('msg')
            and du.get('pending') and du.get('afterUndo') == 'ABC' and du.get('toastGone') and du.get('pendingAfter') is False and du.get('sameData')
            and du.get('afterFinal') == 'BC' and du.get('toastGone2') and du.get('noResurrect') == 'BC', str(du)[:260])

        # v131: PC で なぞる／道を描く／現在地／並べ替え画面 が動き、高低差は1回で開く。スマホの帯は展開すると詳細（4つの数字）
        page.set_viewport_size({'width': 1024, 'height': 700})
        pa = page.evaluate("""()=>{ try{
            leafMap.invalidateSize();
            const vis = el => { if (!el) return false; const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return cs.display !== 'none' && r.width > 0 && r.height > 0; };
            const out = {};
            document.getElementById('btnDraw').click(); out.draw = mode === 'draw' && _drawActive === true && document.getElementById('btnDraw').classList.contains('on');
            setMode('wp'); out.drawOff = _drawActive === false;
            const keepFeat = _customOn_; if (!keepFeat) toggleCustomFeature();
            document.getElementById('btnCustom').click(); out.custom = _customMode_ === true && document.getElementById('btnCustom').classList.contains('on');
            document.getElementById('btnCustom').click(); out.customOff = _customMode_ === false;
            if (!keepFeat) toggleCustomFeature();
            out.gps = vis(document.getElementById('btnGps')) && document.getElementById('btnGps').textContent.trim() === '現在地';
            document.querySelector('.wp-ro-btn').click();
            const rs = document.getElementById('reorderSheet'); const rr = rs ? rs.getBoundingClientRect() : null;
            out.reorder = !!rs && vis(rs) && rr.width <= 480 && Math.abs((rr.left + rr.right) / 2 - innerWidth / 2) < 2 && rs.querySelectorAll('.ro-row').length >= 2;
            closeReorderSheet();
            // 高低差：1回で開く
            closeElevModal(); const panel = document.getElementById('elevDetailPanel'); panel.style.display = '';
            toggleElevPanel(); out.elevOnce = getComputedStyle(panel).display !== 'none'; closeElevModal();
            togglePcPop('popMore', document.getElementById('btnMore'));
            out.moreRows = [...document.querySelectorAll('#popMore .pp-row')].filter(vis).map(b => b.textContent.trim());
            closePcPops();
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        page.set_viewport_size({'width': 390, 'height': 812})
        pb = page.evaluate("""()=>{ try{
            leafMap.invalidateSize();
            const keepE = _elevData;
            if (!_elevData) { const pts = _sampleCoords(_lastRouteCoords || buildStraightCoords(), 50); _elevData = {pts, elevs: pts.map((p, i) => 300 + (i % 7) * 3)}; }
            _setElevExpanded(true);
            const n = document.querySelectorAll('#mobileElevStatsRow .mev-stat').length, txt = document.getElementById('mobileElevStatsRow').textContent;
            const svgH = document.getElementById('mobileElevSvg').getBoundingClientRect().height;
            _setElevExpanded(false); _elevData = keepE;
            return {n, ok: /最高/.test(txt) && /最低/.test(txt) && /上り/.test(txt) && /下り/.test(txt), svgH: Math.round(svgH)};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', 'PC：なぞる・道を描く・現在地・並べ替え画面が動き、高低差は1回で開く',
            isinstance(pa, dict) and pa.get('draw') and pa.get('drawOff') and pa.get('custom') and pa.get('customOff') and pa.get('gps')
            and pa.get('reorder') and pa.get('elevOnce') and '自分で描いた道を使う' in pa.get('moreRows', []) and '描いた道に吸い付く' in pa.get('moreRows', []),
            str(pa)[:260])
        chk('機能', 'スマホ：高低差の帯を開くと詳細（最高・最低・上り・下り）が出る',
            isinstance(pb, dict) and pb.get('n') == 4 and pb.get('ok') and pb.get('svgH', 0) >= 100, str(pb)[:160])

        # v132: 位置を差し替えると「次のスポット」の距離が更新され、ゴールに着くと変わる。向きは矢印＋方角
        #（前の検査の経路計算が途中で終わると _lastRouteCoords が差し替わるので、落ち着くのを待ち、検査中は固定の線を使う）
        try: page.wait_for_function("() => !routingTimer && getComputedStyle(document.getElementById('rtMsg')).display === 'none'", timeout=15000)
        except Exception: pass
        nb = page.evaluate("""()=>{ try{
            const keepV = viewMode, keepCls = document.body.className, keepPos = _walkPos, keepH = _walkHeading, keepLRC = _lastRouteCoords;
            _lastRouteCoords = [[35.152, 134.440], [35.152, 134.445], [35.152, 134.450], [35.152, 134.455], [35.152, 134.460]];   // 西→東の直線 約1.8km
            viewMode = true; document.body.classList.add('viewing');
            _walkPos = null; renderNextBar();
            const bar = document.getElementById('nextBar'), tx = document.getElementById('nbText'), ar = bar.querySelector('.nb-arrow');
            const out = {shown0: !bar.hidden && getComputedStyle(bar).display !== 'none', hint: tx.textContent};
            const c = _lastRouteCoords; const n = c.length;
            const num = s => parseFloat((s.match(/([\\d.]+)(km|m)/) || [])[1]) * ((s.match(/([\\d.]+)(km|m)/) || [])[2] === 'km' ? 1000 : 1);
            _onWalkerPos(c[0][0], c[0][1], 5);                        // 出発点
            out.t1 = tx.textContent; out.d1 = num(tx.textContent); out.rot1 = ar.style.transform;
            const i2 = Math.floor(n * 0.25);
            _onWalkerPos(c[i2][0], c[i2][1], 5);                      // 少し進む
            out.t2 = tx.textContent; out.d2 = num(tx.textContent);
            const p1 = _routeProgress(c[0][0], c[0][1]).along, p2 = _routeProgress(c[i2][0], c[i2][1]).along;
            out.advanced = p2 > p1 + 50;
            const sameNext = out.t1.split(' まで')[0] === out.t2.split(' まで')[0];
            out.closer = !sameNext || out.d2 < out.d1;
            _onWalkerPos(c[n-1][0], c[n-1][1], 5);                    // ゴール
            out.t3 = tx.textContent; out.done = bar.classList.contains('done');
            // 向き：コンパスが無ければ北=0の矢印。あれば体の向き基準
            _onWalkerPos(c[0][0], c[0][1], 5); const info = nextSpotInfo();
            _walkHeading = info.rot; renderNextBar(); out.rotWithHeading = ar.style.transform;
            _walkHeading = null;
            out.dirOk = /(北|南|東|西)/.test(out.t1) && /次：/.test(out.t1) && /まで/.test(out.t1);
            // 埋め込みでは出さない
            document.body.classList.add('embed'); renderNextBar(); out.embedHidden = bar.hidden; document.body.classList.remove('embed');
            viewMode = keepV; document.body.className = keepCls; _walkPos = keepPos; _walkHeading = keepH; _lastRouteCoords = keepLRC; renderNextBar();
            out.hiddenAfter = bar.hidden;
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '次のスポット：位置を差し替えると距離が更新され、ゴールで「着きました」、向きは矢印＋方角',
            isinstance(nb, dict) and nb.get('shown0') and '◎' in nb.get('hint', '') and nb.get('dirOk') and nb.get('d1', 0) > 0
            and nb.get('advanced') and nb.get('closer') and nb.get('t3') == 'ゴールに着きました' and nb.get('done')
            and nb.get('rotWithHeading') == 'rotate(0deg)' and nb.get('embedHidden') and nb.get('hiddenAfter'), str(nb)[:300])

        # v133: 位置を動かすと、高低差グラフの「いまここ」の丸が動く（30%→60%で右へ）。位置が無ければ出ない
        try: page.wait_for_function("() => !routingTimer && getComputedStyle(document.getElementById('rtMsg')).display === 'none'", timeout=15000)
        except Exception: pass
        eh = page.evaluate("""()=>{ try{
            const keepV = viewMode, keepCls = document.body.className, keepPos = _walkPos, keepE = _elevData, keepLRC = _lastRouteCoords;
            _lastRouteCoords = [];
            for (let i = 0; i <= 40; i++) _lastRouteCoords.push([35.152 + Math.sin(i / 4) * 0.0004, 134.440 + i * 0.0005]);   // 東へ進む波線 約1.8km
            { const pts = _sampleCoords(_lastRouteCoords, 50); _elevData = {pts, elevs: pts.map((p, i) => 300 + (i % 7) * 3)}; }
            viewMode = true; document.body.classList.add('viewing');
            _walkPos = null; _drawElevBand();
            const svg = document.getElementById('mobileElevSvg');
            const out = {none: !svg.querySelector('.ev-here')};
            const c = _lastRouteCoords, n = c.length;
            _routeProgress(c[0][0], c[0][1]);                          // 累積距離を作る
            const tot = _routeCum[n - 1];
            const at = f => { let i = 0; while (i < n - 1 && _routeCum[i] < tot * f) i++; return c[i]; };   // 距離で選ぶ（点の間隔は均一でない）
            // 実際の歩きと同じく、点を順にたどる（往復コースでは飛ぶと行きと帰りを取り違えるため）
            const ptAt = d => { let i = 1; while (i < n - 1 && _routeCum[i] < d) i++; const a = _routeCum[i-1], b = _routeCum[i], t = b > a ? Math.max(0, Math.min(1, (d - a) / (b - a))) : 0;
                                return [c[i-1][0] + (c[i][0] - c[i-1][0]) * t, c[i-1][1] + (c[i][1] - c[i-1][1]) * t]; };
            let walked = 0;
            const walkTo = f => { for (let d = walked; d <= tot * f; d += tot / 100) { const q = ptAt(d); _onWalkerPos(q[0], q[1], 5); walked = d; }
                                  const q = ptAt(tot * f); _onWalkerPos(q[0], q[1], 5); const e = svg.querySelector('.ev-here'); return e ? parseFloat(e.getAttribute('cx')) : null; };
            out.x30 = walkTo(0.3); out.a30 = _walkPos.along / tot; out.x60 = walkTo(0.6); out.a60 = _walkPos.along / tot;
            const vb = (svg.getAttribute('viewBox') || '0 0 360 46').split(' ').map(Number); const W = vb[2], PL = 34, PR = 10;
            out.inside = out.x30 > PL && out.x60 < W - PR + 0.5; out.moved = out.x60 > out.x30 + (W - PL - PR) * 0.15;
            viewMode = keepV; document.body.className = keepCls; _walkPos = keepPos; _elevData = keepE; _lastRouteCoords = keepLRC; _drawElevBand(); renderNextBar();
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '高低差グラフの「いまここ」は位置と一緒に動き、位置が無ければ出ない',
            isinstance(eh, dict) and eh.get('none') and eh.get('x30') is not None and eh.get('inside') and eh.get('moved')
            and abs(eh.get('a30', 0) - 0.3) < 0.06 and abs(eh.get('a60', 0) - 0.6) < 0.06, str(eh)[:220])

        # v134: 読み上げ：押すと名前＋解説を日本語で読み、もう一度で止まり、カードを閉じても止まる（音声は差し替えて数える）
        sp2 = page.evaluate("""()=>{ try{
            const keepSS = window.speechSynthesis, keepV = viewMode, calls = [], out = {};
            let cancels = 0;
            Object.defineProperty(window, 'speechSynthesis', {configurable: true, value: {speak: u => calls.push({t: u.text, l: u.lang}), cancel: () => cancels++, getVoices: () => [{lang: 'ja-JP', name: 'テスト'}]}});
            const wp = wps.find(w => w.type !== 'node'); const keepD = wp.desc; wp.desc = '検査用の解説です';
            viewMode = true; showViewInfo(wp.id);
            const b = document.getElementById('vipSay'); out.hasBtn = !!b && b.textContent.trim() === '🔊 読み上げ';
            b.click(); out.spoke = calls.length === 1 && calls[0].l === 'ja-JP' && calls[0].t.indexOf('検査用の解説です') >= 0 && calls[0].t.indexOf((wp.name || '').split('\\n')[0] || 'x') >= 0;
            out.stopLabel = b.textContent.trim() === '⏹ 止める' && _speaking === true;
            b.click(); out.stopped = _speaking === false && cancels >= 1 && b.textContent.trim() === '🔊 読み上げ';
            b.click(); const c2 = cancels; closeViewInfo(); out.closeStops = _speaking === false && cancels > c2;
            wp.desc = keepD; viewMode = keepV;
            Object.defineProperty(window, 'speechSynthesis', {configurable: true, value: keepSS});
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '読み上げ：名前＋解説を日本語で読み、もう一度で止まり、カードを閉じても止まる',
            isinstance(sp2, dict) and sp2.get('hasBtn') and sp2.get('spoke') and sp2.get('stopLabel') and sp2.get('stopped') and sp2.get('closeStops'), str(sp2)[:220])

        # v135: 自動の持ち歩きは、コース範囲のタイルを上限内で取り、コースごとに1回（取得先は差し替えて数える）
        oa = page.evaluate("""()=>{ return (async()=>{ try{
            const keepFetch = window.fetch, keepLS = localStorage.getItem(LS.offAuto); localStorage.removeItem(LS.offAuto);
            let tiles = 0;
            window.fetch = (u, o) => { if (/tile\\.openstreetmap|cyberjapandata|opentopomap|cartocdn|openstreetmap\\.fr/.test(String(u))) { tiles++; return Promise.resolve({ok: true}); } return keepFetch(u, o); };
            const n1 = await _autoOfflineForLink('kensa.json', {force: true, quiet: true}); const t1 = tiles;
            const n2 = await _autoOfflineForLink('kensa.json', {force: true, quiet: true}); const t2 = tiles - t1;
            const n3 = await _autoOfflineForLink('kensa.json', {force: true, quiet: true, redo: true}); const t3 = tiles - t1 - t2;
            const rec = JSON.parse(localStorage.getItem(LS.offAuto) || '{}');
            window.fetch = keepFetch; if (keepLS === null) localStorage.removeItem(LS.offAuto); else localStorage.setItem(LS.offAuto, keepLS);
            return {n1, t1, n2, t2, n3, t3, recorded: !!(rec['kensa.json'] && rec['kensa.json'].n === n1), cap: n1 <= OFFLINE_AUTO_WIFI_TILES};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        chk('機能', '自動の持ち歩き：コース範囲のタイルを上限内で取り、コースごとに1回（やり直し指定で再取得）',
            isinstance(oa, dict) and oa.get('n1', 0) > 0 and oa.get('t1') == oa.get('n1') and oa.get('n2') == 0 and oa.get('t2') == 0
            and oa.get('n3') == oa.get('n1') and oa.get('recorded') and oa.get('cap'), str(oa)[:200])

        # v135: iPhone の幅（402×874・375×812）で、見えている要素が画面からはみ出さない（ボタン・帯・札を含む）
        _ov = {}
        for _w, _h in ((402, 874), (375, 812)):
            page.set_viewport_size({'width': _w, 'height': _h})
            _ov[_w] = page.evaluate("""()=>{ try{
                leafMap.invalidateSize(); closeMobileMenu(); closeShareSheet(); closePcPops();
                const vw = innerWidth, bad = [];
                document.querySelectorAll('body *').forEach(el => { const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden') return;
                  if (el.closest('.leaflet-pane') || el.closest('.leaflet-control-container') || el.closest('#map')) return;
                  const r = el.getBoundingClientRect(); if (r.width > 0 && (r.right > vw + 1 || r.left < -1)) bad.push((el.id || el.className.toString().slice(0, 24)) + ':' + Math.round(r.left) + '-' + Math.round(r.right)); });
                return {vw, sw: document.documentElement.scrollWidth, bad: bad.slice(0, 8)};
              }catch(e){ return 'ERR:'+e.message; } }""")
        page.set_viewport_size({'width': 390, 'height': 812}); page.evaluate("()=>{ leafMap.invalidateSize(); }")
        chk('機能', 'iPhone の幅（402・375）で、見えている要素が画面からはみ出さない',
            all(isinstance(v, dict) and v.get('sw') == v.get('vw') and v.get('bad') == [] for v in _ov.values()), str(_ov)[:220])

        # v136: 長い通知が375px幅に収まる／続けて2回削除しても新しい「元に戻す」が残る
        page.set_viewport_size({'width': 375, 'height': 812})
        rv = page.evaluate("""()=>{ return (async () => { try{
            showToast('👁 歩く人の見え方：スポットをタップすると写真・解説が出ます（検査用の長い文）');
            const t = [...document.querySelectorAll('#toastBox .toast')].pop(); const r = t.getBoundingClientRect(); t.remove();
            const out = {toastIn: r.left >= 0 && r.right <= innerWidth, w: Math.round(r.width)};
            const keepC = getCourses(), keepP = _delPending;
            const mk = (id, name) => ({id, name, wps: [], vps: [], customRoads: [], customPaths: [], savedAt: 'T'});
            setCourses([mk(9201, 'A'), mk(9202, 'B'), mk(9203, 'C')]);
            _showUndoToast('A', () => {}, 400); _delPending = {course: mk(9201, 'A'), index: 0};   // 前の削除（400ms後に確定が走るはずだった）
            deleteCourse(9202);
            await new Promise(res => setTimeout(res, 700));
            out.newToastKept = !!document.getElementById('undoToast') && document.getElementById('undoToast').textContent.indexOf('「B」') >= 0;
            out.pendingKept = !!_delPending && _delPending.course.name === 'B';
            document.querySelector('#undoToast button').click(); out.restored = getCourses().map(c => c.name).join('') === 'ABC';
            _finalizeDelete(); setCourses(keepC); _delPending = keepP; renderCourseList();
            return out;
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        page.set_viewport_size({'width': 390, 'height': 812}); page.evaluate("()=>{ leafMap.invalidateSize(); }")
        chk('機能', '長い通知が375px幅に収まり、続けて2回削除しても新しい「元に戻す」が残って戻せる',
            isinstance(rv, dict) and rv.get('toastIn') and rv.get('newToastKept') and rv.get('pendingKept') and rv.get('restored'), str(rv)[:200])

        # v137: 心得：追記が保存データに入り、配布シートに標準＋追記が載り、読む画面と書く画面が動き、読み上げ文に3見出しが入る
        kk = page.evaluate("""()=>{ try{
            const keepK = courseInfo.kokoroe, keepD = _dirty, keepV = viewMode, keepSS = window.speechSynthesis;
            const calls = [];
            Object.defineProperty(window, 'speechSynthesis', {configurable: true, value: {speak: u => calls.push(u.text), cancel: () => {}, getVoices: () => []}});
            courseInfo.kokoroe = '5月は農道を譲ってください';
            const out = {saved: buildCurrentSaveData().kokoroe === '5月は農道を譲ってください'};
            const html = _sheetHtml('data:,', 800);
            out.sheet = html.indexOf('sh-kokoroe') >= 0 && html.indexOf('田畑や私有地には立ち入らない') >= 0 && html.indexOf('5月は農道を譲ってください') >= 0;
            viewMode = true; openKokoroeSheet('view');
            const sh = document.getElementById('kokoroeSheet');
            out.viewShown = getComputedStyle(sh).display !== 'none' && document.getElementById('kkEdit').hidden && !document.getElementById('kkCustom').hidden
                            && document.getElementById('kkCustom').textContent.indexOf('5月は農道') >= 0;
            document.getElementById('kkSay').click(); out.spoken = calls.length === 1 && /配慮する/.test(calls[0]) && /5月は農道/.test(calls[0]);
            closeKokoroeSheet(); viewMode = false;
            openKokoroeSheet('edit');
            out.editShown = !document.getElementById('kkEdit').hidden && document.getElementById('kkText').value === '5月は農道を譲ってください';
            document.getElementById('kkText').value = 'クマ鈴をお持ちください'; _dirty = false; saveKokoroeSheet();
            out.savedEdit = courseInfo.kokoroe === 'クマ鈴をお持ちください' && _dirty === true;
            renderShareInfo(); out.shareRow = document.getElementById('ssKokoroe').textContent.indexOf('追記') >= 0;
            courseInfo.kokoroe = keepK; _dirty = keepD; viewMode = keepV;
            Object.defineProperty(window, 'speechSynthesis', {configurable: true, value: keepSS});
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '心得：追記が保存され、配布シートに標準＋追記、読む／書く画面と読み上げが動く',
            isinstance(kk, dict) and all(kk.get(k) for k in ('saved', 'sheet', 'viewShown', 'spoken', 'editShown', 'savedEdit', 'shareRow')), str(kk)[:220])

        # v138: 既定の速さ／区間の目安／帯：タップでカード・到着・約
        f3 = page.evaluate("""()=>{ try{
            const keepIdx = _walkSpeedIdx, keepLS = localStorage.getItem(LS.walkSpeed), keepV = viewMode, keepCls = document.body.className, keepPos = _walkPos, keepLRC = _lastRouteCoords;
            localStorage.removeItem(LS.walkSpeed); restoreSizePrefs(); const out = {def: _walkSpeed()};
            if (keepLS === null) localStorage.removeItem(LS.walkSpeed); else localStorage.setItem(LS.walkSpeed, keepLS); _walkSpeedIdx = keepIdx;
            _lastRouteCoords = [[35.152, 134.440], [35.152, 134.445], [35.152, 134.450], [35.152, 134.455], [35.152, 134.460]];
            const segs = _segmentMinutes(); out.segs = segs.length; out.segOk = segs.every(g => g.min >= 1 && g.distM >= 20 && g.from && g.to);
            const html = _sheetHtml('data:,', 800); out.sheet = segs.length ? html.indexOf('sh-segs') >= 0 && html.indexOf('区間の目安') >= 0 : true;
            viewMode = true; document.body.classList.add('viewing');
            const sp = _stampTargets().find(w => w.type !== 'start'); const c = _lastRouteCoords;
            _onWalkerPos(c[0][0], c[0][1], 60);
            const tx = document.getElementById('nbText');
            out.about = /約/.test(tx.textContent) && /約\\d+分/.test(tx.textContent);
            _onWalkerPos(sp.lat, sp.lng, 5);
            out.arrive = document.getElementById('nbLabel').textContent === '到着' && document.getElementById('nextBar').classList.contains('arrive') && _nextWpId === sp.id;
            closeViewInfo(); nextBarTap(); out.card = document.getElementById('viewInfoPanel').classList.contains('show'); closeViewInfo();
            viewMode = keepV; document.body.className = keepCls; _walkPos = keepPos; _lastRouteCoords = keepLRC; renderNextBar();
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '既定3km/h・区間の目安・帯のタップでカード・到着・精度が悪いと「約」',
            isinstance(f3, dict) and f3.get('def') == 3 and f3.get('segOk') and f3.get('sheet') and f3.get('about') and f3.get('arrive') and f3.get('card'), str(f3)[:220])

        # v139: コースの情報：書く→保存データ→配布シートと読む画面に出る。難易度の★
        ci = page.evaluate("""()=>{ try{
            const keepI = JSON.stringify(courseInfo.info || {}), keepD = _dirty, keepV = viewMode;
            courseInfo.info = {};
            openInfoSheet('edit');
            const out = {editShown: !document.getElementById('ciEdit').hidden && document.querySelectorAll('#ciFields input').length === COURSE_INFO_FIELDS.length};
            document.getElementById('ci_toilet').value = '出発点の公民館にあります'; document.getElementById('ci_car').value = '公民館に10台';
            _ciPickDiff('2'); _dirty = false; saveInfoSheet();
            out.saved = buildCurrentSaveData().info.toilet === '出発点の公民館にあります' && buildCurrentSaveData().info.diff === '2' && _dirty === true;
            out.count = _courseInfoCount() === 2;
            const html = _sheetHtml('data:,', 800);
            out.sheet = html.indexOf('sh-info') >= 0 && html.indexOf('出発点の公民館にあります') >= 0 && html.indexOf('★★☆') >= 0;
            viewMode = true; openInfoSheet('view');
            out.view = !document.getElementById('ciView').hidden && document.getElementById('ciView').textContent.indexOf('公民館に10台') >= 0 && document.getElementById('ciView').textContent.indexOf('★★☆') >= 0;
            closeInfoSheet(); viewMode = keepV; courseInfo.info = JSON.parse(keepI); _dirty = keepD; renderShareInfo(); _syncMmValues();
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', 'コースの情報：書く→保存→配布シートと読む画面、難易度の★', isinstance(ci, dict) and all(ci.get(k) for k in ('editShown', 'saved', 'count', 'sheet', 'view')), str(ci)[:220])

        # v140: スポット削除→「元に戻す」で戻る／通知が2つ重ならない／畳んだ種別がこのコースで使った順
        b1 = page.evaluate("""()=>{ try{
            const keepW = wps.slice(), keepU = undoStack.length, keepR = redoStack.length, keepV = viewMode, keepP = _delWpUndo;
            viewMode = false; closeModal();
            const w = addWp(35.1523, 134.4453, 'course'); w.name = '削除検査'; const id = w.id, n0 = wps.length;
            openModal(id); deleteEditing();
            const t = document.getElementById('undoToast');
            const out = {gone: !wps.some(x => x.id === id), toast: !!t && t.textContent.indexOf('削除検査') >= 0};
            t.querySelector('button').click();
            out.back = wps.some(x => x.id === id) && wps.length === n0;
            // 別の操作をした後は戻せない案内（取消で戻せる）
            openModal(id); deleteEditing(); addWp(35.1526, 134.4456, 'course'); const before = wps.length;
            document.getElementById('undoToast').querySelector('button').click();
            out.guarded = wps.length === before && !wps.some(x => x.id === id);
            // 通知の積み重ね
            showToast('一つ目の通知'); showToast('二つ目の通知');
            const ts = [...document.querySelectorAll('#toastBox .toast')].slice(-2).map(e => e.getBoundingClientRect());
            out.stacked = ts.length === 2 && (ts[0].bottom <= ts[1].top + 0.5 || ts[1].bottom <= ts[0].top + 0.5);
            document.querySelectorAll('#toastBox .toast').forEach(e => e.remove());
            // 種別の並び：駐車場を2つ置くと畳んだ側の先頭になる
            const p1 = addWp(35.1529, 134.4459, 'parking'), p2 = addWp(35.1531, 134.4461, 'parking');
            openModal(p1.id); document.querySelector('#mTypeChips .tc-more').click();
            out.order = (document.querySelector('#mTypeChips .tc-row.rest .tc-chip') || {}).textContent.trim() === 'P駐車場';
            closeModal();
            // 後片付け
            wps.slice().forEach(x => { if (!keepW.includes(x) && x.marker) leafMap.removeLayer(x.marker); });
            wps.length = 0; keepW.forEach(x => wps.push(x)); undoStack.length = keepU; redoStack.length = keepR; viewMode = keepV; _delWpUndo = keepP;
            _finalizeDelete(); redrawStraight(); redrawList();
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', 'スポット削除の「元に戻す」が戻し、別の操作の後は案内し、通知は重ならず、種別はこのコースで使った順',
            isinstance(b1, dict) and all(b1.get(k) for k in ('gone', 'toast', 'back', 'guarded', 'stacked', 'order')), str(b1)[:220])

        # v152: 作る人のメニューには「コースのことを書く」、歩く人には心得・情報の行
        wr = page.evaluate("""()=>{ try{
            const keepV = viewMode, keepCls = document.body.className;
            const vis = el => !!el && getComputedStyle(el).display !== 'none' && !el.closest('[hidden]');
            viewMode = false; document.body.classList.remove('viewing'); openMobileMenu();
            const out = {editHidden: !vis(document.getElementById('mmKokoroeRow')) && !vis(document.getElementById('mmInfoRow')), writeRow: vis([...document.querySelectorAll('#mmMain .mm-map')].find(e => (e.getAttribute('onclick') || '').indexOf("openMmSub('write')") >= 0))};
            openMmSub('write'); out.pane = vis(document.querySelector('.mm-subpane[data-sub="write"]')) && document.querySelectorAll('.mm-subpane[data-sub="write"] .mm-map').length === 3 && document.getElementById('mmSubT').textContent === 'コースのことを書く';
            closeMmSub(); closeMobileMenu();
            viewMode = true; document.body.classList.add('viewing'); openMobileMenu();
            out.walkRows = vis(document.getElementById('mmKokoroeRow')) && vis(document.getElementById('mmInfoRow'));
            closeMobileMenu(); viewMode = keepV; document.body.className = keepCls; _syncFindUi();
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', 'メニュー：作る人には「コースのことを書く」（3行の2階層目）、歩く人には心得・情報の行',
            isinstance(wr, dict) and all(wr.get(k) for k in ('editHidden', 'writeRow', 'pane', 'walkRows')), str(wr)[:200])

        # v151: 画面の上に出るもの（歩く人のカード・操作ガイド・メニュー・種類の選択）が body 直下にあり、実際に見える
        dom = page.evaluate("""()=>{ try{
            const ids = ['viewInfoPanel','helpModal','ctxMenu','wpTypePicker','viewBadge','offlineBadge','mobileMenuSheet','toastBox'];
            const inside = ids.filter(id => { const e = document.getElementById(id); return e && e.closest('#mOver'); });
            const keepV = viewMode, keepCls = document.body.className;
            viewMode = true; document.body.classList.add('viewing');
            const w = wps.find(x => x.type !== 'node'); closeModal(); showViewInfo(w.id);
            const pr = document.getElementById('viewInfoPanel').getBoundingClientRect(); const cardVisible = pr.width > 50 && pr.height > 30 && getComputedStyle(document.getElementById('viewInfoPanel')).display !== 'none';
            closeViewInfo(); viewMode = keepV; document.body.className = keepCls;
            openHelp(); const hr = document.querySelector('#helpModal .help-box').getBoundingClientRect(); const helpVisible = hr.width > 200 && hr.height > 100; closeHelp();
            return {inside, cardVisible, helpVisible};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '歩く人のカード・操作ガイドなどが編集画面の中に巻き込まれておらず、実際に画面に出る',
            isinstance(dom, dict) and dom.get('inside') == [] and dom.get('cardVisible') and dom.get('helpVisible'), str(dom)[:200])

        # v150: 置き場所の URL は GitHub Pages のときだけ組み立てる
        gh = page.evaluate("""()=>[_ghUploadUrlFor('editroom1980.github.io','/footpath-map/index.html'), _ghUploadUrlFor('editroom1980.github.io','/footpath-map/'), _ghUploadUrlFor('user.github.io','/index.html'), _ghUploadUrlFor('example.com','/a/index.html')]""")
        chk('機能', '置き場所（GitHub のアップロード画面）の URL：<user>.github.io/<repo>/ のときだけ',
            gh == ['https://github.com/editroom1980/footpath-map/upload/main', 'https://github.com/editroom1980/footpath-map/upload/main', None, None], str(gh)[:200])

        # v148: 自動保存：変更→1.5秒で保存され、ボタンが「保存済み」になる。くわしい設定は中身があるときだけ開く
        asv = page.evaluate("""async ()=>{ try{
            const keepFlag = window.__noAutoSave, keepId = currentCourseId, keepCourses = getCourses(), keepD = _dirty, keepName = courseInfo.name;
            window.__noAutoSave = false; courseInfo.name = courseInfo.name || '自動保存検査';
            _markDirty(); const out = {dirtyLabel: document.querySelector('.mob-save').textContent === '保存', pending: !!_autoSaveT};
            await new Promise(r => setTimeout(r, AUTOSAVE_MS + 900));
            out.saved = _dirty === false && _saveState === 'saved' && document.querySelector('.mob-save').textContent === '保存済み' && getCourses().some(c => c.id === currentCourseId);
            // くわしい設定：空なら閉じ、電話があれば開く
            const w = wps.find(x => x.type !== 'node'); const keepTel = w.tel; w.tel = ''; w.dwell = 0; openModal(w.id); out.closedWhenEmpty = document.getElementById('mMore').open === false; closeModal();
            w.tel = '090-0000-0000'; openModal(w.id); out.openWhenTel = document.getElementById('mMore').open === true; closeModal(); w.tel = keepTel;
            // 後片付け：検査で保存したコースを消す
            window.__noAutoSave = keepFlag; setCourses(keepCourses); currentCourseId = keepId; _dirty = keepD; courseInfo.name = keepName; _setSaveState(keepD ? 'dirty' : 'saved');
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '自動保存：変更→1.5秒で保存済みになる／くわしい設定は中身があるときだけ開く',
            isinstance(asv, dict) and all(asv.get(k) for k in ('dirtyLabel', 'pending', 'saved', 'closedWhenEmpty', 'openWhenTel')), str(asv)[:220])

        # v147: 改変の可否の門と保存／ゴールの1枚の合成
        ge = page.evaluate("""async ()=>{ try{
            const keepN = courseInfo.noEdit, keepD = _dirty;
            const out = {lock: _isLockedShare({shared:true, noEdit:true}) === true && _isLockedShare({noEdit:true}) === false && _isLockedShare({shared:true}) === false};
            courseInfo.noEdit = true; out.saved = buildCurrentSaveData().noEdit === true; courseInfo.noEdit = false; out.omit = buildCurrentSaveData().noEdit === undefined;
            openShareSheet(); toggleNoEdit(); out.row = courseInfo.noEdit === true && document.getElementById('ssEdit').textContent.indexOf('そのまま') >= 0; toggleNoEdit(); closeShareSheet();
            const cv0 = document.createElement('canvas'); cv0.width = 400; cv0.height = 300; const g0 = cv0.getContext('2d'); g0.fillStyle = '#99ccff'; g0.fillRect(0, 0, 400, 300);
            const cv = await _goalCompose(cv0.toDataURL('image/png'));
            const px = cv.getContext('2d').getImageData(10, 295, 1, 1).data, top = cv.getContext('2d').getImageData(10, 5, 1, 1).data;
            out.compose = cv.width === 400 && cv.height === 300 && (px[0] + px[1] + px[2]) < (top[0] + top[1] + top[2]) - 100;   // 下は帯で暗く、上は元の色のまま
            courseInfo.noEdit = keepN; _dirty = keepD; document.querySelectorAll('#toastBox .toast').forEach(e => e.remove());
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '改変の可否：配布ファイルにだけ効く門・保存に入る・配るの行で切り替え／ゴールの1枚：帯を焼き込む',
            isinstance(ge, dict) and all(ge.get(k) for k in ('lock', 'saved', 'omit', 'row', 'compose')), str(ge)[:220])

        # v146: 配る前の確認：手の✓が付いて保存に入る／自動の項目はコースの中身で決まる
        ck = page.evaluate("""()=>{ try{
            const keepC = JSON.stringify(courseInfo.check || {}), keepI = JSON.stringify(courseInfo.info || {}), keepD = _dirty;
            courseInfo.check = {}; courseInfo.info = {};
            openShareSheet();
            const out = {rows: document.querySelectorAll('#ssChecks .ss-li.ck').length === SHARE_CHECKS.length, none: document.getElementById('ssCheckN').textContent.indexOf('0 /') === 0 || !_shareCheckState('walked')};
            shareCheckTap('walked'); out.own = courseInfo.check.walked === true && document.querySelector('#ssChecks .ss-li.ck').classList.contains('on') && buildCurrentSaveData().check.walked === true;
            shareCheckTap('walked'); out.off = !courseInfo.check.walked && buildCurrentSaveData().check === undefined;
            out.auto0 = !_shareCheckState('info') && !_shareCheckState('contact');
            courseInfo.info = {toilet:'公民館', contact:'090'}; _renderShareChecks(); out.auto1 = _shareCheckState('info') && _shareCheckState('contact') && document.querySelectorAll('#ssChecks .ss-li.ck.on').length >= 2;
            closeShareSheet(); courseInfo.check = JSON.parse(keepC); courseInfo.info = JSON.parse(keepI); _dirty = keepD;
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '配る前の確認：6行・手の✓が保存に入る・外すと消える・自動の項目はコースの中身で決まる',
            isinstance(ck, dict) and all(ck.get(k) for k in ('rows', 'none', 'own', 'off', 'auto0', 'auto1')), str(ck)[:220])

        # v145: テーマ：適用で印・線・凡例の色が変わり、実線・太さも効き、保存に入り、標準に戻る
        th = page.evaluate("""()=>{ try{
            const keepT = courseInfo.theme || null, keepD = _dirty, keepLRC = _lastRouteCoords;
            const cw = wps.find(w => w.type === 'course') || wps.find(w => w.type !== 'node');
            applyTheme(null); const w0 = _routeWeight(), c0 = (WT.find(t => t.v === cw.type) || {}).c;
            applyTheme({preset:'mono', dash:false, width:'thick'});
            const out = {color: WT.find(t => t.v === 'course').c === '#222222' && LINE_STYLE.color === '#222222', solid: _routeDash() === null, thick: Math.abs(_routeWeight() / w0 - 1.4) < 0.01,
                         legend: _sheetLegend().indexOf('#222222') >= 0, icon: (function(){ const el = cw.marker && cw.marker.getElement(); return !el || el.innerHTML.indexOf('#222222') >= 0; })(), name: _themeName() === '白黒（実線・太）'};
            applyTheme({preset:'aki', route:'#1976D2'}); out.custom = LINE_STYLE.color === '#1976D2' && WT.find(t => t.v === 'course').c === '#BF360C' && _themeName() === '秋（線の色）';
            courseInfo.theme = {preset:'aki', route:'#1976D2', dash:true, width:'std'}; out.saved = buildCurrentSaveData().theme.preset === 'aki' && buildCurrentSaveData().theme.route === '#1976D2';
            courseInfo.theme = null; out.omit = buildCurrentSaveData().theme === undefined;
            applyTheme(null); out.back = (WT.find(t => t.v === cw.type) || {}).c === c0 && LINE_STYLE.color === '#E84040' && _routeDash() !== null && Math.abs(_routeWeight() - w0) < 0.01 && _sheetLegend().indexOf('#E84040') >= 0;
            courseInfo.theme = keepT; applyTheme(keepT); _dirty = keepD; _lastRouteCoords = keepLRC;
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', 'テーマ：印・線・凡例の色、実線・太さ、線の色だけ変える、保存に theme、標準に戻る',
            isinstance(th, dict) and all(th.get(k) for k in ('color', 'solid', 'thick', 'legend', 'icon', 'name', 'custom', 'saved', 'omit', 'back')), str(th)[:240])

        # v144: 周辺の情報：通信は差し替えて、候補→重複除外→選んで追加→1回で取り消し
        nb = page.evaluate("""async ()=>{ try{
            const keepFetch = window.fetch, keepV = viewMode, n0 = wps.length, keepU = undoStack.length, keepD = _dirty;
            const c = L.latLngBounds(wps.filter(w => w.type !== 'node').map(w => [w.lat, w.lng])).getCenter(); const w0 = wps.find(w => w.type !== 'node');
            window.fetch = async (url, opts) => { const u = String(url);
              if (u.indexOf('overpass') >= 0) return new Response(JSON.stringify({elements:[
                {type:'node', id:1, lat:c.lat + 0.001, lon:c.lng + 0.001, tags:{amenity:'cafe', name:'縁側カフェ', opening_hours:'Sa,Su 10:00-16:00', phone:'0790-00-0000'}},
                {type:'way', id:2, center:{lat:c.lat - 0.001, lon:c.lng}, tags:{amenity:'school', name:'飯見小学校'}},
                {type:'node', id:3, lat:c.lat, lon:c.lng + 0.0015, tags:{amenity:'toilets'}},
                {type:'node', id:4, lat:w0.lat, lon:w0.lng, tags:{amenity:'cafe', name:(w0.name || '').split('\\n')[0]}},
                {type:'node', id:5, lat:c.lat + 0.2, lon:c.lng, tags:{amenity:'cafe', name:'遠いカフェ'}}]}), {status:200});
              if (u.indexOf('wikipedia') >= 0) { if (u.indexOf('geosearch') >= 0) return new Response(JSON.stringify({query:{geosearch:[{pageid:99, title:'飯見の棚田', lat:c.lat + 0.0005, lon:c.lng - 0.0005}]}}), {status:200});
                return new Response(JSON.stringify({query:{pages:{'99':{pageid:99, title:'飯見の棚田', extract:'飯見の棚田は兵庫県宍粟市にある棚田である。日本の棚田百選に選ばれている。'}}}}), {status:200}); }
              return keepFetch(url, opts); };
            viewMode = false; openNearbySheet(); _nb.radius = 2000; _nbKinds().add('wiki');
            await nearbySearch();
            const names = _nb.cands.map(x => x.name);
            const out = {found: _nb.cands.length === 4 && names.includes('縁側カフェ') && names.includes('トイレ') && names.includes('飯見の棚田') && !names.includes('遠いカフェ'),
                         dup: !names.includes((w0.name || '').split('\\n')[0]) || (w0.name || '') === '',
                         layer: !!_nbLayer && _nbLayer.getLayers().length === _nb.cands.length,
                         listed: document.querySelectorAll('#nbList .nb-item').length === 4};
            _nbToggle(_nb.cands.find(x => x.name === '縁側カフェ').id); _nbToggle(_nb.cands.find(x => x.name === '飯見の棚田').id);
            out.btn = document.getElementById('nbAdd').textContent === '選んだ 2 件を追加';
            addNearbySelected();
            const a = wps.find(w => w.name === '縁側カフェ'), b = wps.find(w => w.name === '飯見の棚田');
            out.added = wps.length === n0 + 2 && !!a && a.type === 'shop' && a.onRoute === false && a.tel === '0790-00-0000' && a.desc.indexOf('営業時間') >= 0 && a.desc.indexOf('（情報：OpenStreetMap）') >= 0 && !!a.marker
                        && !!b && b.type === 'history' && b.desc.indexOf('棚田百選') >= 0 && b.desc.indexOf('Wikipedia「飯見の棚田」') >= 0;
            out.closed = document.getElementById('nearbySheet').style.display === 'none' && !_nbLayer;
            undoLast(); out.undone = wps.length === n0 && !wps.some(w => w.name === '縁側カフェ');
            window.fetch = keepFetch; viewMode = keepV; _nb.cands = []; _nb.sel = new Set(); undoStack.length = keepU; _dirty = keepD; document.querySelectorAll('#toastBox .toast').forEach(e => e.remove());
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '周辺の情報：候補（距離・重複を除外）→地図の薄い○→選んで追加（種別・説明・出典）→1回で取り消し',
            isinstance(nb, dict) and all(nb.get(k) for k in ('found', 'dup', 'layer', 'listed', 'btn', 'added', 'closed', 'undone')), str(nb)[:260])

        # v143: 発見：貼る→端末に残る→印とカード→送るファイル→作者が取り込む→消す。編集画面では印を出さない
        fd = page.evaluate("""async ()=>{ try{
            const keepV = viewMode, keepCls = document.body.className, keepId = currentCourseId, keepD = _dirty, keepLS = lsAvail() ? localStorage.getItem(LS.finds) : null;
            const cv = document.createElement('canvas'); cv.width = 60; cv.height = 40; const g = cv.getContext('2d'); g.fillStyle = '#396'; g.fillRect(0,0,60,40); const url = cv.toDataURL('image/png');
            viewMode = true; document.body.classList.add('viewing'); currentCourseId = 424242; loadFinds();
            const c = leafMap.getCenter();
            const f = await _addFind({lat:c.lat, lng:c.lng, word:'マンホールの蓋に鮎', by:'はなこ', photos:[url]});
            const out = {added: !!f && finds.length === 1 && !!f.marker && !!f.marker.getElement()};
            out.saved = ((_allFinds()['424242'] || []).length === 1) && (_allFinds()['424242'][0].word === 'マンホールの蓋に鮎');
            const t0 = Date.now(); while (Date.now() - t0 < 6000 && !f.marker.getElement().querySelector('.wp-sticker.find')) await new Promise(r => setTimeout(r, 100));
            out.sticker = !!f.marker.getElement().querySelector('.wp-sticker.find');
            showFindInfo(f.id); const panel = document.getElementById('viewInfoPanel'); out.card = panel.classList.contains('show') && panel.textContent.indexOf('マンホールの蓋に鮎') >= 0 && panel.textContent.indexOf('はなこ') >= 0; closeViewInfo();
            _syncFindUi(); out.ui = !document.getElementById('mobileFindBtn').hidden && document.getElementById('mmFinds').textContent.indexOf('1 件') >= 0;
            const payload = await _buildFindsPayload(); out.payload = payload.fpFinds === 1 && payload.finds.length === 1 && payload.finds[0].photos[0].indexOf('data:image') === 0 && payload.courseId === 424242;
            // 作者側：一覧に同じIDのコースを置いて取り込む（確認は自動で OK）
            const keepCourses = getCourses(); const keepConfirm = window.confirm; window.confirm = () => true;
            setCourses(keepCourses.concat([{id:424242, name:'発見検査', area:'', wps:[{id:1, type:'start', name:'S', lat:c.lat, lng:c.lng, photos:[]}], vps:[], maxWpId:1}]));
            currentCourseId = null; const imported = await _importFinds(JSON.parse(JSON.stringify(payload))); currentCourseId = 424242;
            const cc = getCourses().find(x => x.id === 424242); const nw = cc && cc.wps[cc.wps.length - 1];
            out.imported = imported === true && cc.wps.length === 2 && nw.type === 'other' && nw.name === 'マンホールの蓋に鮎' && nw.onRoute === false && nw.photos.length === 1 && cc.maxWpId === 2;
            window.confirm = keepConfirm; setCourses(keepCourses);
            // 編集画面に戻すと印は消える。消す→元に戻す
            viewMode = false; loadFinds(); out.hiddenInEdit = finds.length === 1 && !finds[0].marker;
            viewMode = true; loadFinds(); deleteFind(finds[0].id); out.deleted = finds.length === 0 && (_allFinds()['424242'] || []).length === 0;
            // 後片付け
            document.querySelectorAll('#toastBox .toast').forEach(e => e.remove()); _findUndo = null;
            finds.forEach(x => { if (x.marker) leafMap.removeLayer(x.marker); }); finds = [];
            if (lsAvail()) { if (keepLS === null) localStorage.removeItem(LS.finds); else localStorage.setItem(LS.finds, keepLS); }
            viewMode = keepV; document.body.className = keepCls; currentCourseId = keepId; _dirty = keepD; loadFinds(); closeViewInfo();
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '発見：貼る・残る・シールの印・カード・送るファイル・作者が取り込む・編集画面では出ない・消す',
            isinstance(fd, dict) and all(fd.get(k) for k in ('added', 'saved', 'sticker', 'card', 'ui', 'payload', 'imported', 'hiddenInEdit', 'deleted')), str(fd)[:260])

        # v142: シール：写真のある印が写真になり、名札がずれず、近い2つは束ねて「+1」、保存に stickers、写真は1024pxへ（検査用のスポット2つを置いて片づける）
        st = page.evaluate("""async ()=>{ try{
            const cv0 = document.createElement('canvas'); cv0.width = 40; cv0.height = 30; const g0 = cv0.getContext('2d'); g0.fillStyle = '#c33'; g0.fillRect(0,0,40,30);
            const url0 = cv0.toDataURL('image/png'); const n0 = wps.length, c = leafMap.getCenter(), keepD = _dirty;
            const mk = (id, lat, lng) => { const w = {id, type:'view', name:'シール検査' + id, desc:'', tel:'', dwell:0, fitBefore:true, fitAfter:true, onRoute:false, lat, lng, photos:[url0], labelDir:'auto', marker:null}; wps.push(w); buildWpMarker(w); return w; };
            const px = (lat, lng, dx, dy) => leafMap.layerPointToLatLng(leafMap.latLngToLayerPoint([lat, lng]).add([dx, dy]));
            const far = px(c.lat, c.lng, 120, 120); const a = mk(-9001, c.lat, c.lng), b = mk(-9002, far.lat, far.lng);
            courseInfo.stickers = true; refreshIcons();
            const t0 = Date.now(); while (Date.now() - t0 < 8000 && !(a.marker.getElement().querySelector('.wp-sticker') && b.marker.getElement().querySelector('.wp-sticker'))) await new Promise(r => setTimeout(r, 100));
            const out = {sticker: !!a.marker.getElement().querySelector('.wp-sticker .wp-stk-badge') && !!b.marker.getElement().querySelector('.wp-sticker'), saved: buildCurrentSaveData().stickers === true,
                         mem: [..._stickerMem.entries()].filter(([k]) => k === url0).map(([k, v]) => v === null ? 'null' : (v || '').length)};
            const tt = a.marker.getTooltip(); const want = Math.round(_stickerSize()[1] / 2 + 4); out.offset = !!tt && (Math.abs(tt.options.offset[1]) === want || Math.abs(tt.options.offset[0]) === want);
            const near = px(a.lat, a.lng, 10, 10); b.lat = near.lat; b.lng = near.lng; b.marker.setLatLng([b.lat, b.lng]); _clusterStickers();
            out.clustered = b.marker.getElement().style.opacity === '0' && /\\+\\d+/.test((a.marker.getElement().querySelector('.wp-stk-more') || {}).textContent || '');
            b.lat = far.lat; b.lng = far.lng; b.marker.setLatLng([b.lat, b.lng]); _clusterStickers();
            out.opened = b.marker.getElement().style.opacity !== '0' && !a.marker.getElement().querySelector('.wp-stk-more');
            // 写真の縮小：2000×1000 → 長辺1024
            const cv = document.createElement('canvas'); cv.width = 2000; cv.height = 1000; cv.getContext('2d').fillStyle = '#4a4'; cv.getContext('2d').fillRect(0,0,2000,1000);
            const blob = await new Promise(r => cv.toBlob(r, 'image/jpeg', 0.9)); const url = await compressImage(new File([blob], 'x.jpg', {type:'image/jpeg'}));
            const im = new Image(); await new Promise((r, j) => { im.onload = r; im.onerror = j; im.src = url; }); out.px = im.width === 1024 && im.height === 512;
            // 後片付け
            courseInfo.stickers = false;
            [a, b].forEach(w => { try { leafMap.removeLayer(w.marker); } catch(_) {} const i = wps.indexOf(w); if (i >= 0) wps.splice(i, 1); });
            _stickerMem.clear(); _stickerWait.clear(); refreshIcons(); redrawList(); _dirty = keepD;
            out.back = wps.length === n0 && buildCurrentSaveData().stickers === undefined;
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', 'シール：写真の印・名札の位置・近い2つを束ねて開く・保存に stickers・写真は長辺1024pxに',
            isinstance(st, dict) and all(st.get(k) for k in ('sticker', 'saved', 'offset', 'clustered', 'opened', 'px', 'back')), str(st)[:240])

        # v141: 案内：保存に入り、印が変わり、帯が手前で知らせ・ここで示し・過ぎたら確認、シートに載る、閲覧中はカード
        gd = page.evaluate("""()=>{ try{
            const keepV = viewMode, keepCls = document.body.className, keepPos = _walkPos, keepLRC = _lastRouteCoords, keepU = undoStack.length, keepD = _dirty;
            // 検査用の線：全スポットの南西を東へ走り、スポットの手前で終わる（＝スポットは全部「線の終わり」に写るので、案内300m地点は必ず次のスポットより手前）
            const minLat = Math.min(...wps.map(w => w.lat)), minLng = Math.min(...wps.map(w => w.lng));
            const la = minLat - 0.02, lo0 = minLng - 0.04;
            const line = [0, 1, 2, 3, 4].map(i => [la, lo0 + i * 0.005]);
            _lastRouteCoords = line; _routeCandidates(la, lo0);
            const at = d => { const c = line; let i = 1; while (i < c.length - 1 && _routeCum[i] < d) i++; const a = _routeCum[i-1], b = _routeCum[i], t = (d - a) / (b - a); return [c[i-1][0] + (c[i][0]-c[i-1][0])*t, c[i-1][1] + (c[i][1]-c[i-1][1])*t]; };
            const q = at(300);
            const vp = {id:'vTest141', segAfter: wps[0].id, order:0, fitBefore:true, fitAfter:true, lat:q[0], lng:q[1], marker:null,
                        guide:{kind:'turn', dir:'left', note:'橋を渡ってすぐ', photos:[]}};
            vps.push(vp); buildVpMarker(vp);
            const out = {saved: (buildCurrentSaveData().vps.find(v => v.id === vp.id).guide || {}).note === '橋を渡ってすぐ',
                         icon: !!(vp.marker && vp.marker.getElement() && vp.marker.getElement().querySelector('.vp-guide'))};
            const html = _sheetHtml('data:,', 800); out.sheet = html.indexOf('sh-guides') >= 0 && html.indexOf('橋を渡ってすぐ') >= 0;
            viewMode = true; document.body.classList.add('viewing'); _walkPos = null; _guideShown = {}; _guideConfirmed = {};
            const tx = document.getElementById('nbText');
            let p0 = at(200); _onWalkerPos(p0[0], p0[1], 5); out.ahead = /100m先 左/.test(tx.textContent) && /橋を渡ってすぐ/.test(tx.textContent);
            let p1 = at(295); _onWalkerPos(p1[0], p1[1], 5); out.here = /ここを左/.test(tx.textContent);
            closeViewInfo(); nextBarTap(); out.card = document.getElementById('viewInfoPanel').classList.contains('show') && document.getElementById('viewInfoPanel').textContent.indexOf('ここを左') >= 0; closeViewInfo();
            document.querySelectorAll('#toastBox .toast').forEach(e => e.remove());
            let p2 = at(340); _onWalkerPos(p2[0], p2[1], 5); out.confirmed = [...document.querySelectorAll('#toastBox .toast')].some(e => /この道で合っています/.test(e.textContent)) && !/橋を渡って/.test(tx.textContent);
            document.querySelectorAll('#toastBox .toast').forEach(e => e.remove());
            // 閲覧中に点を押しても編集メニューは開かず、案内が出る
            showViaCtxMenu(vp.id, 10, 10); out.viewGate = document.getElementById('ctxMenu').style.display !== 'block' && document.getElementById('viewInfoPanel').classList.contains('show'); closeViewInfo();
            // 後片付け
            try { leafMap.removeLayer(vp.marker); } catch(_) {}
            vps.splice(vps.indexOf(vp), 1);
            viewMode = keepV; document.body.className = keepCls; _walkPos = keepPos; _lastRouteCoords = keepLRC; undoStack.length = keepU; _dirty = keepD; _activeGuideId = null; renderNextBar();
            return out;
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '分岐の案内：保存・印・シート・帯（手前→ここを左→確認）・カード・閲覧中の門',
            isinstance(gd, dict) and all(gd.get(k) for k in ('saved', 'icon', 'sheet', 'ahead', 'here', 'card', 'confirmed', 'viewGate')), str(gd)[:240])

        # v121: バックアップからの日数・未反映の保存回数で色が変わり、書き出すと戻る。iPhone の案内は1回だけ
        bk = page.evaluate("""()=>{ return (async()=>{ try{
            const keepC = getCourses();
            const keys = [LS.backupAt, LS.saveCount, LS.firstSaveAt, LS.homeTipSeen];
            const keepLS = keys.map(k => localStorage.getItem(k));
            setCourses([buildCurrentSaveData()]);
            const ago = d => new Date(Date.now() - d*86400000).toISOString();
            const st = () => { renderCourseList(); const e = document.getElementById('backupInfo');
              return e.className + '|' + e.style.display + '|' + e.textContent; };
            keys.forEach(k => localStorage.removeItem(k));
            const none = st();
            localStorage.setItem(LS.backupAt, ago(61)); localStorage.setItem(LS.saveCount, '7'); const bad = st();
            localStorage.setItem(LS.backupAt, ago(31)); localStorage.setItem(LS.saveCount, '0'); const warn = st();
            localStorage.setItem(LS.backupAt, ago(1));  const ok = st();
            localStorage.setItem(LS.saveCount, '5');    const warn5 = st();
            localStorage.removeItem(LS.backupAt); localStorage.setItem(LS.firstSaveAt, ago(3)); localStorage.setItem(LS.saveCount, '1');
            const never = st();
            const origDl = window._downloadJsonAs; window._downloadJsonAs = () => {};
            await exportAllCourses(); window._downloadJsonAs = origDl;
            const after = st(); const cnt = localStorage.getItem(LS.saveCount);
            const origIos = window._isIosBrowserTab; window._isIosBrowserTab = () => true; localStorage.removeItem(LS.homeTipSeen);
            renderHomeTip(); const tipShown = getComputedStyle(document.getElementById('homeTip')).display !== 'none';
            dismissHomeTip(); const tipHid = getComputedStyle(document.getElementById('homeTip')).display === 'none';
            renderHomeTip(); const tipAgain = getComputedStyle(document.getElementById('homeTip')).display !== 'none';
            window._isIosBrowserTab = origIos;
            keys.forEach((k,i) => { if (keepLS[i] === null) localStorage.removeItem(k); else localStorage.setItem(k, keepLS[i]); });
            setCourses(keepC); renderCourseList();
            return {none, bad, warn, ok, warn5, never, after, cnt, tipShown, tipHid, tipAgain};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        ok_bk = (isinstance(bk, dict)
                 and '|none|' in bk.get('none', '')
                 and bk.get('bad', '').startswith('bk-bad|flex|') and '61 日' in bk['bad'] and '7 回' in bk['bad']
                 and bk.get('warn', '').startswith('bk-warn|flex|') and '31 日' in bk['warn']
                 and bk.get('ok', '').startswith('bk-ok|flex|') and '1 日前' in bk['ok']
                 and bk.get('warn5', '').startswith('bk-warn|') and '5 回' in bk['warn5']
                 and bk.get('never', '').startswith('bk-ok|') and '一度も' in bk['never']
                 and bk.get('after', '').startswith('bk-ok|') and '今日' in bk['after'] and bk.get('cnt') == '0'
                 and bk.get('tipShown') is True and bk.get('tipHid') is True and bk.get('tipAgain') is False)
        chk('機能', 'バックアップからの日数で色が変わり、書き出すと戻る。iPhone の案内は1回だけ', ok_bk, str(bk)[:200])

        # v120: 閲覧モードにすると、押せる編集操作が0になり、地図タップ・編集画面・印の移動が効かない
        vw = page.evaluate("""()=>{ try{
            if (viewMode) toggleViewMode();
            const w = s => { const e = document.querySelector(s); return e ? Math.round(e.getBoundingClientRect().width) : -1; };
            toggleViewMode();
            const viewing = document.body.classList.contains('viewing');
            const hidden = ['#mobileWpBtn','#mobileViaBtn','#mobileDrawBtn','#mobileCustomBtn','.mob-save','#mobileUndoBtn','#mobileRedoBtn'].map(w);
            const eb = document.getElementById('mobileEditBack'); const r = eb.getBoundingClientRect();
            const hit = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
            const backHit = r.width > 0 && !!(hit && (hit === eb || eb.contains(hit)));
            const n0 = wps.length;
            onMapClick({latlng:L.latLng(35.1521,134.4452), originalEvent:{clientX:120,clientY:300}});
            const picker = getComputedStyle(document.getElementById('wpTypePicker')).display;
            openModal(wps[0].id);
            const modal = document.getElementById('mOver').classList.contains('show');
            const dragOn = wps.filter(x => x.marker && x.marker.dragging && x.marker.dragging.enabled()).length;
            undoLast(); redoAction(); clearAll();
            const added = wps.length - n0;
            toggleViewMode();
            const withM = wps.filter(x => x.marker && x.marker.dragging).length;
            const restored = w('#mobileWpBtn') > 0 && !document.body.classList.contains('viewing')
              && wps.filter(x => x.marker && x.marker.dragging && x.marker.dragging.enabled()).length === withM;
            return {viewing, hidden, backHit, added, picker, modal, dragOn, restored};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '閲覧中は編集の操作が押せず、地図タップ・編集画面・印の移動が効かない',
            isinstance(vw, dict) and vw.get('viewing') is True and all(x == 0 for x in vw.get('hidden', [1]))
            and vw.get('backHit') is True and vw.get('added') == 0 and vw.get('picker') == 'none'
            and vw.get('modal') is False and vw.get('dragOn') == 0 and vw.get('restored') is True, str(vw)[:190])

        # v120: 配布リンクを開いた人への案内は、最初の1回だけ出る
        wt = page.evaluate("""()=>{ try{
            localStorage.removeItem(LS.walkTipSeen);
            document.body.classList.add('viewonly');
            const d = () => getComputedStyle(document.getElementById('walkTip')).display;
            maybeShowWalkTip(); const shown = d() !== 'none';
            dismissWalkTip();   const hid = d() === 'none';
            maybeShowWalkTip(); const again = d() !== 'none';
            const flag = !!localStorage.getItem(LS.walkTipSeen);
            document.body.classList.remove('viewonly');
            return {shown, hid, again, flag};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '歩く人への案内は最初の1回だけ出る',
            isinstance(wt, dict) and wt.get('shown') is True and wt.get('hid') is True
            and wt.get('again') is False and wt.get('flag') is True, str(wt)[:150])

        # v119: 保存データの道順を読み戻すと、経路サーバを1回も呼ばずに同じ道順が出る
        rt = page.evaluate("""()=>{ return (async()=>{ try{
            const snapshot = buildCurrentSaveData();                 // あとで元に戻すため
            const origFetch = window.fetch; let calls = 0;
            window.fetch = (u, o) => { const url = String((u && u.url) ? u.url : u);
              if (url.indexOf('/route/v1/') < 0) return origFetch(u, o);
              calls++;
              const m = url.match(/([\d.]+),([\d.]+);([\d.]+),([\d.]+)\?/);   // lng,lat;lng,lat
              const geo = {code:'Ok', routes:[{geometry:{coordinates:[[+m[1],+m[2]],
                [(+m[1]+ +m[3])/2 + 0.0004, (+m[2]+ +m[4])/2], [+m[3],+m[4]]]}}]};
              return Promise.resolve({ok:true, json:()=>Promise.resolve(geo)}); };
            _clearAllMarkers(); wps.length = 0; vps.length = 0; segCache = {};
            _routerDeadUntil = 0; _routerDead = []; _routerIdx = 0;
            courseInfo = {name:'道順同梱テスト', area:'', start:'', goal:''};
            addWp(35.1512,134.4440,'start'); addWp(35.1520,134.4450,'course');
            addWp(35.1535,134.4462,'course'); addWp(35.1548,134.4448,'goal');
            wps[0].onRoute = false; wps[3].onRoute = false;   // 出発点・到着点はルートの外＝つなぎ区間が要る
            await doRouting();
            const calls1 = calls, pts1 = (_lastRouteCoords||[]).length;
            const saved = buildCurrentSaveData();
            const keys = Object.keys(saved.routes || {});
            const shape = keys.every(k => Array.isArray(saved.routes[k]) && saved.routes[k].length === 3);
            calls = 0;
            loadCourseData(saved);
            await new Promise(r => setTimeout(r, 2500));                  // 60ms + 700ms の予約 + 計算
            const calls2 = calls, pts2 = (_lastRouteCoords||[]).length;
            window.fetch = origFetch;
            loadCourseData(snapshot);                                    // 元のコースへ戻す
            await new Promise(r => setTimeout(r, 2500));
            return {calls1, pts1, keys:keys.length, shape, calls2, pts2};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        chk('機能', '保存した道順を読み戻すと経路サーバを呼ばずに同じ道順になる',
            isinstance(rt, dict) and rt.get('calls1', 0) >= 3 and rt.get('keys') == 3 and rt.get('shape') is True
            and rt.get('calls2', 99) == 0 and rt.get('pts2') == rt.get('pts1') and rt.get('pts1', 0) >= 7,
            str(rt)[:190])

        # v118: スマホの説明画面と、パソコンの欄が同じ中身になる
        dsc = page.evaluate("""()=>{ try{
            const src = document.getElementById('iDesc');
            const keep = src.value;
            src.value = '';
            openDescSheet();
            const shown = getComputedStyle(document.getElementById('descSheet')).display;
            document.getElementById('mDescText').value = '棚田と神社をめぐる周回コース。';
            saveDescSheet();
            const after = src.value;
            const closed = getComputedStyle(document.getElementById('descSheet')).display;
            const state = (document.getElementById('mmDescState')||{}).textContent || '';
            const saved = buildCurrentSaveData();
            src.value = keep;
            return {shown:shown, after:after, closed:closed, state:state,
                    inSave:(saved && saved.desc) || ''};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', 'スマホで書いた説明がパソコンの欄・保存データに入る',
            isinstance(dsc, dict) and dsc.get('shown') == 'block'
            and dsc.get('after') == '棚田と神社をめぐる周回コース。'
            and dsc.get('closed') == 'none' and '書かれています' in dsc.get('state', '')
            and dsc.get('inSave') == '棚田と神社をめぐる周回コース。', str(dsc)[:190])

        chk('機能', 'スポットの手前にも三角が出て、○に重ならない',
            isinstance(wpt, dict) and wpt.get('justBefore', 0) >= 1
            and wpt.get('tooClose', 1) == 0,
            str(wpt)[:190])

        chk('機能', '三角が破線5本ごとに並び、進行方向を向く',
            isinstance(trn, dict) and trn.get('n', 0) >= 2 and trn.get('eastOk') is True
            and trn.get('westOk') is True and trn.get('even') is True, str(trn)[:170])

        ok_cas = (isinstance(cas, dict) and cas.get('has') and cas.get('same')
                  and cas.get('thicker') and cas.get('white') and cas.get('notHit')
                  and cas.get('baseLen', 0) > 1 and cas.get('lastLen', 0) > 1)
        chk('機能', 'ルート線の白いふちが同じ形で下に敷かれる', ok_cas, str(cas)[:190])

        # INV-AK: 現在地追従（位置情報を差し替えて動きを確かめる）
        fo = page.evaluate("""()=>{ return (async()=>{ try{
            const realGeo = navigator.geolocation;
            let cb = null, cleared = 0, watchId = 77;
            Object.defineProperty(navigator, 'geolocation', {configurable:true, value:{
              watchPosition: (ok) => { cb = ok; return watchId; },
              clearWatch: () => { cleared++; },
              getCurrentPosition: () => {},
            }});
            const c = leafMap.getCenter();
            _resetBounds(); _setAnchor(c.lat, c.lng, true);       // 現在地を範囲内にする
            toggleFollowMode();
            const on = _followOn;
            cb({coords:{latitude:c.lat, longitude:c.lng, accuracy:12}});
            const first = {marker: !!_gpsMarker, circle: !!_gpsCircle,
                           center: [leafMap.getCenter().lat, leafMap.getCenter().lng]};
            // ほんの少し（1m弱）動いた → 地図は寄せ直さない
            cb({coords:{latitude:c.lat + 0.000005, longitude:c.lng, accuracy:12}});
            const tiny = [leafMap.getCenter().lat, leafMap.getCenter().lng];
            // 20mほど動いた → 追従する（移動はアニメーションなので少し待つ）
            cb({coords:{latitude:c.lat + 0.00018, longitude:c.lng, accuracy:12}});
            await new Promise(r => setTimeout(r, 700));
            const moved = [leafMap.getCenter().lat, leafMap.getCenter().lng];
            toggleFollowMode();                                   // OFF
            const off = {on:_followOn, cleared:cleared, circle: !!_gpsCircle};
            Object.defineProperty(navigator, 'geolocation', {configurable:true, value: realGeo});
            return {on:on, first:first, tinySame: Math.abs(tiny[0]-first.center[0]) < 1e-9,
                    movedDiff: Math.abs(moved[0]-first.center[0]) > 1e-6, off:off};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        ok_fo = (isinstance(fo, dict) and fo.get('on') is True
                 and fo['first']['marker'] is True and fo['first']['circle'] is True
                 and fo.get('tinySame') is True and fo.get('movedDiff') is True
                 and fo['off']['on'] is False and fo['off']['cleared'] == 1
                 and fo['off']['circle'] is False)
        chk('機能', '現在地追従が動き、少しの揺れでは地図を動かさない', ok_fo, str(fo)[:200])

        # INV-AJ: GPXを読み込める（自分で書き出したGPXは往復できる／軌跡だけでもコースになる）
        gi = page.evaluate("""()=>{ try{
            // ① 自分で書き出したGPXを読み直す（往復）
            const mine = buildGpx();
            const back = parseGpx(mine, 'test.gpx');
            const mineSpots = wps.filter(w => w.type !== 'node').length;
            // ② 軌跡だけのGPX（他アプリの記録を想定）
            let trk = '';
            for (let i = 0; i < 8; i++) trk += '<trkpt lat="' + (35.15 + i*0.001) + '" lon="' + (134.44 + i*0.001) + '"></trkpt>';
            const only = parseGpx('<?xml version="1.0"?><gpx version="1.1" creator="t" xmlns="http://www.topografix.com/GPX/1/1">'
                       + '<metadata><name>歩いた記録</name></metadata><trk><trkseg>' + trk + '</trkseg></trk></gpx>', 'x.gpx');
            // ③ GPXでないもの
            const bad = parseGpx('{"name":"json"}', 'x.gpx');
            const bad2 = parseGpx('<?xml version="1.0"?><foo/>', 'x.gpx');
            return {
              backSpots: back.wps ? back.wps.length : -1, mineSpots: mineSpots,
              backPath: back.customPaths ? back.customPaths.length : -1,
              backName: back.name, sameFirstName: back.wps && back.wps[0] && back.wps[0].name,
              typesKept: back.wps ? back.wps.every(w => WT.some(t => t.v === w.type)) : false,
              onlySpots: only.wps ? only.wps.length : -1,
              onlyTypes: only.wps ? only.wps.map(w => w.type).join(',') : '',
              onlyPath: only.customPaths && only.customPaths[0] ? only.customPaths[0].pts.length : 0,
              onlyName: only.name,
              badErr: !!(bad && bad.error), bad2Err: !!(bad2 && bad2.error)
            };
          }catch(e){ return 'ERR:'+e.message; } }""")
        ok_gi = (isinstance(gi, dict) and gi.get('backSpots') == gi.get('mineSpots') and gi.get('backSpots', 0) >= 2
                 and gi.get('typesKept') is True
                 and gi.get('backPath') == 0          # スポットがあるときは軌跡を入れない（二重になるため）
                 and gi.get('onlySpots') == 2 and gi.get('onlyTypes') == 'start,goal'
                 and gi.get('onlyPath', 0) >= 2 and gi.get('onlyName') == '歩いた記録'
                 and gi.get('badErr') is True and gi.get('bad2Err') is True)
        chk('機能', 'GPXを読み込める（往復・軌跡のみ・誤ファイル）', ok_gi, str(gi)[:200])

        # INV-AI: 難易度は距離と登りで決まり、高低差が無いときは出さない
        df = page.evaluate("""()=>{ try{
            const keep = _elevData;
            const set = ups => { const e = [100]; ups.forEach(u => e.push(e[e.length-1] + u)); _elevData = {pts:[], elevs:e}; };
            _elevData = null;
            const none = courseDifficulty(2000);                 // 高低差が無い → 出さない
            set([50]);            const easy   = courseDifficulty(2000);   // 2km・登り50m
            set([200]);           const normal = courseDifficulty(5000);   // 5km・登り200m
            set([400]);           const hard   = courseDifficulty(2000);   // 2km・登り400m（登りで健脚）
            set([50]);            const long   = courseDifficulty(9000);   // 9km・登り50m（距離で健脚）
            _elevData = keep;
            const el = document.getElementById('diffDisp');
            return {none:none, easy:easy && easy.label, normal:normal && normal.label,
                    hard:hard && hard.label, long:long && long.label, hasEl: !!el};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '難易度が距離と登りで正しく決まる',
            isinstance(df, dict) and df.get('none') is None and df.get('easy') == 'やさしい'
            and df.get('normal') == 'ふつう' and df.get('hard') == '健脚'
            and df.get('long') == '健脚' and df.get('hasEl') is True, str(df)[:180])

        # INV-AH: 埋め込み表示では地図だけを見せ、外へ出るリンクが正しい
        emb = page.evaluate("""()=>{ try{
            const keep = document.body.className;
            document.body.classList.add('viewonly', 'embed');
            const g = id => { const e = document.getElementById(id); return e ? getComputedStyle(e).display : 'なし'; };
            const hidden = ['hdr','sidebar','mobileTopBar','mobileShelf'].map(g);
            const barShown = getComputedStyle(document.getElementById('embedBar')).display;
            courseInfo = courseInfo || {}; courseInfo.name = '埋め込みテスト';
            _fillEmbedBar();
            const bar = document.getElementById('embedBar');
            const name = bar.querySelector('.eb-name').textContent;
            const href = bar.querySelector('a').getAttribute('href') || '';
            document.body.className = keep;
            return {hidden:hidden, barShown:barShown, name:name,
                    hrefHasEmbed: href.indexOf('embed=1') >= 0, href:href.slice(-40)};
          }catch(e){ return 'ERR:'+e.message; } }""")
        chk('機能', '埋め込み表示は地図だけを見せる',
            isinstance(emb, dict) and all(d == 'none' for d in emb.get('hidden', ['x']))
            and emb.get('barShown') == 'flex' and emb.get('name') == '埋め込みテスト'
            and emb.get('hrefHasEmbed') is False, str(emb)[:180])

        # INV-AG: 経路サーバへ一斉に投げない（相手への配慮＋止まったサーバを1巡目で見切るため）
        par = page.evaluate("""()=>{ return (async()=>{ try{
            const origFetch = window.fetch, keepIdx = _routerIdx, keepDead = _routerDead.slice();
            const geo = {code:'Ok', routes:[{geometry:{coordinates:[[134.445,35.152],[134.446,35.153]]}}]};
            let live = 0, peak = 0, other = 0;
            // 数えるのは経路サーバへの問い合わせだけ。標高や version.json など別の通信が
            // たまたま重なると、経路の同時数を測ったことにならないため素通しする
            window.fetch = (u, o) => {
              const url = String((u && u.url) ? u.url : u);
              if (url.indexOf('/route/v1/') < 0) { other++; return origFetch(u, o); }
              live++; peak = Math.max(peak, live);
              return new Promise(r => setTimeout(() => { live--; r({ok:true, json:()=>Promise.resolve(geo)}); }, 30)); };
            _routerIdx = 0; _routerDeadUntil = 0; _routerDead = []; segCache = {};
            const jobs = [];
            for (let i = 0; i < 12; i++) jobs.push(fetchOSRM('134.4'+i+',35.15;134.5,35.16',
                                                  [{lat:35.15,lng:134.4},{lat:35.16,lng:134.5}]));
            const out = await Promise.all(jobs);
            window.fetch = origFetch; _routerIdx = keepIdx; _routerDead = keepDead; segCache = {};
            return {peak:peak, limit:ROUTER_MAX_PARALLEL, done:out.length, other:other,
                    ok:out.every(o=>o.length===2)};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        chk('機能', '経路サーバへ同時に投げすぎない',
            isinstance(par, dict) and par.get('done') == 12 and par.get('ok') is True
            and 0 < par.get('peak', 99) <= par.get('limit', 0), str(par))

        # INV-AF: 1台目が止まっていたら予備サーバへ切り替わる／全滅なら直線＋しばらく問い合わせない
        rt = page.evaluate("""()=>{ return (async()=>{ try{
            const origFetch = window.fetch, keepIdx = _routerIdx, keepDead = _routerDeadUntil;
            const keepEach = _routerDead.slice();
            const geo = {code:'Ok', routes:[{geometry:{coordinates:[[134.445,35.152],[134.446,35.153]]}}]};
            const pts = [{lat:35.152,lng:134.445},{lat:35.153,lng:134.446}];
            let calls = [];
            // ① 1台目だけ落ちている → 2台目に切り替わる
            _routerIdx = 0; _routerDeadUntil = 0; _routerDead = []; segCache = {};
            window.fetch = (u) => { calls.push(u);
              return u.indexOf(ROUTERS[0].base) === 0 ? Promise.reject(new Error('down'))
                                                      : Promise.resolve({ok:true, json:()=>Promise.resolve(geo)}); };
            const a = await fetchOSRM('134.445,35.152;134.446,35.153', pts);
            const switched = {idx:_routerIdx, points:a.length, tried:calls.length};
            // 2区間目：止まっているサーバはもう試さない（待ち時間が積み上がらない）
            calls = [];
            const a2 = await fetchOSRM('134.447,35.154;134.448,35.155', pts);
            const second = {tried:calls.length, points:a2.length};
            // ② 全部落ちている → 直線になり、クールダウンが立つ
            calls = []; _routerIdx = 0; _routerDeadUntil = 0; _routerDead = [];
            window.fetch = (u) => { calls.push(u); return Promise.reject(new Error('down')); };
            const b2 = await fetchOSRM('134.445,35.152;134.446,35.153', pts);
            const dead = {straight: b2.length === 2, tried: calls.length, cooldown: _routerDeadUntil > Date.now()};
            // ③ クールダウン中は問い合わせない（待たされない）
            calls = [];
            const c = await fetchOSRM('134.445,35.152;134.446,35.153', pts);
            const cooled = {straight: c.length === 2, tried: calls.length};
            window.fetch = origFetch; _routerIdx = keepIdx; _routerDeadUntil = keepDead;
            _routerDead = keepEach; segCache = {};
            return {switched:switched, second:second, dead:dead, cooled:cooled, routers:ROUTERS.length};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        ok_rt = (isinstance(rt, dict) and rt.get('routers', 0) >= 2
                 and rt['switched']['idx'] == 1 and rt['switched']['points'] == 2
                 and rt['switched']['tried'] == 2
                 and rt['second']['tried'] == 1 and rt['second']['points'] == 2
                 and rt['dead']['straight'] is True and rt['dead']['tried'] == rt['routers']
                 and rt['dead']['cooldown'] is True
                 and rt['cooled']['straight'] is True and rt['cooled']['tried'] == 0)
        chk('機能', '経路サーバが止まったら予備へ切り替わる', ok_rt, str(rt)[:200])

        # INV-AE: 新しい版が出ていれば案内し、同じ版なら何も出さない
        up = page.evaluate("""()=>{ return (async()=>{ try{
            const orig = window.fetch;
            window.fetch = () => Promise.resolve({ok:true, json:()=>Promise.resolve({version:'v999'})});
            const newer = await checkForUpdate();
            window.fetch = () => Promise.resolve({ok:true, json:()=>Promise.resolve({version:APP_VERSION})});
            const same = await checkForUpdate();
            window.fetch = () => Promise.reject(new Error('offline'));
            const fail = await checkForUpdate();
            window.fetch = orig;
            const s2 = document.getElementById('s2'), keep = s2.style.display;
            const kill = () => { const e = document.getElementById('updBar'); if (e) e.remove(); };
            s2.style.display = 'none';            // ① 一覧画面 → 案内が出る
            showUpdateBar('v999');
            const bar = !!document.getElementById('updBar');
            const btn = document.querySelector('#updBar button');
            const txt = document.querySelector('#updBar span') ? document.querySelector('#updBar span').textContent : '';
            kill();
            s2.style.display = 'flex';            // ② 地図画面 → 出さない（操作ボタンを隠さない）
            showUpdateBar('v999');
            const barOnMap = !!document.getElementById('updBar');
            kill();
            s2.style.display = keep;
            return {newer:newer, same:same, fail:fail, bar:bar, barOnMap:barOnMap, hasBtn:!!btn, txt:txt};
          }catch(e){ return 'ERR:'+e.message; } })(); }""")
        chk('機能', '新しい版があるときだけ案内が出る',
            isinstance(up, dict) and up.get('newer') == 'v999' and up.get('same') is None
            and up.get('fail') is None and up.get('bar') is True and up.get('barOnMap') is False
            and up.get('hasBtn') is True and 'v999' in up.get('txt', ''), str(up)[:180])

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

                # ── 配布リンク（v135）：オンラインで開く（同じ場所のJSONがキャッシュに入る）→ 圏外で開き直してもコースが出る ──
                page.goto(url + '?course=sample.json&offauto=0', wait_until='domcontentloaded')
                try:
                    page.wait_for_function("() => document.body.classList.contains('viewonly') && typeof wps !== 'undefined' && wps.length > 10", timeout=30000)
                except Exception:
                    pass
                page.wait_for_timeout(800)
                ctx.set_offline(True)
                try:
                    page.goto(url + '?course=sample.json&offauto=0', wait_until='domcontentloaded')
                    page.wait_for_function("() => document.body.classList.contains('viewonly') && typeof wps !== 'undefined' && wps.length > 10", timeout=20000)
                    page.wait_for_timeout(1500)
                    link_off = page.evaluate("() => ({viewonly: document.body.classList.contains('viewonly'), wps: wps.length,"
                                             " route: !!(_lastRouteCoords && _lastRouteCoords.length > 50), name: courseInfo.name})")
                except Exception as e:
                    link_off = str(e)[:140]
                ctx.set_offline(False)
                chk('オフライン', '圏外で配布リンクを開いてもコースが出る（道順は同梱ぶんで引ける）',
                    isinstance(link_off, dict) and link_off.get('viewonly') and link_off.get('wps', 0) > 10 and link_off.get('route'), str(link_off)[:160])

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
# 4) 見た目の比較検査（配布シート・保存画像）
#    「保存画像の見え方は確認できない」を減らすための検査。
#    地図タイルは比較対象から外す（提供元の絵が変わるため）。比べるのは
#    こちら側が作っている部分＝○・番号・ラベル・凡例・縮尺・方位・タイトル帯。
#    文字の描かれ方はOSごとに違うので、基準画像を作った環境でだけ比較する。
# ----------------------------------------------------------------------
VISUAL_DIFF_MAX = 0.01     # 画素の食い違いが1%を超えたら不合格
VISUAL_CH_TOL   = 24       # 1画素あたり、この差までは同じ色とみなす

def _visual_platform():
    import platform
    return platform.system()

def _compare_png(cur_bytes, base_path, name):
    """基準画像と比べる。無ければ作って報告だけする。"""
    from PIL import Image, ImageChops
    import io as _io
    if not os.path.exists(base_path):
        with open(base_path, 'wb') as f:
            f.write(cur_bytes)
        return True, f'基準画像を新規作成: {os.path.basename(base_path)}（内容を目視で確認してください）'
    cur  = Image.open(_io.BytesIO(cur_bytes)).convert('RGB')
    base = Image.open(base_path).convert('RGB')
    if cur.size != base.size:
        return False, f'大きさが違う 現在={cur.size} 基準={base.size}'
    diff = ImageChops.difference(cur, base)
    bad = 0
    for px in diff.getdata():
        if px[0] > VISUAL_CH_TOL or px[1] > VISUAL_CH_TOL or px[2] > VISUAL_CH_TOL:
            bad += 1
    ratio = bad / float(cur.size[0] * cur.size[1])
    ok = ratio <= VISUAL_DIFF_MAX
    return ok, f'食い違い {ratio*100:.2f}%（許容 {VISUAL_DIFF_MAX*100:.0f}%）'

# ----------------------------------------------------------------------
# 3.5) WebKit（iPhone の Safari と同じエンジン）での見た目の検査（v146・見直し帳 C1）
#   Chromium で通っても iPhone ではみ出すことがあった（v135）。配布リンクと編集画面を 390×812 で開き、
#   横にはみ出す部品が無いこと・歩く人の帯が出ることを確かめる。WebKit が入っていない環境では見送り（失敗にしない）
# ----------------------------------------------------------------------
def webkit_checks(index_path):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return
    import threading, functools, http.server, socketserver
    here = os.path.dirname(os.path.abspath(index_path))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=here)
    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(('127.0.0.1', 0), handler)
    except Exception as e:
        chk('WebKit', 'ローカル配信を起動できる', False, str(e)); return
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{port}/index.html'
    OVERFLOW = """() => { const bad = [];
        document.querySelectorAll('button, .mrb, .pc-pill, #nextBar, #stampBar').forEach(b => { const s = getComputedStyle(b); if (s.display === 'none' || s.visibility === 'hidden') return;
          const r = b.getBoundingClientRect(); if (r.width === 0 || r.height === 0) return;
          if (r.right > innerWidth + 1 || r.left < -1 || r.bottom > innerHeight + 1) bad.push((b.id || b.textContent.trim().slice(0, 10)) + ':' + Math.round(r.right) + ',' + Math.round(r.bottom)); });
        return {bad: bad.slice(0, 6), sw: document.scrollingElement.scrollWidth, iw: innerWidth, wps: (typeof wps !== 'undefined') ? wps.length : -1}; }"""
    try:
        with sync_playwright() as pw:
            try:
                b = pw.webkit.launch()
            except Exception as e:
                chk('WebKit', 'WebKit（iPhone と同じエンジン）で開ける', True, '未導入のため見送り: ' + str(e).splitlines()[0][:90]); return
            ctx = b.new_context(viewport={'width': 390, 'height': 812}, is_mobile=True, has_touch=True, device_scale_factor=2)
            page = ctx.new_page()
            errs = []
            page.on('pageerror', lambda e: errs.append(str(e)))
            page.on('dialog', lambda d: d.accept())
            # 配布リンク（歩く人の画面）
            page.goto(url + '?nosw=1&course=sample.json&offauto=0', wait_until='domcontentloaded')
            page.wait_for_function("() => document.body.classList.contains('viewonly') && typeof wps !== 'undefined' && wps.length > 5", timeout=30000)
            try: page.wait_for_function("() => _lastRouteCoords && _lastRouteCoords.length > 50", timeout=20000)
            except Exception: pass
            page.wait_for_timeout(800)
            page.evaluate("() => { try { dismissWalkTip(); } catch(e){} const c = _lastRouteCoords; if (c && c.length > 2) { const i = Math.floor(c.length * 0.3); _onWalkerPos(c[i][0], c[i][1], 6); } }")
            page.wait_for_timeout(300)
            r = page.evaluate(OVERFLOW)
            r['bar'] = page.evaluate("() => !document.getElementById('nextBar').hidden && /次/.test(document.getElementById('nbText').textContent)")
            chk('WebKit', 'iPhone と同じエンジンで配布リンクが開き、はみ出す部品がなく、歩く人の帯が出る',
                r['wps'] > 5 and not r['bad'] and r['sw'] <= r['iw'] + 1 and r['bar'] and not errs, str(r)[:200] + (' err:' + errs[0][:80] if errs else ''))
            # 編集画面（サンプルを開く）＋メニュー
            page.goto(url + '?nosw=1', wait_until='domcontentloaded')
            page.wait_for_function("() => { try { return getCourses().length > 0; } catch(e){ return false; } }", timeout=30000)
            page.evaluate("() => loadCourseData(getCourses()[0])"); page.wait_for_timeout(1200)
            r2 = page.evaluate(OVERFLOW)
            page.evaluate("() => openMobileMenu()"); page.wait_for_timeout(400)
            r2['menu'] = page.evaluate("() => { const sh = document.getElementById('mobileMenuSheet'); const r = sh.getBoundingClientRect(); return sh.classList.contains('show') && r.right <= innerWidth + 1 && r.left >= -1; }")
            page.evaluate("() => closeMobileMenu()")
            chk('WebKit', 'iPhone と同じエンジンで編集画面とメニューが開き、横にはみ出さない',
                r2['wps'] > 5 and not r2['bad'] and r2['sw'] <= r2['iw'] + 1 and r2['menu'] and not errs, str(r2)[:200] + (' err:' + errs[0][:80] if errs else ''))
            b.close()
    except Exception as e:
        chk('WebKit', 'WebKit の検査が最後まで走る', False, str(e).splitlines()[0][:160])
    finally:
        httpd.shutdown()

def visual_checks(index_path):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return
    try:
        from PIL import Image  # noqa: F401
    except Exception:
        chk('見た目', '画像比較の準備', False, 'Pillow が未導入 → pip install pillow'); return

    here = os.path.dirname(os.path.abspath(index_path))
    base_dir = os.path.join(here, 'tests', 'baseline')
    os.makedirs(base_dir, exist_ok=True)
    mark = os.path.join(base_dir, 'PLATFORM.txt')
    plat = _visual_platform()
    if os.path.exists(mark):
        made_on = open(mark, encoding='utf-8').read().strip()
        if made_on != plat:
            chk('見た目', f'比較は基準を作った環境でのみ実施（基準={made_on} / 現在={plat}）', True,
                '文字の描かれ方がOSで違うため、この環境では比較しない')
            return
    else:
        with open(mark, 'w', encoding='utf-8') as f:
            f.write(plat)

    # 機能チェックと同じローカル差し替え版を使う
    leaf_css = 'file://' + os.path.join(here, 'node_modules/leaflet/dist/leaflet.css')
    leaf_js  = 'file://' + os.path.join(here, 'node_modules/leaflet/dist/leaflet.js')
    h2c      = os.path.join(here, 'node_modules/html2canvas/dist/html2canvas.min.js')
    if not (os.path.exists(leaf_js[7:]) and os.path.exists(h2c)):
        chk('見た目', 'ローカルの部品が揃っている', False, 'npm install が必要'); return
    src = open(index_path, encoding='utf-8').read()
    local = (src.replace('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css', leaf_css)
                .replace('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js', leaf_js)
                .replace('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js',
                         'file://' + h2c))
    tdir = tempfile.mkdtemp()
    tpath = os.path.join(tdir, 'visual.html')
    open(tpath, 'w', encoding='utf-8').write(local)

    sandbox_chrome = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    launch_kwargs = {'args': ['--allow-file-access-from-files', '--force-device-scale-factor=1',
                              '--hide-scrollbars', '--disable-lcd-text']}
    if os.path.exists(sandbox_chrome):
        launch_kwargs['executable_path'] = sandbox_chrome

    with sync_playwright() as pw:
        b = pw.chromium.launch(**launch_kwargs)
        ctx = b.new_context(viewport={'width': 1100, 'height': 800}, device_scale_factor=1)
        page = ctx.new_page()
        page.goto('file://' + tpath, wait_until='domcontentloaded'); page.wait_for_timeout(400)
        page.evaluate("() => { window.__noAutoSave = true; }")   # v148: 検査中は自動保存を止める（状態が勝手に保存されないように）
        page.click('.s1-fab'); page.wait_for_timeout(120)
        # 地名の検索はネット任せで、応答が遅れると『あとから』地図を動かしてしまう。
        # 検査は毎回同じ場所を見たいので、固定の座標を返すように差し替える。
        page.evaluate("() => { window.geocode = async () => ({lat:35.1538, lng:134.4468}); }")
        page.fill('#s1Name', '見た目検査コース'); page.fill('#s1Area', '宍粟市波賀町')
        page.click('#s1Btn'); page.wait_for_timeout(900)

        # 毎回まったく同じコースを作る（座標・名前・種別・縮尺を固定）
        page.evaluate("""() => {
            if (!leafMap) initMap();
            leafMap.eachLayer(l => { if (l instanceof L.TileLayer) leafMap.removeLayer(l); });  // 地図の絵は比較しない
            // 地域名の検索結果（ネット依存）で表示範囲が制限されないよう、基準点を作り直して固定する
            // （_setAnchor は既に基準点があると何もしないので、先に _resetBounds が要る）
            _resetBounds();
            _setAnchor(35.1538, 134.4468, true);
            wps.length = 0; vps.length = 0; idW = 0; idV = 0;
            const S = [[35.1520,134.4450,'start','出発点'],
                       [35.1535,134.4462,'course','棚田の見どころ'],
                       [35.1548,134.4448,'shrine','山の神神社'],
                       [35.1556,134.4470,'view','見晴らし台'],
                       [35.1541,134.4489,'toilet','公衆トイレ'],
                       [35.1524,134.4478,'goal','到着点']];
            S.forEach(s => { const w = addWp(s[0], s[1], s[2]); w.name = s[3]; updateTooltip(w); });
            // 経路サーバの応答でルート形状が変わらないよう、区間はすべて直線に固定する
            // （道なりの精度はここでは検査対象外。○・番号・ラベル・線の描かれ方を見る）
            wps.forEach(w => { w.fitBefore = false; w.fitAfter = false; });
            segCache = {};
            const el = document.getElementById('iDesc');
            if (el) el.value = '棚田と神社をめぐる短い周回コース。見た目検査のための固定データです。';
            setLabelSize(0); setWpSize(0); setWalkSpeed(2);
            leafMap.setView([35.1538, 134.4468], 16);
            // 高低差はルート再計算で消えるため、あとから（下で）入れ直す
            redrawStraight();
        }""")
        page.wait_for_timeout(1200)
        # 高低差を固定値で入れ、難易度も比較対象にする
        # （clearCache() 等でルート再計算のたびに _elevData は消えるので、計算が落ち着いてから入れる）
        page.evaluate("""() => { _elevData = {pts: [], elevs: [100, 140, 120, 180]};   // 登り100m
            updateDistanceAndTime(_lastRouteCoords); }""")
        page.wait_for_timeout(300)

        # 前提の確認：印が地図の中に入っていること。
        # （入っていないまま撮ると「空っぽの基準画像」ができてしまうため必ず確かめる）
        inside = page.evaluate("""() => {
            const m = document.getElementById('map').getBoundingClientRect();
            const els = [...document.querySelectorAll('.leaflet-marker-icon')];
            const tips = [...document.querySelectorAll('.leaflet-tooltip.wp-tt')];
            const ok = e => { const r = e.getBoundingClientRect();
                return r.left >= m.left - 2 && r.right <= m.right + 2 && r.top >= m.top - 2 && r.bottom <= m.bottom + 2; };
            return {markers: els.length, inside: els.filter(ok).length, tips: tips.length,
                    tipsInside: tips.filter(ok).length};
        }""")
        diff_ok = page.evaluate("() => { const d = courseDifficulty(_lastRouteDistM); return d ? d.label : null; }")
        chk('見た目', '検査用コースの難易度が決まっている', diff_ok is not None, str(diff_ok))
        pre_ok = (isinstance(inside, dict) and inside.get('markers', 0) >= 6
                  and inside['markers'] == inside['inside']
                  and inside.get('tips', 0) >= 6 and inside['tips'] == inside['tipsInside'])
        chk('見た目', '検査用コースが地図の中に収まっている', pre_ok, str(inside))

        # (A) 保存画像（地図＋○＋ラベル）— 実際に html2canvas で描く
        img_a = page.evaluate("""() => (async () => {
            const c = await _captureMapCanvas();
            return c.toDataURL('image/png');
        })()""")
        # (B) 配布シート — 地図部分は単色に差し替え、こちらが組んだ紙面だけを比べる
        page.evaluate("""() => {
            window.__origCap = _captureMapCanvas;
            window._captureMapCanvas = async () => {
                const c = document.createElement('canvas');
                c.width = 900; c.height = 560;
                const g = c.getContext('2d'); g.fillStyle = '#E8EDE2'; g.fillRect(0, 0, 900, 560);
                return c;
            };
        }""")
        # QRも比較対象にするため、配布リンクを確実に結びつける
        page.evaluate("""() => { currentCourseId = 'visual-test';
            _setShareLink(currentCourseId, 'https://example.test/footpath/?course=vis.json'); }""")
        page.evaluate("""() => openPrintSheet()""")
        page.wait_for_timeout(1500)
        sheet = page.query_selector('#printSheet')
        img_b = sheet.screenshot(type='png') if sheet else None
        b.close()

    import base64
    if img_a and img_a.startswith('data:image/png;base64,'):
        raw = base64.b64decode(img_a.split(',', 1)[1])
        ok, msg = _compare_png(raw, os.path.join(base_dir, 'map_image.png'), '保存画像')
        chk('見た目', '保存画像（○・番号・ラベル）が基準どおり', ok, msg)
    else:
        chk('見た目', '保存画像を作成できる', False, '画像が取得できなかった')

    if img_b:
        ok, msg = _compare_png(img_b, os.path.join(base_dir, 'print_sheet.png'), '配布シート')
        chk('見た目', '配布シート（凡例・縮尺・方位・QR）が基準どおり', ok, msg)
    else:
        chk('見た目', '配布シートを作成できる', False, 'シートが取得できなかった')

# ----------------------------------------------------------------------
def main():
    if not os.path.exists(INDEX):
        print(f'対象が見つかりません: {INDEX}'); sys.exit(2)
    print(f'対象: {INDEX}\n')
    src = open(INDEX, encoding='utf-8').read()
    static_checks(src)
    functional_checks(INDEX)
    offline_checks(INDEX)
    webkit_checks(INDEX)
    visual_checks(INDEX)

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
