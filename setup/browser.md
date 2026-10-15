# Connect Chrome

Checked against official documentation on 15 October 2026. The assistant uses your normal Chrome to read job pages and fill in applications. Because it's your own browser, with your usual logins, sites behave as they do for you.

## Claude

1. Install the **Claude in Chrome** extension from the [Chrome Web Store](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn). It's available on all paid Claude plans.
2. Click the extension icon and sign in with the **same Claude account** as the desktop app.
3. Back in your Nox-Lite workspace, say **"Test the browser."** Claude asks to use each new website the first time; allowing the site is enough.

If Claude can't see Chrome from the desktop app:

- Check the extension is switched on in the Chrome profile you normally use, then start a new session in the app.
- Or use the terminal: run `claude --chrome` in the workspace folder, then `/chrome` to check the connection. See [Claude setup](claude-code.md#alternative-the-terminal).
- As a last resort, the desktop app's built-in **Browser** pane can fill in most application forms that don't need a login (Greenhouse, Lever and Ashby forms usually don't). It starts with no saved logins.

Uploads of up to 10 MB work. The extension won't upload files with credential-like names (such as `.env` or `.key`), which never applies to CVs. Not supported inside WSL on Windows. [Official guide](https://code.claude.com/docs/en/chrome).

## ChatGPT (Codex)

1. Update the desktop app, then open **Settings → Computer Use**. If Chrome isn't listed, expand **More browsers**.
2. Select **Chrome**, follow any prompt to install the plugin, then click **Install**. Chrome opens the extension's store page: add it and review the permissions.
3. Return to **Computer Use** and check that Chrome shows **Manage**.
4. **For CV uploads:** in Chrome, open the extensions menu → **Manage Extensions** → the ChatGPT extension's **Details** → turn on **Allow access to file URLs**.
5. In a Codex chat in your workspace, type `@`, choose **Chrome** and say **"Test the browser."**

ChatGPT asks before using each new website. You can allow just that site. [Official guide](https://learn.chatgpt.com/docs/chrome-extension).

## Practice test (sends nothing anywhere)

Nox-Lite includes a practice application form that runs only on your computer. The assistant starts it with:

```sh
python3 .nox-lite/scripts/nox.py practice
```

and opens <http://127.0.0.1:8765> in Chrome. It fills the form with a made-up name and `candidate@example.com`, uploads a dummy file, and tries each outcome: **Success**, **Validation error**, **Uncertain outcome** and **New required question**. It should tell them apart, and never call the uncertain one a success. Press Ctrl+C to stop the practice server afterwards. If port 8765 is busy, the assistant can use `--port` with another number.

When the test works, the assistant records the `browser` and `upload` checks.

## If something goes wrong

- **No browser tools:** make sure the extension is on in the right Chrome profile, restart Chrome and the app, then start a new chat or session.
- **Login, CAPTCHA or "verify you're human":** you complete it; the assistant then carries on.
- **Connection dropped after clicking submit:** the assistant treats the outcome as unconfirmed and checks before doing anything else. It never just clicks again.

Connecting Chrome doesn't give Nox-Lite permission to read your email. Your [email choice](email.md) applies to Gmail in the browser too.
