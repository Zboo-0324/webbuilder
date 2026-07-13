from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "webbuilder" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from evidence_core import (  # noqa: E402
    MANIFEST_SCHEMA_VERSION,
    capture_command_evidence,
    git_fingerprint,
    load_manifest,
    redact_text,
    write_manifest,
)


class EvidenceCoreTests(unittest.TestCase):
    def test_redacts_authorization_cookie_and_secret_assignment(self) -> None:
        raw = "Authorization: Bearer abc123\nCookie: sid=secret\nAPI_KEY=hunter2\n"
        redacted, replacements = redact_text(raw, explicit_secrets=["hunter2"])
        self.assertNotIn("abc123", redacted)
        self.assertNotIn("sid=secret", redacted)
        self.assertNotIn("hunter2", redacted)
        self.assertGreaterEqual(replacements, 3)

    def test_manifest_round_trip_uses_project_relative_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {
                "schema_version": MANIFEST_SCHEMA_VERSION,
                "record_id": "EV-1",
                "run_id": "RUN-1",
                "subject_id": "TASK-001",
                "attempt": 1,
                "contract_revision": 1,
                "implementation_fingerprint": "sha256:" + "a" * 64,
                "command": ["python", "-m", "unittest"],
                "cwd": ".",
                "exit_code": 0,
                "tool_versions": {"python": "3.12"},
                "artifacts": [],
                "redaction": {"status": "passed", "replacements": 0},
                "result": "passed",
                "supersedes_record_id": None,
            }
            path = root / ".webbuilder-artifacts" / "RUN-1" / "TASK-001" / "1" / "manifest.json"
            write_manifest(path, manifest, project_root=root)
            self.assertEqual(load_manifest(path), manifest)
            self.assertNotIn(str(root), path.read_text(encoding="utf-8"))

    def test_git_fingerprint_uses_canonical_sha256_prefix_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "a.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "add", "a.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)
            fp = git_fingerprint(root)
            self.assertTrue(
                fp.startswith("sha256:"),
                f"fingerprint should start with 'sha256:' but got: {fp[:20]}...",
            )
            self.assertEqual(len(fp), len("sha256:") + 64)

    def test_git_fingerprint_includes_commit_and_dirty_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "a.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "add", "a.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)
            clean = git_fingerprint(root)
            (root / "a.txt").write_text("two\n", encoding="utf-8")
            dirty = git_fingerprint(root)
            self.assertNotEqual(clean, dirty)


class CommandCaptureTests(unittest.TestCase):
    def test_failed_command_records_output_and_failed_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src.txt"
            source.write_text("tracked\n", encoding="utf-8")
            path = capture_command_evidence(
                root,
                [sys.executable, "-c", "import sys; print('boom'); sys.exit(7)"],
                run_id="RUN-1",
                subject_id="TASK-001",
                attempt=1,
                contract_revision=1,
                allowed_paths=["src.txt"],
            )
            manifest = load_manifest(path)
            self.assertEqual(manifest["exit_code"], 7)
            self.assertEqual(manifest["result"], "failed")
            output = path.with_name("command-output.txt").read_text(encoding="utf-8")
            self.assertIn("boom", output)

    def test_capture_redacts_explicit_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src.txt").write_text("tracked\n", encoding="utf-8")
            path = capture_command_evidence(
                root,
                [sys.executable, "-c", "print('token-value')"],
                run_id="RUN-1",
                subject_id="PROJECT",
                attempt=1,
                contract_revision=1,
                allowed_paths=["src.txt"],
                explicit_secrets=["token-value"],
            )
            self.assertNotIn("token-value", path.with_name("command-output.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
