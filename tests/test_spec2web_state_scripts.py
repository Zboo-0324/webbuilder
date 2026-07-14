from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "webbuilder" / "scripts"
sys.path.insert(0, str(SCRIPTS))
INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
CHECK_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-state.py"
MIGRATE_SCRIPT = ROOT / "webbuilder" / "scripts" / "migrate-state.py"
TRANSITION_SCRIPT = ROOT / "webbuilder" / "scripts" / "transition-state.py"
SKILL_FILE = ROOT / "webbuilder" / "SKILL.md"
LOOP_ENGINEERING_REFERENCE = ROOT / "webbuilder" / "references" / "loop-engineering.md"
TASK_BREAKDOWN_REFERENCE = ROOT / "webbuilder" / "references" / "task-breakdown.md"
STATE_FILES_REFERENCE = ROOT / "webbuilder" / "references" / "state-files.md"
MULTI_AGENT_ORCHESTRATION_REFERENCE = ROOT / "webbuilder" / "references" / "multi-agent-orchestration.md"
INTERFACE_DESIGN_REFERENCE = ROOT / "webbuilder" / "references" / "interface-design.md"
DELIVERY_CHECKLIST_REFERENCE = ROOT / "webbuilder" / "references" / "delivery-checklist.md"
WORKTREE_MODE_REFERENCE = ROOT / "webbuilder" / "references" / "worktree-mode.md"
INSTALL_REFERENCE = ROOT / "webbuilder" / "references" / "install.md"
STATE_DIR_NAME = "webbuilder"

from evidence_core import capture_command_evidence  # noqa: E402
from state_transition import apply_transaction  # noqa: E402


