#!/usr/bin/env python3
"""Validate Spec2Web state structure and phase readiness."""

from __future__ import annotations

import argparse
import re
from itertools import combinations
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
    "risk_level",
    "risk_basis",
    "checker_strategy",
    "review_mode",
    "adversarial_review",
    "user_approval",
    "approval_evidence",
    "rollback_plan",
    "recovery_point",
    "residual_risk_owner",
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
    "shared_resources",
    "conflict_domains",
    "integration_dependencies",
    "repair_attempt",
    "last_failure_fingerprint",
    "same_fingerprint_count",
    "integration_policy",
]

LOOP_STATE_MARKERS = [
    "workflow: spec2web",
    "schema_version:",
    "status:",
    "current_phase:",
    "execution_mode:",
    "host_agent_capability:",
    "available_child_slots:",
    "selected_workers:",
    "active_checker_strategy:",
    "## Active Constraints",
    "continue ready tasks until blocked or delivered",
    "delegated or parallel tasks use PR/worktree handoff when Git is available",
    "delegated workers submit, Orchestrator accepts",
    "unauthorized external AI workers are forbidden",
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

REQUIREMENTS_BASELINE_MARKERS = [
    "## User Discovery",
    "## First-Principles Analysis",
    "### Core Outcome",
    "### Hard Constraints and Invariants",
    "### Assumptions and Evidence",
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
VALID_EXECUTION_MODES = {"single", "delegated", "parallel"}
VALID_AGENT_CAPABILITIES = {"unknown", "unavailable", "available"}
VALID_RISK_LEVELS = {"unclassified", "low", "standard", "high", "critical"}
VALID_REVIEW_MODES = {"standard", "adversarial"}
VALID_CHECKER_STRATEGIES = {
    "single_session",
    "independent_checker",
    "separate_tester_reviewer",
}
VALID_ACTIVE_CHECKER_STRATEGIES = VALID_CHECKER_STRATEGIES | {"mixed"}
VALID_USER_APPROVALS = {"not_required", "required", "approved"}

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
        "not recorded",
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


def task_list_values(body: str, field: str) -> list[str]:
    match = re.search(
        rf"(?ms)^- {re.escape(field)}:\s*\n((?:  - [^\n]*(?:\n|$))*)",
        body,
    )
    if not match:
        return []
    return [
        line.strip()[2:].strip()
        for line in match.group(1).splitlines()
        if line.strip().startswith("- ")
    ]


def markdown_section_list(text: str, heading: str) -> list[str]:
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)",
        text,
    )
    if not match:
        return []
    return [
        line.strip()[2:].strip()
        for line in match.group(1).splitlines()
        if line.strip().startswith("- ")
    ]


def task_dependencies(body: str) -> list[str]:
    value = task_field_value(body, "dependencies") or ""
    return re.findall(r"TASK-[A-Za-z0-9_-]+", value)


def normalized_path_pattern(value: str) -> str:
    normalized = value.strip().strip("`\"'").replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/")


def static_path_prefix(value: str) -> str:
    normalized = normalized_path_pattern(value)
    wildcard = re.search(r"[*?[]", normalized)
    prefix = normalized[: wildcard.start()] if wildcard else normalized
    return prefix if wildcard else prefix.rstrip("/")


def path_patterns_overlap(left: str, right: str) -> bool:
    normalized_left = normalized_path_pattern(left)
    normalized_right = normalized_path_pattern(right)
    left_prefix = static_path_prefix(left)
    right_prefix = static_path_prefix(right)
    if not left_prefix or not right_prefix:
        return True
    left_has_wildcard = bool(re.search(r"[*?[]", normalized_left))
    right_has_wildcard = bool(re.search(r"[*?[]", normalized_right))
    if left_has_wildcard and normalized_right.startswith(left_prefix):
        return True
    if right_has_wildcard and normalized_left.startswith(right_prefix):
        return True
    if left_has_wildcard and right_has_wildcard:
        return left_prefix.startswith(right_prefix) or right_prefix.startswith(left_prefix)
    return (
        left_prefix == right_prefix
        or left_prefix.startswith(right_prefix + "/")
        or right_prefix.startswith(left_prefix + "/")
    )


