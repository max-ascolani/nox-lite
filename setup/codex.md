# Use Nox-Lite with ChatGPT (Codex)

Checked against OpenAI's documentation on 15 October 2026. Names can change. If a screen looks different, use the linked official page.

**You need** a ChatGPT account. Codex is included in every plan. Free and Go work only in the desktop app, are still rolling out and have tight limits. **Plus (US$20/month) is recommended** for a daily job search. See [pricing](https://learn.chatgpt.com/docs/pricing). No API key or developer account is needed.

## Set up

1. Install the **ChatGPT desktop app** from the [official app page](https://learn.chatgpt.com/docs/app) and sign in.
2. Download Nox-Lite from GitHub (**Code → Download ZIP**), unzip it and move the folder into **Documents**.
3. In the app, open **Projects** and create a new local project. Choose **Add folder** and pick the Nox-Lite folder. Start a new **Codex** chat in that project. It needs to be a local project so Codex can use your files and your browser.
4. Type **"Set me up with Nox-Lite."** Codex checks Python, creates your private workspace (`Documents/Nox-Lite Workspace`) and asks you to switch to it.
5. Create another local project for **Nox-Lite Workspace**, start a Codex chat there and say **"Continue setting up."** From now on, always work in this project.

Codex reads Nox-Lite's `AGENTS.md` and skills from the project's main folder automatically. Ask in plain English, or pick a skill from the skill menu. [Projects guide](https://learn.chatgpt.com/codex/projects).

## Connect Chrome

In the app, go to **Settings → Computer Use**, choose **Chrome** and click **Install**. Then turn on **Allow access to file URLs** for the extension so it can upload your CV. Full steps and a practice test are in [Chrome setup](browser.md).

## Usage limits

Limits depend on your plan and on how much work each request takes. To make them last, reuse saved context (Nox-Lite does this), let searches run in batches, and keep long batches for times when you can check in. If you hit a limit mid-batch, progress is saved: say "continue" when the limit resets.

Scheduled searches can run in the desktop app on a local project. The computer must be on and the app open. See [schedules](schedules.md).
