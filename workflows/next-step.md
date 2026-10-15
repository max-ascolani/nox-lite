# What next

Read `workspace.json`, `setup-state.json`, `profile/open-questions.md` and the tracker.

Recommend **one** next step with a reason, plus at most two alternatives, in this order of priority:

1. an interview or deadline coming up;
2. applications waiting for the person's review or approval;
3. an interrupted batch to continue;
4. a question that's blocking several jobs ("Answer these two questions to unblock six applications");
5. setup that isn't finished;
6. a new search: *"Shall I find your next 20–25 jobs?"*

Keep it short. If they seem overwhelmed, suggest one small step, like reviewing three jobs.

Common ways in: "What can you help with?", "Continue", "What needs my attention?", "I'm stuck", "I found a job".

Once a week (when `update_checked_at` in `workspace.json` is missing or more than seven days old), also run the [update](update.md) check. If there's a newer version, add one line offering it. If the check fails, say nothing about it.

## Pause or stop

- **"Pause my search":** set `search.active` to false in `workspace.json`, and pause any real schedule in the app (see [schedule](schedule.md)). Check it's actually paused there; the local setting alone doesn't stop the app.
- **"I found a job":** congratulate them. Ask which job, so you can record it (`update-job … --stage accepted`), and offer to pause searches. Don't withdraw other applications or contact employers unless they ask.
- **"Stop everything, I accepted the job":** record it, turn off searching, pause schedules, and keep all records. Never delete applications automatically.
