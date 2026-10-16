#!/usr/bin/env python3
"""Readable copies of the tracker: an Excel file and a browser page, rebuilt from tracker/jobs.csv.
Standard library only. The CSV stays the record; these are read-only copies for people."""
from __future__ import annotations

from datetime import date, datetime
import io
import json
from pathlib import Path
import re
from urllib.parse import quote, urlsplit
import zipfile
from xml.sax.saxutils import escape as xml_escape

PAGE_TEMPLATE = Path(__file__).resolve().parents[1] / "templates/tracker/page.html"

GROUPS = [  # display order: what needs the person first
    ("needs", "Needs you"),
    ("interview", "Interviews and offers"),
    ("progress", "Being prepared"),
    ("applied", "Applied, waiting to hear"),
    ("closed", "On hold or closed"),
]
STAGE_STATUS = {
    "discovered": ("New: your call", "needs"),
    "preparing": ("Being prepared", "progress"),
    "ready_for_review": ("Ready for you to review", "needs"),
    "verification_needed": ("Needs your help", "needs"),
    "unconfirmed": ("Checking it was sent", "progress"),
    "applied": ("Applied", "applied"),
    "interview": ("Interview", "interview"),
    "offer": ("Offer", "interview"),
    "accepted": ("Accepted", "interview"),
    "rejected": ("Not successful", "closed"),
    "withdrawn": ("Withdrawn", "closed"),
    "closed": ("Job closed", "closed"),
}
ATTEMPTED = {"unconfirmed", "applied", "interview", "offer", "accepted", "rejected", "withdrawn", "closed"}
COLUMNS = {  # key: (heading, Excel width)
    "company": ("Company", 24),
    "role": ("Role", 34),
    "status": ("Status", 25),
    "next_step": ("Next step", 46),
    "fit": ("Fit", 7),
    "fit_reason": ("Why it fits", 52),
    "location": ("Location", 24),
    "salary": ("Salary", 22),
    "applied": ("Applied", 13),
    "checked": ("Last checked", 14),
    "link": ("Job ad", 10),
    "package": ("Application", 13),
}
DETAIL = {
    "simple": ["company", "role", "status", "next_step", "fit", "applied", "link"],
    "detailed": ["company", "role", "status", "next_step", "fit", "fit_reason", "location", "salary",
                 "applied", "checked", "link", "package"],
}
REQUIRED = ["company", "role", "status"]
FORMATS = {"page": ["page"], "excel": ["excel"], "both": ["page", "excel"]}
FIT = re.compile(r"\s*([1-5])\s*/\s*5\b\s*[:.,;\-–]?\s*(.*)", re.S)
CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")


def settings(view, fmt=None, detail=None, add=(), drop=()):
    """The view chosen in workspace.json (`tracker.view`), with any requested changes applied.
    A blank `columns` follows the detail preset; adding or dropping a column saves a custom list."""
    view = dict(view or {})
    columns = None if detail else view.get("columns")  # choosing a detail level starts from its preset
    fmt, detail = fmt or view.get("format") or "page", detail or view.get("detail") or "detailed"
    if fmt not in FORMATS:
        raise ValueError("Choose a tracker view format: page, excel or both")
    if detail not in DETAIL:
        raise ValueError("Choose a tracker detail level: simple or detailed")
    if columns is not None and not isinstance(columns, list):
        raise ValueError("tracker.view.columns in workspace.json should be a list of column names")
    unknown = sorted(set(columns or []).union(add, drop) - set(COLUMNS))
    if unknown:
        raise ValueError(f"Unknown tracker column {', '.join(unknown)}; choose from: {', '.join(COLUMNS)}")
    if set(drop) & set(REQUIRED):
        raise ValueError("Company, role and status are always shown")
    chosen = set(columns or DETAIL[detail]).union(add, REQUIRED) - set(drop)
    ordered = [key for key in COLUMNS if key in chosen]
    view.update(format=fmt, detail=detail, columns=None if chosen == set(DETAIL[detail]) else ordered)
    return view, ordered


def status(row):
    stage, decision = row.get("stage", ""), row.get("decision", "")
    if stage not in ATTEMPTED:  # a decision only changes jobs nobody has tried to send yet
        if decision == "decline":
            return "You passed", "closed"
        if decision == "hold":
            return "On hold", "closed"
        if stage == "discovered" and decision == "prepare":
            return "Queued to prepare", "progress"
    return STAGE_STATUS.get(stage, (stage.replace("_", " ").capitalize() or "No status", "needs"))


