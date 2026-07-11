# WebBuilder Autonomous Full-Stack Delivery Design

Date: 2026-07-12
Status: revised draft for user review

## 1. Summary

WebBuilder will remain a general-purpose full-stack web delivery Skill. It will not become a WebGIS, annotation, ecommerce, or other vertical product generator.

The target experience is:

```text
User requirement
-> AI-generated solution contract
-> one normal consolidated user confirmation
-> autonomous design, implementation, verification, repair, and delivery within host capabilities
-> delivery or a declared stop condition that preserves a resumable checkpoint
-> runnable production-MVP project with verifiable evidence
```

UI/UX design is a mandatory core capability for every user-facing project. Specialized domain knowledge may be loaded progressively when relevant, but it does not own the workflow, create a separate state machine, or appear as a user-selected product mode.

WebBuilder itself is the final product: one portable Skill, local human-readable state files, and small deterministic Python tools. Host-provided agents, browser, Git, worktrees, Docker, and terminals remain the execution environment. No background service is required for the core product.

This design extends the existing WebBuilder phases, state files, task contracts, risk controls, worktree handoff, acceptance gate, integration gate, repair budgets, and delivery report. It does not replace them.

## 2. Goals

1. Accept a concise user requirement for a new web system.
2. Infer a production-MVP product definition instead of asking the user to write a PRD.
3. Present requirements, scope, UI direction, technology, architecture, risk, and acceptance criteria in one review bundle.
4. Require one normal user confirmation before autonomous implementation, then pause only for declared stop conditions or new high-impact authorization.
5. Deliver a complete runnable project covering every applicable UI, backend, data, testing, startup, and documentation capability in the approved contract.
6. Prove completion with machine-verifiable functional, UI, accessibility, performance, security, and delivery evidence when those domains apply.
7. Preserve WebBuilder's final-product architecture as one lightweight host-driven Skill with local files and small deterministic Python tools, without adding a background service, worker pool, plugin runtime, or required external AI provider.
8. Keep the current guided workflow available for projects that need incremental discovery or repeated high-impact decisions.
9. Make every autonomous stop resumable without repeating completed tasks or trusting partially written state.

## 3. Non-Goals

- Guarantee that every possible web product can be delivered from one sentence without any uncertainty.
- Remove user authorization for credentials, paid resources, external accounts, destructive operations, or irreversible production actions.
- Embed complete WebGIS, annotation, ecommerce, healthcare, or other vertical runtimes into WebBuilder.
- Replace the host's agent, browser, Git, worktree, or deployment capabilities.
- Introduce a long-running scheduler, database-backed worker pool, or unattended remote merge service.
- Continue running after the host session has ended; WebBuilder persists a checkpoint for the next session instead.
- Treat attractive screenshots as a substitute for functional correctness, accessibility, security, or performance.
- Force UI gates on a genuinely API-only project; such projects must record an explicit `not_applicable` reason.
- Treat agent-authored `passed` text as proof without validating the command result and referenced artifacts.

## 4. Compatibility with the Existing Workflow

The existing top-level sequence remains authoritative:

```text
Project Rules
-> User Discovery Gate
-> First-Principles Analysis
-> Requirement Baseline
-> Technology Strategy
-> Interface Design Baseline
-> System Design
-> Task Breakdown
-> Task Execution Loop
-> Integration Validation
-> Delivery
```

The autonomous mode changes how the pre-execution phases are presented to the user, not their semantic responsibilities.

In guided mode, WebBuilder may continue asking one high-impact question at a time. In autonomous mode, WebBuilder drafts the pre-execution artifacts internally and presents a consolidated Solution Contract for one confirmation.

The existing execution model remains:

- `single`, `delegated`, or `parallel` execution;
- task branches and worktrees when Git is available;
- Orchestrator-owned acceptance and integration;
- Developer, Tester, Reviewer, and Repairer responsibilities;
- serial integration;
- main-workspace verification;
- task and integration repair limits;
- delivery only after evidence closure.

Schema 1.4 introduces the autonomous state and evidence semantics in this design. Existing schema 1.3 projects migrate idempotently, preserve content, and default to `guided` until the user explicitly approves autonomous mode.

## 5. Delivery Modes

Add a project-level delivery mode:

```yaml
delivery_mode: guided | autonomous
```

### 5.1 Guided

Preserves the current User Discovery behavior and is appropriate when:

