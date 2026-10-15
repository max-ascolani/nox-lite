# Find jobs

The method is in [finding jobs](../docs/finding-jobs.md). This is the procedure.

## Before searching

1. Read `profile/preferences.md`, the right-to-work countries in `profile/answers.md`, `workspace.json` → `search`, and the tracker (every row, including declined and closed ones).
2. If `search.active` is false, a scheduled run stops here. A direct request from the person can still search; ask whether to resume the schedule too.
3. **How many:** the number in the request, otherwise `search.max_new_jobs`. For the very first search, use `search.first_batch` (5). "Find 40 today" applies to this search only; "from now on" updates `max_new_jobs` and `profile/preferences.md`.
4. On the first search, create `research/companies.txt` and `research/source-plan.md` (from [the template](../templates/source-plan.md)), following the method.

## Search

5. Run `ats_search.py` over the company list with the target titles, exclusions, locations and `--tracker tracker/jobs.csv`. Save the leads as `research/leads/YYYY-MM-DD.csv`.
6. Widen as needed: `site:` searches for new companies (add them to the list), the local and specialist sources in the source plan, and logged-in job sites in the person's Chrome if they use them. Search more sources rather than lowering standards.
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
10. Save a short dated report as `research/searches/YYYY-MM-DD.md`: target, results, sources searched, exclusions by reason (closed, duplicate, dealbreaker, weak fit), and anything left unfinished.
11. Show a numbered shortlist, best first:

    | # | Company and role | Where | Salary | Fit | Why, and the main gap |
    |---|---|---|---|---|---|

    Then offer the batch: *"Which should I prepare? You can say 'all of them', '1–8', or 'all except 3'."* Their choice goes to [prepare applications](prepare-application.md) with [batch coordination](batch-applications.md).

If a usage limit or blocked site interrupts the search, save what's done and the next step, and report honestly (for example "14 of 25 so far"). Never claim a source was searched when it wasn't.
