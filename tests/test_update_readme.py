import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_readme.py"
SPEC = importlib.util.spec_from_file_location("update_readme", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ReplaceSectionTests(unittest.TestCase):
    def test_replaces_only_the_requested_marked_section(self):
        original = (
            "# Profile\n"
            "<!--START:stats-->\nold stats\n<!--END:stats-->\n"
            "Keep this paragraph.\n"
        )

        updated = MODULE.replace(original, "stats", "**42** repositories")

        self.assertIn("<!--START:stats-->\n**42** repositories\n<!--END:stats-->", updated)
        self.assertIn("Keep this paragraph.", updated)
        self.assertNotIn("old stats", updated)

    def test_missing_markers_raise_a_clear_error(self):
        with self.assertRaisesRegex(RuntimeError, "markers for 'languages' not found"):
            MODULE.replace("# Profile\n", "languages", "generated")


if __name__ == "__main__":
    unittest.main()
