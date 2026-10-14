#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_guide.py — 把一份「战役数据包」渲染成单文件 HTML 的 DM 速查手册。

用法:
    python build_guide.py <data_module.py> [-o 输出.html]

数据包是普通 Python 模块（见 reference/data-schema.md）。必需: TITLE, CHAPTERS。
输出：自包含 HTML（地图内嵌 base64），离线可开、可打印。
"""
import sys, os, io, html, base64, argparse, importlib.util

try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False


def esc(s):
    return html.escape(str(s), quote=False)


def load_data(path):
    path = os.path.abspath(path)
    spec = importlib.util.spec_from_file_location("guide_data", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.__data_dir__ = os.path.dirname(path)
    return mod


def build_map_data(maps, base_dir):
    """把地图图片读进来、压成 JPEG、转 base64 内嵌。"""
    out = {}
    for m in maps:
        src = m.get("src", "")
        if not src:
            continue
        p = src if os.path.isabs(src) else os.path.join(base_dir, src)
        if not os.path.exists(p):
            print(f"  ! 地图缺失，跳过: {p}")
            continue
        if HAS_PIL:
            im = Image.open(p).convert("RGB")
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=85, optimize=True, progressive=True)
            b = buf.getvalue()
            w, h = im.width, im.height
        else:
            with open(p, "rb") as f:
                b = f.read()
            w, h = 1000, 700
        out[m["key"]] = {"uri": "data:image/jpeg;base64," + base64.b64encode(b).decode(),
                         "w": w, "h": h}
    return out


# ================================================================== 渲染工具
def blocks(items, cls, label, icon):
    if not items:
        return ""
    lis = "".join(f"<li>{esc(x)}</li>" for x in items)
    return f'<div class="blk {cls}"><div class="blk-t">{icon} {esc(label)}</div><ul>{lis}</ul></div>'


def readbox(text, tag="读给玩家"):
    if not text:
        return ""
    return f'<div class="read"><span class="read-tag">📖 {esc(tag)}</span><p>{esc(text)}</p></div>'


def chips(monsters, mby):
    if not monsters:
        return ""
    out = []
    for item in monsters:
        if isinstance(item, (list, tuple)):
            key, label = item[0], (item[1] if len(item) > 1 else "")
        else:
            key, label = item, ""
        m = mby.get(key)
        if not m:
            continue
        out.append(f'<a class="chip" href="#mon-{key}">{esc(m["name"])} · HP {m.get("hpnum","?")}'
                   f' <span class="chip-note">{esc(label)}</span></a>')
    return '<div class="chips">🐺 怪物：' + "".join(out) + "</div>"


def area_card(ch, a, i, mby):
    aid = f'{ch["id"]}-{i+1}'
    objs, hooks, script = a.get("objects"), a.get("hook"), a.get("script")
    body = [readbox(a.get("read"))]
    body.append(blocks(script, "script", "DM 运行脚本（现场怎么带）", "🎬"))
    body.append(blocks(a.get("info"), "info", "DM 信息", "🎯"))
    body.append(blocks(a.get("info2"), "info", "补充信息", "📌"))
    body.append(blocks(a.get("trap"), "trap", "陷阱 / 机关", "⚠️"))
    if a.get("read2"):
        body.append(readbox(a["read2"], "读给玩家（继续）"))
    body.append(blocks(a.get("tactics"), "tactics", "战术 / 处理", "🧠"))
    body.append(blocks(objs, "objects", "可交互物件 / 可调查", "🗿"))
    body.append(blocks(hooks, "hook", "后续伏笔插入点", "🧩"))
    body.append(blocks(a.get("foreshadow"), "fore", "伏笔", "💡"))
    body.append(blocks(a.get("treasure"), "treasure", "宝藏", "💎"))
    body.append(blocks(a.get("dev"), "dev", "发展", "🔀"))
    body.append(blocks(a.get("senses"), "senses", "可以这样描述", "👁️"))
    if a.get("say"):
        rows = "".join(f'<div class="say-row"><span class="say-who">{esc(w)}</span>'
                       f'<span class="say-line">{esc(l)}</span></div>' for w, l in a["say"])
        body.append(f'<div class="blk say"><div class="blk-t">🗣️ 台词</div>{rows}</div>')
    body.append(chips(a.get("monsters"), mby))
    xp = f'<span class="xp-badge">⭐ {esc(a["xp"])}</span>' if a.get("xp") else ""
    search = esc((str(a.get("name", "")) + " " + str(a.get("read", "")) + " " + " ".join(
        (a.get("info") or []) + (a.get("tactics") or []) + (a.get("trap") or []) +
        (a.get("treasure") or []) + (objs or []) + (hooks or []) + (script or []))).lower())
    return f'''<article class="card area" id="{aid}" data-search="{search}">
  <header class="card-h">
    <span class="badge">区域 {esc(a["no"])}</span>
    <h3>{esc(a["name"])} <span class="en">{esc(a.get("en",""))}</span></h3>
    {xp}
  </header>
  <div class="card-b">{''.join(body)}</div>
</article>'''


def chapter_block(ch, map_key, maps, mby):
    feats = "".join(f'<div class="feat"><b>{esc(k)}</b><span>{esc(v)}</span></div>'
                    for k, v in ch.get("features", []))
    intro = "".join(f"<p>{esc(p)}</p>" for p in ch.get("intro", []))
    sit = "".join(f"<li>{esc(p)}</li>" for p in ch.get("situation", []))
    amb = ""
    if ch.get("ambience"):
        amb = ('<div class="blk amb"><div class="blk-t">🌊 招牌氛围</div>' +
               "".join(f"<p>{esc(p)}</p>" for p in ch["ambience"]) + "</div>")
    wander = ""
    if ch.get("wander"):
        wd = ch["wander"]
        rows = "".join(f'<tr><td class="mono">{esc(k)}</td><td>{esc(v)}</td></tr>' for k, v in wd["table"])
        wander = (f'<div class="panel"><h4>🎲 {esc(wd["title"])}</h4><p>{esc(wd.get("trigger",""))}</p>'
                  f'<table class="tbl"><thead><tr><th>d</th><th>结果</th></tr></thead><tbody>{rows}</tbody></table>'
                  f'<p class="tip">{esc(wd.get("tip",""))}</p></div>')
    slim = ""
    m = maps.get(map_key)
    if m:
        chipsel = "".join(f'<a class="mchip" href="#{ch["id"]}-{i+1}">{a["no"]}</a>'
                          for i, a in enumerate(ch.get("areas", [])))
        slim = (f'<div class="mapslim"><span class="ms-title">🗺️ {esc(m["title"])}　'
                f'<span class="ms-scale">{esc(m.get("scale",""))}</span></span>'
                f'<div class="mchips">{chipsel}</div>'
                f'<button class="btn" data-map-open="{map_key}">打开地图悬浮窗</button></div>')
    extras = ""
    for e in ch.get("extras", []) or []:
        bl = "".join(f"<p>{esc(x)}</p>" for x in e.get("body", []))
        xp = f'<span class="xp-badge">⭐ {esc(e["xp"])}</span>' if e.get("xp") else ""
        obl = blocks(e.get("objects"), "objects", "可交互物件 / 可调查", "🗿") if e.get("objects") else ""
        extras += f'<div class="panel extra"><h4>{esc(e["title"])} {xp}</h4>{bl}{obl}</div>'
    areas = "".join(area_card(ch, a, i, mby) for i, a in enumerate(ch.get("areas", [])))
    return f'''<section id="{ch["id"]}" class="chapter">
  <div class="chapter-head">
    <h2>{esc(ch["title"])} <span class="en">{esc(ch.get("en",""))}</span></h2>
    <span class="page-ref">{esc(ch.get("page",""))}</span>
  </div>
  {slim}
  <div class="panel overview"><h4>概览</h4>{intro}
    <div class="blk points"><div class="blk-t">🎯 局势</div><ul>{sit}</ul></div>
    {amb}
    <h4>通用特征</h4><div class="feats">{feats}</div>
  </div>
  {wander}
  <div class="areas">{areas}</div>
  {extras}
</section>'''


def monster_card(m):
    tr = blocks(m.get("traits"), "dev", "特质", "")
    ac = blocks(m.get("actions"), "trap", "动作", "")
    ex = blocks(m.get("extra"), "info", "其它", "")
    return f'''<article class="card monster" id="mon-{m["key"]}">
  <header class="card-h"><h3>{esc(m["name"])} <span class="en">{esc(m.get("en",""))}</span></h3><span class="hp">HP {m.get("hpnum","?")}</span></header>
  <div class="card-b">
    <p class="meta">{esc(m.get("meta",""))}</p>
    <div class="stats3"><span><b>AC</b> {esc(m.get("ac",""))}</span><span><b>HP</b> {esc(m.get("hp",""))}</span><span><b>速度</b> {esc(m.get("speed",""))}</span></div>
    <p class="ab">{esc(m.get("ab",""))}</p>{ex}{tr}{ac}
    <p class="note">🎲 {esc(m.get("note",""))}</p>
  </div>
</article>'''


def item_card(it):
    return (f'<article class="card item"><header class="card-h"><h3>{esc(it["name"])} '
            f'<span class="en">{esc(it.get("en",""))}</span></h3></header>'
            f'<div class="card-b"><p class="find">📍 {esc(it.get("find",""))}</p>'
            f'<p>{esc(it.get("text",""))}</p></div></article>')


def npc_card(n, mby):
    resp = "".join(f'<tr><td class="atk">{esc(a)}</td><td>{esc(b)}</td></tr>' for a, b in n.get("responses", []))
    lines = "".join(f"<li>{esc(x)}</li>" for x in n.get("lines", []))
    open_ = "".join(f'<div class="npc-line">{esc(x)}</div>' for x in n.get("open", []))
    m = mby.get(n.get("monster"))
    chip = (f'<a class="chip" href="#mon-{m["key"]}">{esc(m["name"])} · HP {m.get("hpnum","?")}</a>'
            if m else "")
    return f'''<article class="card npc" data-search="{esc((n["name"]+" "+n.get("voice","")+" "+n.get("wants","")).lower())}">
  <header class="card-h"><h3>{esc(n["name"])} <span class="en">{esc(n.get("en",""))}</span></h3>
    <span class="where">{esc(n.get("where",""))}</span></header>
  <div class="card-b">
    <p class="meta">{esc(n.get("role",""))}　{chip}</p>
    <div class="npc-grid">
      <div class="ng"><b>🎭 语气 / 举止</b><span>{esc(n.get("voice",""))}</span></div>
      <div class="ng"><b>🎯 想要什么</b><span>{esc(n.get("wants",""))}</span></div>
      <div class="ng"><b>🛑 底线 / 怕什么</b><span>{esc(n.get("fears",""))}</span></div>
    </div>
    <div class="blk say"><div class="blk-t">🗣️ 开场白（照着念）</div>{open_}</div>
    {blocks(n.get("lines"), "tactics", "其它台词", "💬")}
    <div class="blk info"><div class="blk-t">🤝 谈判应对（玩家怎么做 → NPC 如何反应）</div>
      <table class="tbl npctbl"><tbody>{resp}</tbody></table></div>
    <div class="npc-foot">
      <div class="nf"><b>🔍 识破 / 欺瞒</b><span>{esc(n.get("deception",""))}</span></div>
      <div class="nf nf-red"><b>💥 翻脸条件</b><span>{esc(n.get("break",""))}</span></div>
      <div class="nf nf-gold"><b>🤝 可谈成的交易</b><span>{esc(n.get("deal",""))}</span></div>
    </div>
  </div>
</article>'''


def quest_card(q):
    how = "".join(f"<li>{esc(x)}</li>" for x in q.get("how", []))
    return f'''<div class="quest">
  <div class="q-head"><span class="q-tag">{esc(q.get("tag",""))}</span><h4>{esc(q["title"])}</h4></div>
  <div class="q-when">📍 什么时候/在哪加：{esc(q.get("when",""))}</div>
  {readbox(q.get("read",""))}
  <div class="blk tactics"><div class="blk-t">🧠 怎么跑</div><ul>{how}</ul></div>
  <div class="q-foot">
    <div class="nf nf-gold"><b>🎯 后面怎么回收</b><span>{esc(q.get("payoff",""))}</span></div>
    <div class="nf"><b>🎁 奖励</b><span>{esc(q.get("reward",""))}</span></div>
    <div class="nf"><b>📚 出处</b><span>{esc(q.get("pages",""))}</span></div>
  </div>
</div>'''


# ================================================================== 章节化小板块
def xp_section(xt):
    out = []
    for _, t in (xt or {}).items():
        rows = "".join(f'<tr><td>{esc(a)}</td><td class="mono">{esc(b)}</td></tr>' for a, b in t["rows"])
        out.append(f'<div class="panel"><h4>{esc(t["title"])}</h4><table class="tbl"><tbody>{rows}</tbody>'
                   f'</table><p class="total">{esc(t.get("total",""))}</p></div>')
    return "".join(out)


def traps_section(tr):
    rows = "".join(f'<tr><td>{esc(t["where"])}</td><td>{esc(t.get("find",""))}</td>'
                   f'<td>{esc(t.get("effect",""))}</td><td class="tip">{esc(t.get("note",""))}</td></tr>' for t in tr)
    return ('<table class="tbl wide"><thead><tr><th>位置</th><th>如何察觉</th><th>效果</th><th>备注</th>'
            f'</tr></thead><tbody>{rows}</tbody></table>')


def fore_section(fs):
    return "".join(f'<div class="panel fore-panel"><h4>💡 {esc(f["title"])}</h4><p>{esc(f["text"])}</p></div>'
                   for f in fs)


def dialogue_section(dl):
    return "".join(f'<div class="say-row big"><span class="say-who">{esc(d["who"])}</span>'
                   f'<span class="say-line">{esc(d["line"])}</span>'
                   f'<span class="say-when">{esc(d.get("when",""))}</span></div>' for d in dl)


def senses_section(sn):
    return "".join(f'<div class="panel"><h4>{esc(k)}</h4><p class="sense-words">{esc(" · ".join(v))}</p></div>'
                   for k, v in (sn or {}).items())


def hooks_section(ov, pre_quests, bridge):
    if not ov:
        return ""
    books = "".join(f'<tr><td class="mono">{esc(a)}</td><td class="mono">{esc(b)}</td><td>{esc(c)}</td></tr>'
                    for a, b, c in ov.get("books", []))
    chk = "".join(f"<li>{esc(x)}</li>" for x in ov.get("checklist", []))
    quests = "".join(quest_card(q) for q in (pre_quests or []))
    return f'''<div class="panel overview">
  <h4>🗺️ 后续走向（知道终点，才知道该埋什么）</h4>
  <p>{esc(ov.get("lede",""))}</p>
  <table class="tbl"><thead><tr><th>章节</th><th>等级</th><th>这一章发生什么</th></tr></thead><tbody>{books}</tbody></table>
  <p class="tip">💡 {esc(ov.get("mindset",""))}</p>
  <h4>✅ 调整清单</h4><ol class="rules-list">{chk}</ol>
</div>
{f'<div class="sec-sub">🧩 开跑前的小支线</div>{quests}' if quests else ''}'''


def bridge_section(b):
    if not b:
        return ""
    steps = "".join(f"<li>{esc(x)}</li>" for x in b.get("steps", []))
    corr = "".join(f'<tr><td class="mono">{esc(a)}</td><td>{esc(c)}</td></tr>' for a, c in b.get("corruption", []))
    corr_tbl = (f'<h4>🌫️ 腐化 / 推进 · 每章叠加一句</h4><table class="tbl"><thead><tr><th>章节</th>'
                f'<th>描述</th></tr></thead><tbody>{corr}</tbody></table>' if corr else "")
    warn = blocks([b["warning"]], "trap", "务必先征得同意", "⚠️") if b.get("warning") else ""
    return f'{readbox(b.get("read",""), b.get("read_tag","念给玩家"))}' \
           f'{blocks(b.get("steps"), "tactics", "衔接步骤", "➡️")}{corr_tbl}{warn}'


# ================================================================== 侧边导航
def nav(chapters, maps):
    out = []
    for g in chapters:
        sub = "".join(f'<a href="#{g["id"]}-{i+1}">{a["no"]}. {esc(a["name"])}</a>'
                      for i, a in enumerate(g.get("areas", [])))
        out.append(f'<div class="nav-group"><a class="nav-top" href="#{g["id"]}">'
                   f'{esc(g.get("nav","📖 "+g["title"]))}</a><div class="nav-sub">{sub}</div></div>')
    extra = ['<div class="nav-group"><a class="nav-top" href="#bestiary">🐺 怪物图鉴</a></div>',
             '<div class="nav-group"><a class="nav-top" href="#items">💎 魔法物品</a></div>',
             '<div class="nav-group"><a class="nav-top" href="#npc">🗣️ NPC 台词与谈判</a></div>',
             '<div class="nav-group"><a class="nav-top" href="#xp">⭐ 经验表</a></div>',
             '<div class="nav-group"><a class="nav-top" href="#traps">⚠️ 陷阱速查</a></div>',
             '<div class="nav-group"><a class="nav-top" href="#foreshadow">💡 伏笔与剧情线</a></div>',
             '<div class="nav-group"><a class="nav-top" href="#dialogue">🗣️ 台词速查</a></div>',
             '<div class="nav-group"><a class="nav-top" href="#senses">👁️ 描述词库</a></div>',
             '<div class="nav-group"><a class="nav-top" href="#tips">🎯 主持提示</a></div>',
             '<div class="nav-group"><a class="nav-top" href="#tracker">⚔️ 先攻 / HP 追踪</a></div>']
    return "".join(out) + "".join(extra)


def maps_section(MAPS, MAPDATA):
    out = []
    for m in MAPS:
        d = MAPDATA.get(m["key"])
        if not d:
            continue
        out.append(f'''<figure class="mapfig" id="map-{m["key"]}">
  <figcaption><b>{esc(m["title"])}</b> <span class="en">{esc(m.get("en",""))}</span>
    <span class="scale">{esc(m.get("scale",""))}</span>
    <button class="btn" data-map-open="{m["key"]}">在悬浮窗打开</button></figcaption>
  <img src="{d["uri"]}" alt="{esc(m["title"])}" data-map-open="{m["key"]}" loading="lazy">
  <p class="tip">{esc(m.get("note",""))}</p></figure>''')
    return "".join(out)


def mapwin_html(MAPS):
    tabs = "".join(f'<button data-map="{m["key"]}">{esc(m["title"])}</button>' for m in MAPS)
    return f'''
<div id="mapWin" class="hide">
  <div class="mw-bar" id="mwBar">
    <span class="mw-grip">⠿</span><span class="mw-title" id="mwTitle">地图</span>
    <div class="mw-tabs">{tabs}</div><span class="mw-spacer"></span>
    <button class="mw-btn" id="mwOut">－</button><button class="mw-btn" id="mwIn">＋</button>
    <button class="mw-btn" id="mwFit">适应</button><button class="mw-btn" id="mwHalf">◱ 半屏</button>
    <button class="mw-btn" id="mwFull">⛶</button><button class="mw-btn" id="mwMin">—</button>
    <button class="mw-btn" id="mwClose">✕</button>
  </div>
  <div class="mw-body" id="mwBody"><img id="mwImg" alt="地图">
    <span class="mw-hint">滚轮缩放 · 拖拽平移 · 拖标题栏移动 · 右下角缩放</span></div>
  <div class="mw-resize" id="mwResize"></div>
</div>'''


# ================================================================== CSS / JS
def _load_asset(name):
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    p = os.path.join(base, name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return ""


CSS = _load_asset("guide.css")
JS = _load_asset("guide.js")


def build(data, out_path):
    chapters = getattr(data, "CHAPTERS", [])
    MAPS = getattr(data, "MAPS", [])
    base = getattr(data, "__data_dir__", ".")
    MAPDATA = build_map_data(MAPS, base)
    MAP_BY = {m["key"]: m for m in MAPS if m["key"] in MAPDATA}
    MONSTERS = getattr(data, "MONSTERS", [])
    mby = {m["key"]: m for m in MONSTERS}
    ITEMS = getattr(data, "ITEMS", [])
    NPCS = getattr(data, "NPCS", [])
    TITLE = getattr(data, "TITLE", "DM 速查")
    SUBTITLE = getattr(data, "SUBTITLE", "")
    SCOPE = getattr(data, "SCOPE", "")
    VERSION = getattr(data, "VERSION", "")

    def ch_map_key(ch):
        for k in ch.get("maps", []) or []:
            if k in MAP_BY:
                return k
        return ch.get("map")

    body_chapters = "".join(chapter_block(ch, ch_map_key(ch), MAP_BY, mby) for ch in chapters)

    sec = []
    qs = getattr(data, "QUICKSTART", None)
    if qs:
        cards = "".join(f'<div class="qs-card"><h4>{esc(c["h"])}</h4><p>{esc(c["b"])}</p></div>' for c in qs)
        sec.append(f'<section id="quickstart"><h2>⚡ 开跑前 30 秒速查</h2><div class="qs">{cards}</div></section>')
    howto = getattr(data, "HOWTO", None)
    if howto:
        lis = "".join(f"<li>{esc(x)}</li>" for x in howto)
        sec.append(f'<section id="howto"><h2>🧭 线索链 / 如何找到这里</h2>'
                   f'<div class="panel"><ul class="bullets">{lis}</ul></div></section>')
    HOOKS = getattr(data, "HOOKS", None)
    if HOOKS:
        sec.append(f'<section id="hooks"><h2>🧩 承上启下 · 埋线 &amp; 小支线</h2>'
                   f'{hooks_section(HOOKS.get("overview"), HOOKS.get("pre_quests"), HOOKS.get("bridge"))}</section>')
    if MAPS and MAPDATA:
        sec.append(f'<section id="maps"><h2>🗺️ 大地图</h2>'
                   f'<p class="tip">点任意地图 → 在右下角<b>悬浮窗</b>打开；可拖动、可缩放、可半屏/全屏/最小化。</p>'
                   f'{maps_section(MAPS, MAPDATA)}</section>')
    sec.append(body_chapters)
    BRIDGE = HOOKS.get("bridge") if HOOKS else None
    if BRIDGE:
        sec.append(f'<section id="bridge"><h2>➡️ 结束之后 · 衔接下一章</h2>{bridge_section(BRIDGE)}</section>')
    if NPCS:
        rules = getattr(data, "NPC_RULES", None)
        rl = ""
        if rules:
            lis = "".join(f"<li>{esc(x)}</li>" for x in rules.get("items", []))
            rl = f'<div class="panel rules"><h4>📏 {esc(rules.get("title","谈判通用法则"))}</h4><ol class="rules-list">{lis}</ol></div>'
        sec.append(f'<section id="npc"><h2>🗣️ 主要 NPC 台词与谈判手册</h2>{rl}'
                   f'{"".join(npc_card(n, mby) for n in NPCS)}</section>')
    if MONSTERS:
        sec.append(f'<section id="bestiary"><h2>🐺 怪物图鉴</h2>'
                   f'{"".join(monster_card(m) for m in MONSTERS)}</section>')
    if ITEMS:
        sec.append(f'<section id="items"><h2>💎 魔法物品与战利品</h2>'
                   f'{"".join(item_card(it) for it in ITEMS)}</section>')
    if getattr(data, "XP_TABLE", None):
        sec.append(f'<section id="xp"><h2>⭐ 经验分配速查</h2>{xp_section(data.XP_TABLE)}</section>')
    if getattr(data, "TRAPS", None):
        sec.append(f'<section id="traps"><h2>⚠️ 陷阱与机关速查</h2>{traps_section(data.TRAPS)}</section>')
    if getattr(data, "FORESHADOW", None):
        sec.append(f'<section id="foreshadow"><h2>💡 伏笔与剧情线</h2>{fore_section(data.FORESHADOW)}</section>')
    if getattr(data, "DIALOGUE", None):
        sec.append(f'<section id="dialogue"><h2>🗣️ 台词速查</h2>'
                   f'<div class="panel">{dialogue_section(data.DIALOGUE)}</div></section>')
    if getattr(data, "SENSES", None):
        sec.append(f'<section id="senses"><h2>👁️ 描述词库</h2><div class="qs">{senses_section(data.SENSES)}</div></section>')
    if getattr(data, "TIPS", None):
        lis = "".join(f"<li>{esc(x)}</li>" for x in data.TIPS)
        sec.append(f'<section id="tips"><h2>🎯 主持提示</h2><div class="panel"><ul class="bullets">{lis}</ul></div></section>')
    sec.append('''<section id="tracker"><h2>⚔️ 先攻 / HP 追踪（离线用，存在本机）</h2>
      <div class="panel"><div class="tk-add">
        <input id="tkName" placeholder="名字（如 地精A）" style="width:180px">
        <input id="tkInit" class="init-in" placeholder="先攻" type="number">
        <input id="tkHp" class="hp-in" placeholder="HP" type="number">
        <button id="tkAdd">加入 / 排序</button></div><div id="tkList"></div></div></section>''')

    maps_json = "{" + ",".join(
        f'"{k}":{{"uri":"{v["uri"]}","w":{v["w"]},"h":{v["h"]},'
        f'"title":"{esc(MAP_BY[k]["title"])}","scale":"{esc(MAP_BY[k].get("scale",""))}"}}'
        for k, v in MAPDATA.items()) + "}"
    js = JS.replace("__MAPS_JSON__", maps_json)
    ver = f'<span class="ver">{esc(VERSION)}</span>' if VERSION else ""
    html_doc = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TITLE)} · {esc(SUBTITLE)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="top">
  <div>
    <h1>🎲 {esc(TITLE)}</h1>
    <div class="sub">{esc(SUBTITLE)}{(' · ' + esc(SCOPE)) if SCOPE else ''} {ver}</div>
  </div>
  <div class="spacer"></div>
  <div class="tools">
    <input id="q" placeholder="🔍 搜索…" autocomplete="off">
    <div class="dice">
      <button data-die="4">d4</button><button data-die="6">d6</button><button data-die="8">d8</button>
      <button data-die="10">d10</button><button data-die="12">d12</button><button data-die="20">d20</button>
      <button data-die="100">d100</button></div>
    <span id="diceOut">—</span>
    <button class="btn" id="printBtn">🖨️ 打印</button>
  </div>
</header>
<div class="layout">
  <aside class="side"><nav>{nav(chapters, MAP_BY)}</nav></aside>
  <main>{''.join(sec)}
    <footer>由 dnd-dm-guide-builder 生成 · 单文件离线可用（地图已内嵌）</footer>
  </main>
</div>
<button id="fab">🗺️ 地图</button>
<button id="toTop" title="回到顶部">↑</button>
{mapwin_html(MAPS)}
<script>{js}</script>
</body>
</html>'''
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", help="数据模块 .py 路径")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()
    data = load_data(args.data)
    out = args.out or os.path.splitext(os.path.basename(args.data))[0] + ".html"
    build(data, out)
    print(f"OK -> {out} ({os.path.getsize(out)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
