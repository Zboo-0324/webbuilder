#!/usr/bin/env python3
"""Validate Spec2Web state structure and phase readiness."""

from __future__ import annotations

import argparse
import re
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

TASK_FIELDS = [
    "requirement_ids",
    "goal",
    "dependencies",
    "status",
    "handoff_mode",
    "integration_strategy",
    "allowed_paths",
    "expected_outputs",
    "verification",
    "completion_criteria",
    "acceptance_gate",
    "repair_budget",
    "submission_package",
    "risks_or_blockers",
    "execution_workspace",
    "parallel_group",
    "integration_policy",
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
    "### Options Considered",
    "### Selected Stack",
    "### Dependency Policy",
    "## Interface Design Baseline",
    "### Component Conventions",
    "### State Coverage",
    "### UI Verification",
]

VALID_LOOP_STATUSES = {"active", "paused", "disabled", "blocked", "delivered"}
VALID_FILE_STATUSES = {
    "project-rules.md": {"draft", "ready"},
    "requirements-baseline.md": {"draft", "confirmed"},
    "system-design.md": {"draft", "ready"},
    "task-plan.md": {"draft", "ready"},
    "delivery-report.md": {"draft", "complete"},
}
VALID_TASK_STATUSES = {
    "pending",
    "in_progress",
    "submitted_for_acceptance",
    "needs_repair",
    "accepted",
    "integrated",
    "complete",
    "blocked",
}
VALID_HANDOFF_MODES = {"pr_worktree", "single_session"}
VALID_INTEGRATION_STRATEGIES = {
    "merge",
    "squash_merge",
    "cherry_pick",
    "integration_commit",
    "direct_apply",
}

EXECUTION_STATUSES = {
    "project-rules.md": "ready",
    "requirements-baseline.md": "confirmed",
    "system-design.md": "ready",
    "task-plan.md": "ready",
}

PLACEHOLDER_FRAGMENTS = {
    "requirements-baseline.md": [
        "replace with the first confirmed requirement.",
        "replace with verification method.",
    ],
    "system-design.md": [
        "not recorded",
        "none recorded yet.",
        "replace with project-specific tradeoffs.",
    ],
    "task-plan.md": [
        "replace with first task title",
        "replace with one concrete outcome.",
        "replace/with/path",
        "replace with expected output",
        "replace with exact command or manual check",
        "replace with worker-observable condition for submitting the task",
        "replace with orchestrator check required before accepting or merging",
    ],
}

DELIVERY_PLACEHOLDERS = [
    "nothing delivered yet",
    "no validation recorded yet",
    "not recorded yet",
    "work has not started",
]

TASK_SECTION_PATTERN = re.compile(
    r"(?ms)^###\s+(TASK-[A-Za-z0-9_-]+):[^\n]*\n(.*?)(?=^###\s+TASK-|\Z)"
)