- the user wants to shape the product interactively;
- the project already exists and contains important undocumented constraints;
- the requirements contain unresolved high-impact choices;
- the work includes critical migration, production, compliance, or external-system risk.

### 5.2 Autonomous

Optimized for a new production-MVP web system:

1. Read the user's brief and project rules.
2. Infer the product, users, workflows, scope, UI direction, stack, architecture, risks, and acceptance criteria.
3. Generate draft baseline and plan artifacts.
4. Present one consolidated Solution Contract.
5. After approval, mark the baselines ready and continue automatically until delivered or a declared stop condition occurs.

Autonomous mode is eligible only when the host can provide every capability required by the approved contract. Missing optional capabilities cause a recorded downgrade, such as `parallel` to `single`. Missing required capabilities cause `environment_blocked` or a switch to `guided`; they never permit a weakened delivery claim.

Existing or migrated projects default to `guided`. A new project may select `autonomous` before confirmation, but execution remains disabled until the approved contract revision and host-capability gate both pass.

## 6. One-Confirmation Contract

Do not create a separate `solution-contract.md`. Add a concise `## Solution Contract` section to `requirements-baseline.md` so the existing state files remain the source of truth.

The confirmation bundle must contain:

- problem and desired outcome;
- target users and primary jobs;
- core capabilities;
- explicit non-goals;
- primary workflows;
- page and navigation summary;
- UI direction and information density;
- selected technology profile and major architecture decisions;
- data, permission, security, and integration assumptions;
- material risks and exclusions;
- deliverables;
- acceptance criteria and verification approach.

Confirmation metadata owned by `requirements-baseline.md`:

```yaml
confirmation_status: pending | approved | changes_requested
contract_revision: 1
approved_contract_revision: null | 1
approval_digest: null | sha256:<digest>
approval_scope: requirements_design_stack_ui_execution
approval_evidence: null | user_message_reference
approved_by: null | user
approved_at: null | ISO-8601 timestamp
discovery_method: interactive | inferred_contract
```

The approval digest covers the material contract: product scope, non-goals, acceptance signals, selected technology profile, public interfaces, data and permission boundaries, delivery assumptions, and declared risks. It does not freeze ordinary task decomposition, low-risk implementation details, or bounded repairs. Those internal changes remain allowed while they continue to satisfy the approved contract revision.

Digest input uses a documented canonical serialization: UTF-8, LF line endings, stable field order, normalized insignificant whitespace, and only the material contract fields listed above. Approval timestamps, actor metadata, evidence references, task execution state, and generated digest values are excluded from their own digest input.

`system-design.md` and `task-plan.md` record `based_on_contract_revision`. A material contract change increments `contract_revision`, invalidates the previous approval, and marks derived design, plan, and evidence stale until the new revision is approved and reconciled.

The approval authorizes normal, reversible implementation decisions inside the confirmed scope. It does not authorize:

- use of real credentials not already provided for the task;
- creation of paid resources;
- destructive or irreversible external actions;
- production deployment or domain changes unless explicitly included;
- material expansion or replacement of the confirmed product scope.

After approval, ordinary technology details, UI details, low-risk dependencies, test fixes, and bounded repairs do not trigger additional user confirmation.

The confirmation bundle includes a workload envelope based on task count, affected browser flows, external dependencies, required quality gates, repair budgets, and available host concurrency. It must not invent fixed token counts, API-call counts, elapsed time, or expected interruption counts when the host cannot measure them reliably.

## 7. Internal Capability Architecture

WebBuilder remains one user-facing Skill with seven LLM-owned responsibilities and two deterministic support kernels. These are logical responsibilities inside one product, not background services, persistent processes, or independently deployed components.

### 7.1 Solution Compiler

Compiles the user brief into:

- outcome, users, jobs, and workflows;
- features and non-goals;
- pages and operations;
- assumptions, constraints, and risks;
- acceptance signals;
- the one-confirmation summary.

### 7.2 Technology and Architecture Planner

- Prefer a versioned golden-stack profile for new projects.
- Select a different profile only when requirements provide a concrete reason.
- Record the selected profile and tradeoffs in the confirmation bundle.
- Freeze the choice after confirmation unless evidence shows it cannot satisfy the contract.
- Avoid adding services, frameworks, or infrastructure that are not required by the confirmed scope.

### 7.3 UI/UX Design Engine

Mandatory for every user-facing project. It owns:

- information architecture;
- user flows and page hierarchy;
- visual direction and density;
- design tokens;
- layout and navigation conventions;
- component behavior;
- loading, empty, error, disabled, success, validation, and permission states;
- responsive and keyboard behavior;
- accessibility requirements;
- rendered visual verification and repair.

### 7.4 Full-Stack Task Planner

Use mixed decomposition:

1. Freeze shared contracts and foundational infrastructure.
2. Deliver vertical business slices that include UI, API, data, permissions, and tests where applicable.
3. Add administration, audit, and cross-cutting quality work only when required by the confirmed product.
4. Finish with full-system validation and delivery.

### 7.5 Execution Controller

Retains the current adaptive execution, worker boundaries, worktrees, independent checking, serial integration, and state update rules.

### 7.6 Quality Gate

Requires independent evidence across:

- functional behavior;
- UI and responsive rendering;
- accessibility;
- engineering health;
- security;
- performance;
- deployment and startup smoke behavior.

### 7.7 Delivery Controller

Produces a runnable project plus requirement-to-evidence traceability, run instructions, known risks, and explicit incomplete items.

### 7.8 State Kernel

A small deterministic Python state-transition tool owns machine-checked lifecycle changes. It validates legal transitions, revision consistency, and cross-file invariants before replacing state files. It uses temporary files plus a transition journal so a host interruption can be detected and recovered idempotently on the next session.

Humans and agents may still edit the descriptive Markdown content. Readiness, approval, stop, resume, acceptance, integration, and delivery transitions must go through the State Kernel rather than being asserted by manually changing a status value.

### 7.9 Evidence Kernel

A small deterministic evidence tool runs or imports declared verification, captures exit status and artifact metadata, redacts secrets, hashes artifacts, and produces a manifest. Markdown files index evidence summaries; they do not manufacture a pass result.

The Evidence Kernel is not a test framework or remote artifact service. It wraps project-selected commands and host-provided browser or security tools so the delivery gate can verify that evidence exists, matches the current contract revision and commit, and represents the latest valid attempt.

## 8. Capability Applicability and Universal Quality Floor

Do not classify whole projects as `lite`, `standard`, or `full`. Authentication, database, UI, accessibility, Docker, audit, performance, and other concerns are orthogonal. The Solution Contract records applicability per capability:

```yaml
capabilities:
  ui:
    status: required | not_applicable
    reason: project-specific reason
  database:
    status: required | not_applicable
    reason: project-specific reason
  authentication:
    status: required | not_applicable
    reason: project-specific reason
  rbac:
    status: required | not_applicable
    reason: project-specific reason
  audit:
    status: required | not_applicable
    reason: project-specific reason
  docker:
    status: required | not_applicable
    reason: project-specific reason
  accessibility:
    status: required | not_applicable
    reason: project-specific reason
  performance:
    status: required
    profile: baseline | product-specific
  security:
    status: required
    profile: baseline | elevated
```

`not_applicable` requires a capability-specific reason and is validated against project facts. Runtime inability is not `not_applicable`; it is `environment_blocked`. A gate-level waiver is recorded separately from capability applicability and is exceptional: it requires explicit user evidence, an owner, expiry or review condition, and residual risk. The agent may not create its own waiver, and baseline security cannot be waived as a whole.

Every project has a universal quality floor:

- reproducible installation or documented no-install startup;
- build or syntax validation appropriate to the selected stack;
- deterministic primary behavioral verification;
- user-visible error handling when a user interface exists;
- no committed credentials and baseline dependency/security hygiene;
- accurate run instructions and known limitations;
- requirement-to-evidence traceability.

Additional obligations are triggered by capability applicability:

- user-facing UI requires responsive behavior, keyboard access, visible focus, relevant states, and accessibility checks;
- persistent data requires schema, migration or initialization, recovery, and clean-state verification;
- authentication requires session lifecycle and authorization-boundary tests;
- multiple roles require RBAC and permission-denial tests;
- material state changes may require audit evidence;
- Docker is required only when the approved delivery contract includes container startup;
- end-to-end, performance, and security depth scales with the approved workflows and risk, but baseline security is never wholly not applicable.

## 9. Specialized Domain Knowledge

Specialized knowledge is progressive reference material, not an optional version of the core workflow.

Examples:

