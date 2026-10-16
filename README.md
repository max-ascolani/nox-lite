# Nox-Lite

**Your own AI job-search assistant, running on your computer. Free and open source.**

> **AI assistant reading this for someone?** Read [START_HERE.md](START_HERE.md) ([plain text](https://raw.githubusercontent.com/max-ascolani/nox-lite/main/START_HERE.md)) and guide them through setup one step at a time, in everyday words. Assume they have never used coding tools.

Nox-Lite turns Claude or ChatGPT into a job-search assistant that:

- **learns your career properly, once.** It reads your CVs, LinkedIn profile and notes, then interviews you, so it can answer application questions without asking again.
- **works out where your jobs are advertised**, for your field and country, and builds a list of companies to watch.
- **finds fresh jobs every day**, straight from company career sites, 20–25 at a time, and tells you plainly which ones fit and why.
- **tailors a CV and every form answer** for each job, in your voice, using only true facts.
- **fills in applications in your own Chrome**, in bulk, after you've reviewed and approved them.
- **keeps track of everything** in a tidy tracker you open in your browser or Excel, and helps you prepare for interviews.

You stay in charge. Nothing is sent without your approval, and your information stays in a private folder on your computer.

## What you need

- A Mac or Windows computer with Google Chrome.
- An AI plan:
  - **Claude** Pro, Max, Team or Enterprise (Pro is US$20/month), or
  - **ChatGPT**: Plus (US$20/month) recommended. Free and Go accounts can try it, with much tighter usage limits.
- About 45 minutes for setup. Most of it is spent telling the assistant about your career, which is what makes every later application good.

Nox-Lite itself is free, with nothing to sign up for: it runs on the AI plan you already have.

## Get started

1. Open [Claude](https://claude.ai) or [ChatGPT](https://chatgpt.com) in your browser.
2. Paste this page's link, `https://github.com/max-ascolani/nox-lite`, and say: **"Help me set this up."**
3. Follow along. The chat helps you install the free desktop app, download Nox-Lite and open it there. From then on, the desktop app does the work. If the chat asks permission to look at Nox-Lite, it's fine to allow it.

If your chat can't open links, download [START_HERE.md](START_HERE.md) and attach it instead.

## Day to day

Talk to it like a person. For example:

| Say | What happens |
|---|---|
| "Find me 25 new jobs" | Searches company career sites and job boards, checks each job is still open, skips ones you've seen, and adds the best matches to your tracker with a reason for each |
| "Prepare applications for 1–12" | Writes a tailored CV and answers for each job, then asks you any missing questions in one go |
| "Looks good, submit them all" | Fills in and submits each approved application in Chrome, and reports back on every one |
| "Help me apply for this job: (link)" | The same, for one job |
| "I've got an interview with Acme on Thursday" | Researches the company and rehearses with you |
| "Search every weekday at 9am" | Sets up a daily search (the desktop app needs to be open) |
| "What should I do next?" | Picks the most useful next step |
| "Check for updates" | Gets the latest Nox-Lite if you agree, without touching your information. It also checks about once a week by itself |

**Work in batches.** A good rhythm is one search a day, then reviewing 10–20 tailored applications in one sitting and approving them with one message. Your time goes on deciding, not on copying and pasting. See the [batch walkthrough](docs/batch-applications.md).

## Why it works

Nox-Lite distils lessons from building Nox, a job-application product, and from running a real job search with it:

- **Apply on the employer's own site.** Direct applications through company career pages (Greenhouse, Lever, Ashby, Workday and similar) did far better than applying through job boards. Nox-Lite searches those sites and applies there.
- **Fit beats volume.** A few strong applications beat a hundred weak ones. It's strict about what counts as a good match and explains its reasons.
- **Ask once, reuse forever.** Every answer you give (notice period, right to work, salary expectations and so on) is saved with its exact meaning, so each new form needs less from you.
- **Your own browser.** It applies from your own Chrome, the way you would, so far fewer sites get in the way.
- **It never makes things up.** If it doesn't know something about you, it asks. It won't guess your salary, right to work or anything legal.

## Your information

- Setup turns the Nox-Lite folder you downloaded (`Documents/nox-lite-main`) into your private folder for your profile, applications and tracker. Nothing is uploaded to GitHub or sent to the Nox-Lite authors.
- Your AI provider (Anthropic or OpenAI) processes what the assistant reads, as with any chat. See [privacy](docs/privacy.md).
- Checking for updates downloads Nox-Lite's public files from GitHub and sends nothing about you.
- Email access is off by default. You enter verification codes yourself unless you choose to connect Gmail.

## Limits

- AI plans have usage limits. A big batch may need to pause and carry on later. Progress is saved, so you just say "continue".
- Some steps need you: logins, CAPTCHAs, and creating accounts on sites like Workday.
- No tool can guarantee interviews. Nox-Lite helps you send good applications quickly; the rest is up to the market.

## More

[Finding jobs](docs/finding-jobs.md) · [Writing guide](docs/writing.md) · [Application forms](docs/ats-playbook.md) · [Batch walkthrough](docs/batch-applications.md) · [Privacy](docs/privacy.md) · [How it fits together](docs/architecture.md) · [Contributing](CONTRIBUTING.md) · Licence: [MIT](LICENSE)
