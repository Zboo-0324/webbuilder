# WebBuilder Autonomous Full-Stack Delivery Implementation Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this roadmap through its four linked plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement every requirement and all 13 acceptance criteria in `docs/superpowers/specs/2026-07-12-webbuilder-autonomous-fullstack-delivery-design.md` while preserving WebBuilder as one portable Skill with local files and small deterministic Python tools.

**Architecture:** Build the autonomous path as four ordered, independently testable increments: State Kernel, Solution Contract, Evidence/Host Capability, and an opt-in end-to-end loop. Shared standard-library modules provide schema parsing, journaled state transactions, canonical contract hashing, evidence manifests, and host capability records; `SKILL.md` remains the workflow router and no background service is introduced.

**Tech Stack:** Python 3.12+ standard library for WebBuilder tooling; Markdown and JSON state/artifact formats; `unittest`; Git and GitHub Actions; Django 5.2 LTS, SQLite, server-rendered HTML/CSS/JavaScript, and Playwright Python for the maintained end-to-end reference profile.

## Global Constraints

- The final product remains one Skill plus local files and small deterministic Python tools; do not add a server, worker pool, database-backed scheduler, plugin runtime, or required external AI provider.
- Preserve the seven state files: `project-rules.md`, `requirements-baseline.md`, `system-design.md`, `task-plan.md`, `loop-state.md`, `validation-log.md`, and `delivery-report.md`.
- Schema 1.4 migration must be non-destructive, idempotent, backed up, and default migrated projects to `guided`.
- Use only the Python standard library in `webbuilder/scripts/`; example-project dependencies remain isolated under `examples/autonomous-reference/`.
- Keep descriptive Markdown human-editable; machine-owned readiness, approval, stop, resume, acceptance, integration, and delivery transitions go through deterministic tools.
- `loop-state.md` alone owns runtime mode, phase, stop reason, checkpoint, active run, state revision, and pending transaction.
- Contract approval covers material scope and boundaries, not ordinary task decomposition or bounded low-risk repairs.
- Baseline security is always required; `not_applicable` is capability-specific and requires a concrete reason.
- Evidence must match the approved contract revision and implementation fingerprint and must pass existence, hash, supersession, and redaction checks.
- Autonomous execution stays opt-in until the narrow end-to-end profile passes stop/resume, evidence-tamper, host-degradation, and final-delivery tests.
- Follow repository `AGENTS.md`: read before writing, use test-first bug/feature development, keep diffs surgical, avoid new dependencies without justification, and verify before completion claims.

---

## 1. Ordered Plan Set

| Order | Plan | Independently testable deliverable | Depends on |
|---|---|---|---|
| 1 | `2026-07-12-webbuilder-state-kernel-implementation.md` | Tracked tests and CI; shared schema 1.4; idempotent migration; journaled state transitions; strategy-aware checker identities; separate repair counters | Current schema 1.3 baseline |
| 2 | `2026-07-12-webbuilder-contract-applicability-implementation.md` | Contract material parser; canonical digest; approval/invalidation transitions; applicability validation; specification gate | Plan 1 APIs |
| 3 | `2026-07-12-webbuilder-evidence-host-capability-implementation.md` | Evidence capture and verification; artifact retention/redaction; host capability record; host/init/UI/delivery gates | Plans 1-2 APIs |
| 4 | `2026-07-12-webbuilder-autonomous-e2e-rollout-implementation.md` | One maintained golden profile; full autonomous stop/resume loop; prompt/host/tamper evaluations; opt-in rollout and documentation | Plans 1-3 complete |

Do not execute plans concurrently. Each later plan consumes exact public interfaces introduced by earlier plans and assumes the earlier plan's full verification suite is green.

## 2. Target File Map

### Shared deterministic tooling

