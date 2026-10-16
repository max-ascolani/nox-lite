# One job tracker

The active tracker is selected in `workspace.json`: `local` or `sheets`. The local CSV works immediately. Google Sheets is an optional upgrade, with [guided setup and migration](../setup/google-sheets.md). Never write a second tracker when the chosen one is unavailable. Save pending evidence in the relevant package and reconcile after access returns.

## What the person sees

People never need the CSV. After every helper write, Nox-Lite rebuilds a readable copy in `tracker/`: a browser page (`Job tracker.html`, which works offline and loads nothing from the internet), an Excel file (`Job tracker.xlsx`, which opens in Excel or Numbers), or both. Each shows plain status words, puts what needs the person first, and links to the job ad and the application folder. The page also has a search box and buttons that copy a suggested message for the chat, such as "Show me the … application"; none of them approves or sends anything. The copies are rebuilt from the CSV, so edits made in them are lost: changes go through the assistant. If a copy can't be written (on Windows, Excel locks a file that's open), the tracker change still succeeds and the helper prints a note. The copy catches up with the next change.

`workspace.json` → `tracker.view` holds the choice: `format` (`page`, `excel` or `both`; `page` if missing), `detail` (`simple` or `detailed`) and `columns` (empty unless the person added or dropped a column). Change it with the helper, which also rebuilds the copy and removes one that's no longer chosen:

```sh
python3 .nox-lite/scripts/nox.py view --workspace . --format both --detail simple
python3 .nox-lite/scripts/nox.py view --workspace . --add salary --drop location
python3 .nox-lite/scripts/nox.py view --workspace . --open
```

| Column | Simple | Detailed |
|---|---|---|
| `company`, `role`, `status` (always shown) | ✓ | ✓ |
| `next_step`, `fit` (the score), `applied`, `link` (the job ad) | ✓ | ✓ |
| `fit_reason`, `location`, `salary`, `checked`, `package` (the application folder) | | ✓ |

`--detail` starts again from that preset. `--open` opens the copy in the person's default app (the page, when there are both). In Sheets mode there's no local copy: the Sheet is what the person sees.

## Columns

Keep these headers in this order for the local CSV and starter Sheet. Live Sheets operations must inspect actual metadata, headers, validation and relevant rows first.

| Column | Meaning |
|---|---|
| `job_id` | Stable identifier derived from canonical vacancy URL; preserved on reconciliation |
| `company` | Hiring organization |
| `role` | Advertised role title |
| `url` | Canonical employer/ATS vacancy URL; keep identity query parameters |
| `location` | Confirmed location and remote/hybrid constraints |
| `salary` | Advertised or researched range with currency, period and source; unknown if absent |
| `fit` | Short evidence-based fit explanation and gaps, not a hiring probability |
| `decision` | User direction: blank, `prepare`, `hold`, `decline` or `submitted` |
| `stage` | Observed progress from the stages below |
| `next_action` | Concrete next action and person responsible |
| `checked_at` | When vacancy status was actually checked, ISO timestamp with timezone |
| `applied_at` | Confirmed submission timestamp, empty until supported by evidence |
| `package` | Workspace-relative package path, empty until one exists |

Use `discovered`, `preparing`, `ready_for_review`, `verification_needed`, `unconfirmed`, `applied`, `interview`, `offer`, `accepted`, `rejected`, `withdrawn` or `closed` as the stage. `submitted` is recorded only after confirmation; it is not an instruction to submit. `prepare` chooses preparation and does not authorize sending.

Do not reset a hold, decline, successful application or uncertain attempt just because a vacancy appears in another search. Assess aliases across company + role + location + vacancy ID/URL. The helper removes known tracking parameters and normalizes Ashby application suffixes, but cannot infer every cross-platform duplicate. Keep identity-bearing query parameters such as `jobId`.

## Writes and evidence

Users can select several jobs together by marking their decisions `prepare`, or by telling the assistant which companies, roles or displayed list entries they want. The assistant resolves each to a stable vacancy identity, preserves other decisions and reads back the selection. A batch does not require extra tracker columns or a separate tracker. Current stages and next actions remain here; the dated batch review records the exact packages presented for approval. See [batch coordination](../workflows/batch-applications.md).

For Sheets, locate the current row by identity each time. Do not retain row numbers as identifiers. Make the smallest update, preserve unrelated cells and formatting, and read it back. Use literal/raw text writes for external text; neutralize spreadsheet formula prefixes if importing CSV. Preserve dropdown validation and add compatible rules only after inspecting the live sheet.

For local CSV, change the file only through the helper; never hand-edit it. Each command locks writes, validates headers, protects formula-looking values and reads back the row. The assistant must supply the real evidence; the helper does not infer success.

- `add-job` adds a vacancy as `discovered`. Optional: `--location`, `--salary`, `--fit`, `--next-action`, `--checked-at`.
- `decision` records the user's direction: `prepare`, `hold` or `decline`.
- `update-job` changes only the fields given: `--stage`, `--next-action`, `--applied-at`, `--salary`, `--location`, `--fit`, `--checked-at`, `--package`, `--decision`. It refuses an unknown stage; `--stage applied` without a confirmation time (`--applied-at`, ISO with timezone); decision `submitted` unless the stage is `applied` or later (`interview`, `offer`, `accepted`, `rejected`), because it records a confirmed fact, not an instruction; moving an `unconfirmed` attempt or an existing application back to `discovered`, `preparing` or `ready_for_review` (reconcile it to `applied`, `rejected`, `closed` or `withdrawn` first); and a `--package` that is not an existing folder inside the workspace.
- `package` links the new package to the matching tracker row and moves a `discovered` row to `preparing`, never backwards. Its output reports `tracker_updated`; with no matching row or in Sheets mode, record the link separately.

Examples from a private workspace (the assistant runs these):

```sh
python3 .nox-lite/scripts/nox.py add-job --workspace . --company "Example Studio" --role "Operations Coordinator" --url "https://example.com/jobs/42" --fit "Relevant coordination experience; working pattern unconfirmed"
python3 .nox-lite/scripts/nox.py update-job --workspace . <job_id> --stage applied --applied-at 2026-10-15T14:05:00+01:00 --next-action "Wait for reply; follow up 2026-10-29 (assistant)"
```

`unconfirmed` means a click or attempt may have happened without reliable confirmation. It blocks another attempt until the portal, receipt or relevant email has resolved the uncertainty. If submission is confirmed but the tracker update fails, preserve the receipt and repair the tracker later. Never repeat a successful application to repair tracking.

See [submission](../workflows/submit-application.md) for review, snapshot and recovery rules.
