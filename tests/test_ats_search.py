"""Offline checks for the ATS job-board search; every network call is replaced by fixtures."""
import contextlib
import csv
from datetime import date
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ats_search
import nox

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ats"
GH = "https://boards-api.greenhouse.io/v1/boards/examplelabs/jobs"
LEVER = "https://api.lever.co/v0/postings/sampleco?mode=json"
LEVER_EU = "https://api.eu.lever.co/v0/postings/sampleco?mode=json"
ASHBY = "https://api.ashbyhq.com/posting-api/job-board/demoworks"
RECRUITEE = "https://fictionalbv.recruitee.com/api/offers/"
WORKABLE = "https://apply.workable.com/api/v1/widget/accounts/mockhouse"
COMPANIES = ["https://job-boards.greenhouse.io/examplelabs", "lever:sampleco", "https://jobs.ashbyhq.com/demoworks",
             "https://fictionalbv.recruitee.com", "workable:mockhouse"]
TODAY = date(2026, 10, 15)


def payload(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def routes():
    return {GH: payload("greenhouse"), LEVER: payload("lever"), ASHBY: payload("ashby"),
            RECRUITEE: payload("recruitee"), WORKABLE: payload("workable")}


def not_found(url):
    return HTTPError(url, 404, "Not Found", {}, None)


class Fake:
    """Answers by URL; a tuple answers successive calls in turn; unknown URLs are 404."""
    def __init__(self, table):
        self.table, self.calls = table, []

    def __call__(self, url):
        self.calls.append(url)
        value = self.table.get(url, not_found(url))
        if isinstance(value, tuple):
            value = value[min(self.calls.count(url), len(value)) - 1]
        if isinstance(value, Exception):
            raise value
        return value


def titles(report):
    return sorted(r["title"] for r in report["results"])


class BoardParsingTests(unittest.TestCase):
    def test_board_and_job_links_resolve_to_the_board(self):
        cases = {
            "https://boards.greenhouse.io/acme": ("greenhouse", "acme", ""),
            "https://job-boards.greenhouse.io/acme/jobs/4012345?gh_jid=4012345": ("greenhouse", "acme", ""),
            "https://job-boards.eu.greenhouse.io/acme": ("greenhouse", "acme", "eu"),
            "https://boards.greenhouse.io/embed/job_app?for=acme&token=4012345": ("greenhouse", "acme", ""),
            "https://jobs.lever.co/acme/6f1c2a9e-0b3d-4c55-9e1a-2b7d8f0a1c11/apply": ("lever", "acme", ""),
            "https://jobs.eu.lever.co/acme": ("lever", "acme", "eu"),
            "https://jobs.ashbyhq.com/acme/1b2c3d4e-5f60-4718-9a0b-1c2d3e4f5a66/application": ("ashby", "acme", ""),
            "https://acme.recruitee.com/o/customer-support": ("recruitee", "acme", ""),
            "acme.recruitee.com": ("recruitee", "acme", ""),
            "https://apply.workable.com/acme/j/AB12CD34EF/": ("workable", "acme", ""),
            "https://apply.workable.com/acme": ("workable", "acme", ""),
            "greenhouse:acme": ("greenhouse", "acme", ""),
            " Lever: acme ": ("lever", "acme", ""),
            "ashby:acme": ("ashby", "acme", ""),
            "recruitee:acme": ("recruitee", "acme", ""),
            "workable:acme": ("workable", "acme", ""),
        }
        for entry, expected in cases.items():
            with self.subTest(entry=entry):
                self.assertEqual(ats_search.board(entry), expected)

    def test_unknown_or_unclear_entries_are_explained(self):
        for entry in ("https://careers.example.com/jobs/42", "smartrecruiters:acme", "Acme Ltd",
                      "https://jobs.workable.com/view/abc", "https://example.com#.recruitee.com"):
            with self.subTest(entry=entry), self.assertRaisesRegex(ats_search.BoardError, "not a supported job board; give the careers page"):
                ats_search.board(entry)
        for entry in ("https://apply.workable.com/j/AB12CD34EF", "https://jobs.lever.co/"):
            with self.subTest(entry=entry), self.assertRaisesRegex(ats_search.BoardError, "doesn't show whose"):
                ats_search.board(entry)

    def test_companies_file_ignores_blank_lines_and_comments(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "companies.txt"
            path.write_text("﻿# my shortlist\n\ngreenhouse:acme\nhttps://jobs.lever.co/acme  # inline note\n   \n", encoding="utf-8")
            self.assertEqual(ats_search.read_companies(path), ["greenhouse:acme", "https://jobs.lever.co/acme"])


class NormalisationTests(unittest.TestCase):
    def jobs(self, ats, slug, name):
        return {j["title"]: j for j in ats_search.normalise(ats, slug, payload(name))}

    def check(self, job, **expected):
        self.assertEqual({k: job[k] for k in expected}, expected)
        self.assertEqual(job["job_id"], nox.identity(job["url"]))

    def test_greenhouse(self):
        jobs = self.jobs("greenhouse", "examplelabs", "greenhouse")
        self.check(jobs["Senior Product Manager"], company="Example Labs", location="London, United Kingdom", remote=False,
                   posted="2026-10-01", ats="greenhouse", url="https://job-boards.greenhouse.io/examplelabs/jobs/4012345")
        # Identity parameters stay; tracking parameters go.
        self.check(jobs["Data Analyst"], remote=True, posted="2026-06-01",
                   url="https://careers.example.com/jobs/data-analyst?gh_jid=4012346")
        self.check(jobs["Engineering Manager"], location="Remote - Europe", remote=True, posted="2026-10-12")

    def test_lever(self):
        jobs = self.jobs("lever", "sampleco", "lever")
        self.check(jobs["Customer Success Manager"], company="sampleco", location="Berlin; Munich", remote=False, posted="2026-10-12",
                   url="https://jobs.lever.co/sampleco/6f1c2a9e-0b3d-4c55-9e1a-2b7d8f0a1c11")
        self.check(jobs["Front-End Developer"], location="Lisbon", remote=True, posted="2026-09-01")
        self.check(jobs["Marketing Intern"], remote=False, posted="2026-10-14")

    def test_ashby_skips_unlisted_and_prefers_workplace_type(self):
        jobs = self.jobs("ashby", "demoworks", "ashby")
        self.assertEqual(sorted(jobs), ["Operations Associate", "Product Designer"])
        self.check(jobs["Product Designer"], company="demoworks", location="New York, NY; Remote (US)", remote=True, posted="2026-10-11",
                   url="https://jobs.ashbyhq.com/demoworks/1b2c3d4e-5f60-4718-9a0b-1c2d3e4f5a66")
        self.check(jobs["Operations Associate"], location="Toronto", remote=False, posted="2026-08-20")

    def test_recruitee(self):
        jobs = self.jobs("recruitee", "fictionalbv", "recruitee")
        self.check(jobs["Customer Support Specialist"], company="Fictional BV", location="Amsterdam, Noord-Holland, Netherlands",
                   remote=False, posted="2026-10-13", url="https://fictionalbv.recruitee.com/o/customer-support-specialist")
        self.check(jobs["Account Executive"], location="Rotterdam, Netherlands", remote=True, posted="2026-09-02")

    def test_workable(self):
        jobs = self.jobs("workable", "mockhouse", "workable")
        self.check(jobs["Warehouse Supervisor"], company="Mockhouse Ltd", location="Athens, Attica, Greece", remote=False,
                   posted="2026-10-02", url="https://apply.workable.com/j/AB12CD34EF")
        self.check(jobs["Senior Data Engineer"], location="Portugal", remote=True, posted="")

    def test_jobs_without_a_usable_link_are_dropped(self):
        data = {"jobs": [{"title": "No link", "absolute_url": None}, {"title": "Bad link", "absolute_url": "mailto:jobs@example.com"}]}
        self.assertEqual(ats_search.normalise("greenhouse", "examplelabs", data), [])


class FilterTests(unittest.TestCase):
    def run_search(self, **options):
        return ats_search.search(COMPANIES, fetch=Fake(routes()), today=TODAY, **options)

    def test_everything_without_filters_newest_first_and_undated_last(self):
        report = self.run_search()
        self.assertEqual((report["searched"], report["scanned"], report["matched"], report["errors"]), (5, 12, 12, []))
        dates = [r["posted"] for r in report["results"]]
        self.assertEqual(dates[0], "2026-10-14")
        self.assertEqual(dates[-1], "")
        self.assertEqual(dates[:-1], sorted(dates[:-1], reverse=True))
        self.assertEqual(report["note"], ats_search.REMINDER)

    def test_keywords_are_whole_words_or_phrases(self):
        self.assertEqual(titles(self.run_search(keywords="manager")),
                         ["Customer Success Manager", "Engineering Manager", "Senior Product Manager"])
        self.assertEqual(titles(self.run_search(keywords="engineer")), ["Senior Data Engineer"])
        self.assertEqual(titles(self.run_search(keywords="Product Manager, designer")), ["Product Designer", "Senior Product Manager"])
        self.assertEqual(titles(self.run_search(keywords="front end")), ["Front-End Developer"])

    def test_exclude_removes_titles_with_any_word(self):
        report = self.run_search(exclude="senior, intern")
        self.assertEqual(report["matched"], 9)
        self.assertFalse(any(word in r["title"] for r in report["results"] for word in ("Senior", "Intern")))
        self.assertEqual(titles(self.run_search(keywords="manager", exclude="senior")), ["Customer Success Manager", "Engineering Manager"])

    def test_location_and_remote(self):
        self.assertEqual(titles(self.run_search(location="berlin")), ["Customer Success Manager", "Marketing Intern"])
        self.assertEqual(titles(self.run_search(location="new york,athens")), ["Product Designer", "Warehouse Supervisor"])
        self.assertEqual(titles(self.run_search(location="lon")), [])  # whole words, so "lon" isn't London
        self.assertEqual(titles(self.run_search(location="remote")),
                         ["Account Executive", "Data Analyst", "Engineering Manager", "Front-End Developer",
                          "Product Designer", "Senior Data Engineer"])

    def test_max_age_keeps_undated_jobs(self):
        report = self.run_search(max_age_days=30)
        self.assertEqual(report["matched"], 8)
        self.assertNotIn("Data Analyst", titles(report))
        self.assertIn("Senior Data Engineer", titles(report))

    def test_limit_counts_all_matches(self):
        report = self.run_search(limit=2)
        self.assertEqual(titles(report), ["Customer Support Specialist", "Marketing Intern"])
        self.assertEqual(report["matched"], 12)

    def test_repeated_companies_are_searched_once(self):
        fake = Fake(routes())
        report = ats_search.search(["lever:sampleco", "https://jobs.lever.co/sampleco/6f1c2a9e-0b3d-4c55-9e1a-2b7d8f0a1c11"], fetch=fake)
        self.assertEqual((fake.calls, report["searched"], report["matched"]), ([LEVER], 1, 3))


class TrackerTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.tracker = self.folder / "jobs.csv"
        tracked = "https://jobs.lever.co/sampleco/6f1c2a9e-0b3d-4c55-9e1a-2b7d8f0a1c11/?utm_campaign=alert"
        nox.write_rows(self.tracker, [{"job_id": nox.identity(tracked), "company": "SampleCo", "role": "Customer Success Manager", "url": tracked}])

    def test_tracked_jobs_are_left_out_unless_asked(self):
        tracked = ats_search.tracked_urls(self.tracker)
        report = ats_search.search(COMPANIES, fetch=Fake(routes()), tracked=tracked)
        self.assertEqual((report["matched"], report["hidden_tracked"]), (11, 1))
        self.assertNotIn("Customer Success Manager", titles(report))
        report = ats_search.search(COMPANIES, fetch=Fake(routes()), tracked=tracked, include_tracked=True)
        flagged = [r["title"] for r in report["results"] if r["already_tracked"]]
        self.assertEqual((report["matched"], flagged), (12, ["Customer Success Manager"]))

    def test_any_csv_with_a_url_column_works(self):
        other = self.folder / "export.csv"
        other.write_text("Company,url\nExample Labs,https://job-boards.greenhouse.io/examplelabs/jobs/4012345/\nBlank,\n", encoding="utf-8")
        self.assertEqual(ats_search.tracked_urls(other), {"https://job-boards.greenhouse.io/examplelabs/jobs/4012345"})
        other.write_text("company,role\nExample Labs,Analyst\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no url column"):
            ats_search.tracked_urls(other)


class OutputTests(unittest.TestCase):
    def main(self, *argv):
        out = io.StringIO()
        with patch.object(ats_search, "fetch_json", Fake(routes())), contextlib.redirect_stdout(out):
            code = ats_search.main(list(argv))
        return code, out.getvalue()

    def test_json_output(self):
        code, out = self.main("--company", COMPANIES[0], "--company", "https://careers.example.com/jobs", "--json", "--keywords", "manager")
        report = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual((report["searched"], titles(report)), (1, ["Engineering Manager", "Senior Product Manager"]))
        self.assertEqual(report["errors"], [{"company": "https://careers.example.com/jobs", "error": ats_search.UNSUPPORTED}])
        self.assertEqual(set(report["results"][0]), set(ats_search.COLUMNS) | {"already_tracked"})

    def test_csv_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "leads.csv"
            code, out = self.main(*sum((["--company", c] for c in COMPANIES), []), "--location", "remote", "--csv", str(path))
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(code, 0)
        self.assertIn(f"Saved to {path}.", out)
        self.assertEqual(list(rows[0]), ats_search.COLUMNS)
        self.assertEqual(len(rows), 6)
        self.assertEqual({r["remote"] for r in rows}, {"yes"})
        for row in rows:
            self.assertEqual(row["job_id"], nox.identity(nox.canonical_url(row["url"])))

    def test_table_output_has_summary_errors_and_reminder(self):
        code, out = self.main("--company", "lever:sampleco", "--company", "greenhouse:missing", "--exclude", "intern")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("COMPANY"))
        self.assertIn("Customer Success Manager", out)
        self.assertIn("2 leads from 1 job boards (3 jobs checked).", out)
        self.assertIn("Couldn't search greenhouse:missing: " + ats_search.NOT_FOUND, out)
        self.assertTrue(out.rstrip().endswith(ats_search.REMINDER))

    def test_nothing_searchable_exits_with_failure(self):
        self.assertEqual(self.main("--company", "greenhouse:missing")[0], 1)
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(ats_search.main([]), 1)
        self.assertIn("at least one company", err.getvalue())


class ErrorHandlingTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(ats_search, "RETRY_PAUSE", 0)
        patcher.start()
        self.addCleanup(patcher.stop)

    def search(self, table, companies):
        fake = Fake(table)
        return ats_search.search(companies, fetch=fake), fake.calls

    def test_missing_board_is_reported(self):
        report, _ = self.search({}, ["greenhouse:missing"])
        self.assertEqual(report["errors"], [{"company": "greenhouse:missing", "error": ats_search.NOT_FOUND}])

    def test_lever_falls_back_to_the_eu_service(self):
        report, calls = self.search({LEVER_EU: payload("lever")}, ["lever:sampleco"])
        self.assertEqual((calls, report["matched"], report["errors"]), ([LEVER, LEVER_EU], 3, []))
        report, calls = self.search({LEVER_EU: payload("lever")}, ["https://jobs.eu.lever.co/sampleco"])
        self.assertEqual((calls, report["matched"]), ([LEVER_EU], 3))

    def test_timeouts_are_retried_once(self):
        for failure in (TimeoutError("timed out"), URLError(TimeoutError("timed out"))):
            with self.subTest(failure=failure):
                report, calls = self.search({GH: failure}, ["greenhouse:examplelabs"])
                self.assertEqual(calls, [GH, GH])
                self.assertIn("didn't answer within 15 seconds", report["errors"][0]["error"])

    def test_server_errors_are_retried_once(self):
        report, calls = self.search({GH: (HTTPError(GH, 503, "Unavailable", {}, None), payload("greenhouse"))}, ["greenhouse:examplelabs"])
        self.assertEqual((calls, report["matched"], report["errors"]), ([GH, GH], 3, []))
        report, calls = self.search({GH: HTTPError(GH, 500, "Error", {}, None)}, ["greenhouse:examplelabs"])
        self.assertEqual(len(calls), 2)
        self.assertIn("HTTP 500", report["errors"][0]["error"])

    def test_other_failures_are_reported_without_retry(self):
        cases = [(HTTPError(GH, 403, "Forbidden", {}, None), "HTTP 403"),
                 (URLError(ConnectionRefusedError("refused")), "couldn't reach"),
                 (json.JSONDecodeError("Expecting value", "<html>", 0), "something other than job data")]
        for failure, message in cases:
            with self.subTest(message=message):
                report, calls = self.search({GH: failure}, ["greenhouse:examplelabs"])
                self.assertEqual(len(calls), 1)
                self.assertIn(message, report["errors"][0]["error"])
        report, _ = self.search({GH: {"unexpected": []}}, ["greenhouse:examplelabs"])
        self.assertIn("unexpected reply", report["errors"][0]["error"])

    def test_one_failing_company_does_not_stop_the_others(self):
        table = routes()
        table[ASHBY] = TimeoutError("timed out")
        report, _ = self.search(table, COMPANIES + ["greenhouse:missing", "https://careers.example.com/jobs"])
        self.assertEqual((report["searched"], report["matched"]), (4, 10))
        self.assertEqual([e["company"] for e in report["errors"]],
                         ["https://careers.example.com/jobs", "https://jobs.ashbyhq.com/demoworks", "greenhouse:missing"])


class FindBoardsTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(ats_search, "RETRY_PAUSE", 0)
        patcher.start()
        self.addCleanup(patcher.stop)

    def find(self, entries, table=None, pages=None):
        pages = pages or {}

        def page(url):
            value = pages.get(url, HTTPError(url, 404, "Not Found", {}, None))
            if isinstance(value, Exception):
                raise value
            return value
        fake = Fake(routes() if table is None else table)
        return ats_search.find_boards(entries, fetch=fake, page=page), fake.calls

    def test_name_guesses(self):
        self.assertEqual(ats_search.guesses("Octopus Energy Ltd"), ["octopusenergy", "octopusenergyltd", "octopus-energy", "octopus"])
        self.assertEqual(ats_search.guesses("Monzo"), ["monzo"])
        self.assertEqual(ats_search.guesses("Société Générale"), ["societegenerale", "societe-generale", "societe"])
        self.assertEqual(ats_search.guesses("Booking.com"), ["booking", "bookingcom"])

    def test_board_names_must_match_exactly(self):
        self.assertTrue(ats_search.same_name("Octopus Energy", "Octopus Energy Group Ltd"))
        self.assertTrue(ats_search.same_name("GoCardless", "Go Cardless"))
        self.assertFalse(ats_search.same_name("Wise", "Wise Worksite Field Sales"))

    def test_empty_boards_count_only_when_given_directly(self):
        empty = {"name": "Nowhere", "jobs": []}
        table = {WORKABLE.replace("mockhouse", "nowherestudio"): empty, WORKABLE.replace("mockhouse", "emptyco"): empty}
        guessed, given = self.find(["Nowhere Studio", "workable:emptyco"], table)[0]
        self.assertEqual((guessed["boards"], guessed["tried"]), ([], ["nowherestudio", "nowhere-studio", "nowhere"]))
        self.assertEqual([(b["board"], b["jobs"]) for b in given["boards"]], [("workable:emptyco", 0)])

    def test_full_name_guess_is_trusted_and_search_stops_at_the_first_hit(self):
        [result], calls = self.find(["Example Labs"])
        self.assertEqual((result["how"], result["tried"]), ("name", ["examplelabs"]))
        self.assertEqual([(b["board"], b["name"], b["jobs"], b["check"]) for b in result["boards"]],
                         [("greenhouse:examplelabs", "Example Labs", 3, "")])
        self.assertEqual(result["boards"][0]["examples"][0], "Senior Product Manager, London, United Kingdom")
        self.assertEqual(len(calls), 6)  # five systems, Lever in two regions, for one guess

    def test_weak_guesses_are_flagged(self):
        [part], _ = self.find(["Demoworks Studio"])
        self.assertEqual(part["tried"], ["demoworksstudio", "demoworks-studio", "demoworks"])
        self.assertEqual([(b["board"], b["check"]) for b in part["boards"]], [("ashby:demoworks", "guessed from part of the name")])
        other = {GH.replace("examplelabs", "northwind"): payload("greenhouse")}
        [wrong], _ = self.find(["Northwind"], other)
        self.assertEqual(wrong["boards"][0]["check"], "the board is called \"Example Labs\"")
        [right], _ = self.find(["Mockhouse"])
        self.assertEqual((right["boards"][0]["name"], right["boards"][0]["check"]), ("Mockhouse Ltd", ""))

    def test_careers_page_links_and_redirects(self):
        html = ('<script src="https://boards.greenhouse.io/embed/job_board/js?for=examplelabs&amp;b=x"></script>'
                '<script>{"jobs":"https:\\/\\/jobs.lever.co\\/sampleco"}</script><a href="https://www.greenhouse.io/">Powered by</a>')
        pages = {"https://careers.example.com/": ("https://careers.example.com/", html),
                 "https://example.com/jobs": ("https://jobs.ashbyhq.com/demoworks", "<html></html>"),
                 "https://blocked.example.com/": HTTPError("https://blocked.example.com/", 403, "Forbidden", {}, None)}
        page, redirect, blocked = self.find(list(pages), pages=pages)[0]
        self.assertEqual((page["how"], [b["board"] for b in page["boards"]]), ("careers page", ["greenhouse:examplelabs", "lever:sampleco"]))
        self.assertEqual([b["board"] for b in redirect["boards"]], ["ashby:demoworks"])
        self.assertEqual((blocked["boards"], blocked["tried"]), ([], []))
        self.assertIn("HTTP 403", blocked["problems"][0])

    def test_board_links_are_checked_and_failures_reported(self):
        results, _ = self.find(["workable:mockhouse", "greenhouse:missing", "Nowhere Studio"], {**routes(), GH.replace("examplelabs", "nowherestudio"): TimeoutError("timed out")})
        found, missing, unknown = results
        self.assertEqual((found["how"], found["boards"][0]["board"]), ("link", "workable:mockhouse"))
        self.assertEqual((missing["boards"], missing["problems"]), ([], []))
        self.assertEqual(unknown["tried"], ["nowherestudio", "nowhere-studio", "nowhere"])
        self.assertTrue(any("greenhouse" in p and "15 seconds" in p for p in unknown["problems"]))

    def test_add_boards_skips_known_and_unconfirmed(self):
        results, _ = self.find(["Example Labs", "lever:sampleco", "Demoworks Studio"])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "companies.txt"
            path.write_text("https://job-boards.greenhouse.io/ExampleLabs  # already here", encoding="utf-8")
            self.assertEqual(ats_search.add_boards(path, results), 1)
            self.assertEqual(path.read_text(encoding="utf-8").splitlines()[1:], ["lever:sampleco  # lever:sampleco"])
            self.assertEqual(ats_search.add_boards(path, results), 0)
            self.assertEqual(ats_search.read_companies(path), ["https://job-boards.greenhouse.io/ExampleLabs", "lever:sampleco"])

    def test_add_boards_labels_with_board_name(self):
        results, _ = self.find(["workable:mockhouse"])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "companies.txt"
            ats_search.add_boards(path, results)
            self.assertEqual(path.read_text(encoding="utf-8"), "workable:mockhouse  # Mockhouse Ltd\n")

    def test_command_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "companies.txt"
            out = io.StringIO()
            with patch.object(ats_search, "fetch_json", Fake(routes())), contextlib.redirect_stdout(out):
                code = ats_search.main(["--find-boards", "Example Labs", "Demoworks Studio", "Nowhere Studio", "--add-to", str(path)])
            self.assertEqual(code, 0)
            text = out.getvalue()
            for expected in ("Found job boards for 2 of 3 companies.", "Example Labs: greenhouse:examplelabs, board name \"Example Labs\", 3 open jobs",
                             "Demoworks Studio: ashby:demoworks", "Check: guessed from part of the name", "Nowhere Studio (tried nowherestudio, nowhere-studio, nowhere)",
                             f"Added 1 new board to {path}."):
                self.assertIn(expected, text)
            self.assertEqual(ats_search.read_companies(path), ["greenhouse:examplelabs"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            ats_search.main(["--add-to", "companies.txt"])


class FetchTests(unittest.TestCase):
    def test_plain_get_with_user_agent_and_timeout(self):
        seen = {}

        def urlopen(request, timeout):
            seen.update(request=request, timeout=timeout)
            return contextlib.nullcontext(io.BytesIO(b'{"jobs": []}'))

        with patch.object(ats_search, "urlopen", urlopen):
            self.assertEqual(ats_search.fetch_json(GH), {"jobs": []})
        request = seen["request"]
        self.assertEqual((request.get_method(), request.full_url, seen["timeout"]), ("GET", GH, 15))
        self.assertEqual(request.get_header("User-agent"), "Nox-Lite/0.1 (+personal job search)")
        self.assertFalse(request.has_header("Cookie") or request.has_header("Authorization"))


if __name__ == "__main__":
    unittest.main()
