# Send an idea or problem

Ideas and problems go to Nox-Lite's public GitHub page as an issue, where the maker reads them. Nothing is sent until the person presses the button on GitHub themselves. Run the helper from the workspace root (on Windows, `py -3` instead of `python3`).

1. **Problems: try to fix it first.** Follow [get unstuck](../setup/troubleshooting.md) and run `doctor`. Offer to report only what's still broken.
2. **Write it up.** A short title and a few plain sentences: what they wanted to do, what happened or what they'd like instead, and why it matters. For a problem, add the steps and the exact error message, if there was one. One idea or problem per report.
3. **Keep it anonymous.** It will be public. Leave out names, the employers and jobs they applied to, places, salaries, contact details, document contents and screenshots. Describe things in general terms, such as "a Workday form asked for…".
4. **Show it and ask.** Show the exact title and text, and say it will be public on GitHub. Change anything they want.
5. **Open it.** Save the text to `.runtime/feedback.md`, then run `python3 .nox-lite/scripts/nox.py feedback --workspace . --kind idea --title "…" --body-file .runtime/feedback.md --open` (`--kind problem` for a problem). It opens GitHub's new-issue page with everything filled in, plus the Nox-Lite version, app and operating system. If it doesn't open, give them the `url` it prints.
6. **They send it.** They check it and press the green button. GitHub asks them to sign in first; a free account takes a minute, and they create it themselves. If they'd rather not, give them the text to send to Max on [LinkedIn](https://www.linkedin.com/in/max-ascolani/) or [X](https://x.com/maxascolani) instead.

Don't press the button for them. Thank them in one line and carry on with what they were doing.
