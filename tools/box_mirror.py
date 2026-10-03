#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""みんなの箱 → GitHub へ写す（v200）

「みんなの箱」は登録も合言葉もいらない共同の置き場で、誰でも上書きできる。
そこに出されたコースを定期的に library/box-<ID>.json へ写し、写したぶんは箱から外す。
以降アプリは GitHub 側（library/）を読むので、箱が消えてもコースは残る。

・書き込む先は library/box-<ID>.json だけ（ID は英数字とハイフンのみに直す）
・1回に写すのは MAX_PER_RUN 件まで／1件 MAX_BYTES まで（荒らし対策）
・箱の一覧は「書き戻す直前にもう一度読む」＝実行中に出された新しいコースを消さない
"""
import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOX_FILE = os.path.join(ROOT, 'box.json')
LIB_DIR = os.path.join(ROOT, 'library')
MAX_PER_RUN = 30          # 1回に写す件数の上限
MAX_BYTES = 400 * 1024    # コース1件の中身の上限
MAX_PH_PARTS = 40         # v242：写真を分けて置ける数の上限（アプリは約70万字ずつに分けて置く）
MAX_PH_BYTES = 12 * 1024 * 1024   # v242：コース1件の写真の上限（荒らし対策）
TIMEOUT = 20
ID_OK = re.compile(r'^[A-Za-z0-9-]{4,40}$')


def _course_from_d(d, kind='d'):
    """配る中身（#d= / #j=）をコースの中身に戻す（v220：中身の指紋を取るため）"""
    try:
        raw = str(d).replace('-', '+').replace('_', '/')
        raw += '=' * (-len(raw) % 4)
        b = base64.b64decode(raw)
        if kind != 'j':
            b = zlib.decompress(b, -15)
        return json.loads(b.decode('utf-8'))
    except Exception:
        return None


def _fingerprint(c):
    """コースの指紋＝スポットの座標（小数4桁）を並べたもののハッシュ。
    同じコースを別の人が出し直しても同じ値になるので、名義だけ変えた再投稿を見つけられる。"""
    pts = []
    for w in ((c or {}).get('wps') or []):
        try:
            pts.append('%.4f,%.4f' % (float(w['lat']), float(w['lng'])))
        except Exception:
            pass
    if len(pts) < 2:
        return ''
    pts.sort()
    return hashlib.sha1('|'.join(pts).encode('utf-8')).hexdigest()[:16]


def _known():
    """library/ にすでにあるコースの {指紋: 作者の印}（v220）"""
    out = {}
    if not os.path.isdir(LIB_DIR):
        return out
    for name in os.listdir(LIB_DIR):
        if not name.lower().endswith('.json') or name.endswith('-photos.json'):
            continue
        try:
            with open(os.path.join(LIB_DIR, name), encoding='utf-8') as f:
                j = json.load(f)
        except Exception:
            continue
        fp = j.get('fp')
        if not fp and j.get('d'):
            fp = _fingerprint(_course_from_d(j.get('d'), j.get('k') or 'd'))
        if fp:
            out.setdefault(fp, j.get('oid') or '')
    return out


def _http(url, data=None, ctype='text/plain'):
    req = urllib.request.Request(url, data=(data.encode('utf-8') if data is not None else None))
    if data is not None:
        req.add_header('Content-Type', ctype)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode('utf-8', 'replace')


def _cfg():
    with open(BOX_FILE, encoding='utf-8') as f:
        c = json.load(f)
    if not c or c.get('kind') in (None, 'off'):
        return None
    return c


def _url(cfg, what, cid=None, i=0):
    """箱の場所。写真（ph）は分けて置ける：1つ目は「-ph」、2つ目からは「-ph1」「-ph2」…（アプリの _boxUrl と同じ）。
    v202〜241 はここで写真の場所を作っておらず、中身と同じ場所を読んでいた＝写真を一度も写せていなかった（v242 で修正）"""
    if cfg.get('kind') == 'firebase':
        u = str(cfg.get('url', '')).rstrip('/')
        if what == 'idx':
            return u + '/idx.json'
        if what == 'row':
            return u + '/idx/' + cid + '.json'
        if what == 'ph':
            return u + '/ph/' + cid + ('-%d' % i if i else '') + '.json'
        return u + '/c/' + cid + '.json'
    base = str(cfg.get('base', '')) + str(cfg.get('key', ''))
    if what == 'idx':
        return base
    if what == 'ph':
        return base + '-' + cid + '-ph' + (str(i) if i else '')
    return base + '-' + cid


def _rows(raw):
    """箱の一覧はいくつかの形を取りうる（配列／{courses:[…]}／ID をキーにした辞書）"""
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict) and isinstance(raw.get('courses'), list):
        return [r for r in raw['courses'] if isinstance(r, dict)]
    if isinstance(raw, dict):
        out = []
        for k, v in raw.items():
            if isinstance(v, dict):
                v = dict(v)
                v['id'] = v.get('id') or k
                out.append(v)
        return out
    return []


