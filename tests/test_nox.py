"""Meaningful state/identity/recovery checks; no external account access."""
import concurrent.futures
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nox
import sync_skills


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nox-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "private"
        nox.initialise(self.root, "both")

    def add(self, url="https://example.com/jobs/42", company="Example Studio"):
        return nox.add_job(self.root, company, "Coordinator", url)

    def test_initialization_is_private_and_resumable(self):
        self.assertFalse((self.root / ".git").exists())
        config = nox.read_json(self.root / "workspace.json")
        self.assertEqual(config["email"]["mode"], "manual")
        self.assertEqual(config["tracker"]["backend"], "local")
        self.assertEqual(nox.read_json(self.root / "profile/claims.json")["claims"], [])
        with self.assertRaisesRegex(ValueError, "already exists"):
            nox.initialise(self.root, "both")
        self.assertTrue(all(x["ok"] for x in nox.doctor(self.root)["local_checks"]))

    def test_rejects_git_and_toolkit_destinations(self):
        git = Path(self.temporary.name) / "repo"
        (git / ".git").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "Git"):
            nox.initialise(git / "private", "codex")
        with self.assertRaisesRegex(ValueError, "outside the toolkit"):
            nox.initialise(nox.ROOT / "never-created-private", "codex")

    def test_installed_skills_resolve_after_toolkit_copy(self):
        import re
        for path in self.root.glob(".*/skills/*/SKILL.md"):
            target = re.search(r"\[the shared procedure\]\(([^)]+)\)", path.read_text()).group(1)
            self.assertTrue((path.parent / target).resolve().is_file())
        self.assertEqual(len(list(self.root.glob(".*/skills/*/SKILL.md"))), 18)
        self.assertEqual(sync_skills.generate(self.root, installed=True, check=True), [])
        self.assertTrue((self.root / ".nox-lite/README.md").exists())
        import release_check
        # The installed snapshot must keep its documentation links usable too.
        _, errors = release_check.check(self.root / ".nox-lite")
        self.assertEqual(errors, [])

    def test_provider_selection(self):
        other = Path(self.temporary.name) / "claude-only"
        nox.initialise(other, "claude")
        self.assertFalse((other / ".agents").exists())
        self.assertEqual(len(list(other.glob(".claude/skills/*/SKILL.md"))), 9)

    def test_duplicate_keeps_user_direction(self):
        row = self.add("https://example.com/jobs/42?utm_source=feed")
        nox.set_decision(self.root, row["job_id"], "decline")
        with self.assertRaisesRegex(ValueError, "already tracked"):
            self.add("https://EXAMPLE.com/jobs/42/#details")
        rows = nox.read_rows(self.root / "tracker/jobs.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["decision"], "decline")

    def test_distinct_ids_are_distinct_vacancies(self):
        self.add("https://example.com/jobs?jobId=1")
        self.add("https://example.com/jobs?jobId=2")
        self.assertEqual(len(nox.read_rows(self.root / "tracker/jobs.csv")), 2)

    def test_formula_and_apostrophe_roundtrip(self):
        for i, value in enumerate(["=1+2", " +SUM(A1:A2)", "@SUM(A1)", "-42", "\ttext", "'=literal", "'ordinary"]):
            row = self.add(f"https://example.com/{i}", company=value)
            self.assertEqual(row["company"], value.strip())
        raw = (self.root / "tracker/jobs.csv").read_text()
        self.assertIn("'=1+2", raw)
        self.assertIn("''=literal", raw)
        for value in ["\rtext", "\ttext", "'=literal", "hello", "@SUM(A1)"]:
            self.assertEqual(nox.decode_cell(nox.safe_cell(value)), value)

    def test_sheet_mode_never_silently_writes_csv(self):
        config = nox.read_json(self.root / "workspace.json")
        config["tracker"]["backend"] = "sheets"
        nox.write_json(self.root / "workspace.json", config)
        before = (self.root / "tracker/jobs.csv").read_bytes()
        with self.assertRaisesRegex(ValueError, "authoritative"):
            self.add()
        self.assertEqual(before, (self.root / "tracker/jobs.csv").read_bytes())
        self.assertIsNone(nox.doctor(self.root)["local_checks"][-1]["ok"])

    def test_unknown_tracker_and_email_modes_fail_closed(self):
        config = nox.read_json(self.root / "workspace.json")
        for section, field in [("tracker", "backend"), ("email", "mode")]:
            bad = copy.deepcopy(config)
            bad[section][field] = "unknown"
            nox.write_json(self.root / "workspace.json", bad)
            with self.assertRaises(ValueError):
                nox.workspace(self.root)

    def test_tracker_rejects_malformed_header_and_row(self):
        path = self.root / "tracker/jobs.csv"
        path.write_text("company,role\nExample,Coordinator\n")
        with self.assertRaisesRegex(ValueError, "headers"):
            self.add()
        path.write_text(",".join(nox.FIELDS) + "\nmissing,columns\n")
        with self.assertRaisesRegex(ValueError, "Malformed"):
            nox.read_rows(path)

    def test_existing_success_or_uncertainty_is_not_prepared_again(self):
        row = self.add()
        for stage in ("applied", "interview", "offer", "accepted", "unconfirmed"):
            row["stage"] = stage
            nox.write_rows(self.root / "tracker/jobs.csv", [row])
            with self.assertRaisesRegex(ValueError, "reconciliation"):
                nox.set_decision(self.root, row["job_id"], "prepare")

    def test_local_paths_and_locks_are_enforced(self):
        with self.assertRaises(ValueError):
            nox.inside(self.root, "../outside.txt")
        with nox.locked(self.root / "tracker/jobs.lock"):
            with self.assertRaisesRegex(ValueError, "write may be in progress"):
                self.add()
        self.add()

    def test_checks_need_observed_evidence(self):
        with self.assertRaises(ValueError):
            nox.record_check(self.root, "browser", "", "passed")
        nox.record_check(self.root, "browser", "Fictional test observation only", "blocked")
        report = nox.doctor(self.root)
        self.assertEqual(report["recorded_checks"]["browser"]["status"], "blocked")
        self.assertIn("not live", report["note"])

    def rows(self):
        return nox.read_rows(self.root / "tracker/jobs.csv")

    def test_update_job_changes_only_given_fields(self):
        row = nox.add_job(self.root, "Example Studio", "Coordinator", "https://example.com/jobs/42",
                          salary="£30,000 a year (advert)", next_action="Decide whether to apply (user)")
        self.assertEqual(self.rows()[0]["salary"], "£30,000 a year (advert)")
        updated = nox.update_job(self.root, row["job_id"], stage="preparing", next_action="Draft CV (assistant)", fit=None)
        self.assertEqual((updated["stage"], updated["next_action"]), ("preparing", "Draft CV (assistant)"))
        self.assertEqual(updated["salary"], "£30,000 a year (advert)")
        self.assertEqual(self.rows(), [updated])

    def test_update_job_needs_one_known_vacancy_and_valid_values(self):
        row = self.add()
        with self.assertRaisesRegex(ValueError, "exactly one"):
            nox.update_job(self.root, "0000000000000000", stage="preparing")
        with self.assertRaisesRegex(ValueError, "Unknown stage"):
            nox.update_job(self.root, row["job_id"], stage="sent")
        with self.assertRaisesRegex(ValueError, "at least one"):
            nox.update_job(self.root, row["job_id"])
        with self.assertRaisesRegex(ValueError, "remain inside"):
            nox.update_job(self.root, row["job_id"], package="../elsewhere")
        with self.assertRaisesRegex(ValueError, "existing folder"):
            nox.update_job(self.root, row["job_id"], package="applications/missing")
        self.assertEqual(self.rows(), [row])

    def test_applied_needs_a_confirmation_time(self):
        row = self.add()
        with self.assertRaisesRegex(ValueError, "applied-at"):
            nox.update_job(self.root, row["job_id"], stage="applied")
        with self.assertRaisesRegex(ValueError, "timezone"):
            nox.update_job(self.root, row["job_id"], stage="applied", applied_at="2026-10-15")
        self.assertEqual(self.rows()[0]["stage"], "discovered")
        done = nox.update_job(self.root, row["job_id"], stage="applied", applied_at="2026-10-15T14:05:00+01:00", decision="submitted")
        self.assertEqual((done["stage"], done["decision"]), ("applied", "submitted"))
        with self.assertRaisesRegex(ValueError, "applied-at"):
            nox.update_job(self.root, row["job_id"], applied_at="")

    def test_uncertain_attempt_cannot_return_to_preparation(self):
        row = self.add()
        nox.update_job(self.root, row["job_id"], stage="unconfirmed")
        for stage in ("preparing", "ready_for_review", "discovered"):
            with self.assertRaisesRegex(ValueError, "reconcile"):
                nox.update_job(self.root, row["job_id"], stage=stage)
        with self.assertRaisesRegex(ValueError, "reconciliation"):
            nox.update_job(self.root, row["job_id"], decision="prepare")
        self.assertEqual(self.rows()[0]["stage"], "unconfirmed")
        self.assertEqual(nox.update_job(self.root, row["job_id"], stage="rejected")["stage"], "rejected")

    def test_submitted_only_records_a_confirmed_submission(self):
        row = self.add()
        for stage in (None, "ready_for_review", "unconfirmed", "withdrawn"):
            with self.assertRaisesRegex(ValueError, "confirmed submission"):
                nox.update_job(self.root, row["job_id"], stage=stage, decision="submitted")
        with self.assertRaisesRegex(ValueError, "Decision must be"):
            nox.update_job(self.root, row["job_id"], decision="send")
        self.assertEqual(self.rows(), [row])
        self.assertEqual(nox.update_job(self.root, row["job_id"], stage="interview", decision="submitted")["decision"], "submitted")
        # Withdrawing after a confirmed submission keeps the recorded fact.
        self.assertEqual(nox.update_job(self.root, row["job_id"], stage="withdrawn")["decision"], "submitted")
        nox.set_decision(self.root, row["job_id"], "hold")  # the existing decision command still works

    def test_update_job_neutralises_formulas(self):
        row = self.add()
        value = '=HYPERLINK("https://example.com","click")'
        nox.update_job(self.root, row["job_id"], next_action=value, salary="+44 negotiable")
        raw = (self.root / "tracker/jobs.csv").read_text()
        self.assertIn("'=HYPERLINK", raw)
        self.assertIn("'+44", raw)
        self.assertEqual((self.rows()[0]["next_action"], self.rows()[0]["salary"]), (value, "+44 negotiable"))

    def test_package_links_tracker_row_without_downgrading(self):
        row = self.add()
        result = nox.create_package(self.root, "Example Studio", "Coordinator", "https://example.com/jobs/42?utm_source=feed", "2026-10")
        self.assertTrue(result["tracker_updated"])
        self.assertEqual((self.rows()[0]["stage"], self.rows()[0]["package"]), ("preparing", result["package"]))
        self.assertEqual(nox.update_job(self.root, row["job_id"], package=result["package"])["package"], result["package"])
        nox.update_job(self.root, row["job_id"], stage="ready_for_review")
        again = nox.create_package(self.root, "Example Studio", "Coordinator", "https://example.com/jobs/42", "2026-11")
        self.assertEqual((self.rows()[0]["stage"], self.rows()[0]["package"]), ("ready_for_review", again["package"]))
        untracked = nox.create_package(self.root, "Other Studio", "Coordinator", "https://example.com/jobs/99", "2026-10")
        self.assertFalse(untracked["tracker_updated"])
        config = nox.read_json(self.root / "workspace.json")
        config["tracker"]["backend"] = "sheets"
        nox.write_json(self.root / "workspace.json", config)
        sheets = nox.create_package(self.root, "Third Studio", "Coordinator", "https://example.com/jobs/7", "2026-10")
        self.assertFalse(sheets["tracker_updated"])
        self.assertTrue(all((self.root / r["package"]).is_dir() for r in (untracked, sheets)))

    def test_doctor_explains_dependencies_in_plain_english(self):
        checks = {d["check"]: d for d in nox.doctor(self.root)["dependencies"]}
        self.assertEqual(set(checks), {"Python", "python-docx (CV builder)", "LibreOffice (optional PDF export)"})
        self.assertTrue(checks["Python"]["ok"])
        self.assertTrue(all(d["note"] for d in checks.values()))
        with patch("build_cv.find_soffice", return_value=None), patch.dict(sys.modules, {"docx": None}), \
                patch.object(nox, "has_docx", return_value=False):
            report = nox.doctor(self.root)
        checks = {d["check"]: d for d in report["dependencies"]}
        self.assertFalse(checks["python-docx (CV builder)"]["ok"])
        self.assertIn(".nox-lite/.venv", checks["python-docx (CV builder)"]["note"])
        self.assertFalse(checks["LibreOffice (optional PDF export)"]["ok"])
        self.assertIn("Optional", checks["LibreOffice (optional PDF export)"]["note"])
        self.assertTrue(all(x["ok"] for x in report["local_checks"]))

    def test_workspace_claude_md_imports_instructions(self):
        lines = (self.root / "CLAUDE.md").read_text().splitlines()
        self.assertIn("@AGENTS.md", lines)
        self.assertIn("@.nox-lite/AGENTS.md", lines)

    def test_init_never_copies_internal_plans(self):
        toolkit = Path(self.temporary.name) / "toolkit"
        shutil.copytree(nox.ROOT, toolkit, ignore=shutil.ignore_patterns(".git", ".runtime", ".venv", "__pycache__"))
        (toolkit / "docs/plans/active").mkdir(parents=True, exist_ok=True)
        (toolkit / "docs/plans/active/internal.md").write_text("Maintainer-only plan fixture.\n")
        fresh = Path(self.temporary.name) / "fresh"
        with patch.object(nox, "ROOT", toolkit):
            nox.initialise(fresh, "codex")
        self.assertTrue((fresh / ".nox-lite/docs/tracker.md").is_file())
        self.assertFalse((fresh / ".nox-lite/docs/plans").exists())


class InPlaceSetupTests(unittest.TestCase):
    """Setup turns the downloaded folder into the workspace, so the person never switches folders."""
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nox-in-place-")
        self.addCleanup(self.temporary.cleanup)

    def download(self, parent):
        folder = Path(parent) / "nox-lite-main"
        shutil.copytree(nox.ROOT, folder, ignore=shutil.ignore_patterns(".git", ".runtime", ".venv", "__pycache__", "plans"))
        return folder

    def init(self, script, cwd):
        return subprocess.run([sys.executable, str(script), "init", "--workspace", ".", "--provider", "claude"],
                              cwd=cwd, capture_output=True, text=True)

    def assert_workspace(self, root):
        self.assertTrue((root / "workspace.json").is_file())
        self.assertTrue((root / ".nox-lite/scripts/nox.py").is_file())
        for name in ("scripts", "workflows", "templates", "START_HERE.md", "README.md", ".agents", "nox-lite-main"):
            self.assertFalse((root / name).exists(), name)
        self.assertIn("My Nox-Lite workspace", (root / "AGENTS.md").read_text())
        self.assertIn("@.nox-lite/AGENTS.md", (root / "CLAUDE.md").read_text())
        self.assertEqual(len(list(root.glob(".claude/skills/*/SKILL.md"))), 9)
        self.assertEqual(sync_skills.generate(root, installed=True, provider="claude", check=True, source=root / ".nox-lite"), [])
        self.assertTrue(all(x["ok"] for x in nox.doctor(root)["local_checks"]))

    def test_converts_the_downloaded_folder_in_place(self):
        folder = self.download(self.temporary.name)
        result = self.init("scripts/nox.py", folder)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Carry on setting up here", result.stdout)
        self.assertNotIn("leftovers", result.stdout)
        self.assert_workspace(folder)
        again = self.init(".nox-lite/scripts/nox.py", folder)
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("already exists", again.stderr)

    def test_handles_the_extra_folder_windows_unzipping_adds(self):
        outer = Path(self.temporary.name) / "nox-lite-main"
        outer.mkdir()
        self.download(outer)
        result = self.init("nox-lite-main/scripts/nox.py", outer)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_workspace(outer)

    def test_never_converts_a_git_checkout(self):
        folder = self.download(self.temporary.name)
        (folder / ".git").mkdir()
        result = self.init("scripts/nox.py", folder)
        self.assertIn("Git", result.stderr)
        self.assertTrue((folder / "scripts/nox.py").is_file())
        self.assertFalse((folder / ".nox-lite").exists())


class URLTests(unittest.TestCase):
    def test_tracking_removed_but_identity_preserved(self):
        self.assertEqual(nox.canonical_url("HTTPS://EXAMPLE.com:443/jobs/42/?utm_source=x&jobId=7#top"), "https://example.com/jobs/42?jobId=7")
        self.assertEqual(nox.identity("https://jobs.ashbyhq.com/example/42/application"), nox.identity("https://jobs.ashbyhq.com/example/42"))
        self.assertNotEqual(nox.identity("https://example.com/?id=1"), nox.identity("https://example.com/?id=2"))

    def test_credentials_and_non_web_urls_rejected(self):
        for value in ("file:///tmp/cv", "javascript:alert(1)", "https://user:secret@example.com/job", "not a URL"):
            with self.assertRaises(ValueError):
                nox.canonical_url(value)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nox-package-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "private"
        nox.initialise(self.root, "codex")
        result = nox.create_package(self.root, "Example Studio", "Coordinator", "https://example.com/jobs/42", "2026-10")
        self.package = self.root / result["package"]
        for filename in ("job.md", "answers.md"):
            (self.package / filename).write_text("Fictional completed fixture for hash tests; no real authorization.\n")
        shutil.copy2(nox.ROOT / "examples/candidate/cv.json", self.package / "cv.json")
        (self.package / "exports").mkdir()
        # Deliberately just bytes: these tests verify snapshot integrity, not document rendering.
        (self.package / "exports/cv.pdf").write_bytes(b"fictional upload bytes, not a rendered PDF")
        self.revision = nox.seal(self.package)["revision"]
        self.approval = dict(revision=self.revision, approved_at="2026-10-14T09:00:00Z", user_reference="synthetic test only", approval_quote="TEST FIXTURE ONLY", submission_authorization_quote="TEST FIXTURE ONLY", form_checked_at="2026-10-14T08:59:00Z", render_evidence="synthetic fixture; not a real visual check", withdrawn=False)
        nox.write_json(self.package / "review/approval.json", self.approval)

    def test_no_package_overwrite(self):
        with self.assertRaisesRegex(ValueError, "already exists"):
            nox.create_package(self.root, "Example Studio", "Coordinator", "https://example.com/jobs/42", "2026-10")

    def test_changed_or_new_material_invalidates_approval(self):
        nox.check_package(self.package)
        path = self.package / "exports/letter.docx"
        path.write_bytes(b"new attachment")
        with self.assertRaisesRegex(ValueError, "changed"):
            nox.check_package(self.package)
        path.unlink()
        (self.package / "answers.md").write_text("Changed commitment")
        with self.assertRaisesRegex(ValueError, "changed"):
            nox.check_package(self.package)

    def test_missing_seal_or_approval_is_explained(self):
        (self.package / "review/approval.json").unlink()
        with self.assertRaisesRegex(ValueError, "Not approved yet"):
            nox.check_package(self.package)
        (self.package / "review/manifest.json").unlink()
        with self.assertRaisesRegex(ValueError, "Not sealed yet"):
            nox.check_package(self.package)

    def test_seal_refuses_unfinished_files(self):
        (self.package / "cover-letter.md").write_text("Dear {{hiring manager}},\n")
        with self.assertRaisesRegex(ValueError, "Unfinished template: cover-letter.md"):
            nox.seal(self.package)
        (self.package / "cover-letter.md").unlink()
        (self.package / "answers.md").write_text("{{Replace this line once every field on the form is listed below.}}\n")
        with self.assertRaisesRegex(ValueError, "Unfinished template: answers.md"):
            nox.seal(self.package)

    def test_reseal_archives_manifest_and_needs_matching_approval(self):
        result = nox.seal(self.package)
        self.assertNotEqual(result["revision"], self.revision)
        self.assertEqual(len(list((self.package / "review/archive").glob("*.json"))), 1)
        with self.assertRaisesRegex(ValueError, "different revision"):
            nox.check_package(self.package)

    def test_incomplete_or_withdrawn_approval_is_blocked(self):
        for key in ("user_reference", "approval_quote", "submission_authorization_quote", "render_evidence"):
            data = dict(self.approval, **{key: ""})
            nox.write_json(self.package / "review/approval.json", data)
            with self.assertRaisesRegex(ValueError, "incomplete"):
                nox.check_package(self.package)
        nox.write_json(self.package / "review/approval.json", dict(self.approval, withdrawn=True))
        with self.assertRaisesRegex(ValueError, "withdrawn"):
            nox.check_package(self.package)

    def test_snapshot_keeps_exact_bytes_and_blocks_retry(self):
        result = nox.create_attempt(self.package)
        record = nox.read_json(result["attempt"])
        self.assertEqual(record["snapshot_state"], "complete")
        self.assertEqual(record["outcome"], "unconfirmed")
        for name, checksum in record["manifest"]["files"].items():
            self.assertEqual(nox.digest(Path(result["snapshot"]) / name), checksum)
        (self.package / "answers.md").write_text("Later edits must not affect the snapshot")
        self.assertNotEqual((Path(result["snapshot"]) / "answers.md").read_text(), (self.package / "answers.md").read_text())
        nox.seal(self.package)
        approval = dict(self.approval, revision=nox.read_json(self.package / "review/manifest.json")["revision"])
        nox.write_json(self.package / "review/approval.json", approval)
        with self.assertRaisesRegex(ValueError, "uncertain"):
            nox.create_attempt(self.package)

    def test_unknown_and_confirmed_outcomes_block_retries(self):
        result = nox.create_attempt(self.package)
        record = nox.read_json(result["attempt"])
        for value in ("confirmed", "unconfirmed", "typo", None):
            record["outcome"] = value
            nox.write_json(result["attempt"], record)
            with self.assertRaisesRegex(ValueError, "reconciliation"):
                nox.check_package(self.package)

    def test_retry_requires_documented_failure(self):
        result = nox.create_attempt(self.package)
        record = nox.read_json(result["attempt"])
        record["outcome"] = "failed"
        nox.write_json(result["attempt"], record)
        with self.assertRaisesRegex(ValueError, "evidence-file"):
            nox.check_package(self.package)
        (self.package / "submission/error.md").write_text("Fixture: explicit validation error, no submission accepted.")
        record["confirmation_evidence"] = "submission/error.md"
        nox.write_json(result["attempt"], record)
        nox.create_attempt(self.package)
        self.assertEqual(len(list((self.package / "submission").glob("*-attempt.json"))), 2)

    def test_interrupted_snapshot_leaves_uncertainty(self):
        with patch.object(nox.shutil, "copy2", side_effect=OSError("simulated disk failure")):
            with self.assertRaises(OSError):
                nox.create_attempt(self.package)
        records = list((self.package / "submission").glob("*-attempt.json"))
        self.assertEqual(len(records), 1)
        self.assertEqual(nox.read_json(records[0])["snapshot_state"], "pending")
        with self.assertRaisesRegex(ValueError, "uncertain"):
            nox.create_attempt(self.package)

    def test_concurrent_attempts_create_at_most_one(self):
        def attempt():
            try:
                return nox.create_attempt(self.package)
            except ValueError:
                return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: attempt(), range(2)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(len(list((self.package / "submission").glob("*-attempt.json"))), 1)

    def test_symlinked_export_cannot_escape_package(self):
        external = Path(self.temporary.name) / "outside.pdf"
        external.write_bytes(b"private data outside package")
        (self.package / "exports/escape.pdf").symlink_to(external)
        with self.assertRaisesRegex(ValueError, "inside"):
            nox.seal(self.package)


if __name__ == "__main__":
    unittest.main()
