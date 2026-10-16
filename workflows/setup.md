# Set up, and get to know the person

Goal for the first sitting: a working workspace, a profile rich enough to apply with, and a first look at real jobs. Context matters more than anything else in setup. Every question answered now is one that never interrupts a batch later.

Go in this order. After each stage, record the check (see [the checklist](../setup/checklist.md)) and save `next_step` in `setup-state.json`. On a later "continue", read `setup-state.json` and the profile first, and pick up where you left off. Never repeat answered questions.

If there's no workspace yet, follow [START_HERE](../START_HERE.md).

## 1. Check the computer (5 minutes)

In the Claude desktop app, if they're asked to allow every file save, suggest **Accept edits** in the mode menu just below the message box. Claude then saves files without asking but still asks before running anything.

Run `python3 .nox-lite/scripts/nox.py doctor --workspace .` and fix what it reports, in plain English:

- **CV builder missing (python-docx):** install it in a private environment. Mac: `python3 -m venv .nox-lite/.venv` then `.nox-lite/.venv/bin/python -m pip install -r .nox-lite/requirements-docs.txt`. Windows: `py -3 -m venv .nox-lite\.venv` then `.nox-lite\.venv\Scripts\python.exe -m pip install -r .nox-lite\requirements-docs.txt`. Use that Python for `build_cv.py` from then on.
- **LibreOffice missing:** optional. It's only needed to make PDFs automatically. Offer the free download from <https://www.libreoffice.org/>, or explain that they can save the .docx as a PDF from Word, Pages or Google Docs. Most forms accept .docx.
- Build the fictional sample CV (see [documents](../docs/documents.md)), look at every page, and record the `files` and `documents` checks.

## 2. Gather everything (the most important step)

Ask for everything at once, and explain why: *"The more you give me now, the fewer questions I'll ask later, and the better every application will be."*

- every CV they have, including old versions, which often hold forgotten detail;
- their LinkedIn profile: on their profile page, **More → Save to PDF**;
- cover letters and application answers they've written before (great for learning their voice);
- performance reviews, a portfolio, project write-ups, a personal website, certificates;
- job ads they liked, even expired ones, and any notes on what they want.

They can attach files in the chat, or you can open the `inbox/` folder for them to drag files into (Mac: `open inbox`; Windows: `explorer inbox`). Save attachments into `inbox/`. Keep originals in `evidence/`.

Read everything, then fill in:

- `profile/experience.md`: every role with real titles, dates, responsibilities and results;
- `profile/claims.json`: important claims (titles, dates, numbers, qualifications), with source and status;
- `profile/stories.md`: candidate stories you spotted;
- `profile/voice.md`: notes from anything they wrote themselves;
- `profile/facts.md` and `profile/answers.md`: anything the documents already answer.

When documents disagree (dates, titles), list the conflicts to ask about. Don't pick the more impressive version. Imported facts stay `unconfirmed` until the person confirms them.

## 3. Interview (20–30 minutes)

Skip anything the documents already answered. Ask open questions one at a time. Ask quick facts in small groups of three to five. Say briefly why a question matters. "Skip" and "not sure" are fine answers: record them in `profile/open-questions.md`. Save each answer as you go.

**A. What they want** → `profile/preferences.md`

1. Which job titles are you aiming for? (Up to five. Suggest the aliases employers use for the same work.)
2. Where can you work: which cities or countries, remote, hybrid? How many office days are OK? Would you relocate?
3. What level: the same as now, a step up, or open?
4. What would make you say no to a job, whatever else it offered? (Binary dealbreakers only: for example a minimum salary, a location, no on-call, no agencies.)
5. Any companies you'd love to work for, or never would? Sectors that excite you or put you off?
6. What does a great ordinary week at work look like? What drains you?

**B. Stories** → `profile/stories.md`

