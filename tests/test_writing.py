import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_letter
import check_writing
import nox

GOOD = """Dear Hiring Manager,

Northwind's move into same-day delivery caught my attention, because I spent three years making that work at a regional courier.

At Example Logistics I cut late deliveries by 18% in six months. My team rebuilt the routing rules with drivers, not around them.

I'd welcome a conversation about the operations role at Northwind.
"""


class WritingCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_clean_letter_has_no_problems(self):
        result = check_writing.check(self.write("letter.md", GOOD), company="Northwind")
        self.assertEqual(result["problems"], [])
        self.assertEqual(result["warnings"], [])

    def test_catches_placeholders_chatter_dashes_and_banned_phrases(self):
        text = "Dear [Company name],\n\nAs an AI, I am passionate about logistics — and {{role}} too. TODO add result.\n"
        problems = " ".join(check_writing.check(self.write("bad.md", text))["problems"])
        for expected in ("[Company name]", "{{", "TODO", "as an ai", "Em dash", "passionate about"):
            self.assertIn(expected.lower(), problems.lower())

    def test_banned_words_match_whole_words_only(self):
        result = check_writing.check(self.write("ok.md", "Dynamics 365 and leveraged buyouts are fine.\n"))
        self.assertEqual(result["problems"], [])

    def test_wrong_employer_and_missing_employer(self):
        nox.initialise(str(self.root / "ws"), "claude")
        nox.add_job(str(self.root / "ws"), "Contoso", "Ops lead", "https://example.com/jobs/1")
        nox.add_job(str(self.root / "ws"), "Northwind", "Ops lead", "https://example.com/jobs/2")
        letter = self.write("letter.md", GOOD.replace("the operations role at Northwind", "the operations role at Contoso"))
        result = check_writing.check(letter, company="Northwind", workspace=str(self.root / "ws"))
        self.assertTrue(any("Contoso" in p for p in result["problems"]))
        other = self.write("other.md", "I'd welcome a conversation.\n")
        self.assertTrue(check_writing.check(other, company="Northwind")["warnings"])

    def test_short_company_name_counts_as_named(self):
        letter = self.write("short.md", "At Elmbridge I'd bring the same habits.\n")
        self.assertEqual(check_writing.check(letter, company="Elmbridge Learning Studio Ltd")["warnings"], [])
        letter = self.write("suffix.md", "Joining Acme Widgets would suit me.\n")
        self.assertEqual(check_writing.check(letter, company="Acme Widgets, Inc.")["warnings"], [])
        letter = self.write("the.md", "The team would suit me.\n")
        self.assertTrue(check_writing.check(letter, company="The Body Shop")["warnings"])

    def test_numbers_must_appear_in_profile_or_job_ad(self):
        nox.initialise(str(self.root / "ws"), "claude")
        (self.root / "ws/profile/experience.md").write_text("Cut late deliveries by 18% over six months.\n", encoding="utf-8")
        package = self.root / "ws/applications/pkg"
        self.write("ws/applications/pkg/job.md", "Manage a fleet of 40 vans.\n")
        letter = self.write("letter.md", "I cut late deliveries by 18%, ran 40 vans and saved £1,250,000.\n")
        result = check_writing.check(letter, workspace=str(self.root / "ws"), package=str(package))
        numbers = [w for w in result["warnings"] if w.startswith("Numbers")]
        self.assertEqual(len(numbers), 1)
        self.assertIn("1250000", numbers[0])
        self.assertNotIn("18", numbers[0].split(":", 1)[1])

    def test_form_audit_numbers_only_come_from_answers(self):
        nox.initialise(str(self.root / "ws"), "claude")
        package = self.root / "ws/applications/pkg"
        self.write("ws/applications/pkg/job.md", "Ops role.\n")
        audit = self.write("ws/applications/pkg/answers.md", (
            "Form URL: https://example.com/jobs/12345\nChecked on: 2026-10-02\n\n"
            "| # | Field | Type, options, limit | Required | Answer | Source |\n|---|---|---|---|---|---|\n"
            "| 1 | Why us? | Text, 150 words | Yes | See below | tailored |\n"
            "| 2 | Years of experience | Number | Yes | 7 | question |\n\n"
            "**1. Why us?** (88 words)\n\nI grew bookings by 40%.\n"))
        result = check_writing.check(audit, workspace=str(self.root / "ws"), package=str(package))
        numbers = [w for w in result["warnings"] if w.startswith("Numbers")]
        self.assertEqual(len(numbers), 1)
        self.assertEqual(numbers[0].split(": ", 1)[1], "7, 40")

    def test_many_i_openers_and_word_limit(self):
        text = "I led the team. I built the tool. I ran the launch.\n"
        result = check_writing.check(self.write("i.md", text), max_words=5)
        self.assertTrue(any("\"I\"" in w for w in result["warnings"]))
        self.assertTrue(any("limit is 5" in p for p in result["problems"]))

    def test_cv_json_prose_is_checked_but_urls_are_not(self):
        cv = nox.read_json(nox.ROOT / "examples/candidate/cv.json")
        cv["summary"] = "Results-driven operations lead."
        path = self.write("cv.json", json.dumps(cv))
        problems = check_writing.check(path)["problems"]
        self.assertEqual(problems, ["Banned phrase: \"results-driven\""])


class LetterParagraphTests(unittest.TestCase):
    def test_sign_off_keeps_line_breaks_and_prose_is_joined(self):
        text = "Dear team,\n\nI ran the depot\nfor two years, cutting delays in half and keeping every route covered through the winter.\n\nKind regards,\nJordan Rivera\n"
        self.assertEqual(build_letter.paragraphs(text), [
            "Dear team,",
            "I ran the depot for two years, cutting delays in half and keeping every route covered through the winter.",
            "Kind regards,\nJordan Rivera",
        ])


@unittest.skipUnless(importlib.util.find_spec("docx"), "Install requirements-docs.txt for document tests")
class LetterBuildTests(unittest.TestCase):
    def test_letter_has_header_paragraphs_and_chosen_font(self):
        cv = nox.read_json(nox.ROOT / "examples/candidate/cv.json")
        with tempfile.TemporaryDirectory() as directory:
            out = build_letter.build("# Cover letter\n\n" + GOOD, cv, Path(directory) / "letter.docx", font="Arial")
            with zipfile.ZipFile(out) as archive:
                document = archive.read("word/document.xml").decode()
                styles = archive.read("word/styles.xml").decode()
            self.assertIn(cv["name"], document)
            self.assertIn("same-day delivery", document)
            self.assertEqual(document.count('w:val="dashSmallGap"'), 2)  # same header as the CV
            self.assertNotIn("# Cover letter", document)
            self.assertNotIn("asciiTheme", styles)
            with self.assertRaises(ValueError):
                build_letter.build(GOOD, cv, out)

    def test_rejects_empty_or_unfinished_letters(self):
        cv = nox.read_json(nox.ROOT / "examples/candidate/cv.json")
        with tempfile.TemporaryDirectory() as directory:
            for text in ("", "# Only a heading\n", "Dear {{name}}\n"):
                with self.assertRaises(ValueError):
                    build_letter.build(text, cv, Path(directory) / "x.docx")


if __name__ == "__main__":
    unittest.main()
