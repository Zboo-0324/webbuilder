from __future__ import annotations

import json
import re
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
    promote_artifacts,
    redact_text,
    sha256_bytes,
    verify_manifest,
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


class IdentifierValidationTests(unittest.TestCase):
    """run_id / subject_id must be plain path components — no escapes."""

    MALICIOUS_IDS = [
        ("../escape", "plain"),
        ("../../deep-escape", "plain"),
        ("RUN/../../escape", "contains separator"),
        ("/absolute/path", "absolute path"),
        (".", "dot"),
        ("..", "dot-dot"),
    ]

    def _make_root(self) -> Path:
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        (root / "src.txt").write_text("ok\n", encoding="utf-8")
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        return root

    def test_rejects_malicious_run_id(self) -> None:
        for bad_id, label in self.MALICIOUS_IDS:
            with self.subTest(run_id=bad_id, reason=label):
                root = self._make_root()
                with self.assertRaises(ValueError, msg=f"run_id={bad_id!r} should be rejected"):
                    capture_command_evidence(
                        root, ["echo", "hi"],
                        run_id=bad_id,
                        subject_id="TASK-001",
                        attempt=1,
                        contract_revision=1,
                        allowed_paths=["src.txt"],
                    )

    def test_rejects_malicious_subject_id(self) -> None:
        for bad_id, label in self.MALICIOUS_IDS:
            with self.subTest(subject_id=bad_id, reason=label):
                root = self._make_root()
                with self.assertRaises(ValueError, msg=f"subject_id={bad_id!r} should be rejected"):
                    capture_command_evidence(
                        root, ["echo", "hi"],
                        run_id="RUN-1",
                        subject_id=bad_id,
                        attempt=1,
                        contract_revision=1,
                        allowed_paths=["src.txt"],
                    )

    def test_no_escaped_files_created(self) -> None:
        """Malicious IDs must not create files outside .webbuilder-artifacts."""
        for bad_id, label in self.MALICIOUS_IDS:
            with self.subTest(subject_id=bad_id, reason=label):
                root = self._make_root()
                try:
                    capture_command_evidence(
                        root, ["echo", "hi"],
                        run_id="RUN-1",
                        subject_id=bad_id,
                        attempt=1,
                        contract_revision=1,
                        allowed_paths=["src.txt"],
                    )
                except ValueError:
                    pass
                artifact_root = root / ".webbuilder-artifacts"
                if artifact_root.exists():
                    for child in artifact_root.rglob("*"):
                        resolved = child.resolve()
                        self.assertTrue(
                            resolved.is_relative_to(artifact_root.resolve()),
                            f"escaped file detected: {resolved}",
                        )


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


