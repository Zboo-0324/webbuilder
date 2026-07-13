# WebBuilder Evidence and Host Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace agent-authored pass claims with deterministic evidence manifests and enforce host-capability, initialization, UI, and final-delivery gates without introducing a background service.

**Architecture:** `evidence_core.py` captures command output and artifact metadata under `.webbuilder-artifacts/<run>/<subject>/<attempt>/`, redacts secrets, fingerprints the implementation, verifies hashes and supersession, and promotes accepted worktree artifacts. `host_capabilities.py` combines local probes with explicit host-reported capabilities and converts missing requirements into an equivalent downgrade or `environment_blocked`.

**Tech Stack:** Python 3.12+ standard library (`subprocess`, `json`, `hashlib`, `shutil`, `secrets`, `re`), project-relative artifact paths, Markdown evidence indexes, `unittest`.

## Global Constraints

- Plans 1 and 2 exit gates must be complete and green.
- Artifact capture defaults to `.webbuilder-artifacts/`, which remains ignored by Git.
- Manifests use project-relative paths and SHA-256; local absolute paths never enter delivery reports.
- Redact cookies, authorization headers, common secret assignments, and values explicitly supplied through the redaction API.
- Evidence must match the current approved contract revision and current Git/direct-apply implementation fingerprint.
- Latest valid non-superseded attempt wins; old, failed, stale, missing, divergent, or tampered evidence fails closed.
- Workers may capture worktree-local evidence, but accepted evidence must be promoted before worktree cleanup.
- Host inspection cannot invent browser/subagent/session capabilities; these require an explicit host report with evidence.
- Missing required capabilities block; optional missing capabilities may downgrade only when the same gates remain enforceable.

---

### Task 1: Define Evidence Manifests, Redaction, and Fingerprints

**Files:**
- Create: `webbuilder/scripts/evidence_core.py`
- Create: `tests/test_webbuilder_evidence.py`

**Interfaces:**
- Consumes: `state_schema.sha256_bytes()` and `direct_apply_fingerprint()`.
- Produces: manifest schema, `redact_text()`, `git_fingerprint()`, `write_manifest()`, and `load_manifest()`.

- [ ] **Step 1: Write failing manifest and redaction tests**

Create `tests/test_webbuilder_evidence.py`:

```python
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
```

- [ ] **Step 2: Run tests and observe the missing module**

```powershell
python -m unittest tests.test_webbuilder_evidence.EvidenceCoreTests -v
```

Expected: import failure for `evidence_core`.

- [ ] **Step 3: Implement manifest persistence and redaction**

Create `evidence_core.py` with:

```python
MANIFEST_SCHEMA_VERSION = "1.0"
SECRET_PATTERNS = (
    re.compile(r"(?im)^(authorization:\s*bearer\s+).+$"),
    re.compile(r"(?im)^(cookie:\s*).+$"),
    re.compile(r"(?im)^([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY)[A-Z0-9_]*=).+$"),
)


def redact_text(text: str, explicit_secrets: Iterable[str] = ()) -> tuple[str, int]:
    redacted = text
    replacements = 0
    for pattern in SECRET_PATTERNS:
        redacted, count = pattern.subn(r"\1[REDACTED]", redacted)
        replacements += count
    for secret in sorted({value for value in explicit_secrets if value}, key=len, reverse=True):
        count = redacted.count(secret)
        redacted = redacted.replace(secret, "[REDACTED]")
        replacements += count
    return redacted, replacements


def write_manifest(path: Path, manifest: dict[str, object], *, project_root: Path) -> None:
    path.resolve().relative_to(project_root.resolve())
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if str(project_root.resolve()) in serialized:
        raise ValueError("manifest contains project absolute path")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8", newline="\n")


def load_manifest(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported evidence manifest")
    return value
```

