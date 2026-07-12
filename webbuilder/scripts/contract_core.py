from __future__ import annotations

import json
import re

from state_schema import sha256_bytes

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