```text
references/domains/
|-- geospatial.md
|-- annotation.md
|-- ecommerce.md
`-- realtime.md
```

Domain references may contribute:

- terminology and invariants;
- requirements and non-goals;
- architecture decisions;
- task patterns;
- risk modifiers;
- test scenarios;
- interoperability and delivery checks.

They must not:

- replace the WebBuilder state machine;
- own confirmation or delivery;
- make UI, testing, security, or deployment optional;
- require users to select or understand a pack;
- load when the requirement is unrelated.

## 10. State File Extensions

This design advances the state schema from 1.3 to 1.4. Initialization creates 1.4 state. Migration from 1.3 is non-destructive, idempotent, preserves project content, creates a recoverable backup, and defaults `delivery_mode` to `guided`.

### 10.1 `requirements-baseline.md`

Add:

- `confirmation_status`;
- `contract_revision`;
- `approved_contract_revision`;
- `approval_digest`;
- `approval_scope`;
- approval actor, timestamp, and evidence;
- `discovery_method`;
- project capability applicability and reasons;
- `## Solution Contract`.

`requirements-baseline.md` is the sole owner of confirmation status and approval evidence.

The existing User Discovery and First-Principles sections remain. In autonomous mode, they record AI-inferred facts and assumptions plus the user's consolidated approval.

The Solution Contract is a user-facing projection of canonical material decisions. It may summarize system design, but canonical architecture details remain owned by `system-design.md`. The projection and derived files must reference the same approved contract revision instead of maintaining independent confirmation states.

### 10.2 `system-design.md`

Strengthen the existing design sections to include:

- `based_on_contract_revision`;
- selected technology profile;
- architecture decisions and rejected alternatives;
- pages and user flows;
- data model and API;
- permissions and security;
- UI Design Lock;
- component and state matrix;
- responsive and accessibility requirements;
- verification strategy.

The UI Design Lock records at minimum:

- interface type and information density;
- semantic color roles;
- typography roles;
- spacing, radius, elevation, and icon conventions;
- navigation and application shell;
- component rules;
- motion policy;
- explicit anti-patterns and justified exceptions.

### 10.3 `task-plan.md`

Add `based_on_contract_revision` and task quality domains:

```yaml
quality_domains:
  - functional
  - ui
  - accessibility
  - performance
  - security
```

Only applicable domains are required. Every user-visible vertical slice requires `ui` and `accessibility` unless a specific reason is recorded.

Capability applicability is project-owned by the approved contract. Tasks select the applicable quality domains they must prove; they may not downgrade a required project capability.

### 10.4 `loop-state.md`

Add:

```yaml
delivery_mode: guided | autonomous
autonomy_scope: unconfirmed | confirmed_plan
stop_reason: none | verification_failed | needs_user_action | needs_decision | repair_exhausted | environment_blocked
resume_checkpoint: none | specification | initialization | task:<TASK-ID> | integration | delivery
active_run_id: null | RUN-ID
state_revision: 1
pending_transition: null | TRANSITION-ID
```

`loop-state.md` owns runtime mode and stop reason, but does not duplicate confirmation status. Existing phase, task, execution-mode, agent-capability, checker, worktree, and handoff state remains authoritative.

Add a host capability record for subagents, free child slots, browser, Git, worktree, Docker, network, and session persistence. Each capability records `available`, `unavailable`, or `unknown` plus evidence or the inspection method. Runtime degradation follows explicit rules; it cannot silently weaken an approved gate.

### 10.5 `validation-log.md`

Retain task acceptance and integration records. Add project-level evidence records:

```text
PROJECT / functional
PROJECT / ui
PROJECT / accessibility
PROJECT / performance
PROJECT / security
PROJECT / delivery-smoke
```

UI evidence includes:

- screenshot path;
- viewport;
- page and state;
- result;
- finding rule IDs and severity;
- repair record;
- re-verification result.

Every evidence record also includes:

- evidence record ID, run ID, attempt, and timestamp;
- approved contract revision and Git commit or `direct_apply` workspace fingerprint;
- command or method, working directory, exit code, and tool version;
- artifact manifest path and SHA-256;
- redaction status;
- superseded record ID when a later repair replaces an earlier attempt.

Evidence selection uses the latest valid non-superseded attempt for the current contract revision and implementation fingerprint. Reusing a record from an older contract, commit, worktree, or failed attempt is invalid.

