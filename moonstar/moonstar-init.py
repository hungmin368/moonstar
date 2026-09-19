#!/usr/bin/env python3
# moonstar 引擎抽取：從 dinodoku 源抽出主題化引擎母本 + 兩套主題配置
import re, json, os

WS = '/home/node/.openclaw/workspace'
MS = f'{WS}/moonstar'
os.makedirs(MS, exist_ok=True)
os.makedirs(f'{MS}/themes', exist_ok=True)

engine = open(f'{WS}/dinodoku-dev/new-code-b.txt', encoding='utf-8').read()
body = open(f'{WS}/dinodoku-dev/new-body.txt', encoding='utf-8').read()

# ============ 1) 引擎：字串 → 標記（長詞先換）============
def markerize(src, pairs):
    for old, mk in pairs:
        src = src.replace(old, mk)
    return src

ls_pairs = []
for key in ['dex','sound','lv','lock','econ','skills','buddy','friend','friend2','story']:
    for old in [f"'meowdoku-{key}'", f"'pikadoku-{key}'"]:
        if old in engine:
            engine = engine.replace(old, f"@@LS_{key}@@")
            break

pairs = [
    ('Dinodoku 龍之數讀', '@@game_title@@'),
    ('恐龍圖鑑', '@@dex_title@@'),
    ('遠古王者', '@@legend_name@@'),
    ('常見 151', '@@tab_gen@@'),
    ('恐龍', '@@mon@@'),
    ('捕捉器', '@@ball_name@@'),
    ('小龍', '@@buddy_mon@@'),
]
engine = markerize(engine, pairs)

# RARITY 陣列 → 標記
engine = re.sub(r"const RARITY_NAMES = \[[^\]]*\];", "const RARITY_NAMES = @@RARITY_NAMES@@;", engine)
engine = re.sub(r"const RARITY_BADGE = \[[^\]]*\];", "const RARITY_BADGE = @@RARITY_BADGE@@;", engine)

# STORY 區塊 → 標記（內容存到主題檔）
m = re.search(r'const STORY = \[[\s\S]*?\n\];', engine)
assert m, 'STORY not found'
story_dino = m.group(0)
# 恐龍故事裡殘留的寶可夢名修正
story_dino = story_dino.replace('烈咬陸鯊','南方巨獸龍').replace('洛奇亞','風神翼龍').replace('鳳王','滄龍')
engine = engine.replace(m.group(0), 'const STORY = @@STORY@@;', 1)

open(f'{MS}/engine.txt','w',encoding='utf-8').write(engine)
open(f'{MS}/themes/story-dino.js','w',encoding='utf-8').write(story_dino)
print('engine.txt OK', len(engine), 'chars; 殘留主題詞:',
      [w for w in ['恐龍','捕捉器','小龍','Dinodoku'] if w in engine])

# ============ 2) body：字串 + SVG + 主題 CSS → 標記 ============
body = markerize(body, [
    ('Dinodoku 龍之數讀 — 恐龍解謎', '@@page_title@@'),
    ('Dinodoku 龍之數讀', '@@game_title@@'),
    ('數獨邏輯 × 踩地雷 × 收集養成 · 4×4 ~ 14×14 · 恐龍版 v1.0', '@@menu_sub@@'),
    ('恐龍圖鑑', '@@dex_title@@'),
    ('遠古王者', '@@legend_name@@'),
    ('常見 151', '@@tab_gen@@'),
    ('恐龍', '@@mon@@'),
    ('捕捉器', '@@ball_name@@'),
    ('小龍', '@@buddy_mon@@'),
])

# 捕捉器 SVG → @@ball_svg@@
m = re.search(r'<svg width="15" height="15" viewBox="0 0 32 32"[\s\S]*?</svg> @@ball_name@@', body)
assert m, 'ball svg not found'
dino_ball_svg = m.group(0).replace(' @@ball_name@@','')
body = body.replace(m.group(0), '@@ball_svg@@ @@ball_name@@', 1)

# 主題 CSS（星級底色 + 待機動畫）→ @@theme_css@@
theme_css_blocks = []
pat1 = re.search(r"/\* 星級底色[\s\S]*?\.dex-cell\.got\.s3 \{[^\}]*\}", body)
if pat1:
    theme_css_blocks.append(pat1.group(0))
    body = body.replace(pat1.group(0), '', 1)
