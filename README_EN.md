# Spec2Web

<div align="center">

**An adaptive multi-agent workflow Skill for full-stack web delivery**

Requirements baseline · Technology strategy · Interface design · Task breakdown · Loop Engineering · PR/worktree handoff · Validation

![skill](https://img.shields.io/badge/skill-spec2web-blue)
![install](https://img.shields.io/badge/install-Codex%20%7C%20Claude%20Code%20%7C%20Hermes-black)
![language](https://img.shields.io/badge/language-%E4%B8%AD%E6%96%87%20%7C%20English-blue)

[中文](./README.md) | English

</div>

Spec2Web is a lightweight Skill for guiding AI coding agents through full-stack web project delivery.

It is intentionally not a runtime, code generator, MCP server, background scheduler, or framework template. Instead, Spec2Web gives an agent a stateful workflow for moving from requirements to implementation, validation, repair, and delivery while keeping scope, quality, and project memory explicit.

## What It Does

Spec2Web helps an agent:

- read project rules before implementation
- establish a requirements baseline
- record the core outcome, hard constraints, assumptions with evidence, and blocking questions through first-principles analysis
- recommend and record a technology strategy
- define an interface design baseline before frontend work
- produce a system design
- break work into bounded tasks
- choose single, delegated, or parallel execution from current host capacity and task risk
- execute tasks through PR/worktree handoff: Orchestrator delegates, subagents develop and submit, Orchestrator reviews, tests, accepts, and integrates
- escalate review by task risk: high-risk work requires adversarial review and separate Tester and Reviewer cross-checks
- default to task branches and worktrees for implementation tasks in Git projects
- continue ready tasks until blocked or delivered
- record validation evidence and delivery notes

## What It Does Not Do

Spec2Web does not:

- generate an application from a prompt
- provide a full-stack code template
- run as a background service
- schedule workers automatically
- call Claude or external AI services as workers
- provide an MCP server or global CLI
- deploy applications
- replace user confirmation for high-impact decisions

## Repository Layout

```text
spec2web/
  SKILL.md
  agents/
    openai.yaml
  references/
    delivery-checklist.md
    install.md
    interface-design.md
    loop-engineering.md
    multi-agent-orchestration.md
    reasoning-and-review.md
    role-protocol.md
    state-files.md
    task-breakdown.md
    technology-strategy.md
    worktree-mode.md
  scripts/
    init-state.py
    check-state.py
    migrate-state.py
```

## Install

Install the whole `spec2web/` folder, not only `SKILL.md`.

### Codex

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\spec2web").Path
$dst = "$env:USERPROFILE\.codex\skills\spec2web"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

Restart Codex after installation.

### Claude Code

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\spec2web").Path
$dst = "$env:USERPROFILE\.claude\skills\spec2web"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

Restart Claude Code after installation.

### Hermes

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\spec2web").Path
$dst = "$env:USERPROFILE\.hermes\skills\spec2web"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

Restart Hermes after installation.

## Usage

Use Spec2Web explicitly when you want the workflow active:

```text
/spec2web initialize this project
/spec2web enable workflow
/spec2web start from requirements.md
/spec2web continue current task
/spec2web show status
/spec2web generate delivery report
```

Natural-language equivalents also work:

```text
use Spec2Web for this project
start Spec2Web mode
resume Spec2Web
```

Spec2Web should not take over ordinary coding tasks unless it has been explicitly requested or the project has an active `spec2web/loop-state.md`.

## Project State

When initialized inside a project, Spec2Web creates:

```text
spec2web/
  project-rules.md
  requirements-baseline.md
  system-design.md
  task-plan.md
  loop-state.md
  validation-log.md
  delivery-report.md
```

These files are the source of truth. Conversation context does not replace them.

## State Scripts

Initialize state files:

```powershell
python spec2web/scripts/init-state.py --target .
```

Migrate existing state:

```powershell
python spec2web/scripts/migrate-state.py --target . --dry-run
python spec2web/scripts/migrate-state.py --target .
```

Migration first creates a timestamped backup under the project's `spec2web/` state folder. Remove it after validation or keep it local; do not commit migration backups.

Check the state structure:

```powershell
python spec2web/scripts/check-state.py --target . --phase structure
```

Before application-code tasks, run the execution gate:

```powershell
python spec2web/scripts/check-state.py --target . --phase execution
```

Before final delivery, run the delivery gate:

```powershell
python spec2web/scripts/check-state.py --target . --phase delivery
```

The checker has seven validation phases:

- `structure`: schema, required files, agent-orchestration metadata, design sections, task contracts, and valid status values
- `execution`: confirmed requirements, ready project/design/task baselines, no placeholders, and an active workflow
- `task`: selected task, dependency, task-owned checker strategy, execution-mode, handoff, workspace, and current-task readiness
- `parallel`: host capacity, group size, unique worktrees, path and declared semantic conflicts, and per-task checker strategies
- `acceptance`: per-task submission package, independent identities, adversarial cases, disagreements, and critical controls
- `integration`: accepted task, matching integration strategy and commit, and main-workspace verification evidence
- `delivery`: acceptance and integration evidence closure for every completed task, a complete delivery report, and terminal workflow state

The initializer does not overwrite older state files. After migrating V1, V1.0, V1.1, or V1.2 state to schema 1.3, tasks without a documented risk basis become `unclassified` and must be explicitly classified before dispatch.

## Workflow

The top-level workflow is:

```text
Project Rules
-> First-Principles Analysis
-> Requirement Baseline
-> Technology Strategy
-> Interface Design Baseline
-> System Design
-> Task Breakdown
-> Task Execution Loop
-> Integration Validation
-> Delivery
```

Each task loop is:

```text
Read State
-> Select Next Task or Parallel Batch
-> Select single, delegated, or parallel Execution Mode
-> Create Task Branch and Worktree when Git is available
-> Delegate Worker with Task Contract
-> Worker Commits to Task Branch
-> PR Handoff Submission
-> Test and Review
-> Acceptance Gate
-> Formal Integration Point
-> Integration Gate and Main-Workspace Verification
-> Repair or Record
-> Update State
```

After one task completes, the Orchestrator continues to the next ready task when `loop-state.md` is active and no stop condition applies.

Application code starts only after `project-rules.md`, `system-design.md`, and `task-plan.md` are `ready`, `requirements-baseline.md` is `confirmed`, and the execution gate passes. Final delivery requires all tasks `complete`, `delivery-report.md` `complete`, `loop-state.md` set to `current_phase: delivery` and `status: delivered`, and the delivery gate passing.

## PR/Worktree Mode

Spec2Web uses PR/worktree handoff for delegated or parallel tasks in Git projects:

- default: one task at a time
- controlled multi-worker mode: only for no-conflict task batches
- worker count: no more than both ready tasks and host-reported free child-agent slots
- the Orchestrator creates the task branch and worktree
- subagent workers develop only in their assigned worktree and commit to the task branch
- workers submit a local PR package or remote PR, then stop
- the Orchestrator integrates serially through `merge`, `squash_merge`, `cherry_pick`, or `integration_commit`
- verification runs in the main workspace after each integration

Spec2Web does not provide an automatic worker pool or unattended integration scheduler.

Spec2Web permits agents exposed by the current Codex host, including host-authorized local or Codex cloud execution. It does not call third-party AI services or external agent products without explicit user authorization.

For non-Git projects or explicit single-session fallback, use `handoff_mode: single_session` with `integration_strategy: direct_apply`. This records that accepted changes already exist in the main workspace and require Orchestrator verification without inventing a merge or commit.

## Validation

Run a state script smoke check:

```powershell
$tmp = Join-Path $env:TEMP "spec2web-smoke"
Remove-Item -Recurse -Force -LiteralPath $tmp -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
python spec2web/scripts/init-state.py --target $tmp
python spec2web/scripts/check-state.py --target $tmp --phase structure
```

Validate the Skill package:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" spec2web
```

## Design Principles

- Keep the workflow lightweight.
- Use explicit state files as project memory.
- Split large work into bounded tasks.
- Require verification before completion claims.
- Separate maker and checker roles.
- Use role responsibilities and evaluation standards, not persona imitation.
- Require adversarial review and separate Tester/Reviewer roles only for high-risk or critical work.
- Prefer existing project conventions.
- Ask the user before changing confirmed requirements, adding high-risk dependencies, using credentials, or consuming paid resources.
