from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "webbuilder" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from contract_core import (  # noqa: E402
    canonical_contract_bytes,
    contract_digest,
    extract_contract_material,
    material_contract_changed,
)
from state_schema import top_level_value  # noqa: E402

_init_spec = importlib.util.spec_from_file_location(
    "init_state", SCRIPTS / "init-state.py"
)
assert _init_spec is not None and _init_spec.loader is not None
init_state = importlib.util.module_from_spec(_init_spec)
_init_spec.loader.exec_module(init_state)


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


class ContractApprovalTests(unittest.TestCase):
    """Tests for approve-contract.py CLI and material change detection."""

    FULL_CONTRACT = {
        "problem": "Build a web application for task management",
        "desired_outcome": "Users can create, track, and complete tasks",
        "target_users": ["project managers", "developers"],
        "primary_jobs": ["create tasks", "track progress", "complete tasks"],
        "core_capabilities": ["task CRUD", "status tracking", "user assignments"],
        "non_goals": ["time tracking", "invoicing"],
        "primary_workflows": ["create task -> assign -> work -> complete"],
        "page_navigation_summary": "Dashboard -> Projects -> Task Detail",
        "ui_direction": "clean minimal with card-based layout",
        "technology_profile": "react-18 + typescript + vite",
        "public_interfaces": ["GET /api/tasks", "POST /api/tasks"],
        "data_boundary": "user-scoped task data",
        "permission_boundary": "authenticated users only",
        "delivery_assumptions": ["cloud deployment", "CI/CD pipeline"],
        "material_risks": ["data migration complexity"],
        "acceptance_signals": ["task CRUD works end-to-end"],
        "capabilities": {"security": {"status": "required", "profile": "baseline"}},
        "workload_envelope": {
            "task_count": "6-8",
            "browser_flows": ["task creation", "task editing"],
            "external_dependencies": [],
            "quality_gates": ["unit tests", "integration tests"],
            "repair_budgets": {"task": 3, "integration": 5},
            "available_concurrency": "single",
        },
    }

    REQUIREMENTS_TEMPLATE = (
        "# Requirements Baseline\n"
        "\n"
        "## Status\n"
        "\n"
        "status: draft\n"
        "confirmation_status: pending\n"
        "contract_revision: 1\n"
        "approved_contract_revision: null\n"
        "approval_digest: null\n"
        "approval_scope: requirements_design_stack_ui_execution\n"
        "approval_evidence: null\n"
        "approved_by: null\n"
        "approved_at: null\n"
        "discovery_method: inferred_contract\n"
        "\n"
        "## User Discovery\n"
        "\n"
        "discovery_status: confirmed\n"
        "\n"
        "### AI Working Hypothesis\n"
        "\n"
        "- Users need a task management system\n"
        "\n"
        "### Questions Asked\n"
        "\n"
        "- What is the primary use case?\n"
        "\n"
        "### User Decisions\n"
        "\n"
        "- Use React for frontend\n"
        "\n"
        "## Solution Contract\n"
        "\n"
        "```json contract-material\n"
        "{contract_json}\n"
        "```\n"
        "\n"
        "## First-Principles Analysis\n"
        "\n"
        "### Core Outcome\n"
        "\n"
        "- Users can manage tasks efficiently\n"
        "\n"
        "### Hard Constraints and Invariants\n"
        "\n"
        "- Data must persist across sessions\n"
        "\n"
        "### Assumptions and Evidence\n"
        "\n"
        "- Users have modern browsers\n"
        "\n"
        "## Open Questions\n"
        "\n"
        "- None.\n"
        "\n"
        "## Confirmed Requirements\n"
        "\n"
        "| ID | Requirement | Priority | Acceptance Signal |\n"
        "|---|---|---|---|\n"
        "| REQ-001 | Task CRUD operations | Must | Create, read, update, delete tasks |\n"
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_dir = tempfile.mkdtemp()
        cls.target = Path(cls.tmp_dir)

    def setUp(self) -> None:
        state_dir = self.target / "webbuilder"
        if state_dir.exists():
            shutil.rmtree(state_dir)
        init_state.initialize(self.target)
        self.state_dir = state_dir
        self._fill_contract(self.FULL_CONTRACT)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def _fill_contract(self, contract_material: dict) -> None:
        contract_json = json.dumps(contract_material, ensure_ascii=False, indent=2)
        text = self.REQUIREMENTS_TEMPLATE.format(contract_json=contract_json)
        (self.state_dir / "requirements-baseline.md").write_text(
            text, encoding="utf-8", newline="\n"
        )

    def _read(self, filename: str) -> str:
        return (self.state_dir / filename).read_text(encoding="utf-8")

    def _run_approve(self, evidence: str = "user-message-42") -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "approve-contract.py"),
                "--target", str(self.target),
                "--approval-evidence", evidence,
            ],
            capture_output=True,
            text=True,
        )

    def _run_invalidate(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "approve-contract.py"),
                "--target", str(self.target),
                "--invalidate-material-change",
            ],
            capture_output=True,
            text=True,
        )

    def test_approve_sets_confirmation_status_and_metadata(self) -> None:
        result = self._run_approve()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        requirements = self._read("requirements-baseline.md")
        system_design = self._read("system-design.md")
        task_plan = self._read("task-plan.md")
        loop_state = self._read("loop-state.md")

        self.assertIn("confirmation_status: approved", requirements)
        self.assertIn("approved_contract_revision: 1", requirements)
        self.assertRegex(requirements, r"approval_digest: sha256:[0-9a-f]{64}")
        self.assertIn("approved_by: user", requirements)
        self.assertIn("based_on_contract_revision: 1", system_design)
        self.assertIn("based_on_contract_revision: 1", task_plan)
        self.assertIn("autonomy_scope: confirmed_plan", loop_state)
        self.assertEqual(top_level_value(loop_state, "state_revision"), "2")

    def test_second_identical_approval_is_idempotent(self) -> None:
        result = self._run_approve()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        result = self._run_approve()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        requirements = self._read("requirements-baseline.md")
        self.assertIn("contract_revision: 1", requirements)

        loop_state = self._read("loop-state.md")
        self.assertEqual(top_level_value(loop_state, "state_revision"), "2")

    def test_invalidate_material_change_resets_approval(self) -> None:
        result = self._run_approve()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        changed_contract = dict(self.FULL_CONTRACT)
        changed_contract["problem"] = "Completely different problem"
        self._fill_contract(changed_contract)

        result = self._run_invalidate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        requirements = self._read("requirements-baseline.md")
        system_design = self._read("system-design.md")
        task_plan = self._read("task-plan.md")
        loop_state = self._read("loop-state.md")

        self.assertIn("confirmation_status: pending", requirements)
        self.assertIn("contract_revision: 2", requirements)
        self.assertIn("approved_contract_revision: null", requirements)
        self.assertIn("approval_digest: null", requirements)
        self.assertIn("approved_by: null", requirements)
        self.assertIn("approved_at: null", requirements)
        self.assertIn("approval_evidence: null", requirements)
        self.assertIn("based_on_contract_revision: stale", system_design)
        self.assertIn("based_on_contract_revision: stale", task_plan)
        self.assertIn("autonomy_scope: unconfirmed", loop_state)
        self.assertEqual(top_level_value(loop_state, "state_revision"), "3")

    def test_non_material_change_preserves_contract_revision(self) -> None:

        before = dict(self.FULL_CONTRACT)
        after = dict(self.FULL_CONTRACT)
        self.assertFalse(material_contract_changed(before, after))

        changed = dict(self.FULL_CONTRACT)
        changed["problem"] = "Different problem"
        self.assertTrue(material_contract_changed(before, changed))

        result = self._run_approve()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        requirements = self._read("requirements-baseline.md")
        self.assertIn("contract_revision: 1", requirements)
