#!/usr/bin/env python3
"""Approve or invalidate a WebBuilder solution contract revision."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from contract_core import (
    _check_approval_revision,
    contract_digest,
    extract_contract_material,
    validate_capabilities,
    validate_workload_envelope,
)
from state_schema import resolve_state_dir, set_top_level_value, top_level_value
from state_transition import apply_transaction


def approve_contract(target: Path, evidence: str) -> int:
    state_dir = resolve_state_dir(target)

    requirements_text = (state_dir / "requirements-baseline.md").read_text(encoding="utf-8")
    design_text = (state_dir / "system-design.md").read_text(encoding="utf-8")
    plan_text = (state_dir / "task-plan.md").read_text(encoding="utf-8")
    loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")

    material = extract_contract_material(requirements_text)

    cap_errors = validate_capabilities(
        material.get("capabilities", {}),
        delivery_assumptions=material.get("delivery_assumptions"),
    )
    if cap_errors:
        raise ValueError("invalid capabilities: " + "; ".join(cap_errors))

    wl_errors = validate_workload_envelope(material.get("workload_envelope", {}))
    if wl_errors:
        raise ValueError("invalid workload envelope: " + "; ".join(wl_errors))

    revision_errors = _check_approval_revision(requirements_text, material)
    if revision_errors:
        raise ValueError("contract revision errors: " + "; ".join(revision_errors))

    digest = contract_digest(material)
    revision = int(top_level_value(requirements_text, "contract_revision") or "1")

    approved_rev = top_level_value(requirements_text, "approved_contract_revision")
    confirmation = top_level_value(requirements_text, "confirmation_status")
    if approved_rev == str(revision) and confirmation == "approved":
        print(f"Contract already approved at revision {revision}.")
        return 0

    now = datetime.now(timezone.utc).isoformat()

    updated_requirements = requirements_text
    for key, value in [
        ("confirmation_status", "approved"),
        ("approved_contract_revision", str(revision)),
        ("approval_digest", digest),
        ("approved_by", "user"),
        ("approved_at", now),
        ("approval_evidence", evidence),
    ]:
        updated_requirements = set_top_level_value(updated_requirements, key, value)

    updated_design = set_top_level_value(design_text, "based_on_contract_revision", str(revision))
    updated_plan = set_top_level_value(plan_text, "based_on_contract_revision", str(revision))
    updated_loop = set_top_level_value(loop_text, "autonomy_scope", "confirmed_plan")

    expected_revision = int(top_level_value(loop_text, "state_revision") or "0")
    transition_id = apply_transaction(
        state_dir,
        "approve-contract",
        {
            "requirements-baseline.md": updated_requirements,
            "system-design.md": updated_design,
            "task-plan.md": updated_plan,
            "loop-state.md": updated_loop,
        },
        expected_revision=expected_revision,
    )

    print(f"Contract approved at revision {revision}. Transition: {transition_id}")
    return 0


def invalidate_contract(target: Path) -> int:
    state_dir = resolve_state_dir(target)

    requirements_text = (state_dir / "requirements-baseline.md").read_text(encoding="utf-8")
    design_text = (state_dir / "system-design.md").read_text(encoding="utf-8")
    plan_text = (state_dir / "task-plan.md").read_text(encoding="utf-8")
    loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")

    material = extract_contract_material(requirements_text)
    current_digest = contract_digest(material)
    approved_digest = top_level_value(requirements_text, "approval_digest")
    if approved_digest and approved_digest != "null" and approved_digest == current_digest:
        print("No material contract change detected. Invalidation skipped.")
        return 0

    revision = int(top_level_value(requirements_text, "contract_revision") or "1")
    next_revision = revision + 1

    updated_requirements = requirements_text
    for key, value in [
        ("contract_revision", str(next_revision)),
        ("confirmation_status", "pending"),
        ("approved_contract_revision", "null"),
        ("approval_digest", "null"),
        ("approved_by", "null"),
        ("approved_at", "null"),
        ("approval_evidence", "null"),
    ]:
        updated_requirements = set_top_level_value(updated_requirements, key, value)

    updated_design = set_top_level_value(design_text, "based_on_contract_revision", "stale")
    updated_plan = set_top_level_value(plan_text, "based_on_contract_revision", "stale")
    updated_loop = set_top_level_value(loop_text, "autonomy_scope", "unconfirmed")

    expected_revision = int(top_level_value(loop_text, "state_revision") or "0")
    transition_id = apply_transaction(
        state_dir,
        "invalidate-contract",
        {
            "requirements-baseline.md": updated_requirements,
            "system-design.md": updated_design,
            "task-plan.md": updated_plan,
            "loop-state.md": updated_loop,
        },
        expected_revision=expected_revision,
    )

    print(f"Contract invalidated. New revision: {next_revision}. Transition: {transition_id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Approve or invalidate a WebBuilder solution contract revision."
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Project directory containing the webbuilder state folder.",
    )
    parser.add_argument(
        "--approval-evidence",
        help="Evidence identifier for the approval (e.g. user-message-42).",
    )
    parser.add_argument(
        "--invalidate-material-change",
        action="store_true",
        help="Invalidate the current approval due to a material contract change.",
    )
    args = parser.parse_args()

    if args.approval_evidence and args.invalidate_material_change:
        parser.error("--approval-evidence and --invalidate-material-change are mutually exclusive")
    if not args.approval_evidence and not args.invalidate_material_change:
        parser.error("either --approval-evidence or --invalidate-material-change is required")

    try:
        target = Path(args.target).resolve()
        if args.invalidate_material_change:
            return invalidate_contract(target)
        return approve_contract(target, args.approval_evidence)
    except (OSError, ValueError) as exc:
        print(f"Contract operation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
