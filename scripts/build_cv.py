#!/usr/bin/env python3
"""Create a clean DOCX from reviewed CV JSON; optionally convert with LibreOffice."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit


def validate_cv(data):
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("CV must be a JSON object with schema_version 1")
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        raise ValueError("A confirmed name is required")
    if "{{" in json.dumps(data):
        raise ValueError("Replace all template placeholders before building")
    for field in ("location", "email", "phone", "summary"):
        if not isinstance(data.get(field, ""), str):
            raise ValueError(f"{field} must be text")
    if not data.get("experience") and not data.get("education"):
        raise ValueError("Include relevant experience or education")
    for key in ("experience", "education", "skills", "links"):
        if not isinstance(data.get(key, []), list):
            raise ValueError(f"{key} must be a list")
    for item in data.get("experience", []):
        if not isinstance(item, dict):
            raise ValueError("Each experience must be an object")
        for field in ("organisation", "role", "dates"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"Experience requires {field}; use an honest year-only range if months are unresolved")
        if not isinstance(item.get("bullets", []), list) or not all(isinstance(x, str) and x.strip() for x in item.get("bullets", [])):
            raise ValueError("Experience bullets must be nonempty strings")
        if not isinstance(item.get("location", ""), str):
            raise ValueError("Experience location must be text")
    for item in data.get("education", []):
        if not isinstance(item, dict):
            raise ValueError("Each education entry must be an object")
        if not all(isinstance(item.get(k), str) and item[k].strip() for k in ("institution", "qualification", "dates")):
            raise ValueError("Education requires institution, qualification and dates")
        if not isinstance(item.get("detail", ""), str):
            raise ValueError("Education detail must be text")
    for item in data.get("skills", []):
        if not isinstance(item, dict):
            raise ValueError("Each skill group must be an object")
        if not isinstance(item.get("category"), str) or not isinstance(item.get("items"), list) or not all(isinstance(x, str) for x in item["items"]):
            raise ValueError("Skills need a category and text items")
    for link in data.get("links", []):
        if not isinstance(link, dict) or not isinstance(link.get("url"), str) or not isinstance(link.get("label"), str):
            raise ValueError("Links need text label and url fields")
        parsed = urlsplit(link.get("url", ""))
        if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password or not link.get("label"):
            raise ValueError("Profile links need a label and public http(s) URL without credentials")


def find_soffice(executable=None):
    """Return LibreOffice from an explicit path, PATH, or a standard macOS/Windows install; else None."""
    if executable:
        return shutil.which(executable)
    candidates = ["/Applications/LibreOffice.app/Contents/MacOS/soffice"]
    for variable, default in (("ProgramFiles", r"C:\Program Files"), ("ProgramFiles(x86)", r"C:\Program Files (x86)")):
        candidates.append(os.path.join(os.environ.get(variable, default), "LibreOffice", "program", "soffice.exe"))
    return shutil.which("soffice") or next((c for c in candidates if os.path.isfile(c) and os.access(c, os.X_OK)), None)


def pin_font(styles, names, font):
    """Theme attributes (w:asciiTheme etc.) outrank w:ascii, so remove them and name the font for every script."""
    from docx.oxml.ns import qn
    for fonts in list(styles.element.iter(qn("w:rFonts"))):
        for key in [k for k in fonts.attrib if k.lower().endswith("theme")]:
            del fonts.attrib[key]
        if not fonts.attrib:
            fonts.getparent().remove(fonts)
    defaults = styles.element.find(qn("w:docDefaults") + "/" + qn("w:rPrDefault") + "/" + qn("w:rPr"))
    for rpr in [defaults] + [styles[name].element.get_or_add_rPr() for name in names]:
        if rpr is not None:
            fonts = rpr.get_or_add_rFonts()
            for script in ("ascii", "hAnsi", "eastAsia", "cs"):
                fonts.set(qn("w:" + script), font)


def build(data, output, paper="a4", font="Arial", replace=False):
    validate_cv(data)
    if paper not in {"a4", "letter"} or not isinstance(font, str) or not font.strip():
        raise ValueError("Choose a4 or letter paper and a nonempty font name")
    try:
        from docx import Document
        from docx.shared import Inches, Mm, Pt, RGBColor
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.opc.constants import RELATIONSHIP_TYPE as RT
    except ImportError as exc:
        raise ValueError("Install requirements-docs.txt in an isolated Python environment, or use your agent's bundled document runtime.") from exc
    output = Path(output).resolve()
    if output.suffix.lower() != ".docx":
        raise ValueError("Output must end in .docx")
    if output.exists() and not replace:
        raise ValueError("Output exists. Reconcile any direct Word edits first; use --replace only intentionally.")
    doc = Document()
    # Remove irrelevant stock template parts, including an out-of-date preview image.
    for rel_id, rel in list(doc.part.rels.items()):
        if rel.reltype == RT.CUSTOM_XML:
            doc.part.drop_rel(rel_id)
    for rel_id, rel in list(doc.part.package.rels.items()):
        if rel.reltype == RT.THUMBNAIL:
            del doc.part.package.rels[rel_id]
    for border in list(doc.styles.element.iter(qn("w:pBdr"))):
        border.getparent().remove(border)
    section = doc.sections[0]
    section.page_width, section.page_height = (Mm(210), Mm(297)) if paper == "a4" else (Inches(8.5), Inches(11))
    section.top_margin = section.bottom_margin = Inches(0.65)
    section.left_margin = section.right_margin = Inches(0.75)
    sizes = [("Normal", 10.5), ("Title", 22), ("Heading 1", 11), ("Heading 2", 10.5), ("List Bullet", 10.5)]
    pin_font(doc.styles, [name for name, _ in sizes], font)
    for name, size in sizes:
        style = doc.styles[name]
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.line_spacing = 1.08
        style.paragraph_format.widow_control = True
        if name.startswith("Heading"):
            style.font.bold = True
            style.paragraph_format.space_before = Pt(11 if name == "Heading 1" else 7)
            style.paragraph_format.keep_with_next = True
        if name == "List Bullet":
            style.paragraph_format.left_indent = Inches(0.16)
            style.paragraph_format.first_line_indent = Inches(-0.12)
    title = doc.add_paragraph(data["name"], "Title")
    title.paragraph_format.keep_with_next = True
    contact = [data.get(k, "").strip() for k in ("location", "email", "phone") if data.get(k, "").strip()]
    if contact:
        doc.add_paragraph(" | ".join(contact))
    if data.get("links"):
        p = doc.add_paragraph()
        for i, link in enumerate(data["links"]):
            if i: p.add_run(" | ")
            hyper = OxmlElement("w:hyperlink")
            hyper.set(qn("r:id"), p.part.relate_to(link["url"], RT.HYPERLINK, is_external=True))
            run = OxmlElement("w:r"); props = OxmlElement("w:rPr")
            underline = OxmlElement("w:u"); underline.set(qn("w:val"), "single"); props.append(underline)
            run.append(props); text = OxmlElement("w:t"); text.text = link["label"]; run.append(text); hyper.append(run); p._p.append(hyper)
    if data.get("summary", "").strip():
        doc.add_paragraph(data["summary"])
    if data.get("experience"):
        doc.add_paragraph("Experience", "Heading 1")
        for item in data["experience"]:
            doc.add_paragraph(item["role"] + " | " + item["organisation"], "Heading 2")
            p = doc.add_paragraph(" | ".join(x for x in [item.get("location", ""), item["dates"]] if x))
            p.paragraph_format.keep_with_next = bool(item.get("bullets"))
            for run in p.runs: run.italic = True
            bullets = item.get("bullets", [])
            for index, bullet in enumerate(bullets):
                p = doc.add_paragraph(bullet, "List Bullet")
                p.paragraph_format.keep_together = True
                p.paragraph_format.keep_with_next = index < len(bullets) - 1
    if data.get("education"):
        doc.add_paragraph("Education", "Heading 1")
        for item in data["education"]:
            doc.add_paragraph(item["qualification"], "Heading 2")
            doc.add_paragraph(item["institution"] + " | " + item["dates"])
            if item.get("detail"): doc.add_paragraph(item["detail"])
    if data.get("skills"):
        doc.add_paragraph("Skills", "Heading 1")
        for item in data["skills"]:
            p = doc.add_paragraph()
            p.add_run(item["category"] + ": ").bold = True
            p.add_run(", ".join(item["items"]))
    cp = doc.core_properties
    cp.title = data["name"] + " CV"
    cp.author = data["name"]
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


def convert_pdf(docx, executable, replace=False):
    output = Path(docx).with_suffix(".pdf")
    if output.exists() and not replace:
        raise ValueError("PDF exists; use --replace only after reconciling edits")
    found = find_soffice(executable)
    if not found:
        raise ValueError("DOCX created. PDF needs LibreOffice: provide --soffice with its executable path, or export from Word and inspect every page.")
    with tempfile.TemporaryDirectory(prefix="nox-render-") as directory:
        root = Path(directory)
        profile = (root / "profile").as_uri()
        result = subprocess.run([found, f"-env:UserInstallation={profile}", "--headless", "--convert-to", "pdf", "--outdir", str(root), str(docx)], capture_output=True, text=True, timeout=120)
        generated = root / output.name
        if result.returncode or not generated.exists() or generated.stat().st_size == 0:
            raise ValueError("PDF conversion failed; DOCX retained. " + result.stderr[-600:])
        shutil.copy2(generated, output)
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source"); p.add_argument("output")
    p.add_argument("--paper", choices=["a4", "letter"], default="a4")
    p.add_argument("--font", default="Arial"); p.add_argument("--replace", action="store_true")
    p.add_argument("--pdf", action="store_true"); p.add_argument("--soffice")
    args = p.parse_args()
    try:
        data = json.loads(Path(args.source).read_text(encoding="utf-8"))
        output = build(data, args.output, args.paper, args.font, args.replace)
        print(f"Created {output}")
        if args.pdf: print(f"Created {convert_pdf(output, args.soffice, args.replace)}")
        print("Render and inspect every page; generation alone does not establish layout quality or human approval.")
    except (ValueError, OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"Nox-Lite: {exc}", file=sys.stderr); raise SystemExit(1)


if __name__ == "__main__": main()