For Git-backed work, the implementation fingerprint is the verified commit hash plus dirty-worktree status. For `direct_apply` or non-Git work, it is a deterministic manifest of project-relative allowed paths and SHA-256 file hashes. Generated artifact directories and explicitly excluded volatile files do not contribute to that fingerprint.

### 10.6 `delivery-report.md`

Add a final coverage matrix across every applicable quality domain:

| Requirement | Implementation | Functional | UI | Accessibility | Performance | Security | Delivery Smoke | Status |
|---|---|---|---|---|---|---|---|---|

### 10.7 Evidence Directory

Store large generated artifacts outside the Markdown state files:

```text
.webbuilder-artifacts/
`-- <run-id>/
    `-- <task-id-or-project>/
        `-- <attempt>/
            |-- manifest.json
            |-- command-output.txt
            |-- screenshots/
            `-- reports/
```

State files contain project-relative stable paths, summaries, and verdicts rather than full raw output. Workers may write attempt-local artifacts in their worktrees. Before a worktree is removed, the Orchestrator copies accepted evidence into the canonical main-workspace artifact directory and verifies its hash.

Raw evidence is ignored by Git by default unless the project rules require durable committed artifacts. The validation log and delivery report always retain the commands, verdicts, stable finding IDs, hashes, and artifact paths or external references needed for audit.

Evidence capture must redact credentials, cookies, authorization headers, secret environment values, real user data, and unnecessary local absolute paths. Screenshots and browser traces use seed or synthetic data by default. The approved contract records artifact retention, size limits, and whether evidence is delivered, retained locally, or replaced by an external durable reference.

### 10.8 State Transitions and Invariants

The State Kernel implements and tests these transitions:

```text
draft contract -> pending confirmation -> approved contract
approved contract -> ready design and plan -> active execution
active execution -> declared stop -> resumable checkpoint -> active execution
active execution -> task acceptance -> serial integration -> next task
active execution -> final validation -> delivered
material contract change -> approval invalidated -> pending confirmation
```

Cross-file invariants:

- execution requires `approved_contract_revision == contract_revision` and a matching approval digest;
- ready design and plan must reference that approved contract revision;
- evidence must reference the approved contract revision and current implementation fingerprint;
- a pending transition prevents further work until it is completed or rolled back by the State Kernel;
- `status: delivered` requires no pending transition, no unresolved stop reason, and complete applicable evidence;
- a completed task is never rerun on resume unless its contract revision, dependencies, implementation fingerprint, or evidence has become stale;
- manually editing a success status cannot bypass a failed transition or gate.

## 11. Phase and Gate Behavior

### 11.1 Specification Gate

Before confirmation, verify:

- every requirement has an acceptance signal;
- pages, data, APIs, and permissions cover the stated workflows;
- decisions do not contradict each other;
- error states and non-goals are explicit;
- the selected technology can satisfy the confirmed scope;
- verification commands or scenarios are defined.
- every capability is `required` or has a justified `not_applicable` decision;
- the contract revision and approval digest input are deterministic.

### 11.2 Host Capability Gate

Before autonomous execution:

- inspect and record subagent, browser, Git, worktree, Docker, network, and session-persistence capabilities;
- compare required capabilities with the approved contract and verification strategy;
- downgrade execution mode only when the affected capability is optional and the same gates remain enforceable;
- stop with `environment_blocked` when a required capability is unavailable;
- never claim a browser, container, deployment, or independent-review result that the host could not actually perform.

### 11.3 Initialization Gate

Before business implementation, run only the checks required by the approved capability matrix:

- dependencies install;
- database starts when persistent data is required;
- migrations or deterministic data initialization run when applicable;
- development server starts;
- typecheck and build execute;
- test harness executes;
- Docker configuration is syntactically and operationally valid when container delivery is required;
- health and initial authentication smoke checks pass when applicable.

### 11.4 Task Gate

Each vertical slice requires:

- requirement IDs;
- bounded implementation scope;
- behavioral verification;
- applicable UI state coverage;
- Developer submission evidence;
- independent checking;
- integration strategy;
- main-workspace re-verification.
- evidence manifest records matching the current contract revision and implementation fingerprint.

For ordinary delegated work, one fresh independent checker may perform both Tester and Reviewer duties. For `checker_strategy: independent_checker`, the acceptance validator requires the Developer identity to differ from the checker identity and permits Tester and Reviewer identities to match. For `checker_strategy: separate_tester_reviewer`, Developer, Tester, and Reviewer identities must all differ. `single_session` remains limited to eligible low-risk work and cannot be represented as independent review.

