#!/usr/bin/env python3
"""Offline structure and common-disclosure checks. Not a complete security audit."""
from pathlib import Path
import json
import re
import sys
from urllib.parse import unquote, urlsplit
import zipfile

from sync_skills import generate

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".runtime", ".venv", "__pycache__", "build", "dist", "node_modules"}
TEXT = {".md", ".json", ".py", ".html", ".js", ".css", ".svg", ".txt", ".yaml", ".yml", ".csv", ""}
RULES = {
    "personal absolute path": re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/|[A-Za-z]:\\Users\\[A-Za-z0-9_.-]+\\"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "possible access token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{32,})\b"),
    "live Sheet identifier": re.compile(r"https?://docs\.google\.com/spreadsheets/d/[A-Za-z0-9_-]{20,}"),
}
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")


def check(root=ROOT):
    root = Path(root).resolve()
    errors = []
    count = 0
    required = ("README.md", "START_HERE.md", "AGENTS.md", "CLAUDE.md", "LICENSE", "docs/privacy.md")
    for name in required:
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")
    if (root / "workspace.json").exists():
        errors.append("Personal workspace configuration must not be at the toolkit root")
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIP for part in rel.parts) or path.name == ".DS_Store":
            continue
        if path.is_symlink():
            errors.append(f"Do not release symlinks: {rel}")
            continue
        if not path.is_file():
            continue
        count += 1
        if path.name.startswith(".env"):
            errors.append(f"Unexpected environment file: {rel}")
        if path.suffix in TEXT or path.name == ".gitignore":
            value = path.read_text(encoding="utf-8")
        elif path.suffix == ".docx":
            with zipfile.ZipFile(path) as archive:
                value = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist() if name.endswith((".xml", ".rels")))
        else:
            errors.append(f"Unreviewed binary/file type: {rel}")
            continue
        for label, rule in RULES.items():
            if rule.search(value):
                errors.append(f"Possible {label}: {rel} (inspect locally; value not printed)")
        if any(match.group(1).lower() not in {"example.com", "example.org", "example.net"} for match in EMAIL.finditer(value)):
            errors.append(f"Non-example email address: {rel}")
        if path.suffix == ".md":
            # Ignore fenced illustrative code; inspect ordinary Markdown links.
            prose = re.sub(r"```.*?```", "", value, flags=re.S)
            for match in LINK.finditer(prose):
                target = match.group(1).split(' "', 1)[0].strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme in {"http", "https", "mailto"} or target.startswith("#"):
                    continue
                if parsed.scheme:
                    errors.append(f"Nonportable link scheme in {rel}")
                    continue
                dest = (path.parent / unquote(parsed.path)).resolve()
                if not dest.is_relative_to(root) or not dest.exists():
                    errors.append(f"Broken/nonportable link in {rel}: {target}")
    if root == ROOT:
        changed = generate(check=True)
        if changed:
            errors.append(f"{len(changed)} provider skill files are missing or out of sync")
        catalogue = json.loads((root / "skills/catalog.json").read_text())
        names = [item["name"] for item in catalogue]
        if len(names) != len(set(names)):
            errors.append("Duplicate skill names")
        for item in catalogue:
            if not 25 <= len(item["short"]) <= 64 or not re.fullmatch(r"[a-z0-9-]+", item["name"]):
                errors.append(f"Invalid skill metadata: {item['name']}")
        for platform in (".agents", ".claude"):
            actual = {p.parent.name for p in (root / platform / "skills").glob("*/SKILL.md")}
            if actual != set(names):
                errors.append(f"Unexpected or missing skills in {platform}")
        sources = json.loads((root / "sources/catalog.json").read_text())["sources"]
        if len({s["id"] for s in sources}) != len(sources):
            errors.append("Duplicate source ids")
        for source in sources:
            if source["verification"] not in {"homepage_reachable", "unverified_tool_error", "not_checked"}:
                errors.append(f"Invalid verification label: {source['id']}")
    return count, errors


if __name__ == "__main__":
    count, errors = check()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS: {count} release files; relative links, skill sync and common-disclosure checks.")
    print("Review contents and Git history separately. This check does not prove live integrations or complete privacy.")