def moment(value):
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")) if value.strip() else None
    except ValueError:
        return None


def short_date(moment_, today):
    if not moment_:
        return ""
    text = f"{moment_.day} {moment_:%b}"
    return text if moment_.year == today.year else f"{text} {moment_.year}"


def job_link(url):
    parts = urlsplit(url.strip())
    return url.strip() if parts.scheme in {"http", "https"} and parts.netloc else ""


def package_link(path):
    """Relative link from tracker/ to a workspace package folder; nothing for odd paths."""
    path = path.strip().strip("/")
    if not path or path.startswith(("/", "\\")) or ".." in path.split("/") or ":" in path:
        return ""
    return "../" + quote(path) + "/"


def jobs(rows):
    order = {key: i for i, (key, _) in enumerate(GROUPS)}
    out = []
    for row in rows:
        label, group = status(row)
        match = FIT.match(row.get("fit", ""))
        score, reason = (int(match.group(1)), match.group(2).strip()) if match else (None, row.get("fit", "").strip())
        reason = reason[:1].upper() + reason[1:]
        applied, checked = moment(row.get("applied_at", "")), moment(row.get("checked_at", ""))
        latest = applied or checked
        out.append({"row": row, "label": label, "group": group, "score": score, "reason": reason,
                    "applied": applied, "checked": checked,
                    "sort": (order[group], -(score or 0) if group in {"needs", "progress"} else 0,
                             -(latest.timestamp() if latest else 0))})
    return sorted(out, key=lambda job: job["sort"])


def counts(items):
    tally = {key: 0 for key, _ in GROUPS}
    for job in items:
        tally[job["group"]] += 1
    tally["sent"] = sum(1 for job in items if job["row"].get("stage") in {"applied", "interview", "offer", "accepted", "rejected"})
    return tally


def summary(tally):
    parts = [f"{tally['needs']} need{'s' if tally['needs'] == 1 else ''} you"]
    if tally["interview"]:
        parts.append(f"{tally['interview']} interview{'' if tally['interview'] == 1 else 's'} or offer{'' if tally['interview'] == 1 else 's'}")
    parts += [f"{tally['progress']} being prepared", f"{tally['sent']} applied"]
    return " · ".join(parts)


def updated_line(updated):
    return f"Updated {updated.day} {updated:%b %Y} at {updated:%H:%M}"


# ---------- Excel ----------

def clean(text):
    return CONTROL.sub("", str(text))[:32000]  # Excel refuses cells over 32,767 characters


