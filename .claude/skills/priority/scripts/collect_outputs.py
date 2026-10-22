#!/usr/bin/env python3
"""Collect the last N outputs of the current Claude Code session.

An *output* is the assistant text the human saw in one turn. A turn starts at
a human prompt, a subagent (peer) message or a task notification. Tool calls,
tool results, thinking blocks and injected skill bodies belong to the turn
they occur in and are not shown. The turn that is still running (the
/priority call itself) has no `turn_duration` marker yet and is skipped.

Default mode prints an *index* of each output:
- what triggered it;
- its size and headings;
- the commands and steps the human may have to do;
- the questions waiting for an answer.

Use --full to print the complete text, for example when an output is no longer
in the model's context after compaction.

Standard library only. Always exits 0: /priority runs this script while its
skill loads, and a non-zero exit would cancel the whole /priority call. Every
problem is reported as a message instead.

The transcript format is internal to Claude Code and can change between
versions. When it isn't recognised, the script says so, and the summarizer
works from the outputs in its own context.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

TURN_ORIGINS = {"human", "peer", "task-notification"}
UNSUBSTITUTED = {"$ARGUMENTS", "$0", "${ARGUMENTS}"}
TURN_END_SUBTYPES = {"turn_duration", "stop_hook_summary"}
SHELL_LANGS = {"bash", "sh", "shell", "zsh", "console", "fish", "terminal"}

COMMAND_NAME_RE = re.compile(r"<command-name>\s*(/?[^<\s]+)\s*</command-name>")
COMMAND_ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)
SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.S)
SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)\s*([\w+-]*)")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
INLINE_BANG_RE = re.compile(r"`!\s*([^`]+)`")
LINE_BANG_RE = re.compile(r"^\s*!\s+(\S.*)$")
INLINE_SLASH_RE = re.compile(r"`(/[a-z][\w.-]*(?::[\w.-]+)?(?:\s[^`]*)?)`")
LINE_SLASH_RE = re.compile(r"^\s*(/[a-z][\w.-]*(?::[\w.-]+)?(?:\s.*)?)$")
INSTRUCTION_RE = re.compile(
    r"\b(you (?:need to|must|have to|will need to|will have to)|which you do yourself|"
    r"you do (?:this|it) yourself|type this|run this|your turn|your next step)\b",
    re.I,
)
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
SHELL_START_RE = re.compile(
    r"^(cd|git|gh|uv|uvx|python3?|pip3?|pipx|podman|docker|npm|npx|pnpm|yarn|make|"
    r"claude|curl|wget|ls|cat|export|source|alembic|pytest|ruff|chmod|mkdir|rm|mv|cp|"
    r"sudo|dnf|apt|brew|systemctl|ssh|scp|kubectl|terraform|gcloud|aws|az|vercel|neonctl)\b"
)
IMPERATIVE_LINE_RE = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.)]\s+)?(?:\*\*|__)?"
    r"(Run|Type|Open|Paste|Copy|Click|Press|Start|Go to|Sign in|Sign up|Log in|"
    r"Install|Answer|Reply|Choose|Pick|Approve|Restart|Add|Set)\b"
)
QUESTION_LINE_RE = re.compile(r"^\s*(?:❓|\*\*Q\d+\b|Q\d+\s*[-–—:])")
RECOMMENDATION_RE = re.compile(r"^\s*➡️\s*(.+)$")


@dataclass
class Turn:
    """One turn of the session: its trigger entry and the assistant text."""

    number: int
    trigger: dict | None
    texts: list[str] = field(default_factory=list)
    complete: bool = False

    @property
    def text(self) -> str:
        return "\n\n".join(t.strip() for t in self.texts if t.strip())


# --------------------------------------------------------------------------
# Locating and reading the transcript
# --------------------------------------------------------------------------


def config_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def sanitize_cwd(cwd: str) -> str:
    """Claude Code names a project folder after its cwd, non-alphanumerics → '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def _newest(paths: list[Path]) -> Path | None:
    paths = [p for p in paths if p.is_file()]
    return max(paths, key=lambda p: p.stat().st_mtime) if paths else None


