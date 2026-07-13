# WebBuilder State Kernel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the tracked test/CI baseline and implement schema 1.4, journaled state transactions, idempotent migration, strategy-aware checker identities, and separate task/integration repair state.

**Architecture:** Extract shared schema and Markdown helpers from the three existing scripts into `state_schema.py`. Use `state_transition.py` for revisioned multi-file writes with a durable JSON journal and recovery; initialization, migration, and later plans consume this kernel rather than independently changing success statuses.

**Tech Stack:** Python 3.12+ standard library, Markdown state files, JSON transition journals, `unittest`, GitHub Actions.

## Global Constraints

- Preserve all existing guided behavior and the seven state files.
- Do not add runtime dependencies.
- Migrated projects default to `delivery_mode: guided`.
- Every migration and transition is non-destructive, UTF-8/LF, backed up when migrating, and idempotent.
- Autonomous execution remains disabled throughout this plan.
- Write a failing behavior test before each implementation change.
- Do not stage or remove the existing untracked `.codegraph/` directory.

---

### Task 1: Track Tests and Add the Cross-Platform Release Gate

**Files:**
- Modify: `.gitignore:1-9`
- Create: `.github/workflows/test.yml`
- Modify: `README.md:274-290`
- Modify: `README_EN.md` validation section
- Test: `tests/test_spec2web_state_scripts.py`

**Interfaces:**
- Consumes: current `python -m unittest discover -s tests -v` and Skill validator commands.
- Produces: a committed test directory and CI contract used by every later task.

- [ ] **Step 1: Capture the current characterization baseline**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: 31 tests pass. Save the count in the commit message body; do not alter assertions to make later changes easier.

- [ ] **Step 2: Stop ignoring tests and ignore generated autonomous artifacts**

Edit `.gitignore` to exactly preserve the existing Python entries and local-doc policy while removing `tests/` and adding generated state artifacts:

```gitignore
__pycache__/
*.py[cod]

# Local planning and project workspace files
CLAUDE.md
docs/
loop engineering.md
spec2web_product_design.md

# Generated WebBuilder runtime artifacts
.webbuilder-artifacts/
webbuilder/.transitions/
webbuilder/.migration-backup-*/
```

Run:

```powershell
git check-ignore tests/test_spec2web_state_scripts.py
```

Expected: exit code 1 and no output.

- [ ] **Step 3: Add CI**

Create `.github/workflows/test.yml`:

```yaml
name: test

on:
  push:
  pull_request:

jobs:
  state-scripts:
    strategy:
      matrix:
        os: [windows-latest, ubuntu-latest]
        python-version: ["3.12", "3.14"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m unittest discover -s tests -v
      - run: python -X utf8 webbuilder/scripts/check-state.py --help
```

- [ ] **Step 4: Make documented validation UTF-8 safe**

Change the README and README_EN Skill validation command to:

```powershell
python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" webbuilder
```

Run that command. Expected: `Skill is valid!`.

- [ ] **Step 5: Re-run the baseline and commit**

```powershell
python -m unittest discover -s tests -v
git diff --check
git add .gitignore .github/workflows/test.yml README.md README_EN.md tests/test_spec2web_state_scripts.py
git commit -m "test: track WebBuilder regression suite"
```

Expected: 31 tests pass and the commit contains the previously ignored test file.

---

### Task 2: Extract the Shared Schema and Markdown Helpers

**Files:**
- Create: `webbuilder/scripts/state_schema.py`
- Modify: `webbuilder/scripts/init-state.py:7-13`
- Modify: `webbuilder/scripts/migrate-state.py:10-34`
- Modify: `webbuilder/scripts/check-state.py:9-25,183-281`
- Create: `tests/test_webbuilder_state_kernel.py`

**Interfaces:**
- Consumes: current state-directory fallback and regex semantics.
- Produces: `SCHEMA_VERSION`, `resolve_state_dir()`, `read_state_files()`, `top_level_value()`, `set_top_level_value()`, `markdown_section()`, `task_sections()`, `sha256_bytes()`, and `direct_apply_fingerprint()`.

