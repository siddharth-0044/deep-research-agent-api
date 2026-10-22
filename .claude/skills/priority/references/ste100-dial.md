# The STE dial

ASD-STE100 **Simplified Technical English (STE)** is a controlled language, first made for aircraft maintenance manuals. Its job is to make sure a reader, often a non-native speaker working under stress, understands every instruction one way only.

The current standard is **Issue 9**, released on 15 January 2025. It has two parts:
- **writing rules**: 53 rules in 9 sections, covering words, multi-word nouns, verbs, sentences, procedural writing, descriptive writing, safety instructions, punctuation and word count, and writing practices;
- a **dictionary**: about 875 approved words, each with one meaning and one part of speech, plus approved alternatives for about 1,270 unapproved words.

`/priority` readers are in a similar state: overwhelmed, scanning, and needing to act correctly. Research on STE points two ways:
- **It helps.** Studies of maintenance workcards and procedures found the biggest comprehension gains on **complex** text and for **weaker or non-native** readers.
- **It has limits.** Simple text gains little. Critics report that full STE is "very bad" at conveying complex ideas, that forced word swaps can change meaning, and that it reads as stilted.

So this skill is **STE-inspired**, not STE-compliant. It turns a **dial** per point and never goes past **80%**. The rule numbers below refer to Issue 9, paraphrased here. The standard itself is free on request at asd-ste100.org, and its text is copyrighted.

## Dial settings per point

| Badge | Kind of text | Dial | Target in `ste_check.py` |
|---|---|---|---|
| 🔴 Do now, 🟣 Later | procedural: instructions | **80%** (the cap) | 80% of sentences pass |
| 🟠 Decide / Warning | descriptive: choices, risks | 60% | 60% |
| 🟢 Done | descriptive: facts, outcomes | 60% | 60% |
| 🔵 Concept / Background | explanatory: ideas, analogies | 35% | 35% |
| code, commands, paths, quotes, errors, names | verbatim | **0%** | not checked |

The **cap** is a ceiling on how hard to push, not a score to beat. When a type meets its target, stop rewriting it. The remaining sentences stay free to break the rules wherever that keeps the meaning clear.

## The rules this skill applies

### Up to 35%: every point

- **Short sentences.** At most 20 words for an instruction (5.1) and at most 25 for a description (6.3). A code span, a number with its unit, or a name counts as one word (8.4–8.7).
- **One topic per sentence**, and information given gradually (6.1).
- **One term per thing** (1.11). After you call it "the spec", never switch to "the blueprint". Use the reader's own term if they have one.
- **Active voice where it is natural** (3.6): "Claude wrote the file", not "The file was written".
- **No semicolons** (8.1). Write two sentences instead.
- **No telegraphic style** (4.2). Keep the articles and the small words. Short is good; cryptic is not.

### Up to 60%: add these for 🟠 and 🟢

- **Simple tenses only** (3.2): present, past and future. "Is running" becomes "runs", and "has finished" becomes "finished". An "-ing" word is allowed only as a technical noun, like "logging" or "tracing" (3.5).
- **At most three words in a multi-word noun** (2.1). "the run status poll endpoint" becomes "the endpoint that shows the run status".
- **Show an action with a verb, not a noun** (3.7). "The test shows a failure", not "gives an indication of a failure".
- **Concrete, not abstract** (4.1). Say the specific value or file, not "the relevant item".
- **One topic per point, at most six sentences** (6.5, 6.6). Start with the topic sentence, which here is the bold lead phrase (6.4).

### Up to 80% (the cap): add these for 🔴 and 🟣

- **Command form** (5.3). Start with the verb: "Type …", "Run …", "Open …".
- **One instruction per sentence** (5.2). The only exception is two actions done at the same time. Use numbered sub-steps for a sequence.
- **Condition first** (5.4). Write "If the test fails, run it again", not "Run it again if the test fails". The reader then sees the condition before acting.
- **Warning before the step, command first, then the risk** (7.2, 7.3). For example: "Do not push to `main`. The hook blocks the push."
- **No contractions in instructions** (4.2). Write "do not", not "don't".
- **Plain, one-meaning words** (1.1, 1.3, 9.3). Use no phrasal verbs ("find", not "figure out"). Use the swap list below. Technical nouns and technical verbs such as click, type, copy, save and install stay exactly as they are (1.5, 1.12).

### Never applied: the last 20%

These parts of STE are left out on purpose, because here STE backfires for a reader who needs to *understand*:

- **Dictionary-only vocabulary** (1.1 in full). The core list has about 875 words, and many everyday teaching words fall outside it. Banning them makes explanations stilted, and forced swaps can change the meaning.
- **One fixed part of speech per word** (1.2), such as "test" as a noun only. That rules out natural phrasing and analogies.
- **The modal collapse**: STE turns "should" into MUST and "may" into CAN. That erases the difference between a recommendation and a requirement, which a reader deciding things needs.
- **No contractions in explanations**, and "we" only for the publisher. In chat this sounds stiff, so 🔵 points keep a natural tone.
- **Manual formatting**: WARNING and CAUTION blocks and note conventions. It is too heavy for a chat summary.

## When to turn the dial down for one sentence

- An **analogy** carries the explanation ("like testing a vending machine from its buttons"). Keep it, even if it breaks a rule.
- **Nuance or a trade-off** is the point ("simpler, but runs die on restart"). Keep the "but".
- A plain word would **change the meaning**. "Verify" might mean "run the test suite", so say exactly what to do.
- The output already used a term the reader knows. Reuse it, even if it isn't a plain word.

## When to turn it up

- Anything the reader will **act on**: commands, replies, browser steps and warnings.
- **Complex** content: many steps, conditions, or several things that depend on each other. This is where the research shows STE helps most.
- When the reader has said they are **lost or overwhelmed**: shorter sentences, one idea each.

## Plain words

`scripts/word_swaps.json` holds the list that `ste_check.py` uses: 99 swaps such as "utilize → use", "prior to → before", "ensure → make sure", "perform → do", "however → but", and "e.g. → for example" (GR-6).

The pairs follow the Issue 9 dictionary, but the file is our own STE-inspired list, not the official dictionary. Two corrections are worth knowing:
- In STE, APPROXIMATELY is the approved word for amounts. "About" means only "concerned with".
- STE maps "require" and "need" to NECESSARY.

Add a swap to the file when you notice a recurring complex word.

## Self-check

Pipe the draft through the checker:

```
python3 <skill-dir>/scripts/ste_check.py <<'EOF'
<draft>
EOF
```

It prints a pass rate per badge type, plus the flagged sentences:

| Rule | What it flags | Applies to |
|---|---|---|
| `LEN` | a sentence that is too long | every type |
| `PASSIVE` | passive voice | every type |
| `ING` | an "-ing" verb form | every type |
| `SEMI` | a semicolon | every type |
| `WORD` | a complex word with a plainer swap | every type |
| `PARA` | more than six sentences in a point | every type |
| `ONE` | two instructions in one sentence | actions only |
| `COND` | a condition after its command | actions only |
| `CONTR` | a contraction | actions only |

- Fix flags only in types marked `REVISE`. Flags in `OK` types are allowed.
- When every type is `OK`, stop.
- The checks are heuristics, so ignore a flag that is wrong, for example a technical name that ends in "-ing".
