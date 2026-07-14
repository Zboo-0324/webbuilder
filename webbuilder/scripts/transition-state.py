from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import tempfile
from pathlib import Path

from state_schema import TASK_SECTION_PATTERN, resolve_state_dir, set_top_level_value, top_level_value
from state_transition import apply_transaction, recover_pending_transaction


CONTROL_KEYS = {
    "workflow",
    "schema_version",
    "status",
    "discovery_status",
    "current_phase",
    "current_task",
    "active_parallel_group",
    "delivery_mode",
    "autonomy_scope",
    "stop_reason",
    "resume_checkpoint",
    "active_run_id",
    "state_revision",
    "pending_transition",
    "execution_mode",
    "host_agent_capability",
    "available_child_slots",
    "selected_workers",
    "active_checker_strategy",
    "user_approval",
    "approval_evidence",
    "rollback_plan",
    "recovery_point",
    "residual_risk_owner",
    "checker_strategy",
    "review_mode",
    "adversarial_review",
    "handoff_mode",
    "integration_strategy",
    "repair_budget",
    "task_repair_attempt",
    "task_failure_fingerprint",
    "task_same_fingerprint_count",
    "integration_repair_attempt",
    "integration_failure_fingerprint",
    "integration_same_fingerprint_count",
    "integration_policy",
}
STOP_REASONS = {
    "verification_failed",
    "needs_user_action",
    "needs_decision",
    "repair_exhausted",
    "environment_blocked",
}
LIFECYCLE_EVENTS = {
    "mark-project-rules-ready",
    "confirm-user-discovery",
    "confirm-requirements",
    "mark-system-design-ready",
    "mark-task-plan-ready",
    "start-task",
    "submit-task",
    "accept-task",
    "complete-task-integration",
    "complete-delivery-report",
    "pause",
    "block",
    "resume",
    "deliver",
}


def parse_update(value: str) -> tuple[str, str, str]:
    if "\r" in value or "\n" in value:
        raise ValueError("invalid --set value: line breaks are not allowed")
    name, separator, assignment = value.partition(":")
    key, equals, field_value = assignment.partition("=")
    if not separator or not name or not equals or not key:
        raise ValueError(f"invalid --set value: {value}")
    return name, key, field_value


def task_body(text: str, task_id: str) -> str:
    body = dict(TASK_SECTION_PATTERN.findall(text)).get(task_id)
    if body is None:
        raise ValueError(f"task not found: {task_id}")
    return body


def task_value(text: str, task_id: str, key: str) -> str | None:
    match = re.search(rf"(?m)^- {re.escape(key)}:\s*([^\s#]+)\s*$", task_body(text, task_id))
    return match.group(1) if match else None


def set_task_value(text: str, task_id: str, key: str, value: str) -> str:
    pattern = (
        rf"(?ms)(^###\s+{re.escape(task_id)}:[^\n]*\n.*?^- {re.escape(key)}:\s*)[^\n]*$"
    )
    updated, replacements = re.subn(pattern, rf"\g<1>{value}", text, count=1)
    if replacements != 1:
        raise ValueError(f"{task_id} missing field: {key}")
    return updated


def require_task(args: argparse.Namespace) -> str:
    if not args.task:
        raise ValueError(f"{args.event} requires --task <TASK-ID>")
    return args.task


def require_top_level_value(text: str, key: str, expected: set[str], filename: str) -> None:
    value = top_level_value(text, key)
    if value not in expected:
        choices = ", ".join(sorted(expected))
        raise ValueError(f"{filename} {key} must be one of: {choices}; found {value or 'missing'}")


def load_checker():
    script = Path(__file__).with_name("check-state.py")
    spec = importlib.util.spec_from_file_location("webbuilder_check_state", script)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load state checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checker_errors(
    state_dir: Path,
    updates: dict[str, str],
    phase: str,
    *,
    task_id: str | None = None,
) -> list[str]:
    checker = load_checker()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        shadow_state = root / state_dir.name
        shutil.copytree(state_dir, shadow_state)
        artifacts_dir = state_dir.parent / ".webbuilder-artifacts"
        if artifacts_dir.is_dir():
            shutil.copytree(artifacts_dir, root / ".webbuilder-artifacts")
        for name, text in updates.items():
            (shadow_state / name).write_text(text, encoding="utf-8", newline="\n")
        return checker.check_state(
            root,
            phase=phase,
            task_id=task_id,
            evidence_project_root=state_dir.parent,
        )