class EvidenceVerificationTests(unittest.TestCase):
    """RED-phase tests: verify_manifest and promote_artifacts do not exist yet."""

    def capture_valid_manifest(self, root: Path, attempt: int = 1) -> Path:
        """Reusable fixture: capture a passing evidence manifest."""
        (root / "src.txt").write_text("tracked\n", encoding="utf-8")
        return capture_command_evidence(
            root,
            [sys.executable, "-c", "print('passed')"],
            run_id="RUN-1",
            subject_id="TASK-001",
            attempt=attempt,
            contract_revision=1,
            allowed_paths=["src.txt"],
        )

    def test_verify_rejects_artifact_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self.capture_valid_manifest(root)
            manifest = load_manifest(manifest_path)
            fingerprint = str(manifest["implementation_fingerprint"])
            manifest_path.with_name("command-output.txt").write_text("tampered\n", encoding="utf-8")
            errors = verify_manifest(
                manifest_path,
                project_root=root,
                expected_contract_revision=1,
                expected_fingerprint=fingerprint,
            )
            self.assertIn(
                "evidence artifact hash mismatch: .webbuilder-artifacts/RUN-1/TASK-001/1/command-output.txt",
                errors,
            )

    def test_verify_rejects_old_contract_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self.capture_valid_manifest(root)
            manifest = load_manifest(manifest_path)
            errors = verify_manifest(
                manifest_path,
                project_root=root,
                expected_contract_revision=2,
                expected_fingerprint=str(manifest["implementation_fingerprint"]),
            )
            self.assertIn("evidence contract revision does not match", errors)

    def test_verify_rejects_wrong_implementation_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self.capture_valid_manifest(root)
            errors = verify_manifest(
                manifest_path,
                project_root=root,
                expected_contract_revision=1,
                expected_fingerprint="sha256:" + "0" * 64,
            )
            self.assertIn("evidence implementation fingerprint does not match", errors)

    def test_verify_rejects_failed_command_with_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src.txt").write_text("tracked\n", encoding="utf-8")
            manifest_path = capture_command_evidence(
                root,
                [sys.executable, "-c", "import sys; print('fail'); sys.exit(1)"],
                run_id="RUN-1",
                subject_id="TASK-001",
                attempt=1,
                contract_revision=1,
                allowed_paths=["src.txt"],
            )
            manifest = load_manifest(manifest_path)
            errors = verify_manifest(
                manifest_path,
                project_root=root,
                expected_contract_revision=1,
                expected_fingerprint=str(manifest["implementation_fingerprint"]),
            )
            self.assertIn("evidence result is not passed", errors)

    def test_verify_rejects_failed_redaction_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self.capture_valid_manifest(root)
            manifest = load_manifest(manifest_path)
            manifest["redaction"]["status"] = "failed"
            write_manifest(manifest_path, manifest, project_root=root)
            errors = verify_manifest(
                manifest_path,
                project_root=root,
                expected_contract_revision=1,
                expected_fingerprint=str(manifest["implementation_fingerprint"]),
            )
            self.assertIn("evidence redaction did not pass", errors)

    def test_promote_copies_artifacts_and_rewrites_relative_paths(self) -> None:
        """promote_artifacts copies artifacts to destination and rewrites paths."""
        with tempfile.TemporaryDirectory() as worker_tmp:
            worker = Path(worker_tmp)
            manifest_path = self.capture_valid_manifest(worker)
            with tempfile.TemporaryDirectory() as main_tmp:
                main = Path(main_tmp)
                promoted_path = promote_artifacts(manifest_path, main)
                promoted = load_manifest(promoted_path)
                self.assertTrue(promoted_path.is_file())
                for artifact in promoted["artifacts"]:
                    self.assertTrue((main / artifact["path"]).is_file())
                    self.assertFalse(Path(artifact["path"]).is_absolute())
                self.assertIn("promoted_from", promoted)
                self.assertTrue(promoted["promoted_from"])
                self.assertFalse(Path(promoted["promoted_from"]).is_absolute())

    def test_verify_rejects_artifacts_list_with_non_mapping_entry(self) -> None:
        """verify_manifest must return errors (not raise) when artifacts contains a non-mapping."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self.capture_valid_manifest(root)
            manifest = load_manifest(manifest_path)
            fingerprint = str(manifest["implementation_fingerprint"])
            manifest["artifacts"] = ["not-a-mapping"]
            write_manifest(manifest_path, manifest, project_root=root)
            errors = verify_manifest(
                manifest_path,
                project_root=root,
                expected_contract_revision=1,
                expected_fingerprint=fingerprint,
            )
            self.assertIsInstance(errors, list, "verify_manifest must return a list, not raise")
            self.assertTrue(errors, "malformed artifacts entry must produce at least one error")

    def test_verify_rejects_redaction_that_is_not_a_mapping(self) -> None:
        """verify_manifest must return errors (not raise) when redaction is not a mapping."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self.capture_valid_manifest(root)
            manifest = load_manifest(manifest_path)
            fingerprint = str(manifest["implementation_fingerprint"])
            manifest["redaction"] = "not-a-mapping"
            write_manifest(manifest_path, manifest, project_root=root)
            errors = verify_manifest(
                manifest_path,
                project_root=root,
                expected_contract_revision=1,
                expected_fingerprint=fingerprint,
            )
            self.assertIsInstance(errors, list, "verify_manifest must return a list, not raise")
            self.assertIn("evidence redaction did not pass", errors)

    def test_verify_rejects_absolute_and_escaping_artifact_paths(self) -> None:
        """verify_manifest rejects absolute or directory-escaping artifact paths."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self.capture_valid_manifest(root)
            manifest = load_manifest(manifest_path)
            fingerprint = str(manifest["implementation_fingerprint"])
            for invalid_path in ("/absolute/path.txt", "../outside.txt"):
                with self.subTest(invalid_path=invalid_path):
                    original_path = manifest["artifacts"][0]["path"]
                    manifest["artifacts"][0]["path"] = invalid_path
                    write_manifest(manifest_path, manifest, project_root=root)
                    errors = verify_manifest(
                        manifest_path,
                        project_root=root,
                        expected_contract_revision=1,
                        expected_fingerprint=fingerprint,
                    )
                    path_errors = [
                        e for e in errors
                        if "path" in e.lower() and ("invalid" in e.lower() or "escape" in e.lower())
                    ]
                    self.assertTrue(
                        path_errors,
                        f"Expected path-invalid/escape error for {invalid_path!r}, got: {errors}",
                    )
                    manifest["artifacts"][0]["path"] = original_path

    def test_promotion_rejects_tampered_source_before_creating_destination(self) -> None:
        """promote_artifacts must reject a manifest whose source artifact was tampered."""
        with tempfile.TemporaryDirectory() as worker_tmp:
            worker = Path(worker_tmp)
            manifest_path = self.capture_valid_manifest(worker)
            manifest = load_manifest(manifest_path)
            run_id = str(manifest["run_id"])
            subject_id = str(manifest["subject_id"])
            attempt = int(manifest["attempt"])

            # Tamper the worker's command-output.txt so its hash no longer matches.
            tampered_file = manifest_path.with_name("command-output.txt")
            tampered_file.write_text("tampered content\n", encoding="utf-8")

            with tempfile.TemporaryDirectory() as main_tmp:
                main = Path(main_tmp)
                dest_attempt_dir = main / ".webbuilder-artifacts" / run_id / subject_id / str(attempt)
                with self.assertRaises(ValueError):
                    promote_artifacts(manifest_path, main)
                self.assertFalse(
                    dest_attempt_dir.exists(),
                    "destination attempt directory must not exist after tampered-source rejection",
                )

    def test_promotion_rejects_escaping_artifact_path_without_writing_outside_destination(self) -> None:
        """promote_artifacts must reject an artifact path that escapes destination root."""
        with tempfile.TemporaryDirectory() as worker_tmp:
            worker = Path(worker_tmp)
            manifest_path = self.capture_valid_manifest(worker)

            # Place a secret file at worker parent level so the escaped path resolves.
            secret_source = worker.parent / "escaped.txt"
            secret_source.write_bytes(b"secret data")
            secret_sha = sha256_bytes(b"secret data")

            # Rewrite the manifest artifact to point at ../escaped.txt.
            manifest = load_manifest(manifest_path)
            manifest["artifacts"] = [{
                "path": "../escaped.txt",
                "sha256": secret_sha,
                "media_type": "text/plain",
                "size": len(b"secret data"),
            }]
            write_manifest(manifest_path, manifest, project_root=worker)

            with tempfile.TemporaryDirectory() as main_tmp:
                main = Path(main_tmp)
                escape_target = main.parent / "escaped.txt"
                original_exists = escape_target.exists()
                with self.assertRaises(ValueError):
                    promote_artifacts(manifest_path, main)
                self.assertFalse(
                    escape_target.exists() and not original_exists,
                    "escaped file must not be written outside destination root",
                )

    def test_promotion_rejects_preexisting_attempt_directory_without_overwriting(self) -> None:
        """promote_artifacts must reject promotion when destination attempt dir already exists."""
        with tempfile.TemporaryDirectory() as worker_tmp:
            worker = Path(worker_tmp)
            manifest_path = self.capture_valid_manifest(worker)
            manifest = load_manifest(manifest_path)
            run_id = str(manifest["run_id"])
            subject_id = str(manifest["subject_id"])
            attempt = int(manifest["attempt"])

            with tempfile.TemporaryDirectory() as main_tmp:
                main = Path(main_tmp)
                dest_attempt_dir = main / ".webbuilder-artifacts" / run_id / subject_id / str(attempt)
                dest_attempt_dir.mkdir(parents=True, exist_ok=True)
                sentinel = dest_attempt_dir / "sentinel.txt"
                sentinel.write_text("original", encoding="utf-8")

                with self.assertRaises(ValueError):
                    promote_artifacts(manifest_path, main)
                self.assertEqual(
                    sentinel.read_text(encoding="utf-8"),
                    "original",
                    "sentinel file must not be overwritten by promote_artifacts",
                )

    def test_promote_is_idempotent_and_rejects_divergent_destination(self) -> None:
        """promote_artifacts is idempotent but rejects divergent destination files."""
        with tempfile.TemporaryDirectory() as worker_tmp:
            worker = Path(worker_tmp)
            manifest_path = self.capture_valid_manifest(worker)
            with tempfile.TemporaryDirectory() as main_tmp:
                main = Path(main_tmp)
                promoted_path1 = promote_artifacts(manifest_path, main)
                promoted_path2 = promote_artifacts(manifest_path, main)
                self.assertEqual(promoted_path1, promoted_path2)
                promoted1 = load_manifest(promoted_path1)
                promoted2 = load_manifest(promoted_path2)
                for a1, a2 in zip(promoted1["artifacts"], promoted2["artifacts"]):
                    self.assertEqual(
                        (main / a1["path"]).read_bytes(),
                        (main / a2["path"]).read_bytes(),
                    )

                # Diverge the command-output artifact in the destination.
                target_artifact = None
                for artifact in promoted2["artifacts"]:
                    if "command-output" in artifact["path"]:
                        target_artifact = artifact
                        break
                self.assertIsNotNone(target_artifact, "No command-output artifact found to diverge")
                divergent_bytes = b"divergent data"
                (main / target_artifact["path"]).write_bytes(divergent_bytes)

                with self.assertRaises(ValueError):
                    promote_artifacts(manifest_path, main)
                self.assertEqual(
                    (main / target_artifact["path"]).read_bytes(),
                    divergent_bytes,
                )

    def test_promotion_rejects_unexpected_existing_destination_content(self) -> None:
        """promote_artifacts must reject promotion when the destination attempt directory
        contains an extra file not tracked in the manifest's artifact list."""
        with tempfile.TemporaryDirectory() as worker_tmp:
            worker = Path(worker_tmp)
            manifest_path = self.capture_valid_manifest(worker)
            with tempfile.TemporaryDirectory() as main_tmp:
                main = Path(main_tmp)
                promoted_path = promote_artifacts(manifest_path, main)

                # Inject an unlisted file into the destination attempt directory.
                dest_attempt_dir = promoted_path.parent
                extra_file = dest_attempt_dir / "unexpected.txt"
                extra_file.write_text("unexpected content\n", encoding="utf-8")

                with self.assertRaises(ValueError):
                    promote_artifacts(manifest_path, main)


