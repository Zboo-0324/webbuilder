from __future__ import annotations

import json
import re
from pathlib import Path

from state_schema import sha256_bytes, top_level_value

CONTRACT_BLOCK = re.compile(
    r"(?ms)^```json contract-material[ \t]*\n(.*?)\n```[ \t]*$"
)
MATERIAL_FIELDS = (
    "problem", "desired_outcome", "target_users", "primary_jobs",
    "core_capabilities", "non_goals", "primary_workflows",
    "page_navigation_summary", "ui_direction", "technology_profile",
    "public_interfaces", "data_boundary", "permission_boundary",
    "delivery_assumptions", "material_risks", "acceptance_signals",
    "capabilities", "workload_envelope",
)


def extract_contract_material(requirements_text: str) -> dict[str, object]:
    matches = CONTRACT_BLOCK.findall(requirements_text)
    if len(matches) != 1:
        raise ValueError("requirements-baseline.md must contain exactly one contract-material block")
    try:
        value = json.loads(matches[0])
    except json.JSONDecodeError:
        raise ValueError("contract-material block contains invalid JSON")
    if not isinstance(value, dict):
        raise ValueError("contract material must be a JSON object")
    missing = [field for field in MATERIAL_FIELDS if field not in value]
    if missing:
        raise ValueError("contract material missing fields: " + ", ".join(missing))
    return value


def canonical_contract_bytes(material: dict[str, object]) -> bytes:
    text = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text.encode("utf-8")


def contract_digest(material: dict[str, object]) -> str:
    selected = {field: material[field] for field in MATERIAL_FIELDS}
    return sha256_bytes(canonical_contract_bytes(selected))


def material_contract_changed(before: dict[str, object], after: dict[str, object]) -> bool:
    return canonical_contract_bytes(before) != canonical_contract_bytes(after)


REQUIRED_CAPABILITY_NAMES = frozenset({
    "ui", "database", "authentication", "rbac", "audit",
    "docker", "accessibility", "performance", "security",
})
VALID_CAPABILITY_STATUSES = frozenset({"required", "not_applicable"})
VALID_CAPABILITY_PROFILES = frozenset({"baseline", "standard", "strict"})
_PROFILE_CAPABILITIES = frozenset({"security", "performance"})


def _check_approval_revision(requirements_text: str, material: dict[str, object]) -> list[str]:
    errors: list[str] = []
    approved_rev = top_level_value(requirements_text, "approved_contract_revision")
    if approved_rev is None or approved_rev == "null":
        return errors
    current_rev = top_level_value(requirements_text, "contract_revision") or "1"
    if approved_rev != current_rev:
        errors.append(
            f"approved_contract_revision ({approved_rev}) does not match "
            f"contract_revision ({current_rev})"
        )
    approved_digest = top_level_value(requirements_text, "approval_digest")
    if approved_digest and approved_digest != "null":
        current_digest = contract_digest(material)
        if approved_digest != current_digest:
            errors.append(
                f"approval_digest does not match current contract material digest"
            )
    return errors