def require_gate(
    state_dir: Path,
    updates: dict[str, str],
    phase: str,
    *,
    task_id: str | None = None,
) -> None:
    errors = checker_errors(state_dir, updates, phase, task_id=task_id)
    if errors:
        raise ValueError(f"{phase} phase check failed: " + "; ".join(errors))


def require_artifact_readiness(state_dir: Path, filename: str, updated: str) -> None:
    checker = load_checker()
    errors = checker_errors(state_dir, {filename: updated}, "structure")
    fragments = checker.PLACEHOLDER_FRAGMENTS.get(filename, [])
    if any(fragment in updated.lower() for fragment in fragments):
        errors.append(f"{filename} contains placeholder content")
    if filename == "project-rules.md" and "- [ ]" in updated:
        errors.append("project-rules.md Sources Read checklist has unchecked entries")
    if errors:
        raise ValueError("; ".join(errors))


def descriptive_updates(state_dir: Path, sets: list[str]) -> dict[str, str]:
    if not sets:
        raise ValueError("edit-descriptive-content requires at least one --set")
    updates: dict[str, str] = {}
    for raw_value in sets:
        name, key, field_value = parse_update(raw_value)
        if key in CONTROL_KEYS:
            raise ValueError(f"may not set control value: {name}:{key}")
        path = state_dir / name
        text = updates.get(name, path.read_text(encoding="utf-8"))
        updates[name] = set_top_level_value(text, key, field_value)
    return updates


