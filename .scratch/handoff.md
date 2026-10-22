# Handoff: continue on a new machine

Session 1 wrote this note on 2026-10-22, on the original Fedora laptop. The work continues on a MacBook, under a different Claude account. There is no Claude memory carried over: everything the next session needs is in this repo.

**Next session:** read this file. Then run the setup below, and work through the next steps in order. When everything is done, delete this file and the "Start here" note at the top of `CLAUDE.md`.

## Where things stand

- **Nothing is built yet. No code exists.**
- **PR 1 (service skeleton) is fully planned.**
  - Spec: `.scratch/pr-1-service-skeleton/spec.md`. It holds every decision, the 4-PR roadmap (under Further Notes), and the "Must be able to explain" list.
  - Tickets: `.scratch/pr-1-service-skeleton/issues/01…04`.
- **The assignment brief** is `SPEC.md`, with the project-level Definition of done at the end.
- **How to work with the developer** is in `CLAUDE.md`: a complete beginner, tutor-then-quiz, one question at a time, YAGNI, and Context7.
- **Domain words** are in `GLOSSARY.md`. **Research for PR 2** is in `docs/research/pydantic-ai.md`.
- **Push guard:** `.claude/hooks/block-push-to-main.sh` blocks Claude from pushing to `main`. It does not stop the developer's own terminal, because the developer chose a hook only, with no GitHub ruleset. Its tests are `.claude/hooks/test-block-push-to-main.sh`.
- **The `/priority` skill** is in `.claude/skills/priority/`. It works in this repo as-is.

## Decided in session 1, outside PR 1's spec

- **Pydantic AI** is the agent framework from PR 2 onward. The developer chose it and has no prior knowledge of it, so explain it as you go.
- The project builds **two Architectures**. Which two is still open, and gets decided when PR 2 is grilled.

## Setup on this machine (once)

Claude runs these commands, following the "You run the mechanics" rule. The developer does only the interactive logins, by typing `! <command>` in Claude Code.

1. **Check that Matt's plugin is installed.** The project settings enable `mattpocock-skills@claude-plugins-official`, so Claude Code should offer to install it. If `/mattpocock-skills:implement` is still unknown, the developer types `/plugin install mattpocock-skills@claude-plugins-official` and restarts Claude Code.
2. **Install `/priority` for every project**, not only this repo:
   `mkdir -p ~/.claude/skills && cp -R .claude/skills/priority ~/.claude/skills/`
3. **Add Context7**, which is needed for library docs:
   `claude mcp add --transport http --scope user context7 https://mcp.context7.com/mcp`
   An API key from context7.com raises the rate limits. If the developer has one, add it as a header. Then check the server with `/mcp`.
4. **Install the tools:** `git`, `gh`, `uv` and `python3`. `jq` is optional, because the hook falls back to `python3`. With Homebrew: `brew install gh uv jq`. The developer then runs `! gh auth login`.
5. **Re-decide how PostgreSQL 18 runs.** The spec says "Podman, already installed", which was true on Fedora but not on macOS. Grill this one decision with the developer before ticket 02, then record it in the README decision log. The options are:
   - Podman: `brew install podman`, then `podman machine init` and `podman machine start`;
   - Docker Desktop or OrbStack;
   - Postgres.app, or `brew install postgresql@18`.
6. **Check the push guard:** `bash .claude/hooks/test-block-push-to-main.sh` should end with "All hook tests passed".

## Next steps, in order

1. **Teach git worktrees.** The developer asked for this and has never used them from the CLI. Then create the build branch `pr-1-service-skeleton` from `main`, directly or in a worktree. That branch name matches the spec folder, so `code-review` can find the spec.
2. **Ticket 01, done by the developer:** generate the Logfire signup with the `wizard` skill, and the developer follows it.
3. **Ticket 02:** settle the PostgreSQL question from setup step 5 first. Then the developer types:
   `/mattpocock-skills:implement .scratch/pr-1-service-skeleton/issues/02-submit-and-look-up-a-run.md`
4. **Tickets 03 and 04:** one fresh session each, with `/clear` between them. `/implement` does not close a ticket, so update its `Status` and tick its criteria by hand.
5. **Close PR 1.** Teach and quiz the developer on every must-explain item, following the Definition of done. Then open PR 1 with the `pr` skill, and the developer merges it.
6. **Grill PR 2**, the first Architecture. The open decisions are under Out of Scope in the PR 1 spec, and the facts are in `docs/research/pydantic-ai.md`.

## Suggested skills

- `grilling` and `domain-modeling`: for the PostgreSQL question and for scoping PR 2.
- `wizard`: ticket 01.
- `tdd` and `code-review`: they run inside `/implement`.
- `pr`: when opening a PR.
- `research`: for any new facts. Save the results under `docs/research/`.
- **Only the developer can type these:**
  - `/mattpocock-skills:implement`
  - `/mattpocock-skills:to-spec`
  - `/mattpocock-skills:to-tickets`
  - `/mattpocock-skills:ask-matt`, which tells you which skill fits
  - `/priority`

## Gotchas

- **`/priority` depends on the transcript format.** It reads Claude Code's session transcript, whose format is internal and can change between versions. If `/priority` reports "format not recognised", it still works from context. Fix `scripts/collect_outputs.py` when that happens.
- **Old Matt Pocock material uses old names.** Older videos and articles say `/grill-me`, `/to-prd` and `/to-issues`, where the current names are `/grill-with-docs`, `/to-spec` and `/to-tickets`. The recommended video is "mattpocock/skills: A complete AI Coding workflow, end-to-end", https://www.youtube.com/watch?v=M6mYodf0dJM. Start at 6:52.
- **Check model limits before choosing models in PR 2.** Free OpenRouter models allow only 50 requests a day without $10 of credit (see the research notes).
- **The developer can't approve their own PR.** GitHub does not let a PR's author approve it, so merging is enough.