class Spec2WebStateScriptTests(unittest.TestCase):
    def run_init(self, target: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INIT_SCRIPT), "--target", target],
            text=True,
            capture_output=True,
            check=False,
        )

    def run_check(
        self,
        target: str,
        phase: str = "structure",
        task: str | None = None,
        parallel_group: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(CHECK_SCRIPT),
            "--target",
            target,
            "--phase",
            phase,
        ]
        if task:
            command.extend(["--task", task])
        if parallel_group:
            command.extend(["--parallel-group", parallel_group])
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_transition(self, target: str, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TRANSITION_SCRIPT), "--target", target, *arguments],
            text=True,
            capture_output=True,
            check=False,
        )

    def set_loop_values(self, target: str, **values: str) -> None:
        loop_state = Path(target) / STATE_DIR_NAME / "loop-state.md"
        text = loop_state.read_text(encoding="utf-8")
        for key, value in values.items():
            text = re.sub(
                rf"(?m)^{re.escape(key)}:\s*.*$",
                f"{key}: {value}",
                text,
            )
        loop_state.write_text(text, encoding="utf-8")

    def make_execution_ready(self, target: str) -> None:
        state_dir = Path(target) / STATE_DIR_NAME

        replacements = {
            "project-rules.md": [("status: draft", "status: ready")],
            "requirements-baseline.md": [
                ("status: draft", "status: confirmed"),
                ("discovery_status: pending", "discovery_status: confirmed"),
                (
                    "Replace with the first confirmed requirement.",
                    "The application exposes a health endpoint.",
                ),
                ("Replace with verification method.", "Run the API test suite."),
                ("not recorded", "verified for this task"),
            ],
            "system-design.md": [
                ("status: draft", "status: ready"),
                ("not recorded", "not applicable"),
                ("None recorded yet.", "None required."),
                ("Replace with project-specific tradeoffs.", "No migration cost."),
            ],
            "task-plan.md": [
                ("status: draft", "status: ready"),
                ("Replace with first task title", "Add health endpoint"),
                ("Replace with one concrete outcome.", "Expose GET /health."),
                ("replace/with/path", "src/health.py"),
                ("replace with expected output", "GET /health returns 200"),
                ("replace with exact command or manual check", "python -m unittest"),
                (
                    "replace with worker-observable condition for submitting the task",
                    "endpoint and tests are implemented",
                ),
                (
                    "replace with Orchestrator check required before accepting or merging",
                    "tests pass and the diff stays in allowed paths",
                ),
                ("risk_level: unclassified", "risk_level: low"),
                ("not recorded", "localized health endpoint change"),
            ],
        }

        for filename, pairs in replacements.items():
            path = state_dir / filename
            text = path.read_text(encoding="utf-8")
            for old, new in pairs:
                text = text.replace(old, new)
            path.write_text(text, encoding="utf-8")

    def test_init_creates_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(INIT_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            state_dir = Path(tmp) / STATE_DIR_NAME
            self.assertTrue((state_dir / "project-rules.md").exists())
            self.assertTrue((state_dir / "requirements-baseline.md").exists())
            self.assertTrue((state_dir / "system-design.md").exists())
            self.assertTrue((state_dir / "task-plan.md").exists())
            self.assertTrue((state_dir / "loop-state.md").exists())
            self.assertTrue((state_dir / "validation-log.md").exists())
            self.assertTrue((state_dir / "delivery-report.md").exists())

    def test_init_does_not_overwrite_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / STATE_DIR_NAME
            state_dir.mkdir()
            project_rules = state_dir / "project-rules.md"
            project_rules.write_text("custom content", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(INIT_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(project_rules.read_text(encoding="utf-8"), "custom content")
            self.assertIn("exists:", result.stdout)

    def test_check_state_passes_after_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            result = self.run_check(tmp)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("structure phase check passed", result.stdout)

    def test_check_state_fails_without_state_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing state directory", result.stdout)

    def test_init_includes_strategy_interface_and_continuation_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(INIT_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=True,
            )

            state_dir = Path(tmp) / STATE_DIR_NAME
            system_design = (state_dir / "system-design.md").read_text(encoding="utf-8")
            loop_state = (state_dir / "loop-state.md").read_text(encoding="utf-8")

            self.assertIn("## Technology Strategy", system_design)
            self.assertIn("## Interface Design Baseline", system_design)
            self.assertIn("continue ready tasks until blocked or delivered", loop_state)

    def test_init_includes_readiness_statuses_and_repair_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            state_dir = Path(tmp) / STATE_DIR_NAME

            self.assertIn(
                "status: draft",
                (state_dir / "project-rules.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "status: draft",
                (state_dir / "system-design.md").read_text(encoding="utf-8"),
            )
            task_plan = (state_dir / "task-plan.md").read_text(encoding="utf-8")
            self.assertIn("status: draft", task_plan)
            self.assertIn("repair_budget: 3", task_plan)

    def test_init_includes_v13_orchestration_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            state_dir = Path(tmp) / STATE_DIR_NAME
            loop_state = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            task_plan = (state_dir / "task-plan.md").read_text(encoding="utf-8")

            self.assertIn("schema_version: 1.4", loop_state)
            self.assertIn("execution_mode: single", loop_state)
            self.assertIn("host_agent_capability: unknown", loop_state)
            self.assertIn("available_child_slots: unknown", loop_state)
            self.assertIn("selected_workers: 0", loop_state)
            self.assertIn("active_checker_strategy: single_session", loop_state)
            self.assertIn("## Shared Contract Paths", task_plan)

    def test_init_creates_schema_1_4_runtime_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            state_dir = Path(tmp) / STATE_DIR_NAME
            loop = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            for marker in (
                "schema_version: 1.4",
                "delivery_mode: guided",
                "autonomy_scope: unconfirmed",
                "stop_reason: none",
                "resume_checkpoint: none",
                "active_run_id: null",
                "state_revision: 1",
                "pending_transition: null",
            ):
                self.assertIn(marker, loop)

            requirements = (state_dir / "requirements-baseline.md").read_text(
                encoding="utf-8"
            )
            system_design = (state_dir / "system-design.md").read_text(
                encoding="utf-8"
            )
            task_plan = (state_dir / "task-plan.md").read_text(encoding="utf-8")
            for marker in (
                "confirmation_status: pending",
                "contract_revision: 1",
                "approved_contract_revision: null",
                "approval_digest: null",
                "approval_scope: requirements_design_stack_ui_execution",
                "approval_evidence: null",
                "approved_by: null",
                "approved_at: null",
                "discovery_method: interactive",
                "## Solution Contract",
                "```json contract-material",
            ):
                self.assertIn(marker, requirements)
            self.assertIn("based_on_contract_revision: 1", system_design)
            self.assertIn("based_on_contract_revision: 1", task_plan)

    def test_init_creates_and_preserves_state_gitignore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "--quiet", tmp], check=True)
            self.assertEqual(self.run_init(tmp).returncode, 0)
            state_dir = Path(tmp) / STATE_DIR_NAME
            gitignore = state_dir / ".gitignore"

            self.assertEqual(
                subprocess.run(
                    ["git", "-C", tmp, "check-ignore", "-q", "webbuilder/.transitions/"],
                    check=False,
                ).returncode,
                0,
            )
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", tmp, "check-ignore", "-q", "webbuilder/.migration-backup-test/"],
                    check=False,
                ).returncode,
                0,
            )

            gitignore.write_text("custom-ignore/\n", encoding="utf-8")
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.assertEqual(gitignore.read_text(encoding="utf-8"), "custom-ignore/\n")

    def test_structure_check_requires_schema_1_4_runtime_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            loop_state = Path(tmp) / STATE_DIR_NAME / "loop-state.md"
            loop_state.write_text(
                loop_state.read_text(encoding="utf-8").replace(
                    "delivery_mode: guided\n", ""
                ),
                encoding="utf-8",
            )

            result = self.run_check(tmp)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("loop-state.md missing marker: delivery_mode:", result.stdout)

    def test_structure_check_requires_solution_contract_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            requirements = Path(tmp) / STATE_DIR_NAME / "requirements-baseline.md"
            requirements.write_text(
                requirements.read_text(encoding="utf-8").replace(
                    "confirmation_status: pending\n", ""
                ),
                encoding="utf-8",
            )

            result = self.run_check(tmp)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "requirements-baseline.md missing marker: confirmation_status:",
                result.stdout,
            )

    def test_execution_check_rejects_initialized_draft_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)

            result = self.run_check(tmp, "execution")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requirements-baseline.md status must be confirmed", result.stdout)
            self.assertIn("task-plan.md contains placeholder content", result.stdout)

    def test_execution_check_passes_ready_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)

            result = self.run_check(tmp, "execution")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("execution phase check passed", result.stdout)

    def test_task_gate_passes_for_single_session_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8")
                .replace("handoff_mode: pr_worktree", "handoff_mode: single_session")
                .replace("integration_strategy: squash_merge", "integration_strategy: direct_apply"),
                encoding="utf-8",
            )
            self.set_loop_values(tmp, current_task="TASK-001")

            result = self.run_check(tmp, "task", task="TASK-001")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("task phase check passed", result.stdout)

    def test_task_gate_rejects_incomplete_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8")
            first_task = text[text.index("### TASK-001") :]
            second_task = (
                first_task.replace("TASK-001", "TASK-002")
                .replace("dependencies: none", "dependencies: TASK-001")
                .replace("src/health.py", "src/metrics.py")
            )
            task_plan.write_text(text + "\n" + second_task, encoding="utf-8")
            self.set_loop_values(tmp, current_task="TASK-002")

            result = self.run_check(tmp, "task", task="TASK-002")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("TASK-002 dependency is not complete: TASK-001", result.stdout)

    def test_task_gate_passes_for_delegated_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8").replace(
                    "execution_workspace: main",
                    "execution_workspace: ../app-TASK-001",
                )
                .replace("risk_level: low", "risk_level: standard")
                .replace(
                    "checker_strategy: single_session",
                    "checker_strategy: independent_checker",
                ),
                encoding="utf-8",
            )
            self.set_loop_values(
                tmp,
                current_task="TASK-001",
                execution_mode="delegated",
                host_agent_capability="available",
                available_child_slots="2",
                selected_workers="1",
                active_checker_strategy="independent_checker",
            )

            result = self.run_check(tmp, "task", task="TASK-001")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_parallel_gate_passes_for_no_conflict_group(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8")
            first_task = text[text.index("### TASK-001") :]
            first_task = (
                first_task.replace("execution_workspace: main", "execution_workspace: ../app-TASK-001")
                .replace("parallel_group: none", "parallel_group: PG-001")
                .replace(
                    "checker_strategy: single_session",
                    "checker_strategy: independent_checker",
                )
            )
            second_task = (
                first_task.replace("TASK-001", "TASK-002")
                .replace("src/health.py", "src/metrics.py")
                .replace("GET /health", "GET /metrics")
            )
            prefix = text[: text.index("### TASK-001")]
            task_plan.write_text(prefix + first_task + "\n" + second_task, encoding="utf-8")
            self.set_loop_values(
                tmp,
                execution_mode="parallel",
                host_agent_capability="available",
                available_child_slots="3",
                selected_workers="2",
                active_checker_strategy="mixed",
                active_parallel_group="PG-001",
            )

            result = self.run_check(tmp, "parallel", parallel_group="PG-001")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("parallel phase check passed", result.stdout)

    def test_parallel_gate_rejects_overlapping_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8")
            first_task = text[text.index("### TASK-001") :]
            first_task = (
                first_task.replace("execution_workspace: main", "execution_workspace: ../app-TASK-001")
                .replace("parallel_group: none", "parallel_group: PG-001")
            )
            second_task = first_task.replace("TASK-001", "TASK-002")
            prefix = text[: text.index("### TASK-001")]
            task_plan.write_text(prefix + first_task + "\n" + second_task, encoding="utf-8")
            self.set_loop_values(
                tmp,
                execution_mode="parallel",
                host_agent_capability="available",
                available_child_slots="2",
                selected_workers="2",
                checker_strategy="independent_checker",
                active_parallel_group="PG-001",
            )

            result = self.run_check(tmp, "parallel", parallel_group="PG-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("allowed_paths overlap", result.stdout)

    def test_parallel_gate_rejects_shared_contract_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8")
            first_task = text[text.index("### TASK-001") :]
            first_task = (
                first_task.replace("src/health.py", "webbuilder/system-design.md")
                .replace("execution_workspace: main", "execution_workspace: ../app-TASK-001")
                .replace("parallel_group: none", "parallel_group: PG-001")
            )
            second_task = (
                first_task.replace("TASK-001", "TASK-002")
                .replace("webbuilder/system-design.md", "src/metrics.py")
            )
            prefix = text[: text.index("### TASK-001")]
            task_plan.write_text(prefix + first_task + "\n" + second_task, encoding="utf-8")
            self.set_loop_values(
                tmp,
                execution_mode="parallel",
                host_agent_capability="available",
                available_child_slots="2",
                selected_workers="2",
                checker_strategy="independent_checker",
                active_parallel_group="PG-001",
            )

            result = self.run_check(tmp, "parallel", parallel_group="PG-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("intersects shared contract path", result.stdout)

    def test_parallel_gate_rejects_wildcard_path_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8")
            first_task = text[text.index("### TASK-001") :]
            first_task = (
                first_task.replace("src/health.py", "src/health*")
                .replace("execution_workspace: main", "execution_workspace: ../app-TASK-001")
                .replace("parallel_group: none", "parallel_group: PG-001")
            )
            second_task = (
                first_task.replace("TASK-001", "TASK-002")
                .replace("src/health*", "src/health_test.py")
            )
            prefix = text[: text.index("### TASK-001")]
            task_plan.write_text(prefix + first_task + "\n" + second_task, encoding="utf-8")
            self.set_loop_values(
                tmp,
                execution_mode="parallel",
                host_agent_capability="available",
                available_child_slots="2",
                selected_workers="2",
                checker_strategy="independent_checker",
                active_parallel_group="PG-001",
            )

            result = self.run_check(tmp, "parallel", parallel_group="PG-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("allowed_paths overlap", result.stdout)

    def test_acceptance_allows_one_independent_checker_for_standard_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME
            task_plan = state_dir / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8")
            text = text.replace("status: pending", "status: submitted_for_acceptance")
            text = text.replace(
                "checker_strategy: single_session", "checker_strategy: independent_checker"
            )
            task_plan.write_text(text, encoding="utf-8")
            (state_dir / "validation-log.md").write_text(
                "# Validation Log\n\n## Entries\n\n### TASK-001 / acceptance\n\n"
                "- gate: acceptance\n- task_status: submitted_for_acceptance\n"
                "- submission_commit: direct_apply\n- developer_identity: developer\n"
                "- tester_identity: checker\n- tester_result: passed\n"
                "- reviewer_identity: checker\n- reviewer_result: approved\n"
                "- adversarial_cases_expected: not_applicable\n"
                "- adversarial_cases_passed: not_applicable\n"
                "- disagreement_status: none\n- orchestrator_decision: accepted\n"
                "- residual_risk: none\n",
                encoding="utf-8",
            )

            result = self.run_check(tmp, "acceptance", task="TASK-001")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_acceptance_requires_three_identities_for_separate_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME
            task_plan = state_dir / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8")
            text = text.replace("status: pending", "status: submitted_for_acceptance")
            text = text.replace("risk_level: low", "risk_level: high")
            text = text.replace(
                "checker_strategy: single_session",
                "checker_strategy: separate_tester_reviewer",
            )
            text = text.replace("review_mode: standard", "review_mode: adversarial")
            text = text.replace("  - not_applicable", "  - CASE-001", 1)
            task_plan.write_text(text, encoding="utf-8")
            (state_dir / "validation-log.md").write_text(
                "# Validation Log\n\n## Entries\n\n### TASK-001 / acceptance\n\n"
                "- gate: acceptance\n- task_status: submitted_for_acceptance\n"
                "- submission_commit: abc123\n- developer_identity: developer\n"
                "- tester_identity: checker\n- tester_result: passed\n"
                "- reviewer_identity: checker\n- reviewer_result: approved\n"
                "- adversarial_cases_expected: CASE-001\n"
                "- adversarial_cases_passed: CASE-001\n"
                "- disagreement_status: none\n- orchestrator_decision: accepted\n"
                "- residual_risk: none\n",
                encoding="utf-8",
            )

            result = self.run_check(tmp, "acceptance", task="TASK-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "separate_tester_reviewer requires distinct identities", result.stdout
            )

    def test_acceptance_rejects_placeholder_developer_for_high_risk_separation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME
            task_plan = state_dir / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8")
            text = text.replace("status: pending", "status: submitted_for_acceptance")
            text = text.replace("risk_level: low", "risk_level: high")
            text = text.replace(
                "checker_strategy: single_session",
                "checker_strategy: separate_tester_reviewer",
            )
            text = text.replace("review_mode: standard", "review_mode: adversarial")
            text = text.replace("  - not_applicable", "  - CASE-001", 1)
            task_plan.write_text(text, encoding="utf-8")
            (state_dir / "validation-log.md").write_text(
                "# Validation Log\n\n## Entries\n\n### TASK-001 / acceptance\n\n"
                "- gate: acceptance\n- task_status: submitted_for_acceptance\n"
                "- submission_commit: abc123\n- developer_identity: none\n"
                "- tester_identity: checker\n- tester_result: passed\n"
                "- reviewer_identity: checker\n- reviewer_result: approved\n"
                "- adversarial_cases_expected: CASE-001\n"
                "- adversarial_cases_passed: CASE-001\n"
                "- disagreement_status: none\n- orchestrator_decision: accepted\n"
                "- residual_risk: none\n",
                encoding="utf-8",
            )

            result = self.run_check(tmp, "acceptance", task="TASK-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "acceptance developer_identity must be usable evidence", result.stdout
            )

    def test_acceptance_rejects_independent_checker_for_high_risk_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME
            task_plan = state_dir / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8")
            text = text.replace("status: pending", "status: submitted_for_acceptance")
            text = text.replace("risk_level: low", "risk_level: high")
            text = text.replace(
                "checker_strategy: single_session", "checker_strategy: independent_checker"
            )
            text = text.replace("review_mode: standard", "review_mode: adversarial")
            text = text.replace("  - not_applicable", "  - CASE-001", 1)
            task_plan.write_text(text, encoding="utf-8")
            (state_dir / "validation-log.md").write_text(
                "# Validation Log\n\n## Entries\n\n### TASK-001 / acceptance\n\n"
                "- gate: acceptance\n- task_status: submitted_for_acceptance\n"
                "- submission_commit: abc123\n- developer_identity: developer\n"
                "- tester_identity: checker\n- tester_result: passed\n"
                "- reviewer_identity: checker\n- reviewer_result: approved\n"
                "- adversarial_cases_expected: CASE-001\n"
                "- adversarial_cases_passed: CASE-001\n"
                "- disagreement_status: none\n- orchestrator_decision: accepted\n"
                "- residual_risk: none\n",
                encoding="utf-8",
            )

            result = self.run_check(tmp, "acceptance", task="TASK-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "high-risk work requires separate Tester and Reviewer", result.stdout
            )

    def test_integration_gate_requires_main_workspace_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME
            task_plan = state_dir / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8")
                .replace("status: pending", "status: accepted")
                .replace("handoff_mode: pr_worktree", "handoff_mode: single_session")
                .replace("integration_strategy: squash_merge", "integration_strategy: direct_apply"),
                encoding="utf-8",
            )
            (state_dir / "validation-log.md").write_text(
                "# Validation Log\n\n## Entries\n\n### TASK-001 / integration\n\n"
                "- gate: integration\n- integration_strategy: direct_apply\n"
                "- integration_commit: direct_apply\n"
                "- main_workspace_verification: passed\n"
                "- verification_evidence: python -m unittest\n"
                "- final_task_status: complete\n",
                encoding="utf-8",
            )

            passed = self.run_check(tmp, "integration", task="TASK-001")

            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            log = state_dir / "validation-log.md"
            log.write_text(
                log.read_text(encoding="utf-8").replace(
                    "main_workspace_verification: passed",
                    "main_workspace_verification: failed",
                ),
                encoding="utf-8",
            )
            rejected = self.run_check(tmp, "integration", task="TASK-001")
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("main_workspace_verification must be passed", rejected.stdout)

    def test_parallel_gate_rejects_shared_resource_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8")
            first_task = (
                text[text.index("### TASK-001") :]
                .replace("execution_workspace: main", "execution_workspace: ../app-TASK-001")
                .replace("parallel_group: none", "parallel_group: PG-001")
                .replace(
                    "checker_strategy: single_session",
                    "checker_strategy: independent_checker",
                )
                .replace("shared_resources:\n  - none", "shared_resources:\n  - database:app")
            )
            second_task = (
                first_task.replace("TASK-001", "TASK-002")
                .replace("src/health.py", "src/metrics.py")
                .replace("GET /health", "GET /metrics")
            )
            task_plan.write_text(
                text[: text.index("### TASK-001")] + first_task + "\n" + second_task,
                encoding="utf-8",
            )
            self.set_loop_values(
                tmp,
                execution_mode="parallel",
                host_agent_capability="available",
                available_child_slots="2",
                selected_workers="2",
                active_checker_strategy="mixed",
                active_parallel_group="PG-001",
            )

            result = self.run_check(tmp, "parallel", parallel_group="PG-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shared_resources conflict: database:app", result.stdout)

    def test_task_gate_blocks_repeated_task_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8")
                .replace("task_repair_attempt: 0", "task_repair_attempt: 2")
                .replace(
                    "task_same_fingerprint_count: 0",
                    "task_same_fingerprint_count: 3",
                ),
                encoding="utf-8",
            )
            self.set_loop_values(tmp, current_task="TASK-001")

            result = self.run_check(tmp, "task", task="TASK-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "repeated task failure fingerprint requires block", result.stdout
            )

    def test_task_gate_rejects_unicode_repair_counter_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8").replace(
                    "task_repair_attempt: 0",
                    "task_repair_attempt: \N{SUPERSCRIPT TWO}",
                ),
                encoding="utf-8",
            )
            self.set_loop_values(tmp, current_task="TASK-001")

            result = self.run_check(tmp, "task", task="TASK-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "task_repair_attempt must be a non-negative integer", result.stdout
            )
            self.assertNotIn("Traceback", result.stderr)

    def test_integration_gate_enforces_its_own_repair_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME
            task_plan = state_dir / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8")
                .replace("status: pending", "status: accepted")
                .replace("handoff_mode: pr_worktree", "handoff_mode: single_session")
                .replace(
                    "integration_strategy: squash_merge",
                    "integration_strategy: direct_apply",
                )
                .replace("task_repair_attempt: 0", "task_repair_attempt: 2")
                .replace(
                    "integration_repair_attempt: 0",
                    "integration_repair_attempt: 6",
                ),
                encoding="utf-8",
            )
            (state_dir / "validation-log.md").write_text(
                "# Validation Log\n\n## Entries\n\n### TASK-001 / integration\n\n"
                "- gate: integration\n- integration_strategy: direct_apply\n"
                "- integration_commit: direct_apply\n"
                "- main_workspace_verification: passed\n"
                "- verification_evidence: python -m unittest\n"
                "- final_task_status: complete\n",
                encoding="utf-8",
            )

            result = self.run_check(tmp, "integration", task="TASK-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("integration_repair_attempt exceeds budget 5", result.stdout)

    def test_delivery_check_requires_terminal_state_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)

            result = self.run_check(tmp, "delivery")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("loop-state.md status must be delivered", result.stdout)
            self.assertIn("validation-log.md has no validation entries", result.stdout)

    def test_delivery_check_passes_completed_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME

            task_plan = state_dir / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8")
                .replace("status: ready", "status: completed", 1)
                .replace("- status: pending", "- status: complete"),
                encoding="utf-8",
            )

            loop_state = state_dir / "loop-state.md"
            loop_state.write_text(
                loop_state.read_text(encoding="utf-8")
                .replace("status: active", "status: delivered")
                .replace("current_phase: project_rules", "current_phase: delivery"),
                encoding="utf-8",
            )

            (state_dir / "delivery-report.md").write_text(
                "# Delivery Report\n\nstatus: complete\n\n## Completed\n\n"
                "- REQ-001 health endpoint.\n\n## Validation\n\n- Tests passed.\n\n"
                "## Run Instructions\n\n- python app.py\n\n## Known Risks\n\n- None.\n\n"
                "## Not Completed\n\n- None.\n",
                encoding="utf-8",
            )

            # Create real evidence manifests AFTER all state modifications
            # so the implementation fingerprint matches the current project state.
            # Must use the same allowed_paths as task-plan.md (src/health.py).
            from evidence_core import capture_command_evidence

            project_root = Path(tmp)
            (project_root / "src").mkdir(exist_ok=True)
            (project_root / "src" / "health.py").write_text("# health\n", encoding="utf-8")
            domain_entries = []
            for domain in ("functional", "security", "performance", "delivery-smoke"):
                manifest_path = capture_command_evidence(
                    project_root,
                    [sys.executable, "-c", "print('ok')"],
                    run_id="DELIVERY",
                    subject_id=domain,
                    attempt=1,
                    contract_revision=1,
                    allowed_paths=["src/health.py"],
                )
                rel_path = manifest_path.relative_to(project_root).as_posix()
                domain_entries.append(
                    f"\n### PROJECT / {domain}\n\n"
                    f"- artifact_manifest: {rel_path}\n"
                )

            (state_dir / "validation-log.md").write_text(
                "# Validation Log\n\n## Entries\n\n### TASK-001 / acceptance\n\n"
                "- gate: acceptance\n- task_status: submitted_for_acceptance\n"
                "- submission_commit: direct_apply\n- developer_identity: developer\n"
                "- tester_identity: tester\n- tester_result: passed\n"
                "- reviewer_identity: reviewer\n- reviewer_result: approved\n"
                "- adversarial_cases_expected: not_applicable\n"
                "- adversarial_cases_passed: not_applicable\n"
                "- disagreement_status: none\n- orchestrator_decision: accepted\n"
                "- residual_risk: none\n\n### TASK-001 / integration\n\n"
                "- gate: integration\n- integration_strategy: squash_merge\n"
                "- integration_commit: abc1234\n"
                "- main_workspace_verification: passed\n"
                "- verification_evidence: python -m unittest\n"
                "- final_task_status: complete\n"
                + "".join(domain_entries),
                encoding="utf-8",
            )

            result = self.run_check(tmp, "delivery")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("delivery phase check passed", result.stdout)

    def test_transition_rejects_unknown_events_without_writing_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            loop_state = Path(tmp) / STATE_DIR_NAME / "loop-state.md"
            before = loop_state.read_text(encoding="utf-8")

            result = self.run_transition(
                tmp,
                "--event",
                "anything",
                "--set",
                "loop-state.md:status=delivered",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported transition event: anything", result.stdout)
            self.assertEqual(loop_state.read_text(encoding="utf-8"), before)

    def test_transition_rejects_arbitrary_control_updates(self) -> None:
        for update in (
            "loop-state.md:status=delivered",
            "loop-state.md:state_revision=2",
            "task-plan.md:user_approval=approved",
        ):
            with self.subTest(update=update), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(self.run_init(tmp).returncode, 0)
                state_dir = Path(tmp) / STATE_DIR_NAME
                before = {
                    path.name: path.read_text(encoding="utf-8")
                    for path in state_dir.iterdir()
                    if path.is_file()
                }

                result = self.run_transition(
                    tmp,
                    "--event",
                    "edit-descriptive-content",
                    "--set",
                    update,
                )

                name, key_value = update.split(":", maxsplit=1)
                key = key_value.split("=", maxsplit=1)[0]
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"may not set control value: {name}:{key}", result.stdout)
                self.assertEqual(
                    (state_dir / name).read_text(encoding="utf-8"), before[name]
                )

    def test_transition_rejects_line_breaks_in_descriptive_updates(self) -> None:
        cases = (
            "loop-state.md\n:note=ordinary",
            "loop-state.md:no\nte=ordinary",
            "loop-state.md:note=ordinary\nstatus: delivered",
            "loop-state.md\r:note=ordinary",
            "loop-state.md:no\rte=ordinary",
            "loop-state.md:note=ordinary\rstatus: delivered",
        )
        for update in cases:
            with self.subTest(update=repr(update)), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(self.run_init(tmp).returncode, 0)
                loop_state = Path(tmp) / STATE_DIR_NAME / "loop-state.md"
                before = loop_state.read_bytes()

                result = self.run_transition(
                    tmp,
                    "--event",
                    "edit-descriptive-content",
                    "--set",
                    update,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("line breaks are not allowed", result.stdout)
                self.assertEqual(loop_state.read_bytes(), before)

    def test_transition_allows_descriptive_content_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            design = Path(tmp) / STATE_DIR_NAME / "system-design.md"

            result = self.run_transition(
                tmp,
                "--event",
                "edit-descriptive-content",
                "--set",
                "system-design.md:custom_note=recorded",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("custom_note: recorded", design.read_text(encoding="utf-8"))

    def test_transition_preserves_literal_backslashes_in_descriptive_updates(self) -> None:
        for value in (
            "ordinary\\nstatus: delivered",
            "ordinary\\rstatus: delivered",
        ):
            with self.subTest(value=repr(value)), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(self.run_init(tmp).returncode, 0)
                loop_state = Path(tmp) / STATE_DIR_NAME / "loop-state.md"
                seeded = self.run_transition(
                    tmp,
                    "--event",
                    "edit-descriptive-content",
                    "--set",
                    "loop-state.md:note=seed",
                )
                self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)

                result = self.run_transition(
                    tmp,
                    "--event",
                    "edit-descriptive-content",
                    "--set",
                    f"loop-state.md:note={value}",
                )

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                text = loop_state.read_text(encoding="utf-8")
                self.assertIn(f"note: {value}", text)
                self.assertEqual(re.findall(r"(?m)^status:\s*(.+)$", text), ["active"])

    def test_readiness_transitions_reject_incomplete_artifacts(self) -> None:
        cases = (
            (
                "mark-project-rules-ready",
                (),
                "project-rules.md Sources Read checklist has unchecked entries",
                "project-rules.md",
            ),
            (
                "confirm-requirements",
                ("requirements-baseline.md:discovery_status=confirmed",),
                "requirements-baseline.md contains placeholder content",
                "requirements-baseline.md",
            ),
            (
                "mark-system-design-ready",
                (),
                "system-design.md contains placeholder content",
                "system-design.md",
            ),
            (
                "mark-task-plan-ready",
                (),
                "task-plan.md contains placeholder content",
                "task-plan.md",
            ),
        )
        for event, setup, expected, filename in cases:
            with self.subTest(event=event), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(self.run_init(tmp).returncode, 0)
                state_dir = Path(tmp) / STATE_DIR_NAME
                for replacement in setup:
                    name, key_value = replacement.split(":", maxsplit=1)
                    key, value = key_value.split("=", maxsplit=1)
                    path = state_dir / name
                    path.write_text(
                        re.sub(
                            rf"(?m)^{re.escape(key)}:\s*.*$",
                            f"{key}: {value}",
                            path.read_text(encoding="utf-8"),
                        ),
                        encoding="utf-8",
                    )
                target = state_dir / filename
                before = target.read_bytes()

                result = self.run_transition(tmp, "--event", event)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stdout)
                self.assertEqual(target.read_bytes(), before)

    def test_confirm_user_discovery_rejects_an_invalid_state_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            requirements = Path(tmp) / STATE_DIR_NAME / "requirements-baseline.md"
            requirements.write_text(
                requirements.read_text(encoding="utf-8")
                .replace("- not recorded", "- recorded")
                .replace("## First-Principles Analysis", "## Missing Analysis"),
                encoding="utf-8",
            )
            before = requirements.read_bytes()

            result = self.run_transition(tmp, "--event", "confirm-user-discovery")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "requirements-baseline.md missing marker: ## First-Principles Analysis",
                result.stdout,
            )
            self.assertEqual(requirements.read_bytes(), before)

    def test_accept_task_transition_requires_submitted_source_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME
            task_plan = state_dir / "task-plan.md"
            before = task_plan.read_text(encoding="utf-8")

            result = self.run_transition(tmp, "--event", "accept-task", "--task", "TASK-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("TASK-001 status must be submitted_for_acceptance", result.stdout)
            self.assertEqual(task_plan.read_text(encoding="utf-8"), before)

    def test_accept_task_transition_rejects_missing_acceptance_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME
            task_plan = state_dir / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8").replace(
                    "status: pending", "status: submitted_for_acceptance"
                ),
                encoding="utf-8",
            )

            result = self.run_transition(tmp, "--event", "accept-task", "--task", "TASK-001")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("validation-log.md missing TASK-001 / acceptance record", result.stdout)
            self.assertIn("status: submitted_for_acceptance", task_plan.read_text(encoding="utf-8"))

    def test_accept_task_transition_constructs_accepted_status_after_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME
            task_plan = state_dir / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8").replace(
                    "status: pending", "status: submitted_for_acceptance"
                ),
                encoding="utf-8",
            )
            (state_dir / "validation-log.md").write_text(
                "# Validation Log\n\n## Entries\n\n### TASK-001 / acceptance\n\n"
                "- gate: acceptance\n- task_status: submitted_for_acceptance\n"
                "- submission_commit: direct_apply\n- developer_identity: developer\n"
                "- tester_identity: checker\n- tester_result: passed\n"
                "- reviewer_identity: checker\n- reviewer_result: approved\n"
                "- adversarial_cases_expected: not_applicable\n"
                "- adversarial_cases_passed: not_applicable\n"
                "- disagreement_status: none\n- orchestrator_decision: accepted\n"
                "- residual_risk: none\n",
                encoding="utf-8",
            )

            result = self.run_transition(tmp, "--event", "accept-task", "--task", "TASK-001")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("status: accepted", task_plan.read_text(encoding="utf-8"))

    def test_all_phase_gates_reject_an_interrupted_journal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            state_dir = Path(tmp) / STATE_DIR_NAME
            validation_log = state_dir / "validation-log.md"
            with self.assertRaises(RuntimeError):
                apply_transaction(
                    state_dir,
                    "test-interruption",
                    {"validation-log.md": validation_log.read_text(encoding="utf-8") + "\n"},
                    expected_revision=1,
                    fail_after_replacements=1,
                )
            self.assertEqual(len(list((state_dir / ".transitions").glob("*.json"))), 1)

            for phase, task, group in (
                ("execution", None, None),
                ("task", "TASK-001", None),
                ("parallel", None, "PG-001"),
                ("acceptance", "TASK-001", None),
                ("integration", "TASK-001", None),
                ("delivery", None, None),
            ):
                with self.subTest(phase=phase):
                    result = self.run_check(tmp, phase, task=task, parallel_group=group)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("pending_transition", result.stdout)

    def test_structure_validates_runtime_domains_and_journal_agreement(self) -> None:
        cases = (
            ("delivery_mode", "autonomous", "delivery_mode must be one of: guided"),
            ("autonomy_scope", "confirmed", "autonomy_scope must be one of:"),
            ("stop_reason", "unsupported", "stop_reason must be one of:"),
            ("resume_checkpoint", "unknown", "resume_checkpoint must be none"),
            ("active_run_id", "RUN-001", "active_run_id must be null"),
            ("state_revision", "one", "state_revision must be a non-negative integer"),
            (
                "pending_transition",
                "TX-missing",
                "pending_transition does not match a pending transition journal",
            ),
        )
        for field, value, expected in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(self.run_init(tmp).returncode, 0)
                self.set_loop_values(tmp, **{field: value})

                result = self.run_check(tmp)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stdout)

    def test_delivery_rejects_unresolved_stop_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.make_execution_ready(tmp)
            state_dir = Path(tmp) / STATE_DIR_NAME

            task_plan = state_dir / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8").replace(
                    "- status: pending", "- status: complete"
                ),
                encoding="utf-8",
            )
            loop_state = state_dir / "loop-state.md"
            loop_state.write_text(
                loop_state.read_text(encoding="utf-8")
                .replace("status: active", "status: delivered")
                .replace("current_phase: project_rules", "current_phase: delivery")
                .replace("stop_reason: none", "stop_reason: environment_blocked"),
                encoding="utf-8",
            )
            (state_dir / "validation-log.md").write_text(
                "# Validation Log\n\n## Entries\n\n### TASK-001 / acceptance\n\n"
                "- gate: acceptance\n- task_status: submitted_for_acceptance\n"
                "- submission_commit: direct_apply\n- developer_identity: developer\n"
                "- tester_identity: tester\n- tester_result: passed\n"
                "- reviewer_identity: reviewer\n- reviewer_result: approved\n"
                "- adversarial_cases_expected: not_applicable\n"
                "- adversarial_cases_passed: not_applicable\n"
                "- disagreement_status: none\n- orchestrator_decision: accepted\n"
                "- residual_risk: none\n\n### TASK-001 / integration\n\n"
                "- gate: integration\n- integration_strategy: squash_merge\n"
                "- integration_commit: abc1234\n"
                "- main_workspace_verification: passed\n"
                "- verification_evidence: python -m unittest\n"
                "- final_task_status: complete\n",
                encoding="utf-8",
            )
            (state_dir / "delivery-report.md").write_text(
                "# Delivery Report\n\nstatus: complete\n\n## Completed\n\n"
                "- REQ-001 health endpoint.\n\n## Validation\n\n- Tests passed.\n\n"
                "## Run Instructions\n\n- python app.py\n\n## Known Risks\n\n- None.\n\n"
                "## Not Completed\n\n- None.\n",
                encoding="utf-8",
            )

            result = self.run_check(tmp, "delivery")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("stop_reason must be none for delivery", result.stdout)

    def test_check_state_requires_strategy_and_interface_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(INIT_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=True,
            )

            system_design = Path(tmp) / STATE_DIR_NAME / "system-design.md"
            text = system_design.read_text(encoding="utf-8")
            system_design.write_text(
                text.replace("## Technology Strategy", "## Missing Technology Strategy"),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("system-design.md missing marker: ## Technology Strategy", result.stdout)

    def test_structure_check_rejects_invalid_artifact_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            project_rules = Path(tmp) / STATE_DIR_NAME / "project-rules.md"
            project_rules.write_text(
                project_rules.read_text(encoding="utf-8").replace(
                    "status: draft", "status: complete"
                ),
                encoding="utf-8",
            )

            result = self.run_check(tmp)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "project-rules.md status must be one of: draft, ready",
                result.stdout,
            )

    def test_structure_check_rejects_incomplete_task_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8").replace(
                    "- repair_budget: 3", "- omitted_repair_budget: 3"
                ),
                encoding="utf-8",
            )

            result = self.run_check(tmp)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("TASK-001 missing field: repair_budget", result.stdout)

    def test_single_session_requires_direct_apply_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            task_plan = Path(tmp) / STATE_DIR_NAME / "task-plan.md"
            text = task_plan.read_text(encoding="utf-8").replace(
                "handoff_mode: pr_worktree", "handoff_mode: single_session"
            )
            task_plan.write_text(text, encoding="utf-8")

            invalid = self.run_check(tmp)

            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn(
                "single_session handoff requires integration_strategy: direct_apply",
                invalid.stdout,
            )

            task_plan.write_text(
                text.replace(
                    "integration_strategy: squash_merge",
                    "integration_strategy: direct_apply",
                ),
                encoding="utf-8",
            )
            valid = self.run_check(tmp)

            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

    def test_migrate_state_upgrades_v1_without_overwriting_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            state_dir = Path(tmp) / STATE_DIR_NAME
            loop_state = state_dir / "loop-state.md"
            task_plan = state_dir / "task-plan.md"
            requirements_baseline = state_dir / "requirements-baseline.md"
            system_design = state_dir / "system-design.md"

            loop_text = loop_state.read_text(encoding="utf-8")
            loop_text = re.sub(
                r"(?m)^(schema_version|execution_mode|host_agent_capability|"
                r"available_child_slots|selected_workers|checker_strategy):.*\n",
                "",
                loop_text,
            )
            loop_text = loop_text.replace(
                "unauthorized external AI workers are forbidden",
                "external AI workers are forbidden",
            )
            loop_text = loop_text.replace(
                "delegated or parallel tasks use PR/worktree handoff when Git is available",
                "implementation tasks use PR/worktree handoff when Git is available",
            )
            loop_state.write_text(loop_text + "\ncustom-note: preserve-me\n", encoding="utf-8")

            plan_text = task_plan.read_text(encoding="utf-8")
            plan_text = re.sub(
                r"(?ms)^## Shared Contract Paths\n.*?(?=^## Tasks)",
                "",
                plan_text,
            )
            plan_text = plan_text.replace("based_on_contract_revision: 1\n", "")
            task_plan.write_text(plan_text, encoding="utf-8")

            requirements_text = requirements_baseline.read_text(encoding="utf-8")
            requirements_text = re.sub(
                r"(?m)^(confirmation_status|contract_revision|"
                r"approved_contract_revision|approval_digest|approval_scope|"
                r"approval_evidence|approved_by|approved_at|discovery_method):.*\n",
                "",
                requirements_text,
            )
            requirements_text = re.sub(
                r"(?ms)^## Solution Contract\n.*?^```\n\n?",
                "",
                requirements_text,
            )
            requirements_baseline.write_text(requirements_text, encoding="utf-8")
            system_design.write_text(
                system_design.read_text(encoding="utf-8").replace(
                    "based_on_contract_revision: 1\n", ""
                ),
                encoding="utf-8",
            )

            before_loop = loop_state.read_text(encoding="utf-8")
            dry_run = subprocess.run(
                [sys.executable, str(MIGRATE_SCRIPT), "--target", tmp, "--dry-run"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stdout + dry_run.stderr)
            self.assertEqual(loop_state.read_text(encoding="utf-8"), before_loop)
            self.assertEqual(
                task_plan.read_text(encoding="utf-8"), plan_text
            )

            applied = subprocess.run(
                [sys.executable, str(MIGRATE_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            migrated_loop = loop_state.read_text(encoding="utf-8")
            migrated_plan = task_plan.read_text(encoding="utf-8")
            migrated_requirements = (state_dir / "requirements-baseline.md").read_text(
                encoding="utf-8"
            )
            migrated_design = (state_dir / "system-design.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("schema_version: 1.4", migrated_loop)
            self.assertIn("execution_mode: single", migrated_loop)
            self.assertIn("custom-note: preserve-me", migrated_loop)
            self.assertIn("## Shared Contract Paths", migrated_plan)
            self.assertIn("## First-Principles Analysis", migrated_requirements)
            self.assertIn("confirmation_status: pending", migrated_requirements)
            self.assertIn("contract_revision: 1", migrated_requirements)
            self.assertIn("approved_contract_revision: null", migrated_requirements)
            self.assertIn("approval_digest: null", migrated_requirements)
            self.assertIn("approval_evidence: null", migrated_requirements)
            self.assertIn("approved_by: null", migrated_requirements)
            self.assertIn("approved_at: null", migrated_requirements)
            self.assertIn("discovery_method: interactive", migrated_requirements)
            self.assertIn("## Solution Contract", migrated_requirements)
            self.assertIn("```json contract-material", migrated_requirements)
            self.assertIn("based_on_contract_revision: 1", migrated_design)
            self.assertIn("based_on_contract_revision: 1", migrated_plan)
            self.assertIn("backup:", applied.stdout)
            backup_dir = next(state_dir.glob(".migration-backup-*"))
            self.assertEqual(
                {path.name for path in backup_dir.iterdir()},
                {
                    "loop-state.md",
                    "requirements-baseline.md",
                    "system-design.md",
                    "task-plan.md",
                },
            )
            self.assertEqual(self.run_check(tmp).returncode, 0)

            repeated = subprocess.run(
                [sys.executable, str(MIGRATE_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
            self.assertIn("Spec2Web state already uses schema 1.4", repeated.stdout)
            self.assertEqual(len(list(state_dir.glob(".migration-backup-*"))), 1)

    def test_migrate_state_upgrades_v13_runtime_fields_transactionally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            state_dir = Path(tmp) / STATE_DIR_NAME
            loop_state = state_dir / "loop-state.md"
            task_plan = state_dir / "task-plan.md"
            source_loop = loop_state.read_text(encoding="utf-8").replace(
                "schema_version: 1.4", "schema_version: 1.3"
            )
            source_loop = re.sub(
                r"(?m)^(delivery_mode|autonomy_scope|stop_reason|resume_checkpoint|"
                r"active_run_id|state_revision|pending_transition):.*\n",
                "",
                source_loop,
            )
            loop_state.write_text(
                source_loop + "custom-note: preserve-me\n",
                encoding="utf-8",
            )
            task_plan.write_text(
                task_plan.read_text(encoding="utf-8")
                .replace("task_repair_attempt", "repair_attempt")
                .replace("task_failure_fingerprint", "last_failure_fingerprint")
                .replace("task_same_fingerprint_count", "same_fingerprint_count")
                .replace("integration_repair_attempt", "repair_attempt")
                .replace(
                    "integration_failure_fingerprint", "last_failure_fingerprint"
                )
                .replace(
                    "integration_same_fingerprint_count", "same_fingerprint_count"
                ),
                encoding="utf-8",
            )

            applied = subprocess.run(
                [sys.executable, str(MIGRATE_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            migrated_loop = loop_state.read_text(encoding="utf-8")
            migrated_plan = task_plan.read_text(encoding="utf-8")
            self.assertIn("schema_version: 1.4", migrated_loop)
            self.assertIn("delivery_mode: guided", migrated_loop)
            self.assertIn("custom-note: preserve-me", migrated_loop)
            self.assertIn("state_revision: 1", migrated_loop)
            for marker in (
                "task_repair_attempt: 0",
                "task_failure_fingerprint: none",
                "task_same_fingerprint_count: 0",
                "integration_repair_attempt: 0",
                "integration_failure_fingerprint: none",
                "integration_same_fingerprint_count: 0",
            ):
                self.assertIn(marker, migrated_plan)
            self.assertEqual(len(list(state_dir.glob(".migration-backup-*"))), 1)

            repeated = subprocess.run(
                [sys.executable, str(MIGRATE_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
            self.assertIn("Spec2Web state already uses schema 1.4", repeated.stdout)
            self.assertEqual(len(list(state_dir.glob(".migration-backup-*"))), 1)

    def test_migrate_state_reports_missing_required_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            requirements_baseline = Path(tmp) / STATE_DIR_NAME / "requirements-baseline.md"
            requirements_baseline.unlink()

            result = subprocess.run(
                [sys.executable, str(MIGRATE_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required file:", result.stdout)
            self.assertIn("requirements-baseline.md", result.stdout)

    def test_migrate_state_preserves_v11_runtime_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            self.set_loop_values(
                tmp,
                execution_mode="delegated",
                host_agent_capability="available",
                available_child_slots="4",
                selected_workers="1",
                checker_strategy="independent_checker",
            )

            result = subprocess.run(
                [sys.executable, str(MIGRATE_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            loop_state = (Path(tmp) / STATE_DIR_NAME / "loop-state.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("execution_mode: delegated", loop_state)
            self.assertIn("available_child_slots: 4", loop_state)
            self.assertIn("selected_workers: 1", loop_state)
            self.assertIn("Spec2Web state already uses schema 1.4", result.stdout)

    def test_migrate_state_rejects_unknown_explicit_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_init(tmp).returncode, 0)
            loop_state = Path(tmp) / STATE_DIR_NAME / "loop-state.md"
            loop_state.write_text(
                loop_state.read_text(encoding="utf-8").replace(
                    "schema_version: 1.4", "schema_version: 2.0"
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(MIGRATE_SCRIPT), "--target", tmp],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported schema_version: 2.0", result.stdout)

    def test_migrate_state_maps_non_default_legacy_repair_fields_for_v1_sources(
        self,
    ) -> None:
        for version in ("1.0", "1.1", "1.2"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(self.run_init(tmp).returncode, 0)
                state_dir = Path(tmp) / STATE_DIR_NAME
                loop_state = state_dir / "loop-state.md"
                task_plan = state_dir / "task-plan.md"
                source_loop = loop_state.read_text(encoding="utf-8").replace(
                    "schema_version: 1.4", f"schema_version: {version}"
                )
                source_loop = re.sub(
                    r"(?m)^(delivery_mode|autonomy_scope|stop_reason|resume_checkpoint|"
                    r"active_run_id|state_revision|pending_transition):.*\n",
                    "",
                    source_loop,
                )
                if version == "1.0":
                    source_loop = re.sub(
                        r"(?m)^(execution_mode|host_agent_capability|"
                        r"available_child_slots|selected_workers|"
                        r"active_checker_strategy):.*\n",
                        "",
                        source_loop,
                    )
                elif version == "1.1":
                    source_loop = source_loop.replace(
                        "active_checker_strategy: single_session\n",
                        "checker_strategy: independent_checker\n",
                    )
                loop_state.write_text(
                    source_loop + f"custom-source-version: {version}\n",
                    encoding="utf-8",
                )

                legacy_task_plan = re.sub(
                    r"(?m)^- (task_repair_attempt|task_failure_fingerprint|"
                    r"task_same_fingerprint_count|integration_repair_attempt|"
                    r"integration_failure_fingerprint|"
                    r"integration_same_fingerprint_count):.*\n",
                    "",
                    task_plan.read_text(encoding="utf-8"),
                )
                task_plan.write_text(
                    legacy_task_plan
                    + "- repair_attempt: 2\n"
                    + "- last_failure_fingerprint: sha256:legacy-non-default\n"
                    + "- same_fingerprint_count: 2\n",
                    encoding="utf-8",
                )

                result = subprocess.run(
                    [sys.executable, str(MIGRATE_SCRIPT), "--target", tmp],
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                migrated_loop = loop_state.read_text(encoding="utf-8")
                migrated_task_plan = task_plan.read_text(encoding="utf-8")
                self.assertIn("schema_version: 1.4", migrated_loop)
                self.assertIn(f"custom-source-version: {version}", migrated_loop)
                for marker in (
                    "task_repair_attempt: 2",
                    "task_failure_fingerprint: sha256:legacy-non-default",
                    "task_same_fingerprint_count: 2",
                    "integration_repair_attempt: 2",
                    "integration_failure_fingerprint: sha256:legacy-non-default",
                    "integration_same_fingerprint_count: 2",
                ):
                    self.assertIn(marker, migrated_task_plan)
                for legacy_field in (
                    "repair_attempt",
                    "last_failure_fingerprint",
                    "same_fingerprint_count",
                ):
                    self.assertNotIn(f"- {legacy_field}:", migrated_task_plan)

    def test_task_contract_guidance_uses_schema_1_4_repair_fields(self) -> None:
        for path in (
            SKILL_FILE,
            LOOP_ENGINEERING_REFERENCE,
            TASK_BREAKDOWN_REFERENCE,
            STATE_FILES_REFERENCE,
        ):
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                for field in (
                    "task_repair_attempt",
                    "task_failure_fingerprint",
                    "task_same_fingerprint_count",
                    "integration_repair_attempt",
                    "integration_failure_fingerprint",
                    "integration_same_fingerprint_count",
                ):
                    self.assertIn(field, text)
                for field in (
                    "repair_attempt",
                    "last_failure_fingerprint",
                    "same_fingerprint_count",
                ):
                    self.assertNotIn(f"`{field}`", text)
                    self.assertNotIn(f"- {field}:", text)

    def test_skill_routes_to_strategy_and_interface_references(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")

        self.assertIn("references/technology-strategy.md", text)
        self.assertIn("references/interface-design.md", text)
        self.assertIn("references/multi-agent-orchestration.md", text)
        self.assertIn("scripts/init-state.py", text)
        self.assertIn("scripts/migrate-state.py", text)
        self.assertIn("schema_version: 1.4", text)
        self.assertIn("scripts/transition-state.py", text)
        self.assertIn("--recover", text)
        self.assertIn("pending_transition", text)
        self.assertIn("task_repair_attempt", text)
        self.assertIn("integration_repair_attempt", text)
        self.assertIn("--phase execution", text)
        self.assertIn("--phase task", text)
        self.assertIn("--phase parallel", text)
        self.assertIn("--phase delivery", text)
        self.assertIn("one question per message", text)
        self.assertIn("2-3 concrete choices", text)
        self.assertIn("Do not ask the user to write the core requirements", text)

    def test_state_file_templates_route_to_schema_1_4(self) -> None:
        text = STATE_FILES_REFERENCE.read_text(encoding="utf-8")

        self.assertEqual(
            re.findall(r"(?m)^schema_version:\s*([^\s#]+)\s*$", text),
            ["1.4"],
        )

    def test_skill_routes_guided_and_autonomous_discovery_through_contract_gate(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")

        self.assertIn("delivery_mode: guided | autonomous", text)
        self.assertIn("discovery_method: interactive | inferred_contract", text)
        self.assertIn("scripts/approve-contract.py", text)
        self.assertIn("--phase specification", text)
        self.assertIn("workload envelope", text.lower())
        self.assertIn("declared stop condition", text.lower())

    def test_skill_contains_all_task6_autonomous_markers(self) -> None:
        """SKILL.md must contain every Task 6 autonomous marker verbatim.

        These markers are also checked by test_webbuilder_installation.py;
        this test provides an independent contract assertion in the
        spec2web state-script suite.
        """
        text = SKILL_FILE.read_text(encoding="utf-8")
        task6_markers = [
            "delivery_mode: guided | autonomous",
            "/webbuilder start autonomous from requirements.md",
            "--phase specification",
            "scripts/approve-contract.py",
            "scripts/check-host.py",
            "--phase initialization",
            "scripts/capture-evidence.py",
            "--phase ui",
            "scripts/transition-state.py",
            "--resume",
            "--phase delivery",
        ]
        missing = [m for m in task6_markers if m not in text]
        self.assertEqual(
            missing,
            [],
            f"SKILL.md is missing Task 6 autonomous markers: {missing}",
        )

    def test_state_files_reference_documents_specification_phase(self) -> None:
        text = STATE_FILES_REFERENCE.read_text(encoding="utf-8")

        self.assertIn("specification", text)
        self.assertIn("scripts/approve-contract.py", text)

    def test_readmes_document_contract_gate(self) -> None:
        for readme_path in (ROOT / "README.md", ROOT / "README_EN.md"):
            with self.subTest(path=readme_path):
                text = readme_path.read_text(encoding="utf-8")
                self.assertIn("approve-contract.py", text)
                self.assertIn("--phase specification", text)

    def test_skill_routes_to_evidence_and_host_capability_scripts(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")

        self.assertIn("scripts/capture-evidence.py", text)
        self.assertIn("scripts/check-host.py", text)
        self.assertIn("--phase host", text)
        self.assertIn("--phase initialization", text)
        self.assertIn("--phase ui", text)
        self.assertIn(".webbuilder-artifacts/", text)

    def test_skill_documents_authorization_header_redaction_policy(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")

        self.assertIn("authorization header", text.lower())
        self.assertIn("redact", text.lower())

    def test_state_files_reference_documents_evidence_artifacts_path(self) -> None:
        text = STATE_FILES_REFERENCE.read_text(encoding="utf-8")

        self.assertIn(".webbuilder-artifacts/", text)
        self.assertIn("capture-evidence.py", text)

    def test_multi_agent_orchestration_documents_evidence_capture(self) -> None:
        text = MULTI_AGENT_ORCHESTRATION_REFERENCE.read_text(encoding="utf-8")

        self.assertIn("capture-evidence.py", text)
        self.assertIn("check-host.py", text)
        self.assertIn(".webbuilder-artifacts/", text)

    def test_delivery_checklist_documents_redaction_and_authorization_policy(self) -> None:
        text = DELIVERY_CHECKLIST_REFERENCE.read_text(encoding="utf-8")

        self.assertIn(".webbuilder-artifacts/", text)
        self.assertIn("authorization header", text.lower())
        self.assertIn("redact", text.lower())

    def test_worktree_mode_documents_evidence_promotion(self) -> None:
        text = WORKTREE_MODE_REFERENCE.read_text(encoding="utf-8")

        self.assertIn(".webbuilder-artifacts/", text)
        self.assertIn("capture-evidence.py", text)

    def test_interface_design_documents_host_capability_phases(self) -> None:
        text = INTERFACE_DESIGN_REFERENCE.read_text(encoding="utf-8")

        self.assertIn("--phase host", text)
        self.assertIn("--phase initialization", text)
        self.assertIn("--phase ui", text)

    def test_readmes_document_evidence_and_host_capability(self) -> None:
        for readme_path in (ROOT / "README.md", ROOT / "README_EN.md"):
            with self.subTest(path=readme_path):
                text = readme_path.read_text(encoding="utf-8")
                self.assertIn("capture-evidence.py", text)
                self.assertIn("check-host.py", text)
                self.assertIn("--phase host", text)
                self.assertIn(".webbuilder-artifacts/", text)

    def test_install_reference_documents_autonomous_opt_in(self) -> None:
        """install.md must document autonomous opt-in and guided default."""
        text = INSTALL_REFERENCE.read_text(encoding="utf-8")
        self.assertIn("/webbuilder start autonomous from requirements.md", text)
        self.assertIn("guided mode is the default", text.lower())

    def test_readmes_document_autonomous_opt_in(self) -> None:
        """READMEs must document autonomous opt-in and guided default."""
        for readme_path in (ROOT / "README.md", ROOT / "README_EN.md"):
            with self.subTest(path=readme_path):
                text = readme_path.read_text(encoding="utf-8")
                self.assertIn("start autonomous from requirements.md", text)

    def test_readmes_document_golden_django_profile(self) -> None:
        """READMEs must reference the golden Django technology profile."""
        for readme_path in (ROOT / "README.md", ROOT / "README_EN.md"):
            with self.subTest(path=readme_path):
                text = readme_path.read_text(encoding="utf-8")
                self.assertIn("django-5.2-lts", text)

    def test_delivery_checklist_documents_stop_reason_and_host_capability(self) -> None:
        """Delivery checklist must document stop_reason and host capability checks."""
        text = DELIVERY_CHECKLIST_REFERENCE.read_text(encoding="utf-8")
        self.assertIn("stop_reason", text)
        self.assertIn("host capability", text.lower())

    def test_openai_yaml_documents_guided_default(self) -> None:
        """openai.yaml must indicate guided mode as default."""
        yaml_path = ROOT / "webbuilder" / "agents" / "openai.yaml"
        text = yaml_path.read_text(encoding="utf-8")
        self.assertIn("guided", text.lower())


if __name__ == "__main__":
    unittest.main()
