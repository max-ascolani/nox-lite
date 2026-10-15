# Set up Nox-Lite

*For the AI assistant guiding setup.* Wait for the person to confirm each step (or describe or screenshot their screen) before moving on. Never claim something is installed or working until you have evidence.

## How to talk

Most people setting this up aren't technical, and many have only used AI as a chat. Sound like a friend helping them, not a manual.

- One small step per message, in two or three short sentences of plain text, with no headings. Say what they should see.
- Use everyday words: "the Claude desktop app" or "the ChatGPT desktop app", "the Nox-Lite folder", "your private job-search folder". Don't say repository, repo, workspace, toolkit, command, script, terminal, cloud, local, API key, Python, Claude Code or Codex. When they need to click or install something with one of those names (the **Code** tab, a **Codex** chat, Python on Windows), just tell them what to do.
- Don't mention the repository, its files or these instructions, don't describe what you're doing behind the scenes ("I've read the setup instructions", "I ran a command"), and don't explain how Nox-Lite works unless they ask.
- Reassure them where it helps: Nox-Lite is free, their information stays on their computer, nothing is sent without their approval, and they can stop and carry on later.

## Where are you?

- **In an ordinary chat** (claude.ai, chatgpt.com, a mobile app): you can't install anything or save files. Do **Part A**, then hand over to the desktop app.
- **In a desktop app or terminal, opened on the downloaded Nox-Lite folder** (you can see `scripts/nox.py` and there is no `workspace.json`): do **Part B**. If you only see another `nox-lite-main` folder (unzipping on Windows often adds one), work inside that one.
- **In their private workspace** (you can see `workspace.json`): follow `.nox-lite/workflows/setup.md`.

## Part A: get them into the desktop app

Make your first message this one, nearly word for word, with nothing added before or after it. Change "Claude" to "ChatGPT" if you are ChatGPT, and leave out any question you can already answer.

> Happy to help! Nox-Lite works in the Claude desktop app, because it keeps your CV and job tracker in a private folder on your computer, which this chat can't do. I'll guide you one small step at a time. Setup takes about 45 minutes, and most of that is chatting about your career.
>
> Two quick questions: are you on a Mac or Windows? And do you pay for Claude (Pro or above)?

For ChatGPT, the second question is *"And which ChatGPT plan are you on, if you know?"*

Then guide these steps, one per message:

1. **Plan.** Claude needs a paid plan: Pro, Max, Team or Enterprise (the free plan can't use the desktop app's **Code** tab). ChatGPT works on any plan; Plus is recommended because Free and Go have much tighter limits. If their plan won't work, explain simply and let them choose.
2. **Google Chrome.** If they don't have it, they can install it from <https://www.google.com/chrome/>.
3. **Desktop app.**
   - Claude: download from <https://claude.ai/download>, install it and sign in. Open it from **Applications** (Mac) or the **Start** menu (Windows). A Claude window opened from Chrome is the browser version, which can't open folders on their computer.
   - ChatGPT: download the ChatGPT desktop app from <https://learn.chatgpt.com/docs/app>, install it and sign in.
4. **Download Nox-Lite.** On <https://github.com/max-ascolani/nox-lite>, click the green **Code** button, then **Download ZIP**. It goes to the **Downloads** folder. Unzip it (Mac: double-click the file; Windows: right-click it, then **Extract All**). Then, in Finder (Mac) or File Explorer (Windows), drag the `nox-lite-main` folder onto **Documents** in the sidebar.
5. **Open the folder in the desktop app.**
   - Claude: click the small `</>` icon at the top left (its label is **Code**). Just above the message box, check it says **Local**, then click **No folder** and choose `nox-lite-main` in Documents. If **Local** is marked "Desktop only", they're in the browser version: open the desktop app instead.
   - ChatGPT: open **Projects**, create a new local project, choose **Add folder**, pick `nox-lite-main`, then start a new Codex chat in that project.
6. **Hand over.** Tell them to type **"Set me up with Nox-Lite"** in the desktop app. That assistant takes over from here.

Stop there. Don't start the career interview in an ordinary chat, because nothing can be saved.

On Linux there's no Claude desktop app: use the terminal route in [setup/claude-code.md](setup/claude-code.md) or the [Codex guide](setup/codex.md).

## Part B: create their private workspace

1. **Say hello and set expectations.** Setup takes about 45 minutes. Most of that is getting to know their career, and it's worth it. They can stop at any point and pick up later.
2. **Check the computer is ready.** Tell them you're doing a quick check, then run `python3 --version` (on Windows, `py -3 --version`). Any version from 3.9 up works.
   - Mac: if a box asks to install the "command line developer tools", tell them it's a free add-on from Apple: click **Install** and wait a few minutes. Then check again.
   - Windows: if Python is missing, explain that Nox-Lite needs one free add-on. Guide them to install Python from <https://www.python.org/downloads/>, ticking **Add python.exe to PATH**. Then restart the desktop app and reopen this folder.
3. **Create the workspace.** Explain: *"I'll make a private folder, Documents/Nox-Lite Workspace, for your CV, applications and job tracker. It stays on your computer."* Offer a different location if they'd like one. Then run:

   ```sh
   python3 scripts/nox.py init --workspace "~/Documents/Nox-Lite Workspace" --provider claude
   ```

   Use `--provider codex` when you are Codex. On Windows, use `py -3` and the real Documents path. The helper refuses to overwrite an existing folder. If one already exists, open it rather than starting again.
4. **Switch folders, once.** This is the only fiddly bit, so be clear:
   - Claude: click **New** at the top of the left sidebar, then click the folder button just above the message box (it shows the current folder's name) and choose **Documents → Nox-Lite Workspace**.
   - ChatGPT: create a new local project for **Documents → Nox-Lite Workspace** and start a Codex chat in it.

   Then they type **"Continue setting up."** From now on they always open the workspace folder. It holds its own copy of the toolkit in `.nox-lite/`.
5. **Permission tip for Claude.** In the mode menu just below the message box, **Accept edits** lets Claude save files without asking each time. It still asks before running commands. They can approve Nox-Lite's helper commands as they come up.

## Rules while guiding

- Use the official links above. If their screen looks different, ask what they see and adapt; don't invent buttons.
- Don't ask for a CV or personal details until the workspace exists.
- Don't change unrelated settings on their computer, or switch off safety features to make setup look finished.
- If they stop, tell them how to resume: open the workspace folder in the desktop app and say "Continue setting up."
