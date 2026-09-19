#!/usr/bin/env python3
"""修正版提示詞：重生成不合格樣本（避免 cat 字眼、強化飛踢動作）"""
import sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen import gen

STYLE = ("3D render of a cute chibi baby {species} dinosaur, kawaii, huge glossy eyes with "
         "catchlights, soft pastel colors, smooth vinyl toy figurine, product photo, "
         "soft studio lighting, pure white background, full body visible, centered")

JOBS = [
    ('01_catteaser_trex',
     STYLE.format(species='tyrannosaurus rex') + ", holding a small fishing-rod toy wand with a fluffy "
     "feather duster at the end, swinging the fluffy feather wand playfully, mischievous grin", 301),
    ('02_catteaser_trike',
     STYLE.format(species='triceratops') + ", holding a small toy wand with a dangling plush fish on a "
     "string, batting at the plush fish playfully", 302),
    ('03_kick_trex',
     STYLE.format(species='tyrannosaurus rex') + ", doing a flying side kick, one leg extended straight "
     "out forward, martial arts action pose, mid-air, dynamic", 303),
    ('04_kick_stego',
     STYLE.format(species='stegosaurus') + ", doing a flying side kick, one leg extended straight out, "
     "martial arts jump kick, mid-air, dynamic", 304),
    ('05_yoga_trex',
     STYLE.format(species='tyrannosaurus rex') + ", sitting in lotus meditation pose on a small pastel "
     "yoga mat, eyes closed, peaceful zen expression", 305),
    ('06_yoga_raptor',
     STYLE.format(species='velociraptor') + ", doing a yoga tree pose, balancing on one leg, front paws "
     "pressed together in prayer, zen, on a small yoga mat", 306),
    ('07_hero_trex',
     STYLE.format(species='tyrannosaurus rex') + ", superhero landing pose, one fist planted on the "
     "ground, one knee down, tiny red cape flowing on its back, dramatic heroic pose, comic style", 307),
    ('08_tattoo_anky',
     STYLE.format(species='ankylosaurus') + ", flexing its arm proudly, a bold black tattoo on its upper "
     "arm that says 'BOSS', confident smirk", 308),
]

if __name__ == '__main__':
    os.makedirs('samples/raw', exist_ok=True)
    only = sys.argv[1:] or None
    ok = 0
    for name, prompt, seed in JOBS:
        if only and name not in only:
            continue
        out = f'samples/raw/{name}.png'
        if gen(prompt, out, 768, 768, seed, 'flux'):
            ok += 1
        time.sleep(2)
    print(f'DONE {ok}', flush=True)
