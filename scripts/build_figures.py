"""生成 guide 里的内联 SVG 配图。

图内联在 Markdown 里，站点构建时原样带进 HTML，因此这里直接输出 SVG 片段，
不生成独立的 HTML 文件。

配色取自文档站自己的 ``docs/intro.css``：暖纸底色、青绿主色、clay 表示
失败或删除、moss 表示保留。字体用站点同款字族，SVG 里的标签不引入网络字体。

用法::

    uv run python scripts/build_figures.py

用法约定：坐标一律落在 4px 网格上；连接器只走直角，弯角半径 8；标签有
不透明底衬，且与连接线之间留出可见间隙。

图和正文的接口是成对的 HTML 注释::

    <!-- figure:slug:start -->
    <!-- figure:slug:end -->

脚本会把这一对注释之间的内容整段替换成最新的图，因此可以反复运行。
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDES = {
    REPO_ROOT / "docs" / "guide.md": "zh",
    REPO_ROOT / "docs" / "guide.en.md": "en",
}

# 文档站的设计令牌，与 docs/intro.css 一致。
PAPER = "#f6f1e8"
PAPER_2 = "#fffdf8"
INK = "#1c1915"
MUTED = "#5e584e"
SOFT = "#6f685c"
RULE = "rgba(28,25,21,0.12)"
RULE_SOLID = "#d8d0c1"
TEAL = "#1b4744"
TEAL_SOFT = "rgba(27,71,68,0.08)"
CLAY = "#9a3412"
CLAY_SOFT = "rgba(154,52,18,0.08)"
MOSS = "#1d6842"
MOSS_SOFT = "rgba(29,104,66,0.08)"

SANS = "'Avenir Next', 'PingFang SC', 'Noto Sans SC', 'Segoe UI', sans-serif"
SERIF = "'Iowan Old Style', Palatino, 'Songti SC', 'Noto Serif SC', serif"
MONO = "'IBM Plex Mono', 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace"

FIGURE_NO = {
    "concepts": 1,
    "stage": 2,
    "rerun": 3,
    "layout": 4,
    "operators": 5,
    "variables": 6,
    "hashes": 7,
    "pipeline": 8,
}


def T(zh: str, en: str, lang: str) -> str:
    """按语言取一份文案。"""
    return zh if lang == "zh" else en


def esc(text: str) -> str:
    """转义 SVG 文本里的尖括号，否则浏览器会把它当成 HTML 标签。"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_TEXT_NODE = re.compile(r"(<(?:text|title|desc)\b[^>]*>)(.*?)(</(?:text|title|desc)>)", re.S)


def escape_text_nodes(content: str) -> str:
    """把 SVG 里所有文本节点的内容转义一遍。

    ``<输出根目录>/`` 这样的名字如果不转义，浏览器会把它当成一个 HTML 标签，
    整段文字就没了。这里统一在文本节点上做一次处理。
    """

    def repl(match: re.Match[str]) -> str:
        return match.group(1) + esc(match.group(2)) + match.group(3)

    return _TEXT_NODE.sub(repl, content)


# --------------------------------------------------------------------------
# 低层绘制
# --------------------------------------------------------------------------


def text_width(text: str, size: float) -> float:
    """估算一段文字的宽度。中日韩字符按全角算，其余按半角算。"""
    width = 0.0
    for ch in text:
        width += size * (1.0 if ord(ch) > 0x2E80 else 0.55)
    return width


def svg(slug: str, title: str, desc: str, width: int, height: int, content: str) -> str:
    """完整的 SVG 外壳，带可访问性契约。``<title>`` 必须是第一个子元素。"""
    return (
        f'<svg role="img" aria-labelledby="{slug}-title {slug}-desc" '
        f'viewBox="0 0 {width} {height}" width="100%" '
        f'style="max-width:{width}px">\n'
        f'  <title id="{slug}-title">{esc(title)}</title>\n'
        f'  <desc>{esc(desc)}</desc>\n'
        f"  <defs>\n"
        f'    <marker id="{slug}-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" '
        f'orient="auto">\n'
        f'      <polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/>\n'
        f"    </marker>\n"
        f'    <marker id="{slug}-arrow-teal" markerWidth="8" markerHeight="6" refX="7" refY="3" '
        f'orient="auto">\n'
        f'      <polygon points="0 0, 8 3, 0 6" fill="{TEAL}"/>\n'
        f"    </marker>\n"
        f'    <marker id="{slug}-arrow-moss" markerWidth="8" markerHeight="6" refX="7" refY="3" '
        f'orient="auto">\n'
        f'      <polygon points="0 0, 8 3, 0 6" fill="{MOSS}"/>\n'
        f"    </marker>\n"
        f"  </defs>\n"
        f'  <rect width="{width}" height="{height}" fill="{PAPER}"/>\n'
        f"{escape_text_nodes(content)}\n"
        f"</svg>"
    )


def node(
    x: int,
    y: int,
    w: int,
    h: int,
    name: str,
    sublabel: str = "",
    *,
    fill: str = PAPER_2,
    stroke: str = INK,
    name_color: str = INK,
    name_size: int = 13,
    sub_size: int = 10,
    stroke_width: int = 1,
    radius: int = 6,
    tag: str = "",
    tag_stroke: str = "",
    name_family: str = SANS,
    dashed: bool = False,
) -> str:
    """一个节点框。纸底衬 + 描边框 + 名字 + 副标签。"""
    dash = ' stroke-dasharray="4,3"' if dashed else ""
    parts = [
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{PAPER}"/>',
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash}/>',
    ]
    if tag:
        tag_w = text_width(tag, 8) + 12
        parts.append(
            f'  <rect x="{x + 8}" y="{y + 7}" width="{tag_w:g}" height="14" rx="2" '
            f'fill="transparent" stroke="{tag_stroke or stroke}" stroke-width="0.8" '
            f'stroke-opacity="0.5"/>'
        )
        parts.append(
            f'  <text x="{x + 8 + tag_w / 2:g}" y="{y + 17}" fill="{tag_stroke or stroke}" '
            f'font-size="8" font-family="{SANS}" text-anchor="middle" '
            f'letter-spacing="0.08em" fill-opacity="0.85">{tag}</text>'
        )
    center = x + w / 2
    if sublabel:
        parts.append(
            f'  <text x="{center:g}" y="{y + h / 2 - 2:g}" fill="{name_color}" '
            f'font-size="{name_size}" font-weight="600" font-family="{name_family}" '
            f'text-anchor="middle">{name}</text>'
        )
        parts.append(
            f'  <text x="{center:g}" y="{y + h / 2 + 15:g}" fill="{MUTED}" '
            f'font-size="{sub_size}" font-family="{MONO}" '
            f'text-anchor="middle">{sublabel}</text>'
        )
    else:
        parts.append(
            f'  <text x="{center:g}" y="{y + h / 2 + 4:g}" fill="{name_color}" '
            f'font-size="{name_size}" font-weight="600" font-family="{name_family}" '
            f'text-anchor="middle">{name}</text>'
        )
    return "\n".join(parts)


