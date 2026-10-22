"""Tests for ste_check.py. Run: python3 -m unittest discover -s <scripts>/tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ste_check as ste  # noqa: E402

SWAPS = {"in order to": "to", "utilize": "use"}


def flags_for(draft, kind):
    report = ste.analyse(draft, SWAPS)
    return [f for s in report["sentences"] if s.kind == kind for f in s.flags]


class PointTyping(unittest.TestCase):
    def test_badges_set_types(self):
        draft = "1. 🔴 **Do:** Type yes.\n2. 🟠 **Decide:** Pick a name.\n3. 🟢 Saved it.\n4. 🔵 A seam is a test point.\n"
        kinds = [p.kind for p in ste.split_points(draft)]
        self.assertEqual(kinds, ["action", "decide", "done", "concept"])

    def test_later_badge_is_an_action(self):
        self.assertEqual(ste.split_points("1. 🟣 **Later:** Type yes.\n")[0].kind, "action")

    def test_point_without_badge_is_done(self):
        self.assertEqual(ste.split_points("1. Plain point here.\n")[0].kind, "done")

    def test_nested_numbers_stay_in_their_point(self):
        draft = "1. 🔴 Do these steps.\n   1. Type yes.\n   2. Press enter.\n2. 🟢 It works now.\n"
        self.assertEqual(len(ste.split_points(draft)), 2)


class Verbatim(unittest.TestCase):
    def test_code_blocks_and_inline_code_are_ignored(self):
        draft = (
            "1. 🔴 Run `! utilize everything being processed here`.\n"
            "   ```\n   this was utilized by something being long and passive\n   ```\n"
        )
        self.assertEqual(flags_for(draft, "action"), [])

    def test_tables_are_skipped(self):
        draft = "1. 🟢 Done.\n| a | it was decided in order to utilize |\n"
        self.assertEqual(flags_for(draft, "done"), [])


class Rules(unittest.TestCase):
    def test_long_action_sentence(self):
        long = " ".join(["word"] * 22) + "."
        self.assertTrue(any(f.startswith("LEN 22>20") for f in flags_for(f"1. 🔴 {long}\n", "action")))

    def test_condition_after_command(self):
        self.assertTrue(any(f.startswith("COND") for f in flags_for("1. 🔴 Run the tests if they fail.\n", "action")))

    def test_condition_first_passes(self):
        self.assertEqual(flags_for("1. 🔴 If the tests fail, run them again.\n", "action"), [])

    def test_two_instructions(self):
        self.assertIn("ONE", flags_for("1. 🔴 Open the file and then type yes.\n", "action"))

    def test_passive(self):
        self.assertTrue(any(f.startswith("PASSIVE") for f in flags_for("1. 🟢 The file was saved.\n", "done")))

    def test_open_is_not_passive(self):
        self.assertEqual(flags_for("1. 🟢 The door is open now.\n", "done"), [])

    def test_ing_form(self):
        self.assertTrue(any(f.startswith("ING") for f in flags_for("1. 🟢 The job is running now.\n", "done")))

    def test_allowed_ing_noun(self):
        self.assertEqual(flags_for("1. 🟢 Nothing changed in the settings.\n", "done"), [])

    def test_semicolon(self):
        self.assertIn("SEMI", flags_for("1. 🟢 It saved the file; it closed the app.\n", "done"))

    def test_contraction_in_action(self):
        self.assertTrue(any(f.startswith("CONTR") for f in flags_for("1. 🔴 Don't push to main.\n", "action")))

    def test_possessive_is_not_a_contraction(self):
        self.assertEqual(flags_for("1. 🔴 Open Claude's settings.\n", "action"), [])

    def test_contraction_allowed_in_concept(self):
        self.assertEqual(flags_for("1. 🔵 It's a test point.\n", "concept"), [])

    def test_abbreviation_swap(self):
        swaps = {"e.g.": "for example"}
        report = ste.analyse("1. 🟢 Use a short name, e.g. demo.\n", swaps)
        self.assertTrue(any("e.g." in f for s in report["sentences"] for f in s.flags))

    def test_word_swap(self):
        self.assertTrue(any("in order to" in f for f in flags_for("1. 🟢 We wait in order to save.\n", "done")))


class Scoring(unittest.TestCase):
    def test_targets_never_exceed_cap(self):
        self.assertTrue(all(t <= ste.CAP for t in ste.TARGETS.values()))

    def test_status(self):
        draft = "1. 🔴 Type yes.\n2. 🔴 Press enter.\n3. 🔴 Open the file and then type yes.\n"
        stats = ste.analyse(draft, SWAPS)["stats"]["action"]
        self.assertEqual(stats["sentences"], 3)
        self.assertEqual(stats["status"], "REVISE")  # 2/3 = 67% < 80%

    def test_long_point(self):
        draft = "1. 🟢 " + " ".join(f"Sentence {i} is here." for i in range(8)) + "\n"
        self.assertEqual(ste.analyse(draft, SWAPS)["long_points"][0][2], 8)

    def test_no_points_message(self):
        self.assertIn("no numbered points", ste.render(ste.analyse("just prose", SWAPS)))


if __name__ == "__main__":
    unittest.main()