| File | Responsibility |
|---|---|
| `webbuilder/scripts/state_schema.py` | Schema constants, state-directory resolution, Markdown key/list/section parsing, canonical text and file fingerprint helpers |
| `webbuilder/scripts/state_transition.py` | Journaled multi-file transaction creation, apply, recovery, state revision, and pending-transition enforcement |
| `webbuilder/scripts/transition-state.py` | CLI wrapper for recovery and explicit lifecycle transitions |
| `webbuilder/scripts/contract_core.py` | Contract JSON extraction, canonical serialization, digest, material-change comparison, and applicability validation |
| `webbuilder/scripts/approve-contract.py` | CLI that approves or invalidates a contract through `state_transition.apply_transaction()` |
| `webbuilder/scripts/evidence_core.py` | Evidence manifest schema, command capture, redaction, artifact hashing, implementation fingerprint, verification, and canonical artifact copy |
| `webbuilder/scripts/capture-evidence.py` | CLI for deterministic command/browser-report evidence capture |
| `webbuilder/scripts/host_capabilities.py` | Capability record schema, local probes, explicit host reports, contract matching, and downgrade/block decisions |
| `webbuilder/scripts/check-host.py` | CLI that records and validates host capabilities through the State Kernel |

### Existing tooling modified in place

| File | Planned change |
|---|---|
| `webbuilder/scripts/init-state.py` | Generate schema 1.4 state and all contract/runtime/evidence skeleton fields |
| `webbuilder/scripts/migrate-state.py` | Migrate 1.0-1.3 to 1.4 through backups and journaled writes |
| `webbuilder/scripts/check-state.py` | Import shared schema helpers; add specification, host, initialization, UI, evidence, revision, and strategy-aware gates |

### Tests and release engineering

| File | Responsibility |
|---|---|
| `.gitignore` | Stop ignoring `tests/`; ignore `.webbuilder-artifacts/` and migration/transition scratch data |
| `.github/workflows/test.yml` | Cross-platform standard-library tests and UTF-8 Skill validation |
| `tests/test_spec2web_state_scripts.py` | Existing characterization suite and backward-compatibility assertions |
| `tests/test_webbuilder_state_kernel.py` | Schema, migration, transaction interruption/recovery, revision, and repair-counter tests |
| `tests/test_webbuilder_contract.py` | Contract digest, approval, invalidation, applicability, and specification-gate tests |
| `tests/test_webbuilder_evidence.py` | Command capture, redaction, hash, supersession, stale evidence, and canonical-copy tests |
| `tests/test_webbuilder_host_capabilities.py` | Probe/report validation and safe downgrade/block tests |
| `tests/test_webbuilder_autonomous_e2e.py` | Reference-profile initialize/approve/execute/stop/resume/deliver flow |
| `tests/test_webbuilder_installation.py` | Copied-tree structure and init/migrate/check smoke tests for Codex, Claude, and Hermes install layouts |

### Skill, references, and example

| File | Responsibility |
|---|---|
| `webbuilder/SKILL.md` | Route autonomous phases to deterministic tools and preserve guided behavior |
| `webbuilder/references/state-files.md` | Schema 1.4 templates, ownership, transaction, staleness, and evidence records |
| `webbuilder/references/role-protocol.md` | Strategy-aware checker identity rules and authorization boundary |
| `webbuilder/references/multi-agent-orchestration.md` | Host-capability gate and safe execution-mode degradation |
| `webbuilder/references/interface-design.md` | Affected-flow UI checks and final risk-based matrix |
| `webbuilder/references/technology-strategy.md` | Versioned profile format, selection, validation, upgrade, and deprecation |
| `webbuilder/references/delivery-checklist.md` | Manifest-backed coverage and final evidence validity |
| `webbuilder/references/technology-profiles/django-5.2-lts.md` | First maintained golden profile |
| `examples/autonomous-reference/` | Django/SQLite vertical-slice project used by the end-to-end suite |

## 3. Cross-Plan Public Interfaces

Later plans must use these names and signatures without renaming them:

