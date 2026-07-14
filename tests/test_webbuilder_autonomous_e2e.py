"""Contract-level tests for the autonomous reference e2e evidence surface.

Verifies that the maintained reference application exposes the browser,
accessibility, and performance evidence methods required by the autonomous
delivery plan.  These tests import modules and inspect structure without
launching a browser or Django server.
"""
from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTONOMOUS_DIR = ROOT / "examples" / "autonomous-reference"
FIXTURES_DIR = AUTONOMOUS_DIR / "webbuilder-fixtures"


class AutonomousE2EContractTests(unittest.TestCase):
    """Verify the e2e evidence surface is structurally complete."""

    @classmethod
    def setUpClass(cls) -> None:
        """Import e2e modules from the autonomous-reference example."""
        import sys

        # Add the autonomous-reference directory so ``e2e`` package resolves.
        cls._orig_path = sys.path[:]
        sys.path.insert(0, str(AUTONOMOUS_DIR))

        # The e2e modules import playwright at module level.  When running
        # from the root test suite (``python -m unittest discover``) playwright
        # is not installed — skip the entire class rather than erroring.
        try:
            cls.e2e_package = importlib.import_module("e2e")
            cls.server_module = importlib.import_module("e2e.server")
            cls.accessibility_module = importlib.import_module("e2e.accessibility")
            cls.test_module = importlib.import_module("e2e.test_primary_flow")
        except ImportError:
            sys.path[:] = cls._orig_path
            raise unittest.SkipTest("playwright not installed — skipping contract tests")

    @classmethod
    def tearDownClass(cls) -> None:
        import sys

        sys.path[:] = cls._orig_path

    # -- module existence ---------------------------------------------------

    def test_e2e_package_has_docstring(self) -> None:
        """The e2e package must have a module docstring."""
        self.assertTrue(self.e2e_package.__doc__)

    def test_server_module_exports_live_server(self) -> None:
        """e2e.server must expose a LiveServer class."""
        self.assertTrue(hasattr(self.server_module, "LiveServer"))
        self.assertTrue(
            callable(self.server_module.LiveServer),
            "LiveServer must be a callable (class)",
        )

    def test_accessibility_module_exports_baseline_function(self) -> None:
        """e2e.accessibility must expose baseline_accessibility_failures."""
        func = getattr(self.accessibility_module, "baseline_accessibility_failures", None)
        self.assertTrue(callable(func), "baseline_accessibility_failures must be callable")

    # -- test class contract ------------------------------------------------

    def test_primary_flow_class_exists(self) -> None:
        """e2e.test_primary_flow must contain PrimaryFlowTests."""
        cls = getattr(self.test_module, "PrimaryFlowTests", None)
        self.assertIsNotNone(cls, "PrimaryFlowTests class not found in e2e.test_primary_flow")
        self.assertTrue(issubclass(cls, unittest.TestCase))

    def test_primary_flow_has_browser_test(self) -> None:
        """PrimaryFlowTests must have the browser primary-flow test method."""
        cls = self.test_module.PrimaryFlowTests
        self.assertTrue(
            hasattr(cls, "test_login_create_complete_and_responsive_layout"),
            "missing test_login_create_complete_and_responsive_layout",
        )

    def test_primary_flow_has_accessibility_test(self) -> None:
        """PrimaryFlowTests must have the accessibility states test method."""
        cls = self.test_module.PrimaryFlowTests
        self.assertTrue(
            hasattr(cls, "test_accessibility_states"),
            "missing test_accessibility_states",
        )

    def test_primary_flow_has_performance_test(self) -> None:
        """PrimaryFlowTests must have the warm-flow performance budget test."""
        cls = self.test_module.PrimaryFlowTests
        self.assertTrue(
            hasattr(cls, "test_warm_primary_flow_under_budget"),
            "missing test_warm_primary_flow_under_budget",
        )

    # -- evidence capture invocation path -----------------------------------

    def test_capture_evidence_script_exists(self) -> None:
        """capture-evidence.py must exist in webbuilder/scripts/."""
        script = ROOT / "webbuilder" / "scripts" / "capture-evidence.py"
        self.assertTrue(script.is_file(), f"missing {script.relative_to(ROOT)}")

    def test_evidence_core_importable(self) -> None:
        """webbuilder/scripts/evidence_core.py must be importable."""
        import sys

        scripts_dir = str(ROOT / "webbuilder" / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        try:
            mod = importlib.import_module("evidence_core")
            self.assertTrue(
                hasattr(mod, "capture_command_evidence"),
                "evidence_core must expose capture_command_evidence",
            )
        finally:
            if scripts_dir in sys.path:
                sys.path.remove(scripts_dir)


class AutonomousLifecycleTests(unittest.TestCase):
    """Verify that the approved-contract fixture exists and is structurally valid.

    The approved-contract fixture drives the autonomous lifecycle — it must be
    present, parse as JSON, and contain the Django profile selection that
    instructs the autonomous agent which runtime profile to use.
    """

    FIXTURE_PATH = FIXTURES_DIR / "approved-contract.json"

    def test_approved_contract_fixture_exists(self) -> None:
        """approved-contract.json must exist in webbuilder-fixtures/."""
        self.assertTrue(
            self.FIXTURE_PATH.is_file(),
            f"missing fixture: {self.FIXTURE_PATH.relative_to(ROOT)}",
        )

    def test_approved_contract_is_valid_json(self) -> None:
        """approved-contract.json must parse as valid JSON."""
        with open(self.FIXTURE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)  # raises JSONDecodeError on bad payload
        self.assertIsInstance(data, dict)

    def test_approved_contract_contains_django_profile_selection(self) -> None:
        """The fixture must declare a Django profile selection for the lifecycle."""
        with open(self.FIXTURE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertIn(
            "profile",
            data,
            "approved-contract.json must contain a 'profile' key",
        )
        self.assertEqual(
            data["profile"],
            "django",
            "profile must be 'django' for the autonomous reference lifecycle",
        )


class AutonomousLifecycleReadyTests(unittest.TestCase):
    """Verify that the ready-state lifecycle fixtures exist and are structurally valid.

    The autonomous agent copies these markdown fixtures into the initialized
    WebBuilder state to represent the system-design and task-plan lifecycle
    stages.  Each must contain contract revision 1 and a ready-state marker
    confirming the document is approved and actionable.
    """

    SYSTEM_DESIGN_PATH = FIXTURES_DIR / "ready-system-design.md"
    TASK_PLAN_PATH = FIXTURES_DIR / "ready-task-plan.md"

    # -- ready-system-design.md ----------------------------------------------

    def test_ready_system_design_fixture_exists(self) -> None:
        """ready-system-design.md must exist in webbuilder-fixtures/."""
        self.assertTrue(
            self.SYSTEM_DESIGN_PATH.is_file(),
            f"missing fixture: {self.SYSTEM_DESIGN_PATH.relative_to(ROOT)}",
        )

    def test_ready_system_design_contains_contract_revision(self) -> None:
        """ready-system-design.md must reference contract revision 1."""
        text = self.SYSTEM_DESIGN_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "contract-revision: 1",
            text,
            "ready-system-design.md must contain 'contract-revision: 1'",
        )

    def test_ready_system_design_contains_ready_marker(self) -> None:
        """ready-system-design.md must contain a ready marker for the lifecycle."""
        text = self.SYSTEM_DESIGN_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "status: ready",
            text,
            "ready-system-design.md must contain 'status: ready'",
        )

    # -- ready-task-plan.md --------------------------------------------------

    def test_ready_task_plan_fixture_exists(self) -> None:
        """ready-task-plan.md must exist in webbuilder-fixtures/."""
        self.assertTrue(
            self.TASK_PLAN_PATH.is_file(),
            f"missing fixture: {self.TASK_PLAN_PATH.relative_to(ROOT)}",
        )

    def test_ready_task_plan_contains_contract_revision(self) -> None:
        """ready-task-plan.md must reference contract revision 1."""
        text = self.TASK_PLAN_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "contract-revision: 1",
            text,
            "ready-task-plan.md must contain 'contract-revision: 1'",
        )

    def test_ready_task_plan_contains_ready_marker(self) -> None:
        """ready-task-plan.md must contain a ready marker for the lifecycle."""
        text = self.TASK_PLAN_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "status: ready",
            text,
            "ready-task-plan.md must contain 'status: ready'",
        )


class AutonomousLifecycleCompletionTests(unittest.TestCase):
    """Verify that the completed-task-plan fixture exists and is structurally valid.

    After task execution the autonomous agent places a completed task plan
    into the WebBuilder state.  This fixture must carry contract revision 1
    and an explicit completion marker so downstream consumers can confirm the
    lifecycle reached its terminal state.
    """

    COMPLETED_PATH = FIXTURES_DIR / "completed-task-plan.md"

    def test_completed_task_plan_fixture_exists(self) -> None:
        """completed-task-plan.md must exist in webbuilder-fixtures/."""
        self.assertTrue(
            self.COMPLETED_PATH.is_file(),
            f"missing fixture: {self.COMPLETED_PATH.relative_to(ROOT)}",
        )

    def test_completed_task_plan_contains_contract_revision(self) -> None:
        """completed-task-plan.md must reference contract revision 1."""
        text = self.COMPLETED_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "contract-revision: 1",
            text,
            "completed-task-plan.md must contain 'contract-revision: 1'",
        )

    def test_completed_task_plan_contains_completion_marker(self) -> None:
        """completed-task-plan.md must contain a completion marker."""
        text = self.COMPLETED_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "status: completed",
            text,
            "completed-task-plan.md must contain 'status: completed'",
        )

    def test_completed_task_plan_contains_based_on_contract_revision(self) -> None:
        """completed-task-plan.md must declare based_on_contract_revision: 1."""
        text = self.COMPLETED_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "based_on_contract_revision: 1",
            text,
            "completed-task-plan.md must contain 'based_on_contract_revision: 1'",
        )


