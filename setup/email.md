# Choose how to handle email

Email access is optional. You can research, prepare and submit applications while checking your own inbox. Your choice applies to both connected email tools and browser access to webmail.

| Choice | What Nox-Lite will use email for |
|---|---|
| **Manual — default** | You check messages and complete verification steps yourself |
| **Codes** | Retrieve a verification message for a specific active application you authorised |
| **Outcomes** | Codes plus requested checks for application receipts, interviews and outcomes |

Suggested explanation from the assistant:

> Connecting email can save you checking for a code while we apply. It is optional. You can do those steps yourself instead. If you also want help tracking interview invitations and application responses, we can enable that separately. The account permission screen may grant broader access than these workflow choices, so let's review what it actually says.

## If you prefer manual handling

Leave `email.mode` as `manual`. When a website asks for a code, the assistant names the site and expected message. Check inbox/spam, enter the code or follow the link yourself, then tell the assistant to continue. Codes and verification links should not be saved in the workspace.

After applying, check your inbox for employer requests, confirmations and interviews. You can paste the relevant non-secret text when you want help. An on-page success can still establish submission; lack of an email connection does not make it unsuccessful.

## If you choose a connection

Use the provider's official Gmail/email integration for the account used in your applications. Connect from the actual job-search surface and verify that the tools are available there. For Codex use the Plugins directory; for Claude follow its current connector instructions. If your email provider is unsupported, retain manual mode; do not redirect a whole mailbox as a workaround.

Review permissions before continuing. Some integrations can also send or modify mail. Nox-Lite's codes/outcomes choices are behavioural limits, not a technical restriction on OAuth permissions. Disable unneeded actions in the provider controls where supported. It will not send, reply to, delete, archive or label email without a separate explicit request.

Choose whether to use a dedicated job-search email account if that suits you; it is optional and does not remove the need to understand access. Never change application contact details or existing account emails without the person's instruction.

Test using a narrow, user-approved search for a known job-related message. Do not scan the whole inbox to prove connectivity. Set the selected mode and record only the connection/test outcome, not message secrets. Outcome monitoring on a schedule is a further choice; enabling outcomes mode alone creates no monitor.

To stop, say “Handle email manually from now on.” Update the saved mode immediately. If you also want to revoke the connection, disconnect it in the provider and, where appropriate, Google Account connections. A local setting alone does not revoke account permission.

Official references, checked 14 October 2026: [OpenAI plugins](https://learn.chatgpt.com/docs/plugins), [Claude Google/Gmail capabilities and permissions](https://support.claude.com/en/articles/10166901-use-google-workspace-connectors).
