"""Installation contract tests for the WebBuilder skill.

Two compact deterministic red tests verifying:
1) SKILL.md contains all Task 6 autonomous markers.
2) Copying webbuilder/ into host skill directories and running state
   scripts against a fresh temp project succeeds.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "webbuilder" / "SKILL.md"
WEBBUILDER_DIR = ROOT / "webbuilder"

# Task 6 autonomous markers that must appear verbatim in SKILL.md.
TASK6_MARKERS = [
    "delivery_mode: guided | autonomous",
    "/webbuilder start autonomous from requirements.md",
    "--phase specification",
    "scripts/approve-contract.py",
    "scripts/check-host.py",
    "--phase initialization",
    "scripts/capture-evidence.py",
    "--phase ui",
    "scripts/transition-state.py",
    "--resume",
    "--phase delivery",
]

# Host tool directories the skill must install into.
INSTALL_TARGETS = [
    ".codex/skills/webbuilder",
    ".claude/skills/webbuilder",
    ".hermes/skills/webbuilder",
]


class SkillMarkdownMarkerTests(unittest.TestCase):
    """SKILL.md must contain every Task 6 autonomous marker verbatim."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SKILL_MD.read_text(encoding="utf-8")

    def test_skill_md_contains_all_task6_markers(self) -> None:
        """Every Task 6 marker must appear as a substring of SKILL.md."""
        missing = [m for m in TASK6_MARKERS if m not in self.text]
        self.assertEqual(
            missing, [],
            f"SKILL.md is missing these Task 6 markers: {missing}",
        )


class InstallationCopyAndRunTests(unittest.TestCase):
    """Copy webbuilder/ into host skill directories; assert scripts run."""

    def test_install_and_run_state_scripts(self) -> None:
        """For each host tool directory (.codex, .claude, .hermes):
        1. Copy webbuilder/ into a temp project's skill path.
        2. Assert SKILL.md and agents/openai.yaml exist in the copy.
        3. Run init-state.py --target <tmpdir>.
        4. Run migrate-state.py --target <tmpdir> --dry-run.
        5. Run check-state.py --target <tmpdir> --phase structure.
        All must exit 0.
        """
        for install_rel in INSTALL_TARGETS:
            with self.subTest(install=install_rel):
                self._assert_install_and_scripts(install_rel)

    # -- helpers --------------------------------------------------------------

    def _assert_install_and_scripts(self, install_rel: str) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            dest = project / install_rel

            # 1. Copy the entire webbuilder/ tree into the install path.
            shutil.copytree(str(WEBBUILDER_DIR), str(dest))

            # 2. Required files must exist in the copy.
            self.assertTrue(
                (dest / "SKILL.md").is_file(),
                f"SKILL.md missing after copy to {install_rel}",
            )
            self.assertTrue(
                (dest / "agents" / "openai.yaml").is_file(),
                f"agents/openai.yaml missing after copy to {install_rel}",
            )

            scripts_dir = dest / "scripts"

            # 3. init-state.py --target <project>
            init_result = subprocess.run(
                [sys.executable, str(scripts_dir / "init-state.py"),
                 "--target", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed for {install_rel}:\n"
                f"stdout: {init_result.stdout}\nstderr: {init_result.stderr}",
            )

            # 4. migrate-state.py --target <project> --dry-run
            migrate_result = subprocess.run(
                [sys.executable, str(scripts_dir / "migrate-state.py"),
                 "--target", str(project), "--dry-run"],
                capture_output=True, text=True,
            )
            self.assertEqual(
                migrate_result.returncode, 0,
                f"migrate-state.py --dry-run failed for {install_rel}:\n"
                f"stdout: {migrate_result.stdout}\n"
                f"stderr: {migrate_result.stderr}",
            )

            # 5. check-state.py --target <project> --phase structure
            check_result = subprocess.run(
                [sys.executable, str(scripts_dir / "check-state.py"),
                 "--target", str(project), "--phase", "structure"],
                capture_output=True, text=True,
            )
            self.assertEqual(
                check_result.returncode, 0,
                f"check-state.py --phase structure failed for {install_rel}:\n"
                f"stdout: {check_result.stdout}\n"
                f"stderr: {check_result.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