def panel(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    lines: list[tuple[str, str]] | None = None,
    *,
    fill: str = PAPER_2,
    stroke: str = RULE_SOLID,
    title_color: str = INK,
    title_size: int = 12,
    line_size: int = 10,
    radius: int = 6,
    stroke_width: int = 1,
    dashed: bool = False,
) -> str:
    """一个带标题和多行内容的框。行类型：``code`` / ``text`` / ``gap``。"""
    dash = ' stroke-dasharray="4,3"' if dashed else ""
    parts = [
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{PAPER}"/>',
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash}/>',
        f'  <text x="{x + 14}" y="{y + 23}" fill="{title_color}" font-size="{title_size}" '
        f'font-weight="600" font-family="{SANS}">{title}</text>',
    ]
    yy = y + 45
    for kind, text in lines or []:
        if kind == "gap":
            yy += 8
            continue
        family = MONO if kind == "code" else SANS
        color = INK if kind == "code" else MUTED
        parts.append(
            f'  <text x="{x + 14}" y="{yy}" fill="{color}" font-size="{line_size}" '
            f'font-family="{family}">{text}</text>'
        )
        yy += 18
    return "\n".join(parts)


def chips(
    center_x: float,
    y: int,
    count: int,
    *,
    w: int = 46,
    h: int = 28,
    gap: int = 8,
    fill: str = PAPER_2,
    stroke: str = RULE_SOLID,
    dashed: bool = False,
) -> tuple[str, float, float]:
    """一排代表实体的小方块。返回 SVG、整组的左边界与右边界。"""
    total = count * w + (count - 1) * gap
    start = center_x - total / 2
    dash = ' stroke-dasharray="4,3"' if dashed else ""
    parts = []
    for i in range(count):
        cx = start + i * (w + gap)
        parts.append(
            f'  <rect x="{cx:g}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="1"{dash}/>'
        )
        # 两道细线，让方块读起来像一份实体而不是空格
        parts.append(
            f'  <line x1="{cx + 9:g}" y1="{y + 11}" x2="{cx + w - 9:g}" y2="{y + 11}" '
            f'stroke="{RULE_SOLID}" stroke-width="1"/>'
        )
        parts.append(
            f'  <line x1="{cx + 9:g}" y1="{y + 18}" x2="{cx + w - 18:g}" y2="{y + 18}" '
            f'stroke="{RULE_SOLID}" stroke-width="1"/>'
        )
    return "\n".join(parts), start, start + total


def elbow(
    points: list[tuple[int, int]],
    *,
    stroke: str = MUTED,
    width: int = 1,
    dashed: bool = False,
    marker: str = "",
    radius: int = 8,
) -> str:
    """直角折线连接器，转角是 r=8 的四分之一圆弧。"""
    pts = [(float(x), float(y)) for x, y in points]
    d = [f"M {pts[0][0]:g} {pts[0][1]:g}"]
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        prev = pts[i - 2] if i >= 2 else None
        nxt = pts[i + 1] if i + 1 < len(pts) else None
        if prev is None or nxt is None:
            d.append(f"L {x1:g} {y1:g}")
            continue
        if x1 == x0:
            in_dir = (0.0, 1.0 if y1 > y0 else -1.0)
            in_len = abs(y1 - y0)
        else:
            in_dir = (1.0 if x1 > x0 else -1.0, 0.0)
            in_len = abs(x1 - x0)
        if x1 == nxt[0]:
            out_dir = (0.0, 1.0 if nxt[1] > y1 else -1.0)
            out_len = abs(nxt[1] - y1)
        else:
            out_dir = (1.0 if nxt[0] > x1 else -1.0, 0.0)
            out_len = abs(nxt[0] - x1)
        r = min(float(radius), in_len / 2, out_len / 2)
        if r <= 0:
            d.append(f"L {x1:g} {y1:g}")
            continue
        sx = x1 - in_dir[0] * r
        sy = y1 - in_dir[1] * r
        ex = x1 + out_dir[0] * r
        ey = y1 + out_dir[1] * r
        d.append(f"L {sx:g} {sy:g}")
        d.append(f"Q {x1:g} {y1:g} {ex:g} {ey:g}")
    path = " ".join(d)
    extra = ""
    if dashed:
        extra += ' stroke-dasharray="5,4"'
    if marker:
        extra += f' marker-end="url(#{marker})"'
    return f'  <path d="{path}" fill="none" stroke="{stroke}" stroke-width="{width}"{extra}/>'


def straight(
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    *,
    stroke: str = MUTED,
    width: int = 1,
    dashed: bool = False,
    marker: str = "",
) -> str:
    """一条直线连接器。"""
    extra = ' stroke-dasharray="5,4"' if dashed else ""
    if marker:
        extra += f' marker-end="url(#{marker})"'
    return (
        f'  <path d="M {x0} {y0} L {x1} {y1}" fill="none" stroke="{stroke}" '
        f'stroke-width="{width}"{extra}/>'
    )


def label(
    x: float,
    y: float,
    text: str,
    *,
    size: int = 9,
    color: str = SOFT,
    anchor: str = "middle",
    width: float | None = None,
    family: str = SANS,
    tracking: str = "",
) -> str:
    """一个带不透明底衬的标签。底衬比文字宽 12px，高 16px。"""
    w = width if width is not None else text_width(text, size) + 12
    h = 16
    if anchor == "middle":
        mask_x = x - w / 2
    elif anchor == "end":
        mask_x = x - w
    else:
        mask_x = x
    mask_y = y - h + 4
    tr = f' letter-spacing="{tracking}"' if tracking else ""
    return (
        f'  <rect x="{mask_x:g}" y="{mask_y:g}" width="{w:g}" height="{h}" rx="2" fill="{PAPER}"/>\n'
        f'  <text x="{x:g}" y="{y:g}" fill="{color}" font-size="{size}" '
        f'font-family="{family}" text-anchor="{anchor}"{tr}>{text}</text>'
    )


def note(x: float, y: float, text: str, *, size: int = 9, color: str = SOFT) -> str:
    """一行普通说明文字，不带底衬。"""
    return (
        f'  <text x="{x:g}" y="{y:g}" fill="{color}" font-size="{size}" '
        f'font-family="{SANS}">{text}</text>'
    )


def legend_item(x: int, y: int, color: str, line1: str, line2: str) -> str:
    """图例里的一行：色块 + 两行文字。"""
    return "\n".join(
        [
            f'  <rect x="{x}" y="{y - 8}" width="8" height="8" rx="2" fill="{color}"/>',
            f'  <text x="{x + 14}" y="{y}" fill="{INK}" font-size="9.5" '
            f'font-family="{SANS}">{line1}</text>',
            f'  <text x="{x + 14}" y="{y + 15}" fill="{MUTED}" font-size="9" '
            f'font-family="{SANS}">{line2}</text>',
        ]
    )


def figure_block(
    slug: str,
    lang: str,
    title: str,
    desc: str,
    caption: str,
    width: int,
    height: int,
    content: str,
) -> str:
    """把一张图包成 ``<figure>``。"""
    num = FIGURE_NO[slug]
    badge = f"图 {num}" if lang == "zh" else f"Figure {num}"
    return (
        f'<figure class="figure" id="fig-{slug}">\n'
        f"{svg(slug, title, desc, width, height, content)}\n"
        f'<figcaption><span class="fig-label">{badge}</span> {caption}</figcaption>\n'
        f"</figure>"
    )


