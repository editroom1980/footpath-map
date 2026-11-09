# ホーム画面のアイコン「藍の町」（v269）を書き出す。tools/アイコンを描く.html を WebKit で 2048 に描き、4つの大きさに縮めてリポジトリの直下に置く。
# 使い方：python3 tools/アイコンを書き出す.py   （playwright の webkit が要る）
import asyncio, os
from playwright.async_api import async_playwright
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
async def main():
    async with async_playwright() as p:
        b = await p.webkit.launch(); pg = await b.new_page(viewport={'width': 2100, 'height': 2100})
        await pg.goto('file://' + os.path.join(HERE, 'アイコンを描く.html')); await pg.wait_for_function('window.DONE===1', timeout=20000)
        tmp = os.path.join(HERE, '_icon_2048.png'); await pg.locator('#T5 svg').screenshot(path=tmp); await b.close()
    src = Image.open(tmp).convert('RGB').resize((1024, 1024), Image.LANCZOS); os.remove(tmp)
    for n, s in (('icon-1024.png', 1024), ('icon-512.png', 512), ('icon-192.png', 192), ('apple-touch-icon.png', 180)):
        (src if s == 1024 else src.resize((s, s), Image.LANCZOS)).save(os.path.join(ROOT, n), optimize=True); print(n)
asyncio.run(main())