def column_letter(index):
    letters, index = "", index + 1
    while index:
        index, rest = divmod(index - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="1"><numFmt numFmtId="164" formatCode="d mmm yyyy"/></numFmts>
<fonts count="11">
<font><sz val="12"/><name val="Calibri"/><family val="2"/></font>
<font><b/><sz val="20"/><name val="Calibri"/><family val="2"/></font>
<font><sz val="12"/><color rgb="FF6B7280"/><name val="Calibri"/><family val="2"/></font>
<font><b/><sz val="12"/><color rgb="FF374151"/><name val="Calibri"/><family val="2"/></font>
<font><u/><sz val="12"/><color rgb="FF2563EB"/><name val="Calibri"/><family val="2"/></font>
<font><b/><sz val="12"/><name val="Calibri"/><family val="2"/></font>
<font><b/><sz val="12"/><color rgb="FF92400E"/><name val="Calibri"/><family val="2"/></font>
<font><b/><sz val="12"/><color rgb="FF5B21B6"/><name val="Calibri"/><family val="2"/></font>
<font><b/><sz val="12"/><color rgb="FF1E40AF"/><name val="Calibri"/><family val="2"/></font>
<font><b/><sz val="12"/><color rgb="FF065F46"/><name val="Calibri"/><family val="2"/></font>
<font><sz val="12"/><color rgb="FF4B5563"/><name val="Calibri"/><family val="2"/></font>
</fonts>
<fills count="8">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFF3F4F6"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFEF3C7"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFEDE9FE"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFDBEAFE"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFD1FAE5"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFF3F4F6"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="3">
<border><left/><right/><top/><bottom/><diagonal/></border>
<border><left/><right/><top/><bottom style="thin"><color rgb="FFE5E7EB"/></bottom><diagonal/></border>
<border><left/><right/><top/><bottom style="medium"><color rgb="FFD1D5DB"/></bottom><diagonal/></border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="15">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>
<xf numFmtId="0" fontId="3" fillId="2" borderId="2" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="5" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="4" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1" applyAlignment="1"><alignment horizontal="left" vertical="top"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="top"/></xf>
<xf numFmtId="0" fontId="6" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="7" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="8" fillId="5" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="9" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="top"/></xf>
<xf numFmtId="0" fontId="10" fillId="7" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="top"/></xf>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""
TITLE, SUBTITLE, HEADER, TEXT, WRAP, BOLD, LINK, DATE, CENTRE = range(1, 10)
STATUS_STYLE = {"needs": 10, "interview": 11, "progress": 12, "applied": 13, "closed": 14}
WRAPPED = {"next_step", "fit_reason", "role"}
HEADER_ROW = 4


def xlsx(rows, columns, updated):
    items, strings, index = jobs(rows), [], {}
    links = []

    def text(ref, value, style):
        value = clean(value)
        if value not in index:
            index[value] = len(strings)
            strings.append(value)
        return f'<c r="{ref}" s="{style}" t="s"><v>{index[value]}</v></c>'

    def day(ref, value):
        if not value:
            return f'<c r="{ref}" s="{DATE}"/>'
        return f'<c r="{ref}" s="{DATE}"><v>{(date(value.year, value.month, value.day) - date(1899, 12, 30)).days}</v></c>'

    last = column_letter(len(columns) - 1)
    sheet = [f'<row r="1" ht="30" customHeight="1">{text("A1", "Job tracker", TITLE)}</row>',
             f'<row r="2">{text("A2", updated_line(updated) + " · " + summary(counts(items)) + " · Your assistant keeps this up to date, so to change anything, just tell it.", SUBTITLE)}</row>',
             '<row r="3" ht="8" customHeight="1"/>',
             f'<row r="{HEADER_ROW}" ht="24" customHeight="1">' +
             "".join(text(f"{column_letter(i)}{HEADER_ROW}", COLUMNS[key][0], HEADER) for i, key in enumerate(columns)) + "</row>"]
    for number, job in enumerate(items, start=HEADER_ROW + 1):
        row, cells = job["row"], []
        for i, key in enumerate(columns):
            ref = f"{column_letter(i)}{number}"
            if key == "company":
                cells.append(text(ref, row.get("company", ""), BOLD))
            elif key == "status":
                cells.append(text(ref, job["label"], STATUS_STYLE[job["group"]]))
            elif key == "fit":
                cells.append(text(ref, f"{job['score']}/5" if job["score"] else "", CENTRE))
            elif key in {"applied", "checked"}:
                cells.append(day(ref, job[key]))
            elif key in {"link", "package"}:
                target = job_link(row.get("url", "")) if key == "link" else package_link(row.get("package", ""))
                if target:
                    links.append((ref, target))
                    cells.append(text(ref, "View job" if key == "link" else "Open folder", LINK))
                else:
                    cells.append(f'<c r="{ref}" s="{TEXT}"/>')
            else:
                value = {"role": row.get("role", ""), "next_step": row.get("next_action", ""), "fit_reason": job["reason"],
                         "location": row.get("location", ""), "salary": row.get("salary", "")}[key]
                cells.append(text(ref, value, WRAP if key in WRAPPED else TEXT))
        sheet.append(f'<row r="{number}">{"".join(cells)}</row>')
    end = HEADER_ROW + max(len(items), 1)
    if not items:
        sheet.append(f'<row r="{HEADER_ROW + 1}">{text(f"A{HEADER_ROW + 1}", "No jobs yet. Ask your assistant to find some.", SUBTITLE)}</row>')

    cols = "".join(f'<col min="{i + 1}" max="{i + 1}" width="{COLUMNS[key][1]}" customWidth="1"/>' for i, key in enumerate(columns))
    hyperlinks = "".join(f'<hyperlink ref="{ref}" r:id="rId{n}"/>' for n, (ref, _) in enumerate(links, start=1))
    worksheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                 '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>'
                 f'<dimension ref="A1:{last}{end}"/>'
                 '<sheetViews><sheetView showGridLines="0" tabSelected="1" workbookViewId="0">'
                 f'<pane xSplit="1" ySplit="{HEADER_ROW}" topLeftCell="B{HEADER_ROW + 1}" activePane="bottomRight" state="frozen"/>'
                 f'<selection pane="topRight"/><selection pane="bottomLeft"/><selection pane="bottomRight" activeCell="B{HEADER_ROW + 1}" sqref="B{HEADER_ROW + 1}"/>'
                 '</sheetView></sheetViews>'
                 '<sheetFormatPr defaultRowHeight="17"/>'
                 f'<cols>{cols}</cols><sheetData>{"".join(sheet)}</sheetData>'
                 f'<autoFilter ref="A{HEADER_ROW}:{last}{end}"/>'
                 + (f"<hyperlinks>{hyperlinks}</hyperlinks>" if links else "") +
                 '<pageMargins left="0.5" right="0.5" top="0.6" bottom="0.6" header="0.3" footer="0.3"/>'
                 '<pageSetup orientation="landscape" fitToWidth="1" fitToHeight="0"/>'
                 '</worksheet>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
            "".join(f'<Relationship Id="rId{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                    f'Target="{xml_escape(clean(target), {chr(34): "&quot;"})}" TargetMode="External"/>'
                    for n, (_, target) in enumerate(links, start=1)) + "</Relationships>")
    shared = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">' +
              "".join(f'<si><t xml:space="preserve">{xml_escape(value)}</t></si>' for value in strings) + "</sst>")
    workbook = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<bookViews><workbookView/></bookViews><sheets><sheet name="Jobs" sheetId="1" r:id="rId1"/></sheets>'
                f'<definedNames><definedName name="_xlnm._FilterDatabase" localSheetId="0" hidden="1">Jobs!$A${HEADER_ROW}:${last}${end}</definedName>'
                f'<definedName name="_xlnm.Print_Titles" localSheetId="0">Jobs!${HEADER_ROW}:${HEADER_ROW}</definedName></definedNames>'
                '</workbook>')
    parts = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
            '</Types>',
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>',
        "xl/workbook.xml": workbook,
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
            '</Relationships>',
        "xl/styles.xml": STYLES,
        "xl/sharedStrings.xml": shared,
        "xl/worksheets/sheet1.xml": worksheet,
    }
    if links:
        parts["xl/worksheets/_rels/sheet1.xml.rels"] = rels
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, body in parts.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, body.encode("utf-8"))
    return out.getvalue()


