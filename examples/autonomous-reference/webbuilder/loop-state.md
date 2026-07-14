# Loop State

workflow: spec2web
schema_version: 1.4
status: delivered
current_phase: delivery
delivery_mode: guided
autonomy_scope: confirmed_plan
stop_reason: none
resume_checkpoint: none
active_run_id: null
state_revision: 8
pending_transition: null
execution_mode: single
host_agent_capability: available
available_child_slots: unknown
selected_workers: 0
active_checker_strategy: single_session

## Active Constraints

- one task per worker
- continue ready tasks until blocked or delivered
- main session remains Orchestrator
- delegated or parallel tasks use PR/worktree handoff when Git is available
- delegated workers submit, Orchestrator accepts
- unauthorized external AI workers are forbidden
- no unplanned full-project generation
- every task maps to requirements
- update state before moving on
- verify before claiming done
- follow project-rules.md
- Orchestrator controls integration

## Host Capabilities

```json
{"browser": {"status": "available", "evidence": "playwright"}, "subagents": {"status": "unavailable", "evidence": "test-single-mode"}}
```

## Worktrees

| Task | Branch | Path | Status |
|---|---|---|---|

## PR Handoffs

| Task | Mode | Branch | Worktree | Commit | PR URL | Integration Strategy | Integration Commit | Status |
|---|---|---|---|---|---|---|---|---|

## Next Step

Delivery complete. All tasks executed, accepted, integrated, and evidence captured.
