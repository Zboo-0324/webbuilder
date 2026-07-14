# System Design

contract-revision: 1
based_on_contract_revision: 1
status: ready

## Technology Strategy

### Existing Stack

- frontend: Django templates with server-rendered HTML
- backend: Python 3.12, Django 5.2 LTS
- database: SQLite (Django default)
- styling: plain CSS with Django static files
- testing: Django TestCase, Python unittest, Playwright for browser tests
- build: pip install from requirements.txt
- deployment assumption: Django's built-in development server

### Options Considered

| Option | Best For | Tradeoffs | Decision |
|---|---|---|---|
| Django 5.2 LTS | Rapid server-rendered development with built-in auth, ORM, and admin. | No SPA interactivity; server round-trips for every action. | selected |
| FastAPI + Jinja2 | Async-first API with template rendering. | Requires separate auth/session library; more boilerplate for forms and CSRF. | rejected |
| Flask + SQLAlchemy | Lightweight micro-framework flexibility. | No built-in auth, admin, or migration tooling; must assemble stack manually. | rejected |

### Selected Stack

- frontend: Django templates with static CSS
- backend: Django 5.2 LTS, Python 3.12
- database: SQLite via Django ORM
- styling: plain CSS in static/app.css
- testing: Django TestCase + unittest, Playwright for browser flows
- validation: Django form validation, axe-core for accessibility, Playwright performance budgets
- deployment assumption: Django development server on localhost

### Dependency Policy

- Reuse Django's built-in auth, ORM, forms, and template engine.
- Add Playwright as a dev/test dependency for browser verification.
- No additional production dependencies required.

### Verification Commands

- install: pip install -r requirements.txt
- build: python manage.py migrate
- test: python manage.py test -v 2
- lint/typecheck: python manage.py check --deploy
- browser/manual: python -m unittest e2e.test_primary_flow -v

## Interface Design Baseline

### Product Shape

- audience: Small internal team (5-10 members) managing operational tasks
- primary jobs: Create work items, view list, mark complete, view responsive layout
- density: Compact operational UI
- visual tone: Clean, minimal, server-rendered

### User Flows

| Flow | Entry | Core Steps | Success State | Requirement IDs |
|---|---|---|---|---|
| Login and view work items | GET /accounts/login/ | Enter credentials, submit, land on work item list | Work item list displayed with status | REQ-001, REQ-002 |
| Create work item | POST /workitems/create/ | Fill title and description, submit | New work item appears in list | REQ-001, REQ-003 |
| Complete work item | POST /workitems/<id>/complete/ | Click complete on a work item | Item marked complete, list updated | REQ-001, REQ-004 |
| Responsive layout verification | Any page | Resize viewport to 320px, 768px, 1280px | Layout adapts without overflow | REQ-005 |

### Pages

| Page | Purpose | Primary Actions | Key States | Requirement IDs |
|---|---|---|---|---|
| Login | Authenticate user | Enter credentials, submit | Empty, invalid, loading | REQ-002 |
| Work Item List | Display all work items | View items, navigate to create, mark complete | Empty list, populated, loading | REQ-001, REQ-003, REQ-004 |
| Work Item Create | Create a new work item | Enter title and description, submit | Empty, validation error, success | REQ-001, REQ-003 |

### Layout Direction

- navigation: Top bar with app title and logout link
- page structure: Single-column centered content area
- information hierarchy: Title first, then action buttons, then content list
- desktop constraints: Max-width container centered on screen
- mobile constraints: Full-width stacked layout with larger touch targets

### Component Conventions

- buttons: Standard HTML button/input type=submit with CSS styling
- forms: Django forms with CSRF tokens, label + input pairs
- tables/lists: Simple HTML tables for work item list
- modals/drawers: None; server-rendered page transitions
- feedback/toasts: Django messages framework for success/error notifications
- icons: None; text-only interface

### State Coverage

- loading: Page-level loading via server response time
- empty: "No work items yet" message when list is empty
- error: Django form validation errors displayed inline
- disabled: Completed items shown with strikethrough and disabled action
- success: Django messages framework success notification after create/complete
- permission denied: Redirect to login for unauthenticated access

### UI Verification

- browser checks: Playwright primary flow test covering login, create, complete, logout
- screenshot or visual checks: Not required for MVP
- responsive checks: Playwright viewport tests at 320px, 768px, 1280px
- accessibility checks: axe-core scan with zero critical violations

## Data Model

- WorkItem: id (auto), title (char 200), description (text), is_complete (bool), created_at (datetime), completed_at (datetime nullable)
- User: Django's built-in auth User model (username, password, email)

## API Contract

- GET /: Redirect to work item list or login
- GET /accounts/login/: Login form (Django auth)
- POST /accounts/logout/: Logout action (Django auth)
- GET /workitems/: Work item list (requires auth)
- POST /workitems/create/: Create work item (requires auth, title + description)
- POST /workitems/<id>/complete/: Mark work item complete (requires auth)

## Permissions

- Authenticated user: Can view, create, and complete work items
- Anonymous user: Can only access login page; all other views redirect to login

## Verification Strategy

- Build command: python manage.py migrate
- Test command: python manage.py test -v 2
- Browser or manual verification: python -m unittest e2e.test_primary_flow -v