def integer_value(text: str, key: str) -> int | None:
    value = top_level_value(text, key)
    if value is None or value == "unknown":
        return None
    try:
        return int(value)
    except ValueError:
        return None


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

        schema_version = top_level_value(loop_state, "schema_version")
        if schema_version != SCHEMA_VERSION:
            errors.append(
                f"loop-state.md schema_version must be {SCHEMA_VERSION}; "
                f"found {schema_version or 'missing'}"
            )

        execution_mode = top_level_value(loop_state, "execution_mode")
        if execution_mode not in VALID_EXECUTION_MODES:
            allowed = ", ".join(sorted(VALID_EXECUTION_MODES))
            errors.append(f"loop-state.md execution_mode must be one of: {allowed}")

        capability = top_level_value(loop_state, "host_agent_capability")
        if capability not in VALID_AGENT_CAPABILITIES:
            allowed = ", ".join(sorted(VALID_AGENT_CAPABILITIES))
            errors.append(
                f"loop-state.md host_agent_capability must be one of: {allowed}"
            )

        slots = top_level_value(loop_state, "available_child_slots")
        slot_count = integer_value(loop_state, "available_child_slots")
        if slots != "unknown" and (slot_count is None or slot_count < 0):
            errors.append(
                "loop-state.md available_child_slots must be unknown or a non-negative integer"
            )

        workers = integer_value(loop_state, "selected_workers")
        if workers is None or workers < 0:
            errors.append(
                "loop-state.md selected_workers must be a non-negative integer"
            )

        checker = top_level_value(loop_state, "active_checker_strategy")
        if checker not in VALID_ACTIVE_CHECKER_STRATEGIES:
            allowed = ", ".join(sorted(VALID_ACTIVE_CHECKER_STRATEGIES))
            errors.append(
                f"loop-state.md active_checker_strategy must be one of: {allowed}"
            )

    system_design = read_text(state_dir, "system-design.md")
    if system_design:
        for marker in SYSTEM_DESIGN_MARKERS:
            if marker not in system_design:
                errors.append(f"system-design.md missing marker: {marker}")

    requirements_baseline = read_text(state_dir, "requirements-baseline.md")
    if requirements_baseline:
        for marker in REQUIREMENTS_BASELINE_MARKERS:
            if marker not in requirements_baseline:
                errors.append(f"requirements-baseline.md missing marker: {marker}")
        discovery_status = top_level_value(requirements_baseline, "discovery_status")
        if discovery_status not in {"pending", "confirmed"}:
            errors.append(
                "requirements-baseline.md discovery_status must be pending or confirmed"
            )

    task_plan = read_text(state_dir, "task-plan.md")
    if task_plan:
        sections = TASK_SECTION_PATTERN.findall(task_plan)
        if not sections:
            errors.append("task-plan.md must contain at least one TASK section")
        task_ids = [task_id for task_id, _ in sections]
        if len(task_ids) != len(set(task_ids)):
            errors.append("task-plan.md contains duplicate task IDs")
        if not markdown_section_list(task_plan, "Shared Contract Paths"):
            errors.append("task-plan.md must define Shared Contract Paths")
        for task_id, body in sections:
            for field in TASK_FIELDS:
                if f"- {field}:" not in body:
                    errors.append(f"{task_id} missing field: {field}")
            status = task_field_value(body, "status")
            if status and status not in VALID_TASK_STATUSES:
                allowed = ", ".join(sorted(VALID_TASK_STATUSES))
                errors.append(f"{task_id} status must be one of: {allowed}")

            risk_level = task_field_value(body, "risk_level")
            if risk_level and risk_level not in VALID_RISK_LEVELS:
                allowed = ", ".join(sorted(VALID_RISK_LEVELS))
                errors.append(f"{task_id} risk_level must be one of: {allowed}")

            checker_strategy = task_field_value(body, "checker_strategy")
            if checker_strategy and checker_strategy not in VALID_CHECKER_STRATEGIES:
                allowed = ", ".join(sorted(VALID_CHECKER_STRATEGIES))
                errors.append(
                    f"{task_id} checker_strategy must be one of: {allowed}"
                )

            review_mode = task_field_value(body, "review_mode")
            if review_mode and review_mode not in VALID_REVIEW_MODES:
                allowed = ", ".join(sorted(VALID_REVIEW_MODES))
                errors.append(f"{task_id} review_mode must be one of: {allowed}")
            if risk_level in {"high", "critical"}:
                if review_mode != "adversarial":
                    errors.append(
                        f"{task_id} {risk_level}-risk work requires review_mode: adversarial"
                    )
                adversarial_cases = task_list_values(body, "adversarial_review")
                if not adversarial_cases or adversarial_cases in (
                    ["not applicable"],
                    ["not_applicable"],
                ):
                    errors.append(
                        f"{task_id} {risk_level}-risk work requires adversarial_review cases"
                    )

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

            user_approval = task_field_value(body, "user_approval")
            if user_approval and user_approval not in VALID_USER_APPROVALS:
                allowed = ", ".join(sorted(VALID_USER_APPROVALS))
                errors.append(f"{task_id} user_approval must be one of: {allowed}")

            for field in ("repair_attempt", "same_fingerprint_count"):
                value = task_field_value(body, field)
                try:
                    valid_value = value is not None and int(value) >= 0
                except ValueError:
                    valid_value = False
                if not valid_value:
                    errors.append(f"{task_id} {field} must be a non-negative integer")

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

    requirements_text = read_text(state_dir, "requirements-baseline.md")
    if top_level_value(requirements_text, "discovery_status") != "confirmed":
        errors.append(
            "requirements-baseline.md discovery_status must be confirmed after user answers"
        )
    if re.search(r"(?mi)^- not recorded\s*$", requirements_text):
        errors.append("requirements-baseline.md user discovery decisions are not recorded")

    actual_loop_status = top_level_value(read_text(state_dir, "loop-state.md"), "status")
    if actual_loop_status != loop_status:
        errors.append(
            f"loop-state.md status must be {loop_status}; "
            f"found {actual_loop_status or 'missing'}"
        )

    return errors


