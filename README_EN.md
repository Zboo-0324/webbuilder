# WebBuilder

<div align="center">

**An adaptive multi-agent workflow Skill for full-stack web delivery**

Requirements baseline · Technology strategy · Interface design · Task breakdown · Loop Engineering · PR/worktree handoff · Validation

![skill](https://img.shields.io/badge/skill-webbuilder-blue)
![install](https://img.shields.io/badge/install-Codex%20%7C%20Claude%20Code%20%7C%20Hermes-black)
![language](https://img.shields.io/badge/language-%E4%B8%AD%E6%96%87%20%7C%20English-blue)

[中文](./README.md) | English

</div>

WebBuilder is a lightweight Skill for guiding AI coding agents through full-stack web project delivery.

It is intentionally not a runtime, code generator, MCP server, background scheduler, or framework template. Instead, WebBuilder gives an agent a stateful workflow for moving from requirements to implementation, validation, repair, and delivery while keeping scope, quality, and project memory explicit.

## What It Does

WebBuilder helps an agent:

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

WebBuilder does not:

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
webbuilder/
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
    check-host.py
    capture-evidence.py
    migrate-state.py
    transition-state.py
    approve-contract.py
    contract_core.py
```

## Install

Install the whole `webbuilder/` folder, not only `SKILL.md`.

### Codex

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\webbuilder").Path
$dst = "$env:USERPROFILE\.codex\skills\webbuilder"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

Restart Codex after installation.

### Claude Code

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\webbuilder").Path
$dst = "$env:USERPROFILE\.claude\skills\webbuilder"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

Restart Claude Code after installation.

### Hermes

```powershell
git clone https://github.com/Zboo-0324/spec2web.git
Set-Location spec2web

$src = (Resolve-Path ".\webbuilder").Path
$dst = "$env:USERPROFILE\.hermes\skills\webbuilder"

New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
robocopy $src $dst /MIR
```

Restart Hermes after installation.

## Usage

Use WebBuilder explicitly when you want the workflow active:

```text
/webbuilder initialize this project
/webbuilder enable workflow
/webbuilder start from requirements.md
/webbuilder start autonomous from requirements.md
/webbuilder continue current task
/webbuilder show status
/webbuilder generate delivery report
```

Autonomous mode requires explicit opt-in; guided mode is the default for all new and existing projects.

Natural-language equivalents also work:

```text
use WebBuilder for this project
start WebBuilder mode
resume WebBuilder
```

WebBuilder should not take over ordinary coding tasks unless it has been explicitly requested or the project has an active `webbuilder/loop-state.md`.

## Project State

When initialized inside a project, WebBuilder creates:

```text
webbuilder/
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
python webbuilder/scripts/init-state.py --target .
```

Migrate existing state:

```powershell
python webbuilder/scripts/migrate-state.py --target . --dry-run
python webbuilder/scripts/migrate-state.py --target .
```

Migration first creates a timestamped backup under the project's `webbuilder/` state folder. Remove it after validation or keep it local; do not commit migration backups.

Check the state structure:

```powershell
python webbuilder/scripts/check-state.py --target . --phase structure
```

Before application-code tasks, run the execution gate:

```powershell
python webbuilder/scripts/check-state.py --target . --phase execution
```

Contract readiness and approval (`--phase specification` validates contract material, `approve-contract.py` applies approval):

```powershell
python webbuilder/scripts/check-state.py --target . --phase specification
python webbuilder/scripts/approve-contract.py --target . --approval-evidence user-message-42
```

Before every resume, recover any interrupted State Kernel transition and re-check structure:

```powershell
python webbuilder/scripts/transition-state.py --target . --recover
python webbuilder/scripts/check-state.py --target . --phase structure
```

Capture verification evidence:

```powershell
python webbuilder/scripts/capture-evidence.py --target . --run RUN-1 --subject TASK-001 --attempt 1 --contract-revision 1 -- python -m unittest
```

Evidence is stored under `.webbuilder-artifacts/<run-id>/<subject-id>/<attempt>/` with manifest.json and command output. All evidence is automatically redacted for authorization headers, cookies, and explicit secrets.

Check host capabilities:

```powershell
python webbuilder/scripts/check-host.py --target . --phase host
python webbuilder/scripts/check-host.py --target . --phase initialization
python webbuilder/scripts/check-host.py --target . --phase ui
```

Before final delivery, run the delivery gate:

```powershell
python webbuilder/scripts/check-state.py --target . --phase delivery
```

The delivery gate verifies that valid evidence manifests exist under `.webbuilder-artifacts/` for every required verification domain.

The checker has eleven validation phases:

- `structure`: schema, required files, agent-orchestration metadata, design sections, task contracts, and valid status values
- `specification`: complete contract material with no `not recorded` values, non-empty acceptance signals and primary workflows, and derived documents referencing the current contract revision
- `execution`: confirmed requirements, ready project/design/task baselines, no placeholders, and an active workflow
- `task`: selected task, dependency, task-owned checker strategy, execution-mode, handoff, workspace, and current-task readiness
- `parallel`: host capacity, group size, unique worktrees, path and declared semantic conflicts, and per-task checker strategies
- `acceptance`: per-task submission package, independent identities, adversarial cases, disagreements, and critical controls
- `integration`: accepted task, matching integration strategy and commit, and main-workspace verification evidence
- `delivery`: acceptance and integration evidence closure for every completed task, a complete delivery report, and terminal workflow state
- `host`: validates required host capabilities are available with evidence
- `initialization`: validates host capabilities satisfy the approved contract; not_applicable capabilities may lack evidence
- `ui`: validates UI evidence manifests exist when the contract declares UI as required

The initializer does not overwrite older state files. Schema 1.4 adds guided delivery and recovery metadata (`delivery_mode`, `autonomy_scope`, `stop_reason`, `resume_checkpoint`, `active_run_id`, `state_revision`, and `pending_transition`). Migration preserves content and brings V1 through V1.3 state forward; tasks without a documented risk basis become `unclassified` and must be explicitly classified before dispatch.

`loop-state.md` is the canonical State Kernel record. Agents may edit descriptive content and submit evidence, but must not manually set approval, readiness, acceptance, integration, stop/resume, or delivery-success values. State-changing operations use a transaction journal under `webbuilder/.transitions/`; recovery completes only a non-divergent pending transition.

## Workflow

The top-level workflow is:

```text
Project Rules
-> User Discovery Gate
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

WebBuilder first reads the user's one-line brief or existing requirements document and forms an AI-authored product hypothesis. It asks one genuinely consequential question at a time, preferably with 2-3 concrete choices and a recommendation, rather than asking the user to write the core requirements or complete an expert questionnaire. The user then confirms the AI-synthesized requirements and design; `discovery_status` remains `pending` until approval.

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

WebBuilder uses PR/worktree handoff for delegated or parallel tasks in Git projects:

- default: one task at a time
- controlled multi-worker mode: only for no-conflict task batches
- worker count: no more than both ready tasks and host-reported free child-agent slots
- the Orchestrator creates the task branch and worktree
- subagent workers develop only in their assigned worktree and commit to the task branch
- workers submit a local PR package or remote PR, then stop
- the Orchestrator integrates serially through `merge`, `squash_merge`, `cherry_pick`, or `integration_commit`
- verification runs in the main workspace after each integration
- accepted evidence is copied to canonical state and `validation-log.md` before its worktree is cleaned up

WebBuilder does not provide an automatic worker pool or unattended integration scheduler.

WebBuilder permits agents exposed by the current Codex host, including host-authorized local or Codex cloud execution. It does not call third-party AI services or external agent products without explicit user authorization.

For non-Git projects or explicit single-session fallback, use `handoff_mode: single_session` with `integration_strategy: direct_apply`. This records that accepted changes already exist in the main workspace and require Orchestrator verification without inventing a merge or commit.

## Validation

Run a state script smoke check:

```powershell
$tmp = Join-Path $env:TEMP "spec2web-smoke"
Remove-Item -Recurse -Force -LiteralPath $tmp -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
python webbuilder/scripts/init-state.py --target $tmp
python webbuilder/scripts/check-state.py --target $tmp --phase structure
```

Validate the Skill package:

```powershell
python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" webbuilder
```

## Golden Technology Profiles

WebBuilder maintains validated technology stack profiles for recommendation and project bootstrapping:

```text
webbuilder/references/technology-profiles/django-5.2-lts.md
```

The Django 5.2 LTS Golden Profile includes verified Python/Django/Playwright version combinations and startup instructions.

- Keep the workflow lightweight.
- Use explicit state files as project memory.
- Split large work into bounded tasks.
- Require verification before completion claims.
- Separate maker and checker roles.
- Use role responsibilities and evaluation standards, not persona imitation.
- Require adversarial review and separate Tester/Reviewer roles only for high-risk or critical work.
- Prefer existing project conventions.
- Ask the user before changing confirmed requirements, adding high-risk dependencies, using credentials, or consuming paid resources.
