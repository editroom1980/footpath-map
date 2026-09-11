#!/usr/bin/env python3
"""国土数値情報（国土交通省）の施設データを、アプリの「周辺の情報を取り込む」用の小さな JSON に変換する。
   使い方: python3 tools/ksj_convert.py --pref 28 --out data/ksj/28      （兵庫県）
           python3 tools/ksj_convert.py --pref 28 --probe                 （中身の確認だけ）
   ・外部ライブラリなし（点のシェープファイルと DBF を自前で読む。文字は cp932）
   ・出典表示：国土数値情報（国土交通省）。利用規約（政府標準利用規約 2.0 準拠）に従い出典を明記する
"""
import argparse, io, json, os, re, struct, sys, urllib.request, zipfile

BASE = 'https://nlftp.mlit.go.jp'
PREF_NAMES = {'28': '兵庫県', '33': '岡山県', '31': '鳥取県', '26': '京都府', '27': '大阪府'}
# 使うデータ（識別子: 年度版のパス, 表示名, アプリの種類, 名前の列, 補足の列）。列は --probe で確かめて決めた
DATASETS = {
  'P29': {'path': '/ksj/gml/data/P29/P29-13/P29-13_{p}.zip',      'label': '学校',                'type': 'school',  'name': 'P29_005', 'sub': 'P29_004', 'edition': '2013', 'subcode': {'16001':'小学校','16002':'中学校','16003':'高等学校','16004':'中等教育学校','16005':'特別支援学校','16011':'大学','16012':'短期大学','16013':'高等専門学校','16021':'専修学校','16022':'各種学校','16031':'幼稚園','16032':'認定こども園'}},
  'P05': {'path': '/ksj/gml/data/P05/P05-22/P05-22_{p}_GML.zip',  'label': '役場・公民館・集会施設', 'type': 'hall', 'name': 'P05_003', 'sub': 'P05_004', 'edition': '2022'},
  'P30': {'path': '/ksj/gml/data/P30/P30-13/P30-13_{p}.zip',      'label': '郵便局',              'type': 'hall',    'name': 'P30_005', 'sub': 'P30_006', 'edition': '2013'},
  'P18': {'path': '/ksj/gml/data/P18/P18-12/P18-12_{p}_GML.zip',  'label': '警察署・交番',        'type': 'hall',    'name': 'P18_001', 'sub': 'P18_004', 'edition': '2012'},
  'P04': {'path': '/ksj/gml/data/P04/P04-20/P04-20_{p}_GML.zip',  'label': '病院・診療所',        'type': 'other',   'name': 'P04_002', 'sub': 'P04_001', 'edition': '2020', 'subcode': {'1':'病院','2':'診療所','3':'歯科'}},
  'P27': {'path': '/ksj/gml/data/P27/P27-13/P27-13_{p}.zip',      'label': '文化施設',            'type': 'hall',    'name': 'P27_005', 'sub': 'P27_006', 'edition': '2013'},
  'P32': {'path': '/ksj/gml/data/P32/P32-14/P32-14_{p}_GML.zip',  'label': '文化財',              'type': 'history', 'name': 'P32_006', 'sub': 'P32_007', 'edition': '2014'},
  'P12': {'path': '/ksj/gml/data/P12/P12-14/P12-14_{p}_GML.zip',  'label': '観光資源',            'type': 'history', 'name': 'P12_002', 'sub': 'P12_006', 'edition': '2014'},
  'P13': {'path': '/ksj/gml/data/P13/P13-11/P13-11_{p}_GML.zip',  'label': '都市公園',            'type': 'park',    'name': 'P13_003', 'sub': 'P13_006', 'edition': '2011'},
  'P11': {'path': '/ksj/gml/data/P11/P11-10/P11-10_{p}_GML.zip',  'label': 'バス停',              'type': 'other',   'name': 'P11_001', 'sub': 'P11_004_1', 'edition': '2010'},
}

def fetch(url, cache):
    os.makedirs(cache, exist_ok=True)
    fn = os.path.join(cache, os.path.basename(url))
    if not os.path.exists(fn):
        req = urllib.request.Request(url, headers={'User-Agent': 'footpath-map ksj_convert/1.0'})
        with urllib.request.urlopen(req, timeout=120) as r: open(fn, 'wb').write(r.read())
    return fn

