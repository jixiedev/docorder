"""把仓库里的 Markdown 文档编译成静态网页站点。

源文件是唯一的事实来源：

- ``docs/guide.md`` / ``docs/guide.en.md``：使用指南，按二级标题切成若干页。
- 根目录的 ``README.md``、``glossary.md``、``CONTRIBUTING.md``、``SECURITY.md``、
  ``CHANGELOG.md``：各自成一个页面。

产物在 ``docs/site/`` 下，目录结构与站点导航一致。生成之后不要手工改产物，
改源文件再重新运行本脚本。

用法::

    uv run python scripts/build_docs.py
"""

from __future__ import annotations

import re
import shutil
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import markdown
from markdown.extensions.toc import TocExtension

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
SITE_DIR = DOCS_DIR / "site"

LANGUAGES = ("zh", "en")

# 使用指南里每个二级标题的锚点，指向该章对应的网页。
# 键是锚点，值是网页在站点根下的相对路径。
GUIDE_ANCHORS: dict[str, dict[str, str]] = {"zh": {}, "en": {}}


def build_guide_anchors(site: Site) -> None:
    """记录每一章里出现过的锚点，用来把 ``guide.md#某节`` 改写成网页链接。"""
    for page in site.by_group("guide"):
        for language, body in (("zh", page.body_zh), ("en", page.body_en)):
            _, outline = render_markdown(body)
            for _, anchor, _ in outline:
                GUIDE_ANCHORS[language].setdefault(anchor, page.path)




@dataclass
class Chapter:
    """使用指南的一个二级标题，对应站点上的一个页面。"""

    key: str
    title_zh: str
    title_en: str
    body_zh: str
    body_en: str
    group: str = "guide"


@dataclass
class Page:
    """站点上的一个页面。

    ``body_*`` 要么是 Markdown 源码，要么是已经写好的 HTML 片段（首页概览
    属于后者，片段放在 ``scripts/templates/`` 下）。两种情况都由
    ``render_page`` 按 ``raw`` 标志区分处理。
    """

    path: str
    title_zh: str
    title_en: str
    body_zh: str
    body_en: str
    group: str
    nav_zh: str = ""
    nav_en: str = ""
    raw: bool = False


@dataclass
class Site:
    """整站的公共结构，用于渲染每一页的外壳。"""

    pages: list[Page] = field(default_factory=list)

    def by_group(self, group: str) -> list[Page]:
        return [p for p in self.pages if p.group == group]


def slugify_factory():
    """生成与 GitHub 一致的标题锚点。

    GitHub 的规则是：标题转小写，去掉标点，空格换成连字符，重复的标题依次加
    ``-1``、``-2``。``docs/guide.md`` 里已有的目录链接就是按这套规则写的，
    所以转换出来的锚点必须与它们逐字相同。
    """
    seen: Counter[str] = Counter()

    def slugify(value: str, separator: str) -> str:
        base = re.sub(r"[^\w\s-]", "", value).strip().lower().replace(" ", separator)
        count = seen[base]
        seen[base] += 1
        return base if count == 0 else f"{base}-{count}"

    return slugify


