# Testing Nox-Lite

Run from the toolkit root with Python 3.9+:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/sync_skills.py --check
python3 scripts/release_check.py
```

Use `discover -s tests` rather than `python3 -m unittest tests.test_nox`: some Python installs ship an unrelated `tests` package that hides this folder.

The tests use only the standard library and temporary workspaces. CV and cover-letter build tests need `requirements-docs.txt` and are skipped if `python-docx` isn't installed, so run release checks in an environment that has it and look at the skip count.

| File | Covers |
|---|---|
| test_nox.py | Workspace creation and isolation, updates (personal files kept, unsafe downloads refused), the tracker helpers, duplicate jobs, formula-safe CSV, sealing, changed approvals and interrupted attempts |
| test_tracker_view.py | The readable tracker page and Excel file: status words, valid files, columns, unsafe job text, and tracker writes that succeed even when the copy can't be written |
| test_documents.py | CV validation and building, the classic layout, fonts, page sizes, overwrite protection, PDF fallback |
| test_writing.py | The writing checks (including CV role habits) and the cover-letter builder |
| test_ats_search.py | Job-board parsing, filters, tracker dedupe and network errors, using the offline fixtures in `fixtures/ats/` |

None of the tests log into anything, send email, contact employers, create schedules or touch the network; the update tests use ZIPs built from the local files. [The acceptance scenarios](scenarios.md) describe the behaviour to check by hand with a real assistant.
