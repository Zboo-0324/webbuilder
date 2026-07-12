from __future__ import annotations

import json
import re

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


VALID_CAPABILITY_STATUSES = frozenset({"required", "recommended", "optional"})
VALID_CAPABILITY_PROFILES = frozenset({"baseline", "standard", "strict"})


def validate_capabilities(capabilities: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(capabilities, dict):
        return ["capabilities must be a JSON object"]
    for name, entry in capabilities.items():
        if not isinstance(entry, dict):
            errors.append(f"capabilities.{name} must be a JSON object")
            continue
        status = entry.get("status")
        if status is None:
            errors.append(f"capabilities.{name}.status is required")
        elif status not in VALID_CAPABILITY_STATUSES:
            errors.append(
                f"capabilities.{name}.status must be one of "
                + ", ".join(sorted(VALID_CAPABILITY_STATUSES))
            )
        profile = entry.get("profile")
        if profile is None:
            errors.append(f"capabilities.{name}.profile is required")
        elif profile not in VALID_CAPABILITY_PROFILES:
            errors.append(
                f"capabilities.{name}.profile must be one of "
                + ", ".join(sorted(VALID_CAPABILITY_PROFILES))
            )
    return errors


def contract_revision_errors(requirements_text: str, material: dict[str, object]) -> list[str]:
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
