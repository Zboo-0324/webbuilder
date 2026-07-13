# WebBuilder Contract and Applicability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add guided/autonomous Solution Contracts with canonical revision approval, material-change invalidation, a capability applicability matrix, workload envelopes, and a deterministic specification gate.

**Architecture:** Store the human-readable contract and one canonical `json contract-material` block inside `requirements-baseline.md`. `contract_core.py` parses and validates that block, hashes canonical material fields, and compares revisions; `approve-contract.py` applies approval and invalidation through the State Kernel transaction API.

**Tech Stack:** Python 3.12+ standard library (`json`, `hashlib`, `re`, `argparse`), Markdown plus embedded canonical JSON, `unittest`.

## Global Constraints

- Plan 1 exit gate must be complete and green.
- `requirements-baseline.md` alone owns contract approval metadata.
- `loop-state.md` alone owns delivery mode, autonomy scope, phase, stop reason, run, checkpoint, revision, and pending transition.
- Approval digest covers material contract fields only; timestamps, actor metadata, evidence references, runtime state, and digest values are excluded.
- Material changes invalidate approval and derived readiness; ordinary task decomposition and bounded implementation detail changes do not.
- Security and performance have required baseline profiles; no project may mark security wholly not applicable.
- `not_applicable` requires a capability-specific reason; unavailable host tooling is `environment_blocked`, not `not_applicable`.
- Autonomous execution remains disabled until Plan 4.

---

### Task 1: Add the Schema 1.4 Contract Skeleton

**Files:**
- Modify: `webbuilder/scripts/init-state.py` requirements/system/task templates
- Modify: `webbuilder/scripts/migrate-state.py`
- Modify: `webbuilder/scripts/check-state.py` structure markers
- Modify: `tests/test_spec2web_state_scripts.py`
- Modify: `tests/test_webbuilder_state_kernel.py`

**Interfaces:**
- Consumes: Plan 1 schema and transaction modules.
- Produces: stable contract metadata and `based_on_contract_revision` fields for later contract APIs.

- [ ] **Step 1: Write failing initialization assertions**

Add to the schema 1.4 initialization test:

```python
requirements = (state_dir / "requirements-baseline.md").read_text(encoding="utf-8")
system_design = (state_dir / "system-design.md").read_text(encoding="utf-8")
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
```

- [ ] **Step 2: Run the test and observe missing fields**

```powershell
python -m unittest tests.test_spec2web_state_scripts.Spec2WebStateScriptTests.test_init_creates_schema_1_4_runtime_fields -v
```

Expected: failure on `confirmation_status: pending`.

- [ ] **Step 3: Add the canonical material block**

Initialize `requirements-baseline.md` with this exact shape:

````markdown
confirmation_status: pending
contract_revision: 1
approved_contract_revision: null
approval_digest: null
approval_scope: requirements_design_stack_ui_execution
approval_evidence: null
approved_by: null
approved_at: null
discovery_method: interactive

## Solution Contract

```json contract-material
{
  "problem": "not recorded",
  "desired_outcome": "not recorded",
  "target_users": [],
  "primary_jobs": [],
  "core_capabilities": [],
  "non_goals": [],
  "primary_workflows": [],
  "page_navigation_summary": "not recorded",
  "ui_direction": "not recorded",
  "technology_profile": "not recorded",
  "public_interfaces": [],
  "data_boundary": "not recorded",
  "permission_boundary": "not recorded",
  "delivery_assumptions": [],
  "material_risks": [],
  "acceptance_signals": [],
  "capabilities": {},
  "workload_envelope": {
    "task_count": "not estimated",
    "browser_flows": [],
    "external_dependencies": [],
    "quality_gates": [],
    "repair_budgets": {"task": 3, "integration": 5},
    "available_concurrency": "unknown"
  }
}
```
````

Add `based_on_contract_revision: 1` near the top of system design and task plan.

- [ ] **Step 4: Migrate 1.3 content without inventing approval**

Migration adds the fields above with `confirmation_status: pending`, `approved_contract_revision: null`, and `discovery_method: interactive`. It generates contract material from existing confirmed-requirement text only when fields can be copied literally; all unresolved values remain `not recorded`, and migration never marks the contract approved.

- [ ] **Step 5: Verify and commit**

```powershell
python -m unittest tests.test_spec2web_state_scripts -v
python -m unittest tests.test_webbuilder_state_kernel -v
git add webbuilder/scripts/init-state.py webbuilder/scripts/migrate-state.py webbuilder/scripts/check-state.py tests/test_spec2web_state_scripts.py tests/test_webbuilder_state_kernel.py
git commit -m "feat: add schema 1.4 solution contract fields"
```

---

### Task 2: Implement Canonical Contract Parsing and Digesting

