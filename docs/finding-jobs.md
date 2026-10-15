# Finding jobs

**Apply on the employer's own job board.** In the job hunt behind Nox-Lite, every interview came from applying directly on an employer's own form, not through a job site's "easy apply". Job sites are great for discovering *companies*. The application should go through the company's own form.

Most companies use a recruiting system (an "ATS") with a public job board: Greenhouse, Lever, Ashby, Workable or Recruitee. Nox-Lite can read those boards directly, which is fast, free and doesn't need a login.

## The method

**1. Keep a company list.** `research/companies.txt` has one company per line, as a board link or `ats:name` (for example `greenhouse:acme`, `lever:acme`, `ashby:acme`). Fill it from:

- the dream companies in `profile/preferences.md`;
- competitors of their past employers, and companies that hire people with their background;
- startup and investor lists in their sector, [Work at a Startup](https://www.workatastartup.com/) and the monthly [Hacker News "Who is hiring?"](https://news.ycombinator.com/submitted?id=whoishiring) thread for tech;
- companies spotted on LinkedIn, Indeed and other job sites while searching.

**2. Find each company's board.** Open its careers page and follow an "Apply" link. If it lands on `job-boards.greenhouse.io`, `jobs.lever.co`, `jobs.ashbyhq.com`, `apply.workable.com` or `*.recruitee.com`, add that board to the list. If not, note the careers page in `research/source-plan.md` to check by hand.

**3. Search the boards in one go.**

```sh
python3 .nox-lite/scripts/ats_search.py --companies research/companies.txt \
  --keywords "operations manager,head of operations,ops lead" \
  --exclude intern,internship,graduate --location "london,remote" \
  --max-age-days 30 --tracker tracker/jobs.csv --csv research/leads/2026-10-15.csv
```

Use the target titles and their aliases from `profile/preferences.md`. Matching is on whole words, so list variants ("engineer,engineering").

**4. Search engines find new companies.** Search for the boards directly, for example `site:job-boards.greenhouse.io "operations manager" London`, and the same with `jobs.lever.co`, `jobs.ashbyhq.com` and `apply.workable.com`. Add every relevant new company to the list, so future searches cover it automatically.

**5. Add the right local sources.** Public-sector, healthcare, teaching and many non-tech jobs are only advertised on specialist or government sites. Pick from the [source catalogue](../sources/README.md) for the person's country and profession, and research others.

**6. Verify every lead.** A search result is a lead, not a vacancy. Open each posting and check: still open; the location and, for remote jobs, *which countries*; the key requirements; salary if shown; deadline; and that the application form works. Some systems, and many job sites, show closed or reposted jobs as open.

**7. Be strict.** Score each job with [scoring](scoring.md), drop anything with a dealbreaker, and keep only good fits. In Nox, no application below a strong fit ever led to an interview. Twenty great applications beat a hundred weak ones.

## How many

- **First search:** 5 jobs, so the person can react and the search can be tuned.
- **After that:** 20–25 verified jobs per search (`search.max_new_jobs`). That was the daily pace in the real job hunt, prepared and reviewed as one batch.
- If only 12 good jobs exist, return 12 and say so. Never pad a batch with weak matches.

## Good to know

- Keep job IDs in links (for example Greenhouse's `gh_jid`). The tracker uses them to spot duplicates.
- The same job often appears on several sites. Track the employer's original posting.
- Logged-in job sites (LinkedIn, for example) work through the person's own Chrome. Never create accounts for them.
- Recruitment agencies only if the person says they're happy with agencies.
