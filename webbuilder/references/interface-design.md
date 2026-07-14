# Interface Design

Interface design is part of System Design for user-facing web projects. It does not need to become a full design system, but frontend tasks must not start from vague page names.

Keep `system-design.md` at `status: draft` until the required interface baseline is concrete enough to verify. Use `not applicable` for genuinely irrelevant fields instead of leaving `not recorded` placeholders.

## Required Baseline

Write this section into `webbuilder/system-design.md` before frontend task breakdown:

```markdown
## Interface Design Baseline

### Product Shape

- audience:
- primary jobs:
- density: compact, balanced, or spacious
- visual tone:

### User Flows

| Flow | Entry | Core Steps | Success State | Requirement IDs |
|---|---|---|---|---|
| Flow name | Where it starts. | Main path. | What success looks like. | REQ-000 |

### Pages

| Page | Purpose | Primary Actions | Key States | Requirement IDs |
|---|---|---|---|---|
| Page name | Why it exists. | Actions. | loading, empty, error, success | REQ-000 |

### Layout Direction

- navigation:
- page structure:
- information hierarchy:
- desktop constraints:
- mobile constraints:

### Component Conventions

- buttons:
- forms:
- tables/lists:
- modals/drawers:
- feedback/toasts:
- icons:

### State Coverage

- loading:
- empty:
- error:
- disabled:
- success:
- permission denied:

### UI Verification

- browser checks:
- screenshot or visual checks:
- responsive checks:
- accessibility checks:
```

## Design Rules

- Match the project domain and audience.
- Prefer usable workflow screens over landing pages unless the user explicitly asks for a landing page.
- Define states that tests or manual verification can observe.
- Record major visual assumptions before implementation.
- If a design choice changes scope or brand direction, ask the user before building.
- Interface decisions that change `ui_direction`, `page_navigation_summary`, or `primary_workflows` in the contract material are material changes and invalidate contract approval.

## Host Capability for UI

When the contract marks `ui` as `required`, verify the host can render and test browser-based UI before dispatching frontend tasks:

```text
python <skill-root>/scripts/check-host.py --target <project-root>
python <skill-root>/scripts/check-state.py --target <project-root> --phase host
python <skill-root>/scripts/check-state.py --target <project-root> --phase initialization
python <skill-root>/scripts/check-state.py --target <project-root> --phase ui
```

- `check-host.py --target <project-root>` inspects and records the host capability report.
- `--phase host` checks that all required capabilities have available evidence.
- `--phase initialization` checks required capabilities have evidence while allowing `not_applicable` capabilities to skip.
- `--phase ui` checks that UI-specific evidence manifests exist when the contract requires a UI.

Record browser and rendering capability in `loop-state.md` under `## Host Capabilities`.

## Task Breakdown Impact

Create frontend tasks as vertical slices around user flows when possible. Each frontend task should include:

- page or flow name
- requirement IDs
- component and state coverage
- responsive expectations
- browser or visual verification method
