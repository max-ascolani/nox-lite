#!/usr/bin/env python3
"""Check application writing before review: placeholders, AI chatter, style, wrong employer and unsourced numbers.

Standard library only. Problems must be fixed; warnings need a human-judgement check.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import sys

PLACEHOLDER = re.compile(r"\{\{|\[(?:company|employer|name|role|job title|insert|your|hiring manager)[^\]]*\]|<insert|\bTODO\b|\bTBC\b|XXX|lorem ipsum", re.I)
CHATTER = ["as an ai", "as a language model", "i can't help with", "i cannot help with", "i'm unable to", "i am unable to",
           "here is a", "here's a", "certainly!", "i hope this helps", "let me know if you"]
BANNED = ["i am writing to express", "i am thrilled", "i'm thrilled", "i am excited to apply", "i'm excited to apply",
          "passionate about", "leverage", "spearhead", "synergy", "results-driven", "dynamic", "fast-paced environment",
          "proven track record", "team player", "go-getter", "think outside the box", "hit the ground running",
          "i believe i would be a great fit", "delve", "tapestry", "testament to"]
NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")


def texts_from(path):
    """Return the prose in a file: JSON string values, or the text of markdown/plain files."""
    raw = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix.lower() != ".json":
        return raw
    found = []
    def walk(value):
        if isinstance(value, str): found.append(value)
        elif isinstance(value, list): [walk(v) for v in value]
        elif isinstance(value, dict): [walk(v) for k, v in value.items() if k not in {"url", "schema_version"}]
    walk(json.loads(raw))
    return "\n\n".join(found)


def normalise_number(value):
    return value.replace(",", "").rstrip(".")


def claim_numbers(text, markdown):
    """Numbers that could be claims: skips URLs, dates, word limits, list markers and non-answer table columns."""
    if markdown:
        kept, answer_col = [], None
        for line in text.splitlines():
            if not line.strip().startswith("|"):
                answer_col = None
                kept.append(line)
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
                continue
            headers = [c.lower() for c in cells]
            if answer_col is None and any(h.startswith("answer") for h in headers):
                answer_col = next(i for i, h in enumerate(headers) if h.startswith("answer"))
                continue
            kept.append(cells[answer_col] if answer_col is not None and answer_col < len(cells) else line)
        text = re.sub(r"^\s*(?:\*\*)?\d+[.)]", "", "\n".join(kept), flags=re.M)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}(?:T[\d:+.-]+)?", "", text)
    text = re.sub(r"\b\d+\s+(?:words|characters|chars)\b", "", text, flags=re.I)
    return {normalise_number(n) for n in NUMBER.findall(text)}


def source_numbers(workspace, package):
    texts = []
    if workspace:
        # Lines still identical to the blank template are guidance, not the person's facts.
        templates = Path(__file__).resolve().parents[1] / "templates" / "workspace" / "profile"
        for path in sorted((Path(workspace) / "profile").glob("*")):
            if path.suffix not in {".md", ".json"}:
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            if (templates / path.name).is_file():
                blank = set((templates / path.name).read_text(encoding="utf-8").splitlines())
                lines = [line for line in lines if line not in blank]
            texts.append("\n".join(lines))
        for path in sorted((Path(workspace) / "evidence").rglob("*")):
            if path.suffix.lower() in {".md", ".txt"}: texts.append(path.read_text(encoding="utf-8", errors="ignore"))
    if package and (Path(package) / "job.md").exists():
        texts.append((Path(package) / "job.md").read_text(encoding="utf-8"))
    return {normalise_number(n) for n in NUMBER.findall("\n".join(texts))}


def other_companies(workspace, company):
    tracker = Path(workspace or "") / "tracker" / "jobs.csv"
    if not workspace or not tracker.exists() or not company:
        return []
    with tracker.open(newline="", encoding="utf-8") as handle:
        names = {row.get("company", "").strip() for row in csv.DictReader(handle)}
    return sorted(n for n in names if len(n) > 2 and n.lower() != company.strip().lower() and n.lower() not in company.lower())


def company_named(company, lower):
    """True when the full name, the name without a legal suffix or its distinctive first word appears."""
    full = company.strip().lower()
    short = re.sub(r"[,.]?\s+(?:inc|ltd|llc|limited|plc|gmbh|corp|corporation|co)\.?$", "", full)
    first = short.split()[0] if short.split() else ""
    names = {full, short} | ({first} if len(first) >= 4 and first != "the" else set())
    return any(re.search(r"\b" + re.escape(name) + r"\b", lower) for name in names if name)


def cv_layout(data):
    """Role habits from the writing guide that the layout makes visible."""
    roles = [r for r in (data.get("experience") or [] if isinstance(data, dict) else []) if isinstance(r, dict)]
    warnings = []
    for role in roles:
        organisation = str(role.get("organisation", ""))
        bracket = re.search(r"\(([^)]*\s[^)]*)\)", organisation)
        if bracket:
            warnings.append(f"\"{organisation}\": move \"{bracket.group(1)}\" into the role's context line (description)")
        if len(str(role.get("role", ""))) > 60:
            warnings.append(f"The job title at {organisation} wraps onto two lines; for a promotion, give the latest title "
                            "and put earlier ones in the context line")
    located = [bool(str(r.get("location", "")).strip()) for r in roles]
    if any(located) and not all(located):
        warnings.append("Some roles have a location and some don't; give each one (or \"Remote\"), or none")
    return warnings


def check(path, company="", workspace=None, package=None, max_words=None):
    text = texts_from(path)
    lower = text.lower()
    problems, warnings = [], []
    for match in sorted({m.group(0) for m in PLACEHOLDER.finditer(text)}):
        problems.append(f"Placeholder left in: {match}")
    problems += [f"AI chatter or refusal: \"{p}\"" for p in CHATTER if p in lower]
    if "—" in text:
        problems.append(f"Em dash used {text.count(chr(0x2014))} time(s); use a comma, full stop or brackets")
    problems += [f"Banned phrase: \"{p}\"" for p in BANNED if re.search(r"\b" + re.escape(p) + r"\b", lower)]
    if re.search(r"~\s?\d", text):
        problems.append("\"~\" before a number; write \"about\" instead")
    if Path(path).suffix.lower() == ".json":
        warnings += cv_layout(json.loads(Path(path).read_text(encoding="utf-8")))
    for name in other_companies(workspace, company):
        if re.search(r"\b" + re.escape(name.lower()) + r"\b", lower):
            problems.append(f"Mentions another employer from the tracker: {name}")
    if company and Path(path).suffix.lower() != ".json" and not company_named(company, lower):
        warnings.append(f"{company} isn't named; check this was written for the right employer")
    if Path(path).suffix.lower() != ".json":
        for number, paragraph in enumerate(p for p in re.split(r"\n\s*\n", text) if p.strip() and not p.lstrip().startswith("#")):
            openers = len(re.findall(r"(?:^|[.!?]\s+)I\b", paragraph.strip()))
            if openers > 1:
                warnings.append(f"Paragraph {number + 1} starts {openers} sentences with \"I\"; vary at least one")
    words = len(re.findall(r"\b\w[\w'’-]*\b", text))
    if max_words and words > max_words:
        problems.append(f"{words} words; the limit is {max_words}")
    if workspace or package:
        known = source_numbers(workspace, package)
        found = claim_numbers(text, Path(path).suffix.lower() == ".md")
        missing = sorted(found - known, key=lambda n: (len(n), n))
        if missing:
            warnings.append("Numbers not found in the profile or job ad (confirm each or remove it): " + ", ".join(missing))
    return {"file": str(path), "words": words, "problems": problems, "warnings": warnings}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("files", nargs="+")
    p.add_argument("--company", default="", help="The employer this was written for")
    p.add_argument("--workspace", help="Workspace root, to compare numbers with the profile and names with the tracker")
    p.add_argument("--package", help="Application package, to compare numbers with job.md")
    p.add_argument("--max-words", type=int)
    args = p.parse_args()
    try:
        results = [check(f, args.company, args.workspace, args.package, args.max_words) for f in args.files]
    except (OSError, ValueError) as exc:
        print(f"Nox-Lite: {exc}", file=sys.stderr); raise SystemExit(2)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    raise SystemExit(1 if any(r["problems"] for r in results) else 0)


if __name__ == "__main__": main()
