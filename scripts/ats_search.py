#!/usr/bin/env python3
"""Find job leads on employers' own public job boards: Greenhouse, Lever, Ashby, Recruitee, Workable.

Many employers list vacancies through a recruiting system (an "ATS") that publishes
a public job board. This reads those boards directly, keeps the jobs whose title,
place and age match, and leaves out jobs already in your tracker. It only reads
public pages: no login, no cookies, no applications. Apply on the employer's page.

Name each company by its job-board link (a link to one job on the board works too)
or as ats:name, e.g. greenhouse:acme, lever:acme, ashby:acme, recruitee:acme, workable:acme.
Other careers sites aren't supported; check those by hand.

Examples (run from your workspace folder):
  python3 .nox-lite/scripts/ats_search.py --company https://jobs.lever.co/acme --company greenhouse:example --keywords "product manager,designer"
  python3 .nox-lite/scripts/ats_search.py --companies companies.txt --location "london,remote" --exclude senior,intern,internship --max-age-days 30
  python3 .nox-lite/scripts/ats_search.py --companies companies.txt --tracker tracker/jobs.csv --csv research/leads.csv

These are leads, not verified vacancies: open each link to check it's still live
before adding it to the tracker.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
from datetime import date, datetime, timedelta, timezone
import io
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError
from urllib.parse import parse_qsl, quote, unquote, urlsplit
from urllib.request import Request, urlopen

from nox import atomic_text, canonical_url, decode_cell, identity, safe_cell

UA = "Nox-Lite/0.1 (+personal job search)"
ATS = ("greenhouse", "lever", "ashby", "recruitee", "workable")
COLUMNS = ["company", "title", "location", "remote", "posted", "ats", "url", "job_id"]
TIMEOUT, WORKERS, RETRY_PAUSE = 15, 6, 1.0
REMINDER = "These are leads, not verified vacancies: open each link to check it's still live before adding it to the tracker."
UNSUPPORTED = "not a supported job board; give the careers page to your assistant to check by hand"
NOT_FOUND = "board not found — check the company's careers page link"
GREENHOUSE = {"boards.greenhouse.io", "job-boards.greenhouse.io", "boards.eu.greenhouse.io", "job-boards.eu.greenhouse.io"}


class BoardError(Exception):
    """A plain-English problem with one company; the rest of the search continues."""


class NotFound(BoardError):
    pass


def board(entry):
    """Return (ats, slug, region) for a board link, a job link on a board, or ats:slug."""
    entry = entry.strip()
    match = re.fullmatch(r"(\w+):\s*([^/\s]+)", entry)
    if match and match.group(1).lower() in ATS:
        ats, slug, host = match.group(1).lower(), match.group(2), ""
    else:
        p = urlsplit(entry if "//" in entry else "https://" + entry)
        host = (p.hostname or "").lower()
        parts = [unquote(x) for x in p.path.split("/") if x]
        first = parts[0] if parts else ""
        if host in GREENHOUSE:  # embed links name the board as ?for=slug
            ats, slug = "greenhouse", dict(parse_qsl(p.query)).get("for") or ("" if first == "embed" else first)
        elif host in {"jobs.lever.co", "jobs.eu.lever.co"}:
            ats, slug = "lever", first
        elif host == "jobs.ashbyhq.com":
            ats, slug = "ashby", first
        elif re.fullmatch(r"[a-z0-9-]+\.recruitee\.com", host):
            ats, slug = "recruitee", host.split(".")[0]
        elif host == "apply.workable.com":
            ats, slug = "workable", "" if first == "j" else first
        elif re.fullmatch(r"[a-z0-9-]+\.workable\.com", host) and host.split(".")[0] not in {"www", "jobs"}:
            ats, slug = "workable", host.split(".")[0]
        else:
            raise BoardError(UNSUPPORTED)
    if not slug:
        raise BoardError("this link doesn't show whose job board it is; give the board's main page instead")
    if not re.fullmatch(r"[\w. -]+", slug):
        raise BoardError(UNSUPPORTED)
    return ats, slug, "eu" if ".eu." in host else ""


def endpoints(ats, slug, region):
    s = quote(slug)
    if ats == "lever":  # EU-hosted Lever boards answer 404 on the main API, so try both unless known
        return [f"https://api{r}.lever.co/v0/postings/{s}?mode=json" for r in ((".eu",) if region else ("", ".eu"))]
    return [{"greenhouse": f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs",  # also serves EU boards
             "ashby": f"https://api.ashbyhq.com/posting-api/job-board/{s}",
             "recruitee": f"https://{s}.recruitee.com/api/offers/",
             "workable": f"https://apply.workable.com/api/v1/widget/accounts/{s}"}[ats]]


def fetch_json(url):
    """GET one public JSON document. No cookies or credentials. Tests replace this function."""
    with urlopen(Request(url, headers={"User-Agent": UA, "Accept": "application/json"}), timeout=TIMEOUT) as response:
        return json.load(response)


def get(url, fetch):
    for attempt in (1, 2):
        try:
            return fetch(url)
        except HTTPError as exc:
            if exc.code == 404:
                raise NotFound(NOT_FOUND)
            if exc.code < 500 or attempt == 2:
                raise BoardError(f"the job board refused the request (HTTP {exc.code}); try again later or check by hand")
        except OSError as exc:  # includes timeouts and connection failures
            if not isinstance(exc, TimeoutError) and not isinstance(getattr(exc, "reason", None), TimeoutError):
                raise BoardError(f"couldn't reach the job board ({getattr(exc, 'reason', exc)})")
            if attempt == 2:
                raise BoardError(f"the job board didn't answer within {TIMEOUT} seconds; try again later")
        except ValueError:
            raise BoardError("the job board sent something other than job data; check it by hand")
        time.sleep(RETRY_PAUSE)


def fetch_board(ats, slug, region, fetch):
    urls = endpoints(ats, slug, region)
    for url in urls:
        try:
            return get(url, fetch)
        except NotFound:
            if url == urls[-1]:
                raise


def text(*parts, sep=", "):
    return sep.join(dict.fromkeys(" ".join(str(p).split()) for p in parts if p))


def day(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):  # Lever: milliseconds since 1970
        return datetime.fromtimestamp(value / 1000, timezone.utc).date().isoformat()
    match = re.match(r"\d{4}-\d{2}-\d{2}", str(value or ""))
    return match.group(0) if match else ""


# Each parser yields (company, title, location, remote, posted, url) from one board's reply.
def greenhouse(data, slug):
    for j in data["jobs"]:
        flags = [str(m.get("value")).lower() for m in j.get("metadata") or []]
        yield (j.get("company_name") or slug, j.get("title"), (j.get("location") or {}).get("name"),
               "remote" in flags, j.get("first_published") or j.get("updated_at"), j.get("absolute_url"))


def lever(data, slug):
    for j in data:
        c = j.get("categories") or {}
        yield (slug, j.get("text"), text(*(c.get("allLocations") or [c.get("location")]), sep="; "),
               j.get("workplaceType") == "remote", j.get("createdAt"), j.get("hostedUrl"))


def ashby(data, slug):
    for j in data["jobs"]:
        if j.get("isListed", True):
            places = [j.get("location")] + [s.get("location") for s in j.get("secondaryLocations") or []]
            remote = str(j["workplaceType"]).lower() == "remote" if j.get("workplaceType") else j.get("isRemote")
            yield slug, j.get("title"), text(*places, sep="; "), remote, j.get("publishedAt"), j.get("jobUrl")


def recruitee(data, slug):
    for j in data["offers"]:
        yield (j.get("company_name") or slug, j.get("title"), j.get("location") or text(j.get("city"), j.get("country")),
               j.get("remote"), j.get("published_at") or j.get("created_at"), j.get("careers_url"))


def workable(data, slug):
    for j in data["jobs"]:
        places = [text(x.get("city"), x.get("region"), x.get("country")) for x in j.get("locations") or [] if not x.get("hidden")]
        yield (data.get("name") or slug, j.get("title"), text(*places, sep="; ") or text(j.get("city"), j.get("state"), j.get("country")),
               j.get("telecommuting"), j.get("published_on") or j.get("created_at"), j.get("url") or j.get("shortlink"))


PARSERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby, "recruitee": recruitee, "workable": workable}


def normalise(ats, slug, data):
    jobs = []
    for company, title, place, remote, posted, url in PARSERS[ats](data, slug):
        try:
            url = canonical_url(url or "")  # keeps identity parameters such as gh_jid
        except ValueError:
            continue  # nothing to open or apply through
        place = text(place)
        jobs.append({"company": text(company), "title": text(title), "location": place,
                     "remote": bool(remote) or "remote" in place.lower(), "posted": day(posted),
                     "ats": ats, "url": url, "job_id": identity(url)})
    return jobs


def terms(value):
    return [t.strip().lower() for t in (value or "").split(",") if t.strip()]


def mentions(value, phrases):
    """True if any phrase appears as whole words; 'front end' also matches 'Front-End'."""
    return any(re.search(r"(?<!\w)" + r"[\s-]+".join(map(re.escape, re.split(r"[\s-]+", p))) + r"(?!\w)", value, re.I)
               for p in phrases)


def search(entries, keywords="", exclude="", location="", max_age_days=None, tracked=frozenset(),
           include_tracked=False, limit=100, fetch=None, today=None):
    fetch = fetch or fetch_json
    boards, errors = {}, []
    for entry in entries:
        try:
            boards.setdefault(board(entry), entry)
        except BoardError as exc:
            errors.append({"company": entry, "error": str(exc)})
    found, searched = [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {key: pool.submit(lambda k: normalise(k[0], k[1], fetch_board(*k, fetch)), key) for key in boards}
        for key, future in futures.items():
            try:
                found += future.result()
                searched += 1
            except BoardError as exc:
                errors.append({"company": boards[key], "error": str(exc)})
            except Exception as exc:  # an unexpected reply must not stop the other companies
                errors.append({"company": boards[key], "error": f"unexpected reply from the job board ({type(exc).__name__}); check it by hand"})
    words, unwanted, places = terms(keywords), terms(exclude), terms(location)
    cutoff = ((today or date.today()) - timedelta(days=max_age_days)).isoformat() if max_age_days is not None else ""
    results, seen, hidden = [], set(), 0
    for job in found:
        if job["url"] in seen or words and not mentions(job["title"], words) or mentions(job["title"], unwanted):
            continue
        if places and not any(p == "remote" and job["remote"] or mentions(job["location"], [p]) for p in places):
            continue
        if cutoff and job["posted"] and job["posted"] < cutoff:
            continue
        seen.add(job["url"])
        job["already_tracked"] = job["url"] in tracked
        if job["already_tracked"] and not include_tracked:
            hidden += 1
            continue
        results.append(job)
    results.sort(key=lambda j: j["posted"], reverse=True)  # newest first; undated last
    return {"results": results[:limit], "errors": errors, "searched": searched, "scanned": len(found),
            "matched": len(results), "hidden_tracked": hidden, "note": REMINDER}


def read_companies(path):
    lines = Path(path).expanduser().read_text(encoding="utf-8-sig").splitlines()
    return [entry for line in lines if (entry := re.sub(r"(^|\s)#.*", "", line).strip())]


def tracked_urls(path):
    with Path(path).expanduser().open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if "url" not in (reader.fieldnames or []):
            raise ValueError("The tracker has no url column; check the --tracker path")
        urls = set()
        for row in reader:
            try:
                urls.add(canonical_url(decode_cell(row.get("url") or "")))
            except ValueError:
                pass
    return urls


def write_csv(path, results):
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(COLUMNS)
    for r in results:
        writer.writerow([safe_cell("yes" if r[c] else "no") if c == "remote" else safe_cell(r[c]) for c in COLUMNS])
    atomic_text(Path(path).expanduser(), out.getvalue())


def table(results):
    def cut(value, width):
        return value if len(value) <= width else value[:width - 1] + "…"
    rows = [("COMPANY", "TITLE", "LOCATION", "POSTED", "LINK")] + [
        (r["company"], r["title"], text(r["location"], "remote" if r["remote"] and "remote" not in r["location"].lower() else "") or "-",
         r["posted"] or "-", r["url"]) for r in results]
    return "\n".join("  ".join(cut(v, w).ljust(w) for v, w in zip(row, (18, 42, 26, 10))) + "  " + row[4] for row in rows)


def summary(report, csv_path=None):
    shown, matched = len(report["results"]), report["matched"]
    line = f"{shown} leads from {report['searched']} job boards ({report['scanned']} jobs checked)"
    if matched > shown:
        line += f"; showing the newest {shown} of {matched}, use --limit for more"
    if report["hidden_tracked"]:
        line += f"; {report['hidden_tracked']} already in your tracker left out"
    lines = [line + "."] + ([f"Saved to {csv_path}."] if csv_path else [])
    lines += [f"Couldn't search {e['company']}: {e['error']}" for e in report["errors"]]
    return "\n".join(lines + [REMINDER])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--company", action="append", default=[], help="a job-board link or ats:name; repeat for more companies")
    parser.add_argument("--companies", metavar="FILE", help="text file with one company per line; blank lines and # comments are ignored")
    parser.add_argument("--keywords", help="comma-separated words or phrases; keep jobs whose title contains any as whole words (list variants: engineer,engineering)")
    parser.add_argument("--exclude", help="comma-separated words; leave out jobs whose title contains any as whole words, e.g. senior,intern,internship")
    parser.add_argument("--location", help="comma-separated places; keep jobs whose location mentions any as whole words ('remote' also matches remote jobs)")
    parser.add_argument("--max-age-days", type=int, metavar="N", help="leave out jobs posted more than N days ago (undated jobs are kept)")
    parser.add_argument("--limit", type=int, default=100, metavar="N", help="show at most N results, newest first (default 100)")
    parser.add_argument("--tracker", metavar="PATH", help="your tracker CSV; jobs already in it are left out")
    parser.add_argument("--include-tracked", action="store_true", help="also show jobs already in the tracker, marked already_tracked")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument("--csv", metavar="PATH", help="also save the results to this CSV file")
    args = parser.parse_args(argv)
    if args.limit < 1 or args.max_age_days is not None and args.max_age_days < 0:
        parser.error("--limit must be at least 1 and --max-age-days can't be negative")
    try:
        entries = args.company + (read_companies(args.companies) if args.companies else [])
        if not entries:
            raise ValueError("Name at least one company with --company or --companies")
        tracked = tracked_urls(args.tracker) if args.tracker else frozenset()
        report = search(entries, args.keywords, args.exclude, args.location, args.max_age_days, tracked,
                        args.include_tracked, args.limit)
        if args.csv:
            write_csv(args.csv, report["results"])
    except (ValueError, OSError, csv.Error) as exc:
        print(f"Nox-Lite: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print((table(report["results"]) + "\n\n" if report["results"] else "") + summary(report, args.csv))
    return 0 if report["searched"] or not report["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
