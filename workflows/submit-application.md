# Submit approved applications

Only packages the person has seen, approved and asked you to submit. For several, also follow [batch coordination](batch-applications.md): one approval message can cover the whole batch, and you work through it without asking again for each job.

## Before each job

1. Re-read the tracker row. A later "hold" or "decline" wins.
2. Run `python3 .nox-lite/scripts/nox.py check-package PACKAGE`. It refuses if files changed since sealing, the approval doesn't match, or an earlier attempt is unresolved. Fix the cause; never work around it.
3. Open the live form. If a required question has changed or appeared, prepare an answer and get the person's decision for that job. Save their answer to `profile/answers.md` if it could come up again. Carry on with the others.

## Fill, check, submit once

Follow the [ATS playbook](../docs/ats-playbook.md):

4. Fill every field with the approved values from `answers.md`, and upload the approved files from `exports/`.
5. Read every field back, check uploads finished, and scan the page for errors or empty required fields. Fix them.
6. Run `python3 .nox-lite/scripts/nox.py attempt PACKAGE` immediately before the final click. It records an unconfirmed attempt and snapshots exactly what's being sent.
7. Click submit **once**.
8. Look for proof: a new confirmation message from this form, or a confirmation email (see [email](email.md) for what you may check). Save the confirmation text or a cropped screenshot in the package's `submission/` folder.

Logins, CAPTCHAs, account creation and assessments go to the person; move on to the next job meanwhile. If the site emails a code, follow [email](email.md) and set the stage to `verification_needed`. Never store the code.

## Record the result

9. In the new `submission/…-attempt.json`, set `outcome` to `confirmed`, `failed` or `unconfirmed`, add `observed_at`, and set `confirmation_evidence` to the saved file's path inside the package (for example `submission/confirmation.png`).
10. On confirmation, update the tracker:

    ```sh
    python3 .nox-lite/scripts/nox.py update-job --workspace . JOB_ID --stage applied \
      --applied-at 2026-10-15T14:05:00+01:00 --decision submitted --next-action "Wait for reply"
    ```

11. Write `submission/receipt.md`: what was sent (files, answers), when, and the proof.

## When it isn't clear

| What you see | What to do |
|---|---|
| A clear error before anything was sent (for example "Phone is required") | Fix it with the approved values, mark that attempt `failed` with evidence, and run `attempt` again |
| No confirmation, a timeout or a crash after clicking | Mark it `unconfirmed`. Check for a confirmation email or the candidate portal. **Never click submit again** until you know it didn't go through |
| A receipt exists but the tracker is out of date | Update the tracker. Don't apply again |
| The tracker says applied but there's no receipt | Look for evidence or ask the person. Don't apply again |
| A new required question | Prepare an answer and ask the person, for this job only |

Report confirmed, failed and unclear results separately. Never count an unclear one as submitted.
