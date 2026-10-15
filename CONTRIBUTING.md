# Contributing

Start with README.md and AGENTS.md. Keep the beginner path understandable without knowing Git, APIs or skill syntax. Make routine choices conversational; use scripts for repeatable checks and transformations.

Use fictional candidates and reserved example domains. Do not submit a real CV, application, receipt, browser screenshot or personal workspace in an issue or pull request. Describe problems with a minimal fictional reproduction and remove access links/tokens from logs.

Change the relevant workflow once, then run `python3 scripts/sync_skills.py` if the skill catalogue changed. Keep the generated Codex and Claude entry points consistent. Instructions for fast-moving products need an official source and an as-of date. Avoid universal claims about plans or browser support based on one account.

Run:

```sh
python3 -m unittest discover -s tests
python3 scripts/release_check.py
```

For document work, install `requirements-docs.txt` into an isolated environment, render changed examples and inspect every page. Verify A4 and Letter, long names, multiple roles and missing optional contact fields. Do not bundle fonts or third-party skill files without redistribution rights.

Behavioural scenarios live in `tests/scenarios.md`. Record actual results and limitations. Automated checks cannot establish whether an agent followed the right workflow on both providers.

The project uses the MIT licence. Publishing a release is a separate maintainer decision; passing checks does not grant permission to publish private material.
