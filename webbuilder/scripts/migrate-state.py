#!/usr/bin/env python3
"""Migrate Spec2Web state metadata to the V1.3 schema."""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


STATE_DIR_NAME = "webbuilder"
LEGACY_STATE_DIR_NAME = "spec2web"
SCHEMA_VERSION = "1.3"


def resolve_state_dir(target: Path) -> Path:
    state_dir = target / STATE_DIR_NAME
    legacy_state_dir = target / LEGACY_STATE_DIR_NAME
    if not (state_dir / "loop-state.md").exists() and (
        legacy_state_dir / "loop-state.md"
    ).exists():
        return legacy_state_dir
    return state_dir

ORCHESTRATION_FIELDS = [
    ("schema_version", SCHEMA_VERSION),
    ("execution_mode", "single"),
    ("host_agent_capability", "unknown"),
    ("available_child_slots", "unknown"),
    ("selected_workers", "0"),
    ("active_checker_strategy", "single_session"),
]

TASK_DEFAULT_LISTS = {
    "risk_basis": ["not recorded"],
    "adversarial_review": ["not_applicable"],
    "approval_evidence": ["not_applicable"],
    "rollback_plan": ["not_applicable"],
    "recovery_point": ["not_applicable"],
    "shared_resources": ["none"],
    "conflict_domains": ["none"],
    "integration_dependencies": ["none"],
}

TASK_DEFAULT_VALUES = {
    "checker_strategy": "single_session",
    "review_mode": "standard",
    "user_approval": "not_required",
    "residual_risk_owner": "not_applicable",
    "repair_attempt": "0",
    "last_failure_fingerprint": "none",
    "same_fingerprint_count": "0",
}

SHARED_CONTRACT_SECTION = """## Shared Contract Paths

- webbuilder/
- package.json
- pyproject.toml
- migrations/
- openapi/

"""

FIRST_PRINCIPLES_SECTION = """## First-Principles Analysis

### Core Outcome

- not recorded

### Hard Constraints and Invariants

- not recorded

### Assumptions and Evidence

- not recorded

"""

DISCOVERY_SECTION = """## User Discovery

discovery_status: pending

### AI Working Hypothesis

- not recorded

### Questions Asked

- generated dynamically after reading the user's brief and project context

### User Decisions

- not recorded

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
    if version_match and version_match.group(1) not in {
        "1.0",
        "1.1",
        "1.2",
        SCHEMA_VERSION,
    }:
        raise ValueError(
            f"unsupported schema_version: {version_match.group(1)}; "
            "manual migration required"
        )

    if not re.search(r"(?m)^active_checker_strategy:\s*[^\s#]+\s*$", text):
        text = re.sub(
            r"(?m)^checker_strategy:\s*([^\s#]+)\s*$",
            r"active_checker_strategy: \1",
            text,
        )

    if version_match and version_match.group(1) == SCHEMA_VERSION:
        has_all_fields = all(
            re.search(rf"(?m)^{re.escape(name)}:\s*[^\s#]+\s*$", text)
            for name, _ in ORCHESTRATION_FIELDS
        )
        if has_all_fields and not re.search(r"(?m)^checker_strategy:\s*", text):
            return text

    field_names = {name for name, _ in ORCHESTRATION_FIELDS}
    field_names.add("checker_strategy")
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
    marker = "## Tasks"
    if marker not in text:
        raise ValueError("task-plan.md missing ## Tasks")
    if not re.search(r"(?m)^## Shared Contract Paths\s*$", text):
        text = text.replace(marker, SHARED_CONTRACT_SECTION + marker, 1)

    def migrate_task(match: re.Match[str]) -> str:
        header, body = match.groups()
        has_risk_basis = bool(re.search(r"(?m)^- risk_basis:\s*$", body))
        if not has_risk_basis:
            if re.search(r"(?m)^- risk_level:\s*[^\n]+$", body):
                body = re.sub(
                    r"(?m)^- risk_level:\s*[^\n]+$",
                    "- risk_level: unclassified",
                    body,
                    count=1,
                )
            else:
                body += "- risk_level: unclassified\n"
            body += "- risk_basis:\n  - not recorded\n"
        elif not re.search(r"(?m)^- risk_level:\s*[^\n]+$", body):
            body += "- risk_level: unclassified\n"

        for field, default in TASK_DEFAULT_VALUES.items():
            if not re.search(rf"(?m)^- {re.escape(field)}:\s*[^\n]+$", body):
                body += f"- {field}: {default}\n"
        for field, values in TASK_DEFAULT_LISTS.items():
            if not re.search(rf"(?m)^- {re.escape(field)}:\s*$", body):
                body += f"- {field}:\n"
                body += "".join(f"  - {value}\n" for value in values)
        return header + body

    return re.sub(
        r"(?ms)(^###\s+TASK-[A-Za-z0-9_-]+:[^\n]*\n)(.*?)(?=^###\s+TASK-|\Z)",
        migrate_task,
        text,
    )


def migrate_requirements_baseline(text: str) -> str:
    if re.search(r"(?m)^## User Discovery\s*$", text):
        return text
    if re.search(r"(?m)^## First-Principles Analysis\s*$", text):
        return text.replace("## First-Principles Analysis", DISCOVERY_SECTION + "## First-Principles Analysis", 1)
    marker = "## Assumptions"
    if marker in text:
        return text.replace(marker, FIRST_PRINCIPLES_SECTION + marker, 1)
    marker = "## Open Questions"
    if marker in text:
        return text.replace(marker, FIRST_PRINCIPLES_SECTION + marker, 1)
    return text.rstrip() + "\n\n" + DISCOVERY_SECTION + FIRST_PRINCIPLES_SECTION


def migrate(target: Path, dry_run: bool) -> tuple[list[Path], Path | None]:
    state_dir = resolve_state_dir(target)
    loop_state = state_dir / "loop-state.md"
    task_plan = state_dir / "task-plan.md"
    requirements_baseline = state_dir / "requirements-baseline.md"
    for path in (loop_state, task_plan, requirements_baseline):
        if not path.exists():
            raise ValueError(f"missing required file: {path}")

    original = {
        loop_state: loop_state.read_text(encoding="utf-8"),
        task_plan: task_plan.read_text(encoding="utf-8"),
        requirements_baseline: requirements_baseline.read_text(encoding="utf-8"),
    }
    migrated = {
        loop_state: migrate_loop_state(original[loop_state]),
        task_plan: migrate_task_plan(original[task_plan]),
        requirements_baseline: migrate_requirements_baseline(
            original[requirements_baseline]
        ),
    }
    changed = [
        path
        for path in (loop_state, task_plan, requirements_baseline)
        if migrated[path] != original[path]
    ]
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
    parser = argparse.ArgumentParser(description="Migrate WebBuilder state to V1.3.")
    parser.add_argument(
        "--target",
        default=".",
        help="Project directory containing the webbuilder state folder.",
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
