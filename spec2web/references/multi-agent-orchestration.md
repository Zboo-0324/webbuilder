# Adaptive Multi-Agent Orchestration

Spec2Web uses host-provided agents adaptively. It remains a state-file workflow, not a background scheduler, worker pool, or autonomous merge service.

## Contents

- Execution modes and capability checks
- Host boundary and mode selection
- Parallel and task gates
- Checker and worker contracts
- Serial integration queue

## Execution Modes

Choose one mode for the current task or batch and record it in `loop-state.md`:

- `single`: keep work in the main session for small, coupled, non-Git, or non-delegable tasks.
- `delegated`: assign one bounded task to one Developer agent, then use an independent checker.
- `parallel`: assign a validated no-conflict task group to multiple Developer agents in independent worktrees.

Select the smallest mode that preserves maker/checker independence. Do not delegate solely because agent slots exist. `high` and `critical` tasks are never eligible for the `single_session` checker strategy.

## Capability Check

Before delegation:

1. Inspect the host's available agent capability and free child-agent slots.
2. Record `host_agent_capability`, `available_child_slots`, and `selected_workers` in `loop-state.md`.
3. Set `selected_workers` to no more than both the ready task count and the host-reported free child slots.
4. Reserve the main session as Orchestrator.
5. Reuse released child slots for checking and repair instead of keeping idle role agents alive.

Do not hardcode a worker count. If the host cannot report slots, use `single` unless the user explicitly chooses a safe delegated path.

Use only these state values:

- `host_agent_capability`: `unknown`, `unavailable`, or `available`
- `available_child_slots`: `unknown` or a non-negative integer
- `selected_workers`: a non-negative integer counting Developer workers, not later checker agents
- `checker_strategy`: `single_session`, `independent_checker`, or `separate_tester_reviewer`

For `single` work, leave capability or slots as `unknown` when they were not inspected. Do not invent values such as `none` or `not_required`.

## Host Boundary

Allowed workers are agents or subsessions exposed by the current Codex host, whether local or Codex-hosted cloud execution. Do not call third-party AI services, another model provider, or an external agent product unless the user explicitly authorizes it.

Agent availability does not imply filesystem isolation. When workers share a filesystem, create and assign explicit Git worktrees before parallel writes.

## Mode Selection

Use `single` when any of these apply:

- the task is small enough that delegation costs more than implementation,
- the task is tightly coupled to active Orchestrator decisions,
- the project is not Git-backed and the user has not authorized Git initialization,
- host agents or safe worktree isolation are unavailable.

Use `delegated` when one bounded task is ready, safe isolation exists, and an independent checker can evaluate the submission.

Use `parallel` only when at least two tasks are ready and all parallel eligibility checks pass.

## Parallel Eligibility

Before spawning parallel workers, run:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase parallel --parallel-group <PG-ID>
```

The selected group must satisfy:

- every dependency is complete,
- every task uses `handoff_mode: pr_worktree`,
- every task has a unique non-main `execution_workspace`,
- `allowed_paths` do not overlap,
- no `allowed_paths` intersect the task plan's Shared Contract Paths,
- each task has independent verification,
- selected worker count matches the group size and does not exceed available child slots.

Development may run in parallel. Acceptance and integration remain serial.

## Task Gate

Before starting one task, set `current_task` and run:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase task --task <TASK-ID>
```

The task gate checks execution readiness, dependency completion, selected execution mode, handoff/workspace consistency, and current-task state.

## Checker Strategy

Record one checker strategy:

- `single_session`: only for low-risk `single` work; the main session explicitly switches out of the Developer role before checking.
- `independent_checker`: one fresh agent combines Tester and Reviewer duties for normal delegated or parallel work.
- `separate_tester_reviewer`: required for `high` and `critical` work, including security-sensitive, migration-heavy, concurrency-sensitive, shared-contract, or release-critical tasks.

The Developer never checks its own completion claim. Checker agents are read-only unless reassigned as Repairer with explicit failure evidence.

## Worker Contract

Give each worker only:

- task and requirement IDs,
- branch and worktree,
- allowed write paths,
- expected outputs,
- verification commands,
- completion criteria,
- required submission package,
- risk level, review mode, and declared adversarial failure paths,
- stop conditions and repair budget.

Workers submit and stop. They do not integrate, expand scope, spawn unplanned workers, or decide completion.

## Integration Queue

For each submitted task:

1. Run independent checking.
2. For `high` and `critical` tasks, run the declared adversarial review and record Tester and Reviewer conclusions separately.
3. Let Orchestrator decide accept, repair, or block.
4. Integrate one accepted task.
5. Run affected verification in the main workspace.
6. Update state before considering the next integration.

Stop the remaining queue on conflict, scope drift, or failed main-workspace verification.