- [ ] **Step 1: Write failing shared-helper tests**

Create `tests/test_webbuilder_state_kernel.py` with repository-local module loading:

```python
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "webbuilder" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from state_schema import (  # noqa: E402
    SCHEMA_VERSION,
    direct_apply_fingerprint,
    set_top_level_value,
    top_level_value,
)


class StateSchemaTests(unittest.TestCase):
    def test_schema_version_is_1_4(self) -> None:
        self.assertEqual(SCHEMA_VERSION, "1.4")

    def test_set_top_level_value_replaces_once_and_appends_when_missing(self) -> None:
        text = "# State\n\nstatus: active\n"
        changed = set_top_level_value(text, "status", "blocked")
        changed = set_top_level_value(changed, "stop_reason", "environment_blocked")
        self.assertEqual(top_level_value(changed, "status"), "blocked")
        self.assertEqual(top_level_value(changed, "stop_reason"), "environment_blocked")
        self.assertEqual(changed.count("status:"), 1)

    def test_direct_apply_fingerprint_changes_with_allowed_file_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            target = root / "src" / "app.py"
            target.write_text("one\n", encoding="utf-8")
            first = direct_apply_fingerprint(root, ["src/app.py"])
            target.write_text("two\n", encoding="utf-8")
            second = direct_apply_fingerprint(root, ["src/app.py"])
            self.assertNotEqual(first, second)
```

- [ ] **Step 2: Run the tests and observe the missing module**

```powershell
python -m unittest tests.test_webbuilder_state_kernel.StateSchemaTests -v
```

Expected: import failure for `state_schema`.

- [ ] **Step 3: Create the shared module**

Create `webbuilder/scripts/state_schema.py` with these public definitions and preserve the existing regex grammar:

```python
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from pathlib import Path

STATE_DIR_NAME = "webbuilder"
LEGACY_STATE_DIR_NAME = "spec2web"
SCHEMA_VERSION = "1.4"
SUPPORTED_SOURCE_VERSIONS = {"1.0", "1.1", "1.2", "1.3"}
REQUIRED_FILES = (
    "project-rules.md",
    "requirements-baseline.md",
    "system-design.md",
    "task-plan.md",
    "loop-state.md",
    "validation-log.md",
    "delivery-report.md",
)
TASK_SECTION_PATTERN = re.compile(
    r"(?ms)^###\s+(TASK-[A-Za-z0-9_-]+):[^\n]*\n(.*?)(?=^###\s+TASK-|\Z)"
)


def resolve_state_dir(target: Path) -> Path:
    state_dir = target / STATE_DIR_NAME
    legacy = target / LEGACY_STATE_DIR_NAME
    if not (state_dir / "loop-state.md").exists() and (legacy / "loop-state.md").exists():
        return legacy
    return state_dir


def read_state_files(state_dir: Path, names: Iterable[str]) -> dict[str, str]:
    return {name: (state_dir / name).read_text(encoding="utf-8") for name in names}


def top_level_value(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*([^\s#]+)\s*$", text)
    return match.group(1) if match else None


def set_top_level_value(text: str, key: str, value: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
    if re.search(pattern, text):
        return re.sub(pattern, f"{key}: {value}", text, count=1)
    lines = text.rstrip().splitlines()
    insert_at = 1 if lines and lines[0].startswith("# ") else 0
    lines[insert_at:insert_at] = ["", f"{key}: {value}"]
    return "\n".join(lines).rstrip() + "\n"


def markdown_section(text: str, heading: str) -> str | None:
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", text)
    return match.group(1).rstrip() if match else None


def task_sections(text: str) -> dict[str, str]:
    return dict(TASK_SECTION_PATTERN.findall(text))


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def direct_apply_fingerprint(project_root: Path, allowed_paths: Iterable[str]) -> str:
    entries = []
    for value in sorted(set(allowed_paths)):
        path = project_root / value
        if path.is_file():
            entries.append({"path": value.replace("\\", "/"), "sha256": sha256_bytes(path.read_bytes())})
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))
```

