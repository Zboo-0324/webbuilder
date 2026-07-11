# WebBuilder Autonomous Full-Stack Delivery Design

Date: 2026-07-12
Status: draft for written review

## 1. Summary

WebBuilder will remain a general-purpose full-stack web delivery Skill. It will not become a WebGIS, annotation, ecommerce, or other vertical product generator.

The target experience is:

```text
User requirement
-> AI-generated solution contract
-> one consolidated user confirmation
-> autonomous design, implementation, verification, repair, and delivery
-> runnable production-MVP project with evidence
```

UI/UX design is a mandatory core capability for every user-facing project. Specialized domain knowledge may be loaded progressively when relevant, but it does not own the workflow, create a separate state machine, or appear as a user-selected product mode.

This design extends the existing WebBuilder phases, state files, task contracts, risk controls, worktree handoff, acceptance gate, integration gate, repair budgets, and delivery report. It does not replace them.

## 2. Goals

1. Accept a concise user requirement for a new web system.
2. Infer a production-MVP product definition instead of asking the user to write a PRD.
3. Present requirements, scope, UI direction, technology, architecture, risk, and acceptance criteria in one review bundle.
4. Require only one normal user confirmation before autonomous implementation.
5. Deliver a complete runnable project, including UI, backend, database, tests, startup configuration, and documentation.
6. Prove completion with functional, UI, accessibility, performance, security, and delivery evidence.
7. Preserve WebBuilder's lightweight, host-driven Skill architecture without adding a background service, worker pool, plugin runtime, or required external AI provider.
8. Keep the current guided workflow available for projects that need incremental discovery or repeated high-impact decisions.

## 3. Non-Goals

- Guarantee that every possible web product can be delivered from one sentence without any uncertainty.
- Remove user authorization for credentials, paid resources, external accounts, destructive operations, or irreversible production actions.
- Embed complete WebGIS, annotation, ecommerce, healthcare, or other vertical runtimes into WebBuilder.
- Replace the host's agent, browser, Git, worktree, or deployment capabilities.
- Introduce a long-running scheduler, database-backed worker pool, or unattended remote merge service.
- Treat attractive screenshots as a substitute for functional correctness, accessibility, security, or performance.
- Force UI gates on a genuinely API-only project; such projects must record an explicit `not_applicable` reason.

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
confirmation_revision: 1
approval_scope: requirements_design_stack_ui_execution
```

The approval authorizes normal, reversible implementation decisions inside the confirmed scope. It does not authorize:

- use of real credentials not already provided for the task;
- creation of paid resources;
- destructive or irreversible external actions;
- production deployment or domain changes unless explicitly included;
- material expansion or replacement of the confirmed product scope.

After approval, ordinary technology details, UI details, low-risk dependencies, test fixes, and bounded repairs do not trigger additional user confirmation.

## 7. Internal Capability Architecture

WebBuilder remains one user-facing Skill with seven internal responsibilities.

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

## 8. Universal Full-Stack Baseline

Every production-MVP project must address, when applicable:

- authentication and session lifecycle;
- role-based authorization;
- primary business workflows;
- administration needed to operate those workflows;
- validation and user-visible errors;
- audit evidence for material changes;
- database schema, migrations, and seed data;
- API contracts and error responses;
- frontend loading, empty, error, disabled, success, and permission states;
- responsive behavior;
- unit, integration, and end-to-end tests;
- environment variable examples;
- local startup and Docker configuration;
- delivery documentation.

These are baseline questions and quality expectations, not unconditional features. For example, a public single-user application may not require RBAC, and that decision must be recorded rather than silently omitted.

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

### 10.1 `requirements-baseline.md`

Add:

- `confirmation_status`;
- `confirmation_revision`;
- `approval_scope`;
- `## Solution Contract`.

`requirements-baseline.md` is the sole owner of confirmation status and approval evidence.

The existing User Discovery and First-Principles sections remain. In autonomous mode, they record AI-inferred facts and assumptions plus the user's consolidated approval.

### 10.2 `system-design.md`

Strengthen the existing design sections to include:

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

