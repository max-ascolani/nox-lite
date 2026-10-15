# Application email within the user's chosen scope

Read `workspace.json` → `email.mode` and the current user request before any mailbox access. Modes apply equally to connectors, browser tabs, searches and other tools. Connecting Chrome or Sheets does not authorize email access.

## Manual

Do not read the inbox. For a code, identify the relevant site and expected message, ask the user to check inbox/spam and enter the code directly in the site. They can provide the relevant confirmation or invitation text if they want help interpreting it. Never request a password or persist a code, magic link, session token or recovery secret. Resume from the saved next action.

## Codes

Only retrieve a code/verification message for a specific active authorised application. Search narrowly by site/sender and the current time window. Check that the message corresponds to the requested site and account. Use the code only for that action; do not store it in profile, notes, receipts or logs. Avoid echoing it into chat. Report if unavailable/expired and hand off; do not repeatedly trigger new messages.

This mode does not authorize scanning for interview outcomes, unrelated mail, password resets or outbound email.

## Outcomes

Includes codes plus explicitly requested reconciliation of relevant application receipts and hiring outcomes. A saved mode is permission scope, not a schedule: unattended monitoring requires a separate requested automation. Confirm the time window and opportunities from the tracker. Read complete matching messages; snippets alone may omit a refusal or redirected role.

Match company + role + requisition. Distinguish receipt, interview invitation, assessment, scheduling request, booked meeting, rejection and offer. Silence is not a rejection; an invitation is not an offer. Separate simultaneous applications at one employer. Save minimal relevant excerpts and source/date, never whole unrelated mailboxes or private meeting links.

Re-read matching tracker entries, preserve later outcomes and directions, update only supported milestones and verify readback. A receipt with a stale tracker needs repair, not a second application. No mode authorizes sending, replying, forwarding, deleting, archiving, labelling mail or changing accounts without an explicit request for that action.

If the user revokes email access, set mode to manual immediately, stop mailbox tools and explain how to disconnect the provider. A workflow preference is not revocation of an OAuth permission; guide the actual account disconnection when requested. See [email setup](../setup/email.md).