**Files:**
- Create: `webbuilder/scripts/contract_core.py`
- Create: `tests/test_webbuilder_contract.py`

**Interfaces:**
- Consumes: `state_schema.markdown_section()` and `sha256_bytes()`.
- Produces: `extract_contract_material()`, `canonical_contract_bytes()`, `contract_digest()`, `validate_capabilities()`, and `contract_revision_errors()`.

- [ ] **Step 1: Write canonicalization tests**

Create `tests/test_webbuilder_contract.py`:

```python
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
```

- [ ] **Step 2: Run the tests and observe the missing module**

```powershell
python -m unittest tests.test_webbuilder_contract.ContractCoreTests -v
```

Expected: import failure for `contract_core`.

- [ ] **Step 3: Implement canonical parsing**

Create `contract_core.py`:

```python
from __future__ import annotations

import json
import re
from pathlib import Path

from state_schema import read_state_files, sha256_bytes, top_level_value

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
    value = json.loads(matches[0])
    if not isinstance(value, dict):
        raise ValueError("contract material must be a JSON object")
    missing = [field for field in MATERIAL_FIELDS if field not in value]
    if missing:
        raise ValueError("contract material missing fields: " + ", ".join(missing))
    return value


def canonical_contract_bytes(material: dict[str, object]) -> bytes:
    selected = {field: material[field] for field in MATERIAL_FIELDS}
    text = json.dumps(selected, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text.encode("utf-8")


def contract_digest(material: dict[str, object]) -> str:
    return sha256_bytes(canonical_contract_bytes(material))
```

- [ ] **Step 4: Add malformed and duplicate-block tests**

Assert invalid JSON, missing material fields, non-object JSON, and two contract blocks each raise a specific `ValueError`; do not silently select the first block.

- [ ] **Step 5: Verify and commit**

```powershell
python -m unittest tests.test_webbuilder_contract.ContractCoreTests -v
python -m unittest discover -s tests -v
git add webbuilder/scripts/contract_core.py tests/test_webbuilder_contract.py
git commit -m "feat: add canonical solution contract digest"
```

---

### Task 3: Approve and Invalidate Contract Revisions Transactionally

**Files:**
- Create: `webbuilder/scripts/approve-contract.py`
- Modify: `webbuilder/scripts/contract_core.py`
- Modify: `tests/test_webbuilder_contract.py`

**Interfaces:**
- Consumes: Plan 1 `apply_transaction()` and Plan 2 Task 2 digest API.
- Produces: approval and invalidation CLI; material/non-material change classification.

- [ ] **Step 1: Write directory-level approval tests**

Use `subprocess.run()` with a temporary initialized project. Fill every contract field, set `discovery_method: inferred_contract`, then run:

```powershell
python webbuilder/scripts/approve-contract.py --target <tmp> --approval-evidence user-message-42
```

Assertions:

```python
self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
self.assertIn("confirmation_status: approved", requirements)
self.assertIn("approved_contract_revision: 1", requirements)
self.assertRegex(requirements, r"approval_digest: sha256:[0-9a-f]{64}")
self.assertIn("approved_by: user", requirements)
self.assertIn("based_on_contract_revision: 1", system_design)
self.assertIn("based_on_contract_revision: 1", task_plan)
self.assertIn("autonomy_scope: confirmed_plan", loop_state)
self.assertEqual(top_level_value(loop_state, "state_revision"), "2")
```

Also test that a second identical approval is idempotent and does not increment `contract_revision`.

- [ ] **Step 2: Run the test and observe the missing CLI**

```powershell
python -m unittest tests.test_webbuilder_contract.ContractApprovalTests -v
```

Expected: failure because `approve-contract.py` does not exist.

- [ ] **Step 3: Implement approval through one transaction**

The CLI reads the three derived files and loop state, validates material and applicability, computes the digest, sets approval metadata, and calls:

```python
transition_id = apply_transaction(
    state_dir,
    "approve-contract",
    {
        "requirements-baseline.md": approved_requirements,
        "system-design.md": set_top_level_value(system_design, "based_on_contract_revision", revision),
        "task-plan.md": set_top_level_value(task_plan, "based_on_contract_revision", revision),
        "loop-state.md": set_top_level_value(loop_state, "autonomy_scope", "confirmed_plan"),
    },
    expected_revision=int(top_level_value(loop_state, "state_revision") or "0"),
)
```

Use `datetime.now(timezone.utc).isoformat()` for `approved_at`, literal `user` for `approved_by`, and the CLI value for approval evidence.

- [ ] **Step 4: Implement material-change invalidation**

Add:

```python
def material_contract_changed(before: dict[str, object], after: dict[str, object]) -> bool:
    return canonical_contract_bytes(before) != canonical_contract_bytes(after)
```

