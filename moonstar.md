# moonstar.md — Moonstar 遊戲引擎 專案記憶（獨立檔案，不入全域 MEMORY.md）

> 最後更新：2026-09-18 16:05 · 引擎版本 v1.6（moonstar 架構 + 本地可攜構建）
> **本檔是 Pikadoku 與 Dinodoku 的唯一真相源記憶**

## Moonstar 架構（2026-09-17 11:00 建立，用戶命名）

```
moonstar/                    ← 引擎母本（改這裡，兩遊戲同步）
├── engine.txt               ← JS 引擎母本（帶 @@標記@@ 佔位）
├── body.txt                 ← HTML/CSS 母本（帶 @@標記@@）
├── build.py                 ← 統一構建器（python3 build.py [pika|dino]）
├── moonstar-init.py         ← 從舊源抽取母本的歷史腳本（一次性）
└── themes/
    ├── pika.json            ← 寶可夢文案/精靈球SVG/4階稀有度/LS=pikadoku-*
    ├── dino.json            ← 恐龍文案/捕捉器SVG/5星制/星級底色CSS/待機動畫/LS=dinodoku-*
    ├── story-pika.js        ← 皮卡丘 17 幕故事
    └── story-dino.js        ← 小龍 17 幕故事（烈咬陸鯊→南方巨獸龍等已修正）
```

- **構建**：`cd moonstar && python3 build.py` → 同時輸出 Pikadoku-v2.0.html（28MB）與 Dinodoku-1.0.html（2.5MB）
- **改引擎流程**：改 engine.txt/body.txt → build.py → jsdom 測試 → 雙遊戲上傳
- **主題標記**：@@mon@@（寶可夢/恐龍）、@@ball_name@@（精靈球/捕捉器）、@@buddy_mon@@（皮卡丘/小龍）、@@game_title@@、@@dex_title@@、@@legend_name@@、@@tab_gen@@、@@RARITY_NAMES@@/@@RARITY_BADGE@@、@@STORY@@、@@LS_{key}@@（存檔命名空間）、@@ball_svg@@、@@theme_css@@、@@menu_sub@@、@@page_title@@
- **數據源**：pika=Pikadoku-v1.1.html 抽 POKEMON + pika-v2-dev/sprites LEGENDS（105隻）+ 星級掛鉤（GEN1_LEG_IDS/MYTHIC_IDS→stars 1-4）；dino=dinodoku-dev/dino-list.json（277隻真實學名）+ dinos/*.webp（AI生成去白底）
- **棋盤池共用**：pika-v2-dev/pool/（10:20、11:18、12:12、13:15、14:25 盤）
- **LS 命名空間已分離**（修掉同瀏覽器互相污染圖鑑的 bug）：pika 保留 pikadoku-*/meowdoku-*，dino 用 dinodoku-*

## 兩遊戲現況

| | Pikadoku 寶讀 | Dinodoku 龍之數讀 |
|---|---|---|
| 版本 | v2.1 | v1.0 |
| 生物 | 256（151初代+105傳說）| 277（真實恐龍學名，無版權問題）|
| 稀有度 | 4階（常見/稀有/遠古/神話）| 5星制（⭐~⭐⭐⭐⭐⭐）|
| 特色 | 寶可夢動圖GIF | AI生成萌恐龍+星級底色+待機動畫+星級光圈 |
| 檔案 | 28MB | 2.5MB |
| 分發 | sophnet-oss 24h 連結 | 同左 |

## 引擎功能全表（v1.3，兩遊戲共用）

- 尺寸 4~14（15-20 已移除，生成數學上不可行）；4=示範教學、5=引導教學；難度名：6-8新手/9-10學徒/11大師/12菁英/13傳奇/14神話
- 沙漏計時 N 分鐘；捕獲+30s；提示每關首次免費（之後🌌×1）；重來↻/放棄⏏按鈕
- **捕捉器＝隻數+3**（容錯）；捕獲動畫 2s、5★ 4s＋煙火＋「王者降臨」橫幅
- 經濟：星願種子🌌（提示/餵食/激發）＋獎勵券🎟（過關+1）；獎勵中心 6 小遊戲（刮刮樂/拉霸/翻牌/輪盤/剪影/尋寶）
- **抽獎概率 v1.2**：星數越多基礎權重越低（2★6→5★0.7）；棋盤越大高星加成越陡（10×10起，5★斜率0.45/級）；連勝加成（ECON.streak，敗/時/棄歸零，5★斜率0.22/層上限20）
- 隨行系統：圖鑑設隨行、右下圖鑑面板下方、閒聊30-90s、友好度♥（per-mon，餵食🍖🌌×1=+5%、過關+5%）、里程碑愛心
- **聊天訊息欄**（v1.6）：隨行訊息同步至頁面下方卷軸（#buddy-bar），垂直捲動、可視高度 118px＝恰好 3 則訊息、自動捲至最新、保留最近 6 則；webkit 細捲軸樣式（與 #board-scroll 同色系）
- **技能按鍵**（玩家主動發動，不自動施放）：星級決定數量（1★=1→5★=5），學過的優先；冷卻按檔位 15/25/40/60s；sweep=自動✕安全格（微風1/淨化2/暴風4）
- **星級光圈**：棋盤捕獲格+隨行圖，drop-shadow 五色（綠/藍/琥珀/橙/紫）
- **滿好感(100%)獎勵**：捕獲後動畫結束，自動✕同行+同列+周圍8格（去重），間隔0.2s逐格，隨行喊話
- 潛能激發：🌌5/25/125/500 抽技能，重複退50%
- 故事 17 幕（LV4-14 首勝觸發）；工程模式（標題連點5次：立即過關/種子+100/券+10/跳關/解鎖/∞開關/獎勵中心直達/餵食/技能測試/清檔）
- 24h 密碼鎖（6688）；WebAudio 音效；jsdom 測試全綠

