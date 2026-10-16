# How Nox-Lite fits together

Nox-Lite is a set of shared procedures, conversation skills and small local helpers. Your chosen assistant runs the procedures using tools available in your session. There is no Nox-Lite account, hosted backend or API key.

```text
Public toolkit                          Private workspace (outside Git)
README / START_HERE                     workspace.json / setup-state.json
workflows/  ← canonical procedures      profile/     ← confirmed context
skills/     ← skill catalogue           inbox/       ← original source material
.agents/    ← generated Codex skills    evidence/    ← provenance and unresolved claims
.claude/    ← generated Claude skills   applications/← review packages and receipts
setup/      ← connection guides         research/    ← source plan and research
scripts/    ← local helpers             tracker/     ← local CSV + readable page/Excel copy
templates/  ← blank starting files      .nox-lite/   ← versioned toolkit snapshot
examples/   ← fictional fixtures        .agents/ or .claude/ ← installed skills
```

## One procedure, two entry points

`AGENTS.md` routes ordinary requests. Codex skills live in `.agents/skills`; Claude Code skills live in `.claude/skills`. The wrappers link to the same workflows, generated from [the catalogue](../skills/catalog.json). They do not duplicate workflow text. Skills can be invoked explicitly, but the default experience is conversation.

The existing search, preparation and submission skills also handle bulk requests. [Batch coordination](../workflows/batch-applications.md) adds shared questions, one review index and continuation across the selected jobs. It is a procedure for the assistant, not a separate background worker. Each job still uses the same package integrity checks and submission evidence.

The toolkit and a personal workspace both have instructions. Inside a workspace, `profile/`, `research/` and `applications/` always mean the workspace root. Tooling and reference paths start with `.nox-lite/`. The initializer copies only the toolkit folders a workspace needs.

## State that survives a new chat

`workspace.json` selects the provider, one authoritative tracker, email mode, locale and search state. `setup-state.json` records observed checks and the next step. The profile separates facts, evidence, preferences and reviewed reusable answers. Each claim should carry its source, confirmation date and limitations.

The tracker answers “what is happening with this vacancy?” The CSV is the assistant's record; people see a page or spreadsheet rebuilt from it after every helper write, so it can't drift. An application package answers “what did we prepare, approve and send?” A package is evidence, not a second tracker. Its path stays stable after preparation; the actual submission date is recorded in the receipt and tracker.

`research/batches/` holds dated selection notes and preserved review versions linking stable job IDs to package revisions. One human message may authorize all displayed unchanged packages; each package records that message against its own revision. Batch notes cannot override current tracker holds, later instructions or uncertain attempts. These review indices are maintained by the assistant; the helper validates each package's files and records, not batch membership or the authenticity of an approval.

## Helper boundaries

`scripts/nox.py` uses Python 3.9+ and the standard library. It initializes and updates workspaces, checks local files, maintains the local CSV, creates packages, hashes review files and snapshots attempts. The practice server listens on localhost and serves only the fictional fixture directory. It never logs into an account, reads mail or submits a real application.

`scripts/ats_search.py` reads public Greenhouse, Lever, Ashby, Recruitee and Workable job boards (plain GET requests, no login or cookies) and returns leads to verify. `scripts/check_writing.py` runs the post-writing checks from [writing](writing.md). Both use only the standard library.

`scripts/build_cv.py` and `scripts/build_letter.py` build clean DOCX files using `python-docx`. PDF conversion is optional and needs LibreOffice. The assistant still needs to review the evidence and inspect every rendered page.

A manifest detects changed files; it cannot prove that a human really approved them. Current conversation instructions and live tracker decisions remain authoritative. Submission helpers fail closed on uncertain attempts, but website behaviour and actual browser actions remain the assistant's responsibility.

## Updating a personal workspace

Setup turns the downloaded folder into your workspace: the toolkit moves into `.nox-lite/` as a snapshot, and your personal folders sit beside it. The snapshot changes only when you agree to an [update](../workflows/update.md). `nox.py update --check` downloads the public GitHub ZIP, reads it in memory (one top folder, no unsafe paths or symlinks) and compares it with `.nox-lite/` file by file. Installing writes only the toolkit's allowlisted files, keeps the replaced ones in `.runtime/update-backup-*`, and then runs the new version's `refresh`, which rewrites the installed instructions and skills and retires skills the new version dropped. `workspace.json` (apart from the version and check dates), `setup-state.json`, profile, research, tracker, applications and `.nox-lite/.venv` are never touched. Never rerun initialization over an existing workspace or reset your profile from blank templates.

The code and [test suite](../tests/README.md) are intentionally small enough to inspect. Provider setup details include official sources and a last-checked date because tools and subscription entitlements can change.
