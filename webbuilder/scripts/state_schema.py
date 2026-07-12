from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from pathlib import Path


STATE_DIR_NAME = "webbuilder"
LEGACY_STATE_DIR_NAME = "spec2web"
SCHEMA_VERSION = "1.4"
SUPPORTED_SOURCE_VERSIONS = {"1.0", "1.1", "1.2", "1.3"}
REQUIRED_FILES = (
    "project-rules.md",
    "requirements-baseline.md",
    "system-design.md",
    "task-plan.md",
    "loop-state.md",
    "validation-log.md",
    "delivery-report.md",
)
TASK_SECTION_PATTERN = re.compile(
    r"(?ms)^###\s+(TASK-[A-Za-z0-9_-]+):[^\n]*\n(.*?)(?=^###\s+TASK-|\Z)"
)


def resolve_state_dir(target: Path) -> Path:
    state_dir = target / STATE_DIR_NAME
    legacy = target / LEGACY_STATE_DIR_NAME
    if not (state_dir / "loop-state.md").exists() and (legacy / "loop-state.md").exists():
        return legacy
    return state_dir


def read_state_files(state_dir: Path, names: Iterable[str]) -> dict[str, str]:
    return {name: (state_dir / name).read_text(encoding="utf-8") for name in names}


def top_level_value(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*([^\s#]+)\s*$", text)
    return match.group(1) if match else None


def set_top_level_value(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
    if re.search(pattern, text):
        return re.sub(pattern, f"{key}: {value}", text, count=1)
    lines = text.rstrip().splitlines()
    insert_at = 1 if lines and lines[0].startswith("# ") else 0
    lines[insert_at:insert_at] = ["", f"{key}: {value}"]
    return "\n".join(lines).rstrip() + "\n"


def markdown_section(text: str, heading: str) -> str | None:
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", text)
    return match.group(1).rstrip() if match else None


def task_sections(text: str) -> dict[str, str]:
    return dict(TASK_SECTION_PATTERN.findall(text))


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def direct_apply_fingerprint(project_root: Path, allowed_paths: Iterable[str]) -> str:
    entries = []
    for value in sorted(set(allowed_paths)):
        path = project_root / value
        if path.is_file():
            entries.append(
                {"path": value.replace("\\", "/"), "sha256": sha256_bytes(path.read_bytes())}
            )
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))
