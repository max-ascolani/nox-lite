# Filling application forms

Practical lessons from submitting hundreds of applications through employers' recruiting systems. Using the person's own Chrome, where they're already signed in to their accounts, avoids most bot checks.

## Every form

1. **Fill everything, then read it back.** Many forms quietly drop typed values. After filling, read each field's actual value on the page, especially dropdowns and search-as-you-type boxes. Compare with `answers.md`.
2. **Check uploads finished.** The file name should appear with no error or spinner. If the form parsed the CV into fields, correct anything it got wrong.
3. **Scan for problems before clicking submit.** Look for fields marked invalid, red outlines, error text or empty required fields. Fix them first. In Nox, this one check caught about 98% of failed submissions.
4. **Run `nox.py attempt PACKAGE`, then click submit once.**
5. **Look for proof.** Only a new message from this form counts: "Application submitted", "Thanks for applying to [role]" or a confirmation email. A disabled button, a page reload or a generic banner isn't proof. Wait up to a minute for slow forms.
6. **No proof?** Don't click again. Mark the attempt unconfirmed and investigate (see [submit applications](../workflows/submit-application.md)).

## By system

**Greenhouse** (`job-boards.greenhouse.io`, `boards.greenhouse.io`, or embedded on a careers site with `gh_jid=` in the link)

- Questions can be read in advance: `https://boards-api.greenhouse.io/v1/boards/COMPANY/jobs/JOB_ID?questions=true`.
- Dropdowns are search boxes: type, pick the option, then read the field back.
- Some employers send an email security code after you click submit, with one box per character. In manual email mode, the person reads the code from their inbox and types it.

**Lever** (`jobs.lever.co`, `jobs.eu.lever.co`)

- One page: CV upload, contact details, links, an "Additional information" box (good for a short cover note), then custom questions.
- hCaptcha can appear. Hand it to the person.

**Ashby** (`jobs.ashbyhq.com`)

- Upload fields sometimes ignore a normal file pick. Try the upload again, or ask the person to drag the file in.
- Ashby can treat rapid back-to-back submissions as suspicious. Leave a few minutes between Ashby applications in a batch.

**Workable** (`apply.workable.com`) and **Recruitee** (`*.recruitee.com`)

- Usually simple single-page forms. Watch for required checkboxes at the bottom.

**Workday** (`*.myworkdayjobs.com`)

- Each employer needs its own account. Account creation is the person's job: hand over, and continue other applications meanwhile.
- Long multi-page forms. Save after each page, and expect to re-enter work history even after a CV upload.

**Other sites** (SmartRecruiters, Taleo, iCIMS, custom forms)

- The same rules apply. SmartRecruiters can show closed jobs as open, so confirm the posting first.

## Hand these to the person

Logins, account creation, CAPTCHAs, verification codes (in manual email mode), online tests and assessments, and anything asking for ID documents. Keep working on other applications meanwhile, and record the next step in the tracker.