def validate_capabilities(capabilities: object, delivery_assumptions: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(capabilities, dict):
        return ["capabilities must be a JSON object"]

    missing_names = REQUIRED_CAPABILITY_NAMES - set(capabilities.keys())
    if missing_names:
        errors.append("capabilities missing required names: " + ", ".join(sorted(missing_names)))

    extra_names = set(capabilities.keys()) - REQUIRED_CAPABILITY_NAMES
    if extra_names:
        errors.append("capabilities has unknown names: " + ", ".join(sorted(extra_names)))

    statuses: dict[str, str] = {}
    for name in REQUIRED_CAPABILITY_NAMES:
        entry = capabilities.get(name)
        if entry is None:
            continue
        if not isinstance(entry, dict):
            errors.append(f"capabilities.{name} must be a JSON object")
            continue
        status = entry.get("status")
        if status is None:
            errors.append(f"capabilities.{name}.status is required")
            continue
        if status not in VALID_CAPABILITY_STATUSES:
            errors.append(
                f"capabilities.{name}.status must be one of "
                + ", ".join(sorted(VALID_CAPABILITY_STATUSES))
            )
            continue
        statuses[name] = status
        if status == "not_applicable":
            reason = entry.get("reason")
            if not reason or not str(reason).strip():
                errors.append(f"capabilities.{name}.reason is required when status is not_applicable")
        if name in _PROFILE_CAPABILITIES and status == "required":
            profile = entry.get("profile")
            if profile is None:
                errors.append(f"capabilities.{name}.profile is required")
            elif profile not in VALID_CAPABILITY_PROFILES:
                errors.append(
                    f"capabilities.{name}.profile must be one of "
                    + ", ".join(sorted(VALID_CAPABILITY_PROFILES))
                )

    if statuses.get("ui") == "required" and statuses.get("accessibility") != "required":
        errors.append("capabilities.ui required requires capabilities.accessibility required")
    if statuses.get("rbac") == "required" and statuses.get("authentication") != "required":
        errors.append("capabilities.rbac required requires capabilities.authentication required")
    if statuses.get("database") == "required":
        assumptions = delivery_assumptions or []
        has_init = any("initialization" in a.lower() or "migration" in a.lower() for a in assumptions)
        if not has_init:
            errors.append("capabilities.database required needs initialization or migration in delivery_assumptions")

    return errors


def validate_workload_envelope(workload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(workload, dict):
        return ["workload_envelope must be a JSON object"]

    task_count = workload.get("task_count")
    if task_count is None:
        errors.append("workload_envelope.task_count is required")
    else:
        tc_str = str(task_count)
        range_match = re.fullmatch(r"(\d+)-(\d+)", tc_str)
        if not range_match:
            errors.append("workload_envelope.task_count must be a range like '4-6'")
        else:
            lo, hi = int(range_match.group(1)), int(range_match.group(2))
            if lo > hi:
                errors.append("workload_envelope.task_count range start must be <= end")

    for list_field in ("browser_flows", "external_dependencies", "quality_gates"):
        value = workload.get(list_field)
        if value is None:
            errors.append(f"workload_envelope.{list_field} is required")
        elif not isinstance(value, list):
            errors.append(f"workload_envelope.{list_field} must be a list")

    repair = workload.get("repair_budgets")
    if repair is None:
        errors.append("workload_envelope.repair_budgets is required")
    elif not isinstance(repair, dict):
        errors.append("workload_envelope.repair_budgets must be a JSON object")
    else:
        if repair.get("task") != 3:
            errors.append("workload_envelope.repair_budgets.task must be 3")
        if repair.get("integration") != 5:
            errors.append("workload_envelope.repair_budgets.integration must be 5")

    if "available_concurrency" not in workload:
        errors.append("workload_envelope.available_concurrency is required")

    for rejected in ("token_count", "api_calls", "elapsed_minutes", "interruptions"):
        if rejected in workload:
            errors.append(f"workload_envelope.{rejected} is not accepted")

    return errors


def contract_revision_errors(state_dir: Path) -> list[str]:
    """Check contract revision, digest, capabilities, workload, and derived document staleness."""
    errors: list[str] = []
    requirements_path = state_dir / "requirements-baseline.md"
    if not requirements_path.exists():
        return ["missing requirements-baseline.md"]
    requirements_text = requirements_path.read_text(encoding="utf-8")
    try:
        material = extract_contract_material(requirements_text)
    except ValueError as exc:
        return [str(exc)]

    cap_errors = validate_capabilities(
        material.get("capabilities", {}),
        delivery_assumptions=material.get("delivery_assumptions"),
    )
    errors.extend(cap_errors)

    wl_errors = validate_workload_envelope(material.get("workload_envelope", {}))
    errors.extend(wl_errors)

    errors.extend(_check_approval_revision(requirements_text, material))

    current_rev = top_level_value(requirements_text, "contract_revision") or "1"
    design_path = state_dir / "system-design.md"
    plan_path = state_dir / "task-plan.md"

    if design_path.exists():
        design_text = design_path.read_text(encoding="utf-8")
        design_rev = top_level_value(design_text, "based_on_contract_revision")
        if design_rev and design_rev != current_rev:
            errors.append(
                f"system-design.md based_on_contract_revision ({design_rev}) "
                f"does not match contract_revision ({current_rev})"
            )

    if plan_path.exists():
        plan_text = plan_path.read_text(encoding="utf-8")
        plan_rev = top_level_value(plan_text, "based_on_contract_revision")
        if plan_rev and plan_rev != current_rev:
            errors.append(
                f"task-plan.md based_on_contract_revision ({plan_rev}) "
                f"does not match contract_revision ({current_rev})"
            )

    return errors