- [ ] **Step 4: Replace duplicated constants/helpers with imports**

In all three existing scripts import the shared values they use. Remove only definitions now owned by `state_schema.py`; preserve task-specific parsing helpers in `check-state.py`.

```python
from state_schema import (
    REQUIRED_FILES,
    SCHEMA_VERSION,
    STATE_DIR_NAME,
    TASK_SECTION_PATTERN,
    resolve_state_dir,
    top_level_value,
)
```

- [ ] **Step 5: Run focused and full tests, then commit**

```powershell
python -m unittest tests.test_webbuilder_state_kernel.StateSchemaTests -v
python -m unittest discover -s tests -v
git add webbuilder/scripts/state_schema.py webbuilder/scripts/init-state.py webbuilder/scripts/migrate-state.py webbuilder/scripts/check-state.py tests/test_webbuilder_state_kernel.py
git commit -m "refactor: centralize WebBuilder state schema"
```

Expected: focused tests and the 31 characterization tests pass.

---

### Task 3: Implement Journaled Multi-File State Transactions

**Files:**
- Create: `webbuilder/scripts/state_transition.py`
- Create: `webbuilder/scripts/transition-state.py`
- Modify: `tests/test_webbuilder_state_kernel.py`

**Interfaces:**
- Consumes: `state_schema.top_level_value()`, `set_top_level_value()`, and `sha256_bytes()`.
- Produces: `apply_transaction()` and `recover_pending_transaction()` exactly as declared in the roadmap.

- [ ] **Step 1: Add interruption and recovery tests**

Append tests that initialize two state files, inject a failure after the first replacement, and assert the journal completes recovery:

```python
from state_transition import apply_transaction, recover_pending_transaction


class StateTransitionTests(unittest.TestCase):
    def test_interrupted_transaction_recovers_all_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "webbuilder"
            state_dir.mkdir()
            loop = "# Loop State\n\nstate_revision: 1\npending_transition: null\nstatus: active\n"
            requirements = "# Requirements Baseline\n\nconfirmation_status: pending\n"
            (state_dir / "loop-state.md").write_text(loop, encoding="utf-8")
            (state_dir / "requirements-baseline.md").write_text(requirements, encoding="utf-8")
            updates = {
                "loop-state.md": loop.replace("status: active", "status: blocked"),
                "requirements-baseline.md": requirements.replace("pending", "approved"),
            }
            with self.assertRaises(RuntimeError):
                apply_transaction(
                    state_dir,
                    "test-interruption",
                    updates,
                    expected_revision=1,
                    fail_after_replacements=1,
                )
            transition_id = recover_pending_transaction(state_dir)
            self.assertIsNotNone(transition_id)
            self.assertIn("status: blocked", (state_dir / "loop-state.md").read_text(encoding="utf-8"))
            self.assertIn("confirmation_status: approved", (state_dir / "requirements-baseline.md").read_text(encoding="utf-8"))
            self.assertEqual(recover_pending_transaction(state_dir), None)

    def test_transaction_rejects_stale_expected_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "webbuilder"
            state_dir.mkdir()
            loop = "# Loop State\n\nstate_revision: 2\npending_transition: null\n"
            (state_dir / "loop-state.md").write_text(loop, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "state revision changed"):
                apply_transaction(state_dir, "stale", {"loop-state.md": loop}, expected_revision=1)
```

- [ ] **Step 2: Run the tests and verify the missing API failure**

```powershell
python -m unittest tests.test_webbuilder_state_kernel.StateTransitionTests -v
```

Expected: import failure for `state_transition`.

- [ ] **Step 3: Implement the transaction module**

