---
name: webbuilder
description: Use when the user asks to initialize, enable, start, resume, or run WebBuilder for a web project, or when the current project contains webbuilder/loop-state.md with status active. Guides full-stack web delivery through first-principles baselines, phase gates, adaptive single/delegated/parallel agent execution, risk-tiered independent and adversarial review, isolated PR/worktree handoffs, serial integration, repair, and delivery reporting.
---

# WebBuilder

Use this Skill to guide a coding agent through full-stack web project delivery without a heavy runtime, code generator, MCP server, or background scheduler.

## Activation

Use this Skill when the user explicitly asks to initialize, enable, start, resume, continue, or run WebBuilder, including natural-language variants such as:

- `/webbuilder initialize this project`
- `/webbuilder enable workflow`
- `/webbuilder start from requirements.md`
- `/webbuilder start autonomous from requirements.md`
- `/webbuilder continue current task`
- `/webbuilder show status`
- `/webbuilder generate delivery report`
- "use WebBuilder for this project"
- "start WebBuilder mode"

If the current project contains `webbuilder/loop-state.md` with `status: active`, continue to use this Skill for full-stack project work. If the workflow is not initialized and the user asks for an ordinary coding task, do not take over the task automatically.

For localized invocation examples and install paths, read `references/install.md`.

## Initialization

When the user asks to initialize WebBuilder:

1. Resolve `<skill-root>` to the folder containing this `SKILL.md` and `<project-root>` to the target project.
2. Read project rule files before changing state.
3. Run `python <skill-root>/scripts/init-state.py --target <project-root>`.
4. If existing state predates schema 1.4, dry-run and then apply the non-destructive migration:

```text
python <skill-root>/scripts/migrate-state.py --target <project-root> --dry-run
python <skill-root>/scripts/migrate-state.py --target <project-root>
```

5. Recover an interrupted transition, then run the structure check and repair remaining fields in older state files without overwriting confirmed content:

```text
python <skill-root>/scripts/transition-state.py --target <project-root> --recover
python <skill-root>/scripts/check-state.py --target <project-root> --phase structure
```

6. Run the mandatory User Discovery Gate below before writing or confirming the Requirement Baseline. Keep generated artifacts `draft` until their phase exit gates are satisfied.

## Resume Through the State Kernel

Before every resume, recover the State Kernel and verify its structure before reading or changing project state:

```text
python <skill-root>/scripts/transition-state.py --target <project-root> --recover
python <skill-root>/scripts/check-state.py --target <project-root> --phase structure
```

Recovery completes the one journaled transition when its files are still at known original or target contents. If it reports divergent state, stop for manual inspection; do not edit around the journal.

After recovery succeeds, record the resume checkpoint:

```text
python <skill-root>/scripts/transition-state.py --target <project-root> --resume
```

The `--resume` event clears `resume_checkpoint` and `stop_reason` in `loop-state.md` and sets `status` to `active`. Use it when the user explicitly resumes after a declared stop condition was resolved.

## Hard Gates

Do not write application code until all of these exist and are ready:

- `webbuilder/project-rules.md` has `status: ready`,
- `webbuilder/requirements-baseline.md` has `status: confirmed`,
- `webbuilder/requirements-baseline.md` has `discovery_status: confirmed` with recorded user answers,
- the Requirement Baseline records outcome, hard constraints/invariants, assumptions with evidence, and blocking questions,
- `webbuilder/system-design.md` has `status: ready`,
- `webbuilder/task-plan.md` has `status: ready`,
- `webbuilder/loop-state.md`

