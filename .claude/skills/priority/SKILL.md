---
name: priority
description: Re-explain the last output (or the last N with /priority N) as priority-ordered numbered points, with diagrams and the exact next actions, in STE-inspired plain English.
disable-model-invocation: true
argument-hint: "[N outputs, default 1] [focus]"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/collect_outputs.py *) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/ste_check.py *)
---

# Priority

Re-explain recent session output for a reader who is **overwhelmed**. The result is priority-ordered numbered points:
- the key part of each point in bold, with a colour badge;
- a diagram for anything that explains a flow or a structure;
- every action the reader must take, now or later, written out exactly.

## Source material

```!
python3 ${CLAUDE_SKILL_DIR}/scripts/collect_outputs.py --session "${CLAUDE_SESSION_ID}" --args-file - <<'PRIORITY_ARGS'
$ARGUMENTS
PRIORITY_ARGS
```

## Steps

1. **Scope.** The index above shows how many outputs it covers (oldest first) and the reader's **focus**, if any. The collector reads the arguments as follows:
   - the first token, when it is a positive whole number, is N, the number of outputs (default 1);
   - the rest of the text is the focus.

   If the index says the transcript was not found or not recognised, work from the last N outputs in your context instead.
2. **Hold every output in full.** For each output in the index, find its full text in your context. If one is missing (for example after compaction), run the collector again with `--full`:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/collect_outputs.py --full --session "${CLAUDE_SESSION_ID}" --args-file - <<'PRIORITY_ARGS'
   $ARGUMENTS
   PRIORITY_ARGS
   ```

   Done when the complete text of every listed output is in front of you.
3. **Extract the items.** Read [`references/prioritization.md`](references/prioritization.md), then go through the outputs and list every distinct item:
   - now-actions
   - decisions
   - warnings
   - outcomes
   - later-actions
   - concepts
   - background

   Merge the outputs into one current picture. Done when every command and question the index lists is either an item or deliberately dropped.
4. **Rank** the items with the rubric in that file. The focus raises matching items within their level.
5. **Draft** the answer in the layout of [`references/output-format.md`](references/output-format.md):
   - Make one numbered point per item, in rank order. There is no fixed count.
   - Write each action **exactly**: `! command` for shell commands that run inside Claude Code, `/command args` for slash commands, and the literal reply for questions.
   - Add a diagram to every point that explains how something works, moves or connects.
   - Set the **STE dial** per badge, following [`references/ste100-dial.md`](references/ste100-dial.md). Calibrate on [`references/examples.md`](references/examples.md).
6. **Check.** Pipe the draft through the checker:

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/ste_check.py <<'DRAFT'
   <the draft>
   DRAFT
   ```

   Revise only the types marked `REVISE`. Done when every type shows `OK` and every command in the draft is copied verbatim from the outputs.
7. **Answer** with the final summary only: the header line and the numbered points.
