#!/usr/bin/env python3
"""Migrate Spec2Web V1 state metadata to the V1.1 schema."""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = "1.1"

ORCHESTRATION_FIELDS = [
    ("schema_version", SCHEMA_VERSION),
    ("execution_mode", "single"),
    ("host_agent_capability", "unknown"),
    ("available_child_slots", "unknown"),
    ("selected_workers", "0"),
    ("checker_strategy", "single_session"),
]

SHARED_CONTRACT_SECTION = """## Shared Contract Paths

- spec2web/
- package.json
- pyproject.toml
- migrations/
- openapi/

"""


def migrate_loop_state(text: str) -> str:
    text = text.replace(
        "- implementation tasks use PR/worktree handoff when Git is available",
        "- delegated or parallel tasks use PR/worktree handoff when Git is available",
    )
    text = text.replace(
        "- external AI workers are forbidden",
        "- unauthorized external AI workers are forbidden",
    )
    version_match = re.search(r"(?m)^schema_version:\s*([^\s#]+)\s*$", text)
    if version_match and version_match.group(1) not in {"1.0", SCHEMA_VERSION}:
        raise ValueError(
            f"unsupported schema_version: {version_match.group(1)}; "
            "manual migration required"
        )

    if version_match and version_match.group(1) == SCHEMA_VERSION:
        has_all_fields = all(
            re.search(rf"(?m)^{re.escape(name)}:\s*[^\s#]+\s*$", text)
            for name, _ in ORCHESTRATION_FIELDS
        )
        if has_all_fields:
            return text

    field_names = {name for name, _ in ORCHESTRATION_FIELDS}
    values: dict[str, str] = {}
    for name, default in ORCHESTRATION_FIELDS:
        match = re.search(rf"(?m)^{re.escape(name)}:\s*([^\s#]+)\s*$", text)
        values[name] = match.group(1) if match else default
    values["schema_version"] = SCHEMA_VERSION
    lines = [
        line
        for line in text.splitlines()
        if not any(re.match(rf"^{re.escape(name)}:\s*", line) for name in field_names)
    ]
    try:
        workflow_index = next(
            index for index, line in enumerate(lines) if line.strip() == "workflow: spec2web"
        )
    except StopIteration as exc:
        raise ValueError("loop-state.md missing workflow: spec2web") from exc

    metadata = [f"{name}: {values[name]}" for name, _ in ORCHESTRATION_FIELDS]
    lines[workflow_index + 1 : workflow_index + 1] = metadata
    return "\n".join(lines).rstrip() + "\n"


def migrate_task_plan(text: str) -> str:
    if re.search(r"(?m)^## Shared Contract Paths\s*$", text):
        return text
    marker = "## Tasks"
    if marker not in text:
        raise ValueError("task-plan.md missing ## Tasks")
    return text.replace(marker, SHARED_CONTRACT_SECTION + marker, 1)


def migrate(target: Path, dry_run: bool) -> tuple[list[Path], Path | None]:
    state_dir = target / "spec2web"
    loop_state = state_dir / "loop-state.md"
    task_plan = state_dir / "task-plan.md"
    for path in (loop_state, task_plan):
        if not path.exists():
            raise ValueError(f"missing required file: {path}")

    original = {
        loop_state: loop_state.read_text(encoding="utf-8"),
        task_plan: task_plan.read_text(encoding="utf-8"),
    }
    migrated = {
        loop_state: migrate_loop_state(original[loop_state]),
        task_plan: migrate_task_plan(original[task_plan]),
    }
    changed = [path for path in (loop_state, task_plan) if migrated[path] != original[path]]
    if dry_run or not changed:
        return changed, None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = state_dir / f".migration-backup-{timestamp}"
    backup_dir.mkdir(parents=False, exist_ok=False)
    for path in changed:
        shutil.copy2(path, backup_dir / path.name)
        path.write_text(migrated[path], encoding="utf-8", newline="\n")
    return changed, backup_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate Spec2Web state to V1.1.")
    parser.add_argument(
        "--target",
        default=".",
        help="Project directory containing the spec2web state folder.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report files that would change without writing them.",
    )
    args = parser.parse_args()

    try:
        changed, backup_dir = migrate(Path(args.target).resolve(), args.dry_run)
    except (OSError, ValueError) as exc:
        print(f"Spec2Web migration failed: {exc}")
        return 1

    if not changed:
        print(f"Spec2Web state already uses schema {SCHEMA_VERSION}.")
        return 0

    action = "would update" if args.dry_run else "updated"
    for path in changed:
        print(f"{action}: {path}")
    if backup_dir:
        print(f"backup: {backup_dir}")
    print("next: run check-state.py --phase structure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