Add task quality domains:

```yaml
quality_domains:
  - functional
  - ui
  - accessibility
  - performance
  - security
```

Only applicable domains are required. Every user-visible vertical slice requires `ui` and `accessibility` unless a specific reason is recorded.

### 10.4 `loop-state.md`

Add:

```yaml
delivery_mode: guided | autonomous
autonomy_scope: unconfirmed | confirmed_plan
stop_reason: none | verification_failed | needs_user_action | needs_decision | repair_exhausted | environment_blocked
```

`loop-state.md` owns runtime mode and stop reason, but does not duplicate confirmation status. Existing phase, task, execution-mode, agent-capability, checker, worktree, and handoff state remains authoritative.

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

### 10.6 `delivery-report.md`

Add a final coverage matrix:

| Requirement | Implementation | Functional Evidence | UI Evidence | Status |
|---|---|---|---|---|

### 10.7 Evidence Directory

Store large generated artifacts outside the Markdown state files:

```text
webbuilder/evidence/
|-- ui/
|-- e2e/
|-- accessibility/
|-- performance/
`-- security/
```

State files contain stable paths, summaries, and verdicts rather than full raw output.

Raw evidence is ignored by Git by default unless the project rules require durable committed artifacts. The validation log and delivery report always retain the commands, verdicts, stable finding IDs, and artifact paths or external references needed for audit.

## 11. Phase and Gate Behavior

### 11.1 Specification Gate

Before confirmation, verify:

- every requirement has an acceptance signal;
- pages, data, APIs, and permissions cover the stated workflows;
- decisions do not contradict each other;
- error states and non-goals are explicit;
- the selected technology can satisfy the confirmed scope;
- verification commands or scenarios are defined.

### 11.2 Initialization Gate

Before business implementation:

- dependencies install;
- database starts;
- migrations run;
- development server starts;
- typecheck and build execute;
- test harness executes;
- Docker configuration is syntactically and operationally valid;
- health and initial authentication smoke checks pass when applicable.

### 11.3 Task Gate

Each vertical slice requires:

- requirement IDs;
- bounded implementation scope;
- behavioral verification;
- applicable UI state coverage;
- Developer submission evidence;
- independent checking;
- integration strategy;
- main-workspace re-verification.

For ordinary delegated work, one independent checker may perform both Tester and Reviewer duties. The acceptance validator must require the checker to be independent from the Developer, but must not require separate Tester and Reviewer identities unless `checker_strategy: separate_tester_reviewer` applies.

High and critical tasks continue to require distinct Developer, Tester, and Reviewer identities.

### 11.4 UI and Browser Gate

For affected user-visible flows during task execution:

- run the relevant Playwright scenario;
- render only affected pages and states;
- capture the viewports needed to exercise the changed layout;
- record console, network, overflow, and interaction failures;
- repair and re-run within the task budget.

For final integration validation, run the complete supported matrix:

- baseline viewports: 390, 768, and 1440 CSS pixels;
- primary pages and workflows;
- loading, empty, error, disabled, validation, success, and permission states where applicable;
- keyboard navigation and visible focus;
- automated accessibility checks;
- profile-defined performance checks in a stable production-like environment;
- console and failed-request checks.

No visual pass may be claimed without actual rendered evidence.

### 11.5 Final Delivery Gate

Prove that:

- the documented standard or Docker command starts the system;
- migrations and seed data work from a clean state;
- authentication, permissions, and primary workflows pass end-to-end tests when applicable;
- build, typecheck, unit, and integration checks pass;
- the final UI evidence matrix is complete;
- no blocking accessibility, security, performance, or runtime findings remain;
- every confirmed requirement maps to implementation and evidence;
- run instructions, risks, and incomplete items are explicit.

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

Findings use stable IDs, severity, affected page or component, evidence path, remediation, and re-verification status.

The implementation should borrow mechanisms rather than copy third-party text or code without license review. Primary references include StyleSeed's persistent design lock and screenshot loop, Impeccable's routed operations and deterministic finding registry, and Web Quality Skills' objective accessibility and performance gates.

## 13. Repair and Stop Policy

Preserve current budgets:

- task repair: at most 3 attempts;
- integration repair: at most 5 attempts;
- the same failure fingerprint 3 times: stop.

Every repair must:

1. cite failure evidence;
2. identify one primary cause;
3. change only what is needed to address that cause;
4. re-run the failing verification;
5. update the validation record;
6. proceed only after the gate passes.

Existing task and workflow statuses remain unchanged. When autonomous continuation stops, `loop-state.md` records a `stop_reason`:

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

## 14. Testing Strategy for WebBuilder Itself

### 14.1 Deterministic State Tests

Add tests for:

- autonomous draft state;
- one-confirmation approval transition;
- rejection of execution before confirmation;
- guided-mode compatibility;
- quality-domain validation;
- project-level evidence records;
- UI evidence completeness;
- delivery rejection when required evidence is missing;
- independent-checker identity behavior;
- migration from schema 1.3 without content loss.

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

## 15. Rollout

### Phase 1: Confirmation and State Semantics

- Add delivery mode and confirmation fields.
- Add Solution Contract templates and checks.
- Preserve guided mode.
- Fix independent-checker identity semantics.

### Phase 2: Universal Full-Stack and UI Baselines

- Strengthen technology, architecture, frontend, backend, data, security, and testing references.
- Add the UI Design Lock and state matrix.
- Add quality domains to task contracts.

### Phase 3: Executable Product Evidence

- Add project-level validation records.
- Add browser, screenshot, accessibility, performance, security, and delivery-smoke evidence contracts.
- Extend the delivery gate and coverage matrix.

### Phase 4: Behavioral Evaluation and Example Project

- Add prompt-level skill evaluations.
- Add a maintained end-to-end example.
- Validate installation and discovery on supported hosts.

### Phase 5: Progressive Domain References

- Add specialized references only after the general full-stack path is stable.
- Validate that irrelevant references are not loaded.
- Keep domain knowledge separate from the core state machine.

## 16. Risks and Mitigations

### Over-automation chooses the wrong product

Mitigation: one consolidated confirmation exposes assumptions, exclusions, architecture, UI direction, and acceptance criteria before implementation.

### One confirmation is mistaken for unlimited authority

Mitigation: approval scope explicitly excludes credentials, paid resources, irreversible external actions, and unconfirmed production changes.

### UI validation becomes slow

Mitigation: task gates render affected pages and states only; the complete viewport and state matrix runs at final integration validation.

### Lighthouse or browser checks are unstable

Mitigation: the selected technology profile records its performance budgets. Final performance gates run in a documented stable production-like environment, preserve raw evidence, and distinguish environmental failure from product failure.

### The Skill becomes too large

Mitigation: keep the main `SKILL.md` as a router and policy source; move detailed universal and specialized guidance into progressively loaded references.

### Specialized knowledge overtakes the general workflow

Mitigation: domain references contribute constraints and checks only. Core product, UI, execution, and delivery responsibilities remain unconditional.

### State schema becomes fragile

Mitigation: preserve existing files, add fields minimally, provide idempotent migration, and extend deterministic state tests before changing execution behavior.

## 17. Acceptance Criteria for This Design

The implementation derived from this design is acceptable when:

1. Existing guided WebBuilder projects remain valid or migrate without content loss.
2. Autonomous mode generates one complete confirmation bundle from a concise requirement.
3. Execution cannot begin before that bundle is approved.
4. Approval transitions existing baseline artifacts to executable states without creating duplicate truth files.
5. User-facing projects cannot deliver without rendered UI evidence and applicable accessibility checks.
6. API-only projects can explicitly mark UI requirements not applicable without bypassing functional, security, or delivery checks.
7. Ordinary delegated work supports one independent checker performing both test and review duties.
8. High and critical work still requires separate Tester and Reviewer identities.
9. Final delivery proves startup, data initialization, primary workflows, requirement coverage, and all applicable quality domains.
10. WebBuilder remains a portable host-driven Skill without a required background runtime or external agent service.
