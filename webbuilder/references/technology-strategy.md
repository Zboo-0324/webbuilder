# Technology Strategy

Technology strategy is part of System Design. It must be decided before task breakdown because it affects dependencies, file boundaries, verification commands, deployment, and future worktree integration risk.

## Decision Rule

For existing projects:

- inspect package files, framework files, build configuration, and current conventions
- prefer the existing stack
- recommend a change only when the current stack blocks requirements or creates clear delivery risk

For new projects:

- propose 2-3 viable stacks
- recommend one default
- explain tradeoffs in delivery speed, maintainability, testing, deployment, data model, and UI needs
- ask the user to confirm when the choice is high impact or ambiguous

Do not add dependencies just because they are popular. Every dependency needs a requirement or a clear implementation benefit.

Keep `system-design.md` at `status: draft` while stack choices or verification commands are unresolved. Set it to `ready` only after the technology and interface baselines support task execution.

## Required Output

Write this section into `webbuilder/system-design.md`:

```markdown
## Technology Strategy

### Existing Stack

- frontend:
- backend:
- database:
- styling:
- testing:
- build:
- deployment:

### Options Considered

| Option | Best For | Tradeoffs | Decision |
|---|---|---|---|
| Option A | Context where it fits. | Main downside. | selected/rejected |

### Selected Stack

- frontend:
- backend:
- database:
- styling:
- testing:
- validation:
- deployment assumption:

### Dependency Policy

- Reuse existing dependencies first.
- Add new dependencies only with justification.
- Record install commands and lockfile impact.

### Verification Commands

- install:
- build:
- test:
- lint/typecheck:
- browser/manual:
```

## Stop Conditions

Stop and ask the user when:

- stack choice changes deployment cost or hosting model
- a new paid service is required
- credentials or production resources are required
- requirements conflict with the existing stack
- the best option depends on business constraints the user has not stated
- the technology choice would invalidate approved contract material

The solution contract does not authorize credentials, paid resources, production deployment, destructive external writes, irreversible migration, high-risk install scripts, or secret transmission. If a technology decision requires any of these, stop and ask before proceeding.
