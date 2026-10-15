# Setup checklist

The assistant keeps track of this in `setup-state.json`, so you can stop and resume any time. A step counts as done only when the assistant has actually seen it work, not just when something is installed. Optional steps can be skipped.

For the assistant: record each step with `python3 .nox-lite/scripts/nox.py check --workspace . NAME --status passed|blocked|skipped --evidence "what you observed"`, and update the saved next step when you finish a stage.

| Step | Check name | Done when | Needed for |
|---|---|---|---|
| Workspace | `files` | `doctor` passes: Python works and the workspace folder can be read and written | Everything |
| CV builder | `documents` | A sample CV was built and every page looked right (PDF optional) | Tailored CVs |
| Your material | `profile` | CVs, LinkedIn and notes are read; experience, stories and answers are filled in; open questions listed | Good applications |
| Search brief | `search` | Target roles, locations, dealbreakers and companies are confirmed | Finding jobs |
| Sources | `sources` | A source plan exists, including target companies' career sites | Finding jobs |
| Tracker | `tracker` | Local tracker checked, or a Google Sheet passed a write and read-back test | Keeping track |
| Browser | `browser` | Chrome opened and read the practice form | Applying |
| Upload | `upload` | A dummy file was uploaded and the practice outcomes were told apart | Applying |
| Email | `email` | Manual, codes or outcomes was chosen and saved (manual is fine) | Verification codes |
| First search | `first_search` | A real search ran, the person reviewed the results and chose a usual batch size | Daily searching |
| Schedule (optional) | `schedule` | Requested, a manual run worked and the saved schedule was checked | Automatic daily searches |

**Ready to search:** workspace, search brief and tracker.

**Ready to prepare applications:** your material, CV builder, and the standard answers in `profile/answers.md` filled in.

**Ready to submit:** browser and upload checks, plus an approved batch. Without the browser, the person can submit the prepared materials themselves.

Checks aren't permanent. Recheck after an app update, an account change or a failed connection.