# --------------------------------------------------------------------------
# 图 1：概念之间的关系（依赖图）
#
# 四层排名，从上到下是「静态定义」到「一次运行的结果」：
#   第 0 层  算子 home（DOCORDER_HOMES 里）
#   第 1 层  作业里的节点
#   第 2 层  节点在本次运行写出的输出目录
#   第 3 层  实体目录
# --------------------------------------------------------------------------


def fig_concepts(lang: str) -> str:
    slug = "concepts"
    w, h = 900, 560

    node_w, node_h = 190, 52
    homes_y = 60
    nodes_y = 200
    outs_y = 330
    ents_y = 450

    home_x = 40
    home2_x = 300
    node_x = 40
    node2_x = 340
    out_x = 40
    out2_x = 340
    ent_x = 40
    ent2_x = 340

    content: list[str] = []

    # ---- 连接器（先画，压在节点下面）----
    content.append(
        elbow(
            [
                (home_x + node_w / 2, homes_y + node_h),
                (home_x + node_w / 2, nodes_y - 20),
                (node_x + node_w / 2, nodes_y - 20),
                (node_x + node_w / 2, nodes_y),
            ],
            marker=f"{slug}-arrow",
        )
    )
    content.append(
        elbow(
            [
                (home2_x + node_w / 2, homes_y + node_h),
                (home2_x + node_w / 2, nodes_y - 20),
                (node2_x + node_w / 2, nodes_y - 20),
                (node2_x + node_w / 2, nodes_y),
            ],
            marker=f"{slug}-arrow",
        )
    )
    content.append(
        elbow(
            [(node_x + node_w / 2, nodes_y + node_h), (node_x + node_w / 2, outs_y)],
            marker=f"{slug}-arrow",
        )
    )
    content.append(
        elbow(
            [(node2_x + node_w / 2, nodes_y + node_h), (node2_x + node_w / 2, outs_y)],
            marker=f"{slug}-arrow",
        )
    )
    content.append(
        elbow(
            [(out_x + node_w / 2, outs_y + node_h), (out_x + node_w / 2, ents_y)],
            marker=f"{slug}-arrow",
        )
    )
    content.append(
        elbow(
            [(out2_x + node_w / 2, outs_y + node_h), (out2_x + node_w / 2, ents_y)],
            marker=f"{slug}-arrow",
        )
    )
    # 节点 notes -> 节点 prompt（上游引用）
    content.append(
        elbow(
            [
                (node_x + node_w, nodes_y + node_h / 2),
                (node_x + node_w + 30, nodes_y + node_h / 2),
                (node_x + node_w + 30, nodes_y - 26),
                (node2_x - 30, nodes_y - 26),
                (node2_x - 30, nodes_y + node_h / 2),
                (node2_x, nodes_y + node_h / 2),
            ],
            stroke=TEAL,
            marker=f"{slug}-arrow-teal",
        )
    )
    # 实体 prompt -> 实体 notes（上游快照指回上游）
    content.append(
        elbow(
            [
                (ent2_x, ents_y + node_h / 2),
                (ent2_x - 30, ents_y + node_h / 2),
                (ent2_x - 30, ents_y - 28),
                (ent_x + node_w + 40, ents_y - 28),
                (ent_x + node_w + 40, ents_y + node_h / 2),
                (ent_x + node_w, ents_y + node_h / 2),
            ],
            stroke=TEAL,
            dashed=True,
            marker=f"{slug}-arrow-teal",
        )
    )

    # ---- 箭头标签（不透明底衬，与线留出可见间隙）----
    content.append(label(node_x + node_w / 2, homes_y + node_h + 28, T("引用", "referenced", lang)))
    content.append(label(home2_x + node_w / 2, homes_y + node_h + 28, T("引用", "referenced", lang)))
    content.append(label(node_x + node_w / 2, nodes_y + node_h + 26, T("写出", "writes", lang)))
    content.append(label(out_x + node_w / 2, outs_y + node_h + 26, T("包含", "holds", lang)))
    content.append(
        label(node2_x - 36, nodes_y - 40, T("上游", "upstream", lang), anchor="end")
    )
    content.append(
        label(
            ent_x + node_w + 60,
            ents_y - 42,
            T("快照指回上游", "snapshot points back", lang),
        )
    )

    # ---- 节点 ----
    content.append(
        node(
            home_x, homes_y, node_w, node_h,
            T("算子 home", "operator home", lang), "notes_source",
            fill=PAPER_2, stroke=INK,
            tag=T("静态", "static", lang), tag_stroke=MUTED,
        )
    )
    content.append(
        node(
            home2_x, homes_y, node_w, node_h,
            T("算子 home", "operator home", lang), "prompt",
            fill=PAPER_2, stroke=INK,
            tag=T("静态", "static", lang), tag_stroke=MUTED,
        )
    )
    content.append(
        node(
            node_x, nodes_y, node_w, node_h,
            T("节点 notes", "node notes", lang),
            T("source · 无上游", "source · no upstream", lang),
            fill=TEAL_SOFT, stroke=TEAL,
            tag=T("作业", "job", lang), tag_stroke=TEAL,
        )
    )
    content.append(
        node(
            node2_x, nodes_y, node_w, node_h,
            T("节点 prompt", "node prompt", lang),
            T("map · 上游 notes", "map · upstream notes", lang),
            fill=TEAL_SOFT, stroke=TEAL,
            tag=T("作业", "job", lang), tag_stroke=TEAL,
        )
    )
    content.append(
        node(
            out_x, outs_y, node_w, node_h,
            "runs/notes/demo/",
            fill=PAPER_2, stroke=MUTED, name_family=MONO, name_size=12,
        )
    )
    content.append(
        node(
            out2_x, outs_y, node_w, node_h,
            "runs/prompt/demo/",
            fill=PAPER_2, stroke=MUTED, name_family=MONO, name_size=12,
        )
    )
    content.append(
        node(
            ent_x, ents_y, node_w, node_h,
            T("实体 hello", "entity hello", lang), "data · tag.json",
            fill=PAPER_2, stroke=RULE_SOLID,
            tag=T("结果", "result", lang), tag_stroke=MUTED,
        )
    )
    content.append(
        node(
            ent2_x, ents_y, node_w, node_h,
            T("实体 hello", "entity hello", lang), "data · tag.json",
            fill=PAPER_2, stroke=RULE_SOLID,
            tag=T("结果", "result", lang), tag_stroke=MUTED,
        )
    )

    # ---- 层标签（右侧）----
    for y, zh, en in (
        (homes_y, "算子 home", "operator home"),
        (nodes_y, "作业节点", "job node"),
        (outs_y, "输出目录", "output directory"),
        (ents_y, "实体", "entity"),
    ):
        content.append(
            f'  <text x="{w - 12}" y="{y + node_h / 2 + 4:g}" fill="{SOFT}" font-size="9" '
            f'font-family="{SANS}" text-anchor="end">{T(zh, en, lang)}</text>'
        )

    title = T("docorder 概念之间的关系", "How docorder's concepts relate", lang)
    desc = T(
        "算子 home 被作业节点引用，节点在一次运行中写出输出目录，输出目录里包含实体，"
        "下游实体的上游快照指回上游实体。",
        "An operator home is referenced by a job node; the node writes an output "
        "directory during a run; the directory holds entities; the upstream snapshot "
        "of a downstream entity points back to its upstream.",
        lang,
    )
    caption = T(
        "概念之间的关系：算子 home 被节点引用，节点写出输出目录，输出目录里是实体，"
        "下游实体的上游快照指回上游。",
        "How the concepts fit together: an operator home is referenced by a node, "
        "the node writes an output directory, the directory holds entities, and a "
        "downstream entity's upstream snapshot points back to its upstream.",
        lang,
    )
    return figure_block(slug, lang, title, desc, caption, w, h, "\n".join(content))


