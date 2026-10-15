#!/usr/bin/env python3
"""Find job leads on employers' own public job boards: Greenhouse, Lever, Ashby, Recruitee, Workable.

Many employers list vacancies through a recruiting system (an "ATS") that publishes
a public job board. This reads those boards directly, keeps the jobs whose title,
place and age match, and leaves out jobs already in your tracker. It only reads
public pages: no login, no cookies, no applications. Apply on the employer's page.

Name each company by its job-board link (a link to one job on the board works too)
or as ats:name, e.g. greenhouse:acme, lever:acme, ashby:acme, recruitee:acme, workable:acme.
Other careers sites aren't supported; check those by hand.

To find a company's board, give its name or careers-page link to --find-boards. It reads
the careers page for a board link, or tries likely board names, and can add what it finds
to your companies file. Name guesses can hit a different company with the same name, so
check any it flags before adding them.

Examples (run from your workspace folder):
  python3 .nox-lite/scripts/ats_search.py --company https://jobs.lever.co/acme --company greenhouse:example --keywords "product manager,designer"
  python3 .nox-lite/scripts/ats_search.py --companies companies.txt --location "london,remote" --exclude senior,intern,internship --max-age-days 30
  python3 .nox-lite/scripts/ats_search.py --companies companies.txt --tracker tracker/jobs.csv --csv research/leads.csv
  python3 .nox-lite/scripts/ats_search.py --find-boards Monzo "Octopus Energy" https://example.com/careers --add-to research/companies.txt

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
import unicodedata
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


# Finding a company's board: from a board link, by scanning its careers page, or by guessing from its name.
SUFFIXES = {"ltd", "limited", "inc", "llc", "llp", "plc", "gmbh", "bv", "nv", "sa", "sas", "ag", "ab", "as", "oy", "spa",
            "srl", "pty", "corp", "corporation", "co", "company", "group", "holdings", "the", "com"}
ON_PAGE = re.compile(r"(?:https?:)?//[\w.-]+\.(?:greenhouse\.io|lever\.co|ashbyhq\.com|recruitee\.com|workable\.com)[^\s\"'<>\\)]*", re.I)


def fetch_page(url):
    """GET one public web page, following redirects; returns (final URL, text). Tests replace this function."""
    with urlopen(Request(url, headers={"User-Agent": UA, "Accept": "text/html"}), timeout=TIMEOUT) as response:
        return response.geturl(), response.read(3_000_000).decode("utf-8", "replace")


def name_words(name):
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", plain.replace("&", " and ").replace("'", "")).split()


def guesses(name):
    """Likely board names: 'Octopus Energy Ltd' -> octopusenergy, octopusenergyltd, octopus-energy, octopus."""
    words = name_words(name)
    core = [w for w in words if w not in SUFFIXES] or words
    out = ["".join(core), "".join(words), "-".join(core)] + ([core[0]] if len(core) > 1 and len(core[0]) > 3 else [])
    return list(dict.fromkeys(g for g in out if g))[:4]


def same_name(a, b):
    """'Octopus Energy' matches 'Octopus Energy Group Ltd'; 'Wise' doesn't match 'Wise Worksite Field Sales'."""
    a, b = ("".join(w for w in name_words(x) if w not in SUFFIXES) for x in (a, b))
    return bool(a) and a == b


def boards_on_page(final_url, html):
    keys = []
    for link in [final_url] + ON_PAGE.findall(html.replace("\\/", "/").replace("&amp;", "&")):
        try:
            key = board("https:" + link if link.startswith("//") else link)
        except BoardError:
            continue
        if (key[0], key[1].lower()) not in [(k[0], k[1].lower()) for k in keys]:
            keys.append(key)
    return keys


def describe(key, fetch):
    """Check a board exists and summarise it; raises NotFound if it doesn't."""
    ats, slug, region = key
    jobs = normalise(ats, slug, fetch_board(ats, slug, region, fetch))
    name = next((j["company"] for j in jobs if j["company"] and j["company"] != slug), "")
    return {"board": f"{ats}:{slug}", "name": name, "jobs": len(jobs), "check": "",
            "examples": [text(j["title"], j["location"]) for j in jobs[:2]], "link": jobs[0]["url"] if jobs else ""}