Implement `git_fingerprint()` as SHA-256 over JSON containing `git rev-parse HEAD` and `git status --porcelain=v1`; use `direct_apply_fingerprint()` only when the project is not Git-backed or the task explicitly uses `direct_apply`.

- [ ] **Step 4: Verify and commit**

```powershell
python -m unittest tests.test_webbuilder_evidence.EvidenceCoreTests -v
python -m unittest discover -s tests -v
git add webbuilder/scripts/evidence_core.py tests/test_webbuilder_evidence.py
git commit -m "feat: add WebBuilder evidence manifest core"
```

---

### Task 2: Capture Command Evidence Deterministically

**Files:**
- Modify: `webbuilder/scripts/evidence_core.py`
- Create: `webbuilder/scripts/capture-evidence.py`
- Modify: `tests/test_webbuilder_evidence.py`

**Interfaces:**
- Consumes: manifest/redaction/fingerprint functions.
- Produces: `capture_command_evidence()` and a CLI that runs project verification without a shell string.

- [ ] **Step 1: Write command capture tests**

```python
from evidence_core import capture_command_evidence


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
```

- [ ] **Step 2: Run tests and observe the missing function**

```powershell
python -m unittest tests.test_webbuilder_evidence.CommandCaptureTests -v
```

Expected: import failure for `capture_command_evidence`.

- [ ] **Step 3: Implement capture without `shell=True`**

Build manifests with this helper:

```python
def build_command_manifest(
    *,
    project_root: Path,
    command: list[str],
    run_id: str,
    subject_id: str,
    attempt: int,
    contract_revision: int,
    fingerprint: str,
    exit_code: int,
    output_path: Path,
    replacements: int,
) -> dict[str, object]:
    relative_output = output_path.relative_to(project_root).as_posix()
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "record_id": f"EV-{secrets.token_hex(8)}",
        "run_id": run_id,
        "subject_id": subject_id,
        "attempt": attempt,
        "contract_revision": contract_revision,
        "implementation_fingerprint": fingerprint,
        "command": command,
        "cwd": ".",
        "exit_code": exit_code,
        "tool_versions": {"python": platform.python_version()},
        "artifacts": [{
            "path": relative_output,
            "sha256": sha256_bytes(output_path.read_bytes()),
            "media_type": "text/plain",
            "size": output_path.stat().st_size,
        }],
        "redaction": {"status": "passed", "replacements": replacements},
        "result": "passed" if exit_code == 0 else "failed",
        "supersedes_record_id": None,
    }
```

```python
def capture_command_evidence(
    project_root: Path,
    command: list[str],
    *,
    run_id: str,
    subject_id: str,
    attempt: int,
    contract_revision: int,
    allowed_paths: list[str],
    explicit_secrets: Iterable[str] = (),
) -> Path:
    if not command:
        raise ValueError("evidence command must not be empty")
    artifact_root = project_root / ".webbuilder-artifacts"
    artifact_root.mkdir(exist_ok=True)
    ignore_file = artifact_root / ".gitignore"
    if not ignore_file.exists():
        ignore_file.write_text("*\n!.gitignore\n", encoding="utf-8", newline="\n")
    attempt_dir = artifact_root / run_id / subject_id / str(attempt)
    attempt_dir.mkdir(parents=True, exist_ok=False)
    completed = subprocess.run(command, cwd=project_root, text=True, capture_output=True, check=False)
    output, replacements = redact_text(completed.stdout + completed.stderr, explicit_secrets)
    output_path = attempt_dir / "command-output.txt"
    output_path.write_text(output, encoding="utf-8", newline="\n")
    fingerprint = git_fingerprint(project_root) if (project_root / ".git").exists() else direct_apply_fingerprint(project_root, allowed_paths)
    manifest = build_command_manifest(
        project_root=project_root,
        command=command,
        run_id=run_id,
        subject_id=subject_id,
        attempt=attempt,
        contract_revision=contract_revision,
        fingerprint=fingerprint,
        exit_code=completed.returncode,
        output_path=output_path,
        replacements=replacements,
    )
    manifest_path = attempt_dir / "manifest.json"
    write_manifest(manifest_path, manifest, project_root=project_root)
    return manifest_path
```

