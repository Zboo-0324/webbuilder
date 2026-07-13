# WebBuilder Autonomous End-to-End Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the complete autonomous workflow with one maintained full-stack reference profile, stop/resume and evidence-tamper scenarios, host-degradation evaluations, and an explicit opt-in release gate.

**Architecture:** Add a small Django 5.2 LTS/SQLite reference application with one authenticated task-management vertical slice and server-rendered responsive UI. Drive the real WebBuilder CLIs from initialization through contract approval, execution, forced stop, resume, evidence promotion, and delivery; keep the example isolated from the standard-library WebBuilder runtime.

**Tech Stack:** Python 3.12-3.14; Django 5.2.16 LTS; SQLite; Django templates; vanilla CSS/JavaScript; Playwright Python 1.61.0 with `unittest`; GitHub Actions.

## Global Constraints

- Plans 1-3 exit gates must be complete and green.
- WebBuilder runtime tooling remains Python-standard-library only; Django and Playwright are confined to `examples/autonomous-reference/requirements.txt`.
- Pin the maintained profile to Django 5.2.16 and Playwright 1.61.0 for reproducible evidence; profile documentation records compatibility range `Django >=5.2,<5.3` and the last validated pins.
- Use SQLite, synthetic seed data, and local-only development resources; no credentials, paid service, remote deployment, or external write is required.
- Docker is `not_applicable` for this profile with reason `reference delivery uses a local Python process`; security and performance remain required at baseline.
- The example must include authentication, database migration/seed, UI/API-equivalent form behavior, permission denial, responsive layout, keyboard/focus behavior, clean startup, and evidence capture.
- Autonomous mode remains explicit opt-in after all final tests pass; guided remains default for migrated/existing projects.
- Do not add specialized domain references until general-path behavior evaluations prove progressive loading.

---

### Task 1: Define and Validate the First Golden Technology Profile

**Files:**
- Create: `webbuilder/references/technology-profiles/django-5.2-lts.md`
- Modify: `webbuilder/references/technology-strategy.md`
- Create: `tests/test_webbuilder_technology_profiles.py`

**Interfaces:**
- Consumes: approved `technology_profile` field from Plan 2.
- Produces: one versioned profile with selection, applicability defaults, commands, compatibility, upgrade, and deprecation policy.

- [ ] **Step 1: Write the profile contract test**

Create `tests/test_webbuilder_technology_profiles.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "webbuilder" / "references" / "technology-profiles" / "django-5.2-lts.md"


class TechnologyProfileTests(unittest.TestCase):
    def test_django_profile_has_required_maintenance_contract(self) -> None:
        text = PROFILE.read_text(encoding="utf-8")
        for marker in (
            "profile_id: django-5.2-lts",
            "profile_version: 1.0",
            "compatibility: Django >=5.2,<5.3",
            "validated_django: 5.2.16",
            "validated_playwright: 1.61.0",
            "supported_python: 3.12 | 3.13 | 3.14",
            "last_validated: 2026-07-12",
            "## Selection Criteria",
            "## Capability Defaults",
            "## Verification Commands",
            "## Upgrade Policy",
            "## Deprecation Policy",
        ):
            self.assertIn(marker, text)
```

- [ ] **Step 2: Run the test and observe the missing profile**

```powershell
python -m unittest tests.test_webbuilder_technology_profiles -v
```

Expected: `FileNotFoundError`.

- [ ] **Step 3: Create the profile**

The profile front matter is:

```yaml
profile_id: django-5.2-lts
profile_version: 1.0
compatibility: Django >=5.2,<5.3
validated_django: 5.2.16
validated_playwright: 1.61.0
supported_python: 3.12 | 3.13 | 3.14
last_validated: 2026-07-12
maintainer: WebBuilder project
```

Selection criteria: data-backed operational apps, server-rendered workflows, built-in auth/admin/ORM/migrations, and teams accepting Python. Reject it for a static-only site, browser-only SPA requirement, non-Python existing stack, or mandatory edge runtime.

