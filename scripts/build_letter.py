#!/usr/bin/env python3
"""Create a cover-letter DOCX from reviewed letter text, with the name and contact line from the CV JSON."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_cv import convert_pdf, pin_font, validate_cv  # noqa: E402


def paragraphs(text):
    """Blank-line separated paragraphs; markdown headings and emphasis markers are dropped.

    A block of short lines (a sign-off or address) keeps its line breaks; prose lines are joined.
    """
    lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    result = []
    for block in re.split(r"\n\s*\n", "\n".join(lines)):
        rows = [" ".join(row.split()) for row in block.splitlines() if row.strip()]
        if not rows:
            continue
        joined = "\n".join(rows) if len(rows) > 1 and all(len(row) <= 60 for row in rows) else " ".join(rows)
        result.append(joined.replace("**", "").replace("__", ""))
    return result


def build(letter_text, cv, output, paper="a4", font="Arial", replace=False):
    validate_cv(cv)
    body = paragraphs(letter_text)
    if not body:
        raise ValueError("The letter is empty")
    if "{{" in letter_text:
        raise ValueError("Replace all template placeholders before building")
    try:
        from docx import Document
        from docx.shared import Inches, Mm, Pt, RGBColor
    except ImportError as exc:
        raise ValueError("Install requirements-docs.txt in an isolated Python environment, or use your agent's bundled document runtime.") from exc
    output = Path(output).resolve()
    if output.suffix.lower() != ".docx":
        raise ValueError("Output must end in .docx")
    if output.exists() and not replace:
        raise ValueError("Output exists. Use --replace only intentionally.")
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = (Mm(210), Mm(297)) if paper == "a4" else (Inches(8.5), Inches(11))
    section.top_margin = section.bottom_margin = Inches(0.9)
    section.left_margin = section.right_margin = Inches(1)
    pin_font(doc.styles, ["Normal", "Title"], font)
    for name, size in (("Normal", 11), ("Title", 18)):
        style = doc.styles[name]
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_after = Pt(9)
        style.paragraph_format.line_spacing = 1.12
    from docx.oxml.ns import qn
    for border in list(doc.styles.element.iter(qn("w:pBdr"))):
        border.getparent().remove(border)
    doc.add_paragraph(cv["name"], "Title")
    contact = [cv.get(k, "").strip() for k in ("location", "email", "phone") if cv.get(k, "").strip()]
    if contact:
        doc.add_paragraph(" | ".join(contact)).paragraph_format.space_after = Pt(18)
    for text in body:
        doc.add_paragraph(text)
    cp = doc.core_properties
    cp.title = cv["name"] + " cover letter"
    cp.author = cv["name"]
    cp.last_modified_by = ""
    cp.subject = cp.keywords = cp.comments = cp.category = ""
    cp.created = cp.modified = datetime.now(timezone.utc)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(suffix=".docx", dir=output.parent)
    os.close(fd)
    try:
        doc.save(temp)
        os.replace(temp, output)
    finally:
        if os.path.exists(temp): os.unlink(temp)
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("letter", help="cover-letter.md")
    p.add_argument("cv", help="The package's cv.json, for the name and contact line")
    p.add_argument("output", help="exports/Name - Cover letter.docx")
    p.add_argument("--paper", choices=["a4", "letter"], default="a4")
    p.add_argument("--font", default="Arial"); p.add_argument("--replace", action="store_true")
    p.add_argument("--pdf", action="store_true"); p.add_argument("--soffice")
    args = p.parse_args()
    try:
        cv = json.loads(Path(args.cv).read_text(encoding="utf-8"))
        output = build(Path(args.letter).read_text(encoding="utf-8"), cv, args.output, args.paper, args.font, args.replace)
        print(f"Created {output}")
        if args.pdf: print(f"Created {convert_pdf(output, args.soffice, args.replace)}")
        print("Render and inspect the page before review.")
    except (ValueError, OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"Nox-Lite: {exc}", file=sys.stderr); raise SystemExit(1)


if __name__ == "__main__": main()
