# Output format

## Layout

```
**/priority · <scope>** · <one line: what these outputs were about>

1. 🔴 **Do now: <short command form>.** <one to three short sentences>
   - `! <shell command>`  (type this in Claude Code)
   - `/<slash-command> <args>`
2. 🟠 **Decide: <the question>.** <the choices and the recommendation>
3. 🟢 **Done: <what changed>.** <why it matters>
   ```
   <ASCII diagram when the point explains a flow or a structure>
   ```
4. 🟣 **Later: <what you will do, and when>.** <the steps>
5. 🔵 **Concept: <term>.** <plain explanation>
```

- **Scope** is `last output`, or `last N outputs`, plus `· focus: <text>` when the user gave a focus.
- The header line gives the topic in one line. Then the numbered points follow, in priority order (see `prioritization.md`). Nothing comes after the last point: no recap and no "let me know".
- A point is a bold lead phrase, then at most about four short sentences. Sub-bullets and a diagram can follow, indented under the point.

## Badges and lead words

The badge gives the colour, and the lead word gives the meaning, so the point still reads correctly where colour doesn't show. Always use both.

| Badge + lead | Use for |
|---|---|
| 🔴 **Do now:** | an action the human must take now |
| 🟠 **Decide:** | a question or choice waiting for the human |
| 🟠 **Warning:** | a failure, risk, limit or correction |
| 🟢 **Done:** | an outcome that already happened |
| 🟣 **Later:** | an action for later, with when |
| 🔵 **Concept:** / **Background:** | an idea to understand / context |

The badge also tells `ste_check.py` how strict to be: 🔴 and 🟣 are procedural, 🟠 and 🟢 are descriptive, 🔵 is explanatory.

## Bold

- The lead phrase of every point is bold: it is the anchor the eye scans for.
- Inside a point, bold at most two more things the reader must not miss, such as a consequence, a deadline, or the one word that changes the meaning.
- Bold phrases, not whole sentences. If everything is bold, nothing is.

## Actions: exactly what the human types or does

Every action shows the **exact** text to type, in a code span, copied verbatim from the outputs. Invent nothing beyond adding the `!` prefix.

| The action is… | Write it as | Also say |
|---|---|---|
| a shell command to run inside Claude Code | `! git status` | "type this in Claude Code" (the `!` runs it in this session and the output lands in the chat) |
| a shell command that starts or replaces Claude Code, like `claude` itself, or a process meant to run in its own window | `cd ~/project && claude` | "in a normal terminal, not inside Claude Code" |
| a slash command | `/mattpocock-skills:to-tickets path/to/spec.md` | what it starts |
| a reply the session waits for | type: `yes` | what the reply chooses, and how to choose differently |
| a step outside the terminal (browser, dashboard, email) | numbered sub-steps, one action each | the page or app it happens in |

- Put a 🔴 point first whenever the session is waiting for the human. If nothing waits, add a 🟢 **Done: nothing to do now.** point that says what Claude is waiting for or doing.
- Later actions go in 🟣 points, in the order they will happen. Name the trigger, as in "after ticket 01 is done", so the reader knows *when*.
- A warning that belongs to an action goes **before** the action, in the same point.

## Diagrams

Draw a diagram whenever a point explains how something **works, moves or connects**:
- a flow (A → B → C);
- a sequence over time;
- a structure or tree;
- a before → after change;
- a state machine;
- what blocks what.

For a single fact or a plain list, skip the diagram.

- Use ASCII inside a fenced code block with no language tag. The terminal does not render Mermaid.
- Keep it at most 60 characters wide and at most 12 lines, and put it directly under the point it explains, indented.
- Label every box and arrow. Use `→` or `──►` for flow, `├─` and `└─` for trees, `[name]` for parts, and `✓` / `✗` for done / not done.
- One idea per diagram. Two flows make two diagrams, in two points.

## Words

- When a technical term first appears, gloss it in at most eight plain words: "the `runs` table (where every research job is stored)". Keep names exact: files, commands, products and functions.
- Apply the STE dial for each point's badge (see `ste100-dial.md`). Code, commands, paths, quotes and error messages stay verbatim.
- Address the reader as "you" and the assistant as "Claude".
