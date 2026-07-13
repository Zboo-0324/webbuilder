"""Evidence manifest persistence, secret redaction, and implementation fingerprints."""
from __future__ import annotations

import hashlib
import json
import re
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
    return hashlib.sha256(payload).hexdigest()
