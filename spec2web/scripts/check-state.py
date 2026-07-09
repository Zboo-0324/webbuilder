#!/usr/bin/env python3
"""Check lightweight Spec2Web state files."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_FILES = [
    "project-rules.md",
    "requirements-baseline.md",
    "system-design.md",
    "task-plan.md",
    "loop-state.md",
    "validation-log.md",
    "delivery-report.md",
]

TASK_PLAN_MARKERS = [
    "requirement_ids:",
    "status:",
    "handoff_mode:",
    "integration_strategy:",
    "allowed_paths:",
    "verification:",
    "completion_criteria:",
    "acceptance_gate:",
    "submission_package:",
    "integration_policy:",
]

LOOP_STATE_MARKERS = [
    "workflow: spec2web",
    "status:",
    "current_phase:",
    "## Active Constraints",
    "continue ready tasks until blocked or delivered",
    "implementation tasks use PR/worktree handoff when Git is available",
    "delegated workers submit, Orchestrator accepts",
    "external AI workers are forbidden",
    "## PR Handoffs",
]

SYSTEM_DESIGN_MARKERS = [
    "## Technology Strategy",
    "## Interface Design Baseline",
    "### Selected Stack",
    "### UI Verification",
]


def check_state(target: Path) -> list[str]:
    state_dir = target / "spec2web"
    errors: list[str] = []

    if not state_dir.exists():
        return [f"missing state directory: {state_dir}"]

    for filename in REQUIRED_FILES:
        path = state_dir / filename
        if not path.exists():
            errors.append(f"missing required file: {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required file: {path}")

    loop_state = state_dir / "loop-state.md"
    if loop_state.exists():
        text = loop_state.read_text(encoding="utf-8")
        for marker in LOOP_STATE_MARKERS:
            if marker not in text:
                errors.append(f"loop-state.md missing marker: {marker}")
        valid_statuses = [
            "status: active",
            "status: paused",
            "status: disabled",
            "status: blocked",
        ]
        if not any(status in text for status in valid_statuses):
            errors.append("loop-state.md status must be active, paused, disabled, or blocked")

    task_plan = state_dir / "task-plan.md"
    if task_plan.exists():
        text = task_plan.read_text(encoding="utf-8")
        for marker in TASK_PLAN_MARKERS:
            if marker not in text:
                errors.append(f"task-plan.md missing marker: {marker}")

    system_design = state_dir / "system-design.md"
    if system_design.exists():
        text = system_design.read_text(encoding="utf-8")
        for marker in SYSTEM_DESIGN_MARKERS:
            if marker not in text:
                errors.append(f"system-design.md missing marker: {marker}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Spec2Web state files.")
    parser.add_argument(
        "--target",
        default=".",
        help="Project directory containing the spec2web state folder.",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    errors = check_state(target)

    if errors:
        print("Spec2Web state check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Spec2Web state check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
