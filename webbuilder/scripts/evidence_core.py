"""Evidence manifest persistence, secret redaction, and implementation fingerprints."""
from __future__ import annotations

import json
import platform
import re
import secrets
import subprocess
from collections.abc import Iterable
from pathlib import Path

from state_schema import direct_apply_fingerprint, sha256_bytes

MANIFEST_SCHEMA_VERSION = "1.0"

SECRET_PATTERNS = (
    re.compile(r"(?im)^(authorization:\s*bearer\s+).+$"),
    re.compile(r"(?im)^(cookie:\s*).+$"),
    re.compile(r"(?im)^([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY)[A-Z0-9_]*=).+$"),
)


def redact_text(text: str, explicit_secrets: Iterable[str] = ()) -> tuple[str, int]:
    """Redact authorization headers, cookies, secret assignments, and explicit secrets."""
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
    """Write a manifest to *path* after verifying no absolute project paths leak."""
    path.resolve().relative_to(project_root.resolve())
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if str(project_root.resolve()) in serialized:
        raise ValueError("manifest contains project absolute path")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8", newline="\n")


def load_manifest(path: Path) -> dict[str, object]:
    """Load a manifest and validate its schema version."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported evidence manifest")
    return value


def git_fingerprint(project_root: Path) -> str:
    """SHA-256 over JSON containing ``git rev-parse HEAD`` and ``git status --porcelain``.

    Entries whose path lies under ``webbuilder/`` are excluded so that
    routine workflow-state writes (validation-log, task-plan, etc.) do
    not alter the implementation fingerprint.
    """
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    # Filter out entries whose path lies under webbuilder/ (workflow state,
    # not implementation).  Handles plain and rename/copy porcelain records.
    filtered_lines: list[str] = []
    for line in status.splitlines():
        if len(line) >= 4:  # minimum: "XY " + 1-char path
            rest = line[3:]
            if " -> " in rest:
                orig, dest = rest.split(" -> ", 1)
                skip = orig.startswith("webbuilder/") or dest.startswith("webbuilder/")
            else:
                skip = rest.startswith("webbuilder/")
            if skip:
                continue
        filtered_lines.append(line)
    filtered_status = "\n".join(filtered_lines)
    payload = json.dumps({"head": head, "status": filtered_status}, sort_keys=True).encode("utf-8")
    return sha256_bytes(payload)


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


def _validate_identifier(name: str, label: str) -> None:
    """Reject identifiers that could escape the artifact directory."""
    if not name or not name.strip():
        raise ValueError(f"{label} must be a nonempty path component")
    pure = Path(name).parts
    if len(pure) != 1 or pure[0] != name:
        raise ValueError(f"{label} must be a plain path component, got: {name!r}")
    if name in (".", ".."):
        raise ValueError(f"{label} must not be '.' or '..'")


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
    _validate_identifier(run_id, "run_id")
    _validate_identifier(subject_id, "subject_id")
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


def verify_manifest(
    manifest_path: Path,
    *,
    project_root: Path,
    expected_contract_revision: int,
    expected_fingerprint: str,
) -> list[str]:
    """Verify an evidence manifest is valid, untampered, and current.

    Returns a list of error strings; empty list means the manifest passes.
    Fails closed on any unreadable or structurally invalid manifest.
    """
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
    redaction = manifest.get("redaction")
    if isinstance(redaction, dict) and redaction.get("status") == "passed":
        pass
    else:
        errors.append("evidence redaction did not pass")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("evidence artifacts is not a list")
    else:
        for i, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"evidence artifact entry is not a mapping: index {i}")
                continue
            rel_path = artifact.get("path")
            if not isinstance(rel_path, str) or not rel_path:
                errors.append(f"evidence artifact path is invalid: {rel_path!r}")
                continue
            sha = artifact.get("sha256")
            if not isinstance(sha, str) or not sha:
                errors.append(f"evidence artifact sha256 is malformed: {rel_path}")
                continue
            abs_path = Path(rel_path)
            if abs_path.is_absolute():
                errors.append(f"evidence artifact path is invalid: {rel_path}")
                continue
            try:
                (project_root / rel_path).resolve().relative_to(project_root.resolve())
            except ValueError:
                errors.append(f"evidence artifact path escapes project root: {rel_path}")
                continue
            path = project_root / rel_path
            if not path.is_file():
                errors.append(f"evidence artifact missing: {rel_path}")
            elif sha256_bytes(path.read_bytes()) != sha:
                errors.append(f"evidence artifact hash mismatch: {rel_path}")
    return errors


def promote_artifacts(manifest_path: Path, destination_root: Path) -> Path:
    """Copy evidence artifacts from a worker to the main project root.

    Validates all manifest metadata, artifact paths, and source hashes
    before creating any destination files.  Idempotent when destination
    content matches; raises ``ValueError`` on any divergence or invalid input.
    """
    manifest = load_manifest(manifest_path)
    run_id = str(manifest["run_id"])
    subject_id = str(manifest["subject_id"])
    attempt_raw = manifest["attempt"]

    # Validate identifiers before any file I/O.
    _validate_identifier(run_id, "run_id")
    _validate_identifier(subject_id, "subject_id")
    if not isinstance(attempt_raw, int) or attempt_raw < 1:
        raise ValueError(f"attempt must be a positive integer, got: {attempt_raw!r}")
    attempt = attempt_raw

    # Validate manifest path matches expected worker attempt path.
    source_root = manifest_path.parent.parent.parent.parent.parent
    expected_manifest = (
        source_root / ".webbuilder-artifacts" / run_id / subject_id / str(attempt) / "manifest.json"
    )
    if manifest_path.resolve() != expected_manifest.resolve():
        raise ValueError("manifest path does not match expected worker attempt path")

    # Validate artifacts list.
    artifacts_raw = manifest.get("artifacts")
    if not isinstance(artifacts_raw, list) or not artifacts_raw:
        raise ValueError("artifacts must be a nonempty list")

    source_attempt_dir = (source_root / ".webbuilder-artifacts" / run_id / subject_id / str(attempt)).resolve()
    validated: list[tuple[str, str, bytes, dict]] = []
    for i, artifact in enumerate(artifacts_raw):
        if not isinstance(artifact, dict):
            raise ValueError(f"artifact entry is not a mapping: index {i}")
        rel_path = artifact.get("path")
        if not isinstance(rel_path, str) or not rel_path:
            raise ValueError(f"artifact path is invalid: {rel_path!r}")
        sha = artifact.get("sha256")
        if not isinstance(sha, str) or not sha:
            raise ValueError(f"artifact sha256 is malformed: index {i}")

        # Path must be relative and resolve under source root.
        if Path(rel_path).is_absolute():
            raise ValueError(f"artifact path is absolute: {rel_path}")
        try:
            resolved_src = (source_root / rel_path).resolve()
            resolved_src.relative_to(source_root.resolve())
        except ValueError:
            raise ValueError(f"artifact path escapes source root: {rel_path}")

        # Artifact must stay within the attempt directory.
        try:
            resolved_src.relative_to(source_attempt_dir)
        except ValueError:
            raise ValueError(f"artifact path is outside attempt directory: {rel_path}")

        # Destination path must not escape destination root.
        try:
            (destination_root / rel_path).resolve().relative_to(destination_root.resolve())
        except ValueError:
            raise ValueError(f"artifact destination path escapes destination root: {rel_path}")

        # Read source and verify hash before any writes.
        src_file = source_root / rel_path
        if not src_file.is_file():
            raise ValueError(f"source artifact missing: {rel_path}")
        src_data = src_file.read_bytes()
        if sha256_bytes(src_data) != sha:
            raise ValueError(f"source artifact hash mismatch: {rel_path}")

        validated.append((rel_path, sha, src_data, artifact))

    # Handle destination.
    dest_attempt_dir = destination_root / ".webbuilder-artifacts" / run_id / subject_id / str(attempt)
    dest_manifest_path = dest_attempt_dir / "manifest.json"

    if dest_attempt_dir.is_dir():
        # Existing directory must have a readable manifest.
        if not dest_manifest_path.is_file():
            raise ValueError(f"destination attempt directory exists without manifest: {dest_attempt_dir}")
        existing = load_manifest(dest_manifest_path)
        existing_arts = existing.get("artifacts")
        if not isinstance(existing_arts, list):
            raise ValueError("destination manifest has malformed artifacts")
        if len(existing_arts) != len(validated):
            raise ValueError("destination artifact count differs from source")
        for (rel_path, sha, _src_data, _src_art), existing_art in zip(validated, existing_arts):
            if not isinstance(existing_art, dict):
                raise ValueError("destination manifest has non-mapping artifact entry")
            if existing_art.get("path") != rel_path:
                raise ValueError(f"destination artifact path mismatch: {rel_path}")
            if existing_art.get("sha256") != sha:
                raise ValueError(f"destination artifact hash mismatch: {rel_path}")
            dest_file = destination_root / rel_path
            if not dest_file.is_file():
                raise ValueError(f"destination artifact missing: {rel_path}")
            if sha256_bytes(dest_file.read_bytes()) != sha:
                raise ValueError(f"destination artifact content diverged: {rel_path}")

        # Verify no unexpected files exist in the destination attempt directory.
        expected_filenames = {"manifest.json"}
        for rel_path, _, _, _ in validated:
            expected_filenames.add(str(Path(rel_path).relative_to(dest_attempt_dir.relative_to(destination_root))))
        actual_filenames = {
            str(f.relative_to(dest_attempt_dir))
            for f in dest_attempt_dir.rglob("*")
            if f.is_file()
        }
        if actual_filenames != expected_filenames:
            unexpected = sorted(actual_filenames - expected_filenames)
            missing = sorted(expected_filenames - actual_filenames)
            parts: list[str] = []
            if unexpected:
                parts.append(f"unexpected={unexpected}")
            if missing:
                parts.append(f"missing={missing}")
            raise ValueError(
                f"destination attempt directory content mismatch: {'; '.join(parts)}"
            )

        return dest_manifest_path

    # Create destination and copy validated artifacts.
    dest_attempt_dir.mkdir(parents=True, exist_ok=True)
    new_artifacts: list[dict[str, object]] = []
    for rel_path, _sha, src_data, src_art in validated:
        dest_file = destination_root / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        dest_file.write_bytes(src_data)
        new_artifacts.append({
            "path": rel_path,
            "sha256": sha256_bytes(src_data),
            "media_type": src_art.get("media_type", "application/octet-stream"),
            "size": len(src_data),
        })

    promoted_manifest = dict(manifest)
    promoted_manifest["artifacts"] = new_artifacts
    promoted_manifest["promoted_from"] = source_root.name
    write_manifest(dest_manifest_path, promoted_manifest, project_root=destination_root)
    return dest_manifest_path
