# -*- coding: utf-8 -*-
"""Markdown -> 规范、美观、可读的 Word(.docx) 转换器。

用法:
    python md_to_docx.py <input.md> [output.docx]

特性:
- 中文字体规范: 标题黑体 / 正文宋体 / 引用楷体 / 代码 Consolas。
- 表格列宽按各列内容自适应(CJK 感知宽度), 描述列自动更宽。
- 表头深色底纹白字、隔行斑马纹、"字段/说明"两列表左列高亮。
- 标题分级配色与装饰线、引用提示框、有序/无序列表、围栏代码块、图片嵌入。
- 表头跨页重复、标题与后段同页、页脚页码等可读性增强。

依赖: python-docx (pip install python-docx)
"""
import os
import re
import sys

from docx import Document
from docx.shared import Pt, RGBColor, Cm, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ---------------------------------------------------------------------------
# 视觉规范(集中配置, 便于统一调整)
# ---------------------------------------------------------------------------
COLOR_PRIMARY = RGBColor(0x1F, 0x49, 0x7D)   # 深蓝: 一级/章节标题
COLOR_ACCENT = RGBColor(0x2E, 0x74, 0xB5)    # 亮蓝: 子标题
COLOR_TEXT = RGBColor(0x33, 0x33, 0x33)      # 正文
COLOR_MUTED = RGBColor(0x44, 0x55, 0x66)     # 引用/弱化
COLOR_CODE = RGBColor(0xA3, 0x1D, 0x11)      # 内联代码
COLOR_LINK = RGBColor(0x1A, 0x5F, 0xB4)      # 链接
COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)

HEX_HEADER = "1F497D"     # 表头填充
HEX_LABEL = "DCE6F1"      # 字段列填充
HEX_STRIPE = "F2F6FB"     # 斑马纹 / 引用底纹
HEX_CODEBG = "F5F5F5"     # 代码块底纹
HEX_BORDER = "B7C6D9"     # 表格边框
HEX_PRIMARY = "1F497D"
HEX_ACCENT = "2E74B5"

FONT_HEI = "黑体"
FONT_SONG = "宋体"
FONT_KAI = "楷体"
FONT_MONO = "Consolas"

BASE_SIZE = 10.5          # 正文字号(pt)
TABLE_SIZE = 10           # 表格字号(pt)

INLINE_RE = re.compile(r'(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`|\[[^\]]+?\]\([^)]+?\))')


# ---------------------------------------------------------------------------
# 底层 OOXML 辅助
# ---------------------------------------------------------------------------
def set_run_font(run, cn=FONT_SONG, en=FONT_SONG, size=None, bold=None,
                 color=None, italic=None, underline=None):
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if underline is not None:
        run.font.underline = underline
    if color is not None:
        run.font.color.rgb = color
    run.font.name = en
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.append(rfonts)
    rfonts.set(qn('w:ascii'), en)
    rfonts.set(qn('w:hAnsi'), en)
    rfonts.set(qn('w:eastAsia'), cn)