def _first_cwd(path: Path) -> str | None:
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for _, line in zip(range(200), handle):
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict) and entry.get("cwd"):
                    return entry["cwd"]
    except OSError:
        return None
    return None


def find_transcript(session: str | None, transcript: str | None, cwd: str) -> Path | None:
    """Explicit path, then session id, then the newest transcript for this cwd."""
    if transcript:
        path = Path(transcript).expanduser()
        return path if path.is_file() else None
    projects = config_dir() / "projects"
    if session and "${" not in session and session.strip():
        hit = _newest(list(projects.glob(f"*/{session.strip()}.jsonl")))
        if hit:
            return hit
    project_dir = projects / sanitize_cwd(cwd)
    hit = _newest(list(project_dir.glob("*.jsonl")))
    if hit:
        return hit
    # Last resort: a project folder whose newest transcript was recorded in this cwd.
    for folder in projects.glob("*"):
        newest = _newest(list(folder.glob("*.jsonl")))
        if newest and _first_cwd(newest) == cwd:
            return newest
    return None


def load_entries(path: Path) -> list[dict]:
    entries: list[dict] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict):
                entries.append(entry)
    return entries


# --------------------------------------------------------------------------
# Turning entries into turns
# --------------------------------------------------------------------------


def content_blocks(entry: dict) -> list[dict]:
    message = entry.get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [block for block in content if isinstance(block, dict)]
    return []


def entry_text(entry: dict | None) -> str:
    if not entry:
        return ""
    parts = [b.get("text", "") for b in content_blocks(entry) if b.get("type") == "text"]
    return "\n".join(p for p in parts if isinstance(p, str))


def is_turn_start(entry: dict) -> bool:
    if entry.get("type") != "user" or entry.get("isSidechain"):
        return False
    blocks = content_blocks(entry)
    if any(block.get("type") == "tool_result" for block in blocks):
        return False
    origin = (entry.get("origin") or {}).get("kind")
    if entry.get("turnPosition") or origin in TURN_ORIGINS:
        return True
    if entry.get("isMeta"):
        return False  # injected skill bodies and context continue the turn
    return bool(blocks)  # older transcripts: a plain user prompt


def build_turns(entries: list[dict]) -> list[Turn]:
    turns: list[Turn] = []
    current: Turn | None = None
    for entry in entries:
        if entry.get("isSidechain"):
            continue
        if is_turn_start(entry):
            current = Turn(number=len(turns) + 1, trigger=entry)
            turns.append(current)
            continue
        kind = entry.get("type")
        if kind == "system" and entry.get("subtype") in TURN_END_SUBTYPES and current:
            current.complete = True
        elif kind == "assistant":
            if current is None:
                current = Turn(number=1, trigger=None)
                turns.append(current)
            for block in content_blocks(entry):
                text = block.get("text")
                if block.get("type") == "text" and isinstance(text, str) and text.strip():
                    current.texts.append(text)
    return turns


def finished_outputs(turns: list[Turn]) -> list[Turn]:
    """Turns with visible text, without the running turn (the /priority call)."""
    usable = list(turns)
    if usable and not usable[-1].complete:
        usable.pop()
    return [turn for turn in usable if turn.text]


# --------------------------------------------------------------------------
# Describing an output
# --------------------------------------------------------------------------


