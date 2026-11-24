"""Helpers for building the LearnOps interim deck on the university template (python-pptx)."""
import copy
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE
from pptx.oxml.ns import qn
from lxml import etree

PURPLE = "3B2A7A"
RED = "E00000"
GREEN = "2E7D32"
GREEN_BG = "E3F2E4"
AMBER = "B26A00"
AMBER_BG = "FFF1CF"
GREY = "5F6672"
GREY_BG = "F0F1F4"
BLUE_BG = "E8E4F5"
INK = "1F2330"
WHITE = "FFFFFF"
FONT = "Arial"

STATUS = {
    "Completed": (GREEN, WHITE),
    "Partially completed": (AMBER, WHITE),
    "Pending": (GREY, WHITE),
    "Blocked": ("C62828", WHITE),
}


def rgb(h):
    return RGBColor.from_string(h)


def clear_slide(slide, keep_title=True):
    """Remove everything except the title placeholder (and template pictures)."""
    for sh in list(slide.shapes):
        if sh.is_placeholder and sh.placeholder_format.type in (1, 3) and keep_title:
            continue
        if sh.shape_type == 13:  # picture
            continue
        sh._element.getparent().remove(sh._element)


def set_title(slide, text, size=26):
    t = slide.shapes.title
    t.left, t.top, t.width, t.height = Inches(0.54), Inches(0.2), Inches(9.75), Inches(0.75)
    tf = t.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    # keep the first paragraph/run (inherits the template's red bold Arial), drop the rest
    paras = tf.paragraphs
    for p in paras[1:]:
        p._p.getparent().remove(p._p)
    p = tf.paragraphs[0]
    for r in p.runs[1:]:
        r._r.getparent().remove(r._r)
    if p.runs:
        p.runs[0].text = text
        r = p.runs[0]
    else:
        r = p.add_run()
        r.text = text
    r.font.size = Pt(size)
    r.font.bold = True
    p.alignment = PP_ALIGN.CENTER


def _apply_runs(p, runs, size, color, bold):
    """runs: str or list of (text, {bold,color,italic,size})."""
    if isinstance(runs, str):
        runs = [(runs, {})]
    elif isinstance(runs, tuple):
        runs = [runs]
    for text, o in runs:
        r = p.add_run()
        r.text = text
        f = r.font
        f.name = FONT
        f.size = Pt(o.get("size", size))
        f.bold = o.get("bold", bold)
        f.italic = o.get("italic", False)
        f.color.rgb = rgb(o.get("color", color))


def add_text(slide, x, y, w, h, paras, size=12, color=INK, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, margin=0.04, space_after=2, name=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    _fill_tf(tb.text_frame, paras, size, color, bold, align, anchor, margin, space_after)
    return tb


def _fill_tf(tf, paras, size, color, bold, align, anchor, margin, space_after):
    tf.word_wrap = True
    tf.auto_size = None
    for extra in tf.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)
    for r in list(tf.paragraphs[0].runs):
        r._r.getparent().remove(r._r)
    tf.vertical_anchor = anchor
    m = Inches(margin)
    tf.margin_left = tf.margin_right = m
    tf.margin_top = tf.margin_bottom = Inches(max(margin * 0.6, 0.02))
    if isinstance(paras, str) or (isinstance(paras, list) and paras and isinstance(paras[0], tuple)):
        paras = [paras]
    first = True
    for para in paras:
        bullet = False
        if isinstance(para, dict):
            bullet = para.get("bullet", False)
            para = para["runs"]
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(space_after)
        if bullet:
            _bullet(p)
        _apply_runs(p, para, size, color, bold)


def _bullet(p):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(0.14)))
    pPr.set("indent", str(-Inches(0.14)))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for e in pPr.findall(qn(tag)):
            pPr.remove(e)
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", "•")


