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
- `stop_reason` is `none` for delivery
- evidence manifests exist under `.webbuilder-artifacts/` for every required verification domain
- host capability evidence is recorded for `required` capabilities in `loop-state.md`
- each manifest passes hash, contract-revision, fingerprint, and redaction verification

Run the bundled checker from the Skill directory:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase delivery
```

## Evidence Manifest Requirements

Each delivery domain (`functional`, `security`, `performance`, `delivery-smoke`, and `ui`/`accessibility` when applicable) requires a `PROJECT / <domain>` entry in `validation-log.md` referencing an `artifact_manifest` path.

The delivery gate verifies each manifest:

- artifact file hashes match the recorded values
- contract revision matches the current approval
- implementation fingerprint matches
- redaction status is `passed`
- result is `passed`

Capture evidence with:

```text
python <skill-root>/scripts/capture-evidence.py --target <project-root> --run-id DELIVERY --subject-id <domain> --attempt 1 --contract-revision <REV> -- <command>
```

## Redaction Policy

All captured evidence is automatically redacted. The redactor strips authorization headers (Bearer tokens, Basic credentials), Cookie headers, and secret-bearing assignment patterns. Use `--explicit-secrets <value>` to redact additional tokens. If redaction fails, the manifest records `redaction.status: failed` and the delivery gate rejects it.

Authorization header values are always redacted regardless of explicit secret lists.

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
