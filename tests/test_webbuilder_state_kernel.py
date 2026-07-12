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
from state_transition import apply_transaction, recover_pending_transaction  # noqa: E402


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


class StateTransitionTests(unittest.TestCase):
    def test_interrupted_transaction_recovers_all_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "webbuilder"
            state_dir.mkdir()
            loop = "# Loop State\n\nstate_revision: 1\npending_transition: null\nstatus: active\n"
            requirements = "# Requirements Baseline\n\nconfirmation_status: pending\n"
            (state_dir / "loop-state.md").write_text(loop, encoding="utf-8")
            (state_dir / "requirements-baseline.md").write_text(requirements, encoding="utf-8")
            updates = {
                "loop-state.md": loop.replace("status: active", "status: blocked"),
                "requirements-baseline.md": requirements.replace("pending", "approved"),
            }
            with self.assertRaises(RuntimeError):
                apply_transaction(
                    state_dir,
                    "test-interruption",
                    updates,
                    expected_revision=1,
                    fail_after_replacements=1,
                )
            transition_id = recover_pending_transaction(state_dir)
            self.assertIsNotNone(transition_id)
            self.assertIn("status: blocked", (state_dir / "loop-state.md").read_text(encoding="utf-8"))
            self.assertIn("confirmation_status: approved", (state_dir / "requirements-baseline.md").read_text(encoding="utf-8"))
            self.assertEqual(recover_pending_transaction(state_dir), None)

    def test_transaction_rejects_stale_expected_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "webbuilder"
            state_dir.mkdir()
            loop = "# Loop State\n\nstate_revision: 2\npending_transition: null\n"
            (state_dir / "loop-state.md").write_text(loop, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "state revision changed"):
                apply_transaction(state_dir, "stale", {"loop-state.md": loop}, expected_revision=1)