def _read_json(url):
    try:
        t = _http(url + ('&' if '?' in url else '?') + 't=' + str(int(time.time()))).strip()
    except Exception as e:
        print('読めません:', url, e)
        return None
    if not t or t == 'null':
        return None
    try:
        return json.loads(t)
    except Exception:
        return None


def _read_state(url):
    """読めたか・空だったか・つながらなかったかを分けて返す（v242：写真を補うときに、つながらなかったものを「無い」と決めつけない）"""
    try:
        t = _http(url + ('&' if '?' in url else '?') + 't=' + str(int(time.time()))).strip()
    except Exception as e:
        if getattr(e, 'code', None) == 404 or '404' in str(e):
            return 'empty', None                # 置かれていない（textdb は 200 で空を返すが、404 の箱もありうる）
        print('読めません:', url, e)
        return 'err', None
    if not t or t in ('null', '""'):
        return 'empty', None
    try:
        return 'ok', json.loads(t)
    except Exception:
        return 'empty', None


def _ph_count(v):
    """一覧の ph＝写真を何個に分けて置いたか（v202〜241 は 1 か True）"""
    if v is True:
        return 1
    try:
        return max(0, min(MAX_PH_PARTS, int(v)))
    except Exception:
        return 0


def _read_photos(cfg, cid, n=0):
    """箱から写真を読んでつなぐ。n が分からないとき（v241 までに写したもの）は、空になるまで順に読む。
    つながらなかったときは None（＝今回は写さず次の回にやり直す。写真を落とさない）"""
    parts = []
    for i in range(n if n else MAX_PH_PARTS):
        st, j = _read_state(_url(cfg, 'ph', cid, i))
        if st == 'err':
            return None
        if st != 'ok' or not isinstance(j, dict) or not isinstance(j.get('p'), dict):
            if n:
                return None                     # あるはずの所が空＝まだ揃っていない
            break
        parts.append(j['p'])
    out, size = {}, 0
    for p in parts:
        for k, arr in p.items():
            if not isinstance(arr, list):
                continue
            for src in arr:
                if isinstance(src, str) and src.startswith('data:image/') and size + len(src) <= MAX_PH_BYTES:
                    out.setdefault(str(k), []).append(src)
                    size += len(src)
    return out


