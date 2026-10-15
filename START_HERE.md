# Set up Nox-Lite

*For the AI assistant guiding setup.* The person may never have used developer tools. Take one step at a time, say what they should see, and wait for them to confirm (or describe or screenshot their screen) before moving on. Keep messages short and friendly. Never claim something is installed or working until you have evidence.

## Where are you?

- **In an ordinary chat** (claude.ai, chatgpt.com, a mobile app): you can't install anything or save files. Do **Part A**, then hand over to the desktop app.
- **In a desktop app or terminal, opened on the downloaded Nox-Lite folder** (you can see `scripts/nox.py` and there is no `workspace.json`): do **Part B**.
- **In their private workspace** (you can see `workspace.json`): follow `.nox-lite/workflows/setup.md`.

## Part A: get them into the desktop app

Ask both questions in one message: *Mac or Windows? Claude or ChatGPT, and do you know which plan?*

Then guide these steps, one per message:

1. **Plan.** Claude needs Pro, Max, Team or Enterprise (the free plan doesn't include Claude Code). ChatGPT works on any plan; Plus is recommended because Free and Go have much tighter limits. If they have neither, explain that and let them choose.
2. **Google Chrome.** If they don't have it, they can install it from <https://www.google.com/chrome/>.
3. **Desktop app.**
   - Claude: download from <https://claude.ai/download>, install it and sign in.
   - ChatGPT: download the ChatGPT desktop app from <https://learn.chatgpt.com/docs/app>, install it and sign in.
4. **Download Nox-Lite.** On <https://github.com/max-ascolani/nox-lite>, click the green **Code** button, then **Download ZIP**. Unzip it (Mac: double-click the file; Windows: right-click it, then **Extract All**). Move the unzipped `nox-lite-main` folder into **Documents**.
5. **Open the folder in the desktop app.**
   - Claude: click the **Code** tab at the top, check **Local** is selected, click **Select folder** and choose `nox-lite-main`.
   - ChatGPT: open **Projects**, create a new local project, choose **Add folder**, pick `nox-lite-main`, then start a new Codex chat in that project.
6. **Hand over.** Tell them to type **"Set me up with Nox-Lite"** in the desktop app. That assistant takes over from here.

Stop there. Don't start the career interview in an ordinary chat, because nothing can be saved.

On Linux there's no Claude desktop app: use the terminal route in [setup/claude-code.md](setup/claude-code.md) or the [Codex guide](setup/codex.md).

## Part B: create their private workspace

1. **Say hello and set expectations.** Setup takes about 45 minutes. Most of that is getting to know their career, and it's worth it. They can stop at any point and pick up later.
2. **Check Python.** Run `python3 --version` (on Windows, `py -3 --version`). Any version from 3.9 up works.
   - Mac: if a box asks to install the "command line developer tools", tell them to click **Install** and wait a few minutes. Then check again.
   - Windows: if Python is missing, guide them to install it from <https://www.python.org/downloads/>, ticking **Add python.exe to PATH**. Then restart the desktop app and reopen this folder.
3. **Create the workspace.** Explain: *"I'll make a private folder, Documents/Nox-Lite Workspace, for your CV, applications and job tracker. It stays on your computer."* Offer a different location if they'd like one. Then run:

   ```sh
   python3 scripts/nox.py init --workspace "~/Documents/Nox-Lite Workspace" --provider claude
   ```

   Use `--provider codex` when you are Codex. On Windows, use `py -3` and the real Documents path. The helper refuses to overwrite an existing folder. If one already exists, open it rather than starting again.
4. **Switch folders, once.** This is the only fiddly bit, so be clear:
   - Claude: start a new session (the **+** or **New session** button), click **Select folder** and choose **Documents → Nox-Lite Workspace**.
   - ChatGPT: create a new local project for **Documents → Nox-Lite Workspace** and start a Codex chat in it.

   Then they type **"Continue setting up."** From now on they always open the workspace folder. It holds its own copy of the toolkit in `.nox-lite/`.
5. **Permission tip for Claude.** In the mode menu next to the send button, **Accept edits** lets Claude save files without asking each time. It still asks before running commands. They can approve Nox-Lite's helper commands as they come up.

## Rules while guiding

- Use the official links above. If their screen looks different, ask what they see and adapt; don't invent buttons.
- Don't ask for a CV or personal details until the workspace exists.
- Don't change unrelated settings on their computer, or switch off safety features to make setup look finished.
- If they stop, tell them how to resume: open the workspace folder in the desktop app and say "Continue setting up."
