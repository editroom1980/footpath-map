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
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOX_FILE = os.path.join(ROOT, 'box.json')
LIB_DIR = os.path.join(ROOT, 'library')
MAX_PER_RUN = 30          # 1回に写す件数の上限
MAX_BYTES = 400 * 1024    # コース1件の中身の上限
TIMEOUT = 20
ID_OK = re.compile(r'^[A-Za-z0-9-]{4,40}$')


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


def _url(cfg, what, cid=None):
    if cfg.get('kind') == 'firebase':
        u = str(cfg.get('url', '')).rstrip('/')
        if what == 'idx':
            return u + '/idx.json'
        if what == 'row':
            return u + '/idx/' + cid + '.json'
        return u + '/c/' + cid + '.json'
    base = str(cfg.get('base', '')) + str(cfg.get('key', ''))
    return base if what == 'idx' else base + '-' + cid


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


def main():
    cfg = _cfg()
    if not cfg:
        print('箱は使わない設定です')
        return 0
    raw = _read_json(_url(cfg, 'idx'))
    rows = _rows(raw)
    if not rows:
        print('箱は空です')
        return 0
    os.makedirs(LIB_DIR, exist_ok=True)
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
        out = {'name': name[:80], 'area': str(row.get('area') or '')[:40],
               'by': str(row.get('by') or '')[:24], 'at': str(row.get('at') or '')[:10],
               'allowEdit': row.get('allowEdit') is not False, 'from': 'box', 'd': d}
        if row.get('ph'):                                   # v202：写真も一緒に写す（別ファイル・一覧では読まない）
            pb = _read_json(_url(cfg, 'ph', cid))
            pics = (pb or {}).get('p')
            if isinstance(pics, dict) and pics:
                ppath = os.path.join(LIB_DIR, 'box-' + cid + '-photos.json')
                with open(ppath, 'w', encoding='utf-8') as f:
                    json.dump({'p': pics}, f, ensure_ascii=False)
                out['ph'] = 'library/box-' + cid + '-photos.json'
                print('写真も写しました:', ppath)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print('写しました:', path)
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
            for cid in done:
                _http(_url(cfg, 'c', cid), data='')      # 中身も空にして箱を軽くする
                _http(_url(cfg, 'ph', cid), data='')     # v202：写真も空にする
        except Exception as e:
            print('箱を書き戻せません（次回また写します）:', e)
    print('写した件数:', len(done))
    return 0


if __name__ == '__main__':
    sys.exit(main())
