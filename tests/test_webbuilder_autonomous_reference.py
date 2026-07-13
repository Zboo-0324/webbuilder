from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTONOMOUS_DIR = ROOT / "examples" / "autonomous-reference"


class AutonomousReferenceGitignoreTests(unittest.TestCase):
    """Verify that the autonomous-reference example excludes runtime artefacts."""

    def test_venv_and_sqlite_are_git_ignored(self) -> None:
        """examples/autonomous-reference/.gitignore must ignore .venv/ and db.sqlite3.

        The reference app is designed to use a project-local virtualenv and a
        SQLite database that Django creates at startup.  Both are runtime
        artefacts and must never be committed.  ``git check-ignore -v`` exits
        0 when every supplied path is covered by an ignore rule.
        """
        ignore_file = AUTONOMOUS_DIR / ".gitignore"
        self.assertTrue(
            ignore_file.exists(),
            f"Missing {ignore_file.relative_to(ROOT)}; "
            "the reference app needs a .gitignore to exclude .venv/ and db.sqlite3",
        )

        result = subprocess.run(
            [
                "git", "check-ignore", "-v",
                "examples/autonomous-reference/.venv",
                "examples/autonomous-reference/db.sqlite3",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"git check-ignore exited {result.returncode}; "
            f"stdout: {result.stdout!r}  stderr: {result.stderr!r}",
        )


if __name__ == "__main__":
    unittest.main()