def add_box(slide, x, y, w, h, paras, fill=WHITE, line=GREY, dash=False, size=11, color=INK,
            bold=False, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
            line_w=1.25, margin=0.06, space_after=1, name=None):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        sp.name = name
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sp.adjustments[0] = 0.08
    sp.shadow.inherit = False
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = rgb(fill)
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = rgb(line)
        sp.line.width = Pt(line_w)
        if dash:
            sp.line.dash_style = MSO_LINE.DASH
    _fill_tf(sp.text_frame, paras, size, color, bold, align, anchor, margin, space_after)
    return sp


def add_arrow(slide, x1, y1, x2, y2, color=GREY, w=1.5, dash=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(w)
    if dash:
        c.line.dash_style = MSO_LINE.DASH
    ln = c.line._get_or_add_ln()
    te = etree.SubElement(ln, qn("a:tailEnd"))
    te.set("type", "triangle")
    return c


def status_chip(slide, x, y, w, h, status, size=10, label=None):
    bg, fg = STATUS[status]
    return add_box(slide, x, y, w, h, label or status, fill=bg, line=None, size=size, color=fg, bold=True,
                   margin=0.03)


def add_table(slide, x, y, w, col_w, rows, header_fill=PURPLE, size=10, row_h=0.4, header_size=None,
              fills=None, bold_first_col=True):
    """rows[0] is the header. Cells are str or runs list. fills: {(r,c): hex}."""
    nrows, ncols = len(rows), len(rows[0])
    gs = slide.shapes.add_table(nrows, ncols, Inches(x), Inches(y), Inches(w), Inches(row_h * nrows))
    tbl = gs.table
    # strip the default table style banding
    tblPr = tbl._tbl.tblPr
    tblPr.set("firstRow", "0")
    tblPr.set("bandRow", "0")
    tot = sum(col_w)
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = Inches(w * cw / tot)
    for r in range(nrows):
        tbl.rows[r].height = Inches(row_h)
        for c in range(ncols):
            cell = tbl.cell(r, c)
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.025)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            val = rows[r][c]
            tf = cell.text_frame
            tf.word_wrap = True
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(header_fill)
                _fill_tf(tf, val, header_size or size, WHITE, True, PP_ALIGN.LEFT, MSO_ANCHOR.MIDDLE, 0.05, 0)
            else:
                f = (fills or {}).get((r, c), WHITE if r % 2 else "F7F7FA")
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(f)
                _fill_tf(tf, val, size, INK, bold_first_col and c == 0, PP_ALIGN.LEFT, MSO_ANCHOR.MIDDLE, 0.05, 0)
            _cell_border(cell)
    return gs


def _cell_border(cell, color="C9CCD4"):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        for e in tcPr.findall(qn(tag)):
            tcPr.remove(e)
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        ln = etree.SubElement(tcPr, qn(tag))
        ln.set("w", "6350")
        sf = etree.SubElement(ln, qn("a:solidFill"))
        c = etree.SubElement(sf, qn("a:srgbClr"))
        c.set("val", color)
    # borders must precede fill in schema order: move fill elements to the end
    for tag in ("a:solidFill", "a:noFill"):
        for e in tcPr.findall(qn(tag)):
            tcPr.remove(e)
            tcPr.append(e)


def tag_banner(slide, text, x=0.54, y=0.95, w=9.75, fill=AMBER_BG, color=AMBER, size=11):
    return add_box(slide, x, y, w, 0.3, text, fill=fill, line=None, size=size, color=color, bold=True,
                   shape=MSO_SHAPE.RECTANGLE, margin=0.08)


def legend(slide, x, y):
    items = [("Merged on main", GREEN_BG, GREEN, False), ("Open / draft PR", AMBER_BG, AMBER, True),
             ("Planned / design only", GREY_BG, GREY, True)]
    cx = x
    for text, bg, ln, dash in items:
        add_box(slide, cx, y, 0.22, 0.16, "", fill=bg, line=ln, dash=dash, shape=MSO_SHAPE.RECTANGLE, line_w=1.25)
        add_text(slide, cx + 0.26, y - 0.04, 1.75, 0.24, text, size=10, color=INK, margin=0.0)
        cx += 2.0


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text
