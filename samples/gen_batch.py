#!/usr/bin/env python3
"""批次生成搞笑恐龍樣本（序列出圖，429 自動重試）"""
import sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen import gen

STYLE = ("cute kawaii chibi baby {species}, big glossy eyes, soft pastel colors, "
         "adorable 3D toy figurine render, sticker style, pure white background, "
         "no shadow, full body visible, centered, funny, playful")

JOBS = [
    ('01_catteaser_trex',
     STYLE.format(species='tyrannosaurus rex') + ", holding a cat teaser wand toy with a fluffy feather, "
     "swinging it like a weapon, mischievous grin", 101),
    ('02_catteaser_trike',
     STYLE.format(species='triceratops') + ", holding a cat teaser wand with a fish-shaped toy dangling, "
     "pouncing at it playfully", 102),
    ('03_kick_trex',
     STYLE.format(species='tyrannosaurus rex') + ", doing a flying kick, one leg stretched out high, "
     "dynamic kung fu action pose, tilted body", 103),
    ('04_kick_stego',
     STYLE.format(species='stegosaurus') + ", doing a flying kick, legs stretched out, "
     "dynamic jump kick pose, motion", 104),
    ('05_yoga_trex',
     STYLE.format(species='tyrannosaurus rex') + ", sitting in lotus yoga pose on a tiny yoga mat, "
     "eyes closed meditating peacefully, zen", 105),
    ('06_yoga_raptor',
     STYLE.format(species='velociraptor') + ", doing a yoga tree pose balancing on one leg, "
     "front paws together in prayer, zen", 106),
    ('07_hero_trex',
     STYLE.format(species='tyrannosaurus rex') + ", superhero landing pose, one fist on the ground, "
     "kneeling dramatically, tiny red hero cape on its back, determined face", 107),
    ('08_tattoo_anky',
     STYLE.format(species='ankylosaurus') + ", flexing its arm muscles proudly, showing a tattoo on its "
     "upper arm that says 'BOSS', confident smirk", 108),
]

if __name__ == '__main__':
    os.makedirs('samples/raw', exist_ok=True)
    ok = 0
    for name, prompt, seed in JOBS:
        out = f'samples/raw/{name}.png'
        if os.path.exists(out):
            print('skip', out, flush=True); ok += 1; continue
        if gen(prompt, out, 768, 768, seed, 'flux'):
            ok += 1
        time.sleep(2)
    print(f'DONE {ok}/{len(JOBS)}', flush=True)