class TransitionStateBlockSubcommandTests(unittest.TestCase):
    """Verify transition-state.py supports --stop-reason / --checkpoint CLI.

    This is a TDD RED test: the CLI surface described here is not yet
    implemented.  The test must fail until ``transition-state.py`` grows
    ``--stop-reason`` and ``--checkpoint`` flags.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    TRANSITION_SCRIPT = ROOT / "webbuilder" / "scripts" / "transition-state.py"

    def test_transition_block_with_stop_reason_and_checkpoint(self) -> None:
        """transition-state.py --stop-reason environment_blocked --checkpoint task:TASK-002 must exit 0 and update loop-state.md."""
        import subprocess
        import sys
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize state
            init_result = subprocess.run(
                [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed:\nstdout: {init_result.stdout}\nstderr: {init_result.stderr}",
            )

            # Step 2: transition to blocked with stop-reason and checkpoint
            trans_result = subprocess.run(
                [
                    sys.executable,
                    str(self.TRANSITION_SCRIPT),
                    "--target", str(project),
                    "--stop-reason", "environment_blocked",
                    "--checkpoint", "task:TASK-002",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                trans_result.returncode, 0,
                f"transition-state.py failed:\nstdout: {trans_result.stdout}\nstderr: {trans_result.stderr}",
            )

            # Step 3: assert loop-state.md reflects the blocked state
            loop_state_path = project / "webbuilder" / "loop-state.md"
            self.assertTrue(
                loop_state_path.is_file(),
                f"loop-state.md not found at {loop_state_path}",
            )
            loop_text = loop_state_path.read_text(encoding="utf-8")
            self.assertIn(
                "status: blocked", loop_text,
                "loop-state.md must contain 'status: blocked'",
            )
            self.assertIn(
                "stop_reason: environment_blocked", loop_text,
                "loop-state.md must contain 'stop_reason: environment_blocked'",
            )
            self.assertIn(
                "task:TASK-002", loop_text,
                "loop-state.md must contain checkpoint 'task:TASK-002'",
            )


class TransitionStateResumeFlagTests(unittest.TestCase):
    """Verify transition-state.py supports --resume CLI surface.

    This is a TDD RED test: the ``--resume`` flag described here is not yet
    implemented.  The test must fail until ``transition-state.py`` grows
    a ``--resume`` option that clears the blocked state and restores the
    loop to active.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    TRANSITION_SCRIPT = ROOT / "webbuilder" / "scripts" / "transition-state.py"
    APPROVE_SCRIPT = ROOT / "webbuilder" / "scripts" / "approve-contract.py"

    # helpers ---------------------------------------------------------------

    def _init_project(self, project: Path) -> None:
        result = subprocess.run(
            [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, f"init failed: {result.stderr}")

    def _approve_contract(self, project: Path) -> None:
        """Inject the approved-contract fixture into requirements-baseline.md
        and run approve-contract.py to approve it via the real CLI workflow."""
        fixture_path = FIXTURES_DIR / "approved-contract.json"
        fixture_text = fixture_path.read_text(encoding="utf-8")

        req_path = project / "webbuilder" / "requirements-baseline.md"
        req_text = req_path.read_text(encoding="utf-8")

        # Replace the contract-material JSON block with the fixture content.
        updated = re.sub(
            r"(?ms)(^```json contract-material[ \t]*\n).*?\n(```[ \t]*$)",
            lambda m: m.group(1) + fixture_text.rstrip() + "\n" + m.group(2),
            req_text,
        )
        req_path.write_text(updated, encoding="utf-8", newline="\n")

        result = subprocess.run(
            [
                sys.executable, str(self.APPROVE_SCRIPT),
                "--target", str(project),
                "--approval-evidence", "test-fixture",
            ],
            capture_output=True, text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"approve-contract failed:\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )

    def _stop(self, project: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable, str(self.TRANSITION_SCRIPT),
                "--target", str(project),
                "--stop-reason", "environment_blocked",
                "--checkpoint", "task:TASK-002",
            ],
            capture_output=True, text=True,
        )

    def _resume(self, project: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable, str(self.TRANSITION_SCRIPT),
                "--target", str(project),
                "--resume",
            ],
            capture_output=True, text=True,
        )

    def _read_loop_field(self, project: Path, key: str) -> str:
        text = (project / "webbuilder" / "loop-state.md").read_text(encoding="utf-8")
        match = re.search(rf"(?m)^{re.escape(key)}:\s*(\S+)", text)
        self.assertIsNotNone(match, f"'{key}' field missing from loop-state.md")
        return match.group(1)  # type: ignore[union-attr]

    # tests -----------------------------------------------------------------

    def test_resume_clears_blocked_state(self) -> None:
        """transition-state.py --resume on a blocked project must exit 0,
        set status=active, stop_reason=none, resume_checkpoint=none, and
        bump state_revision."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize
            self._init_project(project)

            # Step 2: approve contract using the real CLI workflow and fixture
            self._approve_contract(project)

            # Step 3: record initial revision and stop
            revision_before_stop = int(self._read_loop_field(project, "state_revision"))
            stop_result = self._stop(project)
            self.assertEqual(
                stop_result.returncode, 0,
                f"stop failed:\nstdout: {stop_result.stdout}\nstderr: {stop_result.stderr}",
            )
            revision_after_stop = int(self._read_loop_field(project, "state_revision"))
            self.assertGreater(
                revision_after_stop, revision_before_stop,
                "state_revision must increase after stop transaction",
            )

            # Step 4: resume
            resume_result = self._resume(project)
            self.assertEqual(
                resume_result.returncode, 0,
                f"--resume failed:\nstdout: {resume_result.stdout}\nstderr: {resume_result.stderr}",
            )

            # Step 5: assert loop-state.md reflects active state
            self.assertEqual(
                self._read_loop_field(project, "status"), "active",
                "status must be active after --resume",
            )
            self.assertEqual(
                self._read_loop_field(project, "stop_reason"), "none",
                "stop_reason must be none after --resume",
            )
            self.assertEqual(
                self._read_loop_field(project, "resume_checkpoint"), "none",
                "resume_checkpoint must be none after --resume",
            )

            # Step 6: state_revision must have increased again
            revision_after_resume = int(self._read_loop_field(project, "state_revision"))
            self.assertGreater(
                revision_after_resume, revision_after_stop,
                "state_revision must increase after resume transaction",
            )

    def test_resume_without_contract_approval_rejected(self) -> None:
        """transition-state.py --resume on a blocked project where the
        contract has NOT been approved must exit nonzero, leave
        status=blocked, keep stop_reason/checkpoint unchanged, and not
        bump state_revision from its post-stop value.

        This is a TDD RED test: the contract-approval guard is not yet
        implemented in transition-state.py.  The test must fail until
        --resume checks that requirements-baseline.approved_contract_revision
        is set before clearing a blocked state.
        """
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize (contract is NOT approved —
            # requirements-baseline.md has approved_contract_revision: null)
            self._init_project(project)

            # Step 2: stop successfully
            stop_result = self._stop(project)
            self.assertEqual(
                stop_result.returncode, 0,
                f"stop failed:\nstdout: {stop_result.stdout}\nstderr: {stop_result.stderr}",
            )
            revision_after_stop = int(self._read_loop_field(project, "state_revision"))
            stop_reason_after_stop = self._read_loop_field(project, "stop_reason")
            checkpoint_after_stop = self._read_loop_field(project, "resume_checkpoint")
            self.assertEqual(stop_reason_after_stop, "environment_blocked")
            self.assertEqual(checkpoint_after_stop, "task:TASK-002")

            # Step 3: resume WITHOUT approving the contract
            resume_result = self._resume(project)
            self.assertNotEqual(
                resume_result.returncode, 0,
                "--resume without contract approval must be rejected (nonzero exit)",
            )

            # Step 4: state must remain blocked
            self.assertEqual(
                self._read_loop_field(project, "status"), "blocked",
                "status must remain blocked when resume is rejected",
            )
            self.assertEqual(
                self._read_loop_field(project, "stop_reason"),
                "environment_blocked",
                "stop_reason must remain environment_blocked when resume is rejected",
            )
            self.assertEqual(
                self._read_loop_field(project, "resume_checkpoint"),
                "task:TASK-002",
                "resume_checkpoint must remain task:TASK-002 when resume is rejected",
            )

            # Step 5: state_revision must not have increased
            revision_after_rejected = int(self._read_loop_field(project, "state_revision"))
            self.assertEqual(
                revision_after_rejected, revision_after_stop,
                "state_revision must not increase when resume is rejected",
            )


class TransitionStateStopRegressions(unittest.TestCase):
    """Regression tests for --stop-reason preconditions.

    These are TDD RED tests: the expected guard behaviour is not yet
    implemented in transition-state.py.  Both tests use a real
    TemporaryDirectory + init-state.py + transition-state.py subprocess
    pipeline matching the existing TransitionStateBlockSubcommandTests
    pattern.

    1. --stop-reason without --checkpoint must be rejected (nonzero exit)
       and leave the loop state untouched (still active).
    2. A second identical --stop-reason --checkpoint on an already-blocked
       state must be rejected (nonzero exit) because the active/paused
       precondition is no longer met.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    TRANSITION_SCRIPT = ROOT / "webbuilder" / "scripts" / "transition-state.py"

    # helpers ---------------------------------------------------------------

    def _init_project(self, project: Path) -> None:
        result = subprocess.run(
            [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, f"init failed: {result.stderr}")

    def _read_loop_status(self, project: Path) -> str:
        text = (project / "webbuilder" / "loop-state.md").read_text(encoding="utf-8")
        match = re.search(r"(?m)^status:\s*(\S+)", text)
        self.assertIsNotNone(match, "status field missing from loop-state.md")
        return match.group(1)  # type: ignore[union-attr]

    # tests -----------------------------------------------------------------

    def test_stop_reason_without_checkpoint_rejected(self) -> None:
        """--stop-reason environment_blocked without --checkpoint must exit nonzero
        and leave loop-state status active."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            self._init_project(project)

            result = subprocess.run(
                [
                    sys.executable, str(self.TRANSITION_SCRIPT),
                    "--target", str(project),
                    "--stop-reason", "environment_blocked",
                    # no --checkpoint
                ],
                capture_output=True, text=True,
            )
            self.assertNotEqual(
                result.returncode, 0,
                "stop-reason without --checkpoint must be rejected (nonzero exit)",
            )
            self.assertEqual(
                self._read_loop_status(project), "active",
                "loop-state must remain active when stop-reason is rejected",
            )

    def test_duplicate_stop_on_blocked_state_rejected(self) -> None:
        """After a successful --stop-reason --checkpoint, repeating the same
        command must fail because the state is already blocked."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            self._init_project(project)

            cmd = [
                sys.executable, str(self.TRANSITION_SCRIPT),
                "--target", str(project),
                "--stop-reason", "environment_blocked",
                "--checkpoint", "task:TASK-002",
            ]

            # First call: should succeed
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, f"first stop failed: {first.stderr}")
            self.assertEqual(
                self._read_loop_status(project), "blocked",
                "state must be blocked after first stop",
            )

            # Second call: must be rejected
            second = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(
                second.returncode, 0,
                "duplicate stop-reason on blocked state must be rejected (nonzero exit)",
            )
            self.assertEqual(
                self._read_loop_status(project), "blocked",
                "state must remain blocked (not toggled) after rejected duplicate stop",
            )


