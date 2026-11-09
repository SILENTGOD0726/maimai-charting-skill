"""Self-contained unit tests; run from skill root with unittest discover."""
import importlib.util
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


if __name__ == "__main__":
    unittest.main()