def shorten(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def describe_trigger(entry: dict | None) -> str:
    if entry is None:
        return "(session start)"
    raw = SYSTEM_REMINDER_RE.sub("", entry_text(entry))
    origin = (entry.get("origin") or {}).get("kind")
    command = COMMAND_NAME_RE.search(raw)
    if command:
        args = COMMAND_ARGS_RE.search(raw)
        arg_text = shorten(args.group(1), 120) if args and args.group(1).strip() else ""
        return f"you ran {command.group(1)}" + (f" {arg_text}" if arg_text else "")
    if origin == "task-notification" or raw.lstrip().startswith("<task-notification>"):
        summary = SUMMARY_RE.search(raw)
        detail = shorten(summary.group(1), 120) if summary else "a background task"
        return f"background event: {detail}"
    if origin == "peer":
        return "a subagent reported back"
    return f'you said: "{shorten(TAG_RE.sub("", raw), 200)}"'


def scan_output(text: str) -> dict[str, list[str]]:
    """Headings, things the human may have to do, and open questions."""
    headings: list[str] = []
    actions: list[str] = []
    questions: list[str] = []
    in_fence = False
    fence_is_shell = False
    lines = text.splitlines()
    for number, line in enumerate(lines):
        fence = FENCE_RE.match(line)
        if fence:
            in_fence = not in_fence
            fence_is_shell = in_fence and fence.group(2).lower() in SHELL_LANGS
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if in_fence:
            if (bang := LINE_BANG_RE.match(line)):
                actions.append(f"! {bang.group(1).strip()}    [shell, in a code block]")
            elif (slash := LINE_SLASH_RE.match(line)):
                actions.append(f"{slash.group(1).strip()}    [slash command, in a code block]")
            elif SHELL_START_RE.match(stripped):
                actions.append(f"{stripped}    [shell command in a code block: say where it runs, `! …` inside Claude Code or a separate terminal]")
            elif fence_is_shell:
                actions.append(f"{stripped}    [shell code block: run it or only read it?]")
            continue
        heading = HEADING_RE.match(line)
        if heading:
            headings.append(shorten(heading.group(1), 80))
        for bang in INLINE_BANG_RE.findall(line):
            actions.append(f"! {bang.strip()}    [shell, run inside Claude Code]")
        for slash in INLINE_SLASH_RE.findall(line):
            actions.append(f"{slash.strip()}    [slash command, or maybe a URL path]")
        if not heading and (INSTRUCTION_RE.search(line) or IMPERATIVE_LINE_RE.match(line)):
            actions.append(f'"{shorten(stripped, 160)}"    [instruction]')
            for code in INLINE_CODE_RE.findall(line):
                code = code.strip()
                if not code.startswith(("!", "/")) and SHELL_START_RE.match(code):
                    actions.append(f"{code}    [shell command in an instruction: say where it runs, `! {code}` inside Claude Code or a separate terminal]")
        if QUESTION_LINE_RE.match(line) or stripped.endswith("?"):
            question = shorten(stripped, 220)
            for later in lines[number + 1 : number + 8]:
                rec = RECOMMENDATION_RE.match(later)
                if rec:
                    question += f"  → recommended: {shorten(rec.group(1), 120)}"
                    break
            questions.append(question)
    return {
        "headings": _unique(headings),
        "actions": _unique(actions),
        "questions": _unique(questions),
    }


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# --------------------------------------------------------------------------
# Arguments and rendering
# --------------------------------------------------------------------------


def parse_scope(raw: str) -> tuple[int, str, str | None]:
    """'/priority 3 what next' → (3, 'what next', note). Default N is 1."""
    raw = (raw or "").strip()
    if raw in UNSUBSTITUTED:
        raw = ""
    tokens = raw.split()
    if tokens and re.fullmatch(r"[+-]?\d+", tokens[0]):
        value = int(tokens[0])
        rest = " ".join(tokens[1:])
        if value >= 1:
            return value, rest, None
        return 1, rest, f"'{tokens[0]}' is not a positive number of outputs; using 1."
    return 1, " ".join(tokens), None


def render_index(outputs: list[Turn], total: int, path: Path, focus: str, notes: list[str]) -> str:
    out = [f"# Session outputs: the last {len(outputs)} of {total}", f"transcript: {path}"]
    if focus:
        out.append(f'focus: "{focus}"  (rank items about this higher)')
    out.extend(f"note: {note}" for note in notes)
    for position, turn in enumerate(outputs, start=1):
        info = scan_output(turn.text)
        words = len(turn.text.split())
        out += [
            "",
            f"## Output {position} of {len(outputs)}",
            f"- Trigger: {describe_trigger(turn.trigger)}",
            f"- Size: {words} words, {len(turn.text.splitlines())} lines",
        ]
        if info["headings"]:
            out.append("- Headings: " + " · ".join(info["headings"]))
        out.append("- Things the human may have to do (check each one):")
        out += [f"  - {a}" for a in info["actions"]] or ["  - (none detected)"]
        out.append("- Questions that may be waiting for an answer:")
        out += [f"  - {q}" for q in info["questions"]] or ["  - (none detected)"]
    out += [
        "",
        "Output 1 is the oldest; the last one is the newest. If the full text of an "
        "output is not in your context, rerun with --full.",
    ]
    return "\n".join(out)


def render_full(outputs: list[Turn], total: int, path: Path, focus: str, notes: list[str]) -> str:
    out = [f"# Session outputs, full text: the last {len(outputs)} of {total}", f"transcript: {path}"]
    if focus:
        out.append(f'focus: "{focus}"')
    out.extend(f"note: {note}" for note in notes)
    for position, turn in enumerate(outputs, start=1):
        out += [
            "",
            f"======== Output {position} of {len(outputs)} ========",
            f"Trigger: {describe_trigger(turn.trigger)}",
            "",
            turn.text,
        ]
    return "\n".join(out)


def run(options: argparse.Namespace) -> str:
    raw_args = options.args
    if options.args_file:
        source = sys.stdin if options.args_file == "-" else open(options.args_file, encoding="utf-8")
        with source if source is not sys.stdin else contextlib.nullcontext(source):
            raw_args = source.read()
    count, focus, note = parse_scope(raw_args)
    notes = [note] if note else []
    if options.last is not None:
        count = max(1, options.last)

    path = find_transcript(options.session, options.transcript, options.cwd)
    if path is None:
        return (
            "No transcript found for this session. Use the outputs that are in your "
            "context instead, and tell the user the transcript was not found."
        )
    entries = load_entries(path)
    turns = build_turns(entries)
    if entries and not turns:
        return (
            f"Transcript found ({path}), but its format was not recognised; it is internal "
            "to Claude Code and can change between versions. Use the outputs in your context."
        )
    outputs = finished_outputs(turns)
    if not outputs:
        return "This session has no earlier outputs to explain yet."
    if count > len(outputs):
        notes.append(f"{count} outputs requested, but only {len(outputs)} exist; showing all of them.")
    chosen = outputs[-count:]
    render = render_full if options.full else render_index
    return render(chosen, len(outputs), path, focus, notes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--args", default="", help="raw /priority arguments, e.g. '3 what next'")
    parser.add_argument("--args-file", help="read the raw arguments from a file, or '-' for stdin")
    parser.add_argument("--last", type=int, help="number of outputs (overrides the arguments)")
    parser.add_argument("--session", help="session id (${CLAUDE_SESSION_ID})")
    parser.add_argument("--transcript", help="explicit transcript .jsonl path")
    parser.add_argument("--cwd", default=os.getcwd(), help="project directory (default: cwd)")
    parser.add_argument("--full", action="store_true", help="print complete text of each output")
    try:
        options = parser.parse_args(argv)
        print(run(options))
    except SystemExit as stop:
        if stop.code not in (0, None):  # 0 is --help
            print("collect_outputs: bad options. Use the outputs in your context instead.")
    except Exception as error:  # never let /priority fail to load
        print(f"collect_outputs failed ({type(error).__name__}: {error}). "
              "Use the outputs in your context instead.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