def shade_cell(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    tcpr.append(shd)


def set_cell_margins(cell, top=60, bottom=60, left=110, right=110):
    tcpr = cell._tc.get_or_add_tcPr()
    m = OxmlElement('w:tcMar')
    for tag, val in (('top', top), ('bottom', bottom),
                     ('start', left), ('end', right),
                     ('left', left), ('right', right)):
        e = OxmlElement(f'w:{tag}')
        e.set(qn('w:w'), str(val))
        e.set(qn('w:type'), 'dxa')
        m.append(e)
    tcpr.append(m)


def set_table_borders(table, color=HEX_BORDER, sz=6):
    tblpr = table._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        e = OxmlElement(f'w:{edge}')
        e.set(qn('w:val'), 'single')
        e.set(qn('w:sz'), str(sz))
        e.set(qn('w:space'), '0')
        e.set(qn('w:color'), color)
        borders.append(e)
    tblpr.append(borders)


def set_col_widths(table, widths_cm):
    """固定各列宽度(需配合关闭 autofit 才稳定生效)。"""
    table.autofit = False
    table.allow_autofit = False
    # 表级 tblLayout=fixed
    tblpr = table._tbl.tblPr
    layout = OxmlElement('w:tblLayout')
    layout.set(qn('w:type'), 'fixed')
    tblpr.append(layout)
    grid = table._tbl.find(qn('w:tblGrid'))
    if grid is not None:
        for gc, w in zip(grid.findall(qn('w:gridCol')), widths_cm):
            gc.set(qn('w:w'), str(int(Cm(w).twips)))
    for row in table.rows:
        for i, w in enumerate(widths_cm):
            row.cells[i].width = Cm(w)


def mark_header_row(row):
    """表头行跨页重复。"""
    trpr = row._tr.get_or_add_trPr()
    th = OxmlElement('w:tblHeader')
    th.set(qn('w:val'), 'true')
    trpr.append(th)


def keep_with_next(paragraph):
    paragraph.paragraph_format.keep_with_next = True


def add_par_border(paragraph, edge='left', color=HEX_ACCENT, sz=24, space=8):
    ppr = paragraph.paragraph_format.element.get_or_add_pPr()
    pbdr = ppr.find(qn('w:pBdr'))
    if pbdr is None:
        pbdr = OxmlElement('w:pBdr')
        ppr.append(pbdr)
    e = OxmlElement(f'w:{edge}')
    e.set(qn('w:val'), 'single')
    e.set(qn('w:sz'), str(sz))
    e.set(qn('w:space'), str(space))
    e.set(qn('w:color'), color)
    pbdr.append(e)


def add_par_shading(paragraph, fill):
    ppr = paragraph.paragraph_format.element.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), fill)
    ppr.append(shd)


def add_page_number_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for kind, text in (('begin', None), ('instr', 'PAGE'), ('end', None)):
        run = p.add_run()
        if kind == 'instr':
            fld = OxmlElement('w:instrText')
            fld.set(qn('xml:space'), 'preserve')
            fld.text = ' PAGE '
            run._r.append(fld)
        else:
            fc = OxmlElement('w:fldChar')
            fc.set(qn('w:fldCharType'), kind)
            run._r.append(fc)
        set_run_font(run, cn=FONT_SONG, en=FONT_SONG, size=9, color=COLOR_MUTED)


# ---------------------------------------------------------------------------
# 内联解析与宽度测量
# ---------------------------------------------------------------------------
def display_width(text):
    """CJK/全角计 2, 其余计 1。"""
    w = 0
    for ch in text:
        w += 2 if ord(ch) > 0x2E7F else 1
    return w


def strip_inline(text):
    """去除内联标记后用于宽度估算的纯文本。"""
    t = re.sub(r'\[([^\]]+?)\]\([^)]+?\)', r'\1', text)
    t = t.replace('**', '').replace('`', '')
    t = re.sub(r'(?<!\*)\*(?!\*)', '', t)
    return t


def add_inline(paragraph, text, size=BASE_SIZE, color=COLOR_TEXT, cn=FONT_SONG):
    """解析 **加粗** / *斜体* / `代码` / [文本](url)。"""
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            r = paragraph.add_run(part[2:-2])
            set_run_font(r, cn=cn, en=cn, size=size, bold=True, color=color)
        elif part.startswith('`') and part.endswith('`'):
            r = paragraph.add_run(part[1:-1])
            set_run_font(r, cn=FONT_MONO, en=FONT_MONO, size=size - 1,
                         color=COLOR_CODE)
        elif part.startswith('*') and part.endswith('*') and len(part) > 2:
            r = paragraph.add_run(part[1:-1])
            set_run_font(r, cn=cn, en=cn, size=size, italic=True, color=color)
        elif part.startswith('[') and '](' in part:
            m = re.match(r'\[([^\]]+?)\]\(([^)]+?)\)', part)
            r = paragraph.add_run(m.group(1))
            set_run_font(r, cn=cn, en=cn, size=size, color=COLOR_LINK,
                         underline=True)
        else:
            r = paragraph.add_run(part)
            set_run_font(r, cn=cn, en=cn, size=size, color=color)


def compute_col_widths(rows, total_cm, min_cm=1.4, cap_units=52):
    """按各列内容的最大显示宽度成比例分配列宽(内容自适应)。"""
    ncol = max(len(r) for r in rows)
    nat = [0] * ncol
    for r in rows:
        for c in range(ncol):
            if c >= len(r):
                continue
            val = strip_inline(r[c])
            lines = re.split(r'<br\s*/?>', val)
            w = max((display_width(x) for x in lines), default=0)
            nat[c] = max(nat[c], min(w, cap_units))
    s = sum(nat)
    if s == 0:
        return [total_cm / ncol] * ncol
    widths = [max(min_cm, total_cm * n / s) for n in nat]
    scale = total_cm / sum(widths)
    return [w * scale for w in widths]


