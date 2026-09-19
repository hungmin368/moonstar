#!/usr/bin/env python3
"""pollinations 出圖（序列+429重試）"""
import sys, time, urllib.parse, urllib.request, io, os
from PIL import Image

BASE = 'https://image.pollinations.ai/prompt/'

def gen(prompt, out, w=768, h=768, seed=1, model='flux', nologo=True, tries=8):
    q = urllib.parse.urlencode({'width': w, 'height': h, 'seed': seed, 'model': model,
                                'nologo': 'true' if nologo else 'false'})
    url = BASE + urllib.parse.quote(prompt, safe='') + '?' + q
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=150) as r:
                data = r.read()
            im = Image.open(io.BytesIO(data)); im.load()
            im.save(out)
            print(f'OK {out} {im.size} {len(data)}B try={i+1}', flush=True)
            return True
        except Exception as e:
            msg = str(e)[:120]
            print(f'  retry {i+1}/{tries} {out}: {msg}', flush=True)
            time.sleep(7 + i * 3)
    print(f'FAIL {out}', flush=True)
    return False

if __name__ == '__main__':
    ok = gen(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 768,
             int(sys.argv[4]) if len(sys.argv) > 4 else 768,
             int(sys.argv[5]) if len(sys.argv) > 5 else 1,
             sys.argv[6] if len(sys.argv) > 6 else 'flux')
    sys.exit(0 if ok else 1)