def lifecycle_updates(state_dir: Path, args: argparse.Namespace) -> dict[str, str]:
    if args.event not in LIFECYCLE_EVENTS:
        raise ValueError(f"unsupported transition event: {args.event}")
    if args.sets:
        raise ValueError(f"{args.event} constructs control values internally and does not accept --set")
    loop = (state_dir / "loop-state.md").read_text(encoding="utf-8")
    baseline_events = {
        "mark-project-rules-ready": ("project-rules.md", "draft", "ready"),
        "mark-system-design-ready": ("system-design.md", "draft", "ready"),
        "mark-task-plan-ready": ("task-plan.md", "draft", "ready"),
        "complete-delivery-report": ("delivery-report.md", "draft", "complete"),
    }
    if args.event in baseline_events:
        filename, source, target = baseline_events[args.event]
        text = (state_dir / filename).read_text(encoding="utf-8")
        require_top_level_value(text, "status", {source}, filename)
        updated = set_top_level_value(text, "status", target)
        if args.event == "complete-delivery-report":
            delivery_loop = set_top_level_value(loop, "status", "delivered")
            delivery_loop = set_top_level_value(delivery_loop, "current_phase", "delivery")
            delivery_loop = set_top_level_value(delivery_loop, "stop_reason", "none")
            require_gate(
                state_dir,
                {filename: updated, "loop-state.md": delivery_loop},
                "delivery",
            )
        else:
            require_artifact_readiness(state_dir, filename, updated)
        return {filename: updated}

    if args.event == "confirm-user-discovery":
        text = (state_dir / "requirements-baseline.md").read_text(encoding="utf-8")
        require_top_level_value(text, "discovery_status", {"pending"}, "requirements-baseline.md")
        if re.search(r"(?mi)^- not recorded\s*$", text):
            raise ValueError("requirements-baseline.md user discovery decisions are not recorded")
        updated = set_top_level_value(text, "discovery_status", "confirmed")
        require_gate(
            state_dir,
            {"requirements-baseline.md": updated},
            "structure",
        )
        return {"requirements-baseline.md": updated}

    if args.event == "confirm-requirements":
        text = (state_dir / "requirements-baseline.md").read_text(encoding="utf-8")
        require_top_level_value(text, "status", {"draft"}, "requirements-baseline.md")
        require_top_level_value(text, "discovery_status", {"confirmed"}, "requirements-baseline.md")
        updated = set_top_level_value(text, "status", "confirmed")
        require_artifact_readiness(state_dir, "requirements-baseline.md", updated)
        return {"requirements-baseline.md": updated}

    if args.event == "start-task":
        task_id = require_task(args)
        plan = (state_dir / "task-plan.md").read_text(encoding="utf-8")
        status = task_value(plan, task_id, "status")
        if status not in {"pending", "needs_repair"}:
            raise ValueError(f"{task_id} status must be pending or needs_repair; found {status or 'missing'}")
        require_top_level_value(loop, "status", {"active"}, "loop-state.md")
        require_top_level_value(loop, "current_task", {"null", "none"}, "loop-state.md")
        gate_loop = set_top_level_value(loop, "current_task", task_id)
        require_gate(state_dir, {"loop-state.md": gate_loop}, "task", task_id=task_id)
        return {
            "loop-state.md": gate_loop,
            "task-plan.md": set_task_value(plan, task_id, "status", "in_progress"),
        }

    if args.event == "submit-task":
        task_id = require_task(args)
        plan = (state_dir / "task-plan.md").read_text(encoding="utf-8")
        if task_value(plan, task_id, "status") != "in_progress":
            raise ValueError(f"{task_id} status must be in_progress")
        require_top_level_value(loop, "current_task", {task_id}, "loop-state.md")
        return {"task-plan.md": set_task_value(plan, task_id, "status", "submitted_for_acceptance")}

    if args.event == "accept-task":
        task_id = require_task(args)
        plan = (state_dir / "task-plan.md").read_text(encoding="utf-8")
        if task_value(plan, task_id, "status") != "submitted_for_acceptance":
            raise ValueError(f"{task_id} status must be submitted_for_acceptance")
        require_gate(state_dir, {}, "acceptance", task_id=task_id)
        return {"task-plan.md": set_task_value(plan, task_id, "status", "accepted")}

    if args.event == "complete-task-integration":
        task_id = require_task(args)
        plan = (state_dir / "task-plan.md").read_text(encoding="utf-8")
        if task_value(plan, task_id, "status") != "accepted":
            raise ValueError(f"{task_id} status must be accepted")
        require_gate(state_dir, {}, "integration", task_id=task_id)
        return {
            "task-plan.md": set_task_value(plan, task_id, "status", "complete"),
            "loop-state.md": set_top_level_value(loop, "current_task", "null"),
        }

    if args.event == "block":
        if args.reason not in STOP_REASONS:
            allowed = ", ".join(sorted(STOP_REASONS))
            raise ValueError(f"block requires --reason one of: {allowed}")
        require_top_level_value(loop, "status", {"active", "paused"}, "loop-state.md")
        updated = set_top_level_value(loop, "status", "blocked")
        return {"loop-state.md": set_top_level_value(updated, "stop_reason", args.reason)}

    if args.event == "pause":
        require_top_level_value(loop, "status", {"active"}, "loop-state.md")
        return {"loop-state.md": set_top_level_value(loop, "status", "paused")}

    if args.event == "resume":
        require_top_level_value(loop, "status", {"blocked", "paused"}, "loop-state.md")
        req_text = (state_dir / "requirements-baseline.md").read_text(encoding="utf-8")
        approved_rev = top_level_value(req_text, "approved_contract_revision")
        contract_rev = top_level_value(req_text, "contract_revision") or "1"
        if approved_rev is None or approved_rev == "null" or approved_rev != contract_rev:
            raise ValueError(
                "resume requires an approved contract matching the current revision"
            )
        updated = set_top_level_value(loop, "status", "active")
        updated = set_top_level_value(updated, "stop_reason", "none")
        return {"loop-state.md": set_top_level_value(updated, "resume_checkpoint", "none")}

    if args.event == "deliver":
        require_top_level_value(loop, "status", {"active"}, "loop-state.md")
        updated = set_top_level_value(loop, "status", "delivered")
        updated = set_top_level_value(updated, "current_phase", "delivery")
        updated = set_top_level_value(updated, "stop_reason", "none")
        require_gate(state_dir, {"loop-state.md": updated}, "delivery")
        return {"loop-state.md": updated}

    raise ValueError(f"unsupported transition event: {args.event}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply or recover a WebBuilder state transition.")
    parser.add_argument("--target", default=".", help="Project directory containing webbuilder state.")
    parser.add_argument("--recover", action="store_true", help="Recover a pending transition.")
    parser.add_argument("--event", help="Supported transition event name.")
    parser.add_argument("--task", help="Task ID for a task lifecycle transition.")
    parser.add_argument("--reason", help="Declared reason for a block transition.")
    parser.add_argument("--set", dest="sets", action="append", default=[], help="file:key=value for descriptive content only")
    parser.add_argument("--stop-reason", dest="stop_reason", help="Directly set stop_reason and block the loop.")
    parser.add_argument("--checkpoint", help="Set resume_checkpoint on the loop state.")
    parser.add_argument("--resume", action="store_true", help="Resume from a blocked or paused state.")
    parser.add_argument("--deliver", action="store_true", help="Trigger the deliver lifecycle event.")
    args = parser.parse_args()

    if args.recover:
        if args.event or args.sets or args.task or args.reason or args.stop_reason or args.checkpoint or args.resume or args.deliver:
            parser.error("--recover cannot be combined with transition arguments")
    elif args.resume:
        if args.event or args.sets or args.task or args.reason or args.stop_reason or args.checkpoint or args.deliver:
            parser.error("--resume cannot be combined with transition arguments")
    elif args.deliver:
        if args.event or args.sets or args.task or args.reason or args.stop_reason or args.checkpoint:
            parser.error("--deliver cannot be combined with transition arguments")
    elif args.stop_reason:
        if args.event:
            parser.error("--stop-reason cannot be combined with --event")
        if args.stop_reason not in STOP_REASONS:
            allowed = ", ".join(sorted(STOP_REASONS))
            parser.error(f"--stop-reason must be one of: {allowed}")
        if not args.checkpoint:
            parser.error("--stop-reason requires --checkpoint")
    elif args.checkpoint:
        parser.error("--checkpoint requires --stop-reason")
    elif not args.event:
        parser.error("--event is required unless recovering or using --stop-reason")

    try:
        state_dir = resolve_state_dir(Path(args.target).resolve())
        if args.recover:
            transition_id = recover_pending_transaction(state_dir)
            if transition_id:
                print(f"recovered: {transition_id}")
            return 0

        if args.resume:
            updates = lifecycle_updates(state_dir, argparse.Namespace(event="resume", sets=[], task=None, reason=None))
            event_name = "resume"
        elif args.deliver:
            updates = lifecycle_updates(state_dir, argparse.Namespace(event="deliver", sets=[], task=None, reason=None))
            event_name = "deliver"
        elif args.stop_reason:
            loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            require_top_level_value(loop_text, "status", {"active", "paused"}, "loop-state.md")
            updated = set_top_level_value(loop_text, "status", "blocked")
            updated = set_top_level_value(updated, "stop_reason", args.stop_reason)
            updated = set_top_level_value(updated, "resume_checkpoint", args.checkpoint)
            updates = {"loop-state.md": updated}
            event_name = "block"
        elif args.event == "edit-descriptive-content":
            updates = descriptive_updates(state_dir, args.sets)
            event_name = args.event
        else:
            updates = lifecycle_updates(state_dir, args)
            event_name = args.event
        loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")
        expected_revision = int(top_level_value(loop_text, "state_revision") or "0")
        transition_id = apply_transaction(
            state_dir, event_name, updates, expected_revision=expected_revision
        )
    except (OSError, ValueError) as exc:
        print(f"State transition failed: {exc}")
        return 1

    print(f"applied: {transition_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