The artifact entry for `command-output.txt` contains its project-relative path, SHA-256, media type `text/plain`, and byte size.

- [ ] **Step 4: Add the CLI**

CLI form:

```text
python capture-evidence.py --target <project> --run RUN-1 --subject TASK-001 --attempt 1 --contract-revision 1 --allowed-path src/app.py -- python -m unittest
```

Use `argparse.REMAINDER`; remove the leading `--`; print `manifest: <project-relative-path>` and return the captured command exit code.

- [ ] **Step 5: Verify and commit**

```powershell
python -m unittest tests.test_webbuilder_evidence.CommandCaptureTests -v
python -m unittest discover -s tests -v
git add webbuilder/scripts/evidence_core.py webbuilder/scripts/capture-evidence.py tests/test_webbuilder_evidence.py
git commit -m "feat: capture deterministic command evidence"
```

---

### Task 3: Verify, Supersede, and Promote Evidence

**Files:**
- Modify: `webbuilder/scripts/evidence_core.py`
- Modify: `tests/test_webbuilder_evidence.py`

**Interfaces:**
- Consumes: manifest path, project root, current contract revision, current implementation fingerprint.
- Produces: `verify_manifest()` and `promote_artifacts()`.

- [ ] **Step 1: Write the tamper/staleness/supersession matrix**

Add this reusable fixture and concrete mutation tests:

```python
def capture_valid_manifest(self, root: Path, attempt: int = 1) -> Path:
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
        self.assertIn("evidence artifact hash mismatch: .webbuilder-artifacts/RUN-1/TASK-001/1/command-output.txt", errors)

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

def test_promote_copies_artifacts_and_rewrites_relative_paths(self) -> None:
    with tempfile.TemporaryDirectory() as worker_tmp, tempfile.TemporaryDirectory() as main_tmp:
        worker = Path(worker_tmp)
        main = Path(main_tmp)
        manifest_path = self.capture_valid_manifest(worker)
        promoted_path = promote_artifacts(manifest_path, main)
        promoted = load_manifest(promoted_path)
        self.assertTrue(promoted_path.is_file())
        for artifact in promoted["artifacts"]:
            self.assertTrue((main / str(artifact["path"])).is_file())
            self.assertFalse(Path(str(artifact["path"])).is_absolute())
```

Add a failed-command test that expects `evidence result is not passed`, and mutate a valid manifest's redaction status to `failed` to expect `evidence redaction did not pass`. Supersession selection is covered at the validation-log layer in Task 5, where two record IDs reference attempt 1 and attempt 2 and attempt 2 declares `supersedes_record_id: EV-1`.

- [ ] **Step 2: Run tests and observe missing APIs**

```powershell
python -m unittest tests.test_webbuilder_evidence.EvidenceVerificationTests -v
```

Expected: import failure for `verify_manifest` and `promote_artifacts`.

- [ ] **Step 3: Implement fail-closed verification**

```python
def verify_manifest(
    manifest_path: Path,
    *,
    project_root: Path,
    expected_contract_revision: int,
    expected_fingerprint: str,
) -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_manifest(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"invalid evidence manifest: {exc}"]
    if manifest.get("contract_revision") != expected_contract_revision:
        errors.append("evidence contract revision does not match")
    if manifest.get("implementation_fingerprint") != expected_fingerprint:
        errors.append("evidence implementation fingerprint does not match")
    if manifest.get("result") != "passed" or manifest.get("exit_code") != 0:
        errors.append("evidence result is not passed")
    if manifest.get("redaction", {}).get("status") != "passed":
        errors.append("evidence redaction did not pass")
    for artifact in manifest.get("artifacts", []):
        path = project_root / str(artifact["path"])
        if not path.is_file():
            errors.append(f"evidence artifact missing: {artifact['path']}")
        elif sha256_bytes(path.read_bytes()) != artifact.get("sha256"):
            errors.append(f"evidence artifact hash mismatch: {artifact['path']}")
    return errors
```