def find_one(entry, fetch, page):
    result = {"company": entry, "how": "", "tried": [], "boards": [], "problems": []}

    def check(key):
        try:
            result["boards"].append(describe(key, fetch))
        except NotFound:
            pass
        except BoardError as exc:
            result["problems"].append(f"{key[0]}: {exc}")
        except Exception as exc:
            result["problems"].append(f"{key[0]}: unexpected reply ({type(exc).__name__})")

    try:
        keys = [board(entry)]
        result["how"] = "link"
    except BoardError:
        keys = None
    if keys is None and re.match(r"https?://", entry, re.I):
        result["how"], keys = "careers page", []
        try:
            keys = boards_on_page(*page(entry))
        except HTTPError as exc:
            result["problems"].append(f"the careers page refused the request (HTTP {exc.code}); open it in Chrome instead")
        except (OSError, ValueError) as exc:
            result["problems"].append(f"couldn't open the careers page ({getattr(exc, 'reason', exc)})")
    if keys is not None:
        for key in keys:
            check(key)
        return result
    result["how"] = "name"
    for guess in guesses(entry):
        result["tried"].append(guess)
        for ats in ATS:
            check((ats, guess, ""))
        # Empty accounts exist under many common names, so a guess counts only if it has jobs.
        result["boards"] = [b for b in result["boards"] if b["jobs"]]
        if result["boards"]:
            break
    first = result["tried"][0] if result["tried"] else ""
    for b in result["boards"]:
        if b["name"] and not same_name(entry, b["name"]):
            b["check"] = f"the board is called \"{b['name']}\""
        elif not b["name"] and b["board"].split(":", 1)[1] != first:
            b["check"] = "guessed from part of the name"
    return result


def find_boards(entries, fetch=None, page=None):
    """For each company name, careers-page link or board link, find its public job board."""
    fetch, page = fetch or fetch_json, page or fetch_page
    entries = list(dict.fromkeys(e.strip() for e in entries if e.strip()))
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return list(pool.map(lambda e: find_one(e, fetch, page), entries))


def add_boards(path, results):
    """Append confirmed boards that aren't in the companies file yet; returns how many were added."""
    path = Path(path).expanduser()
    existing = path.read_text(encoding="utf-8-sig") if path.exists() else ""
    known = set()
    for entry in read_companies(path) if existing else []:
        try:
            ats, slug, _ = board(entry)
            known.add((ats, slug.lower()))
        except BoardError:
            pass
    lines = []
    for result in results:
        for b in result["boards"]:
            ats, slug = b["board"].split(":", 1)
            key = (ats, slug.lower())
            if not b["check"] and key not in known:
                known.add(key)
                lines.append(f"{b['board']}  # {result['company'].replace('#', '')}")
    if lines:
        atomic_text(path, existing + ("\n" if existing and not existing.endswith("\n") else "") + "\n".join(lines) + "\n")
    return len(lines)


def board_summary(results, added=None, path=None):
    def line(company, b):
        found = f"{b['board']}" + (f", board name \"{b['name']}\"" if b["name"] else "") + f", {b['jobs']} open jobs"
        return f"  {company}: {found}" + (f" (e.g. {'; '.join(b['examples'])})" if b["examples"] else "")
    sure = [line(r["company"], b) for r in results for b in r["boards"] if not b["check"]]
    unsure = [line(r["company"], b) + f". Check: {b['check']}" for r in results for b in r["boards"] if b["check"]]
    missing = [r for r in results if not r["boards"]]
    out = [f"Found job boards for {sum(1 for r in results if r['boards'])} of {len(results)} companies."]
    if sure:
        out += ["Found:"] + sure
    if unsure:
        out += ["Check these first: open a job link to confirm it's the right company, then rerun with the board (for example --find-boards lever:name):"] + unsure
    if missing:
        out.append("Not found (give a careers-page link instead, or note the careers page in the source plan to check in Chrome):")
        for r in missing:
            tried = f" (tried {', '.join(r['tried'])})" if r["tried"] else ""
            out.append(f"  {r['company']}{tried}" + (f": {'; '.join(r['problems'])}" if r["problems"] else ""))
    if added is not None:
        out.append(f"Added {added} new board{'s' if added != 1 else ''} to {path}." if added else f"Nothing new to add to {path}.")
    return "\n".join(out)


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
    parser.add_argument("--find-boards", nargs="+", metavar="COMPANY", help="instead of searching, find these companies' job boards: names, careers-page links or board links")
    parser.add_argument("--add-to", metavar="FILE", help="with --find-boards: add the boards found to this companies file, skipping ones already there and ones to check")
    args = parser.parse_args(argv)
    if args.limit < 1 or args.max_age_days is not None and args.max_age_days < 0:
        parser.error("--limit must be at least 1 and --max-age-days can't be negative")
    if args.add_to and not args.find_boards:
        parser.error("--add-to only works with --find-boards")
    if args.find_boards:
        try:
            results = find_boards(args.find_boards)
            added = add_boards(args.add_to, results) if args.add_to else None
        except (ValueError, OSError) as exc:
            print(f"Nox-Lite: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"companies": results, "added": added}, indent=2, ensure_ascii=False) if args.json
              else board_summary(results, added, args.add_to))
        return 0 if any(r["boards"] for r in results) or not any(r["problems"] for r in results) else 1
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