## 技術要點

- **生成器 gen-v10**（pika-v2-dev/）：v6獵殺+K=60梯度（N≥16初始解300+，K=10截斷梯度失效）+solveK節點上限200k（防全樹卡死）+stuck>50快退；N=13約2s/盤
- **N≥16 唯一解不可行**（已從遊戲移除15-20）；若未來要恢復：少解盤方案（≤4解+遊戲接受任意解，遊戲端補丁見 memory/2026-09-16.md）
- solve2(N,ro,nodeLimit,K)：runtime 節點熔斷防卡死；newBoard 預算 [1200,3000,8000]
- 恐龍圖：Z-Image-Turbo 生成→PIL 200px webp（~4KB/張）→dewhite.py 去白底（白→透明、近白→85alpha）
- 佔位標記必須在 build 斷言全替換（apply_theme assert @@...@@ 清零）
- 測試：jsdom（/tmp/pika-test、/tmp/dino-test，npm i jsdom；28MB 檔先剝 base64 成 slim）；mock 開局需 lock+buddy+econ+ballMode+catUnion 全套

## 開發教訓（v2.0→moonstar 全程）

1. python 補丁 MISS 斷言要在 write 之後，否則提前 SystemExit 全丟（工程模式按鈕 9 處白打過一次）
2. /tmp 容器重啟清空——池/測試環境丟過兩次；持久檔一律 workspace
3. solveK 必須節點上限；K 截斷殺梯度；v6 在 N≥16 無效的根因
4. 交付前必須 jsdom 實測點擊流（grep 只能驗證代碼在檔）；mock 要還原真實調用鏈（ballMode/catUnion/lock）
5. 用戶常拿舊連結舊檔測試——回覆強調「重新下載」
6. CSS 選擇器要對齊真實 class（.alive vs .cat 光圈 bug）
7. & 鏈式後台命令 cwd 陷阱（nohup cmd & cmd2 & 第二個起跑在原 cwd）——用絕對路徑
8. exec 長命令會被 SIGTERM——python heredoc 拆小步驟
9. 同瀏覽器多遊戲必須 LS 命名空間分離

## 版本沿革

- v0.1~v1.0（09-15）：貓咪概念→寶可夢→Pikadoku 更名
- v1.1/v1.1.1（09-15深夜）：尺寸4-12、雙教學、沙漏、LV計分、24h鎖
- v2.0（09-16）：尺寸4-20、經濟系統、獎勵中心、隨行、故事、工程模式、LEGENDS 126、池10-13
- v2.1（09-17晨）：移除15-20、POOL_SIZES修復、提示免費、重來/放棄、技能修正、難度命名
- **moonstar v1.0（09-17 11:00）**：引擎抽取、主題架構、LS 分離
- **moonstar v1.1~v1.3（09-17 午）**：隨行光圈、技能按鍵化+星級數量+檔位冷卻、概率機制（格數/連勝）、捕獲動畫2s/5★4s煙火、捕捉器+3、滿好感自動排除
- **moonstar v1.4（09-18）本地可攜構建 + 致命 bug 修復**：
  - `build.py` 重寫：路徑自動偵測（MOONSTAR_WS env → 容器路徑 → 腳本上層），脫離容器即可跑
  - 資料源回退鏈：開發素材優先，缺件時從現有交付檔抽取 code_a/POKEMON/LEGENDS/hook/POOL 回填 → 母本改版後無需素材即可重現交付檔（已驗證位元組級一致，僅差預期修改行）
  - `--out-dir DIR` 驗證式構建；輸出強制 UTF-8/LF（防 Windows CRLF 污染）
  - 空 LEGENDS／池檔解析失敗改為響亮報錯；名稱注入加 js_str 單引號轉義
  - **修復致命 bug：engine.txt 死引用 `$('dex-title-btn')`**（body.txt 無此元素）→ JS 於此崩潰，其後 35+ 事件綁定（開局/捕捉/結算/24h鎖/啟動渲染）全部失效，兩遊戲交付檔實際不可玩；已刪行重建，瀏覽器實測雙遊戲全流程通（開局→捕獲→過關→故事→獎勵→圖鑑）
  - 譯名修正：id:123 飛天螳螂（原簡体混入）；zh-build.py 路徑改相對；池註釋 10~12→10~14
  - 本機工作區 `C:\MY_AI_JOBS\doku\`：moonstar/（母本+新 build.py）+兩交付檔；開發素材僅存容器，本機構建走交付檔抽取回退
- **moonstar v1.5~v1.6（09-18 下午）**：
  - v1.5：故事清單 `const` 賦值崩潰修復（story-list 改 `let`）
  - v1.6：隨行聊天訊息同步至下方聊天訊息欄（先橫向膠囊 → 當日改為垂直捲軸）；最終規格＝垂直捲動、118px＝3 則訊息高度、保留最近 6 則、自動捲至最新；已加 webkit 細捲軸樣式；兩遊戲已重建並瀏覽器實測（Dinodoku 開局→技能訊息入欄、Pikadoku 渲染）

## 用戶偏好（延續）

- 繁體中文；有小朋友（受眾）→風格可愛、文案萌系
- 分發：sophnet-oss 24h 連結；手機 Chrome 開 file://
- 遊戲不販賣不公開、家庭自用（頁尾宣告）
- Dinodoku 是無版權版本（真實恐龍學名+AI圖）——可自由分享
