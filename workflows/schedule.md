# Schedule a daily search

Only when the person asks. A schedule finds jobs; it never prepares, approves or submits anything. The steps for each app are in [schedules](../setup/schedules.md).

1. **Test first.** Run the same search by hand ([find jobs](find-jobs.md)). If it can't complete, fix that first. Don't create a schedule that can't work.
2. **Ask only what's missing:** days, time and time zone. Use the saved batch size (`search.max_new_jobs`) unless they give a new one.
3. **Check for an existing schedule** in the app and update it rather than creating a duplicate.
4. **The prompt** must: read `workspace.json` and the find-jobs procedure on every run; stop if `search.active` is false; use the current `max_new_jobs`; skip jobs already in the tracker; respect the email mode; save partial progress; and never submit anything. The example in [schedules](../setup/schedules.md) does this.
5. **Create it** with the app's own scheduling feature: Claude desktop **Routines** (Local), or ChatGPT **Scheduled** tasks. Never edit scheduler files directly. Remind them the computer must be awake and the app open.
6. **Read it back** from the app (days, time zone, next run). Then set `scheduling.enabled` to true and `scheduling.platform_id` to its name or ID in `workspace.json`, note it in `research/schedules.md`, and record the `schedule` check.
7. **Check the first real run.** A saved schedule isn't proof a run worked.

## Later

- **"Why didn't it run?"** Check the app's run history, the time zone, whether the computer was awake and the app open, usage limits and sign-ins. Report what you find; don't call a missed run an empty search.
- **Pause:** set `search.active` to false, pause the schedule in the app, and check that it's paused there. Then set `scheduling.enabled` to false, keeping the ID for resuming.
- **Resume or change:** update the existing schedule and read it back.

Report results only when there's something useful: new jobs, a finished run, a failure or a decision needed.
