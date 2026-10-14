---
name: dnd-dm-guide-builder
description: Use when preparing to run a tabletop RPG module (D&D 5e, Pathfinder, Call of Cthulhu...) from a PDF and the user wants a DM quick-reference / DM screen / per-area cheat sheet / "跑团准备""DM速查""模组整理""做DM指南" — especially when they want read-aloud text, per-area running notes for each scene, monster HP/stat lookups, maps, traps, foreshadowing, or NPC dialogue ready at the table.
description_zh: "把跑团模组的 PDF 变成单文件 HTML 的 DM 速查手册：逐区域念白 / 运行脚本 / 怪物血量 / 地图 / NPC 谈判 / 陷阱 / 伏笔"
description_en: "Turn a TTRPG module PDF into a single-file HTML DM quick-reference: read-aloud, per-area running scripts, monster HP, maps, NPC negotiation, traps, foreshadowing"
version: 1.0.0
allowed-tools: Bash,Read,Write
icon: 🎲
---

# TTRPG DM Guide Builder

## 概述

把一本模组 PDF 变成**单文件 HTML 的 DM 速查手册**：离线可开、可打印、带可缩放的**悬浮地图窗**；
每个区域都有「念给玩家 / 运行脚本 / 怪物血量跳转 / 可交互物件 / 陷阱 / 宝藏 / 台词 / 伏笔」。

**核心思想**：手册不是"把 PDF 抄一遍"，而是**帮 DM 现场少翻书**——翻到某个区域，
第一眼看到的就是"这一场该怎么带"。

## 何时使用

- 用户有模组 PDF，说"跑团准备 / DM 速查 / 整理模组 / 做 DM 指南 / DM screen"
- 想把一章或一个副本做成**逐区域速查**
- 需要念白话术、怪物 HP 一览、地图、NPC 谈判话术、陷阱清单

## 工作流

1. **抽 PDF**
   ```bash
   python scripts/extract_module_pdf.py 模组.pdf
   ```
   得到 `pages.txt`（每页带 `===== PAGE n =====`）、`toc.txt`、`maps/pXX_0.png`（地图多半是整页大图）。

2. **定位章节**：用 `toc.txt` 找页码，再在 `pages.txt` 里 grep 章节标题，确定每个区域的文字范围。
   —— 中译 PDF 常有兼容字形（⼤ ⼀ ⻔），整理时用 `unicodedata.normalize('NFKC', text)` 归一化。

3. **写数据包**：照着 `examples/example_data.py` 写一个 `<campaign>_data.py`。
   字段 → `reference/data-schema.md`；内容怎么写 → `reference/content-principles.md`。

4. **生成**
   ```bash
   python scripts/build_guide.py my_data.py -o "DM速查.html"
   ```

5. **自检**：用无头浏览器截图抽查排版有没有溢出。
   ```bash
   chrome --headless=new --screenshot=out.png --window-size=1400,1500 "file:///.../DM速查.html"
   ```

## 关键原则

- **念白只放"读给玩家"的话**；DM 信息 / 战术另起块，别混在一起。
- **每个区域都要有「🎬 DM 运行脚本」**：怎么开场、按什么顺序、检定怎么报、话术、坑。
- **怪物用短 key + 图鉴**：区域里只写 `monsters`，点一下就跳到资料板。
- **地图内嵌 base64**：单文件离线可用；另给一个可缩放 / 半屏 / 最小化的悬浮窗。
- **别把 DM 内容混进玩家讲义**：玩家侧另出一份 Markdown（可粘进 VTT 的 handout）。

## 常见错误

| 错误 | 后果 |
|---|---|
| 直接把 PDF 文本大段粘进去 | 现场还是找不到重点 |
| 区域没有"运行脚本" | 只知道"有什么"，不知道"怎么带" |
| 怪物 HP 散落在正文 | 每次开团都要翻资料板 |
| 把 DM 内容写进玩家讲义 | 剧透，毁掉惊喜 |
| 地图用外链文件 | 离网 / 发给别人就裂图 |

## 参考

- `reference/data-schema.md` —— 数据包全部字段
- `reference/content-principles.md` —— 每块内容怎么写（含示例）
- `examples/example_data.py` —— 最小可运行示例