| Module | Exact public signature | Defined in |
|---|---|---|
| `state_schema.py` | `SCHEMA_VERSION: str = "1.4"` | Plan 1 Task 2 |
| `state_schema.py` | `resolve_state_dir(target: Path) -> Path` | Plan 1 Task 2 |
| `state_schema.py` | `read_state_files(state_dir: Path, names: Iterable[str]) -> dict[str, str]` | Plan 1 Task 2 |
| `state_schema.py` | `top_level_value(text: str, key: str) -> str | None` | Plan 1 Task 2 |
| `state_schema.py` | `set_top_level_value(text: str, key: str, value: str) -> str` | Plan 1 Task 2 |
| `state_schema.py` | `markdown_section(text: str, heading: str) -> str | None` | Plan 1 Task 2 |
| `state_schema.py` | `task_sections(text: str) -> dict[str, str]` | Plan 1 Task 2 |
| `state_schema.py` | `sha256_bytes(value: bytes) -> str` | Plan 1 Task 2 |
| `state_schema.py` | `direct_apply_fingerprint(project_root: Path, allowed_paths: Iterable[str]) -> str` | Plan 1 Task 2 |
| `state_transition.py` | `apply_transaction(state_dir: Path, event: str, updates: dict[str, str], *, expected_revision: int, fail_after_replacements: int | None = None) -> str` | Plan 1 Task 3 |
| `state_transition.py` | `recover_pending_transaction(state_dir: Path) -> str | None` | Plan 1 Task 3 |
| `contract_core.py` | `extract_contract_material(requirements_text: str) -> dict[str, object]` | Plan 2 Task 2 |
| `contract_core.py` | `canonical_contract_bytes(material: dict[str, object]) -> bytes` | Plan 2 Task 2 |
| `contract_core.py` | `contract_digest(material: dict[str, object]) -> str` | Plan 2 Task 2 |
| `contract_core.py` | `validate_capabilities(material: dict[str, object]) -> list[str]` | Plan 2 Task 4 |
| `contract_core.py` | `contract_revision_errors(state_dir: Path) -> list[str]` | Plan 2 Task 4 |
| `evidence_core.py` | `capture_command_evidence(project_root: Path, command: list[str], *, run_id: str, subject_id: str, attempt: int, contract_revision: int, allowed_paths: list[str], explicit_secrets: Iterable[str] = ()) -> Path` | Plan 3 Task 2 |
| `evidence_core.py` | `verify_manifest(manifest_path: Path, *, project_root: Path, expected_contract_revision: int, expected_fingerprint: str) -> list[str]` | Plan 3 Task 3 |
| `evidence_core.py` | `promote_artifacts(manifest_path: Path, destination_root: Path) -> Path` | Plan 3 Task 3 |
| `host_capabilities.py` | `CAPABILITY_NAMES: tuple[str, ...]` with `subagents`, `browser`, `git`, `worktree`, `docker`, `network`, `persistent_session` | Plan 3 Task 4 |
| `host_capabilities.py` | `inspect_local_capabilities(project_root: Path) -> dict[str, dict[str, str]]` | Plan 3 Task 4 |
| `host_capabilities.py` | `merge_host_report(inspected: dict[str, dict[str, str]], explicit: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]` | Plan 3 Task 4 |
| `host_capabilities.py` | `capability_errors(required: set[str], capabilities: dict[str, dict[str, str]]) -> list[str]` | Plan 3 Task 4 |

## 4. Design-Section Coverage Matrix

| Design section | Implemented by | Verification owner |
|---|---|---|
| 1 Summary and final-product boundary | Roadmap; Plans 1 and 4 docs/Skill updates | Plan 4 portability tests |
| 2 Goals | All plans | Final acceptance matrix |
| 3 Non-Goals | All plan constraints | Dependency and architecture review |
| 4 Existing-workflow compatibility | Plans 1-2 | Schema 1.3 characterization and guided migration tests |
| 5 Delivery modes | Plan 2; opt-in in Plan 4 | Contract/guided/autonomous tests |
| 6 One-confirmation contract | Plan 2 | Digest, approval, material-change, and workload-envelope tests |
| 7 Internal capability architecture | Plans 1-3 | Module API and integration tests |
| 8 Applicability and quality floor | Plan 2 | Capability validation tests |
| 9 Specialized knowledge | Plan 4 | Progressive-loading behavior evaluation |
| 10 State extensions | Plans 1-3 | Structure, migration, transaction, manifest, and coverage tests |
| 11 Gates | Plans 2-3 | Specification/host/init/task/UI/delivery phase tests |
| 12 UI quality loop | Plans 3-4 | Affected-flow and final browser matrix tests |
| 13 Repair, stop, resume, authorization | Plans 1 and 3 | Counter, checkpoint, recovery, and permission-boundary tests |
| 14 WebBuilder testing | All plans | Committed tests, CI, behavior evaluations, maintained example |
| 15 Rollout | Plans 1-4 in order | Opt-in flag remains disabled until Plan 4 final gate |
| 16 Risks | Plans 1-4 | Failure-injection, tamper, host-degradation, and scope tests |
| 17 Acceptance criteria | Matrix below | Plan 4 final acceptance run |

