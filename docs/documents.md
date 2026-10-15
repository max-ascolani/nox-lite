# CVs and cover letters

Nox-Lite builds clean, single-column Word documents: selectable text, simple headings, bullet lists and clickable links. Hiring systems read them well. It doesn't reuse the person's original Word file, photos or fonts. A4 and US Letter are supported. What to write is covered in [writing](writing.md).

## Data

The CV lives in each application package as `cv.json`. Start from [the blank template](../templates/cv.json) or [the fictional example](../examples/candidate/cv.json). The assistant maintains the JSON; the person never edits it.

Required: `schema_version: 1`, a name, and experience or education. Contact fields are optional. Each experience needs `organisation`, `role`, `dates` and optional `bullets`; each education entry needs `institution`, `qualification` and `dates`. Links need a label and a public URL. Skills are groups with a `category` and `items`. Year-only dates are fine when that's all that's known; don't invent months.

The cover letter is plain text in `cover-letter.md`: paragraphs separated by blank lines, starting with the greeting. Headings are ignored.

## Setup

The builders need Python 3.9+ and [python-docx](../requirements-docs.txt), installed once in a private environment. From the workspace root:

```sh
python3 -m venv .nox-lite/.venv
.nox-lite/.venv/bin/python -m pip install -r .nox-lite/requirements-docs.txt
```

On Windows, use `py -3 -m venv .nox-lite\.venv` and `.nox-lite\.venv\Scripts\python.exe`. `nox.py doctor` reports whether it's installed. No API key is needed.

## Build

From the workspace root, with `PKG` as the application package:

```sh
PY=.nox-lite/.venv/bin/python
$PY .nox-lite/scripts/build_cv.py PKG/cv.json "PKG/exports/Jordan Rivera CV.docx" --paper a4 --pdf
$PY .nox-lite/scripts/build_letter.py PKG/cover-letter.md PKG/cv.json "PKG/exports/Jordan Rivera Cover Letter.docx" --pdf
python3 .nox-lite/scripts/check_writing.py PKG/cv.json PKG/cover-letter.md PKG/answers.md --company "Employer" --workspace . --package PKG
```

- Name files after the person, not "CV_final_v3". Use US Letter (`--paper letter`) for the US and Canada, and A4 elsewhere.
- `--pdf` needs LibreOffice (free, optional). The builder finds it on macOS and Windows automatically. Without it, the .docx is still made, and the person can save it as a PDF from Word, Pages or Google Docs. Never say a PDF exists until it does.
- Arial is the default font. `--font "Liberation Sans"` is an alternative when installed.
- `check_writing.py` runs the checks from [writing](writing.md). Fix every **problem**; check every **warning** (numbers it can't find in the profile or job ad, missing employer name, too many "I" openers).

## Look at every page

1. Check the facts, dates, contact details and the exact job title.
2. Render the PDF (or open the .docx) and look at **every page**: clipping, text running onto a new page, broken links, stray headings, large gaps.
3. Fix and rebuild if needed. Cut content rather than shrinking text.
4. Keep the final files in the package's `exports/` folder, then seal the package for review (`nox.py seal`).

The builders refuse to overwrite an existing file. If the person edited the Word file directly, bring those changes back into `cv.json` first, then rebuild with `--replace`. Never change a submitted snapshot.

Sealing covers `job.md`, `answers.md`, `cv.json`, every PDF and .docx in `exports/`, and `cover-letter.md` if present. Don't upload anything else (profile, research or evidence map) without the person's say-so.