Before the first application-code task, run the bundled checker from this Skill directory:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase execution
```

Do not proceed while the checker reports draft statuses, placeholders, incomplete task contracts, or an inactive workflow.

Do not accept or mark a task complete until:

- the task maps to requirement IDs,
- the task has a clear verification method,
- the task has an integration strategy,
- delegated or parallel implementation used the assigned PR/worktree handoff; single-session work used `direct_apply`,
- the Developer has submitted an implementation summary and evidence package,
- verification results are recorded in `webbuilder/validation-log.md`,
- Reviewer has checked scope, quality, and workflow compliance,
- high- and critical-risk tasks have passed their declared adversarial review and separate Tester/Reviewer checks,
- Orchestrator has run the task acceptance gate and chosen accept, repair, or block,
- Orchestrator has executed a formal integration point when acceptance passed,
- main-workspace verification passed after integration,
- `webbuilder/loop-state.md` is updated.

## Workflow

Follow this sequence:

1. Project Rules
2. User Discovery Gate
3. First-Principles Analysis
4. Requirement Baseline
5. Technology Strategy
6. Interface Design Baseline
7. System Design
8. Task Breakdown
9. Task Execution Loop: submission, acceptance, integration, and main-workspace verification
10. Integration Validation
11. Delivery

Phase exit gates:

- Project Rules exits only when implementation-relevant rules and conflicts are recorded and `project-rules.md` is `ready`.
- User Discovery exits only after the user has answered the outcome, audience, constraints, success signals, and non-goals questions, and those answers are recorded in `requirements-baseline.md`.
- Requirement Baseline exits only when user discovery is confirmed and the outcome, hard constraints/invariants, assumptions with evidence, open questions, requirements, and acceptance signals are confirmed and `requirements-baseline.md` is `confirmed`.
- System Design exits only when technology, interface, data/API, permissions, and verification decisions are sufficient for the scoped work and `system-design.md` is `ready`.
- Task Breakdown exits only when every task has a complete contract and `task-plan.md` is `ready`.
- Task Execution starts only after the execution-phase state check passes.
- Delivery completes only after every task is `complete`, final evidence is recorded, terminal state is written, and the delivery-phase state check passes.

Each task-level loop follows:

```text
Read State
-> Select Next Task or Parallel Batch
-> Select single, delegated, or parallel Execution Mode
-> Create Task Branch and Worktree when Git is available
-> Plan
-> Delegate Worker with Task Contract
-> Worker Commits to Task Branch
-> PR Handoff Submission
-> Test and Review
-> Orchestrator Acceptance
-> Formal Integration Point or Repair or Record
-> Update State
```

## Orchestration Policy

The main session stays Orchestrator. It owns state, task selection, execution-mode selection, PR/worktree setup, delegation, acceptance, integration decisions, and continuation.

Use agents or subsessions exposed by the current Codex host, including host-authorized local or Codex cloud execution. Do not call third-party AI services, external agent products, or another model provider unless the user explicitly authorizes it.

The old external-agent pattern maps to this local pattern:

```text
Codex Orchestrator -> host subagent worker -> task worktree/branch -> PR handoff -> Orchestrator review/test/integrate
```

Choose adaptively:

- `single` for small, coupled, non-Git, or non-delegable work,
- `delegated` for one bounded worker task followed by an independent checker,
- `parallel` for a machine-validated no-conflict batch in independent worktrees.

Record host capability, free child slots, selected workers, execution mode, and the derived `active_checker_strategy` in `loop-state.md`. The task contract owns `checker_strategy`; do not use runtime state to override it. Do not delegate only because slots exist, and do not assume subagents have isolated filesystems.

For `single_session` tasks, use `integration_strategy: direct_apply`. Treat Orchestrator acceptance plus main-workspace verification as the formal integration point; do not claim a Git merge or commit when none occurred.

Workers submit work for acceptance; they do not decide completion. A Developer may commit only to the assigned task branch and may move a task to `submitted_for_acceptance`. Only Orchestrator may mark it `accepted`, `integrated`, `complete`, `blocked`, or `needs_repair`.

For the complete selection algorithm, task and parallel gates, checker strategies, and integration queue, read `references/multi-agent-orchestration.md`.

## Continuation Policy

After Orchestrator marks a task complete and state is updated, continue automatically when another task is ready.

Continue only when:

- `loop-state.md` has `status: active`,
- the next task has complete dependencies,
- requirement IDs and verification are present,
- current verification and review passed,
- no stop condition applies.

Stop and ask the user when requirements are unclear, design changes are needed, repair budget is exhausted, a Git conflict cannot be resolved safely, credentials or paid resources are needed, or no ready task exists. When no tasks remain, move to Integration Validation and Delivery. After final validation and reporting, set `current_phase: delivery`, set `status: delivered`, and stop automatic continuation.

## Project Rules

Before requirements or coding, read project-level rule files when present:

- `CLAUDE.md`
- `AGENTS.md`
- `GEMINI.md`
- `README.md`

Summarize implementation-relevant rules into `webbuilder/project-rules.md`. User instructions take priority over project rules; project rules take priority over this Skill; this Skill takes priority over default agent habits.

## Mandatory User Discovery Gate

Before filling `requirements-baseline.md`, `system-design.md`, or `task-plan.md`, read the user's brief and the current project context. The brief may be a detailed requirements document or a single sentence. Extract verified facts, likely intent, constraints, and unresolved decisions, then form an AI-authored working hypothesis for the product. Do not ask the user to write the core requirements or design the system for you.

Run discovery as a natural dialogue:

1. Explore relevant project files, requirements documents, and recent decisions first.
2. Draft the likely outcome, users, minimum scope, success signal, and non-goals internally.
3. Ask only the highest-impact unresolved question, one question per message.
4. Prefer 2-3 concrete choices with the recommended option first and a short trade-off. Use an open question only when choices would distort the answer.
5. Incorporate the answer, update the working hypothesis, and ask the next question only if it can materially change scope or design.
6. When the intent is sufficiently clear, propose 2-3 approaches with trade-offs and a recommendation.
7. Present a concise requirements/design summary and ask the user to approve or correct it.

Do not repeat facts already clear from the user's document. Do not ask broad expert questions such as “What constraints, integrations, data, permissions, or compatibility requirements must be preserved?” Instead, infer likely answers and turn genuine uncertainty into an easy decision. Example: “The document suggests the first release is for internal reviewers. Should the MVP optimize for review speed (recommended), annotation throughput, or client reporting?”

Use the host's structured question UI when available. Otherwise ask conversationally and wait. Record the AI working hypothesis, questions asked, and user decisions under `User Discovery`. Set `discovery_status: confirmed` only after the user approves the summarized requirements; do not silently skip the gate.

## Discovery Modes

`loop-state.md` records `delivery_mode: guided | autonomous`. `requirements-baseline.md` records `discovery_method: interactive | inferred_contract`.

**Guided discovery** (default for new and existing projects) keeps the one-question-at-a-time dialogue described above and sets `discovery_method: interactive` in `requirements-baseline.md` when the user confirms requirements.

**Autonomous discovery** drafts the same requirements, system design, and task plan artifacts internally without per-question dialogue. It sets `discovery_method: inferred_contract`, runs the specification phase readiness check, presents one consolidated contract to the user, and waits for approval before proceeding.

Existing and migrated projects remain in guided mode until the user explicitly selects autonomous.

Both modes end with the same specification gate and contract approval commands:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase specification
python <skill-root>/scripts/approve-contract.py --target <project-root> --approval-evidence <user-message-reference>
```