# ---------- Browser page ----------

SHORT = {"Ready for you to review": "Review", "New: your call": "New", "Needs your help": "Your help",
         "Being prepared": "Preparing", "Queued to prepare": "Queued", "Checking it was sent": "Checking",
         "Not successful": "Unsuccessful", "Job closed": "Closed", "You passed": "Passed"}
SPEAKER = re.compile(r"\s*(You|Assistant)\s*:\s*(.+)", re.I | re.S)


def page(rows, columns, updated):
    """The browser page: the template with this tracker's jobs inlined, so it works offline from the file.
    Only the chosen columns are included; every value is shown as text by the page, never as markup."""
    shown, today, out = set(columns), updated.date(), []
    for job in jobs(rows):
        row = job["row"]
        step = row.get("next_action", "").strip() if "next_step" in shown else ""
        speaker = SPEAKER.match(step)
        step = speaker.group(2).strip() if speaker else step
        out.append({"company": row.get("company", ""), "role": row.get("role", ""),
                    "stage": row.get("stage", ""), "decision": row.get("decision", ""),
                    "label": job["label"], "short": SHORT.get(job["label"], job["label"]), "group": job["group"],
                    "score": job["score"] if "fit" in shown else None,
                    "reason": job["reason"] if "fit_reason" in shown else "",
                    "location": row.get("location", "") if "location" in shown else "",
                    "salary": row.get("salary", "") if "salary" in shown else "",
                    "who": speaker.group(1).capitalize() if speaker else "", "next": step[:1].upper() + step[1:],
                    "applied": short_date(job["applied"], today) if "applied" in shown else "",
                    "checked": short_date(job["checked"], today) if "checked" in shown else "",
                    "when": short_date(job["applied"] or job["checked"], today),
                    "url": job_link(row.get("url", "")) if "link" in shown else "",
                    "package": package_link(row.get("package", "")) if "package" in shown else ""})
    data = {"updated": f"{updated.day} {updated:%b}, {updated:%H:%M}", "jobs": out}
    # Escaped so no value can close the <script> block it sits in.
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return PAGE_TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", blob, 1)