def render_markdown(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    """把 Markdown 转成 HTML，同时返回标题大纲。

    返回的大纲是 ``(层级, 锚点, 标题)`` 的列表，层级从 1 开始。
    """
    md = markdown.Markdown(
        extensions=[
            TocExtension(slugify=slugify_factory(), permalink=False),
            "fenced_code",
            "tables",
            "sane_lists",
        ]
    )
    html = md.convert(text)
    outline = [
        (int(level), anchor, title)
        for level, anchor, title in re.findall(
            r'<h([1-6]) id="([^"]+)">(.*?)</h\1>', html, re.S
        )
    ]
    outline = [(level, anchor, re.sub(r"<[^>]+>", "", title)) for level, anchor, title in outline]
    return html, outline


def split_guide(text: str) -> list[tuple[str, str, str]]:
    """按二级标题把指南切成 ``(标题, 标题锚点, 正文)`` 的列表。

    第一个 ``#`` 一级标题和它下面的目录被丢掉：目录由站点的侧栏承担，
    每个页面只保留自己的一章。
    """
    lines = text.split("\n")
    chapters: list[tuple[str, str, str]] = []
    current_title = ""
    current: list[str] = []
    in_fence = False
    seen_first_h2 = False

    for line in lines:
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
        if not in_fence and re.match(r"^##\s+", line):
            if seen_first_h2:
                chapters.append((current_title, github_slug(current_title), "\n".join(current).strip("\n")))
            else:
                seen_first_h2 = True
            current_title = re.sub(r"^##\s+", "", line).strip()
            current = []
            continue
        if not seen_first_h2:
            continue
        current.append(line)

    if seen_first_h2:
        chapters.append((current_title, github_slug(current_title), "\n".join(current).strip("\n")))
    return chapters


def github_slug(title: str) -> str:
    """标题的 GitHub 风格锚点。用法与 ``slugify_factory`` 里的规则一致。"""
    return re.sub(r"[^\w\s-]", "", title).strip().lower().replace(" ", "-")


def chapter_key(title: str, index: int) -> str:
    """给章节一个稳定的文件名片段。中英文按位置一一对应，共用同一个 key。"""
    cleaned = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return cleaned or f"chapter-{index + 1}"


def build() -> Site:
    site = Site()

    templates = Path(__file__).resolve().parent / "templates"
    site.pages.append(
        Page(
            path="index.html",
            title_zh="概览",
            title_en="Overview",
            body_zh=(templates / "overview_zh.html").read_text(encoding="utf-8"),
            body_en=(templates / "overview_en.html").read_text(encoding="utf-8"),
            group="overview",
            nav_zh="概览",
            nav_en="Overview",
            raw=True,
        )
    )

    guide_zh = (DOCS_DIR / "guide.md").read_text(encoding="utf-8")
    guide_en = (DOCS_DIR / "guide.en.md").read_text(encoding="utf-8")

    zh_chapters = split_guide(guide_zh)
    en_chapters = split_guide(guide_en)
    if len(zh_chapters) != len(en_chapters):
        raise SystemExit(
            f"中文章节数 {len(zh_chapters)} 与英文 {len(en_chapters)} 不一致，无法配对"
        )

    for index, ((zh_title, zh_slug, zh_body), (en_title, en_slug, en_body)) in enumerate(
        zip(zh_chapters, en_chapters)
    ):
        key = chapter_key(en_title, index)
        site.pages.append(
            Page(
                path=f"guide/{key}.html",
                title_zh=zh_title,
                title_en=en_title,
                body_zh=zh_body,
                body_en=en_body,
                group="guide",
                nav_zh=zh_title,
                nav_en=en_title,
            )
        )
        GUIDE_ANCHORS["zh"].setdefault(zh_slug, f"guide/{key}.html")
        GUIDE_ANCHORS["en"].setdefault(en_slug, f"guide/{key}.html")

    # 指南的目录页：列出全部章节。每章的摘要取自「文档结构」一章里已有的
    # 编号列表，那份列表与章节顺序一一对应。
    guide_pages = site.by_group("guide")
    summary_zh = chapter_summaries(guide_zh, guide_pages, "zh")
    summary_en = chapter_summaries(guide_en, guide_pages, "en")
    site.pages.append(
        Page(
            path="guide/index.html",
            title_zh="使用指南",
            title_en="The guide",
            body_zh='      <div class="chapter-list">\n'
            + "".join(
                f'      <a class="read" href="{Path(p.path).name}">\n'
                f"        <strong>{p.title_zh}</strong>\n"
                f"        <p>{summary_zh.get(p.path, '')}</p>\n"
                f"      </a>\n"
                for p in guide_pages
            )
            + "      </div>\n",
            body_en='      <div class="chapter-list">\n'
            + "".join(
                f'      <a class="read" href="{Path(p.path).name}">\n'
                f"        <strong>{p.title_en}</strong>\n"
                f"        <p>{summary_en.get(p.path, '')}</p>\n"
                f"      </a>\n"
                for p in guide_pages
            )
            + "      </div>\n",
            group="guide-index",
            nav_zh="使用指南",
            nav_en="The guide",
            raw=True,
        )
    )

    standalone = [
        ("readme.html", "README.md", "README.en.md", "快速开始", "Quick start", "start"),
        (
            "glossary.html",
            "glossary.md",
            "glossary.en.md",
            "术语表",
            "Glossary",
            "reference",
        ),
        (
            "code-of-conduct.html",
            "CODE_OF_CONDUCT.md",
            "CODE_OF_CONDUCT.en.md",
            "行为准则",
            "Code of conduct",
            "project",
        ),
        (
            "contributing.html",
            "CONTRIBUTING.md",
            "CONTRIBUTING.en.md",
            "参与贡献",
            "Contributing",
            "project",
        ),
        (
            "security.html",
            "SECURITY.md",
            "SECURITY.en.md",
            "安全",
            "Security",
            "project",
        ),
        (
            "changelog.html",
            "CHANGELOG.md",
            "CHANGELOG.en.md",
            "更新日志",
            "Changelog",
            "project",
        ),
    ]
    for path, source_zh, source_en, title_zh, title_en, group in standalone:
        body_zh = strip_first_heading((REPO_ROOT / source_zh).read_text(encoding="utf-8"))
        body_en = strip_first_heading((REPO_ROOT / source_en).read_text(encoding="utf-8"))
        site.pages.append(
            Page(
                path=path,
                title_zh=title_zh,
                title_en=title_en,
                body_zh=body_zh,
                body_en=body_en,
                group=group,
                nav_zh=title_zh,
                nav_en=title_en,
            )
        )

    return site


def chapter_summaries(guide_text: str, pages: list[Page], language: str) -> dict[str, str]:
    """从「文档结构」一章的编号列表里取出每一章的摘要。

    那一章按顺序描述了后面每一章的内容，条目与章节一一对应。每条形如
    ``1. 背景：docorder 要解决的问题，……``，冒号前是章名，后面是摘要。
    返回 ``{章节网页路径: 摘要}``。
    """
    lines = guide_text.split("\n")
    start = None
    for index, line in enumerate(lines):
        if line.startswith("## 文档结构") or line.startswith("## Document structure"):
            start = index
            break
    if start is None:
        return {}

    entries: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        match = re.match(r"^\d+\.\s+(.*)$", line)
        if match:
            entries.append(match.group(1))

    summaries: dict[str, str] = {}
    # 编号列表从「背景」开始，不含「文档结构」这一章；附录也不在列表里。
    described = [
        p for p in pages if p.nav_zh != "文档结构" and p.nav_en != "Document structure"
    ]
    for page, entry in zip(described, entries):
        _, _, summary = entry.partition("：")
        if not summary:
            _, _, summary = entry.partition(": ")
        summaries[page.path] = summary.strip() or entry

    # 「文档结构」和三个附录都不在编号列表里，各有一句固定的说明。
    fixed = {
        "zh": {
            "文档结构": "这份手册每一章讲什么，以及文中几张结构示意图的位置。",
            "附录 A：内置 function 一览": (
                "一张表列出每个内置 function：它属于哪种算子、接受什么、写出什么。"
            ),
            "附录 B：实现索引": "docorder 的每一部分在哪里：模块、基类和它们用到的辅助类。",
            "附录 C：相关文档": "README、术语表、贡献指南，以及与本手册配套的其它文档。",
        },
        "en": {
            "Document structure": (
                "What each chapter of this guide covers, and where the structural "
                "sketches in the text sit."
            ),
            "Appendix A: The built-in functions": (
                "Every built-in function in one table: which operator type it implements, "
                "what it takes, and what it writes."
            ),
            "Appendix B: Implementation index": (
                "Where each part of docorder lives: the modules, the base classes, and "
                "the helpers they rely on."
            ),
            "Appendix C: Related documents": (
                "The README, the glossary, the contributing guide, and the other "
                "documents that go with this guide."
            ),
        },
    }
    for page in pages:
        if page.path in summaries:
            continue
        name = page.nav_zh if language == "zh" else page.nav_en
        if name in fixed[language]:
            summaries[page.path] = fixed[language][name]
            continue
        # 附录标题带 A、B、C 的编号，按编号对上对应的说明。
        letter = re.search(r"(?:附录|Appendix)\s+([ABC])\b", name)
        if letter:
            key = {
                "A": ("附录 A：内置 function 一览", "Appendix A: The built-in functions"),
                "B": ("附录 B：实现索引", "Appendix B: Implementation index"),
                "C": ("附录 C：相关文档", "Appendix C: Related documents"),
            }[letter.group(1)]
            summaries[page.path] = fixed[language][key[0] if language == "zh" else key[1]]
            continue
        body = page.body_zh if language == "zh" else page.body_en
        first = first_sentence(body)
        if first:
            summaries[page.path] = first
    return summaries


def first_sentence(body: str) -> str:
    """取正文的第一段，作为没有编号摘要时的兜底。

    编号列表的行也要跳过，它们不是摘要。
    """
    for line in body.split("\n"):
        line = line.strip()
        if not line or re.match(r"^\d+\.\s", line):
            continue
        if line.startswith(("#", "```", "|", ">", "-")):
            continue
        return line
    return ""


def strip_first_heading(text: str) -> str:
    """去掉正文的一级标题，页面自己会渲染标题。"""
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith("# "):
            del lines[index]
            break
    return "\n".join(lines).strip("\n")


def rewrite_links(html: str, depth: int, language: str) -> str:
    """把正文里的 Markdown 链接改写成网页链接。

    源文件里写的是 ``../README.md``、``glossary.md``、``guide.md#一背景`` 这样的
    相对路径，指向仓库里的 Markdown 文件。站点上这些都有对应的网页，所以改成
    指向网页，并按当前页面的位置重新算相对路径。
    """
    up = "../" * depth

    def replace(match: re.Match[str]) -> str:
        href = match.group(1)
        if href.startswith(("http://", "https://", "#", "mailto:")):
            return match.group(0)
        target, _, fragment = href.partition("#")
        # 源文件从仓库根、docs/ 或 docs/site/ 出发写路径，三种写法都要认。
        target = target.lstrip("./")
        for lead in ("docs/site/", "docs/"):
            if target.startswith(lead):
                target = target[len(lead) :]
                break

        if target in ("guide.md", "guide.en.md"):
            # 指向使用指南某一节的链接，改成那一章的网页加锚点。
            # 指向整份指南的链接，改成指南的目录页。
            if not fragment:
                return f'href="{up}guide/index{language_suffix(language)}.html"'
            page_path = GUIDE_ANCHORS[language].get(fragment)
            if page_path is None:
                return match.group(0)
            filename = f"{Path(page_path).stem}{language_suffix(language)}.html"
            relative = f"{Path(page_path).parent}/{filename}".lstrip("./")
            return f'href="{up}{relative}#{fragment}"'

        mapped = SOURCE_TO_PAGE.get(target)
        if mapped is None:
            # 指向仓库里的其它文件，例如 LICENSE、pyproject.toml。
            # 站点放在 docs/site/ 下，仓库根在它的上面两级。
            if target and not target.startswith("http") and "/" not in target:
                repo_file = REPO_ROOT / target
                if repo_file.exists():
                    return f'href="{"../" * (depth + 2)}{target}"'
            return match.group(0)
        new_href = f"{up}{mapped}"
        if fragment:
            new_href = f"{new_href}#{fragment}"
        return f'href="{new_href}"'

    return re.sub(r'href="([^"]+)"', replace, html)


# 源文件路径到网页路径的映射，供正文里的链接改写使用。
SOURCE_TO_PAGE: dict[str, str] = {
    "README.md": "readme.html",
    "README.en.md": "readme.en.html",
    "glossary.md": "glossary.html",
    "glossary.en.md": "glossary.en.html",
    "CONTRIBUTING.md": "contributing.html",
    "CONTRIBUTING.en.md": "contributing.en.html",
    "SECURITY.md": "security.html",
    "SECURITY.en.md": "security.en.html",
    "CHANGELOG.md": "changelog.html",
    "CHANGELOG.en.md": "changelog.en.html",
    "CODE_OF_CONDUCT.md": "code-of-conduct.html",
    "CODE_OF_CONDUCT.en.md": "code-of-conduct.en.html",
    "index.html": "index.html",
    "index.en.html": "index.en.html",
}

def language_suffix(language: str) -> str:
    return ".en" if language == "en" else ""


def page_filename(page: Page, language: str) -> str:
    """英文页面在文件名里带 ``.en``，与仓库里其他文档的命名一致。"""
    return f"{Path(page.path).stem}{language_suffix(language)}.html"


def page_dir(page: Page, language: str) -> str:
    """页面所在子目录。站点根下的页面返回空串。"""
    parent = Path(page.path).parent
    return "" if str(parent) == "." else str(parent)


def page_depth(page: Page) -> int:
    """页面在站点里的层级。站点根下的页面是 0，``guide/`` 下的是 1。"""
    return len(Path(page.path).parts) - 1


def site_href(page: Page, language: str, depth: int) -> str:
    """指向站点内某个页面的相对链接。

    链接一律从站点根算起，再按当前页面所在的层级补上 ``../``。
    """
    filename = f"{Path(page.path).stem}{language_suffix(language)}.html"
    relative = f"{page_dir(page, language)}/{filename}".lstrip("/")
    return f"{'../' * depth}{relative}"


def build_sidebar(site: Site, current: Page, language: str, depth: int) -> list[dict]:
    """侧栏分组。每一组是一个标题加若干页面链接。"""
    groups: list[dict] = []
    for group, items in (
        ("overview", site.by_group("overview")),
        ("start", site.by_group("start")),
        ("guide", site.by_group("guide-index") + site.by_group("guide")),
        ("reference", site.by_group("reference")),
        ("project", site.by_group("project")),
    ):
        entries = []
        for page in items:
            entries.append(
                {
                    "label": page.nav_zh if language == "zh" else page.nav_en,
                    "href": site_href(page, language, depth),
                    "current": page.path == current.path,
                }
            )
        if entries:
            groups.append({"group": group, "entries": entries})
    return groups


def render_page(site: Site, page: Page, language: str) -> str:
    depth = page_depth(page)
    title = page.title_zh if language == "zh" else page.title_en
    if page.raw:
        body = page.body_zh if language == "zh" else page.body_en
        body = rewrite_links(body, depth, language)
        # 手写的片段用 section 的 id 与标题生成本页目录。
        outline = [
            (2, anchor, title)
            for anchor, title in re.findall(
                r'<section[^>]*id="([^"]+)"[^>]*>\s*'
                r'(?:<div class="section-head">\s*)?<h2>(.*?)</h2>',
                body,
                re.S,
            )
        ]
    else:
        body, outline = render_markdown(page.body_zh if language == "zh" else page.body_en)
        body = rewrite_links(body, depth, language)
        # 正文里的标题是二级起，页面标题单独渲染成一级，章标题的锚点落在它上面。
        # 一级标题与正文里同名的小节可能撞上，撞上时给页面标题换个锚点。
        anchor = github_slug(title)
        if anchor in {a for _, a, _ in outline}:
            anchor = f"page-{anchor}"
        heading = f'<h1 id="{anchor}">{title}</h1>\n'
        body = heading + body
        outline = [(1, anchor, title)] + outline

    # 同一组内按顺序找出上一篇和下一篇。首页是单独的一组，
    # 它的下一篇是「快速开始」；最后一组的下一篇为空。
    if page.group == "overview":
        start_pages = site.by_group("start")
        prev_page = None
        next_page = start_pages[0] if start_pages else None
    elif page.group == "guide-index":
        # 目录页的下一篇是第一章，上一篇是「快速开始」。
        chapters = site.by_group("guide")
        start_pages = site.by_group("start")
        prev_page = start_pages[0] if start_pages else None
        next_page = chapters[0] if chapters else None
    else:
        # 指南的各章按顺序排，上下页在目录页与各章之间接续。
        if page.group == "guide":
            siblings = site.by_group("guide-index") + site.by_group("guide")
        else:
            siblings = site.by_group(page.group)
        position = next(i for i, p in enumerate(siblings) if p.path == page.path)
        prev_page = siblings[position - 1] if position > 0 else None
        next_page = siblings[position + 1] if position + 1 < len(siblings) else None

    prefix = "../" * depth
    home = f"{prefix}index{language_suffix(language)}.html"

    labels = {
        "zh": {
            "home": "文档",
            "guide": "使用指南",
            "start": "开始",
            "reference": "参考",
            "project": "项目",
            "onthis": "本页内容",
            "prev": "上一篇",
            "next": "下一篇",
            "lang_link": "English",
            "lang_link_href": f"{prefix}index.en.html",
            "toc": "目录",
        },
        "en": {
            "home": "Docs",
            "guide": "The guide",
            "start": "Start",
            "reference": "Reference",
            "project": "Project",
            "onthis": "On this page",
            "prev": "Previous",
            "next": "Next",
            "lang_link": "中文",
            "lang_link_href": f"{prefix}index.html",
            "toc": "Contents",
        },
    }[language]

    group_labels = {
        "overview": labels["home"],
        "start": labels["start"],
        "guide": labels["guide"],
        "reference": labels["reference"],
        "project": labels["project"],
    }

    sidebar = []
    for group in build_sidebar(site, page, language, depth):
        # 指南目录页和指南各章归在同一组，这一组在它们之间保持展开。
        active = group["group"] == page.group or (
            page.group in ("guide", "guide-index") and group["group"] == "guide"
        )
        sidebar.append(
            f'      <details{" open" if active else ""}>\n'
            f'        <summary>{group_labels[group["group"]]}</summary>\n'
            + "".join(
                f'        <a class="{"current" if e["current"] else ""}" href="{e["href"]}">{e["label"]}</a>\n'
                for e in group["entries"]
            )
            + "      </details>"
        )

    toc = "".join(
        f'      <a href="#{anchor}">{outline_title}</a>\n'
        for level, anchor, outline_title in outline
        if level >= 2
    )

    def pager_link(target: Page | None, kind: str) -> str:
        if target is None:
            return f'        <span class="{kind} empty"></span>'
        href = site_href(target, language, depth)
        label = target.nav_zh if language == "zh" else target.nav_en
        return (
            f'        <a class="{kind}" href="{href}">\n'
            f'          <span class="label">{labels[kind]}</span>\n'
            f'          <span class="name">{label}</span>\n'
            f"        </a>"
        )

    page_title = f"{title} | Docorder"
    html_lang = "zh-CN" if language == "zh" else "en"
    toc_heading = labels["onthis"]
    body_class = "doc" if not page.raw else "overview"

    return f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
  <link rel="stylesheet" href="{prefix}intro.css"></head>
<body>
  <div class="top">
    <a class="brand" href="{home}">Docorder</a>
    <nav>
      <a href="{home}">{labels["home"]}</a>
      <a href="{site_href(site.by_group("guide-index")[0], language, depth)}">{labels["guide"]}</a>
    </nav>
    <a class="lang" href="{labels['lang_link_href']}">{labels["lang_link"]}</a>
  </div>

  <div class="shell">
    <aside class="sidebar">
      <input class="nav-toggle" type="checkbox" id="nav-toggle">
      <label class="nav-toggle-label" for="nav-toggle">{labels["toc"]}</label>
      <nav aria-label="{"文档导航" if language == "zh" else "Documentation navigation"}">
{chr(10).join(sidebar)}
      </nav>
    </aside>

    <main>
      <nav class="crumbs" aria-label="{"面包屑" if language == "zh" else "Breadcrumb"}">
        <a href="{home}">Docorder</a>
        <span aria-hidden="true">/</span>
        <span>{labels["home"]}</span>
        <span aria-hidden="true">/</span>
        <span>{title}</span>
      </nav>

      <article class="{body_class}">
{body}
      </article>

      <nav class="pager" aria-label="{"上下页" if language == "zh" else "Previous and next"}">
{pager_link(prev_page, "prev")}
{pager_link(next_page, "next")}
      </nav>
    </main>

    <aside class="toc">
      <h2>{toc_heading}</h2>
{toc}    </aside>
  </div>

  <footer>Docorder. Python 3.10+{"。许可见仓库中的 LICENSE。" if language == "zh" else ". License: LICENSE in the repository."}</footer>
</body>
</html>
"""

def main() -> None:
    site = build()

    build_guide_anchors(site)

    # 站点目录里全是产物，先清空再生成，章节改名后不会留下旧页面。
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)

    written = 0
    for language in LANGUAGES:
        for page in site.pages:
            target = SITE_DIR / page_dir(page, language) / page_filename(page, language)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render_page(site, page, language), encoding="utf-8")
            written += 1

    # 样式表也放进站点目录，站点因此可以整体拷走。
    (SITE_DIR / "intro.css").write_text(
        (DOCS_DIR / "intro.css").read_text(encoding="utf-8"), encoding="utf-8"
    )

    print(f"生成 {written} 个页面到 {SITE_DIR.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