# --------------------------------------------------------------------------
# 图 2：一个 stage 的经过（流程图）
#
# 主线七步，右侧图例解释「比较」这一步的四种结局。
# --------------------------------------------------------------------------

def fig_stage(lang: str) -> str:
    slug = "stage"
    w, h = 900, 640

    col_x, col_w = 300, 300
    center = col_x + col_w / 2
    rows = {
        "a": 48,
        "b": 124,
        "c": 200,
        "d": 276,
        "e": 372,
        "f": 468,
        "g": 564,
    }
    box_h = 48
    tall_h = 64

    content: list[str] = []

    # ---- 连接器 ----
    content.append(straight(center, rows["a"] + box_h, center, rows["b"], marker=f"{slug}-arrow"))
    content.append(straight(center, rows["b"] + box_h, center, rows["c"], marker=f"{slug}-arrow"))
    content.append(straight(center, rows["c"] + box_h, center, rows["d"], marker=f"{slug}-arrow"))
    content.append(straight(center, rows["d"] + tall_h, center, rows["e"], marker=f"{slug}-arrow"))
    content.append(straight(center, rows["e"] + tall_h, center, rows["f"], marker=f"{slug}-arrow"))
    content.append(straight(center, rows["f"] + tall_h, center, rows["g"], marker=f"{slug}-arrow"))
    # 比较通过 -> 保留
    content.append(
        straight(
            col_x, rows["c"] + box_h / 2, 260, rows["c"] + box_h / 2,
            stroke=MOSS, marker=f"{slug}-arrow-moss",
        )
    )

    # ---- 边标签 ----
    content.append(
        label(280, rows["c"] + box_h / 2 - 12, T("通过", "match", lang))
    )

    # ---- 主线节点 ----
    content.append(
        node(col_x, rows["a"], col_w, box_h, T("建立输出目录", "create the output directory", lang))
    )
    content.append(
        node(
            col_x, rows["b"], col_w, box_h,
            T("列出应得名单", "list the expected names", lang),
            T("读上游在本 epoch 的实体", "read the upstream entities", lang),
        )
    )
    content.append(
        node(
            col_x, rows["c"], col_w, box_h,
            T("与磁盘上的实体比较", "compare with the entities on disk", lang),
        )
    )
    content.append(
        node(
            col_x, rows["d"], col_w, tall_h,
            T("清理与预留", "clean up and reserve", lang),
            T("删掉要删的 · 留空 tag.json", "delete what is gone · empty tag.json", lang),
            fill=TEAL_SOFT, stroke=TEAL,
        )
    )
    content.append(
        node(
            col_x, rows["e"], col_w, tall_h,
            T("调用 function", "call the function", lang),
            "transform_data → transform_props",
        )
    )
    content.append(
        node(
            col_x, rows["f"], col_w, tall_h,
            T("处理附加信息", "post-process the tag", lang),
            T("合并 global_prop · 重置 upstream", "merge global_prop · reset upstream", lang),
        )
    )
    content.append(
        node(
            col_x, rows["g"], col_w, box_h,
            T("写 data，再写 tag.json", "write data, then tag.json", lang),
        )
    )

    # ---- 旁路：比较通过 ----
    content.append(
        node(
            40, rows["c"], 220, tall_h,
            T("比较通过", "matches", lang),
            T("原样保留，不再调用 function", "kept as is, function not called", lang),
            fill=MOSS_SOFT, stroke=MOSS,
        )
    )

    # ---- 图例：比较的四种结局 ----
    content.append(
        panel(
            640, rows["c"] - 24, 240, 208,
            T("比较的四种结局", "four outcomes of the comparison", lang),
        )
    )
    legend = [
        (MOSS, T("比较通过", "snapshot matches", lang), T("保留，不调用 function", "keep, skip the function", lang)),
        (INK, T("名单里有、目录里没有", "expected, not on disk", lang), T("新建并调用 function", "create it and run the function", lang)),
        (INK, T("快照或 depend 不吻合", "snapshot or depend differs", lang), T("清空后重新处理", "clear it and reprocess", lang)),
        (CLAY, T("名单里没有、目录里有", "on disk, not expected", lang), T("删除整个实体目录", "delete the entity directory", lang)),
    ]
    for i, (color, l1, l2) in enumerate(legend):
        content.append(legend_item(654, rows["c"] + 34 + i * 42, color, l1, l2))

    content.append(note(40, 28, T("stage 开始", "stage begins", lang), size=9))
    content.append(note(40, rows["g"] + 66, T("stage 结束", "stage ends", lang), size=9))

    title = T("docorder 中一个 stage 的经过", "What one stage does", lang)
    desc = T(
        "一个 stage 依次建立输出目录、列出应得名单、与磁盘上的实体比较、清理与预留、"
        "调用 function、处理附加信息，最后写 data 与 tag.json；比较通过的实体原样保留。",
        "A stage creates the output directory, lists the expected names, compares them "
        "with the entities on disk, cleans up and reserves, calls the function, "
        "post-processes the tag, and finally writes data and tag.json; entities that "
        "match are kept as they are.",
        lang,
    )
    caption = T(
        "一个 stage 的经过：比较之后，保留的实体就此跳过，其余的走完清理、调用与写出。",
        "One stage: after the comparison, matching entities are skipped and the rest go "
        "through cleanup, the function call and the write.",
        lang,
    )
    return figure_block(slug, lang, title, desc, caption, w, h, "\n".join(content))


# --------------------------------------------------------------------------
# 图 3：再次运行时的判定（状态判定图）
#
# 左边三个判定，右边四个结局。
# --------------------------------------------------------------------------