Capability defaults:

```yaml
ui: required
database: required
authentication: required
rbac: not_applicable
audit: not_applicable
docker: not_applicable
accessibility: required
performance: baseline
security: baseline
```

Verification commands:

```text
python -m pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py seed_reference
python manage.py check --deploy
python manage.py test
python manage.py runserver 127.0.0.1:8000
python -m unittest e2e.test_primary_flow -v
```

State that dependency pins are refreshed only through a PR that reruns the maintained example; a profile becomes deprecated when its supported Django line is outside security support or the example cannot pass supported-host CI.

- [ ] **Step 4: Cite the maintenance basis and verify**

Link the profile to [Django 5.2 release notes](https://docs.djangoproject.com/en/5.2/releases/5.2/) and [Playwright Python installation](https://playwright.dev/python/docs/intro). Run:

```powershell
python -m unittest tests.test_webbuilder_technology_profiles -v
git add webbuilder/references/technology-profiles/django-5.2-lts.md webbuilder/references/technology-strategy.md tests/test_webbuilder_technology_profiles.py
git commit -m "docs: add validated Django golden profile"
```

---

### Task 2: Build the Maintained Full-Stack Vertical Slice

**Files:**
- Create: `examples/autonomous-reference/requirements.txt`
- Create: `examples/autonomous-reference/manage.py`
- Create: `examples/autonomous-reference/config/__init__.py`
- Create: `examples/autonomous-reference/config/settings.py`
- Create: `examples/autonomous-reference/config/urls.py`
- Create: `examples/autonomous-reference/config/wsgi.py`
- Create: `examples/autonomous-reference/workitems/__init__.py`
- Create: `examples/autonomous-reference/workitems/apps.py`
- Create: `examples/autonomous-reference/workitems/models.py`
- Create: `examples/autonomous-reference/workitems/forms.py`
- Create: `examples/autonomous-reference/workitems/views.py`
- Create: `examples/autonomous-reference/workitems/urls.py`
- Create: `examples/autonomous-reference/workitems/tests.py`
- Create: `examples/autonomous-reference/workitems/migrations/__init__.py`
- Create: `examples/autonomous-reference/workitems/migrations/0001_initial.py`
- Create: `examples/autonomous-reference/workitems/management/__init__.py`
- Create: `examples/autonomous-reference/workitems/management/commands/__init__.py`
- Create: `examples/autonomous-reference/workitems/management/commands/seed_reference.py`
- Create: `examples/autonomous-reference/templates/registration/login.html`
- Create: `examples/autonomous-reference/templates/workitems/list.html`
- Create: `examples/autonomous-reference/static/app.css`

**Interfaces:**
- Consumes: Django profile.
- Produces: authenticated list/create/complete flow with migration and deterministic seed data.

- [ ] **Step 1: Create isolated dependency pins**

`requirements.txt` contains:

```text
Django==5.2.16
playwright==1.61.0
```

Create and activate a project-local virtual environment during implementation; do not install these packages into WebBuilder's runtime requirements.

- [ ] **Step 2: Write failing Django behavior tests first**

`workitems/tests.py`:

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import WorkItem


class WorkItemFlowTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user("reviewer", password="review-pass")

    def test_anonymous_user_is_redirected_to_login(self) -> None:
        response = self.client.get(reverse("workitems:list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('workitems:list')}")

    def test_authenticated_user_can_create_and_complete_an_item(self) -> None:
        self.client.force_login(self.user)
        created = self.client.post(reverse("workitems:list"), {"title": "Review case 42"})
        item = WorkItem.objects.get()
        self.assertRedirects(created, reverse("workitems:list"))
        completed = self.client.post(reverse("workitems:complete", args=[item.pk]))
        self.assertRedirects(completed, reverse("workitems:list"))
        item.refresh_from_db()
        self.assertTrue(item.completed)

    def test_empty_title_is_visible_validation_error(self) -> None:
        self.client.force_login(self.user)
        response = self.client.post(reverse("workitems:list"), {"title": ""})
        self.assertContains(response, "Title is required", status_code=400)
```

- [ ] **Step 3: Run tests and observe missing application code**

```powershell
Set-Location examples/autonomous-reference
python -m pip install -r requirements.txt
python manage.py test workitems -v 2
```

Expected: import/configuration failure because the model and Django project are not implemented.

- [ ] **Step 4: Implement the minimal model, form, and views**

Model:

```python
class WorkItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("completed", "-created_at")
```

Form:

```python
class WorkItemForm(forms.ModelForm):
    class Meta:
        model = WorkItem
        fields = ("title",)

    def clean_title(self) -> str:
        value = self.cleaned_data.get("title", "").strip()
        if not value:
            raise forms.ValidationError("Title is required")
        return value
```

Views use `@login_required`, handle GET/POST in `item_list`, return status 400 for invalid form, and accept POST only in `complete_item`. Include CSRF tokens in both forms.

- [ ] **Step 5: Add deterministic seed and clean-state commands**

`seed_reference` uses `get_or_create()` for user `reviewer` and work item `Review the autonomous delivery evidence`; repeated runs do not duplicate records. The test environment sets the password to `review-pass` only for synthetic local data.

- [ ] **Step 6: Implement responsive accessible templates**

The page has one `<main>`, one `<h1>`, an explicit `<label for="id_title">`, visible validation text linked with `aria-describedby`, native buttons, a status text for completed items, visible `:focus-visible` styles, and a mobile layout at 390 CSS pixels. Do not add a JavaScript framework.

- [ ] **Step 7: Verify and commit**

```powershell
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py seed_reference
python manage.py check --deploy
python manage.py test -v 2
git add examples/autonomous-reference
git commit -m "feat: add autonomous delivery reference application"
```

Expected: migration is current, seed is repeatable, Django checks run, and all Django tests pass. Record expected `check --deploy` security warnings for local-only settings in the profile rather than suppressing them.

---

### Task 3: Add Browser, Accessibility, Performance, and Startup Evidence

**Files:**
- Create: `examples/autonomous-reference/e2e/test_primary_flow.py`
- Create: `examples/autonomous-reference/e2e/__init__.py`
- Create: `examples/autonomous-reference/e2e/accessibility.py`
- Create: `examples/autonomous-reference/e2e/server.py`
- Modify: `.github/workflows/test.yml`
- Modify: `tests/test_webbuilder_autonomous_e2e.py`

**Interfaces:**
- Consumes: reference app and Plan 3 evidence capture.
- Produces: browser evidence for 390/768/1440 viewports, keyboard/focus, console/network, accessibility baseline, and startup smoke.

- [ ] **Step 1: Write the browser scenario**

`test_primary_flow.py` uses `unittest` and `playwright.sync_api.sync_playwright`. Its test:

```python
def test_login_create_complete_and_responsive_layout(self) -> None:
    console_errors: list[str] = []
    failed_requests: list[str] = []
    self.page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    self.page.on("requestfailed", lambda request: failed_requests.append(request.url))
    self.page.goto(self.live_url + "/accounts/login/")
    self.page.get_by_label("Username").fill("reviewer")
    self.page.get_by_label("Password").fill("review-pass")
    self.page.get_by_role("button", name="Sign in").click()
    self.page.get_by_label("Title").fill("Browser-created item")
    self.page.get_by_role("button", name="Add item").click()
    self.page.get_by_role("button", name="Complete Browser-created item").click()
    self.assertIn("Completed", self.page.get_by_text("Browser-created item").locator("..").inner_text())
    self.page.keyboard.press("Tab")
    self.assertTrue(self.page.evaluate("document.activeElement !== document.body"))
    self.assertEqual(console_errors, [])
    self.assertEqual(failed_requests, [])
```

Run the same primary assertions at widths 390, 768, and 1440 without multiplying every application state across every viewport.

- [ ] **Step 2: Add deterministic baseline accessibility checks**

`accessibility.py` evaluates and returns failures for missing document language, missing main/h1, images without alt, controls without accessible names, inputs without associated labels, heading-level skips, duplicate IDs, and focusable elements hidden by CSS. The browser test asserts `baseline_accessibility_failures(page) == []` after login and after validation error rendering.

Expose the evidence-specific test methods used by the lifecycle runner:

```python
def test_accessibility_states(self) -> None:
    self.login()
    self.assertEqual(baseline_accessibility_failures(self.page), [])
    self.page.get_by_role("button", name="Add item").click()
    self.assertTrue(self.page.get_by_text("Title is required").is_visible())
    self.assertEqual(baseline_accessibility_failures(self.page), [])

def test_warm_primary_flow_under_budget(self) -> None:
    self.login()
    self.page.goto(self.live_url + "/", wait_until="networkidle")
    started = time.perf_counter()
    self.page.reload(wait_until="networkidle")
    elapsed_ms = (time.perf_counter() - started) * 1000
    self.assertLess(elapsed_ms, 2000, f"warm primary flow took {elapsed_ms:.1f} ms")
```

- [ ] **Step 3: Add startup and baseline performance assertions**

`server.py` starts `manage.py runserver 127.0.0.1:<free-port> --noreload`, waits up to 20 seconds for `/accounts/login/`, and always terminates the process. Browser navigation to the authenticated list must complete in under 2,000 ms on the local CI runner after a warm-up request; record the measured value in the evidence manifest rather than treating a single Lighthouse score as universal truth.

- [ ] **Step 4: Run browser tests through Evidence Kernel**

```powershell
python -m playwright install chromium
python webbuilder/scripts/capture-evidence.py --target examples/autonomous-reference --run RUN-E2E --subject PROJECT --attempt 1 --contract-revision 1 --allowed-path workitems -- python -m unittest e2e.test_primary_flow -v
```

Expected: browser tests pass and a manifest is written beneath `.webbuilder-artifacts/RUN-E2E/PROJECT/1/`.

- [ ] **Step 5: Add the optional CI job and commit**

Add a separate `reference-e2e` job on Windows and Ubuntu that installs the pinned requirements and Chromium, runs Django tests, then runs browser tests. It may be slower than the standard-library matrix but must be required before autonomous opt-in release.

```powershell
git add examples/autonomous-reference/e2e .github/workflows/test.yml tests/test_webbuilder_autonomous_e2e.py
git commit -m "test: add browser evidence for autonomous reference"
```

---

### Task 4: Exercise Contract Approval, Forced Stop, Resume, and Delivery

**Files:**
- Create: `tests/test_webbuilder_autonomous_e2e.py`
- Create: `examples/autonomous-reference/webbuilder-fixtures/approved-contract.json`
- Create: `examples/autonomous-reference/webbuilder-fixtures/ready-system-design.md`
- Create: `examples/autonomous-reference/webbuilder-fixtures/ready-task-plan.md`
- Create: `examples/autonomous-reference/webbuilder-fixtures/completed-task-plan.md`
- Modify: `webbuilder/scripts/transition-state.py`

**Interfaces:**
- Consumes: every Plan 1-3 CLI and the reference app.
- Produces: one complete autonomous lifecycle proof.

- [ ] **Step 1: Write the lifecycle test before fixture implementation**

The test copies the reference app into a temporary Git repository and performs these exact subprocess calls:

```python
ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = ROOT / "webbuilder" / "scripts" / "init-state.py"
CHECK_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-state.py"
APPROVE_SCRIPT = ROOT / "webbuilder" / "scripts" / "approve-contract.py"
CHECK_HOST_SCRIPT = ROOT / "webbuilder" / "scripts" / "check-host.py"
TRANSITION_SCRIPT = ROOT / "webbuilder" / "scripts" / "transition-state.py"
CAPTURE_SCRIPT = ROOT / "webbuilder" / "scripts" / "capture-evidence.py"


def run_cli(self, script: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd or ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    return result


def run_check(self, project: Path, phase: str) -> subprocess.CompletedProcess[str]:
    return self.run_cli(CHECK_SCRIPT, "--target", str(project), "--phase", phase)


def assert_state(self, project: Path, **expected: str) -> None:
    text = (project / "webbuilder" / "loop-state.md").read_text(encoding="utf-8")
    for key, value in expected.items():
        self.assertEqual(top_level_value(text, key), value)


self.run_cli(INIT_SCRIPT, "--target", str(project))
self.fill_contract_from_fixture(project, "approved-contract.json")
self.copy_fixture(project, "ready-system-design.md", "system-design.md")
self.copy_fixture(project, "ready-task-plan.md", "task-plan.md")
self.run_check(project, "specification")
self.run_cli(APPROVE_SCRIPT, "--target", str(project), "--approval-evidence", "e2e-user-approval")
self.run_cli(CHECK_HOST_SCRIPT, "--target", str(project), "--set", "browser=available:playwright", "--set", "subagents=unavailable:test-single-mode")
self.run_check(project, "initialization")
self.force_stop(project, reason="environment_blocked", checkpoint="task:TASK-002")
self.assert_state(project, status="blocked", stop_reason="environment_blocked")
self.run_cli(TRANSITION_SCRIPT, "--target", str(project), "--recover")
self.resume(project)
self.assert_completed_task_not_reexecuted(project, "TASK-001")
self.capture_all_project_evidence(project)
self.write_completed_task_plan_from_fixture(project)
self.run_check(project, "delivery")
```

Implement `copy_fixture()` with `shutil.copy2()` from `examples/autonomous-reference/webbuilder-fixtures/` to the temporary project's `webbuilder/` directory. `fill_contract_from_fixture()` JSON-serializes the fixture with `ensure_ascii=False`, replaces the single `contract-material` block, sets `discovery_method: inferred_contract`, and replaces every `not recorded` contract value. `force_stop()` invokes `transition-state.py --stop-reason <reason> --checkpoint <checkpoint>`; `resume()` invokes `transition-state.py --resume`.

`capture_all_project_evidence()` runs the real capture CLI once per required project domain and appends the returned relative manifest path, record ID, attempt, revision, fingerprint, result, redaction status, and quality domain to `validation-log.md`. Use these exact command/domain pairs:

| Domain | Command |
|---|---|
| `functional` | `python manage.py test -v 2` |
| `ui` | `python -m unittest e2e.test_primary_flow -v` |
| `accessibility` | `python -m unittest e2e.test_primary_flow.PrimaryFlowTests.test_accessibility_states -v` |
| `performance` | `python -m unittest e2e.test_primary_flow.PrimaryFlowTests.test_warm_primary_flow_under_budget -v` |
| `security` | `python manage.py check --deploy` |
| `delivery-smoke` | `python manage.py migrate --check` |

`assert_completed_task_not_reexecuted()` stores TASK-001's acceptance evidence record ID before the stop and asserts the same ID occurs exactly once after resume. `write_completed_task_plan_from_fixture()` copies the completed task plan and uses a State Kernel transaction to preserve the current state revision.

The final assertion checks `status: delivered`, no pending transition, no stop reason, complete coverage rows, current manifests, and unchanged TASK-001 evidence record ID across stop/resume.

- [ ] **Step 2: Run the test and observe missing fixtures/lifecycle support**

```powershell
python -m unittest tests.test_webbuilder_autonomous_e2e.AutonomousLifecycleTests -v
```

Expected: failure at the first missing fixture or unsupported lifecycle transition.

- [ ] **Step 3: Add explicit stop and resume events**

Extend `transition-state.py` with:

```text
--stop-reason <declared-reason> --checkpoint <checkpoint>
--resume
--deliver
```

`--resume` requires `status: blocked|paused`, `pending_transition: null`, resolvable stop evidence, and current contract approval. It clears the stop reason, restores `status: active`, and leaves completed task/evidence records untouched. `--deliver` requires the delivery checker to pass before changing terminal state.

- [ ] **Step 4: Add complete synthetic fixtures**

The contract fixture selects `django-5.2-lts`, UI/database/auth/accessibility/security/performance required, RBAC/audit/Docker not applicable with reasons, four bounded tasks, browser flows, required quality gates, repair budgets 3/5, and no external dependencies.

The task plan fixture contains contract revision 1, all required schema 1.4 fields, complete acceptance/integration records, and no paths outside the example project.

- [ ] **Step 5: Add tamper and host-degradation variants**

Duplicate the lifecycle test with exactly one mutation each:

- change a captured artifact byte: delivery fails hash validation;
- remove browser capability: UI-required project blocks at host gate;
- set Docker unavailable while Docker is not applicable: flow continues;
- increment contract revision without approval: execution and delivery fail;
- interrupt a state transaction after one file: recovery finishes and no task repeats.

- [ ] **Step 6: Verify and commit**

```powershell
python -m unittest tests.test_webbuilder_autonomous_e2e -v
python -m unittest discover -s tests -v
git add tests/test_webbuilder_autonomous_e2e.py examples/autonomous-reference/webbuilder-fixtures webbuilder/scripts/transition-state.py
git commit -m "test: prove autonomous stop resume and delivery"
```

---

### Task 5: Add Prompt-Level Behavior Evaluations and Progressive Loading

**Files:**
- Create: `tests/fixtures/prompts/common-saas.md`
- Create: `tests/fixtures/prompts/content-application.md`
- Create: `tests/fixtures/prompts/operational-application.md`
- Create: `tests/fixtures/prompts/api-only.md`
- Create: `tests/fixtures/prompts/geospatial.md`
- Create: `tests/fixtures/expected/common-saas.json`
- Create: `tests/fixtures/expected/content-application.json`
- Create: `tests/fixtures/expected/operational-application.json`
- Create: `tests/fixtures/expected/api-only.json`
- Create: `tests/fixtures/expected/geospatial.json`
- Create: `tests/test_webbuilder_behavior_evaluations.py`
- Create: `webbuilder/references/domains/geospatial.md`

**Interfaces:**
- Consumes: contract compiler behavior documented in `SKILL.md`.
- Produces: deterministic evaluation fixtures for contract shape, applicability, task bounds, stop behavior, and domain-reference routing.

- [ ] **Step 1: Define evaluation records**

Each expected JSON contains:

```json
{
  "required_capabilities": ["security", "performance"],
  "not_applicable_capabilities": {},
  "required_quality_domains": ["functional", "security", "performance", "delivery-smoke"],
  "forbidden_domain_references": [],
  "required_domain_references": [],
  "maximum_normal_confirmations": 1,
  "allowed_stop_reasons": ["needs_user_action", "needs_decision", "repair_exhausted", "environment_blocked"]
}
```

Customize every fixture with concrete expected capabilities and domain routing. API-only requires UI/accessibility not applicable with reasons. Only the geospatial fixture requires `references/domains/geospatial.md`; all other fixtures forbid it.

- [ ] **Step 2: Write deterministic fixture-validation tests**

The tests validate expected JSON completeness and feed stored contract outputs through `validate_capabilities()` and specification checks. Keep live-LLM scoring outside the required unit suite; the Skill evaluation procedure records prompt, model/host, output, rubric results, and evidence as an optional release evaluation.

- [ ] **Step 3: Add the minimal geospatial reference**

The reference contributes terminology, coordinate-system invariants, data-boundary questions, architecture risks, and tests. It explicitly states that it does not own confirmation, state transitions, UI, evidence, or delivery.

- [ ] **Step 4: Verify progressive loading and commit**

```powershell
python -m unittest tests.test_webbuilder_behavior_evaluations -v
git add tests/fixtures tests/test_webbuilder_behavior_evaluations.py webbuilder/references/domains/geospatial.md
git commit -m "test: add autonomous behavior evaluation fixtures"
```

---

### Task 6: Enable Autonomous Opt-In and Publish the Final Operating Contract

**Files:**
- Modify: `webbuilder/SKILL.md`
- Modify: `webbuilder/agents/openai.yaml`
- Modify: `webbuilder/references/install.md`
- Modify: `webbuilder/references/delivery-checklist.md`
- Modify: `README.md`
- Modify: `README_EN.md`
- Modify: `docs/status/current-development-progress.md`
- Modify: `tests/test_spec2web_state_scripts.py`
- Create: `tests/test_webbuilder_installation.py`

**Interfaces:**
- Consumes: all completed plans and exit evidence.
- Produces: discoverable autonomous opt-in behavior with guided default and final user documentation.

- [ ] **Step 1: Add final Skill contract assertions**

Assert the installed Skill documents and routes every required command:

```python
for marker in (
    "delivery_mode: guided | autonomous",
    "--phase specification",
    "scripts/approve-contract.py",
    "scripts/check-host.py",
    "--phase initialization",
    "scripts/capture-evidence.py",
    "--phase ui",
    "scripts/transition-state.py",
    "--resume",
    "--phase delivery",
):
    self.assertIn(marker, text)
```

- [ ] **Step 2: Enable explicit opt-in only**

Document activation phrases such as `/webbuilder start autonomous from requirements.md`. Existing state and migrated projects remain guided. Autonomous mode may proceed after specification, approval, host, and initialization gates; it stops only for declared reasons and persists a checkpoint when the host session ends.

- [ ] **Step 3: Update delivery and install documentation**

Document the golden profile as the first maintained path, the existing/custom-stack escape hatch, artifact retention, exact local startup, clean data initialization, browser installation, supported host degradation, and the fact that WebBuilder does not continue after the host exits.

Create `tests/test_webbuilder_installation.py` that copies the complete `webbuilder/` tree to temporary `.codex/skills/webbuilder`, `.claude/skills/webbuilder`, and `.hermes/skills/webbuilder` destinations. For each destination assert `SKILL.md`, `agents/openai.yaml`, every reference, and every script named in `SKILL.md` exists; run `init-state.py`, `migrate-state.py --dry-run`, and `check-state.py --phase structure` from the copied tree. This is the deterministic portability gate; a release checklist separately records one real discovery smoke run on each installed host version.

- [ ] **Step 4: Run final acceptance verification**

```powershell
python -m unittest discover -s tests -v
python -m unittest tests.test_webbuilder_autonomous_e2e -v
python -m unittest tests.test_webbuilder_installation -v
python -X utf8 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" webbuilder
python webbuilder/scripts/check-state.py --target examples/autonomous-reference --phase delivery
git diff --check
```

Expected: all tests pass, Skill validation prints `Skill is valid!`, the reference delivery check passes, and diff check is clean.

- [ ] **Step 5: Update progress and commit**

Record the actual commit hashes and measured test counts from the completed work, not estimates. Then:

```powershell
git add webbuilder/SKILL.md webbuilder/agents/openai.yaml webbuilder/references/install.md webbuilder/references/delivery-checklist.md README.md README_EN.md tests/test_spec2web_state_scripts.py tests/test_webbuilder_installation.py
git add -f docs/status/current-development-progress.md
git commit -m "feat: enable autonomous WebBuilder delivery opt-in"
```

## Plan 4 Exit Gate

- [ ] One pinned golden profile and one full-stack example are maintained and documented.
- [ ] Clean install, migration, seed, startup, Django tests, browser tests, and manifest capture pass.
- [ ] Stop/resume preserves completed tasks and accepted evidence.
- [ ] Tamper, stale revision, and missing required host capability variants fail closed.
- [ ] API-only and domain-specific fixtures prove applicability and progressive loading.
- [ ] Autonomous mode is explicit opt-in; guided remains default for existing/migrated projects.
- [ ] All 13 design acceptance criteria have linked passing evidence in the roadmap matrix.
