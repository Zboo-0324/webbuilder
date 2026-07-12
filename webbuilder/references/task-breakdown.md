# Task Breakdown

Use mixed decomposition:

```text
First freeze cross-cutting contracts.
Then deliver vertical business slices.
```

## Contents

- Cross-cutting and vertical tasks
- Task contract and status ownership
- Handoff and integration strategies
- Acceptance and parallel eligibility
- Required refusal rules

## Cross-Cutting Tasks

Use these only when needed:

- project skeleton and run commands
- data model
- API contract
- permission model
- page map
- validation command setup

These tasks are usually serial because they affect shared contracts.

## Vertical Slice Tasks

Prefer small user-visible slices:

- login loop
- list view loop
- create/edit loop
- core business action loop
- report/export loop

Each vertical task should be independently verifiable.

## Task Contract

Each task must include:

```markdown
### TASK-000: Title

- requirement_ids: REQ-000
- goal: One concrete outcome.
- dependencies: TASK-000 or none
- status: pending
- risk_level: unclassified
- risk_basis:
  - Concrete reason and affected surface.
- checker_strategy: single_session
- review_mode: standard
- adversarial_review:
  - not_applicable
- user_approval: not_required
- approval_evidence:
  - not_applicable
- rollback_plan:
  - not_applicable
- recovery_point:
  - not_applicable
- residual_risk_owner: not_applicable
- handoff_mode: pr_worktree
- integration_strategy: squash_merge
- allowed_paths:
  - path/pattern
- expected_outputs:
  - path or behavior
- verification:
  - exact command or manual check
- completion_criteria:
  - worker-observable condition for submitting the task
- acceptance_gate:
  - Orchestrator check required before accepting or merging
- repair_budget: 3
- submission_package:
  - branch name and commit hash
  - worktree path
  - implementation summary
  - changed files
  - verification evidence
  - known risks or follow-up
- risks_or_blockers:
  - none
- execution_workspace: main or worktree
- parallel_group: none or PG-000
- shared_resources:
  - none
- conflict_domains:
  - none
- integration_dependencies:
  - none
- task_repair_attempt: 0
- task_failure_fingerprint: none
- task_same_fingerprint_count: 0
- integration_repair_attempt: 0
- integration_failure_fingerprint: none
- integration_same_fingerprint_count: 0
- integration_policy: orchestrator_review_then_serial_integration
```

## Completion vs Acceptance

`completion_criteria` describes when a worker can submit the task for acceptance. It is not permission to mark the task complete.

Use these status values:

- `pending`: task is ready or waiting on dependencies.
- `in_progress`: a worker is executing the task.
- `submitted_for_acceptance`: Developer has submitted the task package.
- `needs_repair`: Orchestrator or Reviewer rejected the submission with evidence.
- `accepted`: Orchestrator accepted the task before integration.
- `integrated`: Orchestrator integrated the accepted task into the main workspace or main branch.
- `complete`: post-integration verification passed and state is updated.
- `blocked`: task cannot proceed without user input or external change.

Only Orchestrator may set `accepted`, `integrated`, or `complete`. Developer, Tester, and Reviewer provide evidence; they do not self-certify completion.

## Risk and Review Mode

Classify every task as `unclassified`, `low`, `standard`, `high`, or `critical`, and record a concrete `risk_basis`. `unclassified` may pass structure validation but cannot pass execution, task, or parallel validation.

- `low` tasks may use `review_mode: standard` and `checker_strategy: single_session`.
- `standard` delegated work requires `checker_strategy: independent_checker`.
- `high` tasks require `review_mode: adversarial`, concrete `adversarial_review` cases, PR/worktree handoff, and `checker_strategy: separate_tester_reviewer`.
- `critical` tasks inherit the high-risk controls and require `user_approval: approved`, approval evidence, rollback plan, recovery point, and residual-risk owner.

The task contract owns its risk and checker strategy. `loop-state.md` may record the derived `active_checker_strategy` for the current task, but it cannot lower or replace the task contract.

The declared adversarial cases must name credible failure paths relevant to the task, such as invalid or boundary input, timeout and retry, partial failure, concurrency, authorization, rollback, compatibility, deployment, or observability. Record the resulting evidence in `validation-log.md`.

Do not start implementation until `task-plan.md` has top-level `status: ready` and the execution-phase state check passes. Set it back to `draft` whenever requirements, shared contracts, or task boundaries need replanning.

## Handoff Mode

Use `handoff_mode: pr_worktree` for implementation tasks when the project is a Git repository. This means:

- Orchestrator creates the task branch and worktree,
- Developer works only in that worktree,
- Developer commits only to the task branch,
- Developer submits a local or remote PR package,
- Orchestrator reviews, tests, accepts, integrates, and runs post-integration verification.

Use `handoff_mode: single_session` only when subagents are unavailable, the task is too coupled to isolate safely, or the task is small enough that delegation overhead exceeds the work. Record the reason in `loop-state.md`.

Pair `single_session` with `integration_strategy: direct_apply`. The Orchestrator records acceptance, confirms the changes are already in the main workspace, runs main-workspace verification, and then marks the task integrated; no Git operation is implied.

## Integration Strategy

Each implementation task must declare one `integration_strategy`:

- `merge`: preserve the task branch history.
- `squash_merge`: collapse the task branch into one mainline commit.
- `cherry_pick`: apply selected task commits only.
- `integration_commit`: Orchestrator creates a new reconciliation commit from one or more accepted tasks.
- `direct_apply`: for `single_session` tasks whose accepted changes are already in the main workspace, including non-Git projects; record acceptance and main-workspace verification without claiming a merge or commit.

The strategy may change only before integration and only by Orchestrator. Record the chosen strategy and resulting integration commit in `loop-state.md` or `validation-log.md`.

## Acceptance Gate

Each `acceptance_gate` must be specific enough for Orchestrator to decide accept, repair, or block. Include:

- required verification command or manual check,
- Reviewer scope and quality check,
- requirement IDs covered,
- main-workspace verification needed after integration,
- rejection conditions such as scope drift, missing evidence, conflict, or failed tests.

For `high` and `critical` tasks, also include the declared failure paths, the required Tester evidence, the required Reviewer conclusion, and how disagreement will be resolved.

## Parallel Eligibility

Define project-specific serial-only paths near the top of `task-plan.md`:

```markdown
## Shared Contract Paths

- webbuilder/
- package.json
- pyproject.toml
- migrations/
- openapi/
```

Tasks can run in the same parallel group only when:

- all dependencies are complete,
- `allowed_paths` do not overlap,
- neither task modifies shared contract files,
- each task has independent verification,
- each task has an independent worktree,
- Orchestrator records the group in `loop-state.md`.
- their declared `shared_resources` and `conflict_domains` do not intersect;
- their `integration_dependencies` are complete and do not form a cycle.

Declare `shared_resources` (database, generated artifact, port, external service, or `none`), `conflict_domains` (auth, routing, schema, build, deployment, global-state, or `none`), and `integration_dependencies` for every parallel candidate. If the machine cannot judge a conflict, record an explicit Orchestrator safety reason and run serially.

Before dispatch, run the parallel gate. Do not spawn the batch if it fails:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase parallel --parallel-group <PG-ID>
```

Shared contract files are serial by default:

- requirements baseline
- system design
- task plan
- database migrations
- API contract or OpenAPI files
- global router entry
- global state store
- build configuration

## Required Refusal

If a task is too broad, do not implement it. Split it first.

Do not implement features without requirement IDs.