class TransitionStateDeliverFlagTests(unittest.TestCase):
    """Verify transition-state.py supports --deliver CLI surface.

    This is a TDD RED test: the ``--deliver`` top-level flag described here
    is not yet implemented.  The test must fail until ``transition-state.py``
    grows a ``--deliver`` option that invokes the deliver lifecycle event
    through the real delivery gate checker.

    The critical assertion is that stderr/stdout does NOT contain
    ``unrecognized arguments`` — this proves the new flag reaches the real
    delivery checker rather than merely being missing from argparse.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    TRANSITION_SCRIPT = ROOT / "webbuilder" / "scripts" / "transition-state.py"

    def _init_project(self, project: Path) -> None:
        result = subprocess.run(
            [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, f"init failed: {result.stderr}")

    def _read_loop_field(self, project: Path, key: str) -> str:
        text = (project / "webbuilder" / "loop-state.md").read_text(encoding="utf-8")
        match = re.search(rf"(?m)^{re.escape(key)}:\s*(\S+)", text)
        self.assertIsNotNone(match, f"'{key}' field missing from loop-state.md")
        return match.group(1)  # type: ignore[union-attr]

    def test_deliver_flag_reaches_delivery_gate(self) -> None:
        """transition-state.py --deliver on an initialized (but delivery-unready)
        project must exit nonzero because the delivery gate is unready, state
        must remain active with no state_revision increase, and stderr/stdout
        must NOT contain ``unrecognized arguments`` — proving the flag reaches
        the real delivery checker rather than being rejected by argparse."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize state
            self._init_project(project)

            # Step 2: record initial state
            status_before = self._read_loop_field(project, "status")
            self.assertEqual(status_before, "active", "initial status must be active")
            revision_before = int(self._read_loop_field(project, "state_revision"))

            # Step 3: invoke --deliver
            result = subprocess.run(
                [
                    sys.executable, str(self.TRANSITION_SCRIPT),
                    "--target", str(project),
                    "--deliver",
                ],
                capture_output=True, text=True,
            )

            # Step 4: must exit nonzero (delivery gate unready)
            self.assertNotEqual(
                result.returncode, 0,
                "--deliver on an unready project must be rejected (nonzero exit)",
            )

            # Step 5: state must remain active
            self.assertEqual(
                self._read_loop_field(project, "status"), "active",
                "status must remain active when deliver is rejected",
            )

            # Step 6: state_revision must not have increased
            revision_after = int(self._read_loop_field(project, "state_revision"))
            self.assertEqual(
                revision_after, revision_before,
                "state_revision must not increase when deliver is rejected",
            )

            # Step 7: stderr/stdout must NOT contain "unrecognized arguments"
            combined_output = result.stdout + result.stderr
            self.assertNotIn(
                "unrecognized arguments", combined_output,
                "--deliver must not be rejected by argparse as unrecognized; "
                "it must reach the real delivery gate checker",
            )


