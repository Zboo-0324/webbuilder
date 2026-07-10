# PR/Worktree Mode

PR/worktree mode isolates task execution and makes each worker handoff reviewable. It is a workflow protocol, not a background scheduler.

## Contents

- Definition and preconditions
- Single-task and multi-worker modes
- Orchestrator and worker duties
- PR package and integration point
- Integration rules and naming

## Definition

`PR` means a reviewable handoff. It can be:

- a real remote pull request when the repo has a configured remote and the user permits pushing, or
- a local PR package: task branch, worktree path, commit hash, diff command, verification evidence, and submission summary.

Workers must be agents or subsessions exposed by the current Codex host. Do not call third-party AI services, external agent products, or another model provider unless the user explicitly authorizes it.

## Preconditions

- The project is a Git repository.
- The user has not disabled PR/worktree mode.
- Each task has a task contract.
- The execution-phase state check passes.
- Each implementation task has `handoff_mode: pr_worktree`.
- Orchestrator controls branch, worktree, PR, and integration decisions.
- Workers submit evidence; Orchestrator accepts, integrates, and marks completion.
- The task or parallel dispatch gate passes.

If the project is not a Git repository, ask the user before initializing Git.

## Default Single-Task Mode

```text
Orchestrator selects one task
-> Orchestrator creates task branch and worktree
-> Orchestrator delegates Developer with task contract, branch, worktree, and allowed_paths
-> Developer edits only in the assigned worktree
-> Developer runs task verification
-> Developer commits only to the task branch
-> Developer submits local or remote PR package
-> Tester verifies the submitted branch or worktree
-> Reviewer checks diff, evidence, scope, and project rules
-> Orchestrator records evidence and runs the acceptance gate
-> Orchestrator executes the selected integration strategy
-> Orchestrator records evidence and runs the integration gate
-> main workspace verification runs after integration
-> state files are updated
```

## Controlled Multi-Worker Mode

Validate the batch before creating workers:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase parallel --parallel-group <PG-ID>
```

```text
Orchestrator selects a no-conflict parallel group
-> Orchestrator creates one branch and worktree per task
-> Orchestrator delegates one Developer worker per task
-> each Developer works only in its assigned worktree
-> each Developer commits only to its task branch
-> each Developer submits a PR package
-> each task gets Tester evidence and Reviewer review
-> Orchestrator evaluates each acceptance gate
-> Orchestrator integrates accepted tasks serially
-> after each integration, run affected verification in the main workspace
-> stop later integrations if any integration fails or conflicts
```

## Orchestrator Duties

- create task branch and worktree from the approved base,
- give the worker only the bounded task contract and allowed write scope,
- record branch, worktree, and handoff status in `loop-state.md`,
- receive the PR package,
- review diff and evidence before integration,
- run or delegate verification,
- choose and record the integration strategy,
- integrate serially,
- run post-integration verification in the main workspace,
- clean up worktrees only after state and validation evidence are updated.

## Worker Duties

- work only in the assigned worktree,
- edit only `allowed_paths`,
- do not pull unrelated changes into the task branch unless Orchestrator instructs it,
- do not touch the main workspace,
- do not merge, squash, cherry-pick, or create integration commits into the main branch,
- do not push or open a remote PR unless Orchestrator explicitly permits it,
- commit task changes to the task branch before submitting,
- submit the PR package and stop.

## PR Package

Every Developer submission must include:

- task ID and requirement IDs,
- branch name,
- worktree path,
- commit hash,
- changed files,
- summary of implementation,
- verification commands and results,
- known risks, limitations, or follow-up,
- diff command, such as `git diff <base>...<branch>`.

For a real remote PR, also include the PR URL. For a local PR package, record the package in `loop-state.md` or the task entry.

## Formal Integration Point

Acceptance is not completion. A task reaches the formal integration point only when Orchestrator applies one of these strategies to the main workspace or main branch:

- `merge`: merge the task branch as-is when preserving branch history is useful.
- `squash_merge`: squash the task branch into one mainline commit when the task has noisy worker commits.
- `cherry_pick`: cherry-pick one or more task commits when only selected commits should enter mainline.
- `integration_commit`: manually apply or combine changes into a new commit when several accepted task branches must be reconciled together.

Record the chosen strategy, resulting commit hash (or `direct_apply` only for single-session work), and post-integration verification in the task's `validation-log.md` integration record. Run the acceptance and integration gates before changing the task status:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase acceptance --task <TASK-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase integration --task <TASK-ID>
```

Use `integration_commit` sparingly. It is for Orchestrator-owned reconciliation after review, not a way for workers to bypass task branches or PR packages.

## Integration Rules

- Workers never integrate their own work.
- Integrations are serial, even when development was parallel.
- Developer status can advance only to `submitted_for_acceptance`.
- Orchestrator alone marks `accepted`, `integrated`, or `complete`.
- Diff review is required before integration.
- Acceptance gate evaluation is required before integration.
- Integration gate evaluation is required before marking a task complete.
- Main-workspace verification is required after each integration.
- Conflicts stop the integration queue.
- Scope drift rejects the integration.
- Failed verification enters repair or blocked state.

## Naming

Use predictable names:

```text
branch: spec2web/TASK-001-short-title
worktree: ../<repo-name>-TASK-001
local_pr: TASK-001/<short-title>
```

Record actual branch, worktree path, handoff status, integration strategy, integration commit, and PR URL when present in `loop-state.md`.
