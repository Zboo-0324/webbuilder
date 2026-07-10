# Role Protocol

Spec2Web separates responsibilities around a fixed Orchestrator. The main session stays Orchestrator and delegates implementation through PR/worktree handoff when the host provides subagent or subsession capability.

Do not call Claude, external AI services, remote agent products, or another model provider to simulate delegation. Delegation means using the current host's available local agent/session tools.

Fallback to single-session role switching only when:

- subagents are unavailable,
- the task is too coupled to split safely,
- the task is small enough that delegation overhead would exceed the work.

Record the fallback reason in `loop-state.md`.

## Orchestrator

- read and update `loop-state.md`
- select the current task or safe parallel batch
- delegate Developer, Tester, Reviewer, and Repairer roles when available
- ensure project rules are followed
- create and record task branches, worktrees, and PR handoff status
- give each worker a bounded task contract, branch, worktree, and allowed write scope
- receive worker submission packages
- decide accept, repair, block, or integrate
- choose and record the integration strategy
- integrate serially
- use `direct_apply` for accepted `single_session` work already present in the main workspace
- mark tasks `accepted`, `integrated`, `complete`, `needs_repair`, or `blocked`
- stop on conflicts, failed validation, or scope drift

## Planner

- analyze requirements
- state assumptions
- produce `requirements-baseline.md`
- produce `system-design.md`
- produce `task-plan.md`
- leave each artifact `draft` until its phase exit gate is satisfied
- mark requirements `confirmed` and design/task artifacts `ready` only when their contents support execution

## Developer

- implement exactly one task
- start only after the execution-phase state check passes
- work only in the assigned task worktree when PR/worktree mode is available
- stay within `allowed_paths`
- submit only when `completion_criteria` are met
- set or request `status: submitted_for_acceptance`
- include the required submission package
- commit only to the assigned task branch
- do not self-certify completion
- do not merge, squash, cherry-pick, or create integration commits into the main branch
- do not push or open a remote PR unless Orchestrator explicitly permits it
- do not mark `accepted`, `integrated`, or `complete`

Developer submission package:

- branch name and commit hash
- worktree path
- implementation summary
- changed files
- verification commands run and results
- risks, limitations, or follow-up

## Tester

- run task verification
- add or propose missing behavior tests when appropriate
- record results in `validation-log.md`
- distinguish pre-existing failures from new failures
- recommend pass, repair, or block; do not accept or integrate

## Reviewer

Reviewer is read-only.

Check:

- task maps to requirements
- changed files stay inside `allowed_paths`
- implementation follows `project-rules.md`
- no unplanned full-project generation occurred
- no dependency was added without justification
- verification evidence exists
- submission package is sufficient
- acceptance gate can be evaluated
- PR/worktree mode did not bypass integration review

Reviewer recommends approve, repair, or block. Reviewer does not integrate or mark the task complete.

## Repairer

- repair only from explicit failure evidence
- change one main cause per attempt
- stay within repair budget
- update `validation-log.md`
- return the task to `submitted_for_acceptance` only after new evidence exists

## Delivery

- produce `delivery-report.md`
- include completed features, validation evidence, run instructions, known risks, and not-completed items