def fig_rerun(lang: str) -> str:
    slug = "rerun"
    w, h = 900, 640

    dx, dw = 40, 340
    ox, ow = 560, 300

    d1 = (88, 64)
    d2 = (208, 64)
    d3 = (328, 96)
    o_del = (92, 56)
    o_new = (212, 56)
    o_redo = (348, 56)
    o_keep = (440, 56)
    o_fatal = (512, 56)

    content: list[str] = []

    # ---- 连接器 ----
    content.append(straight(dx + 160, d1[0] + d1[1], dx + 160, d2[0], marker=f"{slug}-arrow"))
    content.append(straight(dx + 160, d2[0] + d2[1], dx + 160, d3[0], marker=f"{slug}-arrow"))
    content.append(straight(dx + dw, d1[0] + d1[1] // 2, ox, o_del[0] + o_del[1] // 2, marker=f"{slug}-arrow"))
    content.append(straight(dx + dw, d2[0] + d2[1] // 2, ox, o_new[0] + o_new[1] // 2, marker=f"{slug}-arrow"))
    content.append(straight(dx + dw, d3[0] + d3[1] // 2, ox, o_redo[0] + o_redo[1] // 2, marker=f"{slug}-arrow"))
    # 吻合 -> 保留
    content.append(
        elbow(
            [(dx + 250, d3[0] + d3[1]), (dx + 250, o_keep[0] + o_keep[1] // 2), (ox, o_keep[0] + o_keep[1] // 2)],
            marker=f"{slug}-arrow-moss",
        )
    )
    # depend 文件缺失 -> FatalError
    content.append(
        elbow(
            [(dx + 70, d3[0] + d3[1]), (dx + 70, o_fatal[0] + o_fatal[1] // 2), (ox, o_fatal[0] + o_fatal[1] // 2)],
            stroke=CLAY,
            marker=f"{slug}-arrow",
        )
    )

    # ---- 边标签 ----
    content.append(label(dx + 168, d1[0] + d1[1] + 18, T("是", "yes", lang), anchor="start"))
    content.append(label(dx + 168, d2[0] + d2[1] + 18, T("是", "yes", lang), anchor="start"))
    content.append(label(dx + dw + 80, d1[0] + d1[1] // 2 - 12, T("否", "no", lang)))
    content.append(label(dx + dw + 80, d2[0] + d2[1] // 2 - 12, T("否", "no", lang)))
    content.append(label(dx + dw + 80, d3[0] + d3[1] // 2 - 12, T("否", "no", lang)))
    content.append(label(dx + 258, o_keep[0] + o_keep[1] // 2 - 12, T("是", "yes", lang), anchor="start"))
    content.append(
        label(
            dx + 78,
            o_fatal[0] + o_fatal[1] // 2 - 44,
            T("depend 文件缺失", "depend file missing", lang),
            anchor="start",
            color=CLAY,
        )
    )

    # ---- 判定框 ----
    content.append(
        node(
            dx, d1[0], dw, d1[1],
            T("应得名单里有它吗？", "is it in the expected list?", lang),
        )
    )
    content.append(
        node(
            dx, d2[0], dw, d2[1],
            T("目录里已经有它吗？", "does it already exist on disk?", lang),
        )
    )
    content.append(
        node(
            dx, d3[0], dw, d3[1],
            T("快照吻合，且 depend 吻合或未声明？", "snapshot matches and depend matches?", lang),
            T("名字 / 节点名 / epoch / 哈希都要对", "name, node, epoch and hash must agree", lang),
        )
    )

    # ---- 结局框 ----
    content.append(
        node(
            ox, o_del[0], ow, o_del[1],
            T("删除整个实体目录", "delete the entity directory", lang),
            fill=CLAY_SOFT, stroke=CLAY,
        )
    )
    content.append(
        node(
            ox, o_new[0], ow, o_new[1],
            T("新建 · 调用 function", "create · call the function", lang),
        )
    )
    content.append(
        node(
            ox, o_redo[0], ow, o_redo[1],
            T("清空后重新处理", "clear and reprocess", lang),
        )
    )
    content.append(
        node(
            ox, o_keep[0], ow, o_keep[1],
            T("保留 · 不调用 function", "keep · no function call", lang),
            fill=MOSS_SOFT, stroke=MOSS,
        )
    )
    content.append(
        node(
            ox, o_fatal[0], ow, o_fatal[1],
            T("FatalError · 不清场", "FatalError · nothing is cleared", lang),
            fill=CLAY_SOFT, stroke=CLAY, dashed=True,
        )
    )

    # ---- 说明 ----
    content.append(
        note(
            dx,
            596,
            T(
                "应得名单为空时不比较：map / fanout 上游为空、apply 节点都属这一类；",
                "An empty expected list means no comparison at all: map and fanout with no upstream, and apply nodes.",
                lang,
            ),
        )
    )
    content.append(
        note(
            dx,
            614,
            T(
                "reduce 节点的上游为空时照常比较，function 收到一个空列表。",
                "A reduce node with no upstream compares anyway, and the function receives an empty list.",
                lang,
            ),
        )
    )

    title = T("同一个 epoch 上再次运行时的判定", "How an entity is judged on a re-run", lang)
    desc = T(
        "应得名单里有、目录里没有的实体被新建；目录里有、名单里没有的被删除；两边都有时，"
        "上游快照和 depend 都吻合的实体被保留，其余清空后重做。",
        "An entity that is expected but missing is created; one that exists but is not "
        "expected is deleted; when both exist, the entity is kept if its upstream "
        "snapshot and its depend fingerprint agree, and reprocessed otherwise.",
        lang,
    )
    caption = T(
        "再次运行时的判定：三个判定框决定每个实体是被保留、重做、新建还是删除。",
        "Judging on a re-run: three questions decide whether an entity is kept, "
        "reprocessed, created or deleted.",
        lang,
    )
    return figure_block(slug, lang, title, desc, caption, w, h, "\n".join(content))


# --------------------------------------------------------------------------
# 图 4：一次运行留下的目录（树图）
# --------------------------------------------------------------------------

def fig_layout(lang: str) -> str:
    slug = "layout"
    w, h = 900, 500

    content: list[str] = []

    # ---- 连接器 ----
    content.append(elbow([(150, 84), (150, 104), (130, 104), (130, 124)], marker=f"{slug}-arrow"))
    content.append(elbow([(150, 84), (150, 104), (450, 104), (450, 124)], marker=f"{slug}-arrow"))
    content.append(straight(130, 168, 130, 208, marker=f"{slug}-arrow"))
    content.append(elbow([(450, 168), (450, 188), (400, 188), (400, 208)], marker=f"{slug}-arrow"))
    content.append(elbow([(400, 252), (400, 272), (360, 272), (360, 292)], marker=f"{slug}-arrow"))
    content.append(elbow([(360, 336), (360, 356), (260, 356), (260, 376)], marker=f"{slug}-arrow"))
    content.append(elbow([(360, 336), (360, 356), (445, 356), (445, 376)], marker=f"{slug}-arrow"))

    # ---- 目录节点 ----
    content.append(
        node(40, 40, 220, 44, T("<输出根目录>/", "<output root>/", lang),
             fill=PAPER_2, stroke=INK, name_family=MONO, name_size=12)
    )
    content.append(
        node(40, 124, 180, 44, ".staging/", fill=PAPER_2, stroke=RULE_SOLID, name_family=MONO, name_size=12)
    )
    content.append(
        node(360, 124, 180, 44, T("<节点名>/", "<node name>/", lang),
             fill=PAPER_2, stroke=RULE_SOLID, name_family=MONO, name_size=12)
    )
    content.append(
        node(40, 208, 180, 44, T("<文件名>", "<file name>", lang),
             fill=PAPER_2, stroke=RULE_SOLID, name_family=MONO, name_size=12)
    )
    content.append(
        node(320, 208, 160, 44, "<epoch>/", fill=PAPER_2, stroke=RULE_SOLID, name_family=MONO, name_size=12)
    )
    content.append(
        node(
            560, 208, 200, 44, T("<另一个 epoch>/", "<another epoch>/", lang),
            fill=PAPER_2, stroke=SOFT, name_family=MONO, name_size=12, dashed=True,
        )
    )
    content.append(
        node(280, 292, 160, 44, T("<实体名>/", "<entity name>/", lang),
             fill=PAPER_2, stroke=RULE_SOLID, name_family=MONO, name_size=12)
    )
    content.append(
        node(200, 376, 120, 40, "data", T("正文", "the body", lang),
             fill=PAPER_2, stroke=RULE_SOLID, name_family=MONO, name_size=12, sub_size=9)
    )
    content.append(
        node(380, 376, 130, 40, "tag.json", T("附加信息", "the tag", lang),
             fill=PAPER_2, stroke=RULE_SOLID, name_family=MONO, name_size=12, sub_size=9)
    )

    # ---- 旁注 ----
    content.append(note(236, 150, T("作业整体输出", "the whole job's output", lang)))
    content.append(note(236, 234, T("内容是上游实体的正文", "holds the upstream body", lang)))
    content.append(
        note(560, 276, T("旧 epoch 留在原处，runner 不再读写", "an old epoch stays put", lang))
    )
    content.append(note(525, 400, T("有上游时含 upstream 快照", "carries the upstream snapshot", lang)))
    content.append(
        note(40, 446, T("epoch 是 execute 的参数，同一次运行里所有节点共用一个。", "The epoch is an argument to execute; every node in a run shares it.", lang))
    )
    content.append(
        note(40, 466, T(".staging 不属于任何节点，也不是某一层 epoch。", ".staging belongs to no node and is not an epoch layer.", lang))
    )

    title = T("一次运行留下的目录", "What a run leaves on disk", lang)
    desc = T(
        "输出根目录下有 .staging 与每个节点各自的目录；节点目录按 epoch 分层，"
        "epoch 层下面是实体目录，实体目录里有 data 与 tag.json 两个文件。",
        "Under the output root there is .staging and one directory per node; a node "
        "directory is layered by epoch, and each entity directory holds a data file "
        "and a tag.json.",
        lang,
    )
    caption = T(
        "一次运行留下的目录：节点目录下按 epoch 分层，实体目录里是 data 与 tag.json。",
        "What a run leaves on disk: node directories are layered by epoch, and an entity "
        "directory holds data and tag.json.",
        lang,
    )
    return figure_block(slug, lang, title, desc, caption, w, h, "\n".join(content))


# --------------------------------------------------------------------------
# 图 5：五种算子（数据流图）
#
# 每一行都是「上游实体 -> 算子 -> 输出实体」，箭头上标的是个数。
# --------------------------------------------------------------------------

def fig_operators(lang: str) -> str:
    slug = "operators"
    w, h = 900, 540

    left_c = 140
    right_c = 700
    box_x, box_w = 280, 260
    rows = [48, 132, 216, 300, 384]
    box_h = 56

    content: list[str] = []

    # ---- 表头 ----
    content.append(
        f'  <text x="{left_c}" y="28" fill="{SOFT}" font-size="9.5" font-family="{SANS}" '
        f'text-anchor="middle">{T("上游实体", "upstream entities", lang)}</text>'
    )
    content.append(
        f'  <text x="{box_x + box_w / 2:g}" y="28" fill="{SOFT}" font-size="9.5" '
        f'font-family="{SANS}" text-anchor="middle">{T("算子", "operator", lang)}</text>'
    )
    content.append(
        f'  <text x="{right_c}" y="28" fill="{SOFT}" font-size="9.5" font-family="{SANS}" '
        f'text-anchor="middle">{T("输出实体", "output entities", lang)}</text>'
    )

    specs = [
        # (类型, 基类, 左组, 左标注, 右组, 右标注, 右样式)
        ("source", "SourceFunction", "ext", None, 3, "N", "chips"),
        ("map", "MapFunction", 1, "1", 1, "1", "chips"),
        ("reduce", "ReduceFunction", 3, "N", 1, "1", "chips"),
        ("fanout", "FanoutFunction", 1, "1", 3, "N", "chips"),
        ("apply", "ApplyFunction", 3, "N", 0, "0", "none"),
    ]

    for i, (kind, base, lcount, llabel, rcount, rlabel, rstyle) in enumerate(specs):
        y = rows[i]
        cy = y + box_h / 2

        # 左侧
        if lcount == "ext":
            content.append(
                node(
                    left_c - 70, y + 4, 140, 48,
                    T("外部数据", "external data", lang),
                    fill=TEAL_SOFT, stroke=TEAL, name_size=12,
                )
            )
            l_right = left_c + 70
        else:
            svg_chips, _l, l_right = chips(left_c, y + 14, lcount)
            content.append(svg_chips)

        # 中间
        content.append(
            node(box_x, y, box_w, box_h, kind, base, name_family=MONO, name_size=13)
        )

        # 右侧
        if rstyle == "none":
            content.append(
                node(
                    right_c - 70, y + 4, 140, 48,
                    T("不写实体", "writes no entity", lang),
                    fill=CLAY_SOFT, stroke=CLAY, name_size=12, dashed=True,
                )
            )
            r_left = right_c - 70
        else:
            svg_chips, r_left, _r = chips(right_c, y + 14, rcount)
            content.append(svg_chips)

        # 箭头
        content.append(straight(l_right + 10, cy, box_x - 8, cy, marker=f"{slug}-arrow"))
        content.append(straight(box_x + box_w + 8, cy, r_left - 10, cy, marker=f"{slug}-arrow"))

        # 个数标签
        if llabel:
            content.append(label((l_right + 10 + box_x - 8) / 2, cy - 12, llabel, size=10))
        content.append(label((box_x + box_w + 8 + r_left - 10) / 2, cy - 12, rlabel, size=10))

    # ---- 脚注 ----
    content.append(
        note(
            40,
            470,
            T(
                "实体名：source 由 emit 给出 · map 与上游同名",
                "Entity names: source comes from emit, map matches the upstream,",
                lang,
            ),
        )
    )
    content.append(
        note(
            40,
            490,
            T(
                "reduce 取参数 output（默认 result）· fanout 由 output_names 给出",
                "reduce uses the output argument, fanout comes from output_names,",
                lang,
            ),
        )
    )
    content.append(
        note(
            40,
            510,
            T(
                "apply 没有输出实体，也不能有下游",
                "apply writes no entity and can have no downstream.",
                lang,
            ),
        )
    )

    title = T("五种算子的输入与输出", "The five operator types", lang)
    desc = T(
        "source 从外部数据产生若干实体；map 让一个上游实体对应一个同名输出实体；"
        "reduce 把全部上游实体合成一个；fanout 把一个上游实体拆成若干个；"
        "apply 只调用 function，不产生实体。",
        "source produces entities from external data; map turns one upstream entity into "
        "one entity of the same name; reduce merges every upstream entity into one; "
        "fanout splits one upstream entity into several; apply only calls the function "
        "and produces no entity.",
        lang,
    )
    caption = T(
        "五种算子：箭头上标的是实体个数，apply 是唯一不产生输出实体的类型。",
        "The five operator types: the number over each arrow counts entities, and apply "
        "is the only type that produces none.",
        lang,
    )
    return figure_block(slug, lang, title, desc, caption, w, h, "\n".join(content))


# --------------------------------------------------------------------------
# 图 6：内置模板变量（分层图）
#
# 顶层只有 operator / job / entity 三个名字。
# --------------------------------------------------------------------------

def fig_variables(lang: str) -> str:
    slug = "variables"
    w, h = 900, 560

    top_x, top_w, top_y = 280, 340, 40
    top_c = top_x + top_w / 2
    mid_y, mid_h = 156, 176
    low_y, low_h = 396, 84

    op_x, op_w = 30, 270
    job_x, job_w = 320, 180
    ent_x, ent_w = 520, 350
    op_c = op_x + op_w / 2
    job_c = job_x + job_w / 2
    ent_c = ent_x + ent_w / 2

    content: list[str] = []

    # ---- 连接器 ----
    content.append(elbow([(top_c, 104), (top_c, 128), (op_c, 128), (op_c, mid_y)], marker=f"{slug}-arrow"))
    content.append(elbow([(top_c, 104), (top_c, 128), (job_c, 128), (job_c, mid_y)], marker=f"{slug}-arrow"))
    content.append(elbow([(top_c, 104), (top_c, 128), (ent_c, 128), (ent_c, mid_y)], marker=f"{slug}-arrow"))
    content.append(straight(op_c, mid_y + mid_h, op_c, low_y, marker=f"{slug}-arrow"))
    content.append(straight(job_c, mid_y + mid_h, job_c, low_y, marker=f"{slug}-arrow"))
    content.append(straight(ent_c, mid_y + mid_h, ent_c, low_y, marker=f"{slug}-arrow"))

    # ---- 顶层 ----
    content.append(
        node(
            top_x, top_y, top_w, 64,
            "template_env",
            T("模板读 {{…}}，Command 读 {…}", "templates read {{…}}, Command reads {…}", lang),
            name_family=MONO,
        )
    )

    # ---- 中层三组 ----
    content.append(
        panel(
            op_x, mid_y, op_w, mid_h,
            "operator",
            [
                ("code", "name   home   function_class"),
                ("code", "type   operator_home"),
                ("gap", ""),
                ("text", T("函数参数：props.json 去掉保留键，", "Function arguments: props.json without", lang)),
                ("text", T("再被节点的 config 覆盖", "the reserved keys, then overridden by config", lang)),
                ("code", T("例：template · directory", "e.g. template · directory", lang)),
            ],
        )
    )
    content.append(
        panel(
            job_x, mid_y, job_w, mid_h,
            "job",
            [
                ("code", "name"),
                ("code", "epoch"),
                ("gap", ""),
                ("text", T("作业的名字，和这次", "The job's name and the", lang)),
                ("text", T("运行使用的 epoch", "epoch of this run", lang)),
            ],
        )
    )
    content.append(
        panel(
            ent_x, mid_y, ent_w, mid_h,
            "entity",
            [
                ("code", "source_name    source_data"),
                ("code", "source_tag     source_data_path"),
                ("code", "target_name    target_data_path"),
                ("code", "output"),
                ("gap", ""),
                ("text", T("前四个是上游实体，后三个是", "The first four describe the upstream", lang)),
                ("text", T("正在写出的那个实体", "entity, the last three the one being written", lang)),
            ],
        )
    )

    # ---- 底层来源 ----
    content.append(
        panel(
            op_x, low_y, op_w, low_h,
            T("参数来源", "where the arguments come from", lang),
            [
                ("code", "props.json + 节点 config"),
                ("text", T("runner 再补上 name / home / type", "runner adds name, home and type", lang)),
            ],
        )
    )
    content.append(
        panel(
            job_x, low_y, job_w, low_h,
            T("作业来源", "where the job comes from", lang),
            [
                ("code", "execute(job, epoch)"),
                ("text", T("调用时给的两个参数", "the two arguments of the call", lang)),
            ],
        )
    )
    content.append(
        panel(
            ent_x, low_y, ent_w, low_h,
            T("实体来源", "where the entities come from", lang),
            [
                ("code", T("上游实体 + 正在写出的实体", "the upstream entity + the one being written", lang)),
                ("text", T("entity.source_tag 是上游的 tag.json", "entity.source_tag is the upstream tag.json", lang)),
            ],
        )
    )

    content.append(
        note(
            40,
            516,
            T(
                "JinjaToJsonnet 的最外层不同：上游 JSON 的各个键 + variables 参数 + operator / job / entity / home。",
                "JinjaToJsonnet differs at the top level: the upstream JSON keys, the "
                "variables argument, plus operator, job, entity and home.",
                lang,
            ),
        )
    )

    title = T("内置模板变量", "The built-in template variables", lang)
    desc = T(
        "template_env 的顶层只有 operator、job、entity 三个名字；operator 是被 config "
        "覆盖过的函数参数再加上 runner 填入的几项，job 是作业名和本次 epoch，entity "
        "分成上游实体与正在写出的实体两组。",
        "The top level of template_env holds exactly three names: operator, job and "
        "entity. operator carries the function arguments overridden by config plus a few "
        "values filled in by the runner, job carries the job name and the epoch of this "
        "run, and entity is split between the upstream entity and the one being written.",
        lang,
    )
    caption = T(
        "内置模板变量：顶层只有 operator、job、entity 三个名字，每一组都有各自的来源。",
        "The built-in template variables: three names at the top level, each with its own "
        "origin.",
        lang,
    )
    return figure_block(slug, lang, title, desc, caption, w, h, "\n".join(content))


# --------------------------------------------------------------------------
# 图 7：两类哈希如何决定一个实体的去留（状态判定图）
#
# 左边比上游快照，右边比 depend 的外部文件，两处都吻合才保留。
# --------------------------------------------------------------------------

def fig_hashes(lang: str) -> str:
    slug = "hashes"
    w, h = 900, 640

    content: list[str] = []

    # ---- 连接器 ----
    content.append(straight(210, 112, 210, 148, marker=f"{slug}-arrow"))
    content.append(straight(210, 192, 210, 228, marker=f"{slug}-arrow"))
    content.append(straight(690, 112, 690, 148, marker=f"{slug}-arrow"))
    content.append(straight(690, 192, 690, 228, marker=f"{slug}-arrow"))
    content.append(
        elbow([(210, 296), (210, 320), (330, 320), (330, 344)], marker=f"{slug}-arrow")
    )
    content.append(
        elbow([(690, 296), (690, 320), (570, 320), (570, 344)], marker=f"{slug}-arrow")
    )
    content.append(
        elbow([(390, 404), (390, 428), (220, 428), (220, 452)], marker=f"{slug}-arrow-moss")
    )
    content.append(
        elbow([(510, 404), (510, 428), (680, 428), (680, 452)], stroke=CLAY, marker=f"{slug}-arrow")
    )

    # ---- 边标签 ----
    content.append(label(300, 416, T("是", "yes", lang)))
    content.append(label(590, 416, T("否", "no", lang)))

    # ---- 两条判定支线 ----
    content.append(
        node(
            40, 56, 340, 56,
            T("上游实体的正文 + 用户 tag", "the upstream body and user tag", lang),
            T("正文变了，上游快照就对不上", "a changed body no longer matches", lang),
        )
    )
    content.append(node(105, 148, 210, 44, "sha256", name_family=MONO, name_size=13))
    content.append(
        node(
            40, 228, 340, 68,
            T("与快照里记录的 hash 比较", "compare with the hash in the snapshot", lang),
            T("快照记的是上游正文与用户 tag 的哈希", "the hash of the upstream body and user tag", lang),
        )
    )
    content.append(
        node(
            520, 56, 340, 56,
            T("外部文件（fingerprint.depend）", "the external files named in depend", lang),
            T("上游实体没有携带的那些文件", "files the upstream entity does not carry", lang),
        )
    )
    content.append(node(585, 148, 210, 44, "sha256", name_family=MONO, name_size=13))
    content.append(
        node(
            520, 228, 340, 68,
            T("与 tag.json 里 fingerprint.depend 比较", "compare with fingerprint.depend in tag.json", lang),
            T("键集合不同或任一哈希不同，都会重做", "a different key set or hash means a redo", lang),
        )
    )

    # ---- 合并后的判定与结局 ----
    content.append(
        node(300, 344, 300, 60, T("两处都吻合？", "do both match?", lang))
    )
    content.append(
        node(
            80, 452, 280, 56,
            T("保留 · 不调用 function", "keep · no function call", lang),
            fill=MOSS_SOFT, stroke=MOSS,
        )
    )
    content.append(
        node(
            540, 452, 280, 56,
            T("重做 · 清空后重做", "redo · clear and reprocess", lang),
            fill=CLAY_SOFT, stroke=CLAY,
        )
    )
    content.append(
        node(
            40, 548, 820, 56,
            T("fingerprint.record 只记账，不参与判定", "fingerprint.record is bookkeeping only", lang),
            T(
                "它写进 tag.json，因而随用户 tag 一起算进本实体的哈希",
                "it goes into tag.json, so it is part of this entity's own hash",
                lang,
            ),
        )
    )

    title = T("两类哈希如何决定一个实体的去留", "How the two hashes decide an entity", lang)
    desc = T(
        "一个实体要留下来，需要上游快照与上游当前状态吻合，并且 depend 声明的每一个文件的"
        "哈希与上一次记下的一致；任何一条不成立，这个实体重做。record 只是记账，不参与判断。",
        "An entity stays when the upstream snapshot matches the current upstream and "
        "every file declared in depend has the hash recorded before; if either check "
        "fails the entity is redone. record is bookkeeping and takes no part in the "
        "decision.",
        lang,
    )
    caption = T(
        "两类哈希如何合成一个判定：上游快照和 depend 都吻合，实体才被保留。",
        "How the two hashes make one decision: the entity is kept only when the "
        "upstream snapshot and depend both match.",
        lang,
    )
    return figure_block(slug, lang, title, desc, caption, w, h, "\n".join(content))


# --------------------------------------------------------------------------
# 图 8：数据治理案例的四个作业（数据流图）
#
# 四个作业接力，每个作业的产物交给下一个作业。
# --------------------------------------------------------------------------

def fig_pipeline(lang: str) -> str:
    slug = "pipeline"
    w, h = 900, 500

    job_x, job_w = 40, 500
    art_x, art_w = 600, 260
    rows = [48, 156, 264, 372]
    row_h = 88

    content: list[str] = []

    # ---- 连接器：作业 -> 产物 ----
    for row in rows:
        content.append(
            straight(job_x + job_w, row + row_h // 2, art_x, row + row_h // 2, marker=f"{slug}-arrow")
        )
    # ---- 连接器：产物 -> 下一个作业 ----
    for index, row in enumerate(rows[:-1]):
        top = row + row_h
        drop = top + 8
        content.append(
            elbow(
                [(730, top), (730, drop), (290, drop), (290, rows[index + 1])],
                marker=f"{slug}-arrow",
            )
        )

    # ---- 边标签 ----
    for row in rows:
        content.append(label(570, row + 32, T("写出", "writes", lang)))

    # ---- 作业框 ----
    jobs = [
        (
            "raw_root",
            T("建词根表", "build the root catalogue", lang),
            [("code", "source → librarian → taxonomist_root → publish")],
        ),
        (
            "refine_root",
            T("修词根表", "correct the root catalogue", lang),
            [("code", "source → optimizer_root → merge_root → publish_final")],
        ),
        (
            "root_assigner",
            T("给模型分配词根", "assign roots to the models", lang),
            [
                ("code", "source_assign → root_assigner → reduce_assigner → publish_assigner"),
                ("code", "→ extract_root → taxonomist_member → combine_root_member → publish_root_member"),
            ],
        ),
        (
            "member_attribute",
            T("补成员属性", "fill in the member attributes", lang),
            [("code", "source_member → assign_member → combine_assign_member → publish_assign_member")],
        ),
    ]
    for row, (name, purpose, lines) in zip(rows, jobs):
        content.append(
            panel(
                job_x, row, job_w, row_h,
                f"{name} {T('作业', 'job', lang)}：{purpose}",
                lines,
                title_size=12,
                line_size=9.5,
            )
        )

    # ---- 产物框 ----
    artifacts = [
        ("raw_root.csv", [("text", T("词根表初稿", "the first draft of the catalogue", lang))]),
        ("final_root.csv", [("text", T("词根表定稿", "the final catalogue", lang))]),
        (
            "root_assign.json",
            [
                ("text", T("归属表", "the assignment table", lang)),
                ("code", "root_member.csv"),
            ],
        ),
        (
            T("成员属性", "member attributes", lang),
            [("code", "root_member_assign.json")],
        ),
    ]
    for row, (name, lines) in zip(rows, artifacts):
        content.append(
            panel(
                art_x, row, art_w, row_h, name, lines,
                title_size=11, line_size=9.5,
            )
        )

    title = T("数据治理案例的四个作业", "The four jobs of the data governance case", lang)
    desc = T(
        "四个作业接力：建词根表、修词根表、给模型分配词根、补成员属性，每个作业的产物"
        "写进 .staging，交给下一个作业读取。",
        "Four jobs in sequence: build the root catalogue, correct it, assign roots to "
        "the models and fill in the member attributes. Each job writes its result into "
        ".staging, where the next job reads it.",
        lang,
    )
    caption = T(
        "案例的四个作业：产物写在 .staging 里，后一个作业读前一个的产出。",
        "The four jobs of the case: each result lands in .staging and the next job "
        "reads it.",
        lang,
    )
    return figure_block(slug, lang, title, desc, caption, w, h, "\n".join(content))


FIGURES = {
    "concepts": fig_concepts,
    "stage": fig_stage,
    "rerun": fig_rerun,
    "layout": fig_layout,
    "operators": fig_operators,
    "variables": fig_variables,
    "hashes": fig_hashes,
    "pipeline": fig_pipeline,
}


def replace_figure(text: str, slug: str, html: str) -> tuple[str, bool]:
    """把一对注释之间的内容整段换成最新的图。"""
    pattern = re.compile(
        r"<!-- figure:" + re.escape(slug) + r":start -->.*?<!-- figure:"
        + re.escape(slug)
        + r":end -->",
        re.S,
    )
    replacement = f"<!-- figure:{slug}:start -->\n{html}\n<!-- figure:{slug}:end -->"
    new_text, count = pattern.subn(lambda _m: replacement, text)
    return new_text, count > 0


def main() -> None:
    for path, lang in GUIDES.items():
        text = path.read_text(encoding="utf-8")
        replaced = 0
        for slug, render in FIGURES.items():
            text, ok = replace_figure(text, slug, render(lang))
            replaced += int(ok)
        path.write_text(text, encoding="utf-8")
        rel = path.relative_to(REPO_ROOT)
        print(f"{rel}: {replaced}/{len(FIGURES)} figures ({lang})")


if __name__ == "__main__":
    main()