The `--phase specification` gate validates complete contract material, no remaining `not recorded` values, non-empty acceptance signals and primary workflows, and that system design and task plan reference the current contract revision. Before approval the gate allows `confirmation_status: pending`; during execution readiness it requires `approved` with matching revision and digest.

### Material and Non-Material Contract Changes

The following contract fields are **material** and invalidate approval when changed:

`problem`, `desired_outcome`, `target_users`, `primary_jobs`, `core_capabilities`, `non_goals`, `primary_workflows`, `page_navigation_summary`, `ui_direction`, `technology_profile`, `public_interfaces`, `data_boundary`, `permission_boundary`, `delivery_assumptions`, `material_risks`, `acceptance_signals`, `capabilities`, `workload_envelope`.

The following are **non-material** unless they change one of the fields above:

- low-risk dependency selection,
- component details within the chosen technology profile,
- task reordering within the same scope,
- test repair and minor verification adjustments,
- bounded implementation choices within approved architecture.

### Authorization Boundaries

The contract does **not** authorize:

- credentials or secrets,
- paid resources or services,
- production deployment,
- destructive external writes,
- irreversible migration,
- high-risk install scripts,
- secret transmission.

If execution requires any of the above, stop and ask the user.

### Workload Envelope and Declared Stop Condition

The `workload_envelope` block in the contract material records the estimated scope: task count range, browser flows, external dependencies, quality gates, repair budgets (`task: 3`, `integration: 5`), and available concurrency. It does not include token counts, API call estimates, elapsed time estimates, or interruption counts.

A **declared stop condition** is an explicit reason the Orchestrator must pause and ask the user before continuing. Examples: requirements are unclear, a design change is needed, repair budget is exhausted, credentials or paid resources are required, or no ready task exists. The stop reason is recorded in `loop-state.md` via `stop_reason` and resolved by the user before the workflow resumes.

## First-Principles and Review

Before design or task dispatch, distinguish verified facts and constraints from assumptions, record the evidence for important assumptions, and state which unknowns block safe implementation. Treat roles as explicit evaluation standards, not persona prompts.

Every task must declare `risk_level`, a concrete `risk_basis`, and a task-owned `checker_strategy`. `unclassified` tasks may be structurally valid but cannot start execution. `high` and `critical` tasks require declared adversarial failure paths, `review_mode: adversarial`, and separate Tester and Reviewer roles. Critical tasks additionally require user approval, rollback, recovery-point, and residual-risk-owner evidence. Do not impose that overhead on low-risk work.

For the full first-principles, risk, adversarial-review, and disagreement protocol, read `references/reasoning-and-review.md`.

## State Files

