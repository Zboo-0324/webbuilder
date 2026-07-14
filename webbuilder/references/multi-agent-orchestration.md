# Adaptive Multi-Agent Orchestration

WebBuilder uses host-provided agents adaptively. It remains a state-file workflow, not a background scheduler, worker pool, or autonomous merge service.

## Contents

- Execution modes and capability checks
- Host boundary and mode selection
- Parallel and task gates
- Checker and worker contracts
- Serial integration queue

## State Kernel on Resume

Before every resume, recover the canonical state and run the structure gate:

```text
python <skill-root>/scripts/transition-state.py --target <project-root> --recover
python <skill-root>/scripts/check-state.py --target <project-root> --phase structure
```

The transition journal in `webbuilder/.transitions/` is the recovery record for an interrupted multi-file state update. Do not dispatch, accept, integrate, or manually edit around a pending or divergent journal.

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
- `active_checker_strategy`: derived runtime value for the current task (`single_session`, `independent_checker`, `separate_tester_reviewer`, or `mixed` for a mixed-risk batch)

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
- each task has a classified risk with a documented basis and a task-owned checker strategy,
- declared `shared_resources` and `conflict_domains` do not intersect,
- declared `integration_dependencies` do not require serial execution,
- selected worker count matches the group size and does not exceed available child slots.

Development may run in parallel. Acceptance and integration remain serial.

## Task Gate

Before starting one task, set `current_task` and run:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase task --task <TASK-ID>
```

The task gate checks execution readiness, dependency completion, selected execution mode, handoff/workspace consistency, and current-task state.

## Checker Strategy

Each task contract owns one checker strategy; `loop-state.md` records only the active derived value:

- `single_session`: only for low-risk `single` work; the main session explicitly switches out of the Developer role before checking.
- `independent_checker`: one fresh agent combines Tester and Reviewer duties for normal delegated or parallel work.
- `separate_tester_reviewer`: required for `high` and `critical` work, including security-sensitive, migration-heavy, concurrency-sensitive, shared-contract, or release-critical tasks.

`unclassified` work cannot be dispatched. Critical work also requires approved user evidence, a rollback plan, recovery point, and residual-risk owner before acceptance. In a mixed-risk parallel group, validate each task's strategy separately rather than using one global strategy to lower a high-risk task's controls.

The Developer never checks its own completion claim. Checker agents are read-only unless reassigned as Repairer with explicit failure evidence.

Agents may edit descriptive task content and submit evidence, but the State Kernel alone advances approval, readiness, acceptance, integration, stop/resume, and delivery-success values. Use the transition and checker APIs; if the required transition is unavailable, stop for Orchestrator or user direction rather than editing a control value.

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

## Evidence Capture

Workers capture verification evidence using `capture-evidence.py` in their task worktree:

```text
python <skill-root>/scripts/capture-evidence.py --target <project-root> --run <RUN-ID> --subject <TASK-ID> --attempt <N> --contract-revision <REV> -- <command>
```

Evidence is stored under `.webbuilder-artifacts/<run-id>/<subject-id>/<attempt>/` with project-relative paths. The manifest records the command, exit code, implementation fingerprint, artifact hashes, redaction status, and result.

Before integration, the Orchestrator promotes evidence from the worker worktree to the main workspace. Promotion copies artifacts and rewrites paths to remain project-relative. If the source manifest was tampered or the destination already exists with divergent content, promotion rejects the write.

Host capability evidence is checked with `check-host.py`:

```text
python <skill-root>/scripts/check-host.py --target <project-root> --phase host
python <skill-root>/scripts/check-host.py --target <project-root> --phase initialization
python <skill-root>/scripts/check-host.py --target <project-root> --phase ui
```

Record host capabilities in the `## Host Capabilities` section of `loop-state.md`. All evidence output is automatically redacted for authorization headers, cookies, and explicit secrets.

## Integration Queue

For each submitted task:

1. Run independent checking.
2. For `high` and `critical` tasks, run the declared adversarial review and record Tester and Reviewer conclusions separately.
3. Let Orchestrator decide accept, repair, or block.
4. Integrate one accepted task.
5. Run affected verification in the main workspace.
6. Update state before considering the next integration.

Stop the remaining queue on conflict, scope drift, or failed main-workspace verification.

Repair accounting stays scoped: task execution and acceptance use `task_repair_attempt`, `task_failure_fingerprint`, and `task_same_fingerprint_count`; post-acceptance integration uses `integration_repair_attempt`, `integration_failure_fingerprint`, and `integration_same_fingerprint_count`. Do not let either scope consume or reset the other's repair budget.
