# Examples

Two worked examples. Copy the **shape and the judgement**, not the content.

---

## Example 1: `/priority` (the last output only)

**Input (excerpt of the last output).** Claude explained what tickets are, then showed a table of four proposed tickets for "PR 1":
- 01 is a Logfire signup that the user does with a wizard;
- 02 is "submit a query and look up its run";
- 03 is "watch a run move through its statuses", blocked by 02;
- 04 is "see a run as one trace in Logfire", blocked by 01 and 03.

It ended with: "❓ Q14 - Shall I write these 4 tickets as files? … What 'yes' commits you to: … your next session starts with ticket 01 … then you type `/mattpocock-skills:implement` on ticket 02."

**Output.**

**/priority · last output** · Claude proposed four tickets for PR 1 and waits for your answer.

1. 🔴 **Do now: answer Q14.** Claude cannot continue until you reply. To accept the four tickets, type: `yes`
   - To change the plan, say what to change, for example: `split 02`
2. 🟢 **Done: PR 1 now has a ticket plan, but it is not saved yet.** A ticket is one job. Claude builds each ticket in its own `/implement` session. The files get written only after your "yes".
   ```
   01 Set up Logfire (you) ─────────────────┐
                                            ▼
   02 Submit a query ──► 03 Watch statuses ──► 04 See the trace
   ```
3. 🟣 **Later: two things only you can do.**
   1. Next session, do ticket 01. A wizard guides you through a Logfire signup, in about 5 minutes.
   2. For each ticket after that, type `/mattpocock-skills:implement` with the ticket file. Claude gives you the exact file name.
4. 🔵 **Concept: tracer bullet.** Each ticket goes through **every layer**: the request, the code, the database and the response. So you can try it in `/docs` (the app's built-in test page) as soon as it is finished.
   ```
   request → code → database → response    (one ticket = one full path)
   ```
5. 🔵 **Concept: "Blocked by".** A ticket waits until the tickets it names are finished. Ticket 04 needs both 01 and 03.

**Why it looks like this:**
- The pending question is point 1, with the exact reply to type.
- The table became one diagram, because it shows what blocks what.
- The two "you do this" actions moved to a 🟣 point, with when.
- Jargon got a short gloss: "ticket", "`/docs`", "tracer bullet".
- The 🔴 and 🟣 points use short command sentences (high STE). The 🔵 points are freer.

---

## Example 2: `/priority 3` (merge three outputs)

**Input (three outputs, oldest first).**
1. Claude explained test **seams** and asked "Q13 - Are these the right test seams?", recommending yes.
2. The user said yes. Claude then wrote the spec file, committed it on branch `pr-1-service-skeleton`, updated its memory, and listed the next commands:
   - `cd ~/Desktop/project && claude` to start a new session;
   - `/mattpocock-skills:to-tickets .scratch/pr-1-service-skeleton/spec.md`.
3. Claude proposed four tickets and asked "Q14 - Shall I write these 4 tickets as files?".

**Output.**

**/priority · last 3 outputs** · Claude saved the PR 1 plan, proposed four tickets, and waits for your answer on them.

1. 🔴 **Do now: answer Q14.** Type `yes` to save the four proposed tickets as files, or say what to change.
2. 🟢 **Done: Q13 is answered, and the plan is saved.** You accepted the test seams. Claude wrote the spec, `.scratch/pr-1-service-skeleton/spec.md`, and committed it on branch `pr-1-service-skeleton`. Nothing went to GitHub yet, and `main` did not change.
   ```
   main ── eee3726 (unchanged)
     └─ pr-1-service-skeleton ── a640d06 ✓ spec, glossary, rules
   ```
3. 🟠 **Warning: one command from output 2 is out of date.** Output 2 told you to run `/mattpocock-skills:to-tickets …` in a new session. **You already ran it** in this session (output 3), so skip that step.
4. 🟣 **Later: when you start the next session.**
   1. In a normal terminal, not inside Claude Code, run: `cd ~/Desktop/project && claude`
   2. Do ticket 01: the Logfire wizard, which takes about 5 minutes.
   3. Type `/mattpocock-skills:implement` with the file of ticket 02.
5. 🔵 **Concept: seam.** A seam is the place where a test connects to the app. PR 1 tests the app from the outside, through its two endpoints, like testing a vending machine from its buttons.
   ```
   test ──► POST /research/query ──► app ──► database
   test ──► GET  /research/{id}/status ◄────────┘
   ```

**Why it looks like this:**
- Q13 is no longer pending, because output 2 answered it, so it became a 🟢 outcome.
- The `to-tickets` instruction in output 2 was superseded by output 3, which needed a 🟠 warning so the reader does not run it twice.
- `cd … && claude` starts Claude Code, so it says "in a normal terminal", not `!`.
- One point per idea. The three outputs became five points, not fifteen.
