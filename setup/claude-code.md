# Use Nox-Lite with Claude

Checked against Anthropic's documentation and the Mac desktop app on 15 October 2026. Names can change. If a screen looks different, use the linked official page.

**You need** a Claude Pro, Max, Team or Enterprise plan. The free plan doesn't include Claude Code. Pro is listed at US$20/month, with usage limits. See [pricing](https://claude.com/pricing).

## Main route: the Claude desktop app (no terminal)

1. Download and install the desktop app from <https://claude.ai/download> (Mac or Windows), then sign in. Open it from **Applications** or the **Start** menu. A Claude window opened from Chrome is the browser version, which can't use folders on your computer.
2. Download Nox-Lite from GitHub (**Code → Download ZIP**). It goes to **Downloads**. Unzip it and drag the `nox-lite-main` folder into **Documents**.
3. In the app, click the small `</>` icon at the top left (**Code**). Just above the message box, check it says **Local**, then click **No folder** and choose the Nox-Lite folder.
4. Type **"Set me up with Nox-Lite."** Claude checks Python, creates your private workspace (`Documents/Nox-Lite Workspace`) and asks you to switch to it.
5. Click **New** in the sidebar, click the folder button above the message box and pick **Nox-Lite Workspace**. Say **"Continue setting up."** From now on, always open this folder.

Permission modes are in the menu just below the message box. **Accept edits** lets Claude save files without asking each time but still asks before running commands. For a long batch you can switch to **Auto** if it's offered on your plan. In Auto, Claude works without routine prompts while a safety check reviews each action. [Desktop guide](https://code.claude.com/docs/en/desktop).

The desktop app reads Nox-Lite's `CLAUDE.md` and skills automatically. You can ask in plain English ("find me jobs") or pick a skill such as `/nox-find-jobs`.

## Connect Chrome

Install the **Claude in Chrome** extension and sign in with the same Claude account. See [Chrome setup](browser.md) for steps and a safe practice test. Use the extension rather than the app's built-in Browser pane: the extension uses your normal Chrome, so you're already signed in to your sites and fewer sites get in the way.

## Alternative: the terminal

On Linux, or if you prefer a terminal:

1. Install Claude Code using the command for your system from the [official quickstart](https://code.claude.com/docs/en/quickstart). On a Mac, open **Terminal** (Applications → Utilities). On Windows, open **PowerShell**; the quickstart recommends installing Git for Windows too.
2. Check it worked: `claude --version`.
3. Go to the Nox-Lite folder (Mac: type `cd `, drag the folder onto the window and press Enter) and run `claude --chrome`. Sign in when the browser opens.
4. Say "Set me up with Nox-Lite." After the workspace is created, type `/exit`, `cd` into the workspace folder and run `claude --chrome` again.

In the terminal, `/chrome` shows the browser connection status. [Terminal guide for beginners](https://code.claude.com/docs/en/terminal-guide).