Maintain project memory in `webbuilder/`:

- `project-rules.md`
- `requirements-baseline.md`
- `system-design.md`
- `task-plan.md`
- `loop-state.md`
- `validation-log.md`
- `delivery-report.md`

Conversation context does not replace these files. `loop-state.md` is the canonical State Kernel record. On resume, recover and structure-check it before reading `project-rules.md`, `task-plan.md`, and `loop-state.md`.

Require `schema_version: 1.4` in `loop-state.md`, including `delivery_mode`, `autonomy_scope`, `stop_reason`, `resume_checkpoint`, `active_run_id`, `state_revision`, and `pending_transition`.

Agents may edit descriptive content and submit evidence, but may not manually set approval, readiness, acceptance, integration, stop/resume, or delivery-success values. Use the State Kernel transition and checker APIs for those changes. If no supported transition applies, stop and ask rather than editing a control value directly.

Use only the supported `transition-state.py --event` lifecycle operations; they construct control updates internally and validate their applicable gates before writing. `--set` is reserved for `edit-descriptive-content` and rejects lifecycle control keys. The exact event table is in `references/state-files.md`.

For templates and update rules, read `references/state-files.md`.

## Technology Strategy

During Requirement Baseline and System Design, recommend a technology stack before task breakdown. For existing projects, prefer the current stack unless there is a clear reason to change. For new projects, compare 2-3 viable stacks, recommend one, record tradeoffs, and write the confirmed choice into `system-design.md`.

For stack selection rules and templates, read `references/technology-strategy.md`.

## Interface Design Baseline

Before frontend implementation tasks, define the interface baseline in `system-design.md`: pages, user flows, layout direction, core states, component conventions, responsive constraints, and UI verification. Do not let frontend tasks begin from vague page names alone.

For interface planning rules and templates, read `references/interface-design.md`.

## Loop Engineering Model

WebBuilder owns the loop. The agent must repeatedly read state, select bounded work, execute, verify, review, repair or record, and update state. For the full protocol, read `references/loop-engineering.md`.

## Task Breakdown

Use mixed decomposition:

- first freeze shared cross-cutting contracts,
- then deliver vertical business slices.

Every task must have:

- `task_id`
- `requirement_ids`
- `goal`
- `dependencies`
- `status`
- `risk_level`
- `risk_basis`
- `checker_strategy`
- `review_mode`
- `adversarial_review`
- `user_approval`
- `approval_evidence`
- `rollback_plan`
- `recovery_point`
- `residual_risk_owner`
- `handoff_mode`
- `integration_strategy`
- `allowed_paths`
- `expected_outputs`
- `verification`
- `completion_criteria`
- `acceptance_gate`
- `repair_budget`
- `submission_package`
- `risks_or_blockers`
- `execution_workspace`
- `parallel_group`
- `shared_resources`
- `conflict_domains`
- `integration_dependencies`
- `task_repair_attempt`
- `task_failure_fingerprint`
- `task_same_fingerprint_count`
- `integration_repair_attempt`
- `integration_failure_fingerprint`
- `integration_same_fingerprint_count`
- `integration_policy`

For task rules and templates, read `references/task-breakdown.md`.

## Roles

Use role separation with Orchestrator as the fixed main-session role:

- Orchestrator maintains state, selects tasks, chooses safe parallel batches, and controls integration.
- Planner analyzes requirements, designs the system, and decomposes tasks.
- Developer implements one task inside its boundary.
- Tester verifies behavior and requirement coverage.
- Reviewer performs read-only review of scope, code quality, risk, and workflow compliance.
- Repairer fixes failures using explicit evidence.
- Delivery prepares final reporting.

For normal delegated work, one fresh `independent_checker` may combine Tester and Reviewer duties. `high` and `critical` tasks require `separate_tester_reviewer` and adversarial review. Tester, Reviewer, and Developer identities must be distinct whenever the declared strategy requires it. When safe delegation is unavailable, explicitly switch roles only for low-risk work and record the fallback reason. Developer may not self-certify completion or integrate.

For detailed role rules, read `references/role-protocol.md`.

## PR/Worktree Mode

Default to PR/worktree isolation for implementation tasks when the project is a Git repository. If the project is not a Git repository, ask the user before initializing Git.

Default to one task at a time. Controlled multi-worker mode is allowed only when Orchestrator explicitly selects a no-conflict batch from `task-plan.md`.

Parallel tasks must satisfy:

- dependencies are complete,
- `allowed_paths` do not overlap,
- no shared contract files are modified,
- each task has independent verification,
- each task uses an independent worktree,
- Orchestrator records the batch in `loop-state.md`.

