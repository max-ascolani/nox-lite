"""The readable tracker copies: status words, a valid Excel file, a safe page, columns, and writes that never fail because of them."""
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nox
import tracker_view as tv

UPDATED = datetime(2026, 10, 16, 10, 42, tzinfo=timezone(timedelta(hours=1)))


def row(**values):
    base = dict.fromkeys(nox.FIELDS, "")
    base.update(job_id="0" * 16, company="Example Studio", role="Coordinator", url="https://example.com/jobs/1",
                stage="discovered", checked_at="2026-10-15T09:00:00+01:00")
    base.update(values)
    return base


def page_data(html):
    return json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S).group(1))


class RenderTests(unittest.TestCase):
    def test_status_words_put_what_needs_the_person_first(self):
        self.assertEqual(tv.status(row(stage="ready_for_review")), ("Ready for you to review", "needs"))
        self.assertEqual(tv.status(row(decision="prepare")), ("Queued to prepare", "progress"))
        self.assertEqual(tv.status(row(decision="decline")), ("You passed", "closed"))
        # Once an application was sent or attempted, the stage wins over an old decision.
        self.assertEqual(tv.status(row(stage="applied", decision="hold")), ("Applied", "applied"))
        self.assertEqual(tv.status(row(stage="unconfirmed", decision="decline")), ("Checking it was sent", "progress"))
        order = [job["row"]["company"] for job in tv.jobs([row(company="Sent", stage="applied"),
                                                           row(company="Review", stage="ready_for_review"),
                                                           row(company="Talk", stage="interview")])]
        self.assertEqual(order, ["Review", "Talk", "Sent"])

    def test_excel_file_is_valid_and_text_stays_text(self):
        rows = [row(company="=HYPERLINK(\"https://example.com\")", fit="4/5: close match", package="applications/2026-10/a b",
                    url="https://example.com/jobs/1?a=1&b=2", stage="applied", applied_at="2026-10-15T14:05:00+01:00"),
                row(company="Bad links", url="javascript:alert(1)", package="../../outside", next_action="Bell \x07 here")]
        data = tv.xlsx(rows, tv.DETAIL["detailed"], UPDATED)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            parts = {name: archive.read(name) for name in archive.namelist()}
        for body in parts.values():
            ET.fromstring(body)  # every part is well-formed XML
        sheet = parts["xl/worksheets/sheet1.xml"].decode()
        self.assertNotIn("<f>", sheet)  # no formulas, whatever the text
        self.assertIn('=HYPERLINK', parts["xl/sharedStrings.xml"].decode())
        self.assertNotIn("\x07", parts["xl/sharedStrings.xml"].decode())
        links = parts["xl/worksheets/_rels/sheet1.xml.rels"].decode()
        self.assertIn("https://example.com/jobs/1?a=1&amp;b=2", links)
        self.assertIn("../applications/2026-10/a%20b/", links)
        self.assertNotIn("javascript", links)
        self.assertNotIn("outside", links)
        self.assertEqual(sheet.count("<hyperlink "), 2)
        self.assertIn('<pane xSplit="1" ySplit="4"', sheet)

    def test_columns_follow_the_detail_level(self):
        def headings(columns):
            with zipfile.ZipFile(io.BytesIO(tv.xlsx([row()], columns, UPDATED))) as archive:
                strings = re.findall(r"<t[^>]*>(.*?)</t>", archive.read("xl/sharedStrings.xml").decode())
            return [s for s in strings if s in {heading for heading, _ in tv.COLUMNS.values()}]
        self.assertEqual(headings(tv.DETAIL["simple"]), ["Company", "Role", "Status", "Next step", "Fit", "Applied", "Job ad"])
        self.assertIn("Salary", headings(tv.DETAIL["detailed"]))
        job = page_data(tv.page([row(salary="GBP 40k", location="Leeds", fit="4/5: close")], tv.DETAIL["simple"], UPDATED))["jobs"][0]
        self.assertEqual((job["salary"], job["location"], job["reason"], job["score"]), ("", "", "", 4))

    def test_settings_keep_required_columns_and_refuse_unknown_ones(self):
        view, columns = tv.settings(None)
        self.assertEqual((view["format"], view["detail"], view["columns"]), ("page", "detailed", None))
        view, columns = tv.settings(view, "both", "simple", add=["salary"])
        self.assertEqual(columns, ["company", "role", "status", "next_step", "fit", "salary", "applied", "link"])
        self.assertEqual(view["columns"], columns)
        view, columns = tv.settings(view, drop=["salary"])
        self.assertIsNone(view["columns"])  # back to the plain preset
        self.assertEqual(tv.settings(view, detail="detailed")[1], tv.DETAIL["detailed"])
        with self.assertRaisesRegex(ValueError, "always shown"):
            tv.settings(view, drop=["status"])
        with self.assertRaisesRegex(ValueError, "Unknown tracker column pay"):
            tv.settings(view, add=["pay"])
        with self.assertRaisesRegex(ValueError, "format"):
            tv.settings({"format": "pdf"})

    def test_page_cannot_be_broken_by_job_text(self):
        evil = row(company="</script><img src=x onerror=alert(1)>", role="<b>x</b> & y", url="javascript:alert(1)",
                   package="../../outside", next_action="You: check it")
        html = tv.page([evil], tv.DETAIL["detailed"], UPDATED)
        self.assertNotIn("</script><img", html)
        self.assertEqual(html.count("</script>"), 2)  # the data block and the page script, nothing more
        job = page_data(html)["jobs"][0]
        self.assertEqual((job["company"], job["role"]), (evil["company"], evil["role"]))
        self.assertEqual((job["url"], job["package"], job["who"], job["next"]), ("", "", "You", "Check it"))
        self.assertIn("default-src 'none'", html)
        self.assertNotRegex(html, r"""(?:src|href)=["']https?:""")  # nothing loaded from the internet


class WorkspaceViewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nox-view-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "private"
        nox.initialise(self.root, "claude")
        self.page = self.root / "tracker/Job tracker.html"
        self.excel = self.root / "tracker/Job tracker.xlsx"

    def test_every_helper_write_rebuilds_the_page(self):
        self.assertEqual(page_data(self.page.read_text())["jobs"], [])
        job = nox.add_job(self.root, "Example Studio", "Coordinator", "https://example.com/jobs/42")
        self.assertEqual(page_data(self.page.read_text())["jobs"][0]["label"], "New: your call")
        nox.set_decision(self.root, job["job_id"], "prepare")
        self.assertEqual(page_data(self.page.read_text())["jobs"][0]["label"], "Queued to prepare")
        package = nox.create_package(self.root, "Example Studio", "Coordinator", "https://example.com/jobs/42", "2026-10")
        self.assertEqual(page_data(self.page.read_text())["jobs"][0]["package"], f"../{package['package']}/")
        nox.update_job(self.root, job["job_id"], stage="ready_for_review")
        self.assertEqual(page_data(self.page.read_text())["jobs"][0]["label"], "Ready for you to review")
        self.assertFalse(self.excel.exists())

    def test_view_command_switches_format_and_removes_the_stale_copy(self):
        nox.add_job(self.root, "Example Studio", "Coordinator", "https://example.com/jobs/42")
        result = nox.view(self.root, "both", "simple")
        self.assertEqual(result["files"], ["tracker/Job tracker.html", "tracker/Job tracker.xlsx"])
        self.assertEqual(nox.read_json(self.root / "workspace.json")["tracker"]["view"]["detail"], "simple")
        with zipfile.ZipFile(self.excel) as archive:
            self.assertIn("Example Studio", archive.read("xl/sharedStrings.xml").decode())
        nox.view(self.root, "excel")
        self.assertFalse(self.page.exists())
        self.assertTrue(self.excel.exists())

    def test_a_failed_view_never_fails_the_tracker_write(self):
        stderr = io.StringIO()
        with patch.object(tv, "page", side_effect=PermissionError("file is open")), patch("sys.stderr", stderr):
            job = nox.add_job(self.root, "Example Studio", "Coordinator", "https://example.com/jobs/42")
        self.assertEqual(nox.read_rows(self.root / "tracker/jobs.csv"), [job])
        self.assertIn("tracker was saved", stderr.getvalue())
        self.assertFalse((self.root / "tracker/jobs.lock").exists())

    def test_older_workspaces_get_the_page(self):
        config = nox.read_json(self.root / "workspace.json")
        del config["tracker"]["view"]
        nox.write_json(self.root / "workspace.json", config)
        self.page.unlink()
        self.assertEqual(nox.refresh(self.root)["tracker_view"], ["tracker/Job tracker.html"])

    def test_sheets_mode_points_to_the_sheet(self):
        config = nox.read_json(self.root / "workspace.json")
        config["tracker"]["backend"] = "sheets"
        nox.write_json(self.root / "workspace.json", config)
        with self.assertRaisesRegex(ValueError, "Google Sheet"):
            nox.view(self.root)

    def test_cli_from_the_workspace(self):
        result = subprocess.run([sys.executable, ".nox-lite/scripts/nox.py", "view", "--workspace", ".", "--add", "salary"],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["detail"], "detailed")  # salary is already in the detailed set
        self.assertIn("Salary", json.loads(result.stdout)["columns"])


if __name__ == "__main__":
    unittest.main()