Create `state_transition.py` using a `.transitions/<id>.json` journal. The journal contains `event`, `expected_revision`, `next_revision`, and each file's original/target SHA-256 plus target text. `apply_transaction()` must:

```python
def apply_transaction(
    state_dir: Path,
    event: str,
    updates: dict[str, str],
    *,
    expected_revision: int,
    fail_after_replacements: int | None = None,
) -> str:
    recover_pending_transaction(state_dir)
    loop_path = state_dir / "loop-state.md"
    loop_text = loop_path.read_text(encoding="utf-8")
    actual_revision = int(top_level_value(loop_text, "state_revision") or "0")
    if actual_revision != expected_revision:
        raise ValueError(f"state revision changed: expected {expected_revision}, found {actual_revision}")
    transition_id = f"TX-{uuid.uuid4().hex}"
    next_revision = expected_revision + 1
    target_updates = dict(updates)
    final_loop = target_updates.get("loop-state.md", loop_text)
    final_loop = set_top_level_value(final_loop, "state_revision", str(next_revision))
    final_loop = set_top_level_value(final_loop, "pending_transition", "null")
    target_updates["loop-state.md"] = final_loop
    intermediate_loop = set_top_level_value(loop_text, "pending_transition", transition_id)
    journal = build_journal(state_dir, transition_id, event, expected_revision, next_revision, target_updates)
    write_journal(state_dir, journal)
    atomic_write_text(loop_path, intermediate_loop)
    replace_targets(
        state_dir,
        journal,
        skip_names={"loop-state.md"},
        fail_after_replacements=fail_after_replacements,
    )
    atomic_write_text(loop_path, final_loop)
    mark_journal_complete(state_dir, transition_id)
    return transition_id
```

Implement the helpers with concrete filesystem behavior:

```python
def atomic_write_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def build_journal(
    state_dir: Path,
    transition_id: str,
    event: str,
    expected_revision: int,
    next_revision: int,
    updates: dict[str, str],
) -> dict[str, object]:
    files = {}
    for name, target_text in sorted(updates.items()):
        current_text = (state_dir / name).read_text(encoding="utf-8")
        files[name] = {
            "original_sha256": sha256_bytes(current_text.encode("utf-8")),
            "target_sha256": sha256_bytes(target_text.encode("utf-8")),
            "target_text": target_text,
        }
    return {
        "transition_id": transition_id,
        "event": event,
        "expected_revision": expected_revision,
        "next_revision": next_revision,
        "status": "pending",
        "files": files,
    }


def write_journal(state_dir: Path, journal: dict[str, object]) -> None:
    directory = state_dir / ".transitions"
    directory.mkdir(exist_ok=True)
    path = directory / f"{journal['transition_id']}.json"
    atomic_write_text(path, json.dumps(journal, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def mark_journal_complete(state_dir: Path, transition_id: str) -> None:
    pending = state_dir / ".transitions" / f"{transition_id}.json"
    complete = pending.with_name(f"{transition_id}.complete.json")
    os.replace(pending, complete)
```

`recover_pending_transaction()` finds exactly one non-complete journal. For each non-loop file, it accepts the original or target hash and writes the target when original. For `loop-state.md`, it also accepts an intermediate form whose `pending_transition` equals the journal ID. Any other hash is divergent and raises `ValueError`. Recovery writes the final loop target last and renames the journal complete. If no pending journal exists it returns `None`; if more than one exists it fails for manual inspection.

- [ ] **Step 4: Add the CLI wrapper**

Create `transition-state.py` with two supported forms:

```text
python transition-state.py --target <project> --recover
python transition-state.py --target <project> --event <name> --set loop-state.md:status=blocked --set loop-state.md:stop_reason=environment_blocked
```

Parse each `--set` value with `partition(":")` and `partition("=")`, update top-level keys through `set_top_level_value()`, and call `apply_transaction()` with the current `state_revision`.

- [ ] **Step 5: Run recovery tests and commit**

