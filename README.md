# Deep Research Agent API

A FastAPI service that takes one research question, researches it on the web in the background, and returns a cited report. The full assignment is in [`SPEC.md`](SPEC.md).

**Status:** planning is done and no code exists yet. PR 1, the service skeleton, is next. Its plan and tickets are in [`.scratch/pr-1-service-skeleton/`](.scratch/pr-1-service-skeleton/).

> Setup, environment variables, how to run the service, how to view traces, and the decision log get added to this README as each PR lands.

---

## What you (the human) do

Claude writes the code, runs every command, and keeps the ticket files up to date. You start sessions, answer questions, learn the design, and merge pull requests.

"Type in a **normal terminal**" means the Terminal app. "Type **in Claude Code**" means the prompt you get after you run `claude`.

### 1. First time on a new computer

You need Claude Code installed (claude.com/claude-code). If macOS asks to install "developer tools" when you run `git`, click **Install**.

In a **normal terminal**:

```
git clone https://github.com/siddharth-0044/deep-research-agent-api.git
cd deep-research-agent-api
claude
```

Claude Code may ask you to install the **mattpocock-skills** plugin. Say yes, because every `/mattpocock-skills:…` command below comes from it.

Then type this **in Claude Code**:

```
read the handoff and set up this machine
```

Claude reads [`.scratch/handoff.md`](.scratch/handoff.md) and does the setup:
- it installs the tools and `/priority`;
- it adds Context7, which Claude uses to look up library docs;
- it asks you once how PostgreSQL (the database) should run on this machine;
- it teaches you git worktrees (a separate folder for each PR's branch);
- it sets up the folder and branch for PR 1.

It asks you to step in only for things only you can do, such as a browser login.

### 2. Every work session: one ticket

A **ticket** is one small job. Each one gets its own Claude session.

0. In a **normal terminal**, go to the folder Claude set up for this PR and start Claude:
   ```
   cd <the folder Claude told you>
   claude
   ```
   If Claude says you are on `main`, ask it to switch to the PR's branch first. Work never goes straight onto `main`.
1. **Ticket 01 comes first, and you do it yourself.** Type: `help me do ticket 01`. Claude gives you a step-by-step guide (a "wizard") for creating your Logfire account, and you follow it.
2. **Tickets 02, 03 and 04 are built by Claude.** For each one, type the command that starts it. Ticket 02's is:
   ```
   /mattpocock-skills:implement .scratch/pr-1-service-skeleton/issues/02-submit-and-look-up-a-run.md
   ```
   At the end of each ticket, Claude tells you the exact command for the next one.
3. Answer Claude's questions. Each one comes with a recommendation, and replying `yes` accepts it.
4. Claude builds the ticket **test-first** (it writes an automatic check before the code) and explains what it did as it goes. Then tell Claude: `mark this ticket done`.
5. Type `/clear`. It wipes Claude's short-term memory, so the next ticket starts fresh.

```
claude ──► start the ticket ──► Claude builds + explains ──► "mark this ticket done" ──► /clear
   ▲                                                                                       │
   └───────────────────────────────── next ticket ◄────────────────────────────────────────┘
```

### 3. When all of a PR's tickets are done

1. **The learning check.** Claude teaches, then quizzes you on every item in the PR spec's "Must be able to explain" list, and keeps going until you can explain each one back. This is the "Definition of done" in `SPEC.md`: a PR isn't done until you understand it.
2. Claude opens a **pull request** (PR) on GitHub and gives you the link.
3. Open the link and read the summary. Click **Squash and merge**, which is the only option this repo allows, then **Confirm squash and merge**. Or just tell Claude `merge it`, and it does the same.

### 4. Planning the next PR

1. Tell Claude: `let's plan PR 2`. Claude interviews you one question at a time (this is called "grilling").
2. When Claude says the interview is done, type `/mattpocock-skills:to-spec`. It writes the plan.
3. When that finishes, type `/mattpocock-skills:to-tickets`. It shows you a ticket list and asks if it looks right before it saves anything.
4. **Don't type `/clear` during steps 1 to 3.** The three steps need the same conversation. After them, go back to section 2.

### Commands you type in Claude Code

| Command | When |
|---|---|
| `/mattpocock-skills:implement <ticket file>` | building one ticket |
| `/mattpocock-skills:to-spec` | after the planning interview: writes the plan |
| `/mattpocock-skills:to-tickets` | right after `to-spec`: splits the plan into tickets |
| `/mattpocock-skills:ask-matt` | "which of these should I use now?" |
| `/priority` | lost? It re-explains Claude's last answer as ranked points. `/priority 3` covers the last three answers. |
| `/clear` | between tickets (never during planning) |
| `! <command>` | runs a terminal command inside Claude Code when Claude asks you to, for example `! gh auth login` |

### Rules worth knowing

- **Nothing goes straight to `main`,** the official copy of the code. A hook (an automatic check) stops Claude from pushing there, so every change arrives through a PR that you merge. Your own terminal isn't blocked, so don't push to `main` yourself either.
- **Lost or overwhelmed?** Type `/priority`, or tell Claude "explain that from zero".
- **New to this workflow?** Watch Matt Pocock's video "mattpocock/skills: A complete AI Coding workflow, end-to-end" from 6:52: https://www.youtube.com/watch?v=M6mYodf0dJM&t=412s

## Where things live

| Path | What it is |
|---|---|
| `SPEC.md` | the assignment brief and the project's Definition of done |
| `CLAUDE.md` | how Claude works with you (Claude reads it automatically) |
| `GLOSSARY.md` | the project's words: Run, Architecture, Plan, … |
| `.scratch/<pr>/spec.md` | one PR's plan and decisions |
| `.scratch/<pr>/issues/` | that PR's tickets |
| `.scratch/handoff.md` | notes for continuing on a new machine. Deleted once PR 1 is merged and PR 2 is planned. |
| `docs/research/` | verified facts about the libraries |
| `.claude/` | project settings, the push guard hook, and the `/priority` skill |