Reject absolute paths and any artifact path escaping the project root.

- [ ] **Step 4: Implement canonical promotion**

Copy the attempt directory to `.webbuilder-artifacts/<run>/<subject>/<attempt>/` under the main project, recalculate every hash, rewrite paths relative to the main root, set `promoted_from` to a non-sensitive worktree identifier rather than an absolute path, and write the manifest last.

If the destination exists with different hashes, fail without overwriting. If hashes match, return the existing manifest path idempotently.

- [ ] **Step 5: Verify and commit**

```powershell
python -m unittest tests.test_webbuilder_evidence.EvidenceVerificationTests -v
python -m unittest discover -s tests -v
git add webbuilder/scripts/evidence_core.py tests/test_webbuilder_evidence.py
git commit -m "feat: verify and promote WebBuilder evidence"
```

---

### Task 4: Inspect Host Capabilities and Decide Downgrade or Block

**Files:**
- Create: `webbuilder/scripts/host_capabilities.py`
- Create: `webbuilder/scripts/check-host.py`
- Create: `tests/test_webbuilder_host_capabilities.py`

**Interfaces:**
- Consumes: approved contract capabilities and local executable/project facts.
- Produces: `inspect_local_capabilities()`, `merge_host_report()`, `capability_errors()`, and a transactionally recorded host report.

- [ ] **Step 1: Write capability decision tests**

```python
from host_capabilities import capability_errors, merge_host_report


class HostCapabilityTests(unittest.TestCase):
    def test_required_browser_unavailable_blocks(self) -> None:
        capabilities = {"browser": {"status": "unavailable", "evidence": "host report"}}
        self.assertEqual(
            capability_errors({"browser"}, capabilities),
            ["required host capability unavailable: browser"],
        )

    def test_unknown_required_capability_does_not_pass(self) -> None:
        capabilities = {"browser": {"status": "unknown", "evidence": "not inspected"}}
        self.assertEqual(
            capability_errors({"browser"}, capabilities),
            ["required host capability not confirmed: browser"],
        )

    def test_explicit_host_report_overrides_only_non_local_capabilities(self) -> None:
        inspected = {"git": {"status": "available", "evidence": "git --version"}}
        explicit = {"browser": {"status": "available", "evidence": "Codex browser tool listed"}}
        merged = merge_host_report(inspected, explicit)
        self.assertEqual(merged["git"]["status"], "available")
        self.assertEqual(merged["browser"]["status"], "available")
```

- [ ] **Step 2: Run tests and observe the missing module**

```powershell
python -m unittest tests.test_webbuilder_host_capabilities -v
```

Expected: import failure for `host_capabilities`.

- [ ] **Step 3: Implement probes and validation**

```python
CAPABILITY_NAMES = (
    "subagents", "browser", "git", "worktree", "docker", "network", "persistent_session"
)
VALID_CAPABILITY_STATUS = {"available", "unavailable", "unknown"}


def inspect_local_capabilities(project_root: Path) -> dict[str, dict[str, str]]:
    git = shutil.which("git")
    docker = shutil.which("docker")
    return {
        "git": {"status": "available" if git else "unavailable", "evidence": "git executable probe"},
        "worktree": {
            "status": "available" if git and (project_root / ".git").exists() else "unavailable",
            "evidence": "Git repository and executable probe",
        },
        "docker": {"status": "available" if docker else "unavailable", "evidence": "docker executable probe"},
        "subagents": {"status": "unknown", "evidence": "requires host report"},
        "browser": {"status": "unknown", "evidence": "requires host report"},
        "network": {"status": "unknown", "evidence": "requires host report"},
        "persistent_session": {"status": "unknown", "evidence": "requires host report"},
    }
```

