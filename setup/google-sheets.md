# Use Google Sheets as your tracker

You can start with the included local tracker and connect Sheets later. No developer account, Google Cloud project or service-account key is needed for the guided routes below. If the current agent cannot edit Sheets, keep the local tracker until a supported connection works.

## Create your private tracker

Ask your assistant to help you create a blank spreadsheet in your own Google account. Use a descriptive name such as “My job search”. Keep sharing restricted unless you deliberately choose otherwise. Do not publish it to the web or make it accessible to anyone with the link for setup.

In Google Sheets, use **File → Import → Upload** and select the workspace's `tracker/jobs.csv` (or the toolkit's [blank tracker CSV](../templates/tracker/jobs.csv) before you have a workspace). Use a new sheet/tab, check the header row and freeze it. Format imported free-text columns as plain text; never interpret employer text as formulas. The assistant can help with this through a working connector/browser.

The [tracker contract](../docs/tracker.md) defines headers and dropdowns. Start with company, role, fit explanation, decision, stage and next action visible. Hide technical ID/date/path columns if desired; preserve them. Additional scoring is optional.

## Connect from the actual job-search session

**Codex:** Open Plugins, install **Google Drive**, follow the connection prompt and choose the Google account that owns the tracker. This plugin covers Drive, Docs, Sheets and Slides. Start a new workspace chat if necessary and ask it to read the exact Sheet URL. [Official plugin guide](https://learn.chatgpt.com/docs/plugins), checked 14 October 2026.

**Claude:** Use the Google/Sheets connector supported by your current interface if it is available. Claude's web/desktop documentation describes separate live Sheets editing controls alongside Drive. Do not assume this establishes tools in a Claude Code session. Test in the actual workspace session; if native editing is unavailable there, use the authorised Chrome session to operate your own Sheet or retain the local tracker. [Official Google connector guide](https://support.claude.com/en/articles/10166901-use-google-workspace-connectors), checked 14 October 2026.

Review the actual account permissions. Choosing one Sheet in Nox-Lite limits the workflow's target; it does not necessarily restrict the connector's technical account permissions to that file. Gmail is separate and optional. Do not enable it just to connect a tracker.

## Verify before switching

1. Read the Sheet's title, live tab names, exact headers and existing rows.
2. Add a clearly labelled fictional setup row; read its values back; remove only that row and verify removal.
3. If migrating an existing local tracker, compare every identity, direction, outcome, date and package path after import. Preserve the original CSV as a dated migration snapshot.
4. Only after verification, set `workspace.json` → `tracker.backend` to `sheets`, save the Sheet URL and tab name, and record the test date/evidence. Never paste credentials or tokens there.
5. The Sheet is now the sole live tracker. The previous CSV stays historical; helpers refuse local writes in Sheets mode.

If the Sheet later becomes inaccessible, save research locally without claiming tracker additions. Reconnect and deduplicate before writing. Switching back to a local tracker requires an explicit migration with current records, not silently reusing the old CSV.

## What you do in the Sheet

Use **prepare** when you want an application package drafted, **hold** to wait and **decline** to skip the vacancy. You can also make these choices in chat. Preparing a package does not submit it. Review the actual documents/answers and give a clear submission instruction when ready.