```powershell
python -m unittest tests.test_webbuilder_state_kernel.StateTransitionTests -v
python -m unittest discover -s tests -v
git add webbuilder/scripts/state_transition.py webbuilder/scripts/transition-state.py tests/test_webbuilder_state_kernel.py
git commit -m "feat: add journaled WebBuilder state transitions"
```

Expected: injected interruption recovers once, stale revision is rejected, and all tests pass.

---

### Task 4: Initialize and Migrate Schema 1.4

**Files:**
- Modify: `webbuilder/scripts/init-state.py:13-350`
- Modify: `webbuilder/scripts/migrate-state.py:27-251`
- Modify: `webbuilder/scripts/check-state.py:72-151,284-463`
- Modify: `tests/test_spec2web_state_scripts.py`
- Modify: `tests/test_webbuilder_state_kernel.py`

**Interfaces:**
- Consumes: schema constants and transaction API.
- Produces: schema 1.4 templates and non-destructive 1.0-1.3 migration.

- [ ] **Step 1: Change characterization expectations through new failing tests**

Add a new test without deleting the 1.3 fixture behavior:

```python
def test_init_creates_schema_1_4_runtime_fields(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        self.assertEqual(self.run_init(tmp).returncode, 0)
        loop = (Path(tmp) / STATE_DIR_NAME / "loop-state.md").read_text(encoding="utf-8")
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
```

Add migration assertions that a schema 1.3 fixture becomes 1.4, retains `custom-note: preserve-me`, creates one backup, defaults to guided, and reports already-1.4 on repeated apply.

- [ ] **Step 2: Run the new tests and observe 1.3 output**

```powershell
python -m unittest tests.test_spec2web_state_scripts.Spec2WebStateScriptTests.test_init_creates_schema_1_4_runtime_fields -v
```

Expected: failure because initialization still writes `schema_version: 1.3` and lacks the new fields.

- [ ] **Step 3: Update initialization templates**

Set the loop template to:

```text
workflow: spec2web
schema_version: 1.4
status: active
current_phase: project_rules
current_task: null
active_parallel_group: null
delivery_mode: guided
autonomy_scope: unconfirmed
stop_reason: none
resume_checkpoint: none
active_run_id: null
state_revision: 1
pending_transition: null
execution_mode: single
host_agent_capability: unknown
available_child_slots: unknown
selected_workers: 0
active_checker_strategy: single_session
```

Add task defaults:

```text
- task_repair_attempt: 0
- task_failure_fingerprint: none
- task_same_fingerprint_count: 0
- integration_repair_attempt: 0
- integration_failure_fingerprint: none
- integration_same_fingerprint_count: 0
```

Retain the legacy `repair_attempt`, `last_failure_fingerprint`, and `same_fingerprint_count` only during migration input parsing, not in new templates.

Initialization also creates `webbuilder/.gitignore` when absent, without overwriting an existing file:

```gitignore
.transitions/
.migration-backup-*/
```

Add a test that both directories are ignored in a temporary Git project and that rerunning initialization preserves a user-edited `webbuilder/.gitignore`.

- [ ] **Step 4: Update migration and structure checks**

Accept source versions 1.0-1.3. Populate the six new repair fields from the three legacy values and add the new loop fields. Write changed files through `apply_transaction()` after creating the timestamped migration backup; use event `migrate-schema-1.4` and expected revision `0` when the source lacks `state_revision`.

Update structure checks so schema 1.4 and all runtime fields are required. Reject explicit versions outside `SUPPORTED_SOURCE_VERSIONS | {SCHEMA_VERSION}`.

- [ ] **Step 5: Run migration and complete-suite tests**

```powershell
python -m unittest tests.test_spec2web_state_scripts -v
python -m unittest tests.test_webbuilder_state_kernel -v
python -m unittest discover -s tests -v
```

Expected: all tests pass with assertions updated to schema 1.4; existing content-preservation and idempotence tests remain present.

- [ ] **Step 6: Commit**

