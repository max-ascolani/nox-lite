# Find jobs

The method is in [finding jobs](../docs/finding-jobs.md). This is the procedure.

## Plan where to look

Do this during setup, right after the interview, and again when results are thin or their direction changes. The aim is a short, personal plan: the places this person's jobs are actually advertised, and the companies worth watching. Don't assume a tech job, an English-speaking market, or the US or UK.

1. **Ask three quick questions** (skip what you already know):
   - How did you find your last two or three jobs?
   - Which job sites do you already use or get alerts from? Are you signed in to any in Chrome, such as LinkedIn?
   - In your field, where do good jobs get posted? Any professional body, community, newsletter or recruiter worth watching? ("Not sure" is fine. Finding out is your job.)
2. **Work out how their field hires, in their country.** Start from [where jobs are advertised](../docs/finding-jobs.md#where-jobs-are-advertised) and the [source catalogue](../sources/README.md), then search the web, for example `where are [job title] jobs advertised in [country]` or `[profession] job board [country]`. Open each candidate site and run one real search. Keep it only if it shows current jobs that fit. Prefer free sites that link through to the employer's own posting. Choose three to six.
3. **Build the company list.** For office jobs, aim for 30–60 companies: their dream companies, competitors and peers of their past employers, well-known employers in their sector and city, and companies hiring for their exact title (search `site:job-boards.greenhouse.io "[title]" [city]`, and the same with `jobs.lever.co`, `jobs.ashbyhq.com` and `apply.workable.com`). For public-sector, healthcare, education and local jobs, list the main employers nearby (councils, hospitals, schools, universities) instead.
4. **Find each company's job board** in one go, with names or careers-page links:

   ```sh
   python3 .nox-lite/scripts/ats_search.py --find-boards "Northwind" "Contoso Ltd" https://careers.example.com/ --add-to research/companies.txt
   ```

   It reads careers pages for a board link and tries likely board names, then adds the boards it's sure of. For any it asks you to check, open one job link: if it's the right company, rerun with that board (`--find-boards lever:name --add-to research/companies.txt`). Note companies without a supported board, with their careers page, in the plan; you'll check those in Chrome.
5. **Write `research/source-plan.md`** from [the template](../templates/source-plan.md).
6. **Show the plan in a few lines** and ask what to add or drop. For example: *"Each search I'll check 38 companies' job boards, including your five dream companies, plus Welcome to the Jungle and LinkedIn in your Chrome. Seven companies use their own careers sites; I'll check those in Chrome."* Or: *"I'll search NHS Jobs and Indeed for nursing roles within 10 miles of Leeds, plus the careers pages of the four local hospital trusts."* Save their changes, then record the `sources` check.

**Keep it working.** After each search, update "What's working" in the plan: which sources gave jobs worth keeping. Add companies you discover along the way with `--find-boards … --add-to research/companies.txt`. Drop a source that has given nothing in three searches. If two searches in a row come up short, revisit the plan before lowering standards.

## Before searching

1. Read `profile/preferences.md`, the right-to-work countries in `profile/answers.md`, `workspace.json` → `search`, `research/source-plan.md`, and the tracker (every row, including declined and closed ones).
2. If `search.active` is false, a scheduled run stops here. A direct request from the person can still search; ask whether to resume the schedule too.
3. **How many:** the number in the request, otherwise `search.max_new_jobs`. For the very first search, use `search.first_batch` (5). "Find 40 today" applies to this search only; "from now on" updates `max_new_jobs` and `profile/preferences.md`.
4. If there's no `research/source-plan.md` yet, [plan where to look](#plan-where-to-look) first.

## Search

5. Run `ats_search.py` over the company list with the target titles, exclusions, locations and `--tracker tracker/jobs.csv`. Save the leads as `research/leads/YYYY-MM-DD.csv`.
6. Search the job sites and careers pages in the source plan, and logged-in job sites in the person's Chrome if they use them. Widen with `site:` searches for new companies, and add each relevant one with `--find-boards … --add-to research/companies.txt`. Search more sources rather than lowering standards.
7. **Verify** each promising lead on the live posting (title, open, location and remote countries, requirements, salary, deadline, application route). Leave out reposts and anything already in the tracker under another link.
8. **Score** each verified job with [scoring](../docs/scoring.md). Drop dealbreakers. Keep strong fits.

## Record and report

9. Add each kept job with the helper:

   ```sh
   python3 .nox-lite/scripts/nox.py add-job --workspace . --company "Northwind" --role "Operations Manager" \
     --url "https://job-boards.greenhouse.io/northwind/jobs/123" --location "London, hybrid 2 days" \
     --salary "GBP 60-70k" --fit "4/5: runs a similar fleet; gap: no SAP" --checked-at 2026-10-15T09:30:00+01:00
   ```

   If the tracker is a Google Sheet, follow [the tracker guide](../docs/tracker.md) instead.
10. Save a short dated report as `research/searches/YYYY-MM-DD.md`: target, results, sources searched, exclusions by reason (closed, duplicate, dealbreaker, weak fit), and anything left unfinished. Update "What's working" in the source plan.
11. Show a numbered shortlist, best first:

    | # | Company and role | Where | Salary | Fit | Why, and the main gap |
    |---|---|---|---|---|---|

    Then offer the batch: *"Which should I prepare? You can say 'all of them', '1–8', or 'all except 3'."* Their choice goes to [prepare applications](prepare-application.md) with [batch coordination](batch-applications.md).

If a usage limit or blocked site interrupts the search, save what's done and the next step, and report honestly (for example "14 of 25 so far"). Never claim a source was searched when it wasn't.
