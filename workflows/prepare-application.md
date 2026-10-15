# Prepare applications

For one job or many. With several, also follow [batch coordination](batch-applications.md): prepare them all, ask shared questions once, and present one review. Preparing is not permission to submit.

"Is this a good fit?" alone means assess the job with [scoring](../docs/scoring.md) and explain it. Don't build a package unless they ask.

## For each job

**1. Read first.** The tracker row, `profile/` (facts, answers, experience, stories, voice, preferences) and [writing](../docs/writing.md). Check `applications/` for an existing package or submission for the same job. Never start a duplicate. Reuse what's there.

**2. Check the job and create the package.** Confirm the posting is still open. Then:

```sh
python3 .nox-lite/scripts/nox.py package --workspace . --company "Northwind" --role "Operations Manager" --url "https://…" --month 2026-10
```

This creates the folder and links it to the tracker row. Save the posting (URL, date checked, full text) in the package's `job.md`.

**3. Audit the form.** Open the application form and list every field in `answers.md`: label, type, options, required or not, character limits and upload formats. Include conditional questions. Never submit anything to reveal a later page; note pages you couldn't see. The [ATS playbook](../docs/ats-playbook.md) has tips for each system.

**4. Answer every field.**

- **Standard questions** (right to work, salary, notice, how did you hear, equal opportunities): take the answer from `profile/answers.md` word for word. Check the question's actual meaning and country first.
- **Contact details:** from `profile/facts.md`.
- **Tailored questions** ("why us", free text): research the company (website, product, recent news) and write to [writing](../docs/writing.md).
- **Salary:** follow the disclosure choice in `profile/answers.md`. If a form requires a number and none is recorded, it's a question for the person. Never pick one.
- **Anything new:** draft an answer if the profile supports it, marked as a draft. Otherwise list it as a question for the person. Never invent a fact.

**5. Tailor the CV.** Copy the relevant parts of `profile/experience.md` into the package's `cv.json`: rewrite the summary for this job, choose and order the bullets, use the ad's terms where true. Map key claims to sources in `evidence-map.md`. Build it and look at every page ([documents](../docs/documents.md)).

**6. Cover letter.** If the form has a field or upload for one, write `cover-letter.md`. Build a file only if an upload is needed.

**7. Check.** Run `check_writing.py` on `cv.json`, `cover-letter.md` and `answers.md` with `--company`, `--workspace .` and `--package`. Fix every problem. Check every warning (each flagged number must be in the profile or the job ad, or come out).

**8. Seal for review.** Fill `review.md`: what's attached, the answers, decisions needed, and anything notable (a job-ad trap, a gap, an unusual question). Then:

```sh
python3 .nox-lite/scripts/nox.py seal PACKAGE
python3 .nox-lite/scripts/nox.py update-job --workspace . JOB_ID --stage ready_for_review --next-action "Review"
```

## Review and feedback

Show one job's package directly, or a batch as one numbered review (see [batch coordination](batch-applications.md)). Show the actual CV and every answer, not a summary of them.

When the person answers a question or corrects something:

- **Save every reusable answer to `profile/answers.md`** (under "Other answers", with meaning, scope and date), and corrected facts to the file that owns them. That's how the next batch asks fewer questions.
- Company-specific answers stay in the package.
- Rebuild changed documents, check them again, and seal again. A new seal needs approval of the changes.

## Approval

Record approval only from the person's actual words. Copy [the template](../templates/approval.example.json) to `review/approval.json` and fill it in:

- `revision` from `review/manifest.json`;
- `approved_at`;
- `user_reference` (which message, plus the batch review path and number if it's a batch);
- `approval_quote` and `submission_authorization_quote` (their exact words; one message can be both, for example "Approve all and submit");
- `form_checked_at`;
- `render_evidence` (which pages you looked at).

If their message already asks you to submit, go straight to [submit applications](submit-application.md). A prepared package isn't a submitted application.