```powershell
git add webbuilder/scripts/init-state.py webbuilder/scripts/migrate-state.py webbuilder/scripts/check-state.py tests/test_spec2web_state_scripts.py tests/test_webbuilder_state_kernel.py
git commit -m "feat: migrate WebBuilder state to schema 1.4"
```

---

### Task 5: Enforce Checker Strategy and Separate Repair Budgets

**Files:**
- Modify: `webbuilder/scripts/check-state.py:36-70,440-461,513-531,830-897`
- Modify: `tests/test_spec2web_state_scripts.py:440-477,557-574`
- Modify: `webbuilder/references/role-protocol.md:105-109`
- Modify: `webbuilder/references/loop-engineering.md` repair section

**Interfaces:**
- Consumes: task `checker_strategy`, risk level, six repair fields, and acceptance record identities.
- Produces: conditional identity validation and task/integration repair-state validation.

- [ ] **Step 1: Reverse the incorrect independent-checker regression test**

Replace the old assertion that identical Tester/Reviewer identities always fail with two explicit cases:

```python
def test_acceptance_allows_one_independent_checker_for_standard_work(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        self.assertEqual(self.run_init(tmp).returncode, 0)
        self.make_execution_ready(tmp)
        state_dir = Path(tmp) / STATE_DIR_NAME
        task_plan = state_dir / "task-plan.md"
        text = task_plan.read_text(encoding="utf-8")
        text = text.replace("status: pending", "status: submitted_for_acceptance")
        text = text.replace("checker_strategy: single_session", "checker_strategy: independent_checker")
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
        text = text.replace("checker_strategy: single_session", "checker_strategy: separate_tester_reviewer")
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
        self.assertIn("separate_tester_reviewer requires distinct identities", result.stdout)
```

Use the existing test helpers and full acceptance record text; do not introduce a mock validator.

- [ ] **Step 2: Run both tests and observe the semantic conflict**

```powershell
python -m unittest tests.test_spec2web_state_scripts.Spec2WebStateScriptTests.test_acceptance_allows_one_independent_checker_for_standard_work -v
python -m unittest tests.test_spec2web_state_scripts.Spec2WebStateScriptTests.test_acceptance_requires_three_identities_for_separate_strategy -v
```

Expected: the first test fails under the current unconditional three-identity rule.

- [ ] **Step 3: Implement strategy-aware identity checks**

Replace the unconditional `len(set(identities)) != 3` block with:

```python
developer = record_value(record, "developer_identity")
tester = record_value(record, "tester_identity")
reviewer = record_value(record, "reviewer_identity")
checker_strategy = task_field_value(body, "checker_strategy")

if checker_strategy == "independent_checker":
    if usable_evidence(developer) and developer in {tester, reviewer}:
        errors.append(f"{task_id} independent checker must differ from Developer")
elif checker_strategy == "separate_tester_reviewer":
    identities = [developer, tester, reviewer]
    if all(usable_evidence(value) for value in identities) and len(set(identities)) != 3:
        errors.append(
            f"{task_id} separate_tester_reviewer requires distinct identities"
        )
elif checker_strategy == "single_session" and risk_level not in {"low"}:
    errors.append(f"{task_id} single_session acceptance is limited to low-risk work")
```

Compute `risk_level` before this block.

- [ ] **Step 4: Add separate repair-counter tests and validation**

Test task and integration counters independently. An integration counter of 6 must fail without changing a valid task counter of 2; a task repeated fingerprint count of 3 must block task dispatch.

Implement:

```python
def repair_scope_errors(task_id: str, body: str, scope: str, budget: int) -> list[str]:
    attempt = task_field_value(body, f"{scope}_repair_attempt")
    repeated = task_field_value(body, f"{scope}_same_fingerprint_count")
    errors = []
    if attempt is None or not attempt.isdigit():
        errors.append(f"{task_id} {scope}_repair_attempt must be a non-negative integer")
    elif int(attempt) > budget:
        errors.append(f"{task_id} {scope}_repair_attempt exceeds budget {budget}")
    if repeated is None or not repeated.isdigit():
        errors.append(f"{task_id} {scope}_same_fingerprint_count must be a non-negative integer")
    elif int(repeated) >= 3:
        errors.append(f"{task_id} repeated {scope} failure fingerprint requires block")
    return errors
```

