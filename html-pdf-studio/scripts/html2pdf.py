#!/usr/bin/env python3
"""html-pdf-studio: 把 HTML 渲染成 PDF 的"全功能"命令行工具。

设计要点
========
渲染交给本机无头 Chrome / Edge（CLI `--print-to-pdf`，零额外运行时依赖），
版面与产物加工交给 PyMuPDF。两条职责分离：

* **渲染层**：两种几何模式
    - ``continuous`` —— 渲染到一张超高"基岩页"，再用渲染级 bbox 量出真实内容
      底边，把 MediaBox/CropBox 裁到刚好。高度是"量出来再裁"，不是预测，
      因此精确。适合长滚动式网页（提案、落地页、报告）。
    - ``paged`` —— 按 A4/Letter 等标准纸张正常分页，受 ``@page`` 控制纸张、
      方向、页边距与缩放。适合文档类 HTML。

* **加工层**（两种模式都可用，全部由 PyMuPDF 完成，便于 CJK 字体与不透明度控制）：
    - 页眉/页脚/页码（模板含 ``{title} {page} {pages} {date}`` 占位符）
    - PDF 书签（`--bookmarks`）：按 HTML 标题写阅读器侧栏大纲，不改正文
    - PDF 目录（`--toc`）：剥离 HTML 文内目录，paged 模式插入带页码的目录页
    - 文字水印（斜向、可调不透明度）
    - PDF 元数据（标题/作者/主题/关键词）
    - 加密（AES-256，用户/所有者密码）
    - 多输入合并为一份 PDF
    - 输出缩略图自检 PNG

依赖：PyMuPDF（``pip install pymupdf``）+ 本机 Chrome 或 Edge。
"""

import argparse
import datetime as _dt
import html as _htmllib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

try:
    import pymupdf
except ImportError:  # PyMuPDF < 1.24 只暴露旧名 fitz
    import fitz as pymupdf

# ---------------------------------------------------------------------------
# 常量与可发现路径
# ---------------------------------------------------------------------------

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

# 常见 CJK 字体（用于页眉/页脚/水印里的中文，built-in Helvetica 不含汉字）
CJK_FONTS = [
    r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
    r"C:\Windows\Fonts\msyhl.ttc",
    r"C:\Windows\Fonts\simhei.ttf",    # 黑体
    r"C:\Windows\Fonts\simsun.ttc",    # 宋体
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
]

# 标准纸张的 CSS 尺寸（毫米）
PAPER_MM = {
    "A3": (297, 420), "A4": (210, 297), "A5": (148, 210),
    "LETTER": (215.9, 279.4), "LEGAL": (215.9, 355.6),
}

ACROBAT_LIMIT_PT = 14400  # ISO 32000-1 附录 C 的 Acrobat 实现上限；Chrome 可超出
MM_TO_PT = 72.0 / 25.4
PX_TO_PT = 72.0 / 96.0

REMOTE_URL = re.compile(r"^(?:https?:|data:|//|/)", re.I)
REL_REF = re.compile(r'(?:src|href|poster)\s*=\s*(["\'])([^"\']+)\1', re.I)
HEADING_RE = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")

# 文内目录块：仅 --toc（且未指定 --bookmarks）时从 HTML 剥离，改由 PDF 目录页呈现
HTML_TOC_BLOCK_RES = [
    re.compile(
        r"<nav\b[^>]*\bclass\s*=\s*[\"'][^\"']*\btoc\b[^\"']*[\"'][^>]*>.*?</nav>",
        re.I | re.S,
    ),
    re.compile(
        r"<(?:section|div|aside)\b[^>]*\b(?:id|class)\s*=\s*[\"'][^\"']*"
        r"\b(?:toc|table-of-contents|table_of_contents)\b[^\"']*[\"'][^>]*>"
        r".*?</(?:section|div|aside)>",
        re.I | re.S,
    ),
]
HTML_TOC_HIDE_CSS = """
  nav.toc, #toc, .toc, .table-of-contents, .table_of_contents,
  [class*="table-of-contents"], section.toc, aside.toc {
    display: none !important;
  }
"""

# 注入到 </head> 之前的打印样式。两种模式共享前半段（颜色保真、关动画、
# 显示 scroll-reveal、玻璃拟态降级），@page 由各模式分别拼接。
COMMON_PRINT_CSS = """
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    animation: none !important;
    transition: none !important;
    background-attachment: scroll !important;
  }
  [class*="fade"], [class*="reveal"], [class*="animate"], [class*="aos"],
  [data-aos] {
    opacity: 1 !important;
    transform: none !important;
    visibility: visible !important;
  }
  [style*="backdrop-filter"], .glass, [class*="glass"], [class*="blur"] {
    -webkit-backdrop-filter: none !important;
    backdrop-filter: none !important;
  }
"""


