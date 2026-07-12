from __future__ import annotations

import sys
import tempfile
import threading
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

    def test_concurrent_transactions_serialize_revision_check_and_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "webbuilder"
            state_dir.mkdir()
            loop = "# Loop State\n\nstate_revision: 1\npending_transition: null\nstatus: active\n"
            (state_dir / "loop-state.md").write_text(loop, encoding="utf-8")
            start = threading.Barrier(9)
            outcomes: list[object] = []

            def apply_concurrently(index: int) -> None:
                start.wait()
                try:
                    outcomes.append(
                        apply_transaction(
                            state_dir,
                            f"concurrent-{index}",
                            {"loop-state.md": loop.replace("active", f"blocked-{index}")},
                            expected_revision=1,
                        )
                    )
                except BaseException as exc:
                    outcomes.append(exc)

            threads = [threading.Thread(target=apply_concurrently, args=(index,)) for index in range(8)]
            for thread in threads:
                thread.start()
            start.wait()
            for thread in threads:
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())

            successes = [outcome for outcome in outcomes if isinstance(outcome, str)]
            failures = [outcome for outcome in outcomes if isinstance(outcome, BaseException)]
            self.assertEqual(len(successes), 1)
            self.assertEqual(len(failures), 7)
            self.assertTrue(all(isinstance(failure, ValueError) for failure in failures))
            self.assertEqual(recover_pending_transaction(state_dir), None)
            self.assertEqual(top_level_value((state_dir / "loop-state.md").read_text(encoding="utf-8"), "state_revision"), "2")

    def test_recovery_hashes_unchanged_crlf_files_as_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "webbuilder"
            state_dir.mkdir()
            loop = "# Loop State\r\n\r\nstate_revision: 1\r\npending_transition: null\r\n"
            requirements = "# Requirements Baseline\r\n\r\nconfirmation_status: pending\r\n"
            design = "# System Design\r\n\r\nstatus: draft\r\n"
            (state_dir / "loop-state.md").write_bytes(loop.encode("utf-8"))
            (state_dir / "requirements-baseline.md").write_bytes(requirements.encode("utf-8"))
            (state_dir / "system-design.md").write_bytes(design.encode("utf-8"))
            with self.assertRaises(RuntimeError):
                apply_transaction(
                    state_dir,
                    "crlf-interruption",
                    {
                        "requirements-baseline.md": requirements.replace("pending", "approved"),
                        "system-design.md": design.replace("draft", "ready"),
                    },
                    expected_revision=1,
                    fail_after_replacements=1,
                )
            self.assertIsNotNone(recover_pending_transaction(state_dir))
            self.assertIn("status: ready", (state_dir / "system-design.md").read_text(encoding="utf-8"))

    def test_transaction_rejects_path_traversal_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / "webbuilder"
            state_dir.mkdir()
            loop = "# Loop State\n\nstate_revision: 1\npending_transition: null\n"
            outside = root / "outside.md"
            (state_dir / "loop-state.md").write_text(loop, encoding="utf-8")
            outside.write_text("status: original\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid transaction path"):
                apply_transaction(
                    state_dir,
                    "path-traversal",
                    {"../outside.md": "status: replaced\n"},
                    expected_revision=1,
                )
            self.assertEqual(outside.read_text(encoding="utf-8"), "status: original\n")

    def test_recovery_rejects_tampered_pending_loop_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "webbuilder"
            state_dir.mkdir()
            loop = "# Loop State\n\nstate_revision: 1\npending_transition: null\n"
            requirements = "# Requirements Baseline\n\nconfirmation_status: pending\n"
            (state_dir / "loop-state.md").write_text(loop, encoding="utf-8")
            (state_dir / "requirements-baseline.md").write_text(requirements, encoding="utf-8")
            with self.assertRaises(RuntimeError):
                apply_transaction(
                    state_dir,
                    "tampered-loop",
                    {"requirements-baseline.md": requirements.replace("pending", "approved")},
                    expected_revision=1,
                    fail_after_replacements=1,
                )
            loop_path = state_dir / "loop-state.md"
            loop_path.write_text(
                set_top_level_value(loop_path.read_text(encoding="utf-8"), "state_revision", "99"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "divergent transaction file: loop-state.md"):
                recover_pending_transaction(state_dir)

    def test_transaction_normalizes_loop_aliases_and_rejects_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "webbuilder"
            state_dir.mkdir()
            loop = "# Loop State\n\nstate_revision: 1\npending_transition: null\nstatus: active\n"
            requirements = "# Requirements Baseline\n\nconfirmation_status: pending\n"
            (state_dir / "loop-state.md").write_text(loop, encoding="utf-8")
            (state_dir / "requirements-baseline.md").write_text(requirements, encoding="utf-8")
            with self.assertRaises(RuntimeError):
                apply_transaction(
                    state_dir,
                    "loop-alias",
                    {
                        "./loop-state.md": loop.replace("status: active", "status: blocked"),
                        "requirements-baseline.md": requirements.replace("pending", "approved"),
                    },
                    expected_revision=1,
                    fail_after_replacements=1,
                )
            self.assertIsNotNone(recover_pending_transaction(state_dir))
            current_loop = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            self.assertEqual(top_level_value(current_loop, "status"), "blocked")
            with self.assertRaisesRegex(ValueError, "duplicate transaction path"):
                apply_transaction(
                    state_dir,
                    "duplicate-loop-alias",
                    {"loop-state.md": current_loop, "./loop-state.md": current_loop},
                    expected_revision=2,
                )
