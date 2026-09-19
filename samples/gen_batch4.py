#!/usr/bin/env python3
"""候選加強版：針對弱項概念多生幾張（含 turbo 模型對照）"""
import sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen import gen

STYLE = ("3D render of a cute chibi baby {species} dinosaur, kawaii, big glossy eyes, "
         "soft pastel colors, smooth vinyl toy figurine, product photo, soft studio lighting, "
         "pure white background, full body visible, centered")

JOBS = [
    # 逗貓棒（避免 cat 字眼）
    ('catteaser_a', STYLE.format(species='tyrannosaurus rex') + ", holding a small stick with a fluffy feather on the end, waving the feather toy, happy playful", 501, 'flux'),
    ('catteaser_b', STYLE.format(species='triceratops') + ", playing with a fluffy feather toy on a string, holding the string, joyful", 502, 'flux'),
    ('catteaser_c', STYLE.format(species='tyrannosaurus rex') + ", holding a toy wand with a small plush fish at the end, playful grin", 503, 'turbo'),
    # 飛踢候選
    ('kick_b', STYLE.format(species='triceratops') + ", flying kick pose, one leg kicked up high, kung fu, mid-air action, dynamic", 504, 'flux'),
    ('kick_c', STYLE.format(species='velociraptor') + ", flying jump kick, legs extended, martial arts action, mid-air, dynamic", 505, 'turbo'),
    # 瑜珈候選
    ('yoga_b', STYLE.format(species='tyrannosaurus rex') + ", sitting cross-legged on a purple yoga mat, meditating with eyes closed, paws resting on knees, zen", 506, 'flux'),
    ('yoga_c', STYLE.format(species='stegosaurus') + ", doing yoga, balancing on one leg with paws together, zen meditation, on a pastel yoga mat", 507, 'turbo'),
    # 英雄候選
    ('hero_b', STYLE.format(species='tyrannosaurus rex') + ", wearing a tiny red superhero cape, standing heroically with fists on hips, cape blowing in the wind, confident", 508, 'flux'),
    ('hero_c', STYLE.format(species='triceratops') + ", superhero flying pose, one fist stretched forward, tiny red cape flowing, comic hero, dynamic", 509, 'flux'),
    ('hero_d', STYLE.format(species='tyrannosaurus rex') + ", superhero landing, one knee on the ground, one fist down, red cape, dust, dramatic", 510, 'turbo'),
    # 刺青候選（AI 文字能力有限，仍試）
    ('tattoo_b', STYLE.format(species='tyrannosaurus rex') + ", flexing its arm, the word BOSS tattooed in bold black letters on its arm, proud smirk", 511, 'flux'),
    ('tattoo_c', STYLE.format(species='ankylosaurus') + ", showing off its arm, black tattoo on the arm, confident", 512, 'turbo'),
]

if __name__ == '__main__':
    os.makedirs('samples/cand', exist_ok=True)
    for name, prompt, seed, model in JOBS:
        out = f'samples/cand/{name}.png'
        if os.path.exists(out):
            print('skip', out, flush=True); continue
        gen(prompt, out, 768, 768, seed, model)
        time.sleep(1)
    print('DONE', flush=True)