Do not execute Docker, access the network, or spawn an agent merely to probe availability.

- [ ] **Step 4: Add the host-report CLI**

Supported form:

```text
python check-host.py --target <project> --set browser=available:Codex-browser-tool --set subagents=available:3-free-slots
```

The CLI validates names/status/evidence, merges local probes, writes a `## Host Capabilities` JSON block to `loop-state.md` through one State Kernel transaction, and then evaluates required host capabilities derived from the approved contract and task checker strategies.

If a required capability fails, also set `status: blocked`, `stop_reason: environment_blocked`, and `resume_checkpoint: initialization`. If only parallelism is unavailable but single mode preserves all gates, set `execution_mode: single` and record the downgrade reason.

- [ ] **Step 5: Verify and commit**

```powershell
python -m unittest tests.test_webbuilder_host_capabilities -v
python -m unittest discover -s tests -v
git add webbuilder/scripts/host_capabilities.py webbuilder/scripts/check-host.py tests/test_webbuilder_host_capabilities.py
git commit -m "feat: gate execution on host capabilities"
```

---

### Task 5: Enforce Initialization, UI, Evidence, and Delivery Gates

**Files:**
- Modify: `webbuilder/scripts/check-state.py`
- Modify: `webbuilder/scripts/init-state.py` validation/delivery templates
- Modify: `tests/test_spec2web_state_scripts.py`
- Modify: `tests/test_webbuilder_evidence.py`
- Modify: `tests/test_webbuilder_host_capabilities.py`

**Interfaces:**
- Consumes: approved contract, applicability matrix, host report, evidence manifest verifier, task records.
- Produces: `--phase host`, `--phase initialization`, `--phase ui`, and manifest-backed delivery.

- [ ] **Step 1: Write phase-level failure tests**

Add tests proving:

- UI-required contract plus browser unavailable fails `--phase host`.
- Database not applicable does not require database startup evidence.
- Docker not applicable does not require Docker evidence.
- UI-required task without a manifest fails `--phase ui`.
- Delivery with handwritten `passed` text but no manifests fails.
- Delivery with current valid manifests for every applicable project domain passes.
- API-only delivery with justified UI/accessibility non-applicability still requires functional, security, performance, and delivery-smoke evidence.

Each test invokes the real CLI against a temporary initialized directory.

- [ ] **Step 2: Run the new tests and observe missing phase choices**

```powershell
python -m unittest tests.test_webbuilder_evidence.EvidenceGateTests -v
```

Expected: failures because `host`, `initialization`, and `ui` are not accepted phases and delivery does not verify manifests.

- [ ] **Step 3: Add phase implementations**

Extend CLI choices to:

```python
(
    "structure", "specification", "host", "initialization", "execution",
    "task", "parallel", "acceptance", "integration", "ui", "delivery",
)
```

Implement:

```python
def evidence_record_errors(
    state_dir: Path,
    subject_id: str,
    quality_domain: str,
    expected_contract_revision: int,
    expected_fingerprint: str,
) -> list[str]:
    record = latest_evidence_record(state_dir, subject_id, quality_domain)
    if record is None:
        return [f"missing evidence: {subject_id} / {quality_domain}"]
    manifest_value = record_value(record, "artifact_manifest")
    if not manifest_value:
        return [f"missing artifact_manifest: {subject_id} / {quality_domain}"]
    return verify_manifest(
        state_dir.parent / manifest_value,
        project_root=state_dir.parent,
        expected_contract_revision=expected_contract_revision,
        expected_fingerprint=expected_fingerprint,
    )
```

`latest_evidence_record()` parses record ID, attempt, `supersedes_record_id`, result, and subject/domain, then selects the highest valid non-superseded attempt rather than the first heading match.

- [ ] **Step 4: Make all initialization checks applicability-aware**