High and critical tasks continue to require distinct Developer, Tester, and Reviewer identities.

### 11.5 UI and Browser Gate

For affected user-visible flows during task execution:

- run the relevant Playwright scenario;
- render only affected pages and states;
- capture the viewports needed to exercise the changed layout;
- record console, network, overflow, and interaction failures;
- repair and re-run within the task budget.

The task gate records only affected flows, pages, states, and representative viewports derived from the change. It does not run a Cartesian product of every page, state, and viewport.

For final integration validation, run the complete supported matrix:

- baseline viewports: 390, 768, and 1440 CSS pixels;
- primary pages and workflows;
- loading, empty, error, disabled, validation, success, and permission states where applicable;
- keyboard navigation and visible focus;
- automated accessibility checks;
- profile-defined performance checks in a stable production-like environment;
- console and failed-request checks.

No visual pass may be claimed without actual rendered evidence and a valid artifact manifest. Estimated browser work is expressed as affected flows, states, and viewports, not unsupported fixed time or API-call estimates.

### 11.6 Final Delivery Gate

Prove that:

- the documented standard or Docker command starts the system;
- migrations and seed data work from a clean state;
- authentication, permissions, and primary workflows pass end-to-end tests when applicable;
- build, typecheck, unit, and integration checks pass;
- the final UI evidence matrix is complete;
- no blocking accessibility, security, performance, or runtime findings remain;
- every confirmed requirement maps to implementation and evidence;
- run instructions, risks, and incomplete items are explicit.
- every evidence manifest exists, passes hash and redaction checks, and matches the approved contract revision and delivered implementation fingerprint;
- every justified `not_applicable` decision remains consistent with the delivered product;
- no pending state transition or unresolved stop reason remains.

## 12. UI Quality Loop

The mandatory UI loop is:

```text
Product and UX analysis
-> UI Design Lock
-> implementation
-> deterministic source checks
-> agent design critique
-> rendered screenshot matrix
-> accessibility and performance checks
-> bounded repair
-> re-render and re-test
```

Separate aesthetic findings from objective quality findings. A strong aesthetic score cannot offset accessibility, runtime, or performance failures.

Task-level UI checks cover changed flows only. Final checks cover all primary approved workflows, representative mobile/tablet/desktop layouts, required states, accessibility, and the selected performance profile. The matrix must remain risk-based rather than expanding into an unbounded screenshot Cartesian product.

Findings use stable IDs, severity, affected page or component, evidence path, remediation, and re-verification status.

The implementation should borrow mechanisms rather than copy third-party text or code without license review. Primary references include StyleSeed's persistent design lock and screenshot loop, Impeccable's routed operations and deterministic finding registry, and Web Quality Skills' objective accessibility and performance gates.

## 13. Repair and Stop Policy

Preserve separate finite budgets:

- task repair: at most 3 attempts;
- integration repair: at most 5 attempts;
- the same failure fingerprint 3 times within the same repair scope: stop.

Every repair must:

1. cite failure evidence;
2. identify one primary cause;
3. change only what is needed to address that cause;
4. re-run the failing verification;
5. update the validation record;
6. proceed only after the gate passes.

`task_repair_attempt` and `integration_repair_attempt` are distinct counters with separate failure fingerprints and recovery points. A task-level success does not reset an unresolved integration failure.

Existing task and workflow statuses remain unchanged. When autonomous continuation stops, `loop-state.md` records a `stop_reason` and `resume_checkpoint`:

| Stop reason or existing task state | Meaning |
|---|---|
| `needs_repair` | Existing task state: a bounded automatic repair is available. |
| `verification_failed` | Evidence failed and diagnosis is required. |
| `needs_user_action` | Credentials, paid resources, or an external user-owned action is required. |
| `needs_decision` | The confirmed scope or a material architecture decision must change. |
| `repair_exhausted` | The declared repair budget is exhausted. |
| `environment_blocked` | The required local or external environment is unavailable. |

The existing workflow status becomes `blocked` when a terminal stop reason cannot be cleared safely, and `delivered` only when requirement and evidence closure is complete.

Ordinary coding errors, test failures, UI defects, and low-risk implementation choices do not ask the user for permission before repair.

### 13.1 Checkpoint and Resume Protocol

