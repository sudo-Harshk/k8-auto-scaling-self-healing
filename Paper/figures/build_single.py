"""Build the single-column paper in the layout of the reference paper
(Farming_using_Sprinklers.doc): US Letter, margins L 1.50 / R 1.09 / T 2.06 /
B 1.59 cm, Times New Roman 11 pt justified, 16 pt bold centred title,
bold run-in 'Abstract -' and 'Keywords:', bold numbered headings, centred
figure captions 'Fig N.' below the figure.
usage: python figures/build_single.py SHIELD_AI_final.md SHIELD_AI_final.docx
"""
import re
import sys
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt

md_path, out = sys.argv[1:3]
base = Path(md_path).parent
d = docx.Document()
s = d.sections[0]
s.page_width, s.page_height = Cm(21.59), Cm(27.94)
s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(1.5), Cm(1.09), Cm(2.06), Cm(1.59)
st = d.styles["Normal"]
st.font.name = "Times New Roman"; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.space_after = Pt(0); st.paragraph_format.space_before = Pt(0)
st.paragraph_format.line_spacing = 1.0

INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)")


def runs(p, text, size=None, bold=None):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = p.add_run(part[1:-1]); r.font.name = "Consolas"; r.font.size = Pt(9.5)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = p.add_run(part[1:-1]); r.italic = True
        else:
            r = p.add_run(part)
        if size: r.font.size = Pt(size)
        if bold: r.bold = True


def para(text, align=AL.JUSTIFY, size=None, bold=None, before=0, after=0):
    p = d.add_paragraph(); runs(p, text, size, bold); p.alignment = align
    p.paragraph_format.space_before = Pt(before); p.paragraph_format.space_after = Pt(after)
    return p


lines = Path(md_path).read_text(encoding="utf-8").splitlines()
para(lines[0].lstrip("# ").strip(), AL.CENTER, 16, True, after=10)
i = 1
while i < len(lines) and not lines[i].startswith("**Abstract"):        # author block
    if lines[i].strip() and not lines[i].startswith("---"):
        para(lines[i].strip(), AL.CENTER, 10)
    i += 1
d.paragraphs[-1].paragraph_format.space_after = Pt(10)

while i < len(lines):
    raw = lines[i]; t = raw.strip()
    if not t or re.fullmatch(r"-{3,}", t):
        i += 1; continue
    if t.startswith("```"):
        buf = []; i += 1
        while i < len(lines) and not lines[i].strip().startswith("```"):
            buf.append(lines[i]); i += 1
        i += 1
        p = d.add_paragraph(); r = p.add_run("\n".join(buf))
        r.font.name = "Consolas"; r.font.size = Pt(8.5)
        p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(3)
        continue
    if t.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                rows.append(cells)
            i += 1
        ncol = max(len(r) for r in rows)
        tb = d.add_table(rows=len(rows), cols=ncol); tb.alignment = WD_TABLE_ALIGNMENT.CENTER
        bd = tb._tbl.tblPr.makeelement(qn("w:tblBorders"), {})
        for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
            bd.append(bd.makeelement(qn(f"w:{e}"), {qn("w:val"): "single", qn("w:sz"): "4",
                                                    qn("w:space"): "0", qn("w:color"): "000000"}))
        tb._tbl.tblPr.append(bd)
        for ri, row in enumerate(rows):
            for ci in range(ncol):
                c = tb.cell(ri, ci); c.text = ""
                runs(c.paragraphs[0], row[ci] if ci < len(row) else "", 9, ri == 0 or None)
                if ri < len(rows) - 1:
                    c.paragraphs[0].paragraph_format.keep_with_next = True   # keep the table on one page
            trPr = tb.rows[ri]._tr.get_or_add_trPr()
            trPr.append(trPr.makeelement(qn("w:cantSplit"), {}))
        para("", after=4)
        continue
    m = re.match(r"!\[[^\]]*\]\(([^)]+)\)", t)
    if m:
        img = base / m.group(1)
        if img.exists():
            d.add_picture(str(img), width=Inches(5.0))
            d.paragraphs[-1].alignment = AL.CENTER
            d.paragraphs[-1].paragraph_format.keep_with_next = True          # figure stays with caption
            d.paragraphs[-1].paragraph_format.space_before = Pt(6)
        i += 1; continue
    if t.startswith("#"):
        para(t.lstrip("#").strip(), AL.LEFT, 11, True, before=6, after=2).paragraph_format.keep_with_next = True
        i += 1; continue
    if re.match(r"^\*Fig \d+\.", t):                                     # caption below figure
        para(t.strip("*"), AL.CENTER, 10, after=6)
        i += 1; continue
    if re.match(r"^\*\*(Table|Listing) ", t):                           # caption above table/listing
        p = para(t, AL.CENTER, 10, before=6, after=3)
        p.paragraph_format.keep_with_next = True
        i += 1; continue
    if re.match(r"^(- |\d+\. )", t):
        mark = "• " if t.startswith("- ") else re.match(r"^\d+\. ", t).group(0)
        p = para(mark + re.sub(r"^(- |\d+\. )", "", t))
        p.paragraph_format.left_indent = Inches(0.3); p.paragraph_format.first_line_indent = Inches(-0.2)
        i += 1; continue
    if re.match(r"^\[\d+\]", t):                                         # reference entries
        p = para(t)
        p.paragraph_format.left_indent = Inches(0.3); p.paragraph_format.first_line_indent = Inches(-0.3)
        i += 1; continue
    para(t)
    i += 1

d.save(out)
print("saved", out)