Read the approved contract matrix. Install/build/test/startup remain universal as appropriate to the selected profile. Require database, migration, auth, Docker, UI, accessibility, elevated security, or product-specific performance evidence only when required. A missing host tool is not accepted as a not-applicable reason.

- [ ] **Step 5: Expand delivery coverage**

Require project-level evidence for `functional`, `security`, `performance`, and `delivery-smoke`, plus `ui` and `accessibility` when UI is required. Require task acceptance/integration evidence as before. Validate every delivery coverage row references current manifests and contains no unresolved findings or waivers without approval evidence.

- [ ] **Step 6: Verify and commit**

```powershell
python -m unittest tests.test_webbuilder_evidence -v
python -m unittest tests.test_webbuilder_host_capabilities -v
python -m unittest discover -s tests -v
git add webbuilder/scripts/check-state.py webbuilder/scripts/init-state.py tests/test_spec2web_state_scripts.py tests/test_webbuilder_evidence.py tests/test_webbuilder_host_capabilities.py
git commit -m "feat: enforce manifest-backed delivery gates"
```

---

### Task 6: Document Evidence and Host Boundaries

**Files:**
- Modify: `webbuilder/SKILL.md`
- Modify: `webbuilder/references/state-files.md`
- Modify: `webbuilder/references/multi-agent-orchestration.md`
- Modify: `webbuilder/references/interface-design.md`
- Modify: `webbuilder/references/delivery-checklist.md`
- Modify: `webbuilder/references/worktree-mode.md`
- Modify: `README.md`
- Modify: `README_EN.md`
- Modify: `tests/test_spec2web_state_scripts.py`

**Interfaces:**
- Consumes: all Plan 3 CLIs and phases.
- Produces: deterministic operational instructions for workers and Orchestrator.

- [ ] **Step 1: Add failing routing assertions**

Assert the Skill contains:

```python
self.assertIn("scripts/capture-evidence.py", text)
self.assertIn("scripts/check-host.py", text)
self.assertIn("--phase host", text)
self.assertIn("--phase initialization", text)
self.assertIn("--phase ui", text)
self.assertIn(".webbuilder-artifacts/", text)
self.assertIn("authorization header", text.lower())
```

- [ ] **Step 2: Update worker and Orchestrator protocol**

Workers capture task evidence in their assigned worktree and submit manifest paths. The Orchestrator verifies and promotes accepted evidence before cleanup, appends the validation index, and reruns relevant checks in the main workspace. Worker-authored prose alone never satisfies a gate.

- [ ] **Step 3: Update browser and delivery policy**

Task UI checks cover affected flows and representative viewports. Final UI checks cover primary approved workflows, required states, keyboard/focus, accessibility, console/network failures, and the selected performance profile without creating a full Cartesian screenshot matrix.

Document redaction, synthetic-data default, artifact retention/size, relative paths, hash checking, supersession, and external durable references.

- [ ] **Step 4: Run release verification and commit**

```powershell
python -m unittest discover -s tests -v
python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" webbuilder
git diff --check
git add webbuilder/SKILL.md webbuilder/references/state-files.md webbuilder/references/multi-agent-orchestration.md webbuilder/references/interface-design.md webbuilder/references/delivery-checklist.md webbuilder/references/worktree-mode.md README.md README_EN.md tests/test_spec2web_state_scripts.py
git commit -m "docs: define evidence and host capability protocol"
```

## Plan 3 Exit Gate

- [ ] Command evidence captures exit code, output, tool version, revision, fingerprint, artifact hashes, and redaction status.
- [ ] Tampered, stale, failed, superseded, missing, absolute-path, or unredacted evidence fails closed.
- [ ] Accepted worktree evidence promotes idempotently to the main workspace.
- [ ] Host capabilities are probed or explicitly reported with evidence and cannot be invented.
- [ ] Host/init/UI/delivery gates are capability-aware and manifest-backed.
- [ ] Autonomous execution remains disabled pending Plan 4.
