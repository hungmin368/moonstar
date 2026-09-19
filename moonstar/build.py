#!/usr/bin/env python3
# moonstar 統一遊戲引擎構建器
# 用法: python3 build.py [--out-dir DIR] [pika|dino ...]
#   不帶參數 → 構建全部主題，輸出到工作區根目錄（交付檔位置）
#   --out-dir DIR → 輸出到指定目錄（驗證用，不碰交付檔）
# 路徑解析（依優先序）：MOONSTAR_WS 環境變數 → 容器預設路徑 → 本腳本所在 moonstar/ 的上層
# 資料源（依優先序）：
#   1. 開發素材（Pikadoku-v1.1.html + pika-v2-dev/、dinodoku-dev/）
#   2. 現有交付檔 → 抽取資料段（code_a/POKEMON/LEGENDS/hook/POOL）回填，
#      母本改版後即可重現交付檔，無需開發素材
import re, json, os, sys, base64, glob

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

def detect_ws():
    env = os.environ.get('MOONSTAR_WS')
    if env and os.path.isdir(env):
        return env
    if os.path.isdir('/home/node/.openclaw/workspace'):
        return '/home/node/.openclaw/workspace'
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(here) == 'moonstar':
        return os.path.dirname(here)
    return os.getcwd()

MS = os.path.dirname(os.path.abspath(__file__))
WS = detect_ws()
PIKA_DEV = os.path.join(WS, 'pika-v2-dev')      # LEGENDS 素材、棋盤池共用
DINO_DEV = os.path.join(WS, 'dinodoku-dev')     # 恐龍清單與圖

def js_str(s):
    """名稱注入 JS 單引號字串的防護轉義"""
    return s.replace('\\', '\\\\').replace("'", "\\'")

def apply_theme(src, theme):
    S = theme['strings']
    for k, v in S.items():
        src = src.replace(f'@@{k}@@', v)
    for k, v in theme['ls'].items():
        src = src.replace(f'@@LS_{k}@@', f"'{v}'")
    src = src.replace('@@ball_svg@@', theme['ball_svg'])
    src = src.replace('@@theme_css@@', theme.get('theme_css',''))
    left = re.findall(r'@@[A-Za-z_0-9]+@@', src)
    assert not left, f'未替換標記: {left[:5]}'
    return src

def build_pool():
    pool = {}
    src_dir = f'{PIKA_DEV}/pool'
    if not os.path.isdir(src_dir):
        print(f'[警告] 找不到棋盤池目錄 {src_dir} → POOL_DATA 為空（僅執行期生成，開場較慢）')
        return pool
    for n in range(10, 15):
        boards, seen = [], set()
        for f in sorted(glob.glob(f'{src_dir}/pool-{n}.jsonl')) + sorted(glob.glob(f'{src_dir}/v6-{n}-*.json')):
            try:
                if f.endswith('.jsonl'):
                    for line in open(f, encoding='utf-8'):
                        line = line.strip()
                        if not line: continue
                        obj = json.loads(line)
                        key = obj['board'] if isinstance(obj, dict) else str(obj)
                        if key not in seen: seen.add(key); boards.append(key)
                else:
                    for item in json.load(open(f, encoding='utf-8')):
                        key = item if isinstance(item, str) else ','.join(map(str, item))
                        if key not in seen: seen.add(key); boards.append(key)
            except Exception as e:
                print(f'[警告] 池檔解析失敗（跳過） {f}: {e}')
        if boards: pool[str(n)] = boards
    print('pool:', {k: len(v) for k, v in pool.items()})
    return pool

def sprites_to_base64():
    """pika LEGENDS：sprites → base64（含文件頭驗證）"""
    ZH = json.load(open(f'{MS}/themes/zh-names.json', encoding='utf-8'))
    LEGS = []
    sh = f'{PIKA_DEV}/dl-sprites.sh'
    if not os.path.exists(sh):
        sys.exit(f'[錯誤] 找不到 {sh}（開發素材不完整）')
    ids = open(sh, encoding='utf-8').read()
    id_match = re.findall(r'IDS="([0-9 ]+)"', ids)
    if not id_match:
        sys.exit(f'[錯誤] {sh} 內找不到 IDS="..." 定義 → 拒絕產出空 LEGENDS')
    target_ids = set(int(x) for x in id_match[0].split())
    names = {}
    try:
        raw = json.load(open(f'{PIKA_DEV}/id2name.json', encoding='utf-8'))
        names = {int(k): v for k, v in raw.items()}
    except Exception: pass
    skipped = []
    for fid in sorted(target_ids):
        for ext in ['gif', 'png']:
            path = f'{PIKA_DEV}/sprites/{fid}.{ext}'
            if not os.path.exists(path): continue
            raw = open(path, 'rb').read()
            if ext == 'gif' and not raw[:4] == b'GIF8': skipped.append((fid, ext)); break
            if ext == 'png' and not raw[:4] == b'\x89PNG': skipped.append((fid, ext)); break
            if len(raw) < 1500: skipped.append((fid, ext)); break
            data = base64.b64encode(raw).decode()
            mime = 'image/gif' if ext == 'gif' else 'image/png'
            zh = ZH.get(str(fid))
            name = zh if zh else '-'.join(w.capitalize() for w in names.get(fid, f'Pokemon_{fid}').split('-'))
            LEGS.append(f"{{id:{fid},name:'{js_str(name)}',img:'data:{mime};base64,{data}'}}")
            break
        else:
            skipped.append((fid, '-'))
    if skipped: print('LEGENDS skip:', skipped)
    print(f'LEGENDS: {len(LEGS)} 只注入')
    return '[' + ','.join(LEGS) + ']'

