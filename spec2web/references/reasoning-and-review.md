# First-Principles and Adversarial Review

Spec2Web uses four complementary controls to make delivery decisions reliable without turning every small change into a heavyweight ceremony:

1. First-principles analysis establishes the problem facts before solution design.
2. Role-based review assigns explicit evaluation standards and decision rights.
3. Adversarial review looks for credible ways the proposal or implementation can fail.
4. Cross-review keeps the Maker independent from the Checker and resolves disagreement with evidence.

## First-Principles Analysis

Before confirming `requirements-baseline.md`, record the first-principles analysis, then use it to confirm requirements:

- the user or business outcome that must be true when the work succeeds;
- hard constraints and invariants that the solution must not violate;
- assumptions, their evidence, and the consequence if each assumption is false;
- open questions that block a safe design or require user confirmation.

Do not substitute a familiar implementation pattern for this analysis. Existing conventions remain useful evidence, but they are not requirements unless the project rules, user, or verified system facts make them so.

The Requirement Baseline is ready only when the planned work can be traced to the recorded outcome, constraints, and acceptance signals. The System Design then explains how the chosen approach preserves those constraints.

## Role-Based Standards

Use roles as evaluation contracts, not as theatrical personas:

| Role | Primary standard |
|---|---|
| Planner | Requirements are grounded in facts, constraints, assumptions, and acceptance signals. |
| Developer | The task stays inside its contract and preserves established invariants. |
| Tester | Required behavior and meaningful boundary cases have evidence. |
| Reviewer | Scope, maintainability, operational risk, workflow compliance, and evidence are sufficient. |
| Orchestrator | Independent evidence supports acceptance, integration, and downstream unlocking. |

One agent may switch roles only for low-risk single-session work, and the switch plus its limits must be recorded. A Developer never validates its own completion claim.

## Risk Classification

Every task declares `risk_level`, `risk_basis`, `checker_strategy`, and `review_mode`:

- `unclassified`: no evidence supports a risk judgment yet; it may pass structure validation but cannot be dispatched.
- `low`: localized, reversible, low-impact work; `review_mode: standard` is sufficient.
- `standard`: normal feature or maintenance work; use an independent checker for delegated work.
- `high`: security, permissions, migrations, concurrency, external integrations, shared contracts, destructive actions, or material reliability risk; use `review_mode: adversarial` and separate Tester and Reviewer roles.
- `critical`: release-critical or irreversible work, or work with material user, financial, data-loss, safety, or compliance impact; use the same controls as `high` plus explicit user confirmation for any unresolved risk.

Do not infer risk from a file path, task title, or an old review mode. If a migration cannot preserve a documented `risk_basis`, set the task to `unclassified`. Classify conservatively: if the impact of failure is unclear, use `high` only when there is evidence for that classification; otherwise leave the task `unclassified` until the Planner records a basis.

The task contract is the single source of truth for `risk_level`, `risk_basis`, `checker_strategy`, and review requirements. `loop-state.md` records only the derived `active_checker_strategy` for the current task. `validation-log.md` records evidence and decisions; it never upgrades a task contract or task status.

Critical work additionally requires `user_approval: approved`, non-empty approval evidence, rollback plan, recovery point, and residual-risk owner before acceptance.

## Adversarial Review

For `high` and `critical` tasks, define `adversarial_review` cases before dispatch. They must test credible failure paths, not generic statements such as "check edge cases." Choose the relevant cases:

- invalid, boundary, duplicate, or reordered input;
- timeout, retry, partial failure, and unavailable dependency behavior;
- concurrency, stale state, idempotency, rollback, and recovery;
- authorization, data exposure, and privilege-boundary failures;
- backward compatibility, migration, deployment, and observability failures;
- a counterexample that would make the main design assumption false.

The Tester records the observed behavior. The Reviewer records whether the evidence addresses the stated failure paths and whether new risks remain. A failed adversarial case returns the task to repair or blocks it; it cannot be waived silently.

## Cross-Review and Disagreement

For delegated work, the Checker must be independent from the Developer. For `high` and `critical` work, Tester and Reviewer are separate and read-only.

When review conclusions differ, the Orchestrator records:

- the shared findings;
- the disagreement and the evidence each conclusion relies on;
- the decision, owner, and remaining risk.

Do not decide by majority vote or by the confidence of a role. Resolve the disagreement against requirements, code, tests, runtime evidence, and project rules.