When a changed contract is saved, the invalidation command increments `contract_revision`, sets confirmation pending, clears approved revision/digest/actor/time/evidence, sets `autonomy_scope: unconfirmed`, and writes `based_on_contract_revision: stale` to design and plan in one transaction.

The CLI form is:

```text
python approve-contract.py --target <project> --invalidate-material-change
```

Test that editing task titles alone does not invoke invalidation and does not change the contract revision.

- [ ] **Step 5: Verify and commit**

```powershell
python -m unittest tests.test_webbuilder_contract -v
python -m unittest discover -s tests -v
git add webbuilder/scripts/approve-contract.py webbuilder/scripts/contract_core.py tests/test_webbuilder_contract.py
git commit -m "feat: approve revisioned solution contracts"
```

---

### Task 4: Validate Capability Applicability and Workload Envelopes

**Files:**
- Modify: `webbuilder/scripts/contract_core.py`
- Modify: `webbuilder/scripts/check-state.py`
- Modify: `tests/test_webbuilder_contract.py`

**Interfaces:**
- Consumes: contract material and current project shape.
- Produces: `validate_capabilities()` and `--phase specification`.

- [ ] **Step 1: Write capability-matrix tests**

Create complete fixtures for a UI project and an API-only project:

```python
import copy


def complete_material() -> dict[str, object]:
    material = copy.deepcopy(ContractCoreTests.MATERIAL)
    material["capabilities"] = {
        "ui": {"status": "required", "reason": "reviewers use a browser workflow"},
        "database": {"status": "required", "reason": "decisions persist"},
        "authentication": {"status": "required", "reason": "reviewer access is private"},
        "rbac": {"status": "not_applicable", "reason": "the approved MVP has one role"},
        "audit": {"status": "not_applicable", "reason": "decision history is outside MVP scope"},
        "docker": {"status": "not_applicable", "reason": "local Python startup is the delivery contract"},
        "accessibility": {"status": "required", "reason": "UI is required"},
        "performance": {"status": "required", "profile": "baseline"},
        "security": {"status": "required", "profile": "baseline"},
    }
    material["workload_envelope"] = {
        "task_count": "4-6",
        "browser_flows": ["login", "review decision"],
        "external_dependencies": [],
        "quality_gates": ["functional", "ui", "accessibility", "performance", "security", "delivery-smoke"],
        "repair_budgets": {"task": 3, "integration": 5},
        "available_concurrency": "unknown",
    }
    return material


def complete_api_material() -> dict[str, object]:
    material = complete_material()
    material["page_navigation_summary"] = "not applicable: API-only service"
    material["ui_direction"] = "not applicable: API-only service"
    material["capabilities"]["ui"] = {"status": "not_applicable", "reason": "approved product is API-only"}
    material["capabilities"]["accessibility"] = {"status": "not_applicable", "reason": "no rendered user interface"}
    material["workload_envelope"]["browser_flows"] = []
    material["workload_envelope"]["quality_gates"] = ["functional", "performance", "security", "delivery-smoke"]
    return material


def test_security_and_performance_are_always_required(self) -> None:
    material = complete_material()
    material["capabilities"]["security"] = {
        "status": "not_applicable",
        "reason": "small project",
    }
    self.assertIn("security status must be required", validate_capabilities(material))

def test_ui_requires_accessibility(self) -> None:
    material = complete_material()
    material["capabilities"]["ui"] = {"status": "required", "reason": "browser UI"}
    material["capabilities"]["accessibility"] = {
        "status": "not_applicable",
        "reason": "not evaluated",
    }
    self.assertIn("accessibility is required when ui is required", validate_capabilities(material))

def test_api_only_contract_can_omit_ui_with_a_reason(self) -> None:
    material = complete_api_material()
    self.assertEqual(validate_capabilities(material), [])
```

- [ ] **Step 2: Run tests and observe missing validation**

```powershell
python -m unittest tests.test_webbuilder_contract.ContractCapabilityTests -v
```

Expected: import or assertion failure because capability rules are absent.

- [ ] **Step 3: Implement explicit capability rules**

Define:

```python
CAPABILITY_NAMES = (
    "ui", "database", "authentication", "rbac", "audit",
    "docker", "accessibility", "performance", "security",
)
VALID_APPLICABILITY = {"required", "not_applicable"}
```

Validate every capability exists, status is valid, every `not_applicable` has a non-empty reason, security/performance are required with `baseline` or stronger profiles, UI implies accessibility, RBAC implies authentication, and database-required contracts describe initialization or migration in delivery assumptions.

Validate `workload_envelope` has task count, browser flows, external dependencies, quality gates, repair budgets exactly `{task: 3, integration: 5}`, and available concurrency. Reject numeric token/API/time/interruption estimates under keys `token_count`, `api_calls`, `elapsed_minutes`, or `interruptions`.

