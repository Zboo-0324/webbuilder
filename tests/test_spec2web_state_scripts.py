from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = ROOT / "spec2web" / "scripts" / "init-state.py"
CHECK_SCRIPT = ROOT / "spec2web" / "scripts" / "check-state.py"
SKILL_FILE = ROOT / "spec2web" / "SKILL.md"


class Spec2WebStateScriptTests(unittest.TestCase):
    def test_init_creates_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(INIT_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            state_dir = Path(tmp) / "spec2web"
            self.assertTrue((state_dir / "project-rules.md").exists())
            self.assertTrue((state_dir / "requirements-baseline.md").exists())
            self.assertTrue((state_dir / "system-design.md").exists())
            self.assertTrue((state_dir / "task-plan.md").exists())
            self.assertTrue((state_dir / "loop-state.md").exists())
            self.assertTrue((state_dir / "validation-log.md").exists())
            self.assertTrue((state_dir / "delivery-report.md").exists())

    def test_init_does_not_overwrite_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "spec2web"
            state_dir.mkdir()
            project_rules = state_dir / "project-rules.md"
            project_rules.write_text("custom content", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(INIT_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(project_rules.read_text(encoding="utf-8"), "custom content")
            self.assertIn("exists:", result.stdout)

    def test_check_state_passes_after_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(INIT_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=True,
            )

            result = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Spec2Web state check passed.", result.stdout)

    def test_check_state_fails_without_state_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing state directory", result.stdout)

    def test_init_includes_strategy_interface_and_continuation_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(INIT_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=True,
            )

            state_dir = Path(tmp) / "spec2web"
            system_design = (state_dir / "system-design.md").read_text(encoding="utf-8")
            loop_state = (state_dir / "loop-state.md").read_text(encoding="utf-8")

            self.assertIn("## Technology Strategy", system_design)
            self.assertIn("## Interface Design Baseline", system_design)
            self.assertIn("continue ready tasks until blocked or delivered", loop_state)

    def test_check_state_requires_strategy_and_interface_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(INIT_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=True,
            )

            system_design = Path(tmp) / "spec2web" / "system-design.md"
            text = system_design.read_text(encoding="utf-8")
            system_design.write_text(
                text.replace("## Technology Strategy", "## Missing Technology Strategy"),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("system-design.md missing marker: ## Technology Strategy", result.stdout)

    def test_skill_routes_to_strategy_and_interface_references(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")

        self.assertIn("references/technology-strategy.md", text)
        self.assertIn("references/interface-design.md", text)


if __name__ == "__main__":
    unittest.main()
