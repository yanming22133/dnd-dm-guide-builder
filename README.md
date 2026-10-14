# dnd-dm-guide-builder 🎲

An Agent **Skill** that turns a tabletop RPG module PDF (D&D 5e, Pathfinder, Call of Cthulhu…) into a
**single-file HTML DM quick-reference** — offline, printable, with a floating map window and, for every
area: read-aloud text, a **running script** (how to actually run the scene), monster HP lookups, interactive
objects, traps, treasure, dialogue and foreshadowing.

> 把一个跑团模组的 PDF，变成**单文件 HTML 的 DM 速查手册**。

```
PDF  ──extract──▶  pages.txt + maps/*.png  ──write──▶  data.py  ──build──▶  DM速查.html
```

## Why

A DM running a module spends the whole session flipping through a PDF. This skill produces the thing you
actually want at the table: flip to an area, and the first thing you see is *how to run it*.

## Installation

Copy the skill folder into your runtime's skills directory:

```bash
# Claude Code / opencode style runtimes
cp -r dnd-dm-guide-builder ~/.claude/skills/      # or ~/.agents/skills/
```

Then install the Python deps:

```bash
pip install -r requirements.txt      # pymupdf, pillow
```

## Usage

```bash
# 1) extract text + map images from the module PDF
python scripts/extract_module_pdf.py 模组.pdf
#    -> 模组_extract/pages.txt, toc.txt, maps/pXX_0.png

# 2) write a data package (copy and edit the example)
cp examples/example_data.py my_campaign_data.py

# 3) render
python scripts/build_guide.py my_campaign_data.py -o "DM速查.html"
```

Open the HTML in any browser. It contains:

| Feature | |
|---|---|
| 🎬 **DM 运行脚本** | per-area "how to run this scene": opening beat, order of operations, which check, what to say, gotchas |
| 📖 **念给玩家** | the module's boxed read-aloud text |
| 🐺 **怪物图鉴** | stat blocks; area chips link straight to them |
| 🗺️ **悬浮地图窗** | draggable, resizable, half-screen / full-screen / minimizable; maps embedded as base64 |
| 🗿 **可交互物件** | everything the party can touch/search, with the check or consequence |
| 🗣️ **NPC 谈判手册** | voice, wants, bottom line, opener lines, and a "what the players do → how the NPC reacts" table |
| ⚠️ 陷阱 · 💎 宝藏 · 💡 伏笔 · 👁️ 描述词 | plus an XP table, trap index and dialogue list |
| 🖨️ **print CSS** | turns into a clean paper cheat sheet |
| ⚔️ **initiative / HP tracker** | saved in the browser (offline) |

## Files

```
dnd-dm-guide-builder/
├── SKILL.md                       # skill entry point (agent instructions)
├── scripts/
│   ├── build_guide.py             # data package -> single-file HTML
│   ├── extract_module_pdf.py      # PDF -> text + map images
│   └── assets/guide.css, guide.js
├── reference/
│   ├── data-schema.md             # every field of the data package
│   └── content-principles.md      # how to write each block well (with a full example)
├── examples/example_data.py       # minimal runnable data package
└── requirements.txt
```

## Design principles

- **Read-aloud ≠ DM info.** Keep them in separate blocks, never mixed.
- **Every area needs a running script.** "What's here" is not "how to run it".
- **Numbers complete.** DC, dice, gold, HP, distance — there's no time to compute at the table.
- **Spoiler safety.** The DM guide is never handed to players; produce a separate player Markdown handout.

## License

MIT
