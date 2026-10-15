#!/usr/bin/env python3
"""Local, dependency-free helpers for Nox-Lite. No network or account access."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import hashlib
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import uuid

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["job_id", "company", "role", "url", "location", "salary", "fit", "decision",
          "stage", "next_action", "checked_at", "applied_at", "package"]
DECISIONS = {"", "prepare", "hold", "decline", "submitted"}
STAGES = {"discovered", "preparing", "ready_for_review", "verification_needed", "unconfirmed",
          "applied", "interview", "offer", "accepted", "rejected", "withdrawn", "closed"}
SUBMITTED = {"applied", "interview", "offer", "accepted", "rejected"}  # stages that follow a confirmed submission
SETTLED = {"applied", "interview", "offer", "accepted", "unconfirmed"}  # never prepared again without reconciliation
EARLY = {"discovered", "preparing", "ready_for_review"}
UPDATABLE = ("stage", "next_action", "applied_at", "salary", "location", "fit", "checked_at", "package", "decision")
CHECKS = ["files", "profile", "search", "sources", "documents", "browser", "upload", "tracker", "email", "first_search", "schedule"]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".nox-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    atomic_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def inside(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Path must remain inside the workspace/package")
    return path


def workspace(path):
    root = Path(path).expanduser().resolve()
    config = read_json(root / "workspace.json")
    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise ValueError("Unsupported workspace schema; preserve files and inspect before upgrading")
    if config.get("tracker", {}).get("backend") not in {"local", "sheets"}:
        raise ValueError("Choose one known tracker backend: local or sheets")
    if config.get("email", {}).get("mode") not in {"manual", "codes", "outcomes"}:
        raise ValueError("Unknown email mode; keep inbox access disabled until reconciled")
    return root, config


@contextmanager
def locked(path):
    path = Path(path)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError(f"Another write may be in progress: {path.name}. Inspect before removing a stale lock.")
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def canonical_url(value):
    p = urlsplit(value.strip())
    if p.scheme.lower() not in {"http", "https"} or not p.hostname or p.username or p.password:
        raise ValueError("Use a public http(s) vacancy URL without credentials")
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in {"gclid", "fbclid", "gh_src"}]
    path = p.path.rstrip("/")
    if p.hostname.lower() == "jobs.ashbyhq.com" and path.endswith("/application"):
        path = path[:-12]
    host = p.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    if p.port and not (p.scheme.lower() == "https" and p.port == 443 or p.scheme.lower() == "http" and p.port == 80):
        host += f":{p.port}"
    return urlunsplit((p.scheme.lower(), host, path, urlencode(sorted(query)), ""))


def identity(url):
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()[:16]


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is None or parsed.tzinfo is None:
        raise ValueError("Use an ISO timestamp with timezone, e.g. 2026-10-15T14:05:00+01:00")
    return value


def safe_cell(value):
    value = str(value)
    # CSV opened in a spreadsheet must not evaluate candidate/employer text as a formula.
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("'", "\t", "\r")) else value


def decode_cell(value):
    if value.startswith("'") and safe_cell(value[1:]) == value:
        return value[1:]
    return value


def read_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError("Tracker headers differ from the contract; reconcile them before writing")
        rows = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Malformed CSV row; preserve and repair before writing")
            rows.append({k: decode_cell(v) for k, v in row.items()})
        return rows


def write_rows(path, rows):
    import io
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows({k: safe_cell(row.get(k, "")) for k in FIELDS} for row in rows)
    atomic_text(path, out.getvalue())


def local_tracker(root, config):
    if config["tracker"]["backend"] != "local":
        raise ValueError("Google Sheets is authoritative. Use the live Sheet; do not write the old local CSV.")
    return inside(root, config["tracker"]["path"])


def initialise(destination, provider):
    if provider not in {"codex", "claude", "both"}:
        raise ValueError("Choose codex, claude or both")
    dest = Path(destination).expanduser().resolve()
    if dest.exists():
        raise ValueError("Destination already exists. Use doctor/resume; initialization never overwrites a folder.")
    if dest == ROOT or dest.is_relative_to(ROOT):
        raise ValueError("Choose a private folder outside the toolkit")
    if any((p / ".git").exists() for p in [dest, *dest.parents]):
        raise ValueError("Choose a private folder outside any Git repository")
    dest.mkdir(parents=True, mode=0o700)
    # An explicit allowlist prevents accidental copies of checkout data or author credentials.
    toolkit = dest / ".nox-lite"
    toolkit.mkdir()
    for folder in ("workflows", "setup", "docs", "templates", "sources", "scripts", "skills", "examples", "tests"):
        # "plans" keeps maintainers' docs/plans out of private workspaces.
        shutil.copytree(ROOT / folder, toolkit / folder,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "plans"))
    for name in ("VERSION", "LICENSE", "requirements-docs.txt", "START_HERE.md", "README.md", "CLAUDE.md", "CONTRIBUTING.md"):
        shutil.copy2(ROOT / name, toolkit / name)
    shutil.copytree(ROOT / "templates/workspace", dest, dirs_exist_ok=True)
    config = read_json(dest / "workspace.json")
    config.update(provider=provider, created_at=now(), toolkit_version=(ROOT / "VERSION").read_text().strip())
    write_json(dest / "workspace.json", config)
    write_json(dest / "setup-state.json", {"schema_version": 1, "checks": {}, "next_step": "Import a CV or career notes and confirm the basics."})
    for folder in ("inbox", "evidence", "applications", "research", "tracker", ".runtime"):
        (dest / folder).mkdir(exist_ok=True)
    write_rows(dest / "tracker/jobs.csv", [])
    atomic_text(dest / ".gitignore", "# Personal workspace: do not publish. This is not encryption.\n*\n")
    atomic_text(dest / "AGENTS.md", "# My Nox-Lite workspace\n\n"
                "Read `workspace.json`, `setup-state.json` and `profile/README.md`. This folder contains private candidate information. "
                "Do not publish, upload to GitHub or initialise public backups.\n\n"
                "Shared procedures and all operating rules are in `.nox-lite/AGENTS.md`; read them before work. "
                "Paths in those procedures such as `profile/` and `applications/` refer to THIS workspace root, not `.nox-lite/`. "
                "Use only the tracker chosen in `workspace.json`.\n\n"
                "Start with `.nox-lite/workflows/setup.md` if setup is incomplete. Ordinary requests select the relevant installed skill.\n")
    shutil.copy2(ROOT / "AGENTS.md", toolkit / "AGENTS.md")
    # Rewrite the toolkit introduction for its installed location, retaining all operating rules.
    instructions = (toolkit / "AGENTS.md").read_text()
    instructions = instructions.replace("If `workspace.json` is absent", "At the workspace root, if `workspace.json` is absent")
    atomic_text(toolkit / "AGENTS.md", instructions)
    # Claude Code expands @imports, so both instruction files load without a separate read.
    atomic_text(dest / "CLAUDE.md", "\n".join(["# My Nox-Lite workspace", "", "@AGENTS.md", "@.nox-lite/AGENTS.md", ""]))
    from sync_skills import generate
    generate(dest, installed=True, provider=provider)
    return {"workspace": str(dest), "next": "Open this folder in your agent and say: Continue setting up."}


def has_docx(python):
    try:
        return subprocess.run([str(python), "-c", "import docx"], capture_output=True, timeout=60).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def dependencies(root):
    """Informational: what this computer can do, in plain English. Missing optional tools are not failures."""
    from build_cv import find_soffice
    version = ".".join(map(str, sys.version_info[:3]))
    ok = sys.version_info >= (3, 9)
    report = [{"check": "Python", "ok": ok, "version": version,
               "note": f"Python {version} works with Nox-Lite." if ok else
               "Nox-Lite needs Python 3.9 or newer. Ask your assistant to help you install a current Python."}]
    try:
        import docx  # noqa: F401
        found = ["current Python"]
    except ImportError:
        found = []
    # Docs install python-docx into .nox-lite/.venv (workspace) or .venv (toolkit); check those interpreters too.
    for venv in dict.fromkeys([root / ".nox-lite/.venv", ROOT / ".venv"]):
        python = next((p for p in (venv / "bin/python", venv / "Scripts/python.exe") if p.is_file()), None)
        if python and has_docx(python):
            found.append(str(venv.relative_to(root)) if venv.is_relative_to(root) else str(venv))
    note = ("CV files can be built." if "current Python" in found else
            f"CV files can be built with the Python in {found[0]}; your assistant should use that one." if found else
            "CV files can't be built yet. Ask your assistant to install the CV builder: "
            "it creates .nox-lite/.venv and installs python-docx from .nox-lite/requirements-docs.txt.")
    report.append({"check": "python-docx (CV builder)", "ok": bool(found), "found_in": found, "note": note})
    soffice = find_soffice()
    report.append({"check": "LibreOffice (optional PDF export)", "ok": bool(soffice), "path": soffice or "",
                   "note": "Found. PDF copies of CVs can be made automatically." if soffice else
                   "Optional. Without it you'll get Word (.docx) CVs, which most application forms accept; "
                   "you can also export PDF from Word, Pages or Google Docs."})
    return report


def doctor(path):
    root, config = workspace(path)
    report = {"workspace": str(root), "local_checks": [], "recorded_checks": {}, "next_step": ""}
    for relative in ("profile/README.md", "profile/facts.md", "profile/preferences.md", "profile/claims.json", ".nox-lite/workflows/setup.md"):
        report["local_checks"].append({"check": relative, "ok": inside(root, relative).is_file()})
    with tempfile.NamedTemporaryFile(dir=root / ".runtime", delete=True) as test:
        test.write(b"nox-lite"); test.flush(); test.seek(0)
        report["local_checks"].append({"check": "write and read private runtime file", "ok": test.read() == b"nox-lite"})
    if config["tracker"]["backend"] == "local":
        rows = read_rows(local_tracker(root, config))
        ids = [r["job_id"] for r in rows]
        report["local_checks"].append({"check": "tracker headers and unique identities", "ok": len(ids) == len(set(ids)), "rows": len(rows)})
    else:
        report["local_checks"].append({"check": "Sheets connection", "ok": None, "note": "Must be tested in the agent; this offline helper cannot verify it."})
    state = read_json(root / "setup-state.json")
    report["recorded_checks"] = state["checks"]
    report["next_step"] = state["next_step"]
    report["dependencies"] = dependencies(root)
    report["note"] = ("Recorded checks are dated observations, not live connection tests or an approval to submit. "
                      "Dependencies are informational; a missing optional tool does not block setup.")
    return report


def record_check(path, name, evidence, status):
    root, _ = workspace(path)
    if name not in CHECKS or not evidence.strip() or status not in {"passed", "blocked", "skipped"}:
        raise ValueError("Choose a known check and describe the actual observation")
    with locked(root / ".runtime/setup.lock"):
        state = read_json(root / "setup-state.json")
        state["checks"][name] = {"status": status, "observed_at": now(), "evidence": evidence}
        write_json(root / "setup-state.json", state)
    return state["checks"][name]


def add_job(path, company, role, url, location="", fit="", checked_at="", salary="", next_action=""):
    root, config = workspace(path)
    target = local_tracker(root, config)
    if not company.strip() or not role.strip():
        raise ValueError("Company and role are required")
    if checked_at:
        timestamp(checked_at)
    canonical = canonical_url(url)
    with locked(target.with_suffix(".lock")):
        rows = read_rows(target)
        if any(canonical_url(r["url"]) == canonical for r in rows):
            raise ValueError("This vacancy is already tracked; preserve its direction and history")
        row = dict.fromkeys(FIELDS, "")
        row.update(job_id=identity(canonical), company=company.strip(), role=role.strip(), url=canonical,
                   location=location, salary=salary, fit=fit, stage="discovered", next_action=next_action, checked_at=checked_at)
        rows.append(row)
        write_rows(target, rows)
        if read_rows(target)[-1] != row:
            raise ValueError("Tracker readback differs; inspect before retrying")
    return row


def update_job(path, job_id, **changes):
    """Change only the given fields. `submitted` and `applied` record confirmed facts; they never instruct anyone to submit."""
    root, config = workspace(path)
    target = local_tracker(root, config)
    changes = {k: v.strip() for k, v in changes.items() if v is not None}
    if not changes or set(changes) - set(UPDATABLE):
        raise ValueError("Provide at least one field to update: " + ", ".join(UPDATABLE))
    if "stage" in changes and changes["stage"] not in STAGES:
        raise ValueError("Unknown stage; use one listed in docs/tracker.md")
    if "decision" in changes and changes["decision"] not in DECISIONS:
        raise ValueError("Decision must be blank, prepare, hold, decline or submitted")
    for key in ("applied_at", "checked_at"):
        if changes.get(key):
            timestamp(changes[key])
    if changes.get("package"):
        package = inside(root, changes["package"])
        if package == root or not package.is_dir():
            raise ValueError("Package must be an existing folder inside the workspace, e.g. applications/2026-10/...")
        changes["package"] = package.relative_to(root).as_posix()
    with locked(target.with_suffix(".lock")):
        rows = read_rows(target)
        matches = [r for r in rows if r["job_id"] == job_id]
        if len(matches) != 1:
            raise ValueError("Expected exactly one matching vacancy")
        row = matches[0]
        before = row["stage"]
        row.update(changes)
        stage = row["stage"]
        if "stage" in changes and before in SETTLED and stage in EARLY:
            raise ValueError("An existing application or uncertain attempt cannot return to preparation; "
                             "reconcile it to applied, rejected, closed or withdrawn first")
        if changes.get("decision") == "prepare" and stage in SETTLED:
            raise ValueError("Existing application/uncertain attempt requires reconciliation before new preparation")
        if changes.get("decision") == "submitted" and stage not in SUBMITTED:
            raise ValueError("'submitted' records a confirmed submission; set stage applied (or later) with evidence")
        if stage == "applied" and not row["applied_at"] and ("stage" in changes or "applied_at" in changes):
            raise ValueError("Stage applied means a confirmed submission; add --applied-at from the receipt or confirmation")
        write_rows(target, rows)
        if [r for r in read_rows(target) if r["job_id"] == job_id] != [row]:
            raise ValueError("Tracker readback differs; inspect before retrying")
    return row


def set_decision(path, job_id, decision):
    root, config = workspace(path)
    target = local_tracker(root, config)
    if decision not in {"prepare", "hold", "decline"}:
        raise ValueError("A decision selects preparation or a hold; it is not proof of submission")
    with locked(target.with_suffix(".lock")):
        rows = read_rows(target)
        matches = [r for r in rows if r["job_id"] == job_id]
        if len(matches) != 1:
            raise ValueError("Expected exactly one matching vacancy")
        row = matches[0]
        if decision == "prepare" and row["stage"] in {"applied", "interview", "offer", "accepted", "unconfirmed"}:
            raise ValueError("Existing application/uncertain attempt requires reconciliation before new preparation")
        row["decision"] = decision
        write_rows(target, rows)
    return row


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:65] or "application"


def link_package(root, config, canonical, package):
    """Record a new package on its local tracker row; a later stage is never moved backwards."""
    if config["tracker"]["backend"] != "local":
        return False, "Google Sheets is authoritative; record the package path in the live Sheet."
    target = local_tracker(root, config)
    with locked(target.with_suffix(".lock")):
        rows = read_rows(target)
        matches = [r for r in rows if canonical_url(r["url"]) == canonical]
        if len(matches) != 1:
            return False, "No matching tracker row; add the vacancy with add-job, then update-job --package."
        row = matches[0]
        row["package"] = package
        if row["stage"] in {"", "discovered"}:
            row["stage"] = "preparing"
        write_rows(target, rows)
        if [r for r in read_rows(target) if r["job_id"] == row["job_id"]] != [row]:
            raise ValueError("Tracker readback differs; inspect before retrying")
    return True, ""


def create_package(path, company, role, url, month):
    root, config = workspace(path)
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("Use the preparation month YYYY-MM in the user's timezone")
    if not company.strip() or not role.strip():
        raise ValueError("Company and role are required")
    canonical = canonical_url(url)
    dest = root / "applications" / month / f"{slug(company)}--{slug(role)}--{identity(canonical)[:8]}"
    if dest.exists():
        raise ValueError("Package already exists; resume it without overwriting")
    shutil.copytree(ROOT / "templates/application", dest)
    write_json(dest / "identity.json", {"company": company, "role": role, "url": canonical, "job_id": identity(canonical)})
    relative = dest.relative_to(root).as_posix()
    # The package exists now; a tracker problem is reported, never turned into a failed (unrepeatable) creation.
    try:
        linked, note = link_package(root, config, canonical, relative)
    except (ValueError, OSError) as exc:
        linked, note = False, f"Tracker not updated: {exc}"
    result = {"package": relative, "tracker_updated": linked, "next": "Audit the live form and fill job.md, answers.md and cv.json."}
    if note:
        result["tracker_note"] = note
    return result


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def package_files(package):
    mandatory = ["identity.json", "job.md", "answers.md", "cv.json"]
    for name in mandatory:
        if not inside(package, name).is_file():
            raise ValueError(f"Missing package file: {name}")
    exports = sorted(p for p in (package / "exports").glob("*") if p.suffix.lower() in {".pdf", ".docx"})
    if not exports:
        raise ValueError("At least one reviewed PDF/DOCX export is required")
    names = mandatory + [str(p.relative_to(package)) for p in exports]
    # Explicit optional materials are sealed too, if present; research and private notes aren't uploaded.
    for name in ("cover-letter.md", "hiring-message.md"):
        if (package / name).exists():
            names.append(name)
    return {name: digest(inside(package, name)) for name in names}


def seal(package_path):
    package = Path(package_path).resolve()
    with locked(package / ".review.lock"):
        return _seal(package)


def _seal(package):
    from build_cv import validate_cv
    validate_cv(read_json(package / "cv.json"))
    for name in ("job.md", "answers.md", "cover-letter.md"):
        if name == "cover-letter.md" and not (package / name).exists():
            continue
        value = (package / name).read_text(encoding="utf-8")
        if "{{" in value or not value.strip():
            raise ValueError(f"Unfinished template: {name}")
    manifest_path = package / "review/manifest.json"
    if manifest_path.exists():
        archive = package / "review/archive" / (uuid.uuid4().hex + "-manifest.json")
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_path, archive)
    manifest = {"schema_version": 1, "revision": uuid.uuid4().hex, "created_at": now(), "files": package_files(package)}
    write_json(manifest_path, manifest)
    return {"revision": manifest["revision"], "note": "Sealed for review, not approved. Any old approval no longer matches."}


def check_package(package_path):
    package = Path(package_path).resolve()
    if not (package / "review/manifest.json").is_file():
        raise ValueError("Not sealed yet: run seal after the final review files are ready")
    manifest = read_json(package / "review/manifest.json")
    if manifest["files"] != package_files(package):
        raise ValueError("Package files changed after review; reconcile and seal the new revision")
    if not (package / "review/approval.json").is_file():
        raise ValueError("Not approved yet: record the person's approval in review/approval.json")
    approval = read_json(package / "review/approval.json")
    if approval.get("revision") != manifest["revision"]:
        raise ValueError("Approval refers to a different revision")
    for key in ("approved_at", "user_reference", "approval_quote", "submission_authorization_quote", "form_checked_at", "render_evidence"):
        if not isinstance(approval.get(key), str) or not approval[key].strip():
            raise ValueError(f"Approval is incomplete: {key}")
    if approval.get("withdrawn", False):
        raise ValueError("Approval has been withdrawn")
    for path in (package / "submission").glob("*-attempt.json"):
        attempt = read_json(path)
        if attempt.get("outcome") != "failed":
            raise ValueError("Existing confirmed or uncertain attempt requires reconciliation, not resubmission")
        evidence = attempt.get("confirmation_evidence")
        if not isinstance(evidence, str) or not evidence.strip() or not inside(package, evidence).is_file():
            raise ValueError("A failed attempt needs an existing evidence-file reference before a retry")
    return {"revision": manifest["revision"], "files_unchanged": True,
            "note": "Local records consistent. Re-read the live tracker, current form and actual human authorization before submission."}


def create_attempt(package_path):
    package = Path(package_path).resolve()
    with locked(package / ".review.lock"):
        return _create_attempt(package)


def _create_attempt(package):
    result = check_package(package)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    record = {"attempt_id": stamp, "started_at": now(), "outcome": "unconfirmed",
              "manifest": read_json(package / "review/manifest.json"), "approval": read_json(package / "review/approval.json"),
              "confirmation_evidence": None, "snapshot_state": "pending",
              "note": "Created before the final action; not proof of submission."}
    target = package / "submission" / (stamp + "-attempt.json")
    target.parent.mkdir(exist_ok=True)
    # Persist the uncertainty first. A crash during copying must block a blind retry too.
    write_json(target, record)
    # Snapshot exact upload bytes and answers before the action, including an interrupted action.
    snapshot = package / "submission" / stamp
    snapshot.mkdir()
    for name in record["manifest"]["files"]:
        source = inside(package, name)
        dest = inside(snapshot, name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        if digest(dest) != record["manifest"]["files"][name]:
            raise ValueError("File changed while snapshotting; do not submit. Reconcile the pending attempt.")
    if package_files(package) != record["manifest"]["files"]:
        raise ValueError("Package changed while snapshotting; do not submit. Reconcile the pending attempt.")
    record["snapshot_state"] = "complete"
    write_json(target, record)
    return {**result, "attempt": str(target), "snapshot": str(snapshot)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init"); p.add_argument("--workspace", required=True); p.add_argument("--provider", choices=["codex", "claude", "both"], default="both")
    p = sub.add_parser("doctor"); p.add_argument("--workspace", required=True)
    p = sub.add_parser("check"); p.add_argument("--workspace", required=True); p.add_argument("name", choices=CHECKS); p.add_argument("--evidence", required=True); p.add_argument("--status", choices=["passed", "blocked", "skipped"], default="passed")
    p = sub.add_parser("add-job"); p.add_argument("--workspace", required=True)
    for name in ("company", "role", "url"):
        p.add_argument("--" + name, required=True)
    for name in ("location", "salary", "fit", "next-action", "checked-at"):
        p.add_argument("--" + name, default="")
    p = sub.add_parser("update-job", help="Change only the given tracker fields; 'applied'/'submitted' record confirmed facts")
    p.add_argument("--workspace", required=True); p.add_argument("job_id")
    for name in UPDATABLE:
        p.add_argument("--" + name.replace("_", "-"))
    p = sub.add_parser("decision"); p.add_argument("--workspace", required=True); p.add_argument("job_id"); p.add_argument("value", choices=["prepare", "hold", "decline"])
    p = sub.add_parser("package"); p.add_argument("--workspace", required=True)
    for name in ("company", "role", "url", "month"):
        p.add_argument("--" + name, required=True)
    for command in ("seal", "check-package", "attempt"):
        p = sub.add_parser(command); p.add_argument("package")
    p = sub.add_parser("practice"); p.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        if args.command == "init": result = initialise(args.workspace, args.provider)
        elif args.command == "doctor": result = doctor(args.workspace)
        elif args.command == "check": result = record_check(args.workspace, args.name, args.evidence, args.status)
        elif args.command == "add-job": result = add_job(args.workspace, args.company, args.role, args.url, args.location, args.fit, args.checked_at, args.salary, args.next_action)
        elif args.command == "update-job": result = update_job(args.workspace, args.job_id, **{k: getattr(args, k) for k in UPDATABLE})
        elif args.command == "decision": result = set_decision(args.workspace, args.job_id, args.value)
        elif args.command == "package": result = create_package(args.workspace, args.company, args.role, args.url, args.month)
        elif args.command == "seal": result = seal(args.package)
        elif args.command == "check-package": result = check_package(args.package)
        elif args.command == "attempt": result = create_attempt(args.package)
        elif args.command == "practice":
            from functools import partial
            handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "examples/practice"))
            with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
                print(f"Practice form only: http://127.0.0.1:{server.server_port} — Ctrl+C to stop", flush=True)
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    print("Practice server stopped. No form data was saved.")
            return
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"Nox-Lite: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
