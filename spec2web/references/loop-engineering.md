# Loop Engineering

Spec2Web uses Loop Engineering as a workflow discipline, not as a background runtime.

## Core Rule

Spec2Web owns the loop. Other tools, Skills, subagents, and shell commands can assist a step, but they do not own the project state or decide that the project is complete.

Every loop follows:

```text
Read State
-> Select Bounded Work
-> Plan
-> Act
-> Verify
-> Review
-> Repair or Record
-> Update State
```

## External Memory

Conversation is not memory. The project memory lives in `spec2web/`:

- `project-rules.md` records local engineering rules.
- `requirements-baseline.md` records confirmed requirements.
- `system-design.md` records frozen design facts.
- `task-plan.md` is the work queue.
- `loop-state.md` records the current phase, task, constraints, and worktrees.
- `validation-log.md` records evidence.
- `delivery-report.md` records the handoff.

On resume, read `project-rules.md`, `task-plan.md`, and `loop-state.md` before acting.

## Bounded Work

Do not ask a worker to build the entire project. The Orchestrator selects one task or a safe parallel batch from `task-plan.md`.

Each worker gets one task with:

- requirement IDs
- dependencies
- allowed paths
- expected outputs
- verification
- completion criteria
- repair budget
- merge policy

If the work cannot be bounded, split it before implementation.

## Maker and Checker Split

The Developer creates changes. The Tester and Reviewer check them.

Developer must not self-certify completion. Reviewer is read-only and checks:

- requirement mapping
- scope boundaries
- project rules
- validation evidence
- worktree and merge protocol
- unplanned functionality

Tester records verification evidence in `validation-log.md`.

## Worktree Isolation

Worktrees isolate workers. They prevent parallel workers from editing the same checkout, but they do not solve merge correctness by themselves.

Controlled multi-worker mode is allowed only when:

- dependencies are complete
- allowed paths do not overlap
- shared contract files are not modified
- each task has independent verification
- each task has an independent worktree
- Orchestrator records the batch in `loop-state.md`

Workers never merge their own work. Orchestrator merges serially, even when development was parallel.

## Finite Repair

Repair loops must be evidence-driven and bounded:

- task-level repair: at most 3 attempts
- integration-level repair: at most 5 attempts
- same error fingerprint 3 times: stop

Each repair must cite new evidence, change one main cause, rerun verification, and update state.

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

After a task is completed, the Orchestrator should continue to the next ready task instead of stopping by default.

Continue automatically when:

- `loop-state.md` has `status: active`
- the current task passed verification and review
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

When all tasks are complete, move to Integration Validation and Delivery.

## Completion Rule

Completion is not a claim. Completion requires:

- all completed tasks mapped to requirements
- verification evidence recorded
- Reviewer sign-off or documented exceptions
- main workspace validation after merges
- `delivery-report.md` generated