Use budget 3 in task dispatch/acceptance and budget 5 in integration.

- [ ] **Step 5: Update role and repair references**

Document that same-model fresh sessions can satisfy process independence, but deterministic evidence remains mandatory; `independent_checker` allows one checker identity for Tester and Reviewer, while `separate_tester_reviewer` requires three distinct identities.

- [ ] **Step 6: Verify and commit**

```powershell
python -m unittest discover -s tests -v
git diff --check
git add webbuilder/scripts/check-state.py tests/test_spec2web_state_scripts.py webbuilder/references/role-protocol.md webbuilder/references/loop-engineering.md
git commit -m "fix: enforce task-owned checker and repair strategies"
```

---

### Task 6: Route the Skill Through the State Kernel

**Files:**
- Modify: `webbuilder/SKILL.md:27-82,127-165,204-220,338-365`
- Modify: `webbuilder/references/state-files.md`
- Modify: `webbuilder/references/multi-agent-orchestration.md`
- Modify: `webbuilder/references/worktree-mode.md`
- Modify: `README.md`
- Modify: `README_EN.md`
- Test: `tests/test_spec2web_state_scripts.py:875-889`

**Interfaces:**
- Consumes: completed schema, transition, migration, checker, and repair APIs.
- Produces: user/agent instructions that cannot bypass the State Kernel.

- [ ] **Step 1: Add failing routing assertions**

Extend `test_skill_routes_to_strategy_and_interface_references`:

```python
self.assertIn("schema_version: 1.4", text)
self.assertIn("scripts/transition-state.py", text)
self.assertIn("--recover", text)
self.assertIn("pending_transition", text)
self.assertIn("task_repair_attempt", text)
self.assertIn("integration_repair_attempt", text)
```

Run the single test. Expected: failure because the Skill still documents schema 1.3.

- [ ] **Step 2: Update workflow instructions**

Require recovery before every resume:

```text
python <skill-root>/scripts/transition-state.py --target <project-root> --recover
python <skill-root>/scripts/check-state.py --target <project-root> --phase structure
```

State that agents may edit descriptive content, but may not manually set approval, readiness, acceptance, integration, stop/resume, or delivery success values.

- [ ] **Step 3: Update state and worktree references**

Document schema 1.4 fields, transaction journals, canonical state ownership, separate repair scopes, and the rule that accepted evidence must be copied before worktree cleanup. Do not describe Evidence Kernel details scheduled for Plan 3 beyond the artifact handoff boundary.

- [ ] **Step 4: Run full release verification**

```powershell
python -m unittest discover -s tests -v
python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" webbuilder
git diff --check
```

Expected: all tests pass, Skill validation prints `Skill is valid!`, and diff check is clean.

- [ ] **Step 5: Commit**

```powershell
git add webbuilder/SKILL.md webbuilder/references/state-files.md webbuilder/references/multi-agent-orchestration.md webbuilder/references/worktree-mode.md README.md README_EN.md tests/test_spec2web_state_scripts.py
git commit -m "docs: route WebBuilder through the state kernel"
```

## Plan 1 Exit Gate

- [ ] Tests are tracked and run on Windows/Linux CI.
- [ ] New initialization produces schema 1.4 and migrated projects default to guided.
- [ ] Migration is dry-run safe, backed up, idempotent, and content-preserving.
- [ ] Interrupted multi-file transactions recover or reject divergent state.
- [ ] `independent_checker` and `separate_tester_reviewer` enforce different identity rules.
- [ ] Task and integration repair state are independent.
- [ ] Autonomous execution is still disabled.