Even when development is parallel, integration is serial. Each integration requires worker submission, independent checker evidence or separate Tester/Reviewer evidence, Orchestrator acceptance, a recorded integration strategy, main-workspace verification, and state updates.

Before dispatching one task, run:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase task --task <TASK-ID>
```

Before dispatching a parallel batch, run:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase parallel --parallel-group <PG-ID>
```

Before accepting or completing a task, run the evidence gates:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase acceptance --task <TASK-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase integration --task <TASK-ID>
```

For PR/worktree handoff details, read `references/worktree-mode.md`.

## Repair Budget

Use finite repair loops:

- task-level repair: at most 3 attempts,
- integration-level repair: at most 5 attempts,
- same error fingerprint 3 times: stop.

Each repair must cite new evidence, change one main cause, rerun verification, and update `validation-log.md`. If fixing requires changing confirmed requirements, expanding scope, adding high-risk dependencies, using real credentials, or creating paid resources, stop and ask the user.

Keep the scopes separate: `task_repair_attempt` and its fingerprint fields govern task execution and acceptance, while `integration_repair_attempt` and its fingerprint fields govern post-acceptance integration. A failure in one scope never consumes the other scope's budget.

## Superpowers

Superpowers remain helpers, not the workflow owner. The requirement-baseline helper is mandatory when it is available: invoke `superpowers:brainstorming` during the User Discovery Gate before confirming requirements. If it is unavailable, perform the same discovery questions natively; the absence of the helper is never a reason to skip user clarification.

Use the other helpers when available:

- task planning: `superpowers:writing-plans`
- debugging and repair: `superpowers:systematic-debugging`
- completion claims: `superpowers:verification-before-completion`

All outputs from external Skills must be written back to WebBuilder state files. External Skills may not skip requirements baseline, task breakdown, validation logging, or delivery reporting.

## Evidence Capture

Before integration and delivery, capture machine-verifiable evidence of verification commands:

```text
python <skill-root>/scripts/capture-evidence.py --target <project-root> --run <RUN-ID> --subject <TASK-ID> --attempt <N> --contract-revision <REV> -- <command>
```

Evidence manifests are stored under `.webbuilder-artifacts/<run-id>/<subject-id>/<attempt>/` with relative project paths. Each manifest records the command, exit code, implementation fingerprint, artifact hashes, and redaction status.

Workers capture evidence in their task worktree. Orchestrator promotes evidence to the main workspace before integration using the `promote_artifacts` function, which copies artifacts and rewrites paths to be project-relative.

## Redaction Policy

All captured evidence is automatically redacted before writing. The redactor strips authorization headers, Cookie headers, and secret-bearing assignment patterns from command output. Pass `--explicit-secrets <value>` to redact additional tokens. If redaction fails, the manifest records `redaction.status: failed` and the delivery gate rejects it.

Authorization header values (Bearer tokens, Basic credentials, API keys in headers) are always redacted regardless of `--explicit-secrets`.

## Host Capability Check

Before dispatching tasks that require specific host capabilities (UI, database, docker, etc.), verify the host can support them:

```text
python <skill-root>/scripts/check-host.py --target <project-root> --phase host
python <skill-root>/scripts/check-host.py --target <project-root> --phase initialization
python <skill-root>/scripts/check-host.py --target <project-root> --phase ui
```

- `host` validates that all capabilities marked `required` in the contract have `available` status with evidence in `loop-state.md`.
- `initialization` validates that required capabilities have evidence but allows `not_applicable` capabilities to lack evidence.
- `ui` validates that UI-specific evidence manifests exist when the contract declares `ui` as `required`.

Record host capability evidence in the `## Host Capabilities` section of `loop-state.md` as a JSON block with status and evidence for each capability.

## Manifest-Backed Final Delivery

The delivery gate now verifies that every required verification domain has a valid evidence manifest. Handwritten "passed" text in `validation-log.md` is not sufficient; each delivery domain (`functional`, `security`, `performance`, `delivery-smoke`, and `ui`/`accessibility` when applicable) must have a `PROJECT / <domain>` entry referencing an `artifact_manifest` path under `.webbuilder-artifacts/`.

The delivery gate verifies each manifest: artifact hashes must match, the contract revision must be current, the implementation fingerprint must match, redaction must have passed, and the result must be `passed`.

## Delivery

Before final delivery, run the project-specific verification commands, capture evidence, update `validation-log.md`, generate `delivery-report.md`, mark its status `complete`, set terminal workflow state, and run:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase delivery
```

For final checks and report structure, read `references/delivery-checklist.md`.
