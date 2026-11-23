"""Build Paper/SHIELD_AI_revised.docx from SHIELD_AI_revised.md.

Keeps the title/author block (first 5 paragraphs) of the original
'paper new update.docx', then renders the markdown: headings, paragraphs with
**bold** / *italic* / `code`, pipe tables, images, lists and code blocks.
usage: python build_docx.py <original.docx> <revised.md> <out.docx>
"""
import copy
import re
import sys
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

orig, md_path, out = sys.argv[1:4]
base = Path(md_path).parent
PLAIN = orig == "none"
d = docx.Document() if PLAIN else docx.Document(orig)
body = d.element.body

# keep the title + author block, drop everything else except the final sectPr
keep = [] if PLAIN else [p._p for p in d.paragraphs[:5]]
for el in list(body):
    if el.tag == qn("w:sectPr") or el in keep:
        continue
    body.remove(el)
# single column, one section
sect = body.find(qn("w:sectPr"))
cols = sect.find(qn("w:cols"))
if cols is not None:
    for a in list(cols.attrib):
        if a != qn("w:space"):
            del cols.attrib[a]
d.styles["Normal"].font.name = "Times New Roman"
d.styles["Normal"].font.size = Pt(10.5)

INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)")


def add_runs(par, text):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = par.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1]); r.font.name = "Consolas"; r.font.size = Pt(9)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1]); r.italic = True
        else:
            par.add_run(part)


def para(text, style=None, align=None):
    style = style or ("Normal" if PLAIN else "Body Text")
    p = d.add_paragraph(style=style)
    add_runs(p, text)
    if align is not None:
        p.alignment = align
    return p


lines = Path(md_path).read_text(encoding="utf-8").splitlines()
# revised title into the kept title paragraph (keeps its formatting)
if PLAIN:
    d.add_heading(lines[0].lstrip("# ").strip(), level=0)
else:
    title_par = d.paragraphs[0]
    for r in title_par.runs[1:]:
        r._r.getparent().remove(r._r)
    title_par.runs[0].text = lines[0].lstrip("# ").strip()
i = 0
# skip the markdown title (already in the kept block) and the note line
if PLAIN:
    i = 1
else:
    while i < len(lines) and not lines[i].startswith("**Abstract"):
        i += 1
while i < len(lines):
    ln = lines[i]
    s = ln.strip()
    if not s:
        i += 1; continue
    if s.startswith("```"):
        buf = []; i += 1
        while i < len(lines) and not lines[i].strip().startswith("```"):
            buf.append(lines[i]); i += 1
        i += 1
        p = d.add_paragraph(style="Normal")
        r = p.add_run("\n".join(buf)); r.font.name = "Consolas"; r.font.size = Pt(8)
        continue
    if s.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                rows.append(cells)
            i += 1
        ncol = max(len(r) for r in rows)
        t = d.add_table(rows=len(rows), cols=ncol)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = t._tbl.tblPr
        borders = tblPr.makeelement(qn("w:tblBorders"), {})
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            borders.append(borders.makeelement(qn(f"w:{edge}"), {
                qn("w:val"): "single", qn("w:sz"): "4", qn("w:space"): "0", qn("w:color"): "000000"}))
        tblPr.append(borders)
        for ri, row in enumerate(rows):
            for ci in range(ncol):
                cell = t.cell(ri, ci); cell.text = ""
                p = cell.paragraphs[0]
                add_runs(p, row[ci] if ci < len(row) else "")
                for r in p.runs:
                    r.font.size = Pt(8)
                    if ri == 0:
                        r.bold = True
        d.add_paragraph()
        continue
    m = re.match(r"!\[[^\]]*\]\(([^)]+)\)", s)
    if m:
        img = base / m.group(1)
        if img.exists():
            d.add_picture(str(img), width=Inches(5.5))
            d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        i += 1; continue
    if s.startswith("#"):
        level = len(s) - len(s.lstrip("#"))
        d.add_heading(s.lstrip("#").strip(), level=min(max(level - 1, 1), 3))
        i += 1; continue
    if s.startswith(">"):
        i += 1; continue  # editorial notes are not part of the paper
    if re.match(r"^(- |\d+\. )", s):
        mark = "• " if s.startswith("- ") else re.match(r"^\d+\. ", s).group(0)
        p = para(mark + re.sub(r"^(- |\d+\. )", "", s), align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.18)
        i += 1; continue
    if re.fullmatch(r"-{3,}|\*{3,}", s):
        i += 1; continue
    # caption lines (single italic line starting with *Fig.)
    if s.startswith("*Fig."):
        para(s, align=WD_ALIGN_PARAGRAPH.CENTER)
        i += 1; continue
    para(s, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    i += 1

d.save(out)
print("saved", out)
