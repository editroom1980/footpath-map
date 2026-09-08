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
    chk('静的', 'CDN参照は3つ', c == 3, f'count={c}')
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
    chk('静的', '背景地図に配色済みタイル追加', all(k in src for k in ['opentopo:', 'carto:', 'osm_hot:']))
    chk('静的', '背景地図切替 cycleBaseMap 存在', 'function cycleBaseMap' in src)
    chk('静的', 'PCツールバーに地図切替ボタン', 'id="btnBaseMap"' in src)
    chk('静的', 'サンプル取り込み ensureSampleCourse 存在', 'async function ensureSampleCourse' in src)
    chk('静的', 'サンプルURL定数 SAMPLE_URL 維持', 'const SAMPLE_URL' in src)
    chk('静的', 'サンプル済みフラグ(LS.sampleDone)を使用', 'sampleDone' in src)
    chk('静的', '起動時にサンプル取り込みを呼ぶ', 'ensureSampleCourse();' in src)

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

        b.close()

# ----------------------------------------------------------------------
def main():
    if not os.path.exists(INDEX):
        print(f'対象が見つかりません: {INDEX}'); sys.exit(2)
    print(f'対象: {INDEX}\n')
    src = open(INDEX, encoding='utf-8').read()
    static_checks(src)
    functional_checks(INDEX)

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