def build_pika_data():
    orig = open(f'{WS}/Pikadoku-v1.1.html', encoding='utf-8').read()
    lines = orig.split('\n')
    pi = next(i for i, l in enumerate(lines) if l.startswith('const POKEMON ='))
    si = next(i for i, l in enumerate(lines[:pi]) if l.strip() == '<script>')
    code_a = '\n'.join(lines[si:pi])
    assert 'PALETTE' in code_a and "'use strict'" in code_a
    pokemon_line = lines[pi]
    # 官方中文譯名
    ZH = json.load(open(f'{MS}/themes/zh-names.json', encoding='utf-8'))
    def zh_repl(m):
        mid = int(m.group(1))
        return f"id:{mid},name:'{js_str(ZH.get(str(mid), m.group(2)))}'"
    pokemon_line = re.sub(r"id:(\d+),name:'([^']+)'", zh_repl, pokemon_line)
    legends_line = 'const LEGENDS = ' + sprites_to_base64() + ';'
    # 星級掛鉤：寶可夢 rarity → stars（1-4）
    hook = """
const GEN1_LEG_IDS = new Set([144,145,146,150]);
const MYTHIC_IDS = new Set([151,251,385,386,489,490,491,492,493,494,647,648,649,719,720,721,801,802,807,808,809,1025]);
POKEMON.forEach(p=>{ p.stars = (p.id===151)?4:(GEN1_LEG_IDS.has(p.id)?3:(p.id===149?2:1)); });
LEGENDS.forEach(p=>{ p.stars = MYTHIC_IDS.has(p.id)?4:3; });
"""
    return code_a, pokemon_line, legends_line, hook

def build_dino_data():
    orig = open(f'{WS}/Pikadoku-v1.1.html', encoding='utf-8').read()
    lines = orig.split('\n')
    pi = next(i for i, l in enumerate(lines) if l.startswith('const POKEMON ='))
    si = next(i for i, l in enumerate(lines[:pi]) if l.strip() == '<script>')
    code_a = '\n'.join(lines[si:pi])
    from urllib.parse import quote
    dino_data = json.load(open(f'{DINO_DEV}/dino-list.json', encoding='utf-8'))
    mons = dino_data['mons']
    def placeholder(stars):
        emoji = {1:'🦎',2:'🦕',3:'🦖',4:'🐉',5:'🐲'}[stars]
        bg = {1:'#e8f5e9',2:'#c8e6c9',3:'#ffe0b2',4:'#ffcc80',5:'#ffab91'}[stars]
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='96' height='96'>"
               f"<rect width='96' height='96' rx='16' fill='{bg}'/>"
               f"<text x='48' y='64' font-size='46' text-anchor='middle'>{emoji}</text></svg>")
        return 'data:image/svg+xml;charset=utf-8,' + quote(svg)
    def dino_img(mid, stars):
        for ext in ['webp','png','gif']:
            p = f'{DINO_DEV}/dinos/{mid}.{ext}'
            if os.path.exists(p):
                raw = open(p, 'rb').read()
                if len(raw) > 500:
                    mime = {'webp':'image/webp','png':'image/png','gif':'image/gif'}[ext]
                    return 'data:'+mime+';base64,'+base64.b64encode(raw).decode()
        return placeholder(stars)
    common = [m for m in mons if m['id'] <= 151]
    legend = [m for m in mons if m['id'] >= 200]
    assert len(common) == 151 and len(legend) == 126
    mk = lambda m: "{{id:{id},name:'{name}',stars:{stars},img:'{img}'}}".format(
        id=m['id'], name=js_str(m['name']), stars=m['stars'], img=dino_img(m['id'], m['stars']))
    pokemon_line = 'const POKEMON = [' + ','.join(mk(m) for m in common) + '];'
    legends_line = 'const LEGENDS = [' + ','.join(mk(m) for m in legend) + '];'
    return code_a, pokemon_line, legends_line, ''

