# Delivery Checklist

Before final delivery, verify and record evidence.

## Required Checks

- requirements are mapped to tasks
- all tasks are marked complete by Orchestrator or explicitly listed as not completed
- validation commands have been run
- high- and critical-risk tasks include Tester and Reviewer evidence for their declared adversarial cases
- failures are resolved or documented
- project run instructions are current
- known risks are documented
- credentials are not committed
- local absolute paths are not embedded in deliverables
- every task has `status: complete`
- every task has an accepted `TASK-ID / acceptance` record with independent identity and review evidence
- every task has a `TASK-ID / integration` record with matching strategy and passed main-workspace verification
- `delivery-report.md` has `status: complete`
- `loop-state.md` has `current_phase: delivery` and `status: delivered`
- the delivery-phase state check passes

Run the bundled checker from the Skill directory:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase delivery
```

## Delivery Report Template

````markdown
# Delivery Report

status: complete

## Summary

One paragraph describing what was delivered.

## Completed Features

- Feature mapped to requirement ID.

## Validation Evidence

| Check | Command or Method | Result |
|---|---|---|
| Build | command | passed/failed |
| Tests | command | passed/failed |
| Manual flow | method | passed/failed |

## Run Instructions

```text
exact commands
```

## Known Risks

- Risk and impact.

## Not Completed

- Item and reason.

## Resume Instructions

- Next recommended task or follow-up.
````
