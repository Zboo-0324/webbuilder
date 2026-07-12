from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "webbuilder" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from contract_core import (  # noqa: E402
    canonical_contract_bytes,
    contract_digest,
    extract_contract_material,
)


class ContractCoreTests(unittest.TestCase):
    MATERIAL = {
        "problem": "Reduce manual review time",
        "desired_outcome": "Reviewers finish one case in under five minutes",
        "target_users": ["reviewer"],
        "primary_jobs": ["review a case"],
        "core_capabilities": ["case list", "case decision"],
        "non_goals": ["billing"],
        "primary_workflows": ["open case -> decide -> confirm"],
        "page_navigation_summary": "Queue and case detail",
        "ui_direction": "compact operational UI",
        "technology_profile": "django-5.2-lts",
        "public_interfaces": ["GET /cases", "POST /cases/{id}/decision"],
        "data_boundary": "synthetic local case data",
        "permission_boundary": "single reviewer role",
        "delivery_assumptions": ["local startup"],
        "material_risks": ["incorrect decision persistence"],
        "acceptance_signals": ["decision survives reload"],
        "capabilities": {"security": {"status": "required", "profile": "baseline"}},
        "workload_envelope": {"task_count": "4-6"},
    }

    def test_digest_is_independent_of_dictionary_insertion_order(self) -> None:
        reversed_material = dict(reversed(list(self.MATERIAL.items())))
        self.assertEqual(contract_digest(self.MATERIAL), contract_digest(reversed_material))

    def test_canonical_bytes_use_compact_sorted_utf8_json(self) -> None:
        value = canonical_contract_bytes({"z": "中文", "a": 1})
        self.assertEqual(value, b'{"a":1,"z":"\xe4\xb8\xad\xe6\x96\x87"}')

    def test_extracts_named_contract_json_block(self) -> None:
        import json
        body = json.dumps(self.MATERIAL, ensure_ascii=False, indent=2)
        text = f"# Requirements\n\n## Solution Contract\n\n```json contract-material\n{body}\n```\n"
        self.assertEqual(extract_contract_material(text), self.MATERIAL)

    def test_duplicate_contract_blocks_raise_value_error(self) -> None:
        import json
        body = json.dumps(self.MATERIAL, ensure_ascii=False, indent=2)
        block = f"```json contract-material\n{body}\n```"
        text = f"# Requirements\n\n{block}\n\n{block}\n"
        with self.assertRaises(ValueError):
            extract_contract_material(text)

    def test_missing_contract_block_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            extract_contract_material("# Requirements\n\nNo contract here.\n")

    def test_invalid_json_in_contract_block_raises_value_error(self) -> None:
        text = "# Requirements\n\n```json contract-material\n{not json}\n```\n"
        with self.assertRaisesRegex(ValueError, "contract-material block contains invalid JSON"):
            extract_contract_material(text)

    def test_non_object_json_raises_value_error(self) -> None:
        text = '# Requirements\n\n```json contract-material\n["list", "not", "object"]\n```\n'
        with self.assertRaises(ValueError):
            extract_contract_material(text)

    def test_missing_material_fields_raises_value_error(self) -> None:
        import json
        partial = {"problem": "x"}
        body = json.dumps(partial, ensure_ascii=False, indent=2)
        text = f"# Requirements\n\n```json contract-material\n{body}\n```\n"
        with self.assertRaises(ValueError):
            extract_contract_material(text)
