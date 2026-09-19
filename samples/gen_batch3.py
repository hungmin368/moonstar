#!/usr/bin/env python3
"""候選多張版：每個概念 3 個 seed，事後挑最好的"""
import sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen import gen

STYLE = ("3D render of a cute chibi baby {species}, kawaii, big glossy eyes, soft pastel colors, "
         "smooth vinyl toy figurine, product photo, soft studio lighting, pure white background, "
         "full body visible, centered")

CONCEPTS = {
    'catteaser': STYLE.format(species='tyrannosaurus rex dinosaur') + ", playfully holding a toy wand with a fluffy feather, waving it around, happy",
    'kick': STYLE.format(species='tyrannosaurus rex dinosaur') + ", doing a flying kick, one leg extended straight out, martial arts jump kick pose, mid-air, dynamic",
    'yoga': STYLE.format(species='tyrannosaurus rex dinosaur') + ", sitting in lotus meditation pose, eyes closed, peaceful zen, on a small pastel yoga mat",
    'hero': STYLE.format(species='tyrannosaurus rex dinosaur') + ", superhero landing pose, one fist planted on the ground, one knee down, tiny red cape, heroic",
    'tattoo': STYLE.format(species='tyrannosaurus rex dinosaur') + ", proudly flexing its arm, bold black tattoo on its upper arm reading BOSS, confident smile",
}

if __name__ == '__main__':
    os.makedirs('samples/cand', exist_ok=True)
    which = sys.argv[1:] or list(CONCEPTS)
    for key in which:
        for i, seed in enumerate((401, 402, 403)):
            out = f'samples/cand/{key}_{i + 1}.png'
            if os.path.exists(out):
                print('skip', out, flush=True); continue
            gen(CONCEPTS[key], out, 768, 768, seed + hash(key) % 50, 'flux')
            time.sleep(1)
    print('DONE', flush=True)
