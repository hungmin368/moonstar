# MEMORY.md — 長期記憶

> 最後更新：2026-09-15（精簡版：僅保留用戶基本資料與文件規範；其餘備份至 memory_old.md）

---

## 關於楊大

- 時區：Asia/Shanghai (GMT+8)
- 工作語言：繁體中文為主，技術名詞可用英文
- 回覆偏好：高效、直接、不廢話

---

## HTML 文件規範

- **模板：** `HTML_Template-v3.15.0.html`（已上傳至 media inbound；現有範例：`CABAC_H264_vs_H265-v1.0.0.html` 等）
- **強制規則：** 之後產生任何 HTML 文件，必須參考此模板的結構與樣式，包括：
  - 左側 sticky 目錄欄 + 右側主內容區（閱讀模式佈局）
  - 條目用 `<p class="num-item">` + `<strong>` flex 佈局（不用 `<ol>`）
  - 子項用 `<ol class="sub-items">` 或 `<ul class="sub-items-unordered">`
  - h2/h3 標題不縮進，正文 15px 左縮進
  - 色系：主色 #1565c0，克制用色 ≤3 種
  - 支援 Mermaid 流程圖 + WaveDrom 時序圖
  - contenteditable 編輯 + Ctrl+S 儲存下載
  - 版本號格式：vA.B[.C]，文件命名 XX-vA.B.C.html
