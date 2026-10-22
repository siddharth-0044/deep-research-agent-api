#!/usr/bin/env python3
"""Check a /priority draft against a partial ASD-STE100 rule set.

Reads the draft (markdown) on stdin. Each top-level numbered point gets its
type from its badge:

    🔴 do now, 🟣 later (action: procedural)   🟠 decide/warning, 🟢 done (descriptive)
    🔵 concept/background (explanatory)

A point with no badge counts as `done`. Code is verbatim and never checked:
fenced blocks (commands, diagrams) and inline `code` spans. Tables are skipped.

For each type the script reports the share of sentences that pass every
check, against that type's target:

    action 80% (the cap)   decide 60%   done 60%   concept 35%

A type below its target needs revising. A type at or above its target is
finished: stop there. The other sentences stay free to break the rules where
that keeps the meaning clear.

The checks are heuristics in the spirit of STE, not the official standard.
Standard library only. Always exits 0: the report is advice, not a gate.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

TARGETS = {"action": 0.80, "decide": 0.60, "done": 0.60, "concept": 0.35}
CAP = 0.80
MAX_WORDS = {"action": 20, "decide": 25, "done": 25, "concept": 25}
MAX_SENTENCES_PER_POINT = 6
BADGES = {"🔴": "action", "🟣": "action", "🟠": "decide", "🟢": "done", "🔵": "concept"}

RULE_HINTS = {
    "LEN": "split it into shorter sentences",
    "PASSIVE": "use the active voice: say who does what",
    "ING": "use a simple tense or a plain noun instead of the -ing form",
    "ONE": "write one instruction per sentence",
    "COND": "put the condition first: 'If X, do Y.'",
    "WORD": "use the simpler word",
    "SEMI": "no semicolons: write two sentences",
    "CONTR": "write the full form in instructions (do not, it is)",
}

IMPERATIVES = (
    "run|type|open|click|copy|paste|press|go|start|stop|delete|remove|create|add|install|"
    "select|choose|pick|wait|check|read|write|save|close|enter|use|sign|log|answer|reply|"
    "set|put|make|keep|move|rename|restart|push|pull|commit|merge|approve|review|tell|say|"
    "follow|look|find|give|send|ask|cd"
)
POINT_RE = re.compile(r"^\s{0,3}\d+[.)]\s+")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
LIST_MARK_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
EMPHASIS_RE = re.compile(r"(\*\*|__|\*|_)")
BADGE_RE = re.compile("[" + "".join(BADGES) + "]|[➡️❓✅⚠️▶️]️?")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[\"'(\[A-Z0-9])")
WORD_RE = re.compile(r"[A-Za-z0-9][\w'’-]*")
PASSIVE_RE = re.compile(
    r"\b(?:am|is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?"
    r"(\w+ed|\w+en|built|made|done|sent|set|put|kept|left|shown|known|given|taken|"
    r"written|found|run|held|told|paid|bought|caught|taught|thought|brought|meant|split|"
    r"stored|saved|shown)\b",
    re.I,
)
NOT_PARTICIPLE = {
    "open", "even", "often", "seven", "eleven", "token", "tokens", "garden", "kitchen",
    "oven", "children", "then", "when", "ten", "men", "women", "listen", "red", "bed",
    "shed", "seed", "need", "speed", "feed", "indeed", "naked", "sacred", "wicked",
}
ING_RE = re.compile(r"\b([A-Za-z]{3,}ing)\b")
ING_ALLOW = {
    "thing", "things", "nothing", "something", "anything", "everything", "string",
    "strings", "during", "morning", "evening", "ceiling", "spring", "sibling", "siblings",
    "setting", "settings", "warning", "warnings", "meaning", "meanings", "building",
    "buildings", "heading", "headings", "padding", "wording", "logging", "tracing",
    "testing", "polling", "streaming", "routing", "caching", "parsing", "staging",
    "pricing", "billing", "onboarding", "mapping", "mappings", "binding", "bindings",
    "embedding", "embeddings", "finding", "findings", "listing", "listings",
    "recording", "recordings", "king", "ring", "rings", "wing", "wings", "swing",
    "remaining", "opening", "vending",
}
MULTI_RE = re.compile(rf"\b(?:and|then)\b\s+(?:then\s+)?(?:{IMPERATIVES})\b", re.I)
CONTRACTION_RE = re.compile(r"\b(?:\w+n['’]t|\w+['’](?:re|ll|ve|d|m)|(?:it|that|there|what|here|who|let)['’]s)\b", re.I)
LEADING_IMPERATIVE_RE = re.compile(rf"^(?:{IMPERATIVES})\b", re.I)
CONDITION_RE = re.compile(r"\b(if|when|after|before|unless|once)\b", re.I)


@dataclass
class Sentence:
    point: int
    kind: str
    text: str
    flags: list[str] = field(default_factory=list)


@dataclass
class Point:
    number: int
    kind: str
    lines: list[str] = field(default_factory=list)


def load_swaps(path: Path | None = None) -> dict[str, str]:
    path = path or Path(__file__).with_name("word_swaps.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    swaps = data.get("swaps", data)
    return {k.lower(): v for k, v in swaps.items() if not k.startswith("_")}


def swap_regex(swaps: dict[str, str]) -> re.Pattern | None:
    if not swaps:
        return None
    keys = sorted(swaps, key=len, reverse=True)
    return re.compile(r"(?<!\w)(" + "|".join(re.escape(k) for k in keys) + r")(?!\w)", re.I)


def split_points(draft: str) -> list[Point]:
    """Top-level numbered items, with fenced blocks and tables removed."""
    points: list[Point] = []
    in_fence = False
    for line in draft.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or not line.strip() or line.lstrip().startswith(("#", "|", ">")):
            continue
        if POINT_RE.match(line) and (len(line) - len(line.lstrip())) <= 1:
            badge = next((b for b in BADGES if b in line[:40]), None)
            points.append(Point(number=len(points) + 1, kind=BADGES.get(badge, "done")))
        if points:
            points[-1].lines.append(line)
    return points


def clean(line: str) -> str:
    line = LIST_MARK_RE.sub("", line)
    line = INLINE_CODE_RE.sub("CODE", line)
    line = LINK_RE.sub(r"\1", line)
    line = BADGE_RE.sub("", line)
    line = EMPHASIS_RE.sub("", line)
    return re.sub(r"\s+", " ", line).strip()


def sentences_of(point: Point) -> list[Sentence]:
    result = []
    for line in point.lines:
        text = clean(line)
        if not text:
            continue
        for part in SENTENCE_SPLIT_RE.split(text):
            part = part.strip()
            if len(WORD_RE.findall(part)) >= 2:
                result.append(Sentence(point=point.number, kind=point.kind, text=part))
    return result


def check_sentence(sentence: Sentence, swaps: dict[str, str], swap_re: re.Pattern | None) -> None:
    words = WORD_RE.findall(sentence.text)
    limit = MAX_WORDS[sentence.kind]
    if len(words) > limit:
        sentence.flags.append(f"LEN {len(words)}>{limit}")
    for match in PASSIVE_RE.finditer(sentence.text):
        if match.group(1).lower() not in NOT_PARTICIPLE:
            sentence.flags.append(f'PASSIVE "{match.group(0)}"')
            break
    ing = [w for w in ING_RE.findall(sentence.text) if w.lower() not in ING_ALLOW]
    if ing:
        sentence.flags.append("ING " + ", ".join(sorted(set(ing))))
    if ";" in sentence.text:
        sentence.flags.append("SEMI")
    if sentence.kind == "action":
        contractions = CONTRACTION_RE.findall(sentence.text)
        if contractions:
            sentence.flags.append("CONTR " + ", ".join(sorted(set(contractions))))
        if MULTI_RE.search(sentence.text):
            sentence.flags.append("ONE")
        cond = CONDITION_RE.search(sentence.text)
        if LEADING_IMPERATIVE_RE.match(sentence.text) and cond and cond.start() > 0:
            sentence.flags.append(f'COND "{cond.group(0)}"')
    if swap_re:
        for match in swap_re.finditer(sentence.text):
            sentence.flags.append(f'WORD "{match.group(0)}" → "{swaps[match.group(0).lower()]}"')


def analyse(draft: str, swaps: dict[str, str] | None = None) -> dict:
    swaps = load_swaps() if swaps is None else swaps
    swap_re = swap_regex(swaps)
    points = split_points(draft)
    all_sentences: list[Sentence] = []
    long_points = []
    for point in points:
        sentences = sentences_of(point)
        for sentence in sentences:
            check_sentence(sentence, swaps, swap_re)
        if len(sentences) > MAX_SENTENCES_PER_POINT:
            long_points.append((point.number, point.kind, len(sentences)))
        all_sentences.extend(sentences)
    stats = {}
    for kind, target in TARGETS.items():
        group = [s for s in all_sentences if s.kind == kind]
        if not group:
            continue
        passed = sum(1 for s in group if not s.flags)
        rate = passed / len(group)
        stats[kind] = {
            "sentences": len(group),
            "pass_rate": rate,
            "target": min(target, CAP),
            "status": "OK" if rate >= min(target, CAP) else "REVISE",
        }
    return {"points": len(points), "stats": stats, "sentences": all_sentences, "long_points": long_points}


def render(report: dict) -> str:
    if not report["points"]:
        return (
            "STE check: no numbered points found. Write the summary as a numbered list "
            "(1. 2. 3.), one badge per point, then run the check again."
        )
    out = [
        "STE check (heuristic; no target goes above the 80% cap)",
        "",
        f"{'type':<8} {'sentences':>9} {'pass':>6} {'target':>7}  status",
    ]
    for kind, row in report["stats"].items():
        out.append(
            f"{kind:<8} {row['sentences']:>9} {row['pass_rate']:>6.0%} {row['target']:>7.0%}  {row['status']}"
        )
    revise = {k for k, row in report["stats"].items() if row["status"] == "REVISE"}
    flagged = [s for s in report["sentences"] if s.flags]
    if flagged:
        out += ["", "Flags. Fix them in REVISE types only; elsewhere they are allowed:"]
        for s in flagged:
            marker = "fix " if s.kind in revise else "ok  "
            snippet = s.text if len(s.text) <= 90 else s.text[:89] + "…"
            out.append(f'{marker}point {s.point} ({s.kind}) · {" · ".join(s.flags)} · "{snippet}"')
        used = sorted({f.split()[0] for s in flagged for f in s.flags})
        out += ["", "Hints: " + "; ".join(f"{rule} = {RULE_HINTS[rule]}" for rule in used)]
    for number, kind, count in report["long_points"]:
        out.append(f"point {number} ({kind}) · PARA {count} sentences > {MAX_SENTENCES_PER_POINT}: split the point or cut detail")
    if not revise:
        out += ["", "All types meet their targets. Stop revising for STE now."]
    return "\n".join(out)


def main() -> int:
    draft = sys.stdin.read()
    print(render(analyse(draft)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