On every autonomous stop:

1. complete or roll back any pending State Kernel transition;
2. record the active run, current task, attempt counters, stop evidence, and resume checkpoint;
3. preserve the task worktree and unintegrated branch when they contain diagnostic or resumable work;
4. keep completed and accepted tasks intact;
5. copy accepted evidence out of disposable worktrees before cleanup;
6. present only safe recovery options: continue after unblock, switch to guided, or abandon/restart with explicit user approval.

Resume reads state and evidence before taking action. It does not repeat a completed task unless staleness rules invalidate that task. Database or external-write recovery follows the task's approved rollback or forward-fix plan; WebBuilder does not blindly reverse an irreversible migration.

### 13.2 Authorization Boundary

Solution Contract approval authorizes confirmed, reversible local implementation work. It does not replace host tool permissions or authorize credentials, paid services, production deployment, destructive external writes, irreversible migration, high-risk install scripts, secret transmission, or a material change to scope, data, permissions, or public interfaces.

If a critical action was known at confirmation time, the contract may record its intended plan, but execution still requires the explicit approval evidence required by the host and the critical task contract. Evidence collection follows the redaction and retention rules in Section 10.7.

## 14. Testing Strategy for WebBuilder Itself

### 14.1 Deterministic State Tests

Commit the test suite and run it in CI before enabling autonomous mode. Add characterization tests for schema 1.3 first, then failing tests for every new 1.4 behavior before implementation:

- autonomous draft state;
- one-confirmation approval transition;
- approval digest and contract-revision invalidation;
- rejection of execution before confirmation;
- guided-mode compatibility;
- idempotent migration from 1.3 to 1.4 without content loss;
- interruption between multi-file state writes and deterministic recovery;
- resume without repeating valid completed tasks;
- quality-domain validation;
- capability applicability and invalid `not_applicable` decisions;
- project-level evidence records;
- evidence artifact existence, hash, revision, implementation fingerprint, redaction, supersession, and tamper detection;
- UI evidence completeness;
- delivery rejection when required evidence is missing;
- strategy-aware independent-checker identity behavior;
- separate task and integration repair budgets.

### 14.2 Skill Behavior Evaluations

Use representative prompts for:

- a common SaaS or admin system;
- a content-heavy business application;
- a data-heavy operational application;
- an API-only service;
- a specialized request such as geospatial or annotation.

Evaluate whether WebBuilder:

- produces a usable Solution Contract;
- asks only one normal confirmation in autonomous mode;
- keeps UI mandatory for user-facing systems;
- does not force irrelevant specialized knowledge;
- produces bounded vertical tasks;
- records executable verification;
- stops only for declared conditions;
- generates complete delivery evidence.
- degrades safely when host capabilities are unavailable;
- refuses stale, handwritten, missing, or tampered evidence;
- resumes from declared checkpoints without duplicating completed work.

### 14.3 End-to-End Example

Add one maintained example project that runs from initialization through delivery. It must exercise:

- autonomous confirmation;
- at least one full vertical business slice;
- authentication or a recorded reason it is not required;
- database migration and seed data;
- responsive UI states;
- end-to-end testing;
- evidence capture;
- final delivery reporting.
- a declared stop and successful resume;
- at least one justified `not_applicable` capability;
- evidence capture, tamper rejection, and canonical artifact retention.

The first maintained example uses one validated golden technology profile plus an existing/custom-stack escape hatch. Additional profiles are added only after they have the same end-to-end compatibility and evidence coverage. Profiles record compatibility ranges, last validation date, supported hosts, selection criteria, upgrade policy, and deprecation policy rather than permanently pinning transient framework examples in this design.

## 15. Rollout

Autonomous execution remains behind an opt-in feature flag until Phase 4 exit criteria pass.

### Phase 0: Release Foundation

- Commit the current and new tests instead of ignoring the test directory.
- Add CI for supported Python and operating-system environments.
- Make documented validation commands UTF-8 safe.
- Record the schema 1.3 characterization baseline.

### Phase 1: State Kernel and Compatibility

- Add schema 1.4, the transition table, revision ownership, journaled recovery, and idempotent migration.
- Fix strategy-aware independent-checker identity semantics.
- Separate task and integration repair state.
- Preserve guided mode and default migrated projects to guided.

### Phase 2: Contract and Applicability

