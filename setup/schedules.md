# Search automatically every morning

Optional. Do one search by hand first and make sure the results are useful. A schedule only *finds* jobs: you still choose which to apply for and approve the applications.

Both desktop apps can run a local scheduled task. **Your computer must be on and awake, and the desktop app open**, at the scheduled time. Cloud schedules can't reach the files on your computer or your Chrome.

## What to say

> Every weekday at 9am Europe/London, run my Nox-Lite job search with my saved preferences and batch size. Check each job is still open and not already in my tracker, add the good ones, and tell me how many you found. Don't submit anything.

Change the time zone to yours. The assistant checks for an existing schedule first, creates or updates one, shows you the saved result, and records it in `research/schedules.md`.

## Claude desktop app

The assistant guides you through it, or you can do it yourself: in the **Code** tab, open **Routines**, choose **New routine**, then **Local**. Pick your Nox-Lite folder, paste the prompt above, choose **Weekdays** and a time, and set the permission mode for the task. If the computer was asleep, a missed run catches up once when the app is next open. [Official guide](https://code.claude.com/docs/en/desktop).

## ChatGPT desktop app

Ask in your workspace project's Codex chat, using the prompt above. Scheduled tasks appear under **Scheduled** in the sidebar, where you can see recent runs. Keep the computer on and the app running. [Official guide](https://learn.chatgpt.com/docs/automations).

## After it's set up

Check the first real run's results. A schedule that saved correctly isn't proof that a run worked. Then you can say things like:

- "Prepare applications for the best 10 from this morning."
- "Move my search to 8am on Mondays and Thursdays."
- "Find up to 10 new jobs per search from now on."
- "Why didn't my search run this morning?"
- "Pause my job search." or "I accepted a job. Stop my searches and keep my records."

The assistant checks the real schedule in the app, not just its own notes. Logins or CAPTCHAs can still need you at run time.