class EvidenceGateTests(unittest.TestCase):
    """RED-phase tests: host, initialization, and UI phases do not exist yet,
    and delivery does not verify evidence manifests."""

    CHECK_SCRIPT = SCRIPTS / "check-state.py"
    INIT_SCRIPT = SCRIPTS / "init-state.py"

    UI_CONTRACT = {
        "problem": "Build a task management UI",
        "desired_outcome": "Users manage tasks in a browser",
        "target_users": ["project managers"],
        "primary_jobs": ["create tasks", "track tasks"],
        "core_capabilities": ["task CRUD", "status tracking"],
        "non_goals": ["billing"],
        "primary_workflows": ["create task -> assign -> complete"],
        "page_navigation_summary": "Dashboard and task detail",
        "ui_direction": "compact operational UI",
        "technology_profile": "react-18 + typescript + vite",
        "public_interfaces": ["GET /api/tasks", "POST /api/tasks"],
        "data_boundary": "user-scoped task data",
        "permission_boundary": "authenticated users only",
        "delivery_assumptions": ["cloud deployment", "database migration"],
        "material_risks": ["data migration complexity"],
        "acceptance_signals": ["task CRUD works end-to-end"],
        "capabilities": {
            "ui": {"status": "required", "reason": "browser workflow"},
            "database": {"status": "required", "reason": "task data persists"},
            "authentication": {"status": "required", "reason": "authenticated users"},
            "rbac": {"status": "not_applicable", "reason": "single role MVP"},
            "audit": {"status": "not_applicable", "reason": "outside MVP scope"},
            "docker": {"status": "not_applicable", "reason": "local dev startup"},
            "accessibility": {"status": "required", "reason": "UI is required"},
            "performance": {"status": "required", "profile": "baseline"},
            "security": {"status": "required", "profile": "baseline"},
        },
        "workload_envelope": {
            "task_count": "4-6",
            "browser_flows": ["task creation"],
            "external_dependencies": [],
            "quality_gates": ["unit tests"],
            "repair_budgets": {"task": 3, "integration": 5},
            "available_concurrency": "single",
        },
    }

    API_CONTRACT = {
        "problem": "Build a REST API",
        "desired_outcome": "API serves JSON responses",
        "target_users": ["developers"],
        "primary_jobs": ["list items", "get item"],
        "core_capabilities": ["item list", "item detail"],
        "non_goals": ["UI", "billing"],
        "primary_workflows": ["GET /items", "GET /items/:id"],
        "page_navigation_summary": "not applicable — API only",
        "ui_direction": "not applicable — API only",
        "technology_profile": "fastapi + python 3.12",
        "public_interfaces": ["GET /items", "GET /items/:id"],
        "data_boundary": "public item data",
        "permission_boundary": "unauthenticated reads",
        "delivery_assumptions": ["local startup"],
        "material_risks": ["none"],
        "acceptance_signals": ["GET /items returns 200 with JSON"],
        "capabilities": {
            "ui": {"status": "not_applicable", "reason": "API only"},
            "database": {"status": "not_applicable", "reason": "in-memory store"},
            "authentication": {"status": "not_applicable", "reason": "public read-only API"},
            "rbac": {"status": "not_applicable", "reason": "no write operations"},
            "audit": {"status": "not_applicable", "reason": "public data"},
            "docker": {"status": "not_applicable", "reason": "local dev startup"},
            "accessibility": {"status": "not_applicable", "reason": "no UI"},
            "performance": {"status": "required", "profile": "baseline"},
            "security": {"status": "required", "profile": "baseline"},
        },
        "workload_envelope": {
            "task_count": "2-3",
            "browser_flows": [],
            "external_dependencies": [],
            "quality_gates": ["unit tests"],
            "repair_budgets": {"task": 3, "integration": 5},
            "available_concurrency": "single",
        },
    }

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.target = Path(self.tmp)
        self.state_dir = self.target / "webbuilder"
        result = subprocess.run(
            [sys.executable, str(self.INIT_SCRIPT), "--target", str(self.target)],
            text=True, capture_output=True, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_check(self, phase: str, **extra: str) -> subprocess.CompletedProcess:
        cmd = [
            sys.executable, str(self.CHECK_SCRIPT),
            "--target", str(self.target), "--phase", phase,
        ]
        for key, value in extra.items():
            cmd.extend([f"--{key.replace('_', '-')}", str(value)])
        return subprocess.run(cmd, text=True, capture_output=True, check=False)

    def _write_contract(self, material: dict) -> None:
        contract_json = json.dumps(material, ensure_ascii=False, indent=2)
        requirements = (
            "# Requirements Baseline\n\n## Status\n\n"
            "status: confirmed\nconfirmation_status: approved\n"
            "contract_revision: 1\napproved_contract_revision: 1\n"
            "approval_digest: null\napproval_scope: requirements_design_stack_ui_execution\n"
            "approval_evidence: user-message-42\napproved_by: user\n"
            "approved_at: 2026-07-13\ndiscovery_method: inferred_contract\n\n"
            "## User Discovery\n\ndiscovery_status: confirmed\n\n"
            "### AI Working Hypothesis\n\n- Users need a task management system\n\n"
            "### Questions Asked\n\n- What is the primary use case?\n\n"
            "### User Decisions\n\n- Use React for frontend\n\n"
            "## Solution Contract\n\n```json contract-material\n"
            f"{contract_json}\n```\n\n"
            "## First-Principles Analysis\n\n"
            "### Core Outcome\n\n- Users can manage tasks efficiently\n\n"
            "### Hard Constraints and Invariants\n\n- Data must persist across sessions\n\n"
            "### Assumptions and Evidence\n\n- Users have modern browsers\n\n"
            "## Open Questions\n\n- None.\n\n"
            "## Confirmed Requirements\n\n"
            "| ID | Requirement | Priority | Acceptance Signal |\n"
            "|---|---|---|---|\n"
            "| REQ-001 | Task CRUD operations | Must | Create, read, update, delete tasks |\n"
        )
        (self.state_dir / "requirements-baseline.md").write_text(
            requirements, encoding="utf-8", newline="\n"
        )

    def _write_loop_state(self, **overrides: str) -> None:
        path = self.state_dir / "loop-state.md"
        text = path.read_text(encoding="utf-8")
        for key, value in overrides.items():
            text = re.sub(
                rf"(?m)^{re.escape(key)}:\s*.*$",
                f"{key}: {value}",
                text,
            )
        path.write_text(text, encoding="utf-8")

    def _make_execution_ready(self) -> None:
        for filename, pairs in {
            "project-rules.md": [("status: draft", "status: ready")],
            "system-design.md": [
                ("status: draft", "status: ready"),
                ("not recorded", "not applicable"),
                ("None recorded yet.", "None required."),
                ("Replace with project-specific tradeoffs.", "No migration cost."),
            ],
            "task-plan.md": [
                ("status: draft", "status: ready"),
                ("Replace with first task title", "Build the thing"),
                ("Replace with one concrete outcome.", "Thing works."),
                ("replace/with/path", "src/app.py"),
                ("replace with expected output", "test passes"),
                ("replace with exact command or manual check", "python -m unittest"),
                (
                    "replace with worker-observable condition for submitting the task",
                    "implementation is complete",
                ),
                (
                    "replace with Orchestrator check required before accepting or merging",
                    "tests pass and diff stays in allowed paths",
                ),
                ("risk_level: unclassified", "risk_level: low"),
                ("not recorded", "localized task change"),
            ],
        }.items():
            path = self.state_dir / filename
            text = path.read_text(encoding="utf-8")
            for old, new in pairs:
                text = text.replace(old, new)
            path.write_text(text, encoding="utf-8")

    def _write_host_capabilities(self, capabilities: dict) -> None:
        block = "## Host Capabilities\n\n```json\n"
        block += json.dumps(capabilities, ensure_ascii=False, indent=2, sort_keys=True)
        block += "\n```\n"
        path = self.state_dir / "loop-state.md"
        text = path.read_text(encoding="utf-8")
        section_pattern = re.compile(r"(?ms)^## Host Capabilities\s*\n.*?(?=^## |\Z)")
        if section_pattern.search(text):
            text = section_pattern.sub(block, text)
        else:
            text = text.rstrip() + "\n\n" + block
        path.write_text(text, encoding="utf-8")

    def _set_task_status(self, status: str) -> None:
        path = self.state_dir / "task-plan.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace("- status: pending", f"- status: {status}")
        path.write_text(text, encoding="utf-8")

    def _write_validation_log(self, entry: str) -> None:
        (self.state_dir / "validation-log.md").write_text(
            "# Validation Log\n\n## Entries\n\n" + entry,
            encoding="utf-8",
        )

    _DELIVERY_CORE_DOMAINS = ("functional", "security", "performance", "delivery-smoke")
    _DELIVERY_UI_DOMAINS = ("ui", "accessibility")

    def _applicable_delivery_domains(self, contract: dict) -> list[str]:
        """Core four plus ui/accessibility when the contract marks UI as required."""
        domains = list(self._DELIVERY_CORE_DOMAINS)
        caps = contract.get("capabilities", {})
        if isinstance(caps, dict):
            ui_cap = caps.get("ui")
            if isinstance(ui_cap, dict) and ui_cap.get("status") == "required":
                domains.extend(self._DELIVERY_UI_DOMAINS)
        return domains

    def _append_validation_entries(self, entries: str) -> None:
        """Append validation entries to the existing validation log."""
        path = self.state_dir / "validation-log.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.rstrip() + "\n\n" + entries + "\n", encoding="utf-8")

    def _write_domain_manifests(
        self, contract: dict, domains: list[str] | None = None,
    ) -> dict[str, Path]:
        """Capture evidence manifests and write PROJECT/<domain> validation-log entries."""
        if domains is None:
            domains = self._applicable_delivery_domains(contract)
        src = self.target / "src" / "app.py"
        src.parent.mkdir(parents=True, exist_ok=True)
        if not src.exists():
            src.write_text("# app\n", encoding="utf-8")

        manifests: dict[str, Path] = {}
        entries: list[str] = []
        for domain in domains:
            manifest_path = capture_command_evidence(
                self.target,
                [sys.executable, "-c", "print('ok')"],
                run_id="DELIVERY",
                subject_id=domain,
                attempt=1,
                contract_revision=1,
                allowed_paths=["src/app.py"],
            )
            rel_path = manifest_path.relative_to(self.target).as_posix()
            manifests[domain] = manifest_path
            entries.append(
                f"### PROJECT / {domain}\n\n"
                f"- gate: {domain}\n"
                f"- artifact_manifest: {rel_path}\n"
            )
        self._append_validation_entries("\n".join(entries))
        return manifests

    def _make_delivery_ready(self, *, contract: dict | None = None, create_manifests: bool = True) -> None:
        self._set_task_status("complete")
        self._write_loop_state(status="delivered", current_phase="delivery")
        self._write_validation_log(
            "### TASK-001 / acceptance\n\n"
            "- gate: acceptance\n- task_status: submitted_for_acceptance\n"
            "- submission_commit: direct_apply\n- developer_identity: developer\n"
            "- tester_identity: tester\n- tester_result: passed\n"
            "- reviewer_identity: reviewer\n- reviewer_result: approved\n"
            "- adversarial_cases_expected: not_applicable\n"
            "- adversarial_cases_passed: not_applicable\n"
            "- disagreement_status: none\n- orchestrator_decision: accepted\n"
            "- residual_risk: none\n\n"
            "### TASK-001 / integration\n\n"
            "- gate: integration\n- integration_strategy: squash_merge\n"
            "- integration_commit: abc1234\n"
            "- main_workspace_verification: passed\n"
            "- verification_evidence: python -m unittest\n"
            "- final_task_status: complete\n",
        )
        (self.state_dir / "delivery-report.md").write_text(
            "# Delivery Report\n\nstatus: complete\n\n## Completed\n\n"
            "- REQ-001: task CRUD.\n\n## Validation\n\n- Tests passed.\n\n"
            "## Run Instructions\n\n- python app.py\n\n## Known Risks\n\n- None.\n\n"
            "## Not Completed\n\n- None.\n",
            encoding="utf-8",
        )
        if create_manifests:
            self._write_domain_manifests(contract or self.UI_CONTRACT)

    def test_ui_required_contract_plus_browser_unavailable_fails_host_phase(self) -> None:
        self._write_contract(self.UI_CONTRACT)
        self._make_execution_ready()
        self._write_host_capabilities({
            "browser": {"status": "unavailable", "evidence": "host report: not installed"},
            "git": {"status": "available", "evidence": "git --version"},
        })

        result = self._run_check("host")

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("browser", (result.stdout + result.stderr).lower())

    def test_database_not_applicable_needs_no_evidence(self) -> None:
        """When database is not_applicable, initialization must succeed
        without database evidence — only required capabilities need evidence."""
        self._write_contract(self.API_CONTRACT)
        self._make_execution_ready()
        # Provide evidence for every *required* capability so the only
        # potential blocker is database, which is not_applicable.
        self._write_host_capabilities({
            "git": {"status": "available", "evidence": "git --version"},
            "security": {"status": "available", "evidence": "bandit ok"},
            "performance": {"status": "available", "evidence": "bench ok"},
        })

        result = self._run_check("initialization")

        combined = result.stdout + result.stderr
        self.assertEqual(
            result.returncode, 0,
            f"initialization should succeed when database is not_applicable; "
            f"output: {combined}",
        )

    def test_docker_not_applicable_needs_no_evidence(self) -> None:
        """When docker is not_applicable, initialization must succeed
        without docker evidence — only required capabilities need evidence."""
        self._write_contract(self.API_CONTRACT)
        self._make_execution_ready()
        # Provide evidence for every *required* capability so the only
        # potential blocker is docker, which is not_applicable.
        self._write_host_capabilities({
            "git": {"status": "available", "evidence": "git --version"},
            "security": {"status": "available", "evidence": "bandit ok"},
            "performance": {"status": "available", "evidence": "bench ok"},
        })

        result = self._run_check("initialization")

        combined = result.stdout + result.stderr
        self.assertEqual(
            result.returncode, 0,
            f"initialization should succeed when docker is not_applicable; "
            f"output: {combined}",
        )

    def test_ui_required_task_missing_manifest_fails_ui_phase(self) -> None:
        self._write_contract(self.UI_CONTRACT)
        self._make_execution_ready()
        self._set_task_status("complete")
        self._write_validation_log(
            "### TASK-001 / acceptance\n\n"
            "- gate: acceptance\n- task_status: submitted_for_acceptance\n"
            "- submission_commit: direct_apply\n- developer_identity: developer\n"
            "- tester_identity: tester\n- tester_result: passed\n"
            "- reviewer_identity: reviewer\n- reviewer_result: approved\n"
            "- adversarial_cases_expected: not_applicable\n"
            "- adversarial_cases_passed: not_applicable\n"
            "- disagreement_status: none\n- orchestrator_decision: accepted\n"
            "- residual_risk: none\n",
        )

        result = self._run_check("ui", task="TASK-001")

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("manifest", (result.stdout + result.stderr).lower())

    def test_handwritten_passed_delivery_text_without_manifest_fails(self) -> None:
        self._write_contract(self.UI_CONTRACT)
        self._make_execution_ready()
        self._make_delivery_ready(create_manifests=False)

        result = self._run_check("delivery")

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("manifest", (result.stdout + result.stderr).lower())

    def test_api_only_delivery_passes_without_ui_accessibility_manifests(self) -> None:
        self._write_contract(self.API_CONTRACT)
        self._make_execution_ready()
        self._make_delivery_ready(contract=self.API_CONTRACT)

        result = self._run_check("delivery")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_delivery_passes_with_valid_evidence_manifests(self) -> None:
        self._write_contract(self.UI_CONTRACT)
        self._make_execution_ready()
        self._make_delivery_ready(contract=self.UI_CONTRACT)

        result = self._run_check("delivery")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_delivery_rejects_stale_contract_revision_manifest(self) -> None:
        self._write_contract(self.UI_CONTRACT)
        self._make_execution_ready()
        self._make_delivery_ready(contract=self.UI_CONTRACT)

        # Tamper one manifest's contract_revision.
        manifest_path = self.target / ".webbuilder-artifacts" / "DELIVERY" / "functional" / "1" / "manifest.json"
        manifest = load_manifest(manifest_path)
        manifest["contract_revision"] = 999
        write_manifest(manifest_path, manifest, project_root=self.target)

        result = self._run_check("delivery")

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("contract revision", (result.stdout + result.stderr).lower())

    def test_delivery_rejects_tampered_evidence_manifest(self) -> None:
        self._write_contract(self.UI_CONTRACT)
        self._make_execution_ready()
        self._make_delivery_ready(contract=self.UI_CONTRACT)

        # Tamper the artifact file so its hash no longer matches the manifest.
        output_file = self.target / ".webbuilder-artifacts" / "DELIVERY" / "functional" / "1" / "command-output.txt"
        output_file.write_text("tampered content\n", encoding="utf-8")

        result = self._run_check("delivery")

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("hash mismatch", (result.stdout + result.stderr).lower())

    def test_delivery_rejects_missing_manifest_file(self) -> None:
        self._write_contract(self.UI_CONTRACT)
        self._make_execution_ready()
        self._make_delivery_ready(contract=self.UI_CONTRACT)

        # Delete one manifest file while keeping the validation-log reference.
        manifest_path = self.target / ".webbuilder-artifacts" / "DELIVERY" / "functional" / "1" / "manifest.json"
        manifest_path.unlink()

        result = self._run_check("delivery")

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("manifest", (result.stdout + result.stderr).lower())

    def test_ui_required_delivery_needs_ui_accessibility_manifests(self) -> None:
        self._write_contract(self.UI_CONTRACT)
        self._make_execution_ready()
        self._make_delivery_ready(create_manifests=False)
        # Create manifests for only the core four domains — omit ui/accessibility.
        self._write_domain_manifests(self.UI_CONTRACT, domains=list(self._DELIVERY_CORE_DOMAINS))

        result = self._run_check("delivery")

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        combined = result.stdout + result.stderr
        self.assertTrue(
            any(f"PROJECT / {d}" in combined for d in ("ui", "accessibility")),
            f"expected ui/accessibility domain error in: {combined}",
        )


if __name__ == "__main__":
    unittest.main()
