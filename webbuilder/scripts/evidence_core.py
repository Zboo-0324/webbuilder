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
    """SHA-256 over JSON containing ``git rev-parse HEAD`` and ``git status --porcelain``."""
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
    payload = json.dumps({"head": head, "status": status}, sort_keys=True).encode("utf-8")
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