- Add delivery mode, Solution Contract, approval digest, contract revision, and discovery method.
- Add capability applicability and the universal quality floor.
- Implement approval invalidation and derived-artifact staleness.
- Generate contracts in autonomous mode, but keep autonomous execution disabled.

### Phase 3: Evidence and Host Capability

- Add the Evidence Kernel, manifests, redaction, artifact hashing, retention, and canonical worktree handoff.
- Add host capability inspection and explicit downgrade or block rules.
- Extend task, UI, accessibility, performance, security, integration, and delivery gates.

### Phase 4: Narrow End-to-End Autonomous Loop

- Support one validated golden technology profile plus an existing/custom-stack path.
- Maintain one example from contract approval through stop/resume and delivery.
- Run prompt-level, state, evidence-tamper, host-degradation, and end-to-end evaluations.
- Enable autonomous mode as explicit opt-in only after the full loop passes.

### Phase 5: Controlled Expansion

- Add further technology profiles only with equivalent end-to-end evidence.
- Add specialized domain references only after the general path is stable.
- Validate that irrelevant references are not loaded.
- Keep domain knowledge separate from the core state machine.

## 16. Risks and Mitigations

### Over-automation chooses the wrong product

Mitigation: one consolidated confirmation exposes assumptions, exclusions, architecture, UI direction, and acceptance criteria before implementation.

### One confirmation is mistaken for unlimited authority

Mitigation: approval scope explicitly excludes credentials, paid resources, irreversible external actions, and unconfirmed production changes.

### Host capability is mistaken for product capability

Mitigation: inspect host capabilities before execution, record evidence, downgrade only when gates remain equivalent, and block claims that require unavailable tools.

### Agent-authored evidence produces a false pass

Mitigation: deterministic evidence manifests include exit codes, current revision and implementation fingerprint, artifact hashes, redaction status, and latest-attempt rules. Delivery rejects missing, stale, handwritten, or tampered evidence.

### A host interruption leaves contradictory state

Mitigation: the State Kernel uses revisioned journaled transitions, detects pending work on resume, and completes or rolls back the transition before dispatching more work.

### UI validation becomes slow

Mitigation: task gates render affected pages and states only; the complete viewport and state matrix runs at final integration validation.

### Lighthouse or browser checks are unstable

Mitigation: the selected technology profile records its performance budgets. Final performance gates run in a documented stable production-like environment, preserve raw evidence, and distinguish environmental failure from product failure.

### The Skill becomes too large

Mitigation: keep the main `SKILL.md` as a router and policy source; move detailed universal and specialized guidance into progressively loaded references.

### Specialized knowledge overtakes the general workflow

Mitigation: domain references contribute constraints and checks only. Core product, UI, execution, and delivery responsibilities remain unconditional.

### State schema becomes fragile

Mitigation: preserve existing files, centralize schema 1.4 and transition invariants in the State Kernel, provide idempotent migration and backup, and commit deterministic tests before changing execution behavior.

## 17. Acceptance Criteria for This Design

The implementation derived from this design is acceptable when:

1. The committed test suite and CI preserve the schema 1.3 characterization baseline.
2. Existing guided projects migrate idempotently to schema 1.4 without content loss and default to guided.
3. Autonomous mode generates one complete confirmation bundle, applicability matrix, and workload envelope from a concise requirement.
4. Execution cannot begin until the current contract revision is approved, derived design and plan reference it, and required host capabilities are available.
5. A material contract change invalidates approval and stale evidence without freezing ordinary internal implementation decisions.
6. An interrupted state transition and an autonomous stop both resume deterministically without repeating valid completed tasks.
7. User-facing projects cannot deliver without rendered UI evidence and applicable accessibility checks.
8. API-only and other specialized shapes can record justified `not_applicable` capabilities without bypassing the universal security, behavioral, or delivery floor.
9. Ordinary delegated work supports one fresh independent checker performing both test and review duties, while high and critical work requires distinct Developer, Tester, and Reviewer identities.
10. Delivery rejects handwritten, missing, stale, superseded, wrong-revision, wrong-implementation, unredacted, or tampered evidence.
11. Final delivery proves startup, applicable data initialization, primary workflows, requirement coverage, and every applicable quality domain.
12. Missing host capabilities produce an explicit downgrade, guided handoff, or block rather than a weakened completion claim.
13. WebBuilder remains a portable final-product Skill with local files and small deterministic Python tools, without a required background runtime or external agent service.