- [ ] **Step 4: Add the specification phase**

Extend checker choices with `specification`. `check_specification_readiness()` validates:

- complete contract material and applicability;
- no `not recorded` material values;
- acceptance signals and primary workflows are non-empty;
- system design and task plan reference the current contract revision;
- before execution, approval digest matches the canonical current contract.

Before approval, allow `confirmation_status: pending` but validate digest input. During execution readiness, require `approved` and matching revision/digest.

Implement the shared revision check used by specification, execution, and delivery:

```python
def contract_revision_errors(state_dir: Path) -> list[str]:
    texts = read_state_files(
        state_dir,
        ("requirements-baseline.md", "system-design.md", "task-plan.md"),
    )
    requirements = texts["requirements-baseline.md"]
    current = top_level_value(requirements, "contract_revision")
    approved = top_level_value(requirements, "approved_contract_revision")
    recorded_digest = top_level_value(requirements, "approval_digest")
    errors: list[str] = []
    if not current or approved != current:
        errors.append("approved contract revision does not match current revision")
        return errors
    try:
        expected_digest = contract_digest(extract_contract_material(requirements))
    except ValueError as exc:
        return [str(exc)]
    if recorded_digest != expected_digest:
        errors.append("approval digest does not match current contract material")
    for filename in ("system-design.md", "task-plan.md"):
        if top_level_value(texts[filename], "based_on_contract_revision") != current:
            errors.append(f"{filename} is stale for contract revision {current}")
    return errors
```

- [ ] **Step 5: Verify and commit**

```powershell
python -m unittest tests.test_webbuilder_contract -v
python -m unittest discover -s tests -v
git add webbuilder/scripts/contract_core.py webbuilder/scripts/check-state.py tests/test_webbuilder_contract.py
git commit -m "feat: validate contract capability applicability"
```

---

### Task 5: Route Guided and Autonomous Discovery Through the Contract Gate

**Files:**
- Modify: `webbuilder/SKILL.md` discovery, hard-gate, and continuation sections
- Modify: `webbuilder/references/state-files.md`
- Modify: `webbuilder/references/technology-strategy.md`
- Modify: `webbuilder/references/interface-design.md`
- Modify: `README.md`
- Modify: `README_EN.md`
- Modify: `tests/test_spec2web_state_scripts.py`

**Interfaces:**
- Consumes: specification and approval CLIs.
- Produces: one user-facing workflow with guided and autonomous discovery methods.

- [ ] **Step 1: Add failing Skill routing assertions**

Assert `SKILL.md` contains:

```python
self.assertIn("delivery_mode: guided | autonomous", text)
self.assertIn("discovery_method: interactive | inferred_contract", text)
self.assertIn("scripts/approve-contract.py", text)
self.assertIn("--phase specification", text)
self.assertIn("workload envelope", text.lower())
self.assertIn("declared stop condition", text.lower())
```

Run the routing test. Expected: failure on the new contract CLI.

- [ ] **Step 2: Document guided and autonomous entry rules**

Guided retains one-question-at-a-time discovery and sets `discovery_method: interactive`. Autonomous internally drafts the same artifacts, sets `discovery_method: inferred_contract`, runs the specification phase, presents one consolidated contract, and waits for approval.

Both modes execute:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase specification
python <skill-root>/scripts/approve-contract.py --target <project-root> --approval-evidence <user-message-reference>
```

Existing and migrated projects stay guided until the user explicitly selects autonomous.

- [ ] **Step 3: Document material-change and authorization rules**

List exact material fields that trigger invalidation. State that low-risk dependency selection, component details, task reordering, test repair, and bounded implementation choices do not change the contract unless they change a material field.

The contract does not authorize credentials, paid resources, production deployment, destructive external writes, irreversible migration, high-risk install scripts, or secret transmission.

- [ ] **Step 4: Verify and commit**

```powershell
python -m unittest discover -s tests -v
python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" webbuilder
git diff --check
git add webbuilder/SKILL.md webbuilder/references/state-files.md webbuilder/references/technology-strategy.md webbuilder/references/interface-design.md README.md README_EN.md tests/test_spec2web_state_scripts.py
git commit -m "docs: define guided and autonomous contract gates"
```

## Plan 2 Exit Gate

- [ ] Contract JSON has one canonical format and stable digest.
- [ ] Approval and invalidation are one journaled transaction.
- [ ] Material changes invalidate approval; ordinary internal changes do not.
- [ ] Capability applicability rejects unsafe or unjustified omissions.
- [ ] Specification gate works before approval and execution gate requires approval.
- [ ] Guided mode remains compatible and autonomous execution remains disabled.
