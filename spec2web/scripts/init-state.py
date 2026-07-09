#!/usr/bin/env python3
"""Initialize lightweight Spec2Web state files."""

from __future__ import annotations

import argparse
from pathlib import Path


TEMPLATES = {
    "project-rules.md": """# Project Rules

## Sources Read

- [ ] CLAUDE.md
- [ ] AGENTS.md
- [ ] GEMINI.md
- [ ] README.md

## Active Rules

- Read existing code before writing.
- State assumptions before implementation.
- Keep changes small and focused.
- Verify before claiming completion.
- Avoid new dependencies unless justified.

## Open Rule Conflicts

- None.
""",
    "requirements-baseline.md": """# Requirements Baseline

## Status

status: draft

## Requirements

| ID | Requirement | Priority | Acceptance Signal |
|---|---|---|---|
| REQ-001 | Replace with the first confirmed requirement. | Must | Replace with verification method. |

## Assumptions

- None recorded yet.

## Open Questions

- None recorded yet.
""",
    "system-design.md": """# System Design

## Technology Strategy

### Existing Stack

- frontend: not recorded
- backend: not recorded
- database: not recorded
- styling: not recorded
- testing: not recorded
- build: not recorded
- deployment: not recorded

### Selected Stack

- frontend: not recorded
- backend: not recorded
- database: not recorded
- styling: not recorded
- testing: not recorded
- validation: not recorded
- deployment assumption: not recorded

### Verification Commands

- install: not recorded
- build: not recorded
- test: not recorded
- lint/typecheck: not recorded
- browser/manual: not recorded

## Interface Design Baseline

### Product Shape

- audience: not recorded
- primary jobs: not recorded
- density: not recorded
- visual tone: not recorded

### User Flows

| Flow | Entry | Core Steps | Success State | Requirement IDs |
|---|---|---|---|---|

### Pages

| Page | Purpose | Primary Actions | Key States | Requirement IDs |
|---|---|---|---|---|

### Layout Direction

- navigation: not recorded
- page structure: not recorded
- information hierarchy: not recorded
- desktop constraints: not recorded
- mobile constraints: not recorded

### UI Verification

- browser checks: not recorded
- screenshot or visual checks: not recorded
- responsive checks: not recorded
- accessibility checks: not recorded

## Pages

- None recorded yet.

## Data Model

- None recorded yet.

## API Contract

- None recorded yet.

## Permissions

- None recorded yet.

## Verification Strategy

- Build command: not recorded
- Test command: not recorded
- Browser or manual verification: not recorded
""",
    "task-plan.md": """# Task Plan

## Current Strategy

Default to one task at a time. Use controlled multi-worker mode only for no-conflict tasks.

## Tasks

### TASK-001: Replace with first task title

- requirement_ids: REQ-001
- goal: Replace with one concrete outcome.
- dependencies: none
- status: pending
- handoff_mode: pr_worktree
- integration_strategy: squash_merge
- allowed_paths:
  - replace/with/path
- expected_outputs:
  - replace with expected output
- verification:
  - replace with exact command or manual check
- completion_criteria:
  - replace with worker-observable condition for submitting the task
- acceptance_gate:
  - replace with Orchestrator check required before accepting or merging
- submission_package:
  - branch name and commit hash
  - worktree path
  - implementation summary
  - changed files
  - verification evidence
  - known risks or follow-up
- risks_or_blockers:
  - none
- execution_workspace: main
- parallel_group: none
- integration_policy: orchestrator_review_then_serial_integration
""",
    "loop-state.md": """# Loop State

workflow: spec2web
status: active
current_phase: project_rules
current_task: null
active_parallel_group: null

## Active Constraints

- one task per worker
- continue ready tasks until blocked or delivered
- main session remains Orchestrator
- implementation tasks use PR/worktree handoff when Git is available
- delegated workers submit, Orchestrator accepts
- external AI workers are forbidden
- no unplanned full-project generation
- every task maps to requirements
- update state before moving on
- verify before claiming done
- follow project-rules.md
- Orchestrator controls integration

## Worktrees

| Task | Branch | Path | Status |
|---|---|---|---|

## PR Handoffs

| Task | Mode | Branch | Worktree | Commit | PR URL | Integration Strategy | Integration Commit | Status |
|---|---|---|---|---|---|---|---|---|

## Next Step

Read project rules and update project-rules.md.
""",
    "validation-log.md": """# Validation Log

## Entries

No validation has been recorded yet.
""",
    "delivery-report.md": """# Delivery Report

## Completed

- Nothing delivered yet.

## Validation

- No validation recorded yet.

## Run Instructions

- Not recorded yet.

## Known Risks

- None recorded yet.

## Not Completed

- Work has not started.
""",
}


def initialize(target: Path) -> tuple[list[Path], list[Path]]:
    state_dir = target / "spec2web"
    state_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    skipped: list[Path] = []

    for filename, content in TEMPLATES.items():
        path = state_dir / filename
        if path.exists():
            skipped.append(path)
            continue
        path.write_text(content, encoding="utf-8", newline="\n")
        created.append(path)

    return created, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize Spec2Web state files.")
    parser.add_argument(
        "--target",
        default=".",
        help="Project directory where the spec2web state folder should be created.",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    created, skipped = initialize(target)

    print(f"Spec2Web state directory: {target / 'spec2web'}")
    for path in created:
        print(f"created: {path}")
    for path in skipped:
        print(f"exists:  {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
