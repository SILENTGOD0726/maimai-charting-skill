"""Self-contained unit tests; run from skill root with unittest discover."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "quick_lint.py"
spec = importlib.util.spec_from_file_location("quick_lint", MODULE)
linter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linter)


class LintTest(unittest.TestCase):
    def test_valid_basic_chart(self):
        self.assertEqual([], linter.lint("(120){4}1,2h[4:1],C,1-4[8:3],E"))

    def test_valid_maidata(self):
        self.assertEqual([], linter.lint("&title=Test\n&inote_5=\n(120){4}1,2,3,4,E\n"))

    def test_missing_terminator(self):
        self.assertTrue(any("missing final E" in s for s in linter.lint("(120){4}1,2,")))

    def test_unbalanced(self):
        self.assertTrue(any("unclosed" in s for s in linter.lint("(120){4}1h[4:1,E")))

    def test_bad_bpm(self):
        self.assertTrue(any("invalid BPM" in s for s in linter.lint("(0){4}1,E")))

    def test_bad_grid(self):
        self.assertTrue(any("invalid timing grid" in s for s in linter.lint("(120){0}1,E")))

    def test_advanced_duration_not_rejected(self):
        self.assertFalse(any("ERROR" in s for s in linter.lint("(120){4}1-4[3##160#8:3],E")))

    def test_missing_charts(self):
        self.assertTrue(any("no &inote" in s for s in linter.lint("&title=Demo\n")))

    def test_zero_slide_wait(self):
        self.assertEqual([], linter.lint("(120){4}1-4[0##8:1],,,,E"))

    def test_invalid_duration_roles(self):
        for signature in ["-4:1", "4:-1", "0:1", "4:0", "-1##8:1", "0##0:1", "0##8:-1", "0#8:1", "#-1", "#0"]:
            with self.subTest(signature=signature):
                self.assertTrue(any("ERROR" in s for s in linter.lint(f"(120){{4}}1-4[{signature}],,,,E")))

    def test_supported_duration_forms(self):
        for signature in ["4:1", "#1.5", "150#2:1", "160#2", "3##1.5", "3##8:3", "0##160#8:3"]:
            with self.subTest(signature=signature):
                self.assertEqual([], linter.lint(f"(120){{4}}1-4[{signature}],,,,E"))

    def test_unknown_duration_warns(self):
        self.assertTrue(any("WARN unrecognized duration" in s for s in linter.lint("(120){4}1h[custom],,,,E")))

    def test_bpm_must_precede_first_input(self):
        self.assertTrue(any("initial BPM" in s for s in linter.lint("1,2,(120){4}3,E")))

    def test_relative_grid_without_bpm_warns(self):
        self.assertTrue(any("before BPM" in s for s in linter.lint("{4}1,2,E")))

    def test_absolute_seconds_grid_needs_no_bpm_for_taps(self):
        self.assertEqual([], linter.lint("{#0.35}1,2,E"))

    def test_e_after_timing_prefix_is_not_ignored(self):
        self.assertTrue(any("after E" in s for s in linter.lint("(120){4}E,1,E")))

    def test_timing_after_e_is_reported(self):
        self.assertTrue(any("after E" in s for s in linter.lint("(120){4}1,E,(160)")))

    def test_e_touch_is_not_terminator(self):
        self.assertEqual([], linter.lint("(120){4}E1,E8,E"))
        self.assertTrue(any("missing final E" in s for s in linter.lint("(120){4}E1,E8")))

    def test_finite_timing_values(self):
        for value in ["nan", "inf", "9" * 400]:
            with self.subTest(value=value[:10]):
                self.assertTrue(any("ERROR invalid BPM" in s for s in linter.lint(f"({value}){{4}}1,E")))

    def test_duplicate_fields_and_bom(self):
        self.assertTrue(any("duplicate field" in s for s in linter.lint("&title=A\n&title=B\n&inote_5=(120){4}1,E")))
        self.assertEqual([], linter.lint("\ufeff&inote_5=(120){4}1,E"))

    def test_multiple_charts_have_independent_initial_timing(self):
        problems = linter.lint("&inote_4=(120){4}1,E\n&inote_5={4}1,E")
        self.assertTrue(any(s.startswith("inote_5:") and "before BPM" in s for s in problems))

    def test_demo_tail_covers_its_last_slide(self):
        root = MODULE.parents[1]
        text = (root / "assets" / "maidata-template.txt").read_text(encoding="utf-8-sig")
        body = text.split("&inote_5=", 1)[1]
        self.assertIn("(120){4}", body)
        cells = body.split(',')
        index = next(i for i, cell in enumerate(cells) if "1-4[8:3]" in cell)
        # This authored fixture has a constant 120-BPM quarter grid.
        slide_end = index * 0.5 + 0.5 + 0.75
        chart_end = body.count(',') * 0.5
        self.assertGreaterEqual(chart_end, slide_end, "E cuts off the demonstration slide")
        self.assertEqual([], linter.lint(text))

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory(dir=MODULE.parents[1]) as directory:
            path = Path(directory) / "maidata.txt"
            for body, code in [("(120){4}1,E", 0), ("{4}1,E", 0), ("(120){4}1,", 1)]:
                with self.subTest(body=body):
                    path.write_text(body, encoding="utf-8")
                    result = subprocess.run([sys.executable, str(MODULE), str(path)], capture_output=True)
                    self.assertEqual(code, result.returncode, result.stdout)
            path = Path(directory) / "missing.txt"
            result = subprocess.run([sys.executable, str(MODULE), str(path)], capture_output=True)
            self.assertEqual(2, result.returncode)


if __name__ == "__main__":
    unittest.main()