def _write_photos(cid, pics):
    path = os.path.join(LIB_DIR, 'box-' + cid + '-photos.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'p': pics}, f, ensure_ascii=False)
    print('写真も写しました:', path, sum(len(v) for v in pics.values()), '枚')
    return 'library/box-' + cid + '-photos.json'


def _backfill_photos(cfg):
    """v202〜241 の写し取りは写真を写せていなかった。library/ にあって写真の無いコースに、
    箱に残っている写真をあとから写す（v242）。一度調べたものには phChecked を付けて、毎回は読みに行かない"""
    if not os.path.isdir(LIB_DIR):
        return 0
    n = 0
    for name in sorted(os.listdir(LIB_DIR)):
        m = re.match(r'^box-([A-Za-z0-9-]{4,40})\.json$', name)
        if not m or name.endswith('-photos.json'):
            continue
        path = os.path.join(LIB_DIR, name)
        try:
            with open(path, encoding='utf-8') as f:
                j = json.load(f)
        except Exception:
            continue
        if not isinstance(j, dict) or j.get('ph') or j.get('phChecked'):
            continue
        cid = m.group(1)
        pics = _read_photos(cfg, cid)
        if pics is None:
            continue                            # つながらなかった＝次の回にもう一度
        if pics:
            j['ph'] = _write_photos(cid, pics)
        j['phChecked'] = 1
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(j, f, ensure_ascii=False, indent=1)
        n += 1
        if n >= MAX_PER_RUN:
            break
    return n


def _sweep_deleted(cfg, raw):
    """出した本人が消したコース（del の印）を、library/ からも消す（v212）"""
    ids = []
    if isinstance(raw, dict) and isinstance(raw.get('del'), list):
        ids = [str(i) for i in raw['del'] if ID_OK.match(str(i))]
    if cfg.get('kind') == 'firebase':
        d = _read_json(str(cfg.get('url', '')).rstrip('/') + '/del.json')
        if isinstance(d, dict):
            ids = [k for k in d.keys() if ID_OK.match(str(k))]
    done = []
    for cid in ids[:MAX_PER_RUN]:
        hit = False
        for name in ('box-' + cid + '.json', 'box-' + cid + '-photos.json'):
            path = os.path.join(LIB_DIR, name)
            if os.path.exists(path):
                os.remove(path)
                print('消しました:', path)
                hit = True
        done.append(cid)
        if hit:
            pass
    if done and cfg.get('kind') != 'firebase':      # 消し終わった印は箱から外す（印がたまらないように）
        fresh = _read_json(_url(cfg, 'idx')) or {}
        rest = [str(i) for i in (fresh.get('del') or []) if str(i) not in done]
        try:
            _http(_url(cfg, 'idx'), data=json.dumps({'courses': _rows(fresh), 'del': rest}, ensure_ascii=False))
        except Exception as e:
            print('印を外せません:', e)
    elif done:
        for cid in done:
            try:
                _http(str(cfg.get('url', '')).rstrip('/') + '/del/' + cid + '.json', data='null', ctype='application/json')
            except Exception:
                pass
    return len(done)


def main():
    cfg = _cfg()
    if not cfg:
        print('箱は使わない設定です')
        return 0
    raw = _read_json(_url(cfg, 'idx'))
    swept = _sweep_deleted(cfg, raw)
    if swept:
        raw = _read_json(_url(cfg, 'idx'))          # 書き戻したので読み直す
    rows = _rows(raw)
    filled = _backfill_photos(cfg)                  # v242：写真を写しそこねた古いコースに、箱に残っている写真を補う
    if not rows:
        print('箱は空です（消した印の処理:', swept, '件／写真を補った:', filled, '件）')
        return 0
    os.makedirs(LIB_DIR, exist_ok=True)
    known = _known()          # v220：すでに載っているコースの指紋
    done, kept, bad = [], [], []
    for row in rows:
        if len(done) >= MAX_PER_RUN:
            kept.append(row)
            continue
        cid = str(row.get('id') or '')
        name = str(row.get('name') or '')
        if not ID_OK.match(cid) or not name.strip():
            print('とばす（名前かIDが不正）:', cid[:40])
            bad.append(cid)                             # 壊れた行は箱からも外す（開けない行を残さない）
            continue
        path = os.path.join(LIB_DIR, 'box-' + cid + '.json')
        if os.path.exists(path):
            done.append(cid)
            continue                                    # すでに写してある
        body = _read_json(_url(cfg, 'c', cid))
        d = (body or {}).get('d')
        if not isinstance(d, str) or not d or len(d) > MAX_BYTES:
            print('とばす（中身が無いか大きすぎる）:', cid)
            kept.append(row)
            continue
        kind = (body or {}).get('k') or 'd'
        # v220：他人が出したコースを、名義だけ変えて出し直すのを止める（中身の指紋で見分ける）
        course = _course_from_d(d, kind)
        fp = _fingerprint(course)
        oid = str(row.get('oid') or ((course or {}).get('origin') or {}).get('oid') or '')
        if fp and fp in known and known[fp] and oid and known[fp] != oid:
            print('載せません（同じコースを別の人が出しています）:', cid, name[:20])
            bad.append(cid)
            continue
        out = {'name': name[:80], 'area': str(row.get('area') or '')[:40],
               'by': str(row.get('by') or '')[:24], 'at': str(row.get('at') or '')[:10],
               'allowEdit': row.get('allowEdit') is not False, 'from': 'box',
               'oid': oid or None, 'fp': fp or None, 'k': (kind if kind == 'j' else None), 'd': d}
        out = {k: v for k, v in out.items() if v is not None}
        if row.get('cid'):                                  # v204：同じコースの出し直しを見分ける印
            out['cid'] = str(row['cid'])[:24]
            out['ts'] = str(row.get('ts') or '')[:24]
        nph = _ph_count(row.get('ph'))
        if nph:                                             # v202：写真も一緒に写す（別ファイル・一覧では読まない）
            pics = _read_photos(cfg, cid, nph)              # v242：分けて置いた全部を読んで1つにまとめる
            if pics is None:
                print('写真がまだ読めないので、次の回に写します:', cid)
                kept.append(row)
                continue
            if pics:
                _write_photos(cid, pics)
                out['ph'] = 'library/box-' + cid + '-photos.json'
                out['phn'] = nph
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print('写しました:', path)
        if fp:
            known[fp] = oid
        done.append(cid)
    if not done and not bad:
        print('新しく写したものはありません')
        return 0
    # 書き戻す直前にもう一度読む＝実行中に出されたコースを消さない
    fresh = _rows(_read_json(_url(cfg, 'idx')))
    drop = set(done) | set(bad)
    if cfg.get('kind') == 'firebase':
        for cid in done:
            try:
                _http(_url(cfg, 'row', cid), data='null', ctype='application/json')
                _http(_url(cfg, 'c', cid), data='null', ctype='application/json')
            except Exception as e:
                print('箱から外せません:', cid, e)
    else:
        rest = [r for r in fresh if str(r.get('id') or '') not in drop]
        try:
            _http(_url(cfg, 'idx'), data=json.dumps({'courses': rest}, ensure_ascii=False))
            nphs = {str(r.get('id') or ''): _ph_count(r.get('ph')) for r in rows}
            for cid in done:
                _http(_url(cfg, 'c', cid), data='')      # 中身も空にして箱を軽くする
                for i in range(nphs.get(cid, 0)):        # v202：写真も空にする（v242：分けて置いた全部）
                    _http(_url(cfg, 'ph', cid, i), data='')
        except Exception as e:
            print('箱を書き戻せません（次回また写します）:', e)
    print('写した件数:', len(done))
    return 0


if __name__ == '__main__':
    sys.exit(main())
