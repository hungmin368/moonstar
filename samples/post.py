#!/usr/bin/env python3
"""樣本後處理：去背（漸層背景 flood-fill）→ 去浮水印孤島 → 縮成 200px 透明 PNG"""
import sys, os
from collections import deque
from PIL import Image, ImageDraw, ImageFilter

OUT = 200


def bg_mask_small(im, W=256, T=10):
    """從四邊 flood-fill（逐步比較鄰居色差，可沿平滑漸層流動）"""
    small = im.convert('RGB').resize((W, max(1, int(W * im.height / im.width))), Image.LANCZOS)
    w, h = small.size
    px = small.load()
    mask = bytearray(w * h)
    dq = deque()

    def push(x, y, c0):
        if 0 <= x < w and 0 <= y < h and not mask[y * w + x]:
            c = px[x, y]
            if max(abs(c[i] - c0[i]) for i in range(3)) <= T:
                mask[y * w + x] = 1
                dq.append((x, y, c))

    for x in range(w):
        push(x, 0, px[x, 0]); push(x, h - 1, px[x, h - 1])
    for y in range(h):
        push(0, y, px[0, y]); push(w - 1, y, px[w - 1, y])
    while dq:
        x, y, c = dq.popleft()
        push(x + 1, y, c); push(x - 1, y, c); push(x, y + 1, c); push(x, y - 1, c)
    return mask, w, h


def fg_components(mask, w, h):
    """回傳前景連通元件清單（8-連通），每項為 (size, minx, miny, maxx, maxy)"""
    seen = bytearray(w * h)
    comps = []
    for i in range(w * h):
        if mask[i] or seen[i]:
            continue
        dq = deque([i]); seen[i] = 1
        n = 0; x0 = y0 = 10 ** 9; x1 = y1 = -1
        while dq:
            j = dq.popleft(); n += 1
            x, y = j % w, j // w
            x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        k = ny * w + nx
                        if not mask[k] and not seen[k]:
                            seen[k] = 1; dq.append(k)
        comps.append((n, x0, y0, x1, y1))
    comps.sort(reverse=True)
    return comps


def process(src, dst, W=256, T=10, drop_islands=True, shadow=True):
    im = Image.open(src).convert('RGB')
    mask, mw, mh = bg_mask_small(im, W, T)
    if drop_islands:
        comps = fg_components(mask, mw, mh)
        if comps:
            big = comps[0][0]
            keep = bytearray(len(mask))
            for (n, x0, y0, x1, y1) in comps:
                corner = x0 > mw * 0.62 and y0 > mh * 0.86
                if n >= big * 0.04 and not (corner and n < big * 0.5):
                    # 保留：主體與夠大的元件；排除右下角小孤島（浮水印）
                    for yy in range(y0, y1 + 1):
                        for xx in range(x0, x1 + 1):
                            keep[yy * mw + xx] = 1
            mask = bytes(1 - b for b in keep)
    m = Image.frombytes('L', (mw, mh), bytes(255 * (1 - b) for b in mask))
    m = m.resize(im.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.0))
    out = im.convert('RGBA')
    out.putalpha(m)
    # 去背殘渣：極低 alpha 全清
    a = out.split()[3].point(lambda v: 0 if v < 40 else v)
    out.putalpha(a)
    bb = out.split()[3].getbbox()
    if bb:
        out = out.crop(bb)
    k = min((OUT - 6) / out.width, (OUT - 6) / out.height)
    out = out.resize((max(1, int(out.width * k)), max(1, int(out.height * k))), Image.LANCZOS)
    fin = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
    fin.alpha_composite(out, ((OUT - out.width) // 2, (OUT - out.height) // 2))
    if shadow:
        sh = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
        d = ImageDraw.Draw(sh)
        cx = OUT // 2; by = min(OUT - 8, (OUT - out.height) // 2 + out.height - 4)
        rw = int(out.width * 0.42)
        d.ellipse([cx - rw, by - 6, cx + rw, by + 6], fill=(90, 80, 70, 70))
        sh = sh.filter(ImageFilter.GaussianBlur(5))
        fin = Image.alpha_composite(sh, fin)
    fin.save(dst)
    return fin


if __name__ == '__main__':
    os.makedirs('samples/out', exist_ok=True)
    for f in sys.argv[1:]:
        name = os.path.splitext(os.path.basename(f))[0]
        process(f, f'samples/out/{name}.png')
        print('processed', name, flush=True)