## 5. Acceptance-Criteria Traceability

| Acceptance criterion | Plan/task owner | Evidence required before closure |
|---|---|---|
| AC-1 tracked tests and CI preserve 1.3 baseline | Plan 1 Tasks 1-2 | CI and local 31-test characterization output |
| AC-2 guided projects migrate idempotently to 1.4 | Plan 1 Task 4 | dry-run/apply/reapply tests and preserved-content hashes |
| AC-3 contract, applicability, workload envelope generated | Plan 2 Tasks 2-4 | contract fixture and specification-gate evidence |
| AC-4 execution requires approved revision and host capability | Plans 2 Task 5 and 3 Task 4 | execution/host gate rejection and pass cases |
| AC-5 material changes invalidate approval without freezing internal work | Plan 2 Task 3 | material/non-material comparison tests |
| AC-6 transitions and stops resume without duplicate work | Plans 1 Task 3 and 4 Task 3 | injected interruption and stop/resume E2E evidence |
| AC-7 user-facing delivery requires UI/a11y evidence | Plans 3 Task 5 and 4 Task 2 | browser manifest and delivery gate |
| AC-8 justified API-only/non-UI applicability preserves quality floor | Plan 2 Task 4 | API-only contract fixture and security/behavior checks |
| AC-9 checker identity follows strategy and risk | Plan 1 Task 5 | independent-checker and separate-reviewer tests |
| AC-10 stale, wrong, unredacted, superseded, or tampered evidence rejected | Plan 3 Tasks 2-3 | manifest mutation test matrix |
| AC-11 final delivery proves all applicable domains | Plans 3 Task 5 and 4 Task 4 | coverage matrix and clean-start run |
| AC-12 missing host capability degrades, hands off, or blocks explicitly | Plan 3 Task 4 | capability decision table tests |
| AC-13 portable Skill with no required background runtime | Plan 4 Task 5 | clean install/validation on supported CI hosts |

## 6. Execution Gates Between Plans

- [ ] **Gate A — before Plan 2:** schema 1.4 init, 1.3 migration, transaction recovery, checker identity, and repair-counter tests pass on Windows and Linux; autonomous execution remains disabled.
- [ ] **Gate B — before Plan 3:** contract approval, revision invalidation, applicability, guided compatibility, and specification gate pass; no evidence claim is yet accepted for delivery.
- [ ] **Gate C — before Plan 4:** manifests, redaction, implementation fingerprints, host capability decisions, UI evidence, and delivery rejection rules pass; worktree artifacts promote canonically.
- [ ] **Gate D — enable autonomous opt-in:** the maintained Django reference runs from clean checkout through approval, task execution, forced stop, resume, evidence verification, and delivery on CI.

## 7. Full Verification Command Set

Run from the repository root after every plan and at final closure:

```powershell
python -m unittest discover -s tests -v
python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" webbuilder
git diff --check
```

At Plan 4 closure also run:

```powershell
python -m unittest tests.test_webbuilder_autonomous_e2e -v
python webbuilder/scripts/check-state.py --target examples/autonomous-reference --phase delivery
```

Expected final result: all tests pass, Skill validation prints `Skill is valid!`, `git diff --check` emits no errors, and the delivery check prints `Spec2Web delivery phase check passed.`