pat2 = re.search(r"/\* 恐龍待機動畫[\s\S]*?#buddy img \{ animation:dinoIdle[^\}]*\}", body)
if pat2:
    theme_css_blocks.append(pat2.group(0))
    body = body.replace(pat2.group(0), '', 1)
dino_theme_css = '\n'.join(theme_css_blocks)

# 注入點：放在 </style> 前
body = body.replace('</style>', '@@theme_css@@\n</style>', 1)
open(f'{MS}/body.txt','w',encoding='utf-8').write(body)
print('body.txt OK; 殘留:', [w for w in ['恐龍','捕捉器','Dinodoku'] if w in body])

# ============ 3) pika 主題素材抽取 ============
pika_engine = open(f'{WS}/pika-v2-dev/new-code-b.txt', encoding='utf-8').read()
m = re.search(r'const STORY = \[[\s\S]*?\n\];', pika_engine)
assert m
open(f'{MS}/themes/story-pika.js','w',encoding='utf-8').write(m.group(0))
print('story-pika.js OK')

pika_body = open(f'{WS}/pika-v2-dev/new-body.txt', encoding='utf-8').read()
m = re.search(r'<svg width="15" height="15" viewBox="0 0 32 32"[\s\S]*?</svg> 精靈球', pika_body)
assert m, 'pika ball svg not found'
pika_ball_svg = m.group(0).replace(' 精靈球','')
print('pika ball svg OK')

# ============ 4) 主題配置 ============
pika_theme = {
  'name': 'pika',
  'output': f'{WS}/Pikadoku-v2.0.html',
  'strings': {
    'page_title': 'Pikadoku 寶讀 — 寶可夢解謎',
    'game_title': 'Pikadoku 寶讀',
    'menu_sub': '數獨邏輯 × 踩地雷 × 收集養成 · 4×4 ~ 14×14 · v2.1',
    'dex_title': '寶可夢圖鑑',
    'legend_name': '傳說·神話',
    'tab_gen': '初代 151',
    'mon': '寶可夢',
    'ball_name': '精靈球',
    'buddy_mon': '皮卡丘',
    'RARITY_NAMES': "['常見','稀有','遠古','神話']",
    'RARITY_BADGE': "['🟢','🔵','🟣','🟠']",
  },
  'ls': {k: v for k, v in {
    'dex':'meowdoku-dex','sound':'meowdoku-sound','lv':'pikadoku-lv','lock':'pikadoku-lock',
    'econ':'pikadoku-econ','skills':'pikadoku-skills','buddy':'pikadoku-buddy',
    'friend':'pikadoku-friend','friend2':'pikadoku-friend2','story':'pikadoku-story'}.items()},
  'ball_svg': pika_ball_svg,
  'theme_css': '',
  'story_file': 'story-pika.js',
  'data': 'pika',
}
dino_theme = {
  'name': 'dino',
  'output': f'{WS}/Dinodoku-1.0.html',
  'strings': {
    'page_title': 'Dinodoku 龍之數讀 — 恐龍解謎',
    'game_title': 'Dinodoku 龍之數讀',
    'menu_sub': '數獨邏輯 × 踩地雷 × 收集養成 · 4×4 ~ 14×14 · 恐龍版 v1.0',
    'dex_title': '恐龍圖鑑',
    'legend_name': '遠古王者',
    'tab_gen': '常見 151',
    'mon': '恐龍',
    'ball_name': '捕捉器',
    'buddy_mon': '小龍',
    'RARITY_NAMES': "['⭐','⭐⭐','⭐⭐⭐','⭐⭐⭐⭐','⭐⭐⭐⭐⭐']",
    'RARITY_BADGE': "['🟢','🔵','🟣','🟠','💠']",
  },
  'ls': {k: f'dinodoku-{k}' for k in ['dex','sound','lv','lock','econ','skills','buddy','friend','friend2','story']},
  'ball_svg': dino_ball_svg,
  'theme_css': dino_theme_css,
  'story_file': 'story-dino.js',
  'data': 'dino',
}
json.dump(pika_theme, open(f'{MS}/themes/pika.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(dino_theme, open(f'{MS}/themes/dino.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('themes OK')
print('dino_theme_css len:', len(dino_theme_css))
