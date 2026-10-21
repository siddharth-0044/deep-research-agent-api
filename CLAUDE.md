## Working with the developer

The developer is a **complete beginner** with this stack. They have never used Pydantic, and it has been a long time since they used FastAPI endpoints or Alembic. In every session, branch and PR, the developer must understand what is happening as it happens. Work they can't follow counts as vibe coding, not progress.

- **Explain from zero before every question or change.** Define each term in plain words, give an everyday analogy, and show a small concrete example such as a request and response, a table or a diagram.
- **No unexplained jargon.** Don't use a term that hasn't been explained in this session. If it was explained earlier, recap it in one line.
- **Spell out what "yes" commits to.** Every question ends with a plain-words line saying what answering "yes" signs the developer up for.
- **If the developer didn't understand, go back further, not faster.**

## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default triage roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), recorded as a `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Definition of done

A PR is not done until the developer can explain it (see "Definition of done" in `SPEC.md`). Act as a tutor and interview coach, not a quizmaster. For every item in the "Must be able to explain" list of the current PR's spec (`.scratch/<feature>/spec.md`):

1. **Explain** it against the real code and trace.
2. **Quiz** the developer on what you just explained.
3. **Re-explain** anything shaky, then quiz again.

Tick an item only after the developer explains it back correctly. Whenever a decision is made that the developer doesn't yet understand, add an item to that list.

## Where decisions live

Follow the Matt Pocock flow: grilling, then `/to-spec`, then `/to-tickets`, then `/implement` once per ticket. A PR's decisions go into that PR's spec through `/to-spec`. Never add them to `SPEC.md`, which is the assignment brief, or to Claude's memory. Domain terms go in `GLOSSARY.md`.
