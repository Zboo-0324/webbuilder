---
name: spec2web
description: Use when the user asks to initialize, enable, start, resume, or run Spec2Web for a web project, or when the current project contains spec2web/loop-state.md with status active. Guides full-stack web delivery through project rules, requirement baseline, technology strategy, interface design, system design, task breakdown, role-separated loops, worktree isolation, validation, repair, and delivery reporting.
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

## Hard Gates

Do not write application code until all of these exist:

- `spec2web/project-rules.md`
- `spec2web/requirements-baseline.md`
- `spec2web/system-design.md`
- `spec2web/task-plan.md`
- `spec2web/loop-state.md`

Do not mark a task complete until:

- the task maps to requirement IDs,
- the task has a clear verification method,
- verification results are recorded in `spec2web/validation-log.md`,
- Reviewer has checked scope, quality, and workflow compliance,
- `spec2web/loop-state.md` is updated.

## Workflow

Follow this sequence:

1. Project Rules
2. Requirement Baseline
3. Technology Strategy
4. Interface Design Baseline
5. System Design
6. Task Breakdown
7. Task Execution Loop
8. Integration Validation
9. Delivery

Each task-level loop follows:

```text
Read State
-> Select Next Task or Parallel Batch
-> Prepare Worktree(s) when enabled
-> Plan
-> Act
-> Verify
-> Review
-> Serial Merge or Repair or Record
-> Update State
```

## Continuation Policy

After a task is completed and state is updated, continue automatically when another task is ready.

Continue only when:

- `loop-state.md` has `status: active`,
- the next task has complete dependencies,
- requirement IDs and verification are present,
- current verification and review passed,
- no stop condition applies.

Stop and ask the user when requirements are unclear, design changes are needed, repair budget is exhausted, a Git conflict cannot be resolved safely, credentials or paid resources are needed, or no ready task exists. When no tasks remain, move to Integration Validation and Delivery.

## Project Rules

Before requirements or coding, read project-level rule files when present:

- `CLAUDE.md`
- `AGENTS.md`
- `GEMINI.md`
- `README.md`

Summarize implementation-relevant rules into `spec2web/project-rules.md`. User instructions take priority over project rules; project rules take priority over this Skill; this Skill takes priority over default agent habits.

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
- `allowed_paths`
- `expected_outputs`
- `verification`
- `completion_criteria`
- `risks_or_blockers`
- `execution_workspace`
- `parallel_group`
- `merge_policy`

For task rules and templates, read `references/task-breakdown.md`.

## Roles

Use role separation even when only one agent is available:

- Orchestrator maintains state, selects tasks, chooses safe parallel batches, and controls merges.
- Planner analyzes requirements, designs the system, and decomposes tasks.
- Developer implements one task inside its boundary.
- Tester verifies behavior and requirement coverage.
- Reviewer performs read-only review of scope, code quality, risk, and workflow compliance.
- Repairer fixes failures using explicit evidence.
- Delivery prepares final reporting.

When subagents are available, use separate agents for Developer, Tester, and Reviewer. When they are not available, explicitly switch roles. Developer may not self-certify completion.

For detailed role rules, read `references/role-protocol.md`.

## Worktree Mode

Prefer Git worktree isolation for development tasks when the project is a Git repository. If the project is not a Git repository, ask the user before initializing Git.

Default to one task at a time. Controlled multi-worker mode is allowed only when Orchestrator explicitly selects a no-conflict batch from `task-plan.md`.

Parallel tasks must satisfy:

- dependencies are complete,
- `allowed_paths` do not overlap,
- no shared contract files are modified,
- each task has independent verification,
- each task uses an independent worktree,
- Orchestrator records the batch in `loop-state.md`.

Even when development is parallel, merges are serial. Each merge requires diff review, task verification, main-workspace verification, and state updates.

For worktree details, read `references/worktree-mode.md`.

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

Before final delivery, run the project-specific verification commands, update `validation-log.md`, and generate `delivery-report.md`.

For final checks and report structure, read `references/delivery-checklist.md`.