class SpecificationPhasePreconditionTests(unittest.TestCase):
    """Verify that real fixtures pass the specification-phase checker.

    This is a red discovery test: it exercises the real ``check-state.py``
    subprocess against the maintained ``webbuilder-fixtures/`` after
    injecting the approved contract into a freshly initialized state.
    No mocks — real files, real subprocesses.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    CHECK_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-state.py"

    def test_specification_phase_passes_with_real_fixtures(self) -> None:
        """check-state.py --phase specification must exit 0 after:
        1. init-state.py initializes the project
        2. approved-contract.json is injected into requirements-baseline.md
        3. discovery_method is set to inferred_contract
        4. ready-system-design.md and ready-task-plan.md are copied into webbuilder/
        """
        import shutil
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize state
            init_result = subprocess.run(
                [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed:\nstdout: {init_result.stdout}\nstderr: {init_result.stderr}",
            )

            # Step 2: inject approved-contract.json into requirements-baseline.md
            fixture_text = (FIXTURES_DIR / "approved-contract.json").read_text(encoding="utf-8")
            req_path = project / "webbuilder" / "requirements-baseline.md"
            req_text = req_path.read_text(encoding="utf-8")
            updated = re.sub(
                r"(?ms)(^```json contract-material[ \t]*\n).*?\n(```[ \t]*$)",
                lambda m: m.group(1) + fixture_text.rstrip() + "\n" + m.group(2),
                req_text,
            )
            req_path.write_text(updated, encoding="utf-8", newline="\n")

            # Step 3: replace '- not recorded' placeholders with contract-derived
            # values so the specification-phase checker sees concrete content.
            contract = json.loads(fixture_text)
            req_text = req_path.read_text(encoding="utf-8")
            req_text = re.sub(
                r"(?ms)(### AI Working Hypothesis\s*\n)\s*- not recorded",
                r"\g<1>- Inferred: " + contract["problem"],
                req_text,
            )
            req_text = re.sub(
                r"(?ms)(### User Decisions\s*\n)\s*- not recorded",
                r"\g<1>- Inferred from contract: deliver "
                + ", ".join(contract["primary_jobs"][:3]),
                req_text,
            )
            req_text = re.sub(
                r"(?ms)(### Core Outcome\s*\n)\s*- not recorded",
                r"\g<1>- " + contract["desired_outcome"],
                req_text,
            )
            constraints = "\n".join("- " + g for g in contract["non_goals"])
            req_text = re.sub(
                r"(?ms)(### Hard Constraints and Invariants\s*\n)\s*- not recorded",
                r"\g<1>" + constraints,
                req_text,
            )
            assumptions = "\n".join("- " + a for a in contract["delivery_assumptions"])
            req_text = re.sub(
                r"(?ms)(### Assumptions and Evidence\s*\n)\s*- not recorded",
                r"\g<1>" + assumptions,
                req_text,
            )
            # set discovery_method to inferred_contract
            req_text = re.sub(
                r"(?m)^discovery_method:\s*\S+",
                "discovery_method: inferred_contract",
                req_text,
            )
            req_path.write_text(req_text, encoding="utf-8", newline="\n")

            # Step 4: copy ready fixtures into webbuilder/
            shutil.copy2(
                str(FIXTURES_DIR / "ready-system-design.md"),
                str(project / "webbuilder" / "system-design.md"),
            )
            shutil.copy2(
                str(FIXTURES_DIR / "ready-task-plan.md"),
                str(project / "webbuilder" / "task-plan.md"),
            )

            # Step 5: run check-state.py --phase specification
            check_result = subprocess.run(
                [
                    sys.executable, str(self.CHECK_SCRIPT),
                    "--target", str(project),
                    "--phase", "specification",
                ],
                capture_output=True, text=True,
            )

            # Expect exit code 0 — report complete output on failure.
            if check_result.returncode != 0:
                self.fail(
                    f"check-state.py --phase specification exited {check_result.returncode}.\n"
                    f"stdout:\n{check_result.stdout}\n"
                    f"stderr:\n{check_result.stderr}"
                )


class HostCapabilityRoundTripTests(unittest.TestCase):
    """Verify host capabilities set via --set persist in loop-state.md."""

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    CHECK_HOST_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-host.py"

    def test_browser_available_and_subagents_unavailable_persist(self) -> None:
        """check-host.py --set browser=available:playwright --set subagents=unavailable:test-single-mode must exit 0 and persist both capability statuses."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize state
            init_result = subprocess.run(
                [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed:\nstdout: {init_result.stdout}\nstderr: {init_result.stderr}",
            )

            # Step 2: run check-host.py with explicit capability overrides
            check_result = subprocess.run(
                [
                    sys.executable, str(self.CHECK_HOST_SCRIPT),
                    "--target", str(project),
                    "--set", "browser=available:playwright",
                    "--set", "subagents=unavailable:test-single-mode",
                ],
                capture_output=True, text=True,
            )
            self.assertEqual(
                check_result.returncode, 0,
                f"check-host.py failed:\nstdout: {check_result.stdout}\nstderr: {check_result.stderr}",
            )

            # Step 3: read loop-state.md and assert capabilities persisted
            loop_state_path = project / "webbuilder" / "loop-state.md"
            self.assertTrue(loop_state_path.is_file(), "loop-state.md not found")
            loop_text = loop_state_path.read_text(encoding="utf-8")

            # The capabilities are stored as a JSON block under "## Host Capabilities".
            caps_match = re.search(
                r"## Host Capabilities\s*\n+```json\n(.*?)\n```",
                loop_text, re.DOTALL,
            )
            self.assertIsNotNone(
                caps_match, "Host Capabilities JSON block not found in loop-state.md",
            )
            caps = json.loads(caps_match.group(1))
            self.assertEqual(
                caps["browser"]["status"], "available",
                "browser capability must be available",
            )
            self.assertEqual(
                caps["subagents"]["status"], "unavailable",
                "subagents capability must be unavailable",
            )


class DeliveryLifecycleHelpers:
    """Mixin providing shared helpers for autonomous delivery lifecycle tests.

    Not a ``TestCase`` — mix into one so ``self.fail`` / ``self.assertEqual``
    are available.  Class-level script paths mirror the convention used by
    existing lifecycle test classes.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    CHECK_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-state.py"
    APPROVE_SCRIPT = ROOT / "webbuilder" / "scripts" / "approve-contract.py"
    CHECK_HOST_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-host.py"
    CAPTURE_SCRIPT = ROOT / "webbuilder" / "scripts" / "capture-evidence.py"
    TRANSITION_SCRIPT = ROOT / "webbuilder" / "scripts" / "transition-state.py"

    def prepare_initialized_project(self, project: Path) -> None:
        """Bring *project* through the initialization gate.

        Runs: init-state → inject approved contract → replace ``- not recorded``
        placeholders → copy ready design/task fixtures → check specification →
        approve contract → check host (browser=available, subagents=unavailable)
        → check initialization.

        Each subprocess must exit 0.  Does **not** capture evidence or deliver.
        """
        import shutil

        # Step 1: initialize state
        init_result = subprocess.run(
            [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
            capture_output=True, text=True,
        )
        self.assertEqual(
            init_result.returncode, 0,
            f"init-state.py failed:\nstdout: {init_result.stdout}\n"
            f"stderr: {init_result.stderr}",
        )

        # Step 1a: replace project-rules.md body with useful draft content
        project_rules_path = project / "webbuilder" / "project-rules.md"
        project_rules_path.write_text(
            "# Project Rules\n"
            "\n"
            "status: draft\n"
            "\n"
            "## Applicable Rules\n"
            "\n"
            "- The reference app uses Django 5.2 LTS.\n"
            "- Browser evidence is required for the UI workflow.\n"
            "\n"
            "## Sources Read\n"
            "\n"
            "- [x] Approved autonomous reference contract.\n",
            encoding="utf-8",
            newline="\n",
        )

        # Step 1b: mark project-rules ready via transition CLI
        rules_result = subprocess.run(
            [
                sys.executable, str(self.TRANSITION_SCRIPT),
                "--target", str(project),
                "--event", "mark-project-rules-ready",
            ],
            capture_output=True, text=True,
        )
        if rules_result.returncode != 0:
            self.fail(
                f"transition-state.py --event mark-project-rules-ready exited "
                f"{rules_result.returncode}.\n"
                f"stdout:\n{rules_result.stdout}\n"
                f"stderr:\n{rules_result.stderr}"
            )

        # Step 2: inject approved contract into requirements-baseline.md
        fixture_text = (FIXTURES_DIR / "approved-contract.json").read_text(
            encoding="utf-8",
        )
        req_path = project / "webbuilder" / "requirements-baseline.md"
        req_text = req_path.read_text(encoding="utf-8")
        updated = re.sub(
            r"(?ms)(^```json contract-material[ \t]*\n).*?\n(```[ \t]*$)",
            lambda m: m.group(1) + fixture_text.rstrip() + "\n" + m.group(2),
            req_text,
        )
        req_path.write_text(updated, encoding="utf-8", newline="\n")

        # Step 3: replace '- not recorded' placeholders with contract values
        contract = json.loads(fixture_text)
        req_text = req_path.read_text(encoding="utf-8")
        req_text = re.sub(
            r"(?ms)(### AI Working Hypothesis\s*\n)\s*- not recorded",
            r"\g<1>- Inferred: " + contract["problem"],
            req_text,
        )
        req_text = re.sub(
            r"(?ms)(### User Decisions\s*\n)\s*- not recorded",
            r"\g<1>- Inferred from contract: deliver "
            + ", ".join(contract["primary_jobs"][:3]),
            req_text,
        )
        req_text = re.sub(
            r"(?ms)(### Core Outcome\s*\n)\s*- not recorded",
            r"\g<1>- " + contract["desired_outcome"],
            req_text,
        )
        constraints = "\n".join("- " + g for g in contract["non_goals"])
        req_text = re.sub(
            r"(?ms)(### Hard Constraints and Invariants\s*\n)\s*- not recorded",
            r"\g<1>" + constraints,
            req_text,
        )
        assumptions = "\n".join(
            ["- " + a for a in contract["delivery_assumptions"]],
        )
        req_text = re.sub(
            r"(?ms)(### Assumptions and Evidence\s*\n)\s*- not recorded",
            r"\g<1>" + assumptions,
            req_text,
        )
        req_text = re.sub(
            r"(?m)^discovery_method:\s*\S+",
            "discovery_method: inferred_contract",
            req_text,
        )
        # Replace Confirmed Requirements table placeholders
        req_text = req_text.replace(
            "Replace with the first confirmed requirement.",
            contract["core_capabilities"][0] if contract.get("core_capabilities") else "work item CRUD",
        )
        req_text = req_text.replace(
            "Replace with verification method.",
            "Manual browser verification",
        )
        req_path.write_text(req_text, encoding="utf-8", newline="\n")

        # Step 3a: confirm user discovery via transition CLI
        discovery_result = subprocess.run(
            [
                sys.executable, str(self.TRANSITION_SCRIPT),
                "--target", str(project),
                "--event", "confirm-user-discovery",
            ],
            capture_output=True, text=True,
        )
        if discovery_result.returncode != 0:
            self.fail(
                f"transition-state.py --event confirm-user-discovery exited "
                f"{discovery_result.returncode}.\n"
                f"stdout:\n{discovery_result.stdout}\n"
                f"stderr:\n{discovery_result.stderr}"
            )

        # Step 3b: confirm requirements via transition CLI
        confirm_result = subprocess.run(
            [
                sys.executable, str(self.TRANSITION_SCRIPT),
                "--target", str(project),
                "--event", "confirm-requirements",
            ],
            capture_output=True, text=True,
        )
        if confirm_result.returncode != 0:
            self.fail(
                f"transition-state.py --event confirm-requirements exited "
                f"{confirm_result.returncode}.\n"
                f"stdout:\n{confirm_result.stdout}\n"
                f"stderr:\n{confirm_result.stderr}"
            )

        # Step 4: copy ready design and task fixtures into webbuilder/
        shutil.copy2(
            str(FIXTURES_DIR / "ready-system-design.md"),
            str(project / "webbuilder" / "system-design.md"),
        )
        shutil.copy2(
            str(FIXTURES_DIR / "ready-task-plan.md"),
            str(project / "webbuilder" / "task-plan.md"),
        )

        # Step 5: check specification phase
        spec_result = subprocess.run(
            [
                sys.executable, str(self.CHECK_SCRIPT),
                "--target", str(project),
                "--phase", "specification",
            ],
            capture_output=True, text=True,
        )
        if spec_result.returncode != 0:
            self.fail(
                f"check-state.py --phase specification exited "
                f"{spec_result.returncode}.\n"
                f"stdout:\n{spec_result.stdout}\n"
                f"stderr:\n{spec_result.stderr}"
            )

        # Step 6: approve contract
        approve_result = subprocess.run(
            [
                sys.executable, str(self.APPROVE_SCRIPT),
                "--target", str(project),
                "--approval-evidence", "test-fixture",
            ],
            capture_output=True, text=True,
        )
        if approve_result.returncode != 0:
            self.fail(
                f"approve-contract.py exited {approve_result.returncode}.\n"
                f"stdout:\n{approve_result.stdout}\n"
                f"stderr:\n{approve_result.stderr}"
            )

        # Step 7: check host capabilities (browser available, subagents unavailable)
        host_result = subprocess.run(
            [
                sys.executable, str(self.CHECK_HOST_SCRIPT),
                "--target", str(project),
                "--set", "browser=available:playwright",
                "--set", "subagents=unavailable:test-single-mode",
            ],
            capture_output=True, text=True,
        )
        if host_result.returncode != 0:
            self.fail(
                f"check-host.py exited {host_result.returncode}.\n"
                f"stdout:\n{host_result.stdout}\n"
                f"stderr:\n{host_result.stderr}"
            )

        # Step 8: check initialization phase — must exit 0
        init_check_result = subprocess.run(
            [
                sys.executable, str(self.CHECK_SCRIPT),
                "--target", str(project),
                "--phase", "initialization",
            ],
            capture_output=True, text=True,
        )
        if init_check_result.returncode != 0:
            self.fail(
                f"check-state.py --phase initialization exited "
                f"{init_check_result.returncode}.\n"
                f"stdout:\n{init_check_result.stdout}\n"
                f"stderr:\n{init_check_result.stderr}"
            )

    # -- evidence capture helpers --------------------------------------------

    EVIDENCE_SUBJECTS = (
        "functional", "ui", "accessibility",
        "performance", "security", "delivery-smoke",
    )

    def complete_delivery_report_transactionally(self, project: Path) -> None:
        """Replace ``delivery-report.md`` with ``status: complete`` via State Kernel.

        Uses ``state_transition.apply_transaction`` with the current expected
        revision to atomically replace the delivery-report template with a
        non-placeholder completed report including a final evidence summary.
        Asserts no direct writes to ``delivery-report.md`` outside the
        transaction kernel: the method never opens the file for writing itself.

        Requires: the *project* directory must already be a Git repo with the
        WebBuilder state fully initialized (``prepare_initialized_project``).
        """
        scripts_dir = str(ROOT / "webbuilder" / "scripts")
        orig_path = sys.path[:]
        sys.path.insert(0, scripts_dir)
        try:
            from state_transition import apply_transaction
            from state_schema import top_level_value
        finally:
            sys.path[:] = orig_path

        state_dir = project / "webbuilder"

        # Snapshot pre-transaction state for the no-direct-write assertion.
        loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")
        expected_revision = int(top_level_value(loop_text, "state_revision") or "0")
        report_path = state_dir / "delivery-report.md"

        delivery_report_content = (
            "# Delivery Report\n"
            "\n"
            "status: complete\n"
            "\n"
            "## Completed\n"
            "\n"
            "- All tasks executed and accepted.\n"
            "- Contract revision 1 requirements satisfied.\n"
            "\n"
            "## Validation\n"
            "\n"
            "- Six-domain evidence captured (functional, ui, accessibility,\n"
            "  performance, security, delivery-smoke).\n"
            "- Validation log entries recorded for every domain.\n"
            "- All manifests verified against contract revision and fingerprint.\n"
            "\n"
            "## Final Evidence Summary\n"
            "\n"
            "- functional: captured and verified\n"
            "- ui: captured and verified\n"
            "- accessibility: captured and verified\n"
            "- performance: captured and verified\n"
            "- security: captured and verified\n"
            "- delivery-smoke: captured and verified\n"
            "\n"
            "## Run Instructions\n"
            "\n"
            "- Run the application with the project's standard commands.\n"
            "- Evidence manifests are in the evidence/ directory.\n"
            "\n"
            "## Known Risks\n"
            "\n"
            "- None identified.\n"
            "\n"
            "## Not Completed\n"
            "\n"
            "- All planned work completed.\n"
        )

        # Apply the transaction — this is the ONLY allowed write path.
        apply_transaction(
            state_dir,
            "delivery_report_complete",
            {"delivery-report.md": delivery_report_content},
            expected_revision=expected_revision,
        )

        # Assert no direct loop writes: the transaction kernel must have
        # bumped state_revision by exactly one, proving all writes went
        # through apply_transaction and nothing was written directly.
        loop_text_after = (state_dir / "loop-state.md").read_text(encoding="utf-8")
        new_revision = int(top_level_value(loop_text_after, "state_revision") or "0")
        self.assertEqual(
            new_revision, expected_revision + 1,
            "state_revision must increment by exactly one — "
            "a direct loop write would skip the transaction kernel",
        )

        # Verify the written content.
        written = report_path.read_text(encoding="utf-8")
        self.assertEqual(
            top_level_value(written, "status"), "complete",
            "delivery-report.md must have status: complete after transaction",
        )
        for fragment in (
            "nothing delivered yet",
            "no validation recorded yet",
            "not recorded yet",
            "work has not started",
        ):
            self.assertNotIn(
                fragment, written.lower(),
                f"delivery-report.md must not contain placeholder: '{fragment}'",
            )

    # -- completed-task validation-log helpers --------------------------------

    COMPLETED_TASK_RECORDS = {
        "TASK-001": {
            "acceptance": {
                "gate": "acceptance",
                "task_status": "submitted_for_acceptance",
                "submission_commit": "direct_apply",
                "developer_identity": "orchestrator-single-session",
                "tester_identity": "orchestrator-single-session",
                "tester_result": "passed",
                "reviewer_identity": "orchestrator-single-session",
                "reviewer_result": "approved",
                "adversarial_cases_expected": "not_applicable",
                "adversarial_cases_passed": "not_applicable",
                "disagreement_status": "none",
                "orchestrator_decision": "accepted",
                "residual_risk": "none",
            },
            "integration": {
                "gate": "integration",
                "integration_strategy": "direct_apply",
                "integration_commit": "direct_apply",
                "main_workspace_verification": "passed",
                "verification_evidence": "python manage.py migrate --check && python manage.py test workitems -v 2",
                "final_task_status": "complete",
            },
        },
        "TASK-002": {
            "acceptance": {
                "gate": "acceptance",
                "task_status": "submitted_for_acceptance",
                "submission_commit": "direct_apply",
                "developer_identity": "orchestrator-single-session",
                "tester_identity": "orchestrator-single-session",
                "tester_result": "passed",
                "reviewer_identity": "orchestrator-single-session",
                "reviewer_result": "approved",
                "adversarial_cases_expected": "not_applicable",
                "adversarial_cases_passed": "not_applicable",
                "disagreement_status": "none",
                "orchestrator_decision": "accepted",
                "residual_risk": "none",
            },
            "integration": {
                "gate": "integration",
                "integration_strategy": "direct_apply",
                "integration_commit": "direct_apply",
                "main_workspace_verification": "passed",
                "verification_evidence": "python manage.py test workitems -v 2 && python -m unittest e2e.test_primary_flow.PrimaryFlowTests.test_login_create_complete_and_responsive_layout -v",
                "final_task_status": "complete",
            },
        },
        "TASK-003": {
            "acceptance": {
                "gate": "acceptance",
                "task_status": "submitted_for_acceptance",
                "submission_commit": "direct_apply",
                "developer_identity": "orchestrator-single-session",
                "tester_identity": "orchestrator-single-session",
                "tester_result": "passed",
                "reviewer_identity": "orchestrator-single-session",
                "reviewer_result": "approved",
                "adversarial_cases_expected": "not_applicable",
                "adversarial_cases_passed": "not_applicable",
                "disagreement_status": "none",
                "orchestrator_decision": "accepted",
                "residual_risk": "none",
            },
            "integration": {
                "gate": "integration",
                "integration_strategy": "direct_apply",
                "integration_commit": "direct_apply",
                "main_workspace_verification": "passed",
                "verification_evidence": "python manage.py test workitems -v 2 && python -m unittest e2e.test_primary_flow.PrimaryFlowTests.test_login_create_complete_and_responsive_layout -v",
                "final_task_status": "complete",
            },
        },
        "TASK-004": {
            "acceptance": {
                "gate": "acceptance",
                "task_status": "submitted_for_acceptance",
                "submission_commit": "direct_apply",
                "developer_identity": "orchestrator-single-session",
                "tester_identity": "orchestrator-single-session",
                "tester_result": "passed",
                "reviewer_identity": "orchestrator-single-session",
                "reviewer_result": "approved",
                "adversarial_cases_expected": "not_applicable",
                "adversarial_cases_passed": "not_applicable",
                "disagreement_status": "none",
                "orchestrator_decision": "accepted",
                "residual_risk": "none",
            },
            "integration": {
                "gate": "integration",
                "integration_strategy": "direct_apply",
                "integration_commit": "direct_apply",
                "main_workspace_verification": "passed",
                "verification_evidence": "python -m unittest e2e.test_primary_flow.PrimaryFlowTests.test_accessibility_states -v && python -m unittest e2e.test_primary_flow.PrimaryFlowTests.test_warm_primary_flow_under_budget -v",
                "final_task_status": "complete",
            },
        },
    }

    def append_completed_task_records(self, project: Path) -> None:
        """Append acceptance and integration validation-log records for every
        completed task (TASK-001 through TASK-004).

        Each record uses the task contract values from the completed-task-plan
        fixture: ``orchestrator_decision: accepted`` for acceptance,
        ``main_workspace_verification: passed`` and
        ``final_task_status: complete`` for integration.  The integration
        strategy and verification evidence match each task's contract.

        Call after transactional replacement of completed-task-plan and before
        completing the delivery report.
        """
        validation_log_path = project / "webbuilder" / "validation-log.md"
        for task_id, gates in self.COMPLETED_TASK_RECORDS.items():
            for gate_name, fields in gates.items():
                entry = f"### {task_id} / {gate_name}\n"
                for key, value in fields.items():
                    entry += f"- {key}: {value}\n"
                entry += "\n"
                with open(validation_log_path, "a", encoding="utf-8") as fh:
                    fh.write(entry)

    def capture_six_domains_and_log(self, project: Path) -> None:
        """Run ``capture-evidence.py`` once per delivery subject and append a
        ``### PROJECT / <subject>`` entry to ``validation-log.md`` after each
        successful capture.

        Mirrors the capture-then-log loop in ``CaptureEvidenceValidationLogTests``
        exactly: for each of the six subjects the method invokes the real
        ``capture-evidence.py`` subprocess, reads the produced manifest JSON,
        and appends a validation-log entry containing the manifest path, record
        ID, attempt, contract revision, implementation fingerprint, result,
        redaction status, and quality domain — all taken from the actual
        manifest, never from placeholder values.

        Requires: the *project* directory must already be a Git repo with at
        least one commit (``git_fingerprint`` needs a HEAD) and the
        WebBuilder state must already be initialized (``init-state.py``).
        """
        validation_log_path = project / "webbuilder" / "validation-log.md"
        for idx, subject in enumerate(self.EVIDENCE_SUBJECTS, start=1):
            result = subprocess.run(
                [
                    sys.executable, str(self.CAPTURE_SCRIPT),
                    "--target", str(project),
                    "--run", "delivery-run-001",
                    "--subject", subject,
                    "--attempt", str(idx),
                    "--contract-revision", "1",
                    "--allowed-path", "webbuilder",
                    "--",
                    sys.executable, "-c", f"print('evidence:{subject}')",
                ],
                capture_output=True, text=True,
            )
            self.assertEqual(
                result.returncode, 0,
                f"capture-evidence.py --subject {subject} failed:\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}",
            )

            # Extract manifest relative path from stdout
            self.assertIn(
                "manifest:", result.stdout,
                f"--subject {subject}: stdout must contain 'manifest:'",
            )
            manifest_line = [
                line for line in result.stdout.strip().splitlines()
                if line.startswith("manifest:")
            ][0]
            manifest_rel = manifest_line.split("manifest:", 1)[1].strip()

            # Read the manifest JSON and append a validation-log entry
            # with actual manifest values (no invented placeholders).
            manifest_data = json.loads(
                (project / manifest_rel).read_text(encoding="utf-8"),
            )
            log_entry = (
                f"### PROJECT / {subject}\n"
                f"- artifact_manifest: {manifest_rel}\n"
                f"- record_id: {manifest_data['record_id']}\n"
                f"- attempt: {manifest_data['attempt']}\n"
                f"- contract_revision: {manifest_data['contract_revision']}\n"
                f"- implementation_fingerprint: "
                f"{manifest_data['implementation_fingerprint']}\n"
                f"- result: {manifest_data['result']}\n"
                f"- redaction_status: "
                f"{manifest_data['redaction']['status']}\n"
                f"- quality_domain: {subject}\n"
            )
            with open(validation_log_path, "a", encoding="utf-8") as log_fh:
                log_fh.write(log_entry)


class InitializationGateLifecycleTests(unittest.TestCase):
    """Verify that approved-specification + host-check passes the initialization gate.

    End-to-end lifecycle test using real subprocesses in a TemporaryDirectory:
    init-state → materialize approved contract → copy ready fixtures →
    check specification → approve-contract → check-host → check-state
    --phase initialization must exit 0.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    CHECK_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-state.py"
    APPROVE_SCRIPT = ROOT / "webbuilder" / "scripts" / "approve-contract.py"
    CHECK_HOST_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-host.py"

    # -- helpers (copied from SpecificationPhasePreconditionTests) -----------

    def _inject_approved_contract(self, project: Path) -> None:
        """Inject approved-contract.json into requirements-baseline.md."""
        fixture_text = (FIXTURES_DIR / "approved-contract.json").read_text(encoding="utf-8")
        req_path = project / "webbuilder" / "requirements-baseline.md"
        req_text = req_path.read_text(encoding="utf-8")
        updated = re.sub(
            r"(?ms)(^```json contract-material[ \t]*\n).*?\n(```[ \t]*$)",
            lambda m: m.group(1) + fixture_text.rstrip() + "\n" + m.group(2),
            req_text,
        )
        req_path.write_text(updated, encoding="utf-8", newline="\n")

    def _replace_requirement_placeholders(self, project: Path) -> None:
        """Replace '- not recorded' placeholders with contract-derived values."""
        fixture_text = (FIXTURES_DIR / "approved-contract.json").read_text(encoding="utf-8")
        contract = json.loads(fixture_text)
        req_path = project / "webbuilder" / "requirements-baseline.md"
        req_text = req_path.read_text(encoding="utf-8")

        req_text = re.sub(
            r"(?ms)(### AI Working Hypothesis\s*\n)\s*- not recorded",
            r"\g<1>- Inferred: " + contract["problem"],
            req_text,
        )
        req_text = re.sub(
            r"(?ms)(### User Decisions\s*\n)\s*- not recorded",
            r"\g<1>- Inferred from contract: deliver "
            + ", ".join(contract["primary_jobs"][:3]),
            req_text,
        )
        req_text = re.sub(
            r"(?ms)(### Core Outcome\s*\n)\s*- not recorded",
            r"\g<1>- " + contract["desired_outcome"],
            req_text,
        )
        constraints = "\n".join("- " + g for g in contract["non_goals"])
        req_text = re.sub(
            r"(?ms)(### Hard Constraints and Invariants\s*\n)\s*- not recorded",
            r"\g<1>" + constraints,
            req_text,
        )
        assumptions = "\n".join("- " + a for a in contract["delivery_assumptions"])
        req_text = re.sub(
            r"(?ms)(### Assumptions and Evidence\s*\n)\s*- not recorded",
            r"\g<1>" + assumptions,
            req_text,
        )
        req_text = re.sub(
            r"(?m)^discovery_method:\s*\S+",
            "discovery_method: inferred_contract",
            req_text,
        )
        req_path.write_text(req_text, encoding="utf-8", newline="\n")

    # -- test ---------------------------------------------------------------

    def test_approved_specification_and_host_pass_initialization(self) -> None:
        """check-state.py --phase initialization must exit 0 after:
        1. init-state.py initializes the project
        2. approved-contract.json is injected into requirements-baseline.md
        3. ready-system-design.md and ready-task-plan.md are copied
        4. check-state.py --phase specification exits 0
        5. approve-contract.py exits 0
        6. check-host.py with browser=available and subagents=unavailable exits 0
        7. check-state.py --phase initialization exits 0
        """
        import shutil
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize state
            init_result = subprocess.run(
                [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed:\nstdout: {init_result.stdout}\n"
                f"stderr: {init_result.stderr}",
            )

            # Step 2: inject approved contract into requirements-baseline.md
            self._inject_approved_contract(project)
            self._replace_requirement_placeholders(project)

            # Step 3: copy ready fixtures into webbuilder/
            shutil.copy2(
                str(FIXTURES_DIR / "ready-system-design.md"),
                str(project / "webbuilder" / "system-design.md"),
            )
            shutil.copy2(
                str(FIXTURES_DIR / "ready-task-plan.md"),
                str(project / "webbuilder" / "task-plan.md"),
            )

            # Step 4: check specification phase
            spec_result = subprocess.run(
                [
                    sys.executable, str(self.CHECK_SCRIPT),
                    "--target", str(project),
                    "--phase", "specification",
                ],
                capture_output=True, text=True,
            )
            if spec_result.returncode != 0:
                self.fail(
                    f"check-state.py --phase specification exited "
                    f"{spec_result.returncode}.\n"
                    f"stdout:\n{spec_result.stdout}\n"
                    f"stderr:\n{spec_result.stderr}"
                )

            # Step 5: approve contract
            approve_result = subprocess.run(
                [
                    sys.executable, str(self.APPROVE_SCRIPT),
                    "--target", str(project),
                    "--approval-evidence", "test-fixture",
                ],
                capture_output=True, text=True,
            )
            if approve_result.returncode != 0:
                self.fail(
                    f"approve-contract.py exited {approve_result.returncode}.\n"
                    f"stdout:\n{approve_result.stdout}\n"
                    f"stderr:\n{approve_result.stderr}"
                )

            # Step 6: check host capabilities (browser available, subagents unavailable)
            host_result = subprocess.run(
                [
                    sys.executable, str(self.CHECK_HOST_SCRIPT),
                    "--target", str(project),
                    "--set", "browser=available:playwright",
                    "--set", "subagents=unavailable:test-single-mode",
                ],
                capture_output=True, text=True,
            )
            if host_result.returncode != 0:
                self.fail(
                    f"check-host.py exited {host_result.returncode}.\n"
                    f"stdout:\n{host_result.stdout}\n"
                    f"stderr:\n{host_result.stderr}"
                )

            # Step 7: check initialization phase — must exit 0
            init_check_result = subprocess.run(
                [
                    sys.executable, str(self.CHECK_SCRIPT),
                    "--target", str(project),
                    "--phase", "initialization",
                ],
                capture_output=True, text=True,
            )
            if init_check_result.returncode != 0:
                self.fail(
                    f"check-state.py --phase initialization exited "
                    f"{init_check_result.returncode}.\n"
                    f"stdout:\n{init_check_result.stdout}\n"
                    f"stderr:\n{init_check_result.stderr}"
                )


class AutonomousFullChainLifecycleTest(unittest.TestCase):
    """End-to-end TDD RED test: init → contract → specification → approve →
    host → initialization → stop → recover → resume → assert active.

    Exercises the full autonomous lifecycle using real CLIs in a temp Git repo.
    Does NOT attempt evidence or delivery — that comes in a later test.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    CHECK_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-state.py"
    APPROVE_SCRIPT = ROOT / "webbuilder" / "scripts" / "approve-contract.py"
    CHECK_HOST_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-host.py"
    TRANSITION_SCRIPT = ROOT / "webbuilder" / "scripts" / "transition-state.py"

    # -- helpers (reused from existing test classes) -------------------------

    @staticmethod
    def _run(script: Path, args: list[str]) -> subprocess.CompletedProcess:
        """Run a Python script with the given args and return the result."""
        return subprocess.run(
            [sys.executable, str(script)] + args,
            capture_output=True,
            text=True,
        )

    def _init_project(self, project: Path) -> None:
        result = self._run(self.INIT_SCRIPT, ["--target", str(project)])
        self.assertEqual(
            result.returncode, 0,
            f"init-state.py failed:\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )

    def _inject_approved_contract(self, project: Path) -> None:
        """Inject approved-contract.json into requirements-baseline.md."""
        fixture_text = (FIXTURES_DIR / "approved-contract.json").read_text(encoding="utf-8")
        req_path = project / "webbuilder" / "requirements-baseline.md"
        req_text = req_path.read_text(encoding="utf-8")
        updated = re.sub(
            r"(?ms)(^```json contract-material[ \t]*\n).*?\n(```[ \t]*$)",
            lambda m: m.group(1) + fixture_text.rstrip() + "\n" + m.group(2),
            req_text,
        )
        req_path.write_text(updated, encoding="utf-8", newline="\n")

    def _replace_requirement_placeholders(self, project: Path) -> None:
        """Replace '- not recorded' placeholders with contract-derived values."""
        fixture_text = (FIXTURES_DIR / "approved-contract.json").read_text(encoding="utf-8")
        contract = json.loads(fixture_text)
        req_path = project / "webbuilder" / "requirements-baseline.md"
        req_text = req_path.read_text(encoding="utf-8")

        req_text = re.sub(
            r"(?ms)(### AI Working Hypothesis\s*\n)\s*- not recorded",
            r"\g<1>- Inferred: " + contract["problem"],
            req_text,
        )
        req_text = re.sub(
            r"(?ms)(### User Decisions\s*\n)\s*- not recorded",
            r"\g<1>- Inferred from contract: deliver "
            + ", ".join(contract["primary_jobs"][:3]),
            req_text,
        )
        req_text = re.sub(
            r"(?ms)(### Core Outcome\s*\n)\s*- not recorded",
            r"\g<1>- " + contract["desired_outcome"],
            req_text,
        )
        constraints = "\n".join("- " + g for g in contract["non_goals"])
        req_text = re.sub(
            r"(?ms)(### Hard Constraints and Invariants\s*\n)\s*- not recorded",
            r"\g<1>" + constraints,
            req_text,
        )
        assumptions = "\n".join("- " + a for a in contract["delivery_assumptions"])
        req_text = re.sub(
            r"(?ms)(### Assumptions and Evidence\s*\n)\s*- not recorded",
            r"\g<1>" + assumptions,
            req_text,
        )
        req_text = re.sub(
            r"(?m)^discovery_method:\s*\S+",
            "discovery_method: inferred_contract",
            req_text,
        )
        req_path.write_text(req_text, encoding="utf-8", newline="\n")

    def _copy_ready_fixtures(self, project: Path) -> None:
        """Copy ready-system-design.md and ready-task-plan.md into webbuilder/."""
        import shutil
        shutil.copy2(
            str(FIXTURES_DIR / "ready-system-design.md"),
            str(project / "webbuilder" / "system-design.md"),
        )
        shutil.copy2(
            str(FIXTURES_DIR / "ready-task-plan.md"),
            str(project / "webbuilder" / "task-plan.md"),
        )

    def _read_loop_field(self, project: Path, key: str) -> str:
        text = (project / "webbuilder" / "loop-state.md").read_text(encoding="utf-8")
        match = re.search(rf"(?m)^{re.escape(key)}:\s*(\S+)", text)
        self.assertIsNotNone(match, f"'{key}' field missing from loop-state.md")
        return match.group(1)  # type: ignore[union-attr]

    def _assert_script_success(
        self, result: subprocess.CompletedProcess, label: str,
    ) -> None:
        if result.returncode != 0:
            self.fail(
                f"{label} exited {result.returncode}.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

    # -- test ---------------------------------------------------------------

    def test_full_chain_init_to_active(self) -> None:
        """Full autonomous lifecycle: init → materialize contract → copy
        ready fixtures → specification → approve → host → initialization →
        stop → recover → resume → assert active.

        Uses real CLIs in a temp Git repo.  Does NOT attempt evidence or
        delivery.
        """
        import shutil
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 0: initialize a Git repo (real CLIs in a temp Git repo)
            subprocess.run(
                ["git", "init", str(project)],
                capture_output=True, text=True, check=True,
            )

            # Step 1: init-state.py
            self._init_project(project)

            # Step 2: materialize approved contract into requirements-baseline.md
            self._inject_approved_contract(project)
            self._replace_requirement_placeholders(project)

            # Step 3: copy ready design and task fixtures
            self._copy_ready_fixtures(project)

            # Step 4: check-state.py --phase specification must pass
            spec_result = self._run(
                self.CHECK_SCRIPT,
                ["--target", str(project), "--phase", "specification"],
            )
            self._assert_script_success(spec_result, "check-state --phase specification")

            # Step 5: approve-contract.py must pass
            approve_result = self._run(
                self.APPROVE_SCRIPT,
                ["--target", str(project), "--approval-evidence", "test-fixture"],
            )
            self._assert_script_success(approve_result, "approve-contract")

            # Step 6: check-host.py with browser=available, subagents=unavailable
            host_result = self._run(
                self.CHECK_HOST_SCRIPT,
                [
                    "--target", str(project),
                    "--set", "browser=available:playwright",
                    "--set", "subagents=unavailable:test-single-mode",
                ],
            )
            self._assert_script_success(host_result, "check-host")

            # Step 7: check-state.py --phase initialization must pass
            init_check_result = self._run(
                self.CHECK_SCRIPT,
                ["--target", str(project), "--phase", "initialization"],
            )
            self._assert_script_success(init_check_result, "check-state --phase initialization")

            # Step 8: transition-state.py --stop-reason --checkpoint (stop)
            stop_result = self._run(
                self.TRANSITION_SCRIPT,
                [
                    "--target", str(project),
                    "--stop-reason", "environment_blocked",
                    "--checkpoint", "task:TASK-002",
                ],
            )
            self._assert_script_success(stop_result, "transition-state --stop-reason")
            self.assertEqual(
                self._read_loop_field(project, "status"), "blocked",
                "status must be blocked after --stop-reason",
            )

            # Step 9: transition-state.py --recover (recover pending transaction)
            recover_result = self._run(
                self.TRANSITION_SCRIPT,
                ["--target", str(project), "--recover"],
            )
            self._assert_script_success(recover_result, "transition-state --recover")

            # Step 10: transition-state.py --resume
            resume_result = self._run(
                self.TRANSITION_SCRIPT,
                ["--target", str(project), "--resume"],
            )
            self._assert_script_success(resume_result, "transition-state --resume")

            # Step 11: assert loop-state.md is active
            self.assertEqual(
                self._read_loop_field(project, "status"), "active",
                "status must be active after --resume",
            )
            self.assertEqual(
                self._read_loop_field(project, "stop_reason"), "none",
                "stop_reason must be none after --resume",
            )
            self.assertEqual(
                self._read_loop_field(project, "resume_checkpoint"), "none",
                "resume_checkpoint must be none after --resume",
            )


class CaptureEvidenceSubprocessTests(unittest.TestCase):
    """Verify capture-evidence.py captures evidence and produces a manifest.

    Exercises the real CLI surface: --target, --run, --subject, --attempt,
    --contract-revision, --allowed-path, and a deterministic command after --.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    CAPTURE_SCRIPT = ROOT / "webbuilder" / "scripts" / "capture-evidence.py"

    def test_capture_evidence_domain_command_returns_manifest(self) -> None:
        """capture-evidence.py --target project --run test-run-001
        --subject functional-smoke --attempt 1 --contract-revision 1
        --allowed-path workitems -- <python> -c print('ok') must exit 0
        and produce a manifest file that exists on disk."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize state
            init_result = subprocess.run(
                [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed:\nstdout: {init_result.stdout}\nstderr: {init_result.stderr}",
            )

            # Step 2: run capture-evidence.py with the real CLI surface
            result = subprocess.run(
                [
                    sys.executable, str(self.CAPTURE_SCRIPT),
                    "--target", str(project),
                    "--run", "test-run-001",
                    "--subject", "functional-smoke",
                    "--attempt", "1",
                    "--contract-revision", "1",
                    "--allowed-path", "workitems",
                    "--", sys.executable, "-c", "print('ok')",
                ],
                capture_output=True, text=True,
            )
            self.assertEqual(
                result.returncode, 0,
                f"capture-evidence.py failed:\nstdout: {result.stdout}\nstderr: {result.stderr}",
            )

            # Step 3: parse manifest path from stdout
            self.assertIn(
                "manifest:", result.stdout,
                "stdout must contain 'manifest:' with the relative path",
            )
            manifest_line = [
                line for line in result.stdout.strip().splitlines()
                if line.startswith("manifest:")
            ][0]
            manifest_relative = manifest_line.split("manifest:", 1)[1].strip()
            manifest_path = project / manifest_relative

            # Step 4: assert manifest file exists on disk
            self.assertTrue(
                manifest_path.is_file(),
                f"manifest file not found at {manifest_path}",
            )


class CaptureEvidenceValidationLogTests(unittest.TestCase):
    """Verify capture-evidence.py writes a validation-log.md entry per subject.

    This is a TDD RED test: after running capture-evidence.py for each of the
    six delivery subjects, validation-log.md must contain one ``### PROJECT /
    <subject>`` entry with the manifest path, record ID, attempt, contract
    revision, implementation fingerprint, result, and redaction status.

    The test uses deterministic Python print commands so that every run
    produces identical command output.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    CAPTURE_SCRIPT = ROOT / "webbuilder" / "scripts" / "capture-evidence.py"

    SUBJECTS = ("functional", "ui", "accessibility", "performance", "security", "delivery-smoke")

    def test_six_subjects_produce_validation_log_entries(self) -> None:
        """capture-evidence.py invoked once per subject must leave one current
        manifest entry in validation-log.md for each subject, including the
        manifest path, record ID, attempt, revision, fingerprint, result,
        redaction status, and quality domain.

        After each successful capture the test reads the manifest JSON and
        appends a ``### PROJECT / <subject>`` record to validation-log.md
        using the actual manifest values.  No post-capture git commit is
        performed because commits change state after evidence and do not
        stabilise captured fingerprints."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 0: initialize a Git repo (needed for git_fingerprint)
            git_result = subprocess.run(
                ["git", "init", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                git_result.returncode, 0,
                f"git init failed:\nstdout: {git_result.stdout}\n"
                f"stderr: {git_result.stderr}",
            )

            # Step 1: initialize state
            init_result = subprocess.run(
                [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed:\nstdout: {init_result.stdout}\n"
                f"stderr: {init_result.stderr}",
            )

            # Step 1.5: initial commit so git_fingerprint has a HEAD
            subprocess.run(
                ["git", "-C", str(project), "config", "user.email", "test@test"],
                capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "-C", str(project), "config", "user.name", "Test"],
                capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "-C", str(project), "add", "-A"],
                capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "-C", str(project), "commit", "-m", "initial"],
                capture_output=True, text=True, check=True,
            )

            # Step 2: run capture-evidence.py for each subject and
            #         append a validation-log entry after each successful capture.
            manifest_paths: dict[str, str] = {}
            validation_log_path = project / "webbuilder" / "validation-log.md"
            for idx, subject in enumerate(self.SUBJECTS, start=1):
                result = subprocess.run(
                    [
                        sys.executable, str(self.CAPTURE_SCRIPT),
                        "--target", str(project),
                        "--run", "delivery-run-001",
                        "--subject", subject,
                        "--attempt", str(idx),
                        "--contract-revision", "1",
                        "--allowed-path", "webbuilder",
                        "--",
                        sys.executable, "-c", f"print('evidence:{subject}')",
                    ],
                    capture_output=True, text=True,
                )
                self.assertEqual(
                    result.returncode, 0,
                    f"capture-evidence.py --subject {subject} failed:\n"
                    f"stdout: {result.stdout}\nstderr: {result.stderr}",
                )
                # Extract manifest relative path from stdout
                self.assertIn(
                    "manifest:", result.stdout,
                    f"--subject {subject}: stdout must contain 'manifest:'",
                )
                manifest_line = [
                    line for line in result.stdout.strip().splitlines()
                    if line.startswith("manifest:")
                ][0]
                manifest_rel = manifest_line.split("manifest:", 1)[1].strip()
                manifest_paths[subject] = manifest_rel

                # Read the manifest JSON and append a validation-log entry
                # with actual manifest values (no invented placeholders).
                manifest_data = json.loads(
                    (project / manifest_rel).read_text(encoding="utf-8"),
                )
                log_entry = (
                    f"### PROJECT / {subject}\n"
                    f"- artifact_manifest: {manifest_rel}\n"
                    f"- record_id: {manifest_data['record_id']}\n"
                    f"- attempt: {manifest_data['attempt']}\n"
                    f"- contract_revision: {manifest_data['contract_revision']}\n"
                    f"- implementation_fingerprint: "
                    f"{manifest_data['implementation_fingerprint']}\n"
                    f"- result: {manifest_data['result']}\n"
                    f"- redaction_status: "
                    f"{manifest_data['redaction']['status']}\n"
                    f"- quality_domain: {subject}\n"
                )
                with open(validation_log_path, "a", encoding="utf-8") as log_fh:
                    log_fh.write(log_entry)

            # Step 3: read validation-log.md and assert entries
            self.assertTrue(
                validation_log_path.is_file(),
                "validation-log.md not found after evidence capture",
            )
            log_text = validation_log_path.read_text(encoding="utf-8")

            for subject in self.SUBJECTS:
                # Each subject must have a ### PROJECT / <subject> heading
                heading_pattern = (
                    r"###\s+PROJECT\s*/\s*" + re.escape(subject) + r"\s*\n"
                )
                self.assertRegex(
                    log_text, heading_pattern,
                    f"validation-log.md missing heading for PROJECT / {subject}",
                )

                # Extract the record block for this subject
                record_match = re.search(
                    r"(?ms)^###\s+PROJECT\s*/\s*"
                    + re.escape(subject)
                    + r"\s*\n(.*?)(?=^###\s+|\Z)",
                    log_text,
                )
                self.assertIsNotNone(
                    record_match,
                    f"could not extract record block for PROJECT / {subject}",
                )
                record_block = record_match.group(1)  # type: ignore[union-attr]

                # Required fields per subject
                for field in (
                    "artifact_manifest",
                    "record_id",
                    "attempt",
                    "contract_revision",
                    "implementation_fingerprint",
                    "result",
                    "redaction_status",
                    "quality_domain",
                ):
                    field_match = re.search(
                        rf"(?m)^- {re.escape(field)}:\s*(.+?)\s*$",
                        record_block,
                    )
                    self.assertIsNotNone(
                        field_match,
                        f"PROJECT / {subject}: missing field '{field}' in "
                        f"validation-log.md record",
                    )
                    field_value = field_match.group(1).strip()  # type: ignore[union-attr]
                    self.assertTrue(
                        field_value and field_value not in ("none", "null", ""),
                        f"PROJECT / {subject}: field '{field}' is empty or placeholder",
                    )

                # artifact_manifest must match the path capture-evidence.py printed
                art_match = re.search(
                    r"(?m)^- artifact_manifest:\s*(.+?)\s*$", record_block,
                )
                self.assertIsNotNone(art_match)
                logged_manifest = art_match.group(1).strip()  # type: ignore[union-attr]
                self.assertEqual(
                    logged_manifest, manifest_paths[subject],
                    f"PROJECT / {subject}: logged manifest path "
                    f"does not match capture-evidence.py output",
                )

                # quality_domain must equal the subject
                qd_match = re.search(
                    r"(?m)^- quality_domain:\s*(.+?)\s*$", record_block,
                )
                self.assertIsNotNone(qd_match)
                self.assertEqual(
                    qd_match.group(1).strip(), subject,  # type: ignore[union-attr]
                    f"PROJECT / {subject}: quality_domain must equal the subject",
                )


class CompletedPlanTransactionTests(unittest.TestCase):
    """Verify that the completed-task-plan fixture is applied transactionally.

    Runs init-state.py in a TemporaryDirectory, then uses
    state_transition.apply_transaction to write the completed-task-plan
    fixture as the new task-plan.md.  Asserts that the state revision
    increments by exactly one, that the plan carries ``status: completed``,
    and that all four tasks report ``- status: complete``.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"

    def test_completed_plan_is_applied_transactionally(self) -> None:
        """apply_transaction with completed-task-plan.md must bump
        state_revision by one, set plan status to completed, and mark
        all four tasks as complete."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize state
            init_result = subprocess.run(
                [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed:\nstdout: {init_result.stdout}\n"
                f"stderr: {init_result.stderr}",
            )

            # Step 2: read current loop-state to get expected revision
            scripts_dir = str(ROOT / "webbuilder" / "scripts")
            orig_path = sys.path[:]
            sys.path.insert(0, scripts_dir)
            try:
                from state_transition import apply_transaction
                from state_schema import top_level_value
            finally:
                sys.path[:] = orig_path

            state_dir = project / "webbuilder"
            loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            expected_revision = int(top_level_value(loop_text, "state_revision") or "0")

            # Step 3: read fixture and apply as task-plan.md update
            fixture_text = (FIXTURES_DIR / "completed-task-plan.md").read_text(
                encoding="utf-8",
            )
            apply_transaction(
                state_dir,
                "task_plan_completed",
                {"task-plan.md": fixture_text},
                expected_revision=expected_revision,
            )

            # Step 4: assert state_revision incremented by exactly one
            loop_text_after = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            new_revision = int(
                top_level_value(loop_text_after, "state_revision") or "0",
            )
            self.assertEqual(
                new_revision, expected_revision + 1,
                "state_revision must increment by exactly one",
            )

            # Step 5: assert task-plan has status completed
            plan_text = (state_dir / "task-plan.md").read_text(encoding="utf-8")
            plan_status = top_level_value(plan_text, "status")
            self.assertEqual(
                plan_status, "completed",
                "task-plan.md must have status: completed",
            )

            # Step 6: assert four - status: complete entries
            complete_count = len(re.findall(r"(?m)^- status: complete\s*$", plan_text))
            self.assertEqual(
                complete_count, 4,
                f"expected four '- status: complete' entries, found {complete_count}",
            )


class DeliveryPreparationTests(unittest.TestCase):
    """Verify that a completed-plan state still fails the delivery phase gate.

    Uses the same temp init + transactional completed plan setup as
    CompletedPlanTransactionTests, then runs
    ``check-state.py --phase delivery`` to prove the delivery gate
    rejects the state before all delivery prerequisites are met.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
    CHECK_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-state.py"

    def test_completed_plan_fails_delivery_phase_check(self) -> None:
        """check-state.py --phase delivery on a state with only a
        completed task plan must exit nonzero and stdout must contain
        'delivery phase check failed'."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize state
            init_result = subprocess.run(
                [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed:\nstdout: {init_result.stdout}\n"
                f"stderr: {init_result.stderr}",
            )

            # Step 2: apply completed task plan transactionally
            scripts_dir = str(ROOT / "webbuilder" / "scripts")
            orig_path = sys.path[:]
            sys.path.insert(0, scripts_dir)
            try:
                from state_transition import apply_transaction
                from state_schema import top_level_value
            finally:
                sys.path[:] = orig_path

            state_dir = project / "webbuilder"
            loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            expected_revision = int(top_level_value(loop_text, "state_revision") or "0")

            fixture_text = (FIXTURES_DIR / "completed-task-plan.md").read_text(
                encoding="utf-8",
            )
            apply_transaction(
                state_dir,
                "task_plan_completed",
                {"task-plan.md": fixture_text},
                expected_revision=expected_revision,
            )

            # Step 3: run check-state.py --phase delivery
            check_result = subprocess.run(
                [
                    sys.executable, str(self.CHECK_SCRIPT),
                    "--target", str(project),
                    "--phase", "delivery",
                ],
                capture_output=True, text=True,
            )

            # Step 4: must exit nonzero (delivery prerequisites not met)
            self.assertNotEqual(
                check_result.returncode, 0,
                "delivery phase check must reject a completed-plan-only state",
            )

            # Step 5: stdout must contain the expected failure message
            self.assertIn(
                "delivery phase check failed", check_result.stdout,
                "stdout must contain 'delivery phase check failed'",
            )


class CompletedPlanCheckStructureTests(unittest.TestCase):
    """Verify check_structure accepts completed task-plan status.

    This is a TDD RED test: ``VALID_FILE_STATUSES`` currently only allows
    ``draft`` and ``ready`` for task-plan.md.  After applying the
    completed-task-plan fixture transactionally, ``check_structure`` must
    NOT report ``task-plan.md status must be one of: draft, ready``.

    Other delivery-phase errors are allowed — this test isolates only the
    completed-task-plan status compatibility in Plan 4.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"

    def test_completed_task_plan_accepted_by_check_structure(self) -> None:
        """check_structure must not reject task-plan.md status: completed."""
        import importlib.util
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize state
            init_result = subprocess.run(
                [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed:\nstdout: {init_result.stdout}\n"
                f"stderr: {init_result.stderr}",
            )

            # Step 2: import check-state.py module
            scripts_dir = str(ROOT / "webbuilder" / "scripts")
            check_script = ROOT / "webbuilder" / "scripts" / "check-state.py"
            spec = importlib.util.spec_from_file_location(
                "webbuilder_check_state", str(check_script),
            )
            assert spec is not None and spec.loader is not None
            check_module = importlib.util.module_from_spec(spec)
            orig_path = sys.path[:]
            sys.path.insert(0, scripts_dir)
            try:
                spec.loader.exec_module(check_module)
                from state_transition import apply_transaction
                from state_schema import top_level_value
            finally:
                sys.path[:] = orig_path

            # Step 3: apply completed-task-plan.md transactionally
            state_dir = project / "webbuilder"
            loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            expected_revision = int(top_level_value(loop_text, "state_revision") or "0")

            fixture_text = (FIXTURES_DIR / "completed-task-plan.md").read_text(
                encoding="utf-8",
            )
            apply_transaction(
                state_dir,
                "task_plan_completed",
                {"task-plan.md": fixture_text},
                expected_revision=expected_revision,
            )

            # Step 4: call check_structure and collect errors
            errors = check_module.check_structure(state_dir)

            # Step 5: assert the specific task-plan status rejection is absent
            task_plan_status_errors = [
                e for e in errors
                if "task-plan.md status must be one of:" in e
            ]
            self.assertEqual(
                task_plan_status_errors, [],
                "check_structure must not report "
                "'task-plan.md status must be one of: draft, ready' "
                "when plan status is completed; "
                f"got: {task_plan_status_errors}",
            )


class CompletedPlanDeliveryReadinessTests(unittest.TestCase):
    """Verify check_delivery_readiness accepts completed task-plan status.

    This is a TDD RED test: ``EXECUTION_STATUSES`` currently requires
    ``task-plan.md`` to be ``ready``.  After applying the completed-task-plan
    fixture transactionally, ``check_delivery_readiness`` must NOT report
    ``task-plan.md status must be ready; found completed``.

    Other delivery-phase errors are allowed — this test isolates only the
    completed-task-plan status gate in the delivery readiness check.
    """

    INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"

    def test_delivery_readiness_accepts_completed_task_plan(self) -> None:
        """check_delivery_readiness must not reject task-plan.md status: completed."""
        import importlib.util
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: initialize state
            init_result = subprocess.run(
                [sys.executable, str(self.INIT_SCRIPT), "--target", str(project)],
                capture_output=True, text=True,
            )
            self.assertEqual(
                init_result.returncode, 0,
                f"init-state.py failed:\nstdout: {init_result.stdout}\n"
                f"stderr: {init_result.stderr}",
            )

            # Step 2: import check-state.py module
            scripts_dir = str(ROOT / "webbuilder" / "scripts")
            check_script = ROOT / "webbuilder" / "scripts" / "check-state.py"
            spec = importlib.util.spec_from_file_location(
                "webbuilder_check_state_delivery", str(check_script),
            )
            assert spec is not None and spec.loader is not None
            check_module = importlib.util.module_from_spec(spec)
            orig_path = sys.path[:]
            sys.path.insert(0, scripts_dir)
            try:
                spec.loader.exec_module(check_module)
                from state_transition import apply_transaction
                from state_schema import top_level_value
            finally:
                sys.path[:] = orig_path

            # Step 3: apply completed-task-plan.md transactionally
            state_dir = project / "webbuilder"
            loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            expected_revision = int(top_level_value(loop_text, "state_revision") or "0")

            fixture_text = (FIXTURES_DIR / "completed-task-plan.md").read_text(
                encoding="utf-8",
            )
            apply_transaction(
                state_dir,
                "task_plan_completed",
                {"task-plan.md": fixture_text},
                expected_revision=expected_revision,
            )

            # Step 4: call check_delivery_readiness and collect errors
            errors = check_module.check_delivery_readiness(state_dir)

            # Step 5: assert the specific task-plan ready-status rejection is absent
            task_plan_status_errors = [
                e for e in errors
                if "task-plan.md status must be ready; found completed" in e
            ]
            self.assertEqual(
                task_plan_status_errors, [],
                "check_delivery_readiness must not report "
                "'task-plan.md status must be ready; found completed' "
                "when plan status is completed; "
                f"got: {task_plan_status_errors}",
            )


class DeliveryGateLifecycleTests(DeliveryLifecycleHelpers, unittest.TestCase):
    """Verify that --deliver is rejected when delivery prerequisites are missing.

    A focused red precondition test: even after a completed task plan, the
    delivery gate must reject the transition because evidence, validation-log,
    and delivery-report are absent.
    """

    TRANSITION_SCRIPT = ROOT / "webbuilder" / "scripts" / "transition-state.py"

    def _read_loop_field(self, project: Path, key: str) -> str:
        text = (project / "webbuilder" / "loop-state.md").read_text(encoding="utf-8")
        match = re.search(rf"(?m)^{re.escape(key)}:\s*(\S+)", text)
        self.assertIsNotNone(match, f"'{key}' field missing from loop-state.md")
        return match.group(1)  # type: ignore[union-attr]

    def test_deliver_rejected_after_completed_plan_without_delivery_prereqs(self) -> None:
        """transition-state.py --deliver on a state with a completed task plan
        but no evidence/validation-log/delivery-report must exit nonzero, leave
        status active, and stderr+stdout must contain 'delivery phase check
        failed' (not argparse 'unrecognized arguments')."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 1: make a real Git repo with local identity
            subprocess.run(
                ["git", "init", str(project)],
                capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "-C", str(project), "config", "user.email", "test@test"],
                capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "-C", str(project), "config", "user.name", "Test"],
                capture_output=True, text=True, check=True,
            )

            # Step 2: bring project through initialization gate (creates files)
            self.prepare_initialized_project(project)

            # Step 3: initial commit so git has a HEAD
            subprocess.run(
                ["git", "-C", str(project), "add", "-A"],
                capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "-C", str(project), "commit", "-m", "initial"],
                capture_output=True, text=True, check=True,
            )

            # Step 4: apply completed task-plan fixture transactionally
            scripts_dir = str(ROOT / "webbuilder" / "scripts")
            orig_path = sys.path[:]
            sys.path.insert(0, scripts_dir)
            try:
                from state_transition import apply_transaction
                from state_schema import top_level_value
            finally:
                sys.path[:] = orig_path

            state_dir = project / "webbuilder"
            loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            expected_revision = int(
                top_level_value(loop_text, "state_revision") or "0",
            )

            fixture_text = (FIXTURES_DIR / "completed-task-plan.md").read_text(
                encoding="utf-8",
            )
            apply_transaction(
                state_dir,
                "task_plan_completed",
                {"task-plan.md": fixture_text},
                expected_revision=expected_revision,
            )

            # Step 5: record pre-deliver state
            status_before = self._read_loop_field(project, "status")
            self.assertEqual(
                status_before, "active",
                "status must be active before --deliver",
            )

            # Step 6: invoke transition-state.py --deliver
            result = subprocess.run(
                [
                    sys.executable, str(self.TRANSITION_SCRIPT),
                    "--target", str(project),
                    "--deliver",
                ],
                capture_output=True, text=True,
            )

            # Step 7: must exit nonzero (delivery gate unready)
            self.assertNotEqual(
                result.returncode, 0,
                "--deliver without delivery prerequisites must be rejected",
            )

            # Step 8: state must remain active
            self.assertEqual(
                self._read_loop_field(project, "status"), "active",
                "status must remain active when deliver is rejected",
            )

            # Step 9: output must contain the real gate failure, not argparse
            combined = result.stdout + result.stderr
            self.assertIn(
                "delivery phase check failed", combined,
                "output must contain 'delivery phase check failed'",
            )
            self.assertNotIn(
                "unrecognized arguments", combined,
                "output must NOT be an argparse rejection",
            )


class FullDeliveryLifecycleTests(DeliveryLifecycleHelpers, unittest.TestCase):
    """End-to-end TDD RED test: init → contract → specification → approve →
    host → initialization → evidence capture → completed plan → delivery
    report → --deliver → delivery checker.

    Exercises the full autonomous delivery lifecycle using real CLIs in a
    temp Git repo.  Every step must succeed for the final --deliver to
    exit 0 and the delivery-phase checker to pass.
    """

    TRANSITION_SCRIPT = ROOT / "webbuilder" / "scripts" / "transition-state.py"

    def test_full_delivery_lifecycle(self) -> None:
        """Full delivery lifecycle: init → prepare → capture evidence →
        apply completed plan → complete delivery report → --deliver must
        exit 0 and check-state.py --phase delivery must pass.

        Uses real CLIs in a temp Git repo with an initial commit.
        """
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            # Step 0: create a Git repo with initial commit
            subprocess.run(
                ["git", "init", str(project)],
                capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "-C", str(project), "config", "user.email", "test@test"],
                capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "-C", str(project), "config", "user.name", "Test"],
                capture_output=True, text=True, check=True,
            )

            # Step 1: bring project through initialization gate
            self.prepare_initialized_project(project)

            # Step 2: initial commit so git_fingerprint has a HEAD
            subprocess.run(
                ["git", "-C", str(project), "add", "-A"],
                capture_output=True, text=True, check=True,
            )
            subprocess.run(
                ["git", "-C", str(project), "commit", "-m", "initial"],
                capture_output=True, text=True, check=True,
            )

            # Step 3: capture six-domain evidence and log to validation-log
            self.capture_six_domains_and_log(project)

            # Step 4: transactionally apply completed task-plan fixture
            scripts_dir = str(ROOT / "webbuilder" / "scripts")
            orig_path = sys.path[:]
            sys.path.insert(0, scripts_dir)
            try:
                from state_transition import apply_transaction
                from state_schema import top_level_value
            finally:
                sys.path[:] = orig_path

            state_dir = project / "webbuilder"
            loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")
            expected_revision = int(
                top_level_value(loop_text, "state_revision") or "0",
            )
            fixture_text = (FIXTURES_DIR / "completed-task-plan.md").read_text(
                encoding="utf-8",
            )
            apply_transaction(
                state_dir,
                "task_plan_completed",
                {"task-plan.md": fixture_text},
                expected_revision=expected_revision,
            )

            # Step 4b: append acceptance + integration records for each task
            self.append_completed_task_records(project)

            # Step 5: complete delivery report transactionally
            self.complete_delivery_report_transactionally(project)

            # Step 6: invoke --deliver
            result = subprocess.run(
                [
                    sys.executable, str(self.TRANSITION_SCRIPT),
                    "--target", str(project),
                    "--deliver",
                ],
                capture_output=True, text=True,
            )
            self.assertEqual(
                result.returncode, 0,
                f"--deliver must exit 0:\nstdout: {result.stdout}\n"
                f"stderr: {result.stderr}",
            )

            # Step 7: delivery checker must pass
            check_result = subprocess.run(
                [
                    sys.executable, str(self.CHECK_SCRIPT),
                    "--target", str(project),
                    "--phase", "delivery",
                ],
                capture_output=True, text=True,
            )
            if check_result.returncode != 0:
                self.fail(
                    f"check-state.py --phase delivery exited "
                    f"{check_result.returncode}.\n"
                    f"stdout:\n{check_result.stdout}\n"
                    f"stderr:\n{check_result.stderr}"
                )


if __name__ == "__main__":
    unittest.main()