# ---------------------------------------------------------------------------
# 输入准备
# ---------------------------------------------------------------------------

def load_source(spec, workdir, idx):
    """把一个输入(本地文件或 URL)读成 HTML 文本，并返回其资源根目录。

    URL 输入直接抓取 HTML；相对资源仍由浏览器按原始 URL 解析（保留 <base>）。
    本地文件按所在目录解析相对资源。
    """
    if re.match(r"^https?://", spec, re.I):
        req = urllib.request.Request(spec, headers={"User-Agent": "html-pdf-studio"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
        try:
            html = raw.decode("utf-8")
        except UnicodeDecodeError:
            html = raw.decode("latin-1")
        # 注入 <base> 让相对资源回到原站点
        if "<base" not in html.lower() and "<head" in html.lower():
            html = re.sub(r"(<head[^>]*>)", r"\1<base href=\"%s\">" % spec,
                          html, count=1, flags=re.I)
        return html, None
    src = Path(spec)
    if not src.is_file():
        sys.exit(f"输入不存在: {spec}")
    return src.read_text(encoding="utf-8-sig"), src.parent


def stage_local_assets(html, src_dir, workdir):
    """把相对路径的本地资源复制进暂存目录。

    渲染发生在临时目录（ASCII 安全，规避 Chrome 在中文路径下写盘不稳定的问题），
    因此相对 img/link 路径需要一并搬过去，否则 404。
    """
    if src_dir is None:
        return
    src_root = src_dir.resolve()
    copied = set()
    for m in REL_REF.finditer(html):
        ref = m.group(2)
        if REMOTE_URL.match(ref) or ref in copied:
            continue
        asset = (src_dir / ref).resolve()
        if not asset.is_file():
            continue
        try:
            asset.relative_to(src_root)
        except ValueError:
            continue
        dest = workdir / ref
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset, dest)
        copied.add(ref)


def apply_replacements(html, replace_file):
    # utf-8-sig 容忍 BOM（PowerShell `Out-File -Encoding utf8` 会写 BOM）
    pairs = json.loads(Path(replace_file).read_text(encoding="utf-8-sig"))
    for old, new in pairs:  # 顺序敏感：更长/更具体的串放前面
        html = html.replace(old, new)
    return html


def check_forbidden(text, forbid_file, where):
    words = [w.strip() for w in
             Path(forbid_file).read_text(encoding="utf-8-sig").splitlines() if w.strip()]
    leaks = [w for w in words if w in text]
    if leaks:
        sys.exit(f"泄漏检测失败 [{where}]: {leaks}")
    return len(words)


# ---------------------------------------------------------------------------
# 浏览器渲染
# ---------------------------------------------------------------------------

def find_browser(explicit):
    if explicit:
        if Path(explicit).exists():
            return explicit
        sys.exit(f"指定的浏览器不存在: {explicit}")
    for p in BROWSERS:
        if Path(p).exists():
            return p
    found = (shutil.which("chrome") or shutil.which("chromium")
             or shutil.which("chromium-browser") or shutil.which("msedge"))
    if found:
        return found
    sys.exit("未找到 Chrome/Edge，请用 --chrome 指定可执行文件路径")


def align8(px):
    """对齐到 8px（8px = 6pt 整），规避 px→inch→pt 取整误差产生的幻影页。"""
    return max(8, int(round(px / 8.0)) * 8)


def build_page_css(mode, *, width, bedrock, paper, landscape, margin_mm, scale):
    """拼出 @page 规则。"""
    if mode == "continuous":
        # 单张超高页，零边距；宽高对齐 8px
        return f"@page {{ size: {align8(width)}px {align8(bedrock)}px; margin: 0; }}"
    # paged：标准纸张 + 毫米边距 + 方向
    pw, ph = PAPER_MM[paper.upper()]
    if landscape:
        pw, ph = ph, pw
    t, r, b, l = margin_mm
    return (f"@page {{ size: {pw}mm {ph}mm; "
            f"margin: {t}mm {r}mm {b}mm {l}mm; }}")


def remove_html_toc_blocks(html):
    """剥离 HTML 文内目录块，避免与 PDF 目录页重复。"""
    out = html
    for pat in HTML_TOC_BLOCK_RES:
        out = pat.sub("", out)
    return out


def inject_css(html, page_css, extra_css, *, hide_html_toc=False):
    toc_css = HTML_TOC_HIDE_CSS if hide_html_toc else ""
    block = (f"<style data-html-pdf-studio>\n{page_css}\n"
             f"{COMMON_PRINT_CSS}\n{toc_css}\n{extra_css}\n</style>\n</head>")
    return html.replace("</head>", block, 1)


def render(browser, html_path, pdf_path, width, virtual_time, scale):
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--hide-scrollbars",
        f"--window-size={width},2000",
        f"--virtual-time-budget={virtual_time}",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf-scale={scale}" if abs(scale - 1.0) > 1e-6 else "--no-first-run",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    subprocess.run(cmd, check=True, timeout=300,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------------------
# continuous 模式裁切
# ---------------------------------------------------------------------------

def content_bottom_vector(page):
    """用渲染级 bbox 日志求内容底边（pt，自页顶起算）。

    get_bboxlog() 覆盖文本/图像/矢量路径并展开 Form XObject，是唯一不漏的接口。
    跳过 ignore-text（不可见文本）与高度 ≥97% 页高的填充（铺满基岩页的页面背景）。
    """
    page_h = page.rect.height
    bottom = None
    for kind, bbox in page.get_bboxlog():
        if kind == "ignore-text":
            continue
        r = pymupdf.Rect(bbox)
        if r.is_empty or r.is_infinite or r.height >= 0.97 * page_h:
            continue
        bottom = r.y1 if bottom is None else max(bottom, r.y1)
    try:
        for annot in page.annots():
            bottom = annot.rect.y1 if bottom is None else max(bottom, annot.rect.y1)
    except TypeError:
        pass
    return bottom


def content_bottom_pixel(page, dpi=24, stdev_threshold=3.0):
    """兜底：栅格化后自底向上扫描，找第一行"水平方差超阈值"的像素行。

    垂直渐变背景在水平方向均匀（方差≈0），真正的内容（文字/卡片/分隔线）会
    打破水平均匀性。当矢量模式把装饰几何误判为内容时改用本法。
    """
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    w, h, buf = pix.width, pix.height, pix.samples
    threshold = stdev_threshold ** 2
    for row in range(h - 1, -1, -1):
        line = buf[row * w:(row + 1) * w]
        mean = sum(line) / w
        if sum((v - mean) ** 2 for v in line) / w > threshold:
            return (row + 1) / dpi * 72.0
    return None


def crop_to_content(doc, padding_px, crop_mode):
    page = doc[0]
    bottom = None
    if crop_mode != "pixel":
        bottom = content_bottom_vector(page)
    if bottom is None:
        bottom = content_bottom_pixel(page)
    if bottom is None:
        sys.exit("无法在页面上定位任何内容")
    new_h = min(page.rect.height, bottom + padding_px * PX_TO_PT)
    # 在原始 PDF 坐标(y-up)里同时改写 MediaBox 与 CropBox，避开 PyMuPDF
    # set_mediabox 会删 CropBox 的副作用，也消除"有的看 MediaBox、有的看 CropBox"
    # 的查看器歧义。
    mb = page.mediabox
    box = f"[{mb.x0:.2f} {mb.y1 - new_h:.2f} {mb.x1:.2f} {mb.y1:.2f}]"
    doc.xref_set_key(page.xref, "MediaBox", box)
    doc.xref_set_key(page.xref, "CropBox", box)
    normalize_page_origin(doc)
    return new_h


def normalize_page_origin(doc):
    """裁切后把页面压平到 MediaBox [0,0,w,h]。

    crop_to_content 只改页面框、不移动内容流，MediaBox.y0 常为非零；书签
    dest 会写成 mediabox.y0 + y，WPS 等阅读器按 0 起算时会全部跳到页首。
    用 show_pdf_page 把可见区重绘到原点，search_for 与书签坐标即一致。
    """
    if doc.page_count != 1:
        return
    page = doc[0]
    mb = page.mediabox
    if abs(mb.x0) < 0.01 and abs(mb.y0) < 0.01:
        return
    visible = page.rect
    w, h = visible.width, visible.height
    flat = pymupdf.open()
    fp = flat.new_page(width=w, height=h)
    fp.show_pdf_page(fp.rect, doc, 0, clip=visible)
    doc.delete_page(0)
    doc.insert_pdf(flat)
    flat.close()


def want_pdf_toc(args):
    """是否生成 PDF 目录页（剥离 HTML 文内目录）。--bookmarks 优先时返回 False。"""
    return args.toc and not args.bookmarks


def render_one(browser, html, src_dir, workdir, idx, args, page_css_kwargs):
    """渲染单个输入为一份 PDF（已按模式裁切/分页），返回打开的 doc。"""
    extra_css = ""
    if args.extra_css:
        extra_css = Path(args.extra_css).read_text(encoding="utf-8-sig")
    if "</head>" not in html:
        sys.exit(f"输入 #{idx} 缺少 </head>，无法注入打印 CSS")

    hide_html_toc = want_pdf_toc(args)
    stage_local_assets(html, src_dir, workdir)
    tmp_pdf = workdir / f"render-{idx}.pdf"

    if args.mode == "continuous":
        bedrock = align8(args.bedrock)
        for attempt in range(args.max_retries + 1):
            page_css = build_page_css("continuous",
                                      bedrock=bedrock, **page_css_kwargs)
            injected = inject_css(html, page_css, extra_css,
                                  hide_html_toc=hide_html_toc)
            tmp_html = workdir / f"in-{idx}.html"
            tmp_html.write_text(injected, encoding="utf-8")
            render(browser, tmp_html, tmp_pdf, args.width, args.virtual_time, args.scale)
            doc = pymupdf.open(tmp_pdf)
            if doc.page_count == 1:
                break
            print(f"内容溢出 {bedrock}px 基岩页（{doc.page_count} 页），高度翻倍重试")
            doc.close()
            bedrock = align8(bedrock * 2)
        else:
            sys.exit(f"重试 {args.max_retries} 次后仍分页；请手动调大 --bedrock")
        crop_to_content(doc, args.padding, args.crop)
        return doc

    # paged 模式：正常分页，不裁切
    page_css = build_page_css("paged", bedrock=0, **page_css_kwargs)
    injected = inject_css(html, page_css, extra_css, hide_html_toc=hide_html_toc)
    tmp_html = workdir / f"in-{idx}.html"
    tmp_html.write_text(injected, encoding="utf-8")
    render(browser, tmp_html, tmp_pdf, args.width, args.virtual_time, args.scale)
    return pymupdf.open(tmp_pdf)


# ---------------------------------------------------------------------------
# 后期加工（页眉页脚 / 水印 / TOC / 元数据 / 加密）
# ---------------------------------------------------------------------------

def find_cjk_font():
    for p in CJK_FONTS:
        if Path(p).exists():
            return p
    return None


def _has_cjk(text):
    return any("\u4e00" <= ch <= "\u9fff" or "\u3040" <= ch <= "\u30ff"
               for ch in text)


def _make_font(text):
    """文本含 CJK 时加载系统字体，否则用内置 Helvetica。返回 Font 对象。"""
    if _has_cjk(text):
        fp = find_cjk_font()
        if fp:
            return pymupdf.Font(fontfile=fp)
    return pymupdf.Font("helv")


def expand_tokens(template, title, page_no, total):
    today = _dt.date.today().isoformat()
    return (template.replace("{title}", title or "")
                    .replace("{page}", str(page_no))
                    .replace("{pages}", str(total))
                    .replace("{date}", today))


def stamp_header_footer(doc, header, footer, title, font_size, margin_mm):
    if not header and not footer:
        return
    sample = (header or "") + (footer or "") + (title or "")
    font = _make_font(sample)
    total = doc.page_count
    top_pt = max(margin_mm[0] * MM_TO_PT * 0.45, font_size + 4)
    bot_pt = max(margin_mm[2] * MM_TO_PT * 0.45, font_size + 4)
    for i, page in enumerate(doc, start=1):
        rect = page.rect
        if header:
            txt = expand_tokens(header, title, i, total)
            _place_line(page, txt, rect, top_pt, font, font_size, top=True)
        if footer:
            txt = expand_tokens(footer, title, i, total)
            _place_line(page, txt, rect, bot_pt, font, font_size, top=False)


def _place_line(page, text, rect, y_pt, font, size, top):
    """在页面顶部/底部放一行文字。支持 ``左|中|右`` 三段对齐语法。"""
    parts = text.split("|")
    if len(parts) == 1:
        segments = [(parts[0], 0.5)]
    elif len(parts) == 2:
        segments = [(parts[0], 0.0), (parts[1], 1.0)]
    else:
        segments = [(parts[0], 0.0), (parts[1], 0.5), (parts[2], 1.0)]
    y = y_pt if top else rect.height - y_pt
    tw = pymupdf.TextWriter(rect, color=(0.4, 0.4, 0.4))
    wrote = False
    for seg, anchor in segments:
        seg = seg.strip()
        if not seg:
            continue
        sw = font.text_length(seg, fontsize=size)
        x = (rect.width - sw) * anchor
        x = min(max(x, 4), max(4, rect.width - sw - 4))
        tw.append((x, y), seg, font=font, fontsize=size)
        wrote = True
    if wrote:
        tw.write_text(page)


def stamp_watermark(doc, text, opacity, font_size):
    font = _make_font(text)
    for page in doc:
        rect = page.rect
        tw = pymupdf.TextWriter(rect, opacity=opacity, color=(0.5, 0.5, 0.5))
        sw = font.text_length(text, fontsize=font_size)
        cx, cy = rect.width / 2, rect.height / 2
        # 文本基线起点放在中心左侧，再绕中心旋转 45° 形成对角水印
        tw.append((cx - sw / 2, cy), text, font=font, fontsize=font_size)
        pivot = pymupdf.Point(cx, cy)
        mat = pymupdf.Matrix(45)
        tw.write_text(page, morph=(pivot, mat))


def extract_headings(html, depth):
    """从 HTML 抽取 h1..hN 标题（已剥离文内目录块）。"""
    cleaned = remove_html_toc_blocks(html)
    headings = []
    for m in HEADING_RE.finditer(cleaned):
        level = int(m.group(1))
        if level > depth:
            continue
        raw = TAG_RE.sub("", m.group(2))
        text = _htmllib.unescape(raw).strip()
        text = re.sub(r"\s+", " ", text)
        if text:
            headings.append((level, text))
    return headings


def _pick_heading_y(rects, min_y):
    """多命中时取阅读顺序上位于上一书签之后的第一个（避免文内交叉引用抢先）。"""
    if not rects:
        return None
    ordered = sorted(rects, key=lambda r: r.y0)
    for r in ordered:
        if r.y0 >= min_y - 0.5:
            return r.y0
    return ordered[-1].y0


def locate_headings(doc, headings):
    """在 PDF 文本层定位标题，返回 [(level, text, page_0based, y), ...]。"""
    located = []
    cursor_page = 0
    min_y = 0.0
    for level, text in headings:
        found = None
        probe = text[:40]
        for pno in range(cursor_page, doc.page_count):
            rects = doc[pno].search_for(probe, quads=False)
            floor = min_y if pno == cursor_page else 0.0
            y = _pick_heading_y(rects, floor)
            if y is not None:
                found = (pno, y)
                cursor_page = pno
                min_y = y
                break
        if found is None:
            for pno in range(doc.page_count):
                rects = doc[pno].search_for(probe, quads=False)
                y = _pick_heading_y(rects, min_y)
                if y is not None:
                    found = (pno, y)
                    cursor_page = pno
                    min_y = y
                    break
        if found is None:
            found = (cursor_page, min_y)
        pno, y = found
        located.append((level, text, pno, y))
    return located


def apply_bookmarks(doc, located, page_offset):
    """按已定位标题写入书签大纲，page_offset 为文前插入的目录页数。"""
    toc = []
    for level, text, pno, y in located:
        toc.append([level, text, pno + 1 + page_offset,
                    {"kind": 1, "to": pymupdf.Point(0, y)}])
    doc.set_toc(toc)
    return len(toc)


def _toc_lines_per_page(page_h, margin_top, margin_bottom, line_h):
    usable = page_h - margin_top - margin_bottom
    return max(1, int(usable / line_h))


def _draw_toc_line(page, font, size, x_left, x_right, y, level, text, page_no,
                   indent_pt):
    """绘制一行目录：缩进标题 + 点线 + 右对齐页码。"""
    x = x_left + (level - 1) * indent_pt
    num = str(page_no)
    num_w = font.text_length(num, fontsize=size)
    max_text_w = x_right - num_w - 8 - x
    display = text
    while display and font.text_length(display + "…", fontsize=size) > max_text_w:
        display = display[:-1]
    if display != text and display:
        display += "…"
    tw = pymupdf.TextWriter(page.rect, color=(0.1, 0.1, 0.1))
    tw.append((x, y), display, font=font, fontsize=size)
    tw.write_text(page)
    # 点引导符
    text_w = font.text_length(display, fontsize=size)
    dot_x0 = x + text_w + 4
    dot_x1 = x_right - num_w - 4
    if dot_x1 > dot_x0 + 6:
        dot = "."
        dot_w = font.text_length(dot, fontsize=size)
        n_dots = max(3, int((dot_x1 - dot_x0) / dot_w))
        tw2 = pymupdf.TextWriter(page.rect, color=(0.55, 0.55, 0.55))
        tw2.append((dot_x0, y), dot * n_dots, font=font, fontsize=size)
        tw2.write_text(page)
    tw3 = pymupdf.TextWriter(page.rect, color=(0.1, 0.1, 0.1))
    tw3.append((x_right - num_w, y), num, font=font, fontsize=size)
    tw3.write_text(page)


def insert_pdf_toc_pages(doc, located, title="目录", *, title_size=20.0,
                         body_size=11.0, line_h=17.0, indent_pt=14.0):
    """在文前插入 PDF 目录页（paged 模式）。返回插入的页数。

    located: [(level, text, page_0based, y), ...]，定位基于插入目录页之前。
    目录行上的页码 = 正文中的 1-based 页码 + 将插入的目录页数。
    """
    if not located or doc.page_count == 0:
        return 0

    ref = doc[0].rect
    w, h = ref.width, ref.height
    margin_x = 56.0
    margin_top = 64.0
    margin_bottom = 56.0
    x_left, x_right = margin_x, w - margin_x

    # 估算所需目录页数（标题占 2 行 + 每条目 1 行）
    lpp = _toc_lines_per_page(h, margin_top, margin_bottom, line_h)
    lines_needed = 2 + len(located)
    num_pages = max(1, (lines_needed + lpp - 1) // lpp)

    for _ in range(num_pages):
        doc.insert_page(0, width=w, height=h)

    sample = title + "".join(t for _, t, _, _ in located)
    font = _make_font(sample)
    y = margin_top + title_size

    # 目录标题
    title_w = font.text_length(title, fontsize=title_size)
    page0 = doc[0]
    tw_title = pymupdf.TextWriter(page0.rect, color=(0.05, 0.05, 0.05))
    tw_title.append(((w - title_w) / 2, y), title, font=font, fontsize=title_size)
    tw_title.write_text(page0)
    y += line_h * 1.6

    page_idx = 0
    for level, text, _pno, _y in located:
        if y + line_h > h - margin_bottom:
            page_idx += 1
            if page_idx >= num_pages:
                break
            y = margin_top
        page_no = _pno + 1 + num_pages  # 最终文档中的 1-based 页码
        _draw_toc_line(doc[page_idx], font, body_size, x_left, x_right, y,
                       level, text, page_no, indent_pt)
        y += line_h

    return num_pages


def build_bookmarks(doc, html, depth):
    """仅写 PDF 书签大纲：不改正文、不插目录页。返回书签条数。"""
    headings = extract_headings(html, depth)
    if not headings:
        return 0
    located = locate_headings(doc, headings)
    return apply_bookmarks(doc, located, 0)


def build_toc(doc, html, depth, *, mode="continuous", toc_title="目录"):
    """生成 PDF 目录页：剥离 HTML 文内目录；paged 插入目录页；同步写书签。返回 (书签数, 目录页数)。"""
    headings = extract_headings(html, depth)
    if not headings:
        return 0, 0

    located = locate_headings(doc, headings)
    toc_pages = 0
    if mode == "paged":
        toc_pages = insert_pdf_toc_pages(doc, located, title=toc_title)
    bookmark_n = apply_bookmarks(doc, located, toc_pages)
    return bookmark_n, toc_pages


def make_preview(doc, out_png, dpi=60):
    """把首页渲染成缩略图，便于肉眼自检版面。超高页会自动降 dpi。"""
    page = doc[0]
    use_dpi = dpi
    if page.rect.height * dpi / 72.0 > 12000:  # 控制像素高度
        use_dpi = max(8, int(12000 * 72.0 / page.rect.height))
    doc[0].get_pixmap(dpi=use_dpi).save(out_png)
    return use_dpi


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def parse_margin(spec):
    nums = [float(x) for x in re.split(r"[ ,]+", spec.strip()) if x]
    if len(nums) == 1:
        return (nums[0],) * 4
    if len(nums) == 2:
        return (nums[0], nums[1], nums[0], nums[1])
    if len(nums) == 4:
        return tuple(nums)
    sys.exit("--margin 需要 1/2/4 个数字（上 右 下 左，单位 mm）")


def main():
    ap = argparse.ArgumentParser(
        description="HTML -> PDF 全功能工具（连续单页 / 标准分页，含页眉页脚、目录、水印、加密）")
    ap.add_argument("inputs", nargs="+", help="一个或多个 HTML 文件或 http(s) URL；多个输入合并为一份 PDF")
    ap.add_argument("-o", "--output", required=True, help="输出 PDF 路径")
    ap.add_argument("--mode", choices=["continuous", "paged"], default="continuous",
                    help="continuous=单张长页(默认)；paged=标准纸张分页")

    # paged 几何
    ap.add_argument("--paper", default="A4", help="纸张(paged)：A3/A4/A5/Letter/Legal，默认 A4")
    ap.add_argument("--landscape", action="store_true", help="横向(paged)")
    ap.add_argument("--margin", default="16 16 18 16", help="页边距 mm(paged)：'上 右 下 左' 或单值，默认 '16 16 18 16'")

    # continuous 几何
    ap.add_argument("--width", type=int, default=1280, help="页面宽度(CSS px)，默认 1280，对齐 8px")
    ap.add_argument("--bedrock", type=int, default=18000, help="基岩页初始高度 px(continuous)，溢出自动翻倍")
    ap.add_argument("--padding", type=int, default=32, help="内容下方保留留白 px(continuous)，默认 32")
    ap.add_argument("--crop", choices=["vector", "pixel"], default="vector",
                    help="内容底边检测(continuous)：vector(默认)/pixel")

    # 渲染
    ap.add_argument("--scale", type=float, default=1.0, help="打印缩放 0.1~2，默认 1.0")
    ap.add_argument("--extra-css", help="追加到注入打印样式后的 CSS 文件(断点锁定/玻璃降级等)")
    ap.add_argument("--virtual-time", type=int, default=10000, help="Chrome --virtual-time-budget 毫秒，默认 10000")
    ap.add_argument("--chrome", help="显式指定浏览器可执行文件")
    ap.add_argument("--max-retries", type=int, default=2, help="continuous 溢出时基岩翻倍次数，默认 2")

    # 加工
    ap.add_argument("--title", help="PDF 元数据标题，也用于页眉页脚 {title}")
    ap.add_argument("--author", help="PDF 元数据作者")
    ap.add_argument("--subject", help="PDF 元数据主题")
    ap.add_argument("--keywords", help="PDF 元数据关键词")
    ap.add_argument("--header", help="页眉模板，支持 {title}{page}{pages}{date} 与 '左|中|右' 三段对齐")
    ap.add_argument("--footer", help="页脚模板，同上")
    ap.add_argument("--hf-font-size", type=float, default=9.0, help="页眉页脚字号 pt，默认 9")
    ap.add_argument("--bookmarks", action="store_true",
                    help="仅生成 PDF 书签大纲（阅读器侧栏），不改正文、不插目录页；优先于 --toc")
    ap.add_argument("--toc", action="store_true",
                    help="生成 PDF 目录页：剥离 HTML 文内目录，插入目录页(paged)并写书签")
    ap.add_argument("--toc-depth", type=int, default=3,
                    help="书签/目录的标题层级深度 h1..hN，默认 3")
    ap.add_argument("--toc-title", default="目录", help="PDF 目录页标题，默认「目录」")
    ap.add_argument("--watermark", help="文字水印(斜向平铺)")
    ap.add_argument("--watermark-opacity", type=float, default=0.12, help="水印不透明度，默认 0.12")
    ap.add_argument("--watermark-size", type=float, default=60.0, help="水印字号 pt，默认 60")
    ap.add_argument("--password", help="打开密码(用户密码)，启用 AES-256 加密")
    ap.add_argument("--owner-password", help="所有者密码(权限口令)，默认同 --password")

    # 校验 / 脱敏 / 自检
    ap.add_argument("--replace", help="JSON 文件 [[old,new],...]，渲染前替换(脱敏)")
    ap.add_argument("--forbid", help="逐行禁词表；HTML 或最终 PDF 文本里命中即中止")
    ap.add_argument("--preview", action="store_true", help="额外导出 <output>.png 首页缩略图自检")
    ap.add_argument("--keep-temp", action="store_true")
    args = ap.parse_args()
    if args.bookmarks and args.toc:
        print("提示: 同时指定 --bookmarks 与 --toc，按 --bookmarks 处理（不插目录页、保留 HTML 文内目录）")

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    margin_mm = parse_margin(args.margin)
    args.scale = min(max(args.scale, 0.1), 2.0)
    browser = find_browser(args.chrome)

    page_css_kwargs = dict(width=args.width, paper=args.paper,
                           landscape=args.landscape, margin_mm=margin_mm,
                           scale=args.scale)

    # Chrome 在非 ASCII 路径下写 PDF 不稳定，所有中间产物落在 TEMP
    workdir = Path(tempfile.gettempdir()) / f"html-pdf-studio-{uuid.uuid4().hex[:8]}"
    workdir.mkdir()

    try:
        merged = pymupdf.open()
        first_html_for_outline = None
        for idx, spec in enumerate(args.inputs):
            html, src_dir = load_source(spec, workdir, idx)
            if args.replace:
                html = apply_replacements(html, args.replace)
            if want_pdf_toc(args):
                html = remove_html_toc_blocks(html)
            if args.forbid:
                n = check_forbidden(html, args.forbid, f"输入#{idx} HTML(替换后)")
                print(f"禁词检测(html#{idx}): {n} 词，干净")
            if first_html_for_outline is None:
                first_html_for_outline = html
            doc = render_one(browser, html, src_dir, workdir, idx, args, page_css_kwargs)
            merged.insert_pdf(doc)
            doc.close()

        if merged.page_count == 0:
            sys.exit("没有渲染出任何页面")

        # 元数据
        meta = {}
        if args.title:
            meta["title"] = args.title
        if args.author:
            meta["author"] = args.author
        if args.subject:
            meta["subject"] = args.subject
        if args.keywords:
            meta["keywords"] = args.keywords
        if meta:
            merged.set_metadata(meta)

        bookmark_n = 0
        toc_pages = 0
        if args.bookmarks:
            bookmark_n = build_bookmarks(
                merged, first_html_for_outline, args.toc_depth)
        elif args.toc:
            bookmark_n, toc_pages = build_toc(
                merged, first_html_for_outline, args.toc_depth,
                mode=args.mode, toc_title=args.toc_title,
            )

        # 页眉页脚 / 水印
        stamp_header_footer(merged, args.header, args.footer,
                            args.title, args.hf_font_size, margin_mm)
        if args.watermark:
            stamp_watermark(merged, args.watermark,
                            args.watermark_opacity, args.watermark_size)

        # 保存（按需加密）
        final = workdir / "final.pdf"
        save_kw = dict(garbage=4, deflate=True)
        if args.password or args.owner_password:
            save_kw.update(
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                user_pw=args.password or "",
                owner_pw=args.owner_password or args.password or "",
                permissions=int(pymupdf.PDF_PERM_PRINT | pymupdf.PDF_PERM_COPY),
            )
        merged.save(final, **save_kw)

        # 禁词复核（针对最终 PDF 文本层；加密时跳过文本提取）
        if args.forbid and not (args.password or args.owner_password):
            check = pymupdf.open(final)
            text = "".join(p.get_text() for p in check)
            check_forbidden(text, args.forbid, "最终 PDF 文本")
            check.close()
            print("禁词检测(pdf): 干净")

        dest = Path(args.output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(final, dest)

        # 自检缩略图
        if args.preview:
            png = dest.with_suffix(".png")
            chk = pymupdf.open(dest) if not (args.password or args.owner_password) else merged
            used = make_preview(chk, str(png))
            if chk is not merged:
                chk.close()
            print(f"预览图: {png} (dpi={used})")

        # 汇报
        page0 = merged[0].rect
        size_kb = dest.stat().st_size / 1024
        print(f"OK {merged.page_count} 页, 首页 {page0.width:.0f}x{page0.height:.0f}pt, "
              f"{size_kb:.0f} KB, 模式={args.mode}"
              + (f", 目录页 {toc_pages}" if toc_pages else "")
              + (f", 书签 {bookmark_n} 条" if bookmark_n else "")
              + f" -> {dest}")
        if args.mode == "continuous" and page0.height > ACROBAT_LIMIT_PT:
            print(f"提示: 页高 {page0.height:.0f}pt 超过 14400pt 的 Acrobat 上限；"
                  f"Chrome/Firefox/微信预览正常，旧版 Acrobat 可能拒绝")
        merged.close()
    finally:
        if args.keep_temp:
            print(f"保留临时目录: {workdir}")
        else:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
