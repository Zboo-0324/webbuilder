from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "webbuilder" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from state_schema import (  # noqa: E402
    SCHEMA_VERSION,
    direct_apply_fingerprint,
    set_top_level_value,
    top_level_value,
)


class StateSchemaTests(unittest.TestCase):
    def test_schema_version_is_1_4(self) -> None:
        self.assertEqual(SCHEMA_VERSION, "1.4")

    def test_set_top_level_value_replaces_once_and_appends_when_missing(self) -> None:
        text = "# State\n\nstatus: active\n"
        changed = set_top_level_value(text, "status", "blocked")
        changed = set_top_level_value(changed, "stop_reason", "environment_blocked")
        self.assertEqual(top_level_value(changed, "status"), "blocked")
        self.assertEqual(top_level_value(changed, "stop_reason"), "environment_blocked")
        self.assertEqual(changed.count("status:"), 1)

    def test_direct_apply_fingerprint_changes_with_allowed_file_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            target = root / "src" / "app.py"
            target.write_text("one\n", encoding="utf-8")
            first = direct_apply_fingerprint(root, ["src/app.py"])
            target.write_text("two\n", encoding="utf-8")
            second = direct_apply_fingerprint(root, ["src/app.py"])
            self.assertNotEqual(first, second)