def read_dbf(b):
    n = struct.unpack('<I', b[4:8])[0]; hl = struct.unpack('<H', b[8:10])[0]; rl = struct.unpack('<H', b[10:12])[0]
    fields = []; i = 32
    while b[i] != 0x0d:
        name = b[i:i+11].split(b'\x00')[0].decode('ascii', 'ignore'); typ = chr(b[i+11]); ln = b[i+16]
        fields.append((name, typ, ln)); i += 32
    recs = []
    for k in range(n):
        off = hl + k * rl; row = b[off:off+rl]
        if row[:1] == b'*': continue
        pos = 1; rec = {}
        for name, typ, ln in fields:
            raw = row[pos:pos+ln]; pos += ln
            try: v = raw.decode('cp932', 'ignore').strip()
            except Exception: v = ''
            rec[name] = v
        recs.append(rec)
    return fields, recs

def read_shp_points(b):
    """点（type 1）の x,y を順に返す。点以外は中心（バウンディングボックスの中央）"""
    pts = []; pos = 100
    while pos < len(b):
        clen = struct.unpack('>i', b[pos+4:pos+8])[0] * 2; body = b[pos+8:pos+8+clen]; pos += 8 + clen
        if len(body) < 4: pts.append(None); continue
        st = struct.unpack('<i', body[:4])[0]
        if st == 1: x, y = struct.unpack('<dd', body[4:20]); pts.append((y, x))
        elif st in (3, 5, 8, 13, 15, 18): xmin, ymin, xmax, ymax = struct.unpack('<dddd', body[4:36]); pts.append(((ymin+ymax)/2, (xmin+xmax)/2))
        else: pts.append(None)
    return pts

def load(code, pref, cache):
    d = DATASETS[code]; url = BASE + d['path'].format(p=pref)
    fn = fetch(url, cache); z = zipfile.ZipFile(fn)
    shp = next(n for n in z.namelist() if n.lower().endswith('.shp')); dbf = shp[:-4] + '.dbf'
    fields, recs = read_dbf(z.read(dbf)); pts = read_shp_points(z.read(shp))
    return fields, recs, pts

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--pref', required=True); ap.add_argument('--out'); ap.add_argument('--probe', action='store_true'); ap.add_argument('--cache', default='/tmp/ksj_cache')
    a = ap.parse_args()
    written = []; bbox = [90, 180, -90, -180]
    for code, d in DATASETS.items():
        try: fields, recs, pts = load(code, a.pref, a.cache)
        except Exception as e: print(code, 'ERR', e); continue
        if a.probe:
            print('==', code, d['label'], 'records', len(recs), 'fields', [f[0] for f in fields])
            for r, p in list(zip(recs, pts))[:3]: print('  ', p, {k: v[:24] for k, v in r.items() if v})
            continue
        items = []
        for r, p in zip(recs, pts):
            if not p: continue
            name = (r.get(d['name']) or '').strip(); sub = (r.get(d['sub']) or '').strip()
            if d.get('subcode'): sub = d['subcode'].get(sub, '')
            sub = sub.replace('\x00', '').replace('‐', '')
            if not name: continue
            items.append([round(p[0], 5), round(p[1], 5), name, sub])
        os.makedirs(a.out, exist_ok=True)
        out = {'code': code, 'label': d['label'], 'type': d['type'], 'edition': d['edition'], 'pref': a.pref,
               'attribution': '出典：国土数値情報（' + d['label'] + 'データ・' + d['edition'] + '年度）国土交通省', 'items': items}
        fn = os.path.join(a.out, code + '.json'); open(fn, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
        print(code, d['label'], len(items), 'items ->', fn, os.path.getsize(fn) // 1024, 'KB')
        written.append((code, d['label'], d['type'], len(items)))
        for it in items:
            bbox[0] = min(bbox[0], it[0]); bbox[1] = min(bbox[1], it[1]); bbox[2] = max(bbox[2], it[0]); bbox[3] = max(bbox[3], it[1])
    if a.out and written:
        idx_fn = os.path.join(os.path.dirname(a.out.rstrip('/')), 'index.json')
        idx = {'prefs': []}
        if os.path.exists(idx_fn):
            try: idx = json.load(open(idx_fn, encoding='utf-8'))
            except Exception: idx = {'prefs': []}
        idx['prefs'] = [p for p in idx['prefs'] if p.get('code') != a.pref]
        idx['prefs'].append({'code': a.pref, 'name': PREF_NAMES.get(a.pref, a.pref), 'bbox': [round(v, 4) for v in bbox], 'sets': [{'code': c, 'label': l, 'type': t, 'n': n} for c, l, t, n in written]})
        idx['attribution'] = '出典：国土数値情報（国土交通省）'
        open(idx_fn, 'w', encoding='utf-8').write(json.dumps(idx, ensure_ascii=False, separators=(',', ':')))
        print('index ->', idx_fn)

if __name__ == '__main__': main()
