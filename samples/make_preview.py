#!/usr/bin/env python3
"""最終樣本包：去背 → 200px → preview.html（含原圖對照與棋盤格小尺寸模擬）"""
import os, re, base64, glob
from PIL import Image
from rembg import remove, new_session

OUT = 200

# 挑選結果：(來源檔, 分類, 說明)
SELECTION = [
    # ('samples/raw/03_kick_trex.png', '飛踢', '暴龍 — 空中飛踢'),
]


def extract_originals(dst='samples/orig'):
    os.makedirs(dst, exist_ok=True)
    html = open('Dinodoku-1.0.html', encoding='utf-8').read()
    got = []
    for name, mid in (('POKEMON', 1), ('LEGENDS', 200)):
        m = re.search(r'const ' + name + r' = (\[.*?\]);\n', html, re.S)
        mm = re.search(r"\{id:%d,name:'(.*?)',stars:(\d+),img:'data:image/webp;base64,([A-Za-z0-9+/=]+)'\}" % mid, m.group(1))
        nm, st, b64 = mm.group(1), mm.group(2), mm.group(3)
        fn = f'{dst}/orig_{mid}.webp'
        open(fn, 'wb').write(base64.b64decode(b64))
        png = f'{dst}/orig_{mid}.png'
        Image.open(fn).convert('RGBA').save(png)
        got.append((png, nm, st))
    return got


def cut_one(src, dst, sess):
    im = Image.open(src).convert('RGB')
    cut = remove(im, session=sess, alpha_matting=False)
    bb = cut.split()[3].getbbox()
    if bb:
        cut = cut.crop(bb)
    k = (OUT - 6) / max(cut.width, cut.height)
    cut = cut.resize((max(1, int(cut.width * k)), max(1, int(cut.height * k))), Image.LANCZOS)
    fin = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
    fin.alpha_composite(cut, ((OUT - cut.width) // 2, (OUT - cut.height) // 2))
    fin.save(dst)
    return dst


def b64img(path):
    return 'data:image/png;base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def build(selection):
    sess = new_session('u2net')
    os.makedirs('samples/out', exist_ok=True)
    cards = ''
    for png, nm, st in extract_originals():
        cards += f'''
    <div class="card"><div class="stage orig"><img src="{b64img(png)}" class="s200"></div>
      <div class="cap"><b>原圖對照</b><span>{nm}（{st}★）</span></div></div>'''
    for i, (src, tag, desc) in enumerate(selection):
        name = 'sel_%02d_%s' % (i + 1, re.sub(r'[^A-Za-z0-9_]+', '', os.path.splitext(os.path.basename(src))[0])[:24])
        dst = f'samples/out/{name}.png'
        cut_one(src, dst, sess)
        cards += f'''
    <div class="card"><div class="stage"><img src="{b64img(dst)}" class="s200"></div>
      <div class="stage mini"><img src="{b64img(dst)}" class="s64"><span class="mini-cap">棋盤格大小</span></div>
      <div class="cap"><b>{tag}</b><span>{desc}</span></div></div>'''
    html = f'''<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dinodoku 搞笑恐龍樣本</title>
<style>
 body {{ font-family:"Microsoft JhengHei","PingFang TC",sans-serif; background:#fffdf9; color:#43382c; margin:0; padding:24px; }}
 h1 {{ font-size:22px; }} p.sub {{ color:#8a7d6c; font-size:14px; margin-top:4px; }}
 .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:16px; margin-top:18px; }}
 .card {{ background:#fff; border-radius:14px; padding:12px; box-shadow:0 2px 10px rgba(150,120,80,.15); }}
 .stage {{ background:#f3e2f7; border-radius:10px; display:flex; align-items:center; justify-content:center; padding:6px; }}
 .stage.orig {{ background:#f4ecdd; }}
 .stage.mini {{ background:#e8f0e0; margin-top:8px; height:84px; position:relative; }}
 .s200 {{ width:200px; height:200px; object-fit:contain; }}
 .s64 {{ width:64px; height:64px; object-fit:contain; }}
 .mini-cap {{ position:absolute; right:8px; bottom:6px; font-size:11px; color:#9c8f7d; }}
 .cap {{ margin-top:10px; display:flex; flex-direction:column; gap:2px; font-size:13px; }}
 .cap b {{ color:#c2570f; }} .cap span {{ color:#7a6d5b; }}
</style></head><body>
<h1>Dinodoku 搞笑恐龍樣本（AI 重新生成）</h1>
<p class="sub">第一張為原圖對照；其餘為搞笑版樣本。紫底＝圖鑑卡大小、綠底＝棋盤格大小。喜歡哪幾種再跟我說。</p>
<div class="grid">{cards}</div>
</body></html>'''
    open('samples/preview.html', 'w', encoding='utf-8').write(html)
    print('preview → samples/preview.html')


def sheet(paths, dst='samples/sheet.png'):
    cols = 4
    rows = (len(paths) + cols - 1) // cols
    sh = Image.new('RGBA', (cols * 210, rows * 210), (255, 253, 249, 255))
    for i, f in enumerate(paths):
        im = Image.open(f)
        if im.size != (OUT, OUT):
            im.thumbnail((OUT, OUT), Image.LANCZOS)
        sh.alpha_composite(im.convert('RGBA'), ((i % cols) * 210 + 5, (i // cols) * 210 + 5))
    sh.convert('RGB').save(dst)
    print('sheet →', dst)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        # 模式：python make_preview.py a.png b.png ... → 直接列出檔名當選項（逗號分隔標籤）
        sel = []
        for arg in sys.argv[1:]:
            parts = arg.split('|')
            src = parts[0]
            tag = parts[1] if len(parts) > 1 else ''
            desc = parts[2] if len(parts) > 2 else os.path.basename(src)
            sel.append((src, tag, desc))
        build(sel)
        sheet([f'samples/out/{f}' for f in sorted(os.listdir('samples/out')) if f.startswith('sel_')])
    else:
        print('usage: make_preview.py src.png|分類|說明 ...')
