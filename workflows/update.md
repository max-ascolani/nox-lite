# Update Nox-Lite

An update replaces Nox-Lite's own files in `.nox-lite/` with the latest version from GitHub. The person's profile, applications, tracker, settings and the CV builder in `.nox-lite/.venv` stay as they are. Run these from the workspace root (on Windows, `py -3` instead of `python3`).

1. **Check.** Run `python3 .nox-lite/scripts/nox.py update --workspace . --check`. It downloads the latest version and compares it with theirs without changing anything.
2. **Up to date** (`update_available` is false): say so in one line and stop.
3. **Offer it.** Say in a sentence what's new, judged from the changed files (for example "a better CV layout and faster searches"), and ask whether to install it now. It takes a few seconds and doesn't touch their information. Don't list files.
4. **Install** when they agree: run the same command without `--check`. The result names a backup folder in `.runtime/` holding the replaced files. If `requirements-docs.txt` changed, reinstall the CV builder as setup does.
5. **Confirm.** Run `doctor` and check the local checks pass. Then tell them it's done, and that the new version takes full effect the next time they start a chat in this folder.

If the download fails (no internet, a proxy or a certificate error), download <https://github.com/max-ascolani/nox-lite/archive/refs/heads/main.zip> another way, for example `curl -L -o .runtime/nox-lite.zip <link>` (Windows: `curl.exe`). Then run the command again with `--zip .runtime/nox-lite.zip` added, and delete the ZIP afterwards.

If `update` isn't a known command, their copy predates updates. Download the ZIP as above, copy `scripts/nox.py` from inside it over `.nox-lite/scripts/nox.py`, then start again from step 1.

Never update by running setup again, and never copy files into their profile or tracker. In the toolkit folder itself (no `workspace.json`), use Git instead.
