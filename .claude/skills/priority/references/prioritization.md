# Prioritization

How to turn the outputs into **items**, and how to rank them.

## Items

An item is one distinct thing the reader needs from the outputs: one idea, one point. Every item has one kind:

| Kind | What it is | Badge |
|---|---|---|
| **Now** | Something the human must do before the work can go on: type a command, answer a question, approve, sign in. | 🔴 Do now |
| **Decide** | A question or choice that waits for the human's answer. | 🟠 Decide |
| **Warning** | A failure, a risk, a limit, a skipped step, or a correction of something said earlier. | 🟠 Warning |
| **Outcome** | Something that changed: a file written, a commit, a test result, a decision recorded. | 🟢 Done |
| **Later** | Something the human will have to do further along: a future command, signup, review or session. Say when. | 🟣 Later |
| **Concept** | An idea the reader must understand to follow the other items: a term, a mechanism, a flow. | 🔵 Concept |
| **Background** | Context that helps but changes nothing. | 🔵 Background |

The things the assistant did itself, such as running tests or writing files, are **outcomes**, not actions. An action is something the **human** does.

## Ranking

Order the points by these levels, top first:

1. **Now**: the work is blocked until the human acts. A question that the session is waiting on goes here, not under Decide.
2. **Decide**: questions and choices that wait for the human but don't block yet.
3. **Warning**: anything that changes what the human should do or believe.
4. **Outcome**: what changed, most consequential first.
5. **Later**: future actions, in the order they will happen.
6. **Concept**: ideas needed to understand the points above, in the order the points above need them.
7. **Background**.

Within a level, put first the item whose miss would cost the most. If there is a tie, keep the order in which the outputs said them.

**Focus.** When the user gave a focus (the text after the number, as in `/priority 2 what do I run`), move the items that match it to the top of their level. A concept that matches the focus moves up to just after Decide. Nothing goes above **Now**.

## Merging several outputs

With `/priority N` the outputs overlap. Merge them into one current picture:

- One idea in several outputs is **one** point. The newest wording and facts win.
- A question that a later output answered is no longer pending. Report the answer as an outcome, as in "Done: you chose (A)".
- A plan that a later output replaced appears only in its final form. Mention the change only when it matters to the reader, as a warning: "X was replaced by Y because Z".
- Keep cause before effect when one item explains another.

## Coverage

The collector lists every command and question it found. Each one must end in one of these places:

- a point (an action, a decision, or a command inside a point), or
- deliberately dropped because it is illustrative, already done, or meant for the assistant rather than the human.

Never mention dropped candidates in the output.

## Size

There is no fixed number of points: make as many as there are distinct items.
- Two small items on the same subject and level become one point, as in "three files were created".
- One idea never splits across points.
- A point that needs more than about six sentences is two ideas, or has too much detail. Cut the detail before you add a point.