def incomplete_dependency_errors(
    task_id: str,
    body: str,
    tasks: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    for dependency in task_dependencies(body):
        dependency_body = tasks.get(dependency)
        if dependency_body is None:
            errors.append(f"{task_id} dependency does not exist: {dependency}")
            continue
        if task_field_value(dependency_body, "status") != "complete":
            errors.append(f"{task_id} dependency is not complete: {dependency}")
    return errors


def repair_state_errors(task_id: str, body: str) -> list[str]:
    errors: list[str] = []
    repair_budget = task_field_value(body, "repair_budget")
    repair_attempt = task_field_value(body, "repair_attempt")
    same_fingerprint_count = task_field_value(body, "same_fingerprint_count")
    if (
        repair_budget is not None
        and repair_attempt is not None
        and repair_budget.isdigit()
        and repair_attempt.isdigit()
        and int(repair_attempt) > int(repair_budget)
    ):
        errors.append(f"{task_id} repair_attempt exceeds repair_budget")
    if (
        same_fingerprint_count is not None
        and same_fingerprint_count.isdigit()
        and int(same_fingerprint_count) >= 3
    ):
        errors.append(f"{task_id} repeated failure fingerprint requires block")
    return errors


def check_task_readiness(state_dir: Path, task_id: str | None) -> list[str]:
    errors = check_execution_readiness(state_dir, loop_status="active")
    if not task_id:
        errors.append("task phase requires --task <TASK-ID>")
        return errors

    task_plan = read_text(state_dir, "task-plan.md")
    tasks = dict(TASK_SECTION_PATTERN.findall(task_plan))
    body = tasks.get(task_id)
    if body is None:
        errors.append(f"task not found: {task_id}")
        return errors

    loop_state = read_text(state_dir, "loop-state.md")
    current_task = top_level_value(loop_state, "current_task")
    if current_task != task_id:
        errors.append(
            f"loop-state.md current_task must be {task_id}; "
            f"found {current_task or 'missing'}"
        )

    status = task_field_value(body, "status")
    if status not in {"pending", "needs_repair"}:
        errors.append(
            f"{task_id} status must be pending or needs_repair to start; "
            f"found {status or 'missing'}"
        )
    errors.extend(incomplete_dependency_errors(task_id, body, tasks))
    if not task_list_values(body, "allowed_paths"):
        errors.append(f"{task_id} requires at least one allowed path")
    if not task_list_values(body, "verification"):
        errors.append(f"{task_id} requires at least one verification step")

    handoff_mode = task_field_value(body, "handoff_mode")
    workspace = task_field_value(body, "execution_workspace")
    execution_mode = top_level_value(loop_state, "execution_mode")
    capability = top_level_value(loop_state, "host_agent_capability")
    selected_workers = integer_value(loop_state, "selected_workers") or 0
    available_slots = integer_value(loop_state, "available_child_slots")
    active_checker = top_level_value(loop_state, "active_checker_strategy")
    risk_level = task_field_value(body, "risk_level")
    checker_strategy = task_field_value(body, "checker_strategy")

    if handoff_mode == "single_session":
        if execution_mode != "single":
            errors.append(f"{task_id} single_session handoff requires execution_mode: single")
        if workspace != "main":
            errors.append(f"{task_id} single_session handoff requires execution_workspace: main")
        if selected_workers != 0:
            errors.append(f"{task_id} single_session handoff requires selected_workers: 0")
    elif handoff_mode == "pr_worktree":
        if execution_mode != "delegated":
            errors.append(
                f"{task_id} task dispatch requires execution_mode: delegated"
            )
        if capability != "available":
            errors.append(f"{task_id} pr_worktree handoff requires host agents to be available")
        if not workspace or workspace in {"main", "worktree"}:
            errors.append(f"{task_id} pr_worktree handoff requires a concrete worktree path")
        if selected_workers != 1:
            errors.append(f"{task_id} delegated task requires selected_workers: 1")
        if available_slots is None:
            errors.append(f"{task_id} delegated work requires known available_child_slots")
        if checker_strategy == "single_session":
            errors.append(f"{task_id} delegated work requires an independent checker")

    if risk_level == "unclassified":
        errors.append(f"{task_id} risk_level must be classified before dispatch")
    if active_checker != checker_strategy:
        errors.append(
            f"loop-state.md active_checker_strategy must match {task_id} checker_strategy"
        )

    if risk_level == "standard" and handoff_mode == "pr_worktree":
        if checker_strategy != "independent_checker":
            errors.append(
                f"{task_id} standard delegated work requires independent_checker"
            )

    if risk_level in {"high", "critical"}:
        if handoff_mode != "pr_worktree":
            errors.append(f"{task_id} {risk_level}-risk work requires PR/worktree handoff")
        if checker_strategy != "separate_tester_reviewer":
            errors.append(
                f"{task_id} {risk_level}-risk work requires separate Tester and Reviewer"
            )

    if available_slots is not None and selected_workers > available_slots:
        errors.append(
            f"selected_workers exceeds available_child_slots: "
            f"{selected_workers} > {available_slots}"
        )

    errors.extend(repair_state_errors(task_id, body))

    return errors


def check_parallel_readiness(
    state_dir: Path,
    requested_group: str | None,
) -> list[str]:
    errors = check_execution_readiness(state_dir, loop_status="active")
    loop_state = read_text(state_dir, "loop-state.md")
    task_plan = read_text(state_dir, "task-plan.md")
    tasks = dict(TASK_SECTION_PATTERN.findall(task_plan))

    group = requested_group or top_level_value(loop_state, "active_parallel_group")
    if not group or group in {"none", "null"}:
        errors.append("parallel phase requires --parallel-group <PG-ID>")
        return errors

    active_group = top_level_value(loop_state, "active_parallel_group")
    if active_group != group:
        errors.append(
            f"loop-state.md active_parallel_group must be {group}; "
            f"found {active_group or 'missing'}"
        )

    execution_mode = top_level_value(loop_state, "execution_mode")
    capability = top_level_value(loop_state, "host_agent_capability")
    available_slots = integer_value(loop_state, "available_child_slots")
    selected_workers = integer_value(loop_state, "selected_workers") or 0
    active_checker = top_level_value(loop_state, "active_checker_strategy")

    if execution_mode != "parallel":
        errors.append("parallel phase requires execution_mode: parallel")
    current_task = top_level_value(loop_state, "current_task")
    if current_task not in {"null", "none"}:
        errors.append("parallel phase requires current_task: null")
    if capability != "available":
        errors.append("parallel phase requires host_agent_capability: available")
    if available_slots is None or available_slots < 2:
        errors.append("parallel phase requires at least 2 available_child_slots")
    if selected_workers < 2:
        errors.append("parallel phase requires at least 2 selected_workers")
    if available_slots is not None and selected_workers > available_slots:
        errors.append(
            f"selected_workers exceeds available_child_slots: "
            f"{selected_workers} > {available_slots}"
        )
    if active_checker not in VALID_ACTIVE_CHECKER_STRATEGIES:
        errors.append("parallel phase requires a valid active_checker_strategy")

    group_tasks = [
        (task_id, body)
        for task_id, body in tasks.items()
        if task_field_value(body, "parallel_group") == group
    ]
    if len(group_tasks) < 2:
        errors.append(f"parallel group {group} must contain at least 2 tasks")
        return errors
    if selected_workers != len(group_tasks):
        errors.append(
            f"selected_workers must match parallel group size: "
            f"{selected_workers} != {len(group_tasks)}"
        )

    shared_paths = markdown_section_list(task_plan, "Shared Contract Paths")
    workspaces: set[str] = set()
    allowed_paths_by_task: dict[str, list[str]] = {}
    shared_resources_by_task: dict[str, list[str]] = {}
    conflict_domains_by_task: dict[str, list[str]] = {}
    integration_dependencies_by_task: dict[str, list[str]] = {}

    for task_id, body in group_tasks:
        status = task_field_value(body, "status")
        if status not in {"pending", "needs_repair"}:
            errors.append(
                f"{task_id} status must be pending or needs_repair for parallel start"
            )
        errors.extend(incomplete_dependency_errors(task_id, body, tasks))
        errors.extend(repair_state_errors(task_id, body))

        if task_field_value(body, "handoff_mode") != "pr_worktree":
            errors.append(f"{task_id} parallel task requires handoff_mode: pr_worktree")

        risk_level = task_field_value(body, "risk_level")
        checker_strategy = task_field_value(body, "checker_strategy")
        if risk_level == "unclassified":
            errors.append(f"{task_id} risk_level must be classified before parallel dispatch")
        if checker_strategy == "single_session":
            errors.append(f"{task_id} parallel work requires an independent checker")
        if risk_level == "standard" and checker_strategy != "independent_checker":
            errors.append(
                f"{task_id} standard parallel work requires independent_checker"
            )
        if risk_level in {"high", "critical"} and checker_strategy != "separate_tester_reviewer":
            errors.append(
                f"{task_id} {risk_level}-risk parallel work requires separate Tester and Reviewer"
            )

        workspace = task_field_value(body, "execution_workspace")
        if not workspace or workspace in {"main", "worktree"}:
            errors.append(f"{task_id} parallel task requires a concrete worktree path")
        elif workspace in workspaces:
            errors.append(f"{task_id} reuses execution_workspace: {workspace}")
        else:
            workspaces.add(workspace)

        verification = task_list_values(body, "verification")
        if not verification:
            errors.append(f"{task_id} parallel task requires independent verification")

        allowed_paths = task_list_values(body, "allowed_paths")
        allowed_paths_by_task[task_id] = allowed_paths
        shared_resources_by_task[task_id] = task_list_values(body, "shared_resources")
        conflict_domains_by_task[task_id] = task_list_values(body, "conflict_domains")
        integration_dependencies_by_task[task_id] = task_list_values(
            body, "integration_dependencies"
        )
        if not allowed_paths:
            errors.append(f"{task_id} parallel task requires at least one allowed path")
        for allowed_path in allowed_paths:
            for shared_path in shared_paths:
                if path_patterns_overlap(allowed_path, shared_path):
                    errors.append(
                        f"{task_id} allowed path {allowed_path} "
                        f"intersects shared contract path {shared_path}"
                    )

    for (left_id, _), (right_id, _) in combinations(group_tasks, 2):
        for left_path in allowed_paths_by_task[left_id]:
            for right_path in allowed_paths_by_task[right_id]:
                if path_patterns_overlap(left_path, right_path):
                    errors.append(
                        f"{left_id} and {right_id} allowed_paths overlap: "
                        f"{left_path} <> {right_path}"
                    )
        left_resources = set(shared_resources_by_task[left_id]) - {"none"}
        right_resources = set(shared_resources_by_task[right_id]) - {"none"}
        for resource in sorted(left_resources & right_resources):
            errors.append(
                f"{left_id} and {right_id} shared_resources conflict: {resource}"
            )
        left_domains = set(conflict_domains_by_task[left_id]) - {"none"}
        right_domains = set(conflict_domains_by_task[right_id]) - {"none"}
        for domain in sorted(left_domains & right_domains):
            errors.append(
                f"{left_id} and {right_id} conflict_domains conflict: {domain}"
            )
        if right_id in integration_dependencies_by_task[left_id] or left_id in integration_dependencies_by_task[right_id]:
            errors.append(
                f"{left_id} and {right_id} cannot run in parallel due to integration dependency"
            )

    return errors


def validation_record(text: str, task_id: str, gate: str) -> str | None:
    match = re.search(
        rf"(?ms)^###\s+{re.escape(task_id)}\s*/\s*{re.escape(gate)}\s*\n"
        rf"(.*?)(?=^###\s+|\Z)",
        text,
    )
    return match.group(1) if match else None


def record_value(record: str, field: str) -> str | None:
    match = re.search(rf"(?m)^- {re.escape(field)}:\s*(.+?)\s*$", record)
    return match.group(1).strip() if match else None


def record_values(record: str, field: str) -> list[str]:
    value = record_value(record, field)
    if value is None:
        return []
    return [item.strip() for item in value.split(",")]


def usable_evidence(value: str | None) -> bool:
    return value not in {None, "", "none", "not_applicable", "not applicable"}


def recorded_value(value: str | None) -> bool:
    return value not in {None, ""}


def critical_contract_errors(task_id: str, body: str) -> list[str]:
    errors: list[str] = []
    if task_field_value(body, "user_approval") != "approved":
        errors.append(f"{task_id} critical work requires user_approval: approved")
    for field in (
        "approval_evidence",
        "rollback_plan",
        "recovery_point",
    ):
        values = task_list_values(body, field)
        if not values or values in (["not_applicable"], ["not applicable"]):
            errors.append(f"{task_id} critical work requires {field}")
    if not usable_evidence(task_field_value(body, "residual_risk_owner")):
        errors.append(f"{task_id} critical work requires residual_risk_owner")
    return errors


def check_acceptance_readiness(state_dir: Path, task_id: str | None) -> list[str]:
    errors: list[str] = []
    if not task_id:
        return ["acceptance phase requires --task <TASK-ID>"]

    tasks = dict(TASK_SECTION_PATTERN.findall(read_text(state_dir, "task-plan.md")))
    body = tasks.get(task_id)
    if body is None:
        return [f"task not found: {task_id}"]
    if task_field_value(body, "status") != "submitted_for_acceptance":
        errors.append(f"{task_id} status must be submitted_for_acceptance for acceptance")

    record = validation_record(read_text(state_dir, "validation-log.md"), task_id, "acceptance")
    if record is None:
        return errors + [f"validation-log.md missing {task_id} / acceptance record"]

    required_fields = (
        "gate",
        "task_status",
        "submission_commit",
        "developer_identity",
        "tester_identity",
        "tester_result",
        "reviewer_identity",
        "reviewer_result",
        "adversarial_cases_expected",
        "adversarial_cases_passed",
        "disagreement_status",
        "orchestrator_decision",
        "residual_risk",
    )
    for field in required_fields:
        if not recorded_value(record_value(record, field)):
            errors.append(f"{task_id} acceptance record missing {field}")
    if record_value(record, "gate") != "acceptance":
        errors.append(f"{task_id} acceptance record gate must be acceptance")
    if record_value(record, "task_status") != "submitted_for_acceptance":
        errors.append(f"{task_id} acceptance record task_status must be submitted_for_acceptance")
    if record_value(record, "tester_result") != "passed":
        errors.append(f"{task_id} acceptance tester_result must be passed")
    if record_value(record, "reviewer_result") != "approved":
        errors.append(f"{task_id} acceptance reviewer_result must be approved")
    if record_value(record, "orchestrator_decision") != "accepted":
        errors.append(f"{task_id} acceptance orchestrator_decision must be accepted")
    if record_value(record, "disagreement_status") == "unresolved":
        errors.append(f"{task_id} acceptance record has unresolved reviewer disagreement")

    identities = [
        record_value(record, "developer_identity"),
        record_value(record, "tester_identity"),
        record_value(record, "reviewer_identity"),
    ]
    if all(usable_evidence(identity) for identity in identities) and len(set(identities)) != 3:
        errors.append(f"{task_id} Developer, Tester, and Reviewer identities must differ")

    risk_level = task_field_value(body, "risk_level")
    if risk_level in {"high", "critical"}:
        expected = record_values(record, "adversarial_cases_expected")
        passed = record_values(record, "adversarial_cases_passed")
        if (
            not expected
            or expected in (["not_applicable"], ["not applicable"])
            or set(expected) != set(passed)
        ):
            errors.append(f"{task_id} acceptance adversarial cases are not fully covered")
    if risk_level == "critical":
        errors.extend(critical_contract_errors(task_id, body))
    return errors


def check_integration_readiness(state_dir: Path, task_id: str | None) -> list[str]:
    errors: list[str] = []
    if not task_id:
        return ["integration phase requires --task <TASK-ID>"]

    tasks = dict(TASK_SECTION_PATTERN.findall(read_text(state_dir, "task-plan.md")))
    body = tasks.get(task_id)
    if body is None:
        return [f"task not found: {task_id}"]
    if task_field_value(body, "status") != "accepted":
        errors.append(f"{task_id} status must be accepted for integration")

    record = validation_record(read_text(state_dir, "validation-log.md"), task_id, "integration")
    if record is None:
        return errors + [f"validation-log.md missing {task_id} / integration record"]
    for field in (
        "gate",
        "integration_strategy",
        "integration_commit",
        "main_workspace_verification",
        "verification_evidence",
        "final_task_status",
    ):
        if not recorded_value(record_value(record, field)):
            errors.append(f"{task_id} integration record missing {field}")
    if record_value(record, "gate") != "integration":
        errors.append(f"{task_id} integration record gate must be integration")
    strategy = task_field_value(body, "integration_strategy")
    if record_value(record, "integration_strategy") != strategy:
        errors.append(f"{task_id} integration strategy does not match task contract")
    integration_commit = record_value(record, "integration_commit")
    handoff_mode = task_field_value(body, "handoff_mode")
    if handoff_mode == "pr_worktree" and integration_commit == "direct_apply":
        errors.append(f"{task_id} PR/worktree integration requires an integration commit")
    if handoff_mode == "single_session" and integration_commit != "direct_apply":
        errors.append(f"{task_id} single_session integration must record direct_apply")
    if record_value(record, "main_workspace_verification") != "passed":
        errors.append(f"{task_id} main_workspace_verification must be passed")
    if record_value(record, "final_task_status") != "complete":
        errors.append(f"{task_id} integration final_task_status must be complete")
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
    validation_log = read_text(state_dir, "validation-log.md")
    for task_id, body in TASK_SECTION_PATTERN.findall(task_plan):
        status = task_field_value(body, "status") or "missing"
        if status != "complete":
            errors.append(f"{task_id} status must be complete for delivery; found {status}")
        acceptance = validation_record(validation_log, task_id, "acceptance")
        integration = validation_record(validation_log, task_id, "integration")
        if acceptance is None:
            errors.append(f"{task_id} lacks acceptance evidence for delivery")
        elif record_value(acceptance, "orchestrator_decision") != "accepted":
            errors.append(f"{task_id} acceptance evidence is not accepted")
        if integration is None:
            errors.append(f"{task_id} lacks integration evidence for delivery")
        elif (
            record_value(integration, "main_workspace_verification") != "passed"
            or record_value(integration, "final_task_status") != "complete"
        ):
            errors.append(f"{task_id} integration evidence is incomplete for delivery")

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


def check_state(
    target: Path,
    phase: str = "structure",
    task_id: str | None = None,
    parallel_group: str | None = None,
) -> list[str]:
    state_dir = resolve_state_dir(target)
    if not state_dir.exists():
        return [f"missing state directory: {state_dir}"]

    errors = check_structure(state_dir)
    if phase == "execution":
        errors.extend(check_execution_readiness(state_dir, loop_status="active"))
    elif phase == "task":
        errors.extend(check_task_readiness(state_dir, task_id))
    elif phase == "parallel":
        errors.extend(check_parallel_readiness(state_dir, parallel_group))
    elif phase == "acceptance":
        errors.extend(check_acceptance_readiness(state_dir, task_id))
    elif phase == "integration":
        errors.extend(check_integration_readiness(state_dir, task_id))
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
        help="Project directory containing the webbuilder state folder.",
    )
    parser.add_argument(
        "--phase",
        choices=(
            "structure",
            "execution",
            "task",
            "parallel",
            "acceptance",
            "integration",
            "delivery",
        ),
        default="structure",
        help=(
            "Validation depth: structure checks files and contracts; execution "
            "requires confirmed baselines; task and parallel validate dispatch; "
            "acceptance and integration validate per-task evidence; delivery requires "
            "terminal state and evidence closure."
        ),
    )
    parser.add_argument(
        "--task",
        help="Task ID required by --phase task, acceptance, or integration.",
    )
    parser.add_argument(
        "--parallel-group",
        help="Parallel group to validate; defaults to loop-state.md when omitted.",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    errors = check_state(
        target,
        phase=args.phase,
        task_id=args.task,
        parallel_group=args.parallel_group,
    )

    if errors:
        print(f"Spec2Web {args.phase} phase check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Spec2Web {args.phase} phase check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