def read_text(state_dir: Path, filename: str) -> str:
    path = state_dir / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def top_level_value(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*([^\s#]+)\s*$", text)
    return match.group(1) if match else None


def task_field_value(body: str, field: str) -> str | None:
    match = re.search(rf"(?m)^- {re.escape(field)}:\s*([^\s#]+)\s*$", body)
    return match.group(1) if match else None


def check_structure(state_dir: Path) -> list[str]:
    errors: list[str] = []

    for filename in REQUIRED_FILES:
        path = state_dir / filename
        if not path.exists():
            errors.append(f"missing required file: {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required file: {path}")

    for filename, valid_statuses in VALID_FILE_STATUSES.items():
        text = read_text(state_dir, filename)
        if not text:
            continue
        status = top_level_value(text, "status")
        if status not in valid_statuses:
            allowed = ", ".join(sorted(valid_statuses))
            errors.append(f"{filename} status must be one of: {allowed}")

    loop_state = read_text(state_dir, "loop-state.md")
    if loop_state:
        for marker in LOOP_STATE_MARKERS:
            if marker not in loop_state:
                errors.append(f"loop-state.md missing marker: {marker}")
        status = top_level_value(loop_state, "status")
        if status not in VALID_LOOP_STATUSES:
            allowed = ", ".join(sorted(VALID_LOOP_STATUSES))
            errors.append(f"loop-state.md status must be one of: {allowed}")

    system_design = read_text(state_dir, "system-design.md")
    if system_design:
        for marker in SYSTEM_DESIGN_MARKERS:
            if marker not in system_design:
                errors.append(f"system-design.md missing marker: {marker}")

    task_plan = read_text(state_dir, "task-plan.md")
    if task_plan:
        sections = TASK_SECTION_PATTERN.findall(task_plan)
        if not sections:
            errors.append("task-plan.md must contain at least one TASK section")
        for task_id, body in sections:
            for field in TASK_FIELDS:
                if f"- {field}:" not in body:
                    errors.append(f"{task_id} missing field: {field}")
            status = task_field_value(body, "status")
            if status and status not in VALID_TASK_STATUSES:
                allowed = ", ".join(sorted(VALID_TASK_STATUSES))
                errors.append(f"{task_id} status must be one of: {allowed}")

            handoff_mode = task_field_value(body, "handoff_mode")
            if handoff_mode and handoff_mode not in VALID_HANDOFF_MODES:
                allowed = ", ".join(sorted(VALID_HANDOFF_MODES))
                errors.append(f"{task_id} handoff_mode must be one of: {allowed}")

            strategy = task_field_value(body, "integration_strategy")
            if strategy and strategy not in VALID_INTEGRATION_STRATEGIES:
                allowed = ", ".join(sorted(VALID_INTEGRATION_STRATEGIES))
                errors.append(
                    f"{task_id} integration_strategy must be one of: {allowed}"
                )
            if handoff_mode == "single_session" and strategy != "direct_apply":
                errors.append(
                    f"{task_id} single_session handoff requires "
                    "integration_strategy: direct_apply"
                )
            if handoff_mode == "pr_worktree" and strategy == "direct_apply":
                errors.append(
                    f"{task_id} pr_worktree handoff cannot use "
                    "integration_strategy: direct_apply"
                )

            repair_budget = task_field_value(body, "repair_budget")
            if repair_budget:
                try:
                    valid_budget = 1 <= int(repair_budget) <= 3
                except ValueError:
                    valid_budget = False
                if not valid_budget:
                    errors.append(f"{task_id} repair_budget must be an integer from 1 to 3")

    return errors


def check_execution_readiness(state_dir: Path, loop_status: str) -> list[str]:
    errors: list[str] = []

    for filename, expected in EXECUTION_STATUSES.items():
        actual = top_level_value(read_text(state_dir, filename), "status")
        if actual != expected:
            errors.append(f"{filename} status must be {expected}; found {actual or 'missing'}")

    for filename, fragments in PLACEHOLDER_FRAGMENTS.items():
        text = read_text(state_dir, filename).lower()
        if any(fragment in text for fragment in fragments):
            errors.append(f"{filename} contains placeholder content")

    actual_loop_status = top_level_value(read_text(state_dir, "loop-state.md"), "status")
    if actual_loop_status != loop_status:
        errors.append(
            f"loop-state.md status must be {loop_status}; "
            f"found {actual_loop_status or 'missing'}"
        )

    return errors


def check_delivery_readiness(state_dir: Path) -> list[str]:
    errors = check_execution_readiness(state_dir, loop_status="delivered")

    loop_state = read_text(state_dir, "loop-state.md")
    current_phase = top_level_value(loop_state, "current_phase")
    if current_phase != "delivery":
        errors.append(
            f"loop-state.md current_phase must be delivery; "
            f"found {current_phase or 'missing'}"
        )

    task_plan = read_text(state_dir, "task-plan.md")
    for task_id, body in TASK_SECTION_PATTERN.findall(task_plan):
        status = task_field_value(body, "status") or "missing"
        if status != "complete":
            errors.append(f"{task_id} status must be complete for delivery; found {status}")

    validation_log = read_text(state_dir, "validation-log.md")
    if not re.search(r"(?m)^###\s+\S", validation_log):
        errors.append("validation-log.md has no validation entries")

    delivery_report = read_text(state_dir, "delivery-report.md")
    report_status = top_level_value(delivery_report, "status")
    if report_status != "complete":
        errors.append(
            f"delivery-report.md status must be complete; "
            f"found {report_status or 'missing'}"
        )
    lowered_report = delivery_report.lower()
    if any(fragment in lowered_report for fragment in DELIVERY_PLACEHOLDERS):
        errors.append("delivery-report.md contains placeholder content")

    return errors


def check_state(target: Path, phase: str = "structure") -> list[str]:
    state_dir = target / "spec2web"
    if not state_dir.exists():
        return [f"missing state directory: {state_dir}"]

    errors = check_structure(state_dir)
    if phase == "execution":
        errors.extend(check_execution_readiness(state_dir, loop_status="active"))
    elif phase == "delivery":
        errors.extend(check_delivery_readiness(state_dir))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Spec2Web state structure and phase readiness."
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Project directory containing the spec2web state folder.",
    )
    parser.add_argument(
        "--phase",
        choices=("structure", "execution", "delivery"),
        default="structure",
        help=(
            "Validation depth: structure checks files and contracts; execution "
            "requires confirmed baselines; delivery requires terminal state and evidence."
        ),
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    errors = check_state(target, phase=args.phase)

    if errors:
        print(f"Spec2Web {args.phase} phase check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Spec2Web {args.phase} phase check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