def extract_data_from_product(product_path):
    """從現有交付檔抽取資料段（code_a/POKEMON/LEGENDS/hook/POOL），母本改版後重現交付檔用"""
    lines = open(product_path, encoding='utf-8').read().split('\n')
    si = next(i for i, l in enumerate(lines) if l.strip() == '<script>')
    pi = next(i for i, l in enumerate(lines) if l.startswith('const POKEMON ='))
    li = next(i for i, l in enumerate(lines) if l.startswith('const LEGENDS ='))
    ei = next(i for i, l in enumerate(lines) if l.startswith('/* ---------- 配色'))
    assert si < pi < li < ei, f'交付檔結構異常: script={si} POKEMON={pi} LEGENDS={li} engine={ei}'
    code_a = '\n'.join(lines[si:pi])
    assert 'PALETTE' in code_a and "'use strict'" in code_a
    between = lines[li+1:ei]
    assert between[0] == '' and between[-1] == '', '交付檔 hook 段結構異常'
    core = between[1:-1]
    hook = ('\n' + '\n'.join(core) + '\n') if core else ''
    pool_line = next(l for l in lines if l.startswith('const POOL_DATA = '))
    pool_json = pool_line[len('const POOL_DATA = '):].rstrip(';')
    assert pool_json.startswith('{'), 'POOL_DATA 抽取失敗'
    print('pool（抽取）:', {k: len(v) for k, v in json.loads(pool_json).items()})
    print(f"抽取自 {os.path.basename(product_path)}：POKEMON/LEGENDS/hook({len(core)} 行)/POOL")
    return code_a, lines[pi], lines[li], hook, pool_json

def resolve_data(theme, product_path):
    """資料源：開發素材優先，缺件時退回現有交付檔抽取"""
    if theme['data'] == 'pika':
        need = [f'{WS}/Pikadoku-v1.1.html', f'{PIKA_DEV}/dl-sprites.sh']
    else:
        need = [f'{DINO_DEV}/dino-list.json']
    if all(os.path.exists(p) for p in need):
        print(f"[{theme['name']}] 資料源：開發素材")
        if theme['data'] == 'pika':
            code_a, pokemon_line, legends_line, hook = build_pika_data()
        else:
            code_a, pokemon_line, legends_line, hook = build_dino_data()
        return code_a, pokemon_line, legends_line, hook, json.dumps(build_pool())
    if os.path.exists(product_path):
        missing = ', '.join(os.path.basename(p) for p in need if not os.path.exists(p))
        print(f"[{theme['name']}] 開發素材缺件（{missing}）→ 改用交付檔抽取")
        return extract_data_from_product(product_path)
    sys.exit(f"[錯誤] 資料源皆不可用：開發素材 {need} 與交付檔 {product_path} 均不存在")

def build(theme_name, out_dir=None):
    theme = json.load(open(f'{MS}/themes/{theme_name}.json', encoding='utf-8'))
    body = apply_theme(open(f'{MS}/body.txt', encoding='utf-8').read(), theme)
    engine_raw = open(f'{MS}/engine.txt', encoding='utf-8').read().replace('@@STORY@@', '__STORY_SLOT__')
    engine = apply_theme(engine_raw, theme)
    story = open(f"{MS}/themes/{theme['story_file']}", encoding='utf-8').read()
    assert 'const STORY = __STORY_SLOT__;' in engine, 'engine.txt 缺少 STORY 插槽'
    engine = engine.replace('const STORY = __STORY_SLOT__;', story, 1)

    product_path = os.path.join(WS, os.path.basename(theme['output']))
    code_a, pokemon_line, legends_line, hook, pool_json = resolve_data(theme, product_path)
    assert '/*__POOL_DATA__*/ {}' in engine, 'engine.txt 缺少 POOL_DATA 插槽'
    engine = engine.replace('/*__POOL_DATA__*/ {}', pool_json)

    out = (body + '\n' + code_a + '\n' + pokemon_line + '\n' + legends_line + '\n' + hook
           + '\n' + engine + '\n</script>\n</body>\n</html>\n')
    left = re.findall(r'@@[A-Za-z_0-9]+@@', out)
    assert not left, f'未替換標記殘留於最終輸出: {left[:5]}'

    target_dir = out_dir or WS
    os.makedirs(target_dir, exist_ok=True)
    out_path = os.path.join(target_dir, os.path.basename(theme['output']))
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        f.write(out)
    print(f"[{theme_name}] 寫出 {out_path}，大小 {os.path.getsize(out_path)}")

if __name__ == '__main__':
    args = sys.argv[1:]
    out_dir = None
    if '--out-dir' in args:
        i = args.index('--out-dir')
        if i + 1 >= len(args):
            sys.exit('--out-dir 需要一個目錄參數')
        out_dir = args[i+1]
        del args[i:i+2]
    print(f'工作區 WS = {WS}')
    for t in (args or ['pika', 'dino']):
        build(t, out_dir)
