# Get unstuck

Tell the assistant what you tried and exactly what you saw, leaving out passwords and codes. You can also say "Check my setup and fix what's broken." It runs `doctor`, which explains problems in plain English.

| What happened | What to do |
|---|---|
| The chat can't open the GitHub link | Download START_HERE.md from GitHub and attach it to the chat |
| `python3` not found (Mac) | Run it once: a box offers to install the "command line developer tools". Click **Install**, wait, then try again |
| `python3` not found (Windows) | Try `py -3`. Otherwise install Python from python.org with **Add python.exe to PATH** ticked, then restart the app |
| The CV builder is missing (`python-docx`) | Ask: "Install the CV builder." The assistant creates a small private Python environment in `.nox-lite/.venv` and installs it there |
| No PDF, only Word files | PDF needs LibreOffice (free, optional) from libreoffice.org. Or open the .docx in Word, Pages or Google Docs and save it as a PDF. Most forms accept .docx |
| "Destination already exists" when creating the workspace | This folder is already set up. Say "Continue setting up" |
| The assistant asks things you've already answered | Check the desktop app has your Nox-Lite folder open (the one you set up, usually `Documents/nox-lite-main`), not a fresh download |
| Skills don't appear | Start a new session in the workspace folder. Plain requests still work without them |
| Chrome isn't available | See [Chrome setup](browser.md#if-something-goes-wrong) |
| An upload appears but the form rejects it | Wait for the upload to finish and check the error message on the page. Codex needs **Allow access to file URLs** |
| The application timed out after clicking submit | The assistant keeps it as unconfirmed and checks for a confirmation email or page before doing anything else |
| You hit a usage limit | Progress is saved. When the limit resets, say "continue" |
| A scheduled search didn't run | The computer must be awake and the app open. Ask "Why didn't my search run?" |
| The tracker page or spreadsheet didn't update | If the spreadsheet is open in Excel, close it. It updates with the next change, or say "Update my tracker" |
| "Tracker is locked" | Another task is writing to it. Wait a moment. Don't run two batches at once in the same workspace |

Don't fix problems by switching off safety settings or giving the assistant access it doesn't need.

Still stuck? Say "Report this problem". The assistant writes it up, without your personal details, for you to send to the maker ([feedback](../workflows/feedback.md)).
