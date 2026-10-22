"""Tests for collect_outputs.py. Run: python3 -m unittest discover -s <scripts>/tests"""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "transcript.jsonl"
sys.path.insert(0, str(SCRIPTS))

import collect_outputs as co  # noqa: E402


def outputs():
    return co.finished_outputs(co.build_turns(co.load_entries(FIXTURE)))


class TurnBuilding(unittest.TestCase):
    def test_two_finished_outputs(self):
        self.assertEqual(len(outputs()), 2)

    def test_tool_result_continues_the_turn(self):
        first = outputs()[0].text
        self.assertIn("Setting up.", first)
        self.assertIn("## Done", first)

    def test_sidechain_text_is_ignored(self):
        self.assertTrue(all("SIDECHAIN" not in o.text for o in outputs()))

    def test_running_turn_is_excluded(self):
        self.assertTrue(all("Collecting outputs" not in o.text for o in outputs()))

    def test_injected_skill_body_does_not_start_a_turn(self):
        second = outputs()[1]
        self.assertEqual((second.trigger.get("origin") or {}).get("kind"), "peer")

    def test_bad_json_line_is_skipped(self):
        self.assertTrue(all(isinstance(e, dict) for e in co.load_entries(FIXTURE)))


class Scanning(unittest.TestCase):
    def test_actions_found(self):
        actions = "\n".join(co.scan_output(outputs()[0].text)["actions"])
        self.assertIn("! uv sync", actions)
        self.assertIn("/mattpocock-skills:to-tickets", actions)
        self.assertIn("! podman ps", actions)
        self.assertIn("cd ~/demo && claude", actions)

    def test_question_with_recommendation(self):
        questions = co.scan_output(outputs()[1].text)["questions"]
        self.assertTrue(any("Q2" in q and "recommended: Yes, demo." in q for q in questions))

    def test_heading_is_not_an_instruction(self):
        actions = co.scan_output("## The only commands you need to type\nplain text")["actions"]
        self.assertEqual(actions, [])


class Triggers(unittest.TestCase):
    def test_command_trigger(self):
        entry = {"message": {"content": "<command-name>/priority</command-name><command-args>2</command-args>"}}
        self.assertEqual(co.describe_trigger(entry), "you ran /priority 2")

    def test_task_notification_trigger(self):
        entry = {"origin": {"kind": "task-notification"},
                 "message": {"content": "<task-notification><summary>Agent finished</summary></task-notification>"}}
        self.assertEqual(co.describe_trigger(entry), "background event: Agent finished")

    def test_peer_trigger(self):
        self.assertEqual(co.describe_trigger({"origin": {"kind": "peer"}, "message": {"content": "x"}}),
                         "a subagent reported back")


class Scope(unittest.TestCase):
    def test_number_and_focus(self):
        self.assertEqual(co.parse_scope("3 what next"), (3, "what next", None))

    def test_default_is_one(self):
        self.assertEqual(co.parse_scope(""), (1, "", None))

    def test_focus_only(self):
        self.assertEqual(co.parse_scope("the tickets"), (1, "the tickets", None))

    def test_unsubstituted_placeholder_is_empty(self):
        self.assertEqual(co.parse_scope("$ARGUMENTS"), (1, "", None))

    def test_zero_falls_back_to_one(self):
        count, focus, note = co.parse_scope("0")
        self.assertEqual((count, focus), (1, ""))
        self.assertIsNotNone(note)


class Main(unittest.TestCase):
    def run_main(self, *argv):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = co.main(list(argv))
        return code, buffer.getvalue()

    def test_more_than_available(self):
        code, text = self.run_main("--transcript", str(FIXTURE), "--args", "5")
        self.assertEqual(code, 0)
        self.assertIn("only 2 exist", text)

    def test_full_mode_prints_text(self):
        code, text = self.run_main("--transcript", str(FIXTURE), "--full")
        self.assertEqual(code, 0)
        self.assertIn("Got the report.", text)
        self.assertNotIn("Setting up.", text)  # default N is 1: only the newest output

    def test_missing_transcript_still_exits_zero(self):
        code, text = self.run_main("--transcript", "/nonexistent/file.jsonl")
        self.assertEqual(code, 0)  # a non-zero exit would cancel /priority
        self.assertIn("No transcript found", text)

    def test_args_from_stdin_heredoc(self):
        old_stdin = sys.stdin
        sys.stdin = io.StringIO('2 what\'s "next $(echo PWNED)\n')
        try:
            code, text = self.run_main("--transcript", str(FIXTURE), "--args-file", "-")
        finally:
            sys.stdin = old_stdin
        self.assertEqual(code, 0)
        self.assertIn("the last 2 of 2", text)
        self.assertIn('what\'s "next $(echo PWNED)', text)  # kept literally, never run

    def test_bad_option_still_exits_zero(self):
        code, text = self.run_main("--last", "abc")
        self.assertEqual(code, 0)
        self.assertIn("bad options", text)

    def test_unrecognised_format(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as handle:
            handle.write('{"kind": "something-new"}\n')
        try:
            code, text = self.run_main("--transcript", handle.name)
        finally:
            os.unlink(handle.name)
        self.assertEqual(code, 0)
        self.assertIn("not recognised", text)


class Locating(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.old = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = str(self.home)

    def tearDown(self):
        if self.old is None:
            os.environ.pop("CLAUDE_CONFIG_DIR", None)
        else:
            os.environ["CLAUDE_CONFIG_DIR"] = self.old
        shutil.rmtree(self.home)

    def place(self, folder, name):
        target = self.home / "projects" / folder
        target.mkdir(parents=True)
        shutil.copy(FIXTURE, target / name)
        return target / name

    def test_by_session_id(self):
        path = self.place("-somewhere-else", "abc-123.jsonl")
        self.assertEqual(co.find_transcript("abc-123", None, "/tmp/other"), path)

    def test_unsubstituted_variable_falls_back_to_cwd(self):
        path = self.place("-tmp-demo-project", "x.jsonl")
        self.assertEqual(co.find_transcript("${CLAUDE_SESSION_ID}", None, "/tmp/demo-project"), path)

    def test_by_recorded_cwd(self):
        path = self.place("renamed-folder", "y.jsonl")
        self.assertEqual(co.find_transcript(None, None, "/tmp/demo-project"), path)


if __name__ == "__main__":
    unittest.main()