# ---------------------------------------------------------------------------
# 块级解析
# ---------------------------------------------------------------------------
def parse_table(lines, i):
    rows = []
    while i < len(lines) and lines[i].strip().startswith('|'):
        raw = lines[i].strip().strip('|')
        cells = [c.strip() for c in raw.split('|')]
        if not re.match(r'^[\s:\-]+$', ''.join(cells)):
            rows.append(cells)
        i += 1
    return rows, i


def content_width_cm(section):
    return (section.page_width - section.left_margin -
            section.right_margin) / 360000.0  # EMU -> cm


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def build(src_path, out_path):
    with open(src_path, encoding='utf-8') as f:
        lines = f.read().replace('\r\n', '\n').split('\n')

    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(2.5)
    sec.bottom_margin = Cm(2.3)
    sec.left_margin = Cm(2.8)
    sec.right_margin = Cm(2.8)
    add_page_number_footer(sec)

    normal = doc.styles['Normal']
    normal.font.name = FONT_SONG
    normal.font.size = Pt(BASE_SIZE)
    normal._element.get_or_add_rPr().get_or_add_rFonts().set(
        qn('w:eastAsia'), FONT_SONG)

    cwidth = content_width_cm(sec)

    i, n = 0, len(lines)
    while i < n:
        line = lines[i].rstrip()
        s = line.strip()

        if not s or s == '---' or s == '***':
            i += 1
            continue

        # 围栏代码块
        if s.startswith('```'):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith('```'):
                code.append(lines[i])
                i += 1
            i += 1  # 跳过结束 ```
            p = doc.add_paragraph()
            add_par_shading(p, HEX_CODEBG)
            add_par_border(p, 'left', HEX_BORDER, sz=18, space=8)
            p.paragraph_format.left_indent = Cm(0.3)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(8)
            for idx, cl in enumerate(code):
                if idx > 0:
                    p.add_run().add_break()
                r = p.add_run(cl)
                set_run_font(r, cn=FONT_MONO, en=FONT_MONO, size=9,
                             color=COLOR_TEXT)
            continue

        # 标题
        if s.startswith('# '):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(18)
            keep_with_next(p)
            r = p.add_run(s[2:])
            set_run_font(r, cn=FONT_HEI, en=FONT_HEI, size=22, bold=True,
                         color=COLOR_PRIMARY)
            add_par_border(p, 'bottom', HEX_PRIMARY, sz=12, space=6)
            i += 1
            continue
        if s.startswith('## '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(8)
            keep_with_next(p)
            r = p.add_run(s[3:])
            set_run_font(r, cn=FONT_HEI, en=FONT_HEI, size=15, bold=True,
                         color=COLOR_PRIMARY)
            i += 1
            continue
        if s.startswith('### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            keep_with_next(p)
            add_par_border(p, 'left', HEX_ACCENT, sz=24, space=8)
            r = p.add_run(s[4:])
            set_run_font(r, cn=FONT_HEI, en=FONT_HEI, size=12.5, bold=True,
                         color=COLOR_ACCENT)
            i += 1
            continue
        if s.startswith('#### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            keep_with_next(p)
            r = p.add_run(s[5:])
            set_run_font(r, cn=FONT_HEI, en=FONT_HEI, size=11, bold=True,
                         color=COLOR_ACCENT)
            i += 1
            continue

        # 引用块(连续多行合并)
        if s.startswith('>'):
            quote = []
            while i < n and lines[i].strip().startswith('>'):
                q = lines[i].strip().lstrip('>').strip().rstrip('\\').rstrip()
                if q:
                    quote.append(q)
                i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.4)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            add_par_shading(p, HEX_STRIPE)
            add_par_border(p, 'left', HEX_ACCENT, sz=18, space=10)
            for idx, ql in enumerate(quote):
                if idx > 0:
                    p.add_run().add_break()
                add_inline(p, ql, size=BASE_SIZE - 0.5, color=COLOR_MUTED,
                           cn=FONT_KAI)
            continue

        # 列表(有序 / 无序)
        m_ul = re.match(r'^[-*+]\s+(.*)', s)
        m_ol = re.match(r'^(\d+)\.\s+(.*)', s)
        if m_ul or m_ol:
            while i < n:
                cur = lines[i].strip()
                mu = re.match(r'^[-*+]\s+(.*)', cur)
                mo = re.match(r'^(\d+)\.\s+(.*)', cur)
                if not (mu or mo):
                    break
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.75)
                p.paragraph_format.first_line_indent = Cm(-0.35)
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing_rule = \
                    WD_LINE_SPACING.ONE_POINT_FIVE
                if mo:
                    bullet, txt = mo.group(1) + '. ', mo.group(2)
                else:
                    bullet, txt = '\u2022 ', mu.group(1)
                rb = p.add_run(bullet)
                set_run_font(rb, cn=FONT_SONG, en=FONT_SONG, size=BASE_SIZE,
                             color=COLOR_ACCENT, bold=True)
                add_inline(p, txt, size=BASE_SIZE)
                i += 1
            continue

        # 图片
        m_img = re.match(r'^!\[[^\]]*\]\(([^)]+?)\)', s)
        if m_img:
            img = m_img.group(1).strip().strip('"')
            base = os.path.dirname(os.path.abspath(src_path))
            path = img if os.path.isabs(img) else os.path.join(base, img)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            if os.path.exists(path):
                try:
                    run = p.add_run()
                    run.add_picture(path, width=Cm(min(cwidth, 14)))
                except Exception:
                    add_inline(p, f'[图片无法嵌入: {img}]', size=BASE_SIZE,
                               color=COLOR_MUTED)
            else:
                add_inline(p, f'[缺失图片: {img}]', size=BASE_SIZE,
                           color=COLOR_MUTED)
            i += 1
            continue

        # 表格
        if s.startswith('|'):
            rows, i = parse_table(lines, i)
            if not rows:
                continue
            ncol = max(len(r) for r in rows)
            rows = [r + [''] * (ncol - len(r)) for r in rows]
            table = doc.add_table(rows=len(rows), cols=ncol)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.style = 'Table Grid'
            set_table_borders(table)

            is_field = (ncol == 2 and rows[0][0] in ('字段', '项目', '项'))

            for ri, row in enumerate(rows):
                if ri == 0:
                    mark_header_row(table.rows[0])
                for ci, val in enumerate(row):
                    cell = table.cell(ri, ci)
                    set_cell_margins(cell)
                    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                    para = cell.paragraphs[0]
                    para.paragraph_format.line_spacing_rule = \
                        WD_LINE_SPACING.ONE_POINT_FIVE
                    para.paragraph_format.space_after = Pt(0)
                    # 单元格内 <br> 支持
                    segs = re.split(r'<br\s*/?>', val)

                    def render(segments, **kw):
                        for si, seg in enumerate(segments):
                            if si > 0:
                                para.add_run().add_break()
                            add_inline(para, seg, **kw)

                    if ri == 0:
                        shade_cell(cell, HEX_HEADER)
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        render(segs, size=TABLE_SIZE + 0.5, color=COLOR_WHITE,
                               cn=FONT_HEI)
                        for rr in para.runs:
                            rr.font.bold = True
                    elif is_field and ci == 0:
                        shade_cell(cell, HEX_LABEL)
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        render(segs, size=TABLE_SIZE + 0.5, color=COLOR_PRIMARY,
                               cn=FONT_HEI)
                        for rr in para.runs:
                            rr.font.bold = True
                    else:
                        if not is_field and ri % 2 == 0:
                            shade_cell(cell, HEX_STRIPE)
                        if not is_field:
                            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        render(segs, size=TABLE_SIZE)

            widths = compute_col_widths(rows, cwidth)
            set_col_widths(table, widths)

            sp = doc.add_paragraph()
            sp.paragraph_format.space_after = Pt(2)
            continue

        # 普通段落
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.first_line_indent = Cm(0)
        add_inline(p, s, size=BASE_SIZE)
        i += 1

    doc.save(out_path)
    return out_path


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    src = argv[1]
    if not os.path.exists(src):
        print(f"输入文件不存在: {src}")
        return 1
    out = argv[2] if len(argv) > 2 else os.path.splitext(src)[0] + '.docx'
    build(src, out)
    print("saved:", out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
