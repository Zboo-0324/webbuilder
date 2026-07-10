---
name: spec2web
description: Use when the user asks to initialize, enable, start, resume, or run Spec2Web for a web project, or when the current project contains spec2web/loop-state.md with status active. Guides full-stack web delivery through first-principles baselines, phase gates, adaptive single/delegated/parallel agent execution, risk-tiered independent and adversarial review, isolated PR/worktree handoffs, serial integration, repair, and delivery reporting.
---

# Spec2Web

Use this Skill to guide a coding agent through full-stack web project delivery without a heavy runtime, code generator, MCP server, or background scheduler.

## Activation

Use this Skill when the user explicitly asks to initialize, enable, start, resume, continue, or run Spec2Web, including natural-language variants such as:

- `/spec2web initialize this project`
- `/spec2web enable workflow`
- `/spec2web start from requirements.md`
- `/spec2web continue current task`
- `/spec2web show status`
- `/spec2web generate delivery report`
- "use Spec2Web for this project"
- "start Spec2Web mode"

If the current project contains `spec2web/loop-state.md` with `status: active`, continue to use this Skill for full-stack project work. If the workflow is not initialized and the user asks for an ordinary coding task, do not take over the task automatically.

For localized invocation examples and install paths, read `references/install.md`.

## Initialization

When the user asks to initialize Spec2Web:

1. Resolve `<skill-root>` to the folder containing this `SKILL.md` and `<project-root>` to the target project.
2. Read project rule files before changing state.
3. Run `python <skill-root>/scripts/init-state.py --target <project-root>`.
4. If existing state predates schema 1.3, dry-run and then apply the non-destructive migration:

```text
python <skill-root>/scripts/migrate-state.py --target <project-root> --dry-run
python <skill-root>/scripts/migrate-state.py --target <project-root>
```

5. Run the structure check and repair remaining fields in older state files without overwriting confirmed content:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase structure
```

6. Populate Project Rules, Requirement Baseline, System Design, and Task Breakdown in order. Keep generated artifacts `draft` until their phase exit gates are satisfied.

## Hard Gates

Do not write application code until all of these exist and are ready:

- `spec2web/project-rules.md` has `status: ready`,
- `spec2web/requirements-baseline.md` has `status: confirmed`,
- the Requirement Baseline records outcome, hard constraints/invariants, assumptions with evidence, and blocking questions,
- `spec2web/system-design.md` has `status: ready`,
- `spec2web/task-plan.md` has `status: ready`,
- `spec2web/loop-state.md`

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
- verification results are recorded in `spec2web/validation-log.md`,
- Reviewer has checked scope, quality, and workflow compliance,
- high- and critical-risk tasks have passed their declared adversarial review and separate Tester/Reviewer checks,
- Orchestrator has run the task acceptance gate and chosen accept, repair, or block,
- Orchestrator has executed a formal integration point when acceptance passed,
- main-workspace verification passed after integration,
- `spec2web/loop-state.md` is updated.

## Workflow

Follow this sequence:

1. Project Rules
2. First-Principles Analysis
3. Requirement Baseline
4. Technology Strategy
5. Interface Design Baseline
6. System Design
7. Task Breakdown
8. Task Execution Loop: submission, acceptance, integration, and main-workspace verification
9. Integration Validation
10. Delivery

Phase exit gates:

- Project Rules exits only when implementation-relevant rules and conflicts are recorded and `project-rules.md` is `ready`.
- Requirement Baseline exits only when the outcome, hard constraints/invariants, assumptions with evidence, open questions, requirements, and acceptance signals are confirmed and `requirements-baseline.md` is `confirmed`.
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

Summarize implementation-relevant rules into `spec2web/project-rules.md`. User instructions take priority over project rules; project rules take priority over this Skill; this Skill takes priority over default agent habits.

## First-Principles and Review

Before design or task dispatch, distinguish verified facts and constraints from assumptions, record the evidence for important assumptions, and state which unknowns block safe implementation. Treat roles as explicit evaluation standards, not persona prompts.

Every task must declare `risk_level`, a concrete `risk_basis`, and a task-owned `checker_strategy`. `unclassified` tasks may be structurally valid but cannot start execution. `high` and `critical` tasks require declared adversarial failure paths, `review_mode: adversarial`, and separate Tester and Reviewer roles. Critical tasks additionally require user approval, rollback, recovery-point, and residual-risk-owner evidence. Do not impose that overhead on low-risk work.

For the full first-principles, risk, adversarial-review, and disagreement protocol, read `references/reasoning-and-review.md`.

## State Files

Maintain project memory in `spec2web/`:

- `project-rules.md`
- `requirements-baseline.md`
- `system-design.md`
- `task-plan.md`
- `loop-state.md`
- `validation-log.md`
- `delivery-report.md`

Conversation context does not replace these files. On resume, first read `project-rules.md`, `task-plan.md`, and `loop-state.md`.

Require `schema_version: 1.3` in `loop-state.md`.

For templates and update rules, read `references/state-files.md`.

## Technology Strategy

During Requirement Baseline and System Design, recommend a technology stack before task breakdown. For existing projects, prefer the current stack unless there is a clear reason to change. For new projects, compare 2-3 viable stacks, recommend one, record tradeoffs, and write the confirmed choice into `system-design.md`.

For stack selection rules and templates, read `references/technology-strategy.md`.

## Interface Design Baseline

Before frontend implementation tasks, define the interface baseline in `system-design.md`: pages, user flows, layout direction, core states, component conventions, responsive constraints, and UI verification. Do not let frontend tasks begin from vague page names alone.

For interface planning rules and templates, read `references/interface-design.md`.

## Loop Engineering Model

Spec2Web owns the loop. The agent must repeatedly read state, select bounded work, execute, verify, review, repair or record, and update state. For the full protocol, read `references/loop-engineering.md`.

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
- `repair_attempt`
- `last_failure_fingerprint`
- `same_fingerprint_count`
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

## Optional Superpowers

Superpowers are optional step-level helpers, not the workflow owner.

Use them when available:

- requirement baseline: `superpowers:brainstorming`
- task planning: `superpowers:writing-plans`
- debugging and repair: `superpowers:systematic-debugging`
- completion claims: `superpowers:verification-before-completion`

All outputs from external Skills must be written back to Spec2Web state files. External Skills may not skip requirements baseline, task breakdown, validation logging, or delivery reporting.

## Delivery

Before final delivery, run the project-specific verification commands, update `validation-log.md`, generate `delivery-report.md`, mark its status `complete`, set terminal workflow state, and run:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase delivery
```

For final checks and report structure, read `references/delivery-checklist.md`.
