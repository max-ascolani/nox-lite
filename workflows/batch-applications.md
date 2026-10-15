# Batches

Bulk is the normal way to work: find 20–25 jobs, the person picks, you prepare them all, they review once and approve once, you submit them all. This procedure coordinates [find jobs](find-jobs.md), [prepare](prepare-application.md) and [submit](submit-application.md) across many jobs. Each job still follows its own procedure.

Finding 25 jobs doesn't select them. Selecting 15 doesn't approve them. Approving doesn't submit them unless the person says so.

## 1. Choose

- Resolve "1–8", "all of them" or "all except 3" against the shortlist you showed, then record each choice: `nox.py decision --workspace . JOB_ID prepare` (or `hold`, `decline`).
- Create `research/batches/YYYY-MM-DD-label/notes.md` with the selection message, the job IDs and, later, the package paths. Current stages stay in the tracker.

## 2. Prepare them all

- Prepare every selected job, deadlines first, then best fit. Don't stop after the first, and don't let one blocked job hold up the rest.
- Collect questions as you go. Ask each shared question **once**, saying which jobs it affects ("Your notice period: needed for 9 of these"). For employer-specific questions, bring a suggested answer. Send them in one grouped message, not one at a time.
- Save each answer to `profile/answers.md` so it covers this batch and every future one. Update every affected draft.

## 3. One review

Create `research/batches/…/review-v1.md` from [the template](../templates/batch-review.md): a numbered list of ready applications, each linking its CV, cover letter and answers, with decisions highlighted, plus a separate list of jobs that aren't ready and why.

- Changes go into a new version (`review-v2.md`). Only changed packages are resealed and need approving again.
- One message can approve everything or a subset: "Approve and submit all except 7."
- Record approval in each included package's `review/approval.json`: the same quote and message reference, with its own revision and the review path and number. Held or unfinished jobs get nothing.

## 4. Submit them all

- Work through the approved jobs with the submit procedure, running `attempt` right before each click. Don't ask "shall I continue?" between jobs.
- A login, code, CAPTCHA or new question blocks only that job: record its next step and move on.
- Leave a few minutes between submissions to the same system (Ashby especially).
- Give a short progress update every five or so: confirmed, needs you, still to go.
- At the end, check every job against the tracker, report the totals, and list each unfinished job with its next step. Then offer the next batch: *"Shall I find the next 20–25?"*

## Usage limits and resuming

Big batches use a lot of the assistant's allowance, especially on Free and entry plans. Everything is saved as you go. If a limit hits, tell the person: *"I've hit my usage limit. Everything is saved. When it resets, say 'Continue my batch'."* On smaller plans, suggest preparing in groups of about ten.

On "continue": re-read the batch notes, the latest review, the approvals and the tracker. Skip confirmed submissions, resolve unclear ones first, honour new holds, and carry on. Never restart a batch from the beginning.
