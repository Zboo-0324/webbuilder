# Loop Engineering

Spec2Web uses Loop Engineering as a workflow discipline, not as a background runtime.

## Contents

- Core rule and external memory
- Phase gates and adaptive dispatch
- Bounded work and maker/checker split
- Acceptance, worktrees, and repair
- State updates, continuation, and completion

## Core Rule

Spec2Web owns the loop. Other tools, Skills, subagents, worktrees, pull requests, and shell commands can assist a step, but they do not own the project state or decide that the project is complete.

The main session stays Orchestrator. Developer, Tester, Reviewer, and Repairer should be delegated to host-provided subagents or subsessions through PR/worktree handoff when available. Do not call Claude, external AI services, remote agent products, or another model provider. If delegation is not available, too coupled, or too small to justify, explicitly switch roles in the main session and record the fallback reason in `loop-state.md`.

Every loop follows:

```text
Read State
-> Select Bounded Work
-> Create Branch and Worktree
-> Delegate Worker with Task Contract
-> Worker Commit on Task Branch
-> PR Handoff Submission
-> Test and Review
-> Acceptance Gate
-> Formal Integration Point
-> Integration Gate and Main-Workspace Verification
-> Repair or Record
-> Update State
```

## External Memory

Conversation is not memory. The project memory lives in `webbuilder/`:

- `project-rules.md` records local engineering rules.
- `requirements-baseline.md` records confirmed requirements.
- `system-design.md` records frozen design facts.
- `task-plan.md` is the work queue.
- `loop-state.md` records the current phase, task, constraints, and worktrees.
- `validation-log.md` records evidence.
- `delivery-report.md` records the handoff.

On resume, read `project-rules.md`, `task-plan.md`, and `loop-state.md` before acting.

## Phase Gates

File presence is only a structural check. Before application-code work, require ready or confirmed baselines and run the bundled checker:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase execution
```

Before claiming final delivery, record final evidence, make every task `complete`, mark `delivery-report.md` as `complete`, set `loop-state.md` to `current_phase: delivery` and `status: delivered`, then run:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase delivery
```

If either check fails, repair state or evidence instead of bypassing the gate.

## Adaptive Agent Dispatch

Before each task or batch, inspect host agent capability and free child slots, then record the selected mode in `loop-state.md`:

- `single`: no child Developer; use explicit main-session role switching.
- `delegated`: one child Developer, followed by an independent checker.
- `parallel`: two or more child Developers in validated independent worktrees, followed by independent checking and serial integration.

Run the matching dispatch gate:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase task --task <TASK-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase parallel --parallel-group <PG-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase acceptance --task <TASK-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase integration --task <TASK-ID>
```

Do not hardcode worker count or assume that child agents have isolated filesystems. Reuse released child slots for checking and repair. Read `multi-agent-orchestration.md` for the full selection and queue rules.

## Bounded Work

Do not ask a worker to build the entire project. The Orchestrator selects one task or a safe parallel batch from `task-plan.md`.

Each worker gets one task with:

- requirement IDs
- dependencies
- handoff mode
- integration strategy
- allowed paths
- expected outputs
- verification
- completion criteria
- acceptance gate
- submission package
- repair budget
- integration policy

If the work cannot be bounded, split it before implementation.

For a `single_session` task, use `integration_strategy: direct_apply`. After the Developer role submits evidence, switch back to Orchestrator, evaluate acceptance, record that the accepted changes are already in the main workspace, and run main-workspace verification before marking the task integrated.

## Maker and Checker Split

The Developer creates changes. The Tester and Reviewer check them. Orchestrator accepts or rejects them.

Developer must not self-certify completion. In PR/worktree mode, Developer works only in the assigned worktree, commits only to the task branch, and may only submit `submitted_for_acceptance` with branch, commit hash, worktree path, implementation summary, changed files, verification evidence, and known risks.

Reviewer is read-only and checks:

- requirement mapping
- scope boundaries
- project rules
- validation evidence
- acceptance gate readiness
- worktree and integration protocol
- unplanned functionality

Tester records verification evidence in `validation-log.md`.

For `high` and `critical` tasks, the loop also requires adversarial review: Tester executes declared failure paths, Reviewer evaluates the evidence and remaining risk, and Orchestrator records any disagreement before acceptance.

## Acceptance Ownership

Workers submit evidence; Orchestrator decides state.

Only Orchestrator may set a task to:

- `accepted`
- `integrated`
- `complete`
- `needs_repair`
- `blocked`

Before acceptance, Orchestrator must check the submission package, task branch diff, Tester evidence, Reviewer recommendation, and task `acceptance_gate`. After acceptance, Orchestrator must execute a formal integration point using the task `integration_strategy`. After integration, Orchestrator runs the required main-workspace verification before marking the task complete.

## Worktree Isolation

Worktrees isolate workers. They prevent parallel workers from editing the same checkout, but they do not solve integration correctness by themselves.

Controlled multi-worker mode is allowed only when:

- dependencies are complete
- allowed paths do not overlap
- shared contract files are not modified
- declared shared resources and conflict domains do not intersect
- integration dependencies do not require serial execution
- each task has independent verification
- each task has an independent worktree
- Orchestrator records the batch in `loop-state.md`

Workers never integrate their own work. Orchestrator integrates serially, even when development was parallel.

## Finite Repair

Repair loops must be evidence-driven and bounded:

- task-level repair: at most 3 attempts
- integration-level repair: at most 5 attempts
- same error fingerprint 3 times: stop

Each repair must cite new evidence, change one main cause, rerun verification, and update state.
Record `task_repair_attempt`, `task_failure_fingerprint`, and `task_same_fingerprint_count` for task execution, plus `integration_repair_attempt`, `integration_failure_fingerprint`, and `integration_same_fingerprint_count` for integration repair. The checker rejects task attempts beyond the task budget and stops automatic task repair when the same fingerprint reaches three occurrences.

Stop and ask the user when repair needs:

- changed requirements
- expanded scope
- high-risk dependencies
- real credentials
- paid resources
- unsafe Git operations

## State Update Requirement

Every loop ends with a state update:

- update `loop-state.md` with current status and next step
- update `validation-log.md` with evidence
- update `task-plan.md` when tasks are split, blocked, or completed

If state is not updated, the loop is not complete.

## Continuation Policy

After Orchestrator marks a task complete, it should continue to the next ready task instead of stopping by default.

Continue automatically when:

- `loop-state.md` has `status: active`
- the current task passed verification, review, acceptance, integration, and any required post-integration verification
- state files have been updated
- another task has complete dependencies
- the next task has requirement IDs, allowed paths, and verification
- no stop condition applies

Stop and ask the user when:

- no task is ready
- requirements or design need user confirmation
- repair budget is exhausted
- a Git conflict cannot be resolved safely
- credentials, paid resources, or unsafe operations are needed
- the next task would exceed the current project scope

When all tasks are Orchestrator-complete, move to Integration Validation and Delivery. Terminal `status: delivered` stops automatic continuation.

## Completion Rule

Completion is not a claim and not a worker decision. Completion requires:

- all completed tasks mapped to requirements
- Developer submission package recorded
- verification evidence recorded
- Reviewer sign-off or documented exceptions
- Orchestrator acceptance recorded
- formal integration point recorded
- main workspace validation after integration
- task state updated to `complete`
- `delivery-report.md` generated