For each recent role, ask what they're proudest of, what they personally did, and what changed as a result. Estimates are fine if labelled as estimates. Aim for **8–12 stories** that cover a big achievement, leading or influencing people, a failure and what they learned, a disagreement, dealing with ambiguity, and their core skill at its best. Rank each A, B or C for how strong it is.

**C. Standard answers** → `profile/answers.md`

Work through the template's list: right to work and sponsorship for each target country, the four salary facts, notice period and start date, relocation, office days, travel, education details, languages, licences, contact details, and the policy questions (how did you hear, equal-opportunities questions, criminal record, consent, AI use). These questions appear on almost every form. Answering them now is what makes bulk applying possible.

- Salary: record **target**, **disclosure choice** (share target / say negotiable / ask me each time), **private floor** and **whether the posted range is OK**. Never suggest a number they haven't given.
- Criminal record and equal-opportunities questions: offer the suggested default where one exists, and record what they choose. If they'd rather not decide now, record "ask me each time".

**D. Voice** → `profile/voice.md`

If you have nothing they wrote themselves, ask for two or three short things (emails, a past cover letter), or ask them to answer one question in their own words. Note US or British English.

Before moving on, read back a short summary (who they are, what they want, their top stories, their key answers) and ask for corrections. Record the `profile` and `search` checks.

## 4. Plan where to look (10 minutes, mostly you working)

Where good jobs are advertised depends on the person's field and country, so work it out for them. Follow [plan where to look](find-jobs.md#plan-where-to-look): ask three quick questions, research where their field hires, build their company list and find each company's job board. Show them the plan in a few lines, ask what to add or drop, and record `sources`.

## 5. First look at real jobs

Follow [find jobs](find-jobs.md), using the plan, with a small first batch (`search.first_batch`, usually 5). Ask what they like and dislike about each, and why. Update the preferences and scoring notes. This calibration is worth more than any questionnaire. Record `tracker` and `first_search`.

Then show them their tracker: run `python3 .nox-lite/scripts/nox.py view --workspace . --open`, which opens `tracker/Job tracker.html` in their browser (if it doesn't open, tell them where it is: their job-search folder → tracker → Job tracker). Ask one question: *"This is your job tracker, and I keep it up to date. Would you like it as this page, an Excel spreadsheet (opens in Excel or Numbers), or both? And detailed like this, or simple: company, role, status and next step?"* Save the answer with `view --format … --detail …`. Tell them they can change it any time, such as "add salary" or "switch to Excel" (see [the tracker guide](../docs/tracker.md#what-the-person-sees)).

## 6. Connect Chrome and practise (10 minutes)

Follow [Chrome setup](../setup/browser.md). Run the practice form, including a dummy upload. Record `browser` and `upload`.

## 7. Agree how to work

- **Batch size:** explain the normal rhythm: find 20–25 jobs, choose the best, prepare them all, review once, approve once. Save their usual number in `workspace.json` → `search.max_new_jobs` (25 by default).
- **Email:** explain the three [email choices](../setup/email.md) briefly. Manual is the default and works fine. Record `email`.
- **Tracker:** the local tracker works now, as the page or spreadsheet they chose in step 5. [Google Sheets](../setup/google-sheets.md) is optional.
- **Schedule:** offer a [daily search](../setup/schedules.md) only after a manual search worked. Create nothing unless they ask.

## 8. Wrap up

Say what's ready (searching, preparing, submitting) and anything still blocked, in one short message. Suggest the next step, usually: *"Shall I find your first 20–25 jobs?"* Save open questions. If they stop here, tell them: open the workspace folder and say "Continue."

End with one line, once, here and never again: *"Nox-Lite is free, made by Max Ascolani. For updates and tips, follow Max on [LinkedIn](https://www.linkedin.com/in/max-ascolani/) or [X](https://x.com/maxascolani)."*

Throughout: when you can't see their screen, ask what they see; don't invent buttons. Sign-ins happen in the service's own sign-in page. Setup approves nothing: applications, emails, accounts, purchases and schedules each need their own instruction.
