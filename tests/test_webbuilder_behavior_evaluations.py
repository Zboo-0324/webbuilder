"""RED-phase contract tests for behavior evaluation scenarios.

Deterministically specifies the Task 5 contract for five named evaluation
scenarios: common-saas, content-application, operational-application,
api-only, and geospatial.  These tests load scenario definitions from
``tests/fixtures/expected/<scenario>.json`` and prompt text from
``tests/fixtures/prompts/<scenario>.md``.  They intentionally fail because
the required fixture files, domain reference files, and the
behavior_evaluation module do not exist yet.

No live LLM calls, no mocks, no implementation fixtures.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "webbuilder" / "scripts"
FIXTURES_DIR = ROOT / "tests" / "fixtures"
EXPECTED_DIR = FIXTURES_DIR / "expected"
PROMPTS_DIR = FIXTURES_DIR / "prompts"

sys.path.insert(0, str(SCRIPTS))

from contract_core import validate_capabilities  # noqa: E402


# ---------------------------------------------------------------------------
# Scenario names — the contract requires exactly these five.
# ---------------------------------------------------------------------------

SCENARIO_NAMES = (
    "common-saas",
    "content-application",
    "operational-application",
    "api-only",
    "geospatial",
)


# ---------------------------------------------------------------------------
# Expected JSON keys and shapes — enforced against every loaded fixture.
# ---------------------------------------------------------------------------

# Top-level keys every expected-JSON fixture must carry, with required types.
EXPECTED_JSON_SCHEMA: dict[str, type | tuple[type, ...]] = {
    "scenario_name": str,
    "capabilities": dict,
    "quality_domains": list,
    "task_bounds": dict,
    "domain_reference": (str, type(None)),
    "stop_reasons": list,
}

# Quality domain shape: each entry must carry these keys.
QUALITY_DOMAIN_KEYS = frozenset({"name", "applicable", "reason"})

# Task bounds shape: each entry must carry these keys.
TASK_BOUNDS_KEYS = frozenset({"task_id", "max_repair_attempts", "stop_reason"})

# Valid stop reasons matching check-state.py VALID_STOP_REASONS.
VALID_STOP_REASONS = frozenset({
    "none",
    "verification_failed",
    "needs_user_action",
    "needs_decision",
    "repair_exhausted",
    "environment_blocked",
})

# The six delivery quality domains.
ALL_QUALITY_DOMAINS = (
    "functional",
    "ui",
    "accessibility",
    "performance",
    "security",
    "delivery-smoke",
)

# Core domains that always apply.
CORE_QUALITY_DOMAINS = ("functional", "security", "performance", "delivery-smoke")

# UI-specific domains that apply only when ui is required.
UI_QUALITY_DOMAINS = ("ui", "accessibility")

# Geospatial domain reference path — exactly this path, no other.
GEOSPATIAL_DOMAIN_REFERENCE = "webbuilder/references/domains/geospatial.md"

# All non-geospatial scenarios must NOT reference the geospatial domain file.
NON_GEOSPATIAL_SCENARIOS = (
    "common-saas",
    "content-application",
    "operational-application",
    "api-only",
)


# ---------------------------------------------------------------------------
# Fixture loading helpers — all assertions derive from these.
# ---------------------------------------------------------------------------

def _expected_json_path(scenario_name: str) -> Path:
    """Return the expected path for *scenario_name*'s JSON fixture."""
    return EXPECTED_DIR / f"{scenario_name}.json"


def _prompt_path(scenario_name: str) -> Path:
    """Return the expected path for *scenario_name*'s prompt fixture."""
    return PROMPTS_DIR / f"{scenario_name}.md"


def _load_expected_json(scenario_name: str) -> dict:
    """Load and return the expected-JSON fixture for *scenario_name*.

    Raises ``FileNotFoundError`` with the fixture path if the file does not
    exist — the intended RED-phase failure mode.
    """
    path = _expected_json_path(scenario_name)
    if not path.is_file():
        raise FileNotFoundError(
            f"Expected JSON fixture missing: {path.relative_to(ROOT)}"
        )
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_prompt_text(scenario_name: str) -> str:
    """Load and return the prompt fixture text for *scenario_name*.

    Raises ``FileNotFoundError`` if the prompt file does not exist.
    """
    path = _prompt_path(scenario_name)
    if not path.is_file():
        raise FileNotFoundError(
            f"Prompt fixture missing: {path.relative_to(ROOT)}"
        )
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class FixtureExistenceTests(unittest.TestCase):
    """All required fixture files must be present on disk."""

    def test_expected_json_fixtures_exist(self) -> None:
        """Each scenario must have a JSON fixture under tests/fixtures/expected/."""
        missing = [
            str(_expected_json_path(name).relative_to(ROOT))
            for name in SCENARIO_NAMES
            if not _expected_json_path(name).is_file()
        ]
        self.assertEqual(
            missing, [],
            f"Missing expected JSON fixtures: {missing}",
        )

    def test_prompt_fixtures_exist(self) -> None:
        """Each scenario must have a prompt fixture under tests/fixtures/prompts/."""
        missing = [
            str(_prompt_path(name).relative_to(ROOT))
            for name in SCENARIO_NAMES
            if not _prompt_path(name).is_file()
        ]
        self.assertEqual(
            missing, [],
            f"Missing prompt fixtures: {missing}",
        )


class PromptContentTests(unittest.TestCase):
    """Prompt fixture files must be nonempty."""

    def test_each_prompt_fixture_is_nonempty(self) -> None:
        """Every prompt .md file must contain non-whitespace content.

        Fails (not skips) if any prompt fixture file is missing, so the
        RED phase is visible as a test failure.
        """
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_prompt_path(name).relative_to(ROOT))
            if not _prompt_path(name).is_file():
                failures.append(f"{rel}: file missing")
                continue
            text = _prompt_path(name).read_text(encoding="utf-8").strip()
            if not text:
                failures.append(f"{rel}: file is empty")
        self.assertEqual(failures, [], f"Prompt fixture failures:\n" + "\n".join(failures))


class BehaviorEvaluationJSONSchemaTests(unittest.TestCase):
    """Every loaded scenario fixture must carry the required top-level JSON keys."""

    def test_expected_json_schema_keys_exist(self) -> None:
        """EXPECTED_JSON_SCHEMA must define all required keys."""
        required = {
            "scenario_name", "capabilities", "quality_domains",
            "task_bounds", "domain_reference", "stop_reasons",
        }
        self.assertEqual(set(EXPECTED_JSON_SCHEMA.keys()), required)

    def test_each_fixture_has_required_keys(self) -> None:
        """Each loaded JSON fixture must contain every key in EXPECTED_JSON_SCHEMA."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            for key in EXPECTED_JSON_SCHEMA:
                if key not in data:
                    failures.append(f"{rel}: missing key '{key}'")
        self.assertEqual(failures, [], f"JSON schema failures:\n" + "\n".join(failures))

    def test_each_fixture_has_correct_types(self) -> None:
        """Each JSON fixture value must match its expected type."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            for key, expected_type in EXPECTED_JSON_SCHEMA.items():
                if key not in data:
                    continue  # caught by test_each_fixture_has_required_keys
                if not isinstance(data[key], expected_type):
                    failures.append(
                        f"{rel}: '{key}' must be {expected_type}, "
                        f"got {type(data[key]).__name__}"
                    )
        self.assertEqual(failures, [], f"Type failures:\n" + "\n".join(failures))

    def test_fixture_scenario_name_matches_filename(self) -> None:
        """Each fixture's scenario_name field must match its filename."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            if data.get("scenario_name") != name:
                failures.append(
                    f"{rel}: scenario_name is {data.get('scenario_name')!r}, expected '{name}'"
                )
        self.assertEqual(failures, [], f"Scenario name mismatches:\n" + "\n".join(failures))


class CapabilityApplicabilityTests(unittest.TestCase):
    """Capabilities from loaded fixtures must pass validate_capabilities()."""

    def _load_fixture_or_fail(self, name: str) -> dict:
        """Load fixture data; fail immediately if the file is absent."""
        try:
            return _load_expected_json(name)
        except FileNotFoundError as exc:
            self.fail(str(exc))

    def test_common_saas_capabilities_valid(self) -> None:
        data = self._load_fixture_or_fail("common-saas")
        caps = data["capabilities"]
        delivery = data.get("delivery_assumptions", [])
        errors = validate_capabilities(caps, delivery_assumptions=delivery)
        self.assertEqual(
            errors, [],
            f"tests/fixtures/expected/common-saas.json: capabilities invalid: {errors}",
        )

    def test_content_application_capabilities_valid(self) -> None:
        data = self._load_fixture_or_fail("content-application")
        caps = data["capabilities"]
        delivery = data.get("delivery_assumptions", [])
        errors = validate_capabilities(caps, delivery_assumptions=delivery)
        self.assertEqual(
            errors, [],
            f"tests/fixtures/expected/content-application.json: capabilities invalid: {errors}",
        )

    def test_operational_application_capabilities_valid(self) -> None:
        data = self._load_fixture_or_fail("operational-application")
        caps = data["capabilities"]
        delivery = data.get("delivery_assumptions", [])
        errors = validate_capabilities(caps, delivery_assumptions=delivery)
        self.assertEqual(
            errors, [],
            f"tests/fixtures/expected/operational-application.json: capabilities invalid: {errors}",
        )

    def test_api_only_capabilities_valid(self) -> None:
        data = self._load_fixture_or_fail("api-only")
        caps = data["capabilities"]
        delivery = data.get("delivery_assumptions", [])
        errors = validate_capabilities(caps, delivery_assumptions=delivery)
        self.assertEqual(
            errors, [],
            f"tests/fixtures/expected/api-only.json: capabilities invalid: {errors}",
        )

    def test_geospatial_capabilities_valid(self) -> None:
        data = self._load_fixture_or_fail("geospatial")
        caps = data["capabilities"]
        delivery = data.get("delivery_assumptions", [])
        errors = validate_capabilities(caps, delivery_assumptions=delivery)
        self.assertEqual(
            errors, [],
            f"tests/fixtures/expected/geospatial.json: capabilities invalid: {errors}",
        )

    def test_api_only_ui_and_accessibility_not_applicable(self) -> None:
        """API-only fixture must mark ui and accessibility as not_applicable."""
        data = self._load_fixture_or_fail("api-only")
        caps = data["capabilities"]
        self.assertEqual(
            caps["ui"]["status"], "not_applicable",
            "tests/fixtures/expected/api-only.json: ui must be not_applicable",
        )
        self.assertEqual(
            caps["accessibility"]["status"], "not_applicable",
            "tests/fixtures/expected/api-only.json: accessibility must be not_applicable",
        )

    def test_api_only_ui_reason_nonempty(self) -> None:
        """API-only ui not_applicable must have a nonempty reason."""
        data = self._load_fixture_or_fail("api-only")
        reason = data["capabilities"]["ui"].get("reason", "")
        self.assertTrue(
            reason and reason.strip(),
            "tests/fixtures/expected/api-only.json: ui reason must be nonempty",
        )

    def test_api_only_accessibility_reason_nonempty(self) -> None:
        """API-only accessibility not_applicable must have a nonempty reason."""
        data = self._load_fixture_or_fail("api-only")
        reason = data["capabilities"]["accessibility"].get("reason", "")
        self.assertTrue(
            reason and reason.strip(),
            "tests/fixtures/expected/api-only.json: accessibility reason must be nonempty",
        )


class QualityDomainShapeTests(unittest.TestCase):
    """Loaded quality domains must satisfy the contract shape."""

    def _load_or_fail(self, name: str) -> dict:
        """Load fixture data; fail immediately if the file is absent."""
        try:
            return _load_expected_json(name)
        except FileNotFoundError as exc:
            self.fail(str(exc))

    def test_quality_domain_entries_have_required_keys(self) -> None:
        """Every quality domain entry must have name, applicable, and reason."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            for i, domain in enumerate(data["quality_domains"]):
                keys = set(domain.keys())
                if keys != QUALITY_DOMAIN_KEYS:
                    failures.append(
                        f"{rel}: quality_domains[{i}] keys are {keys}, "
                        f"expected {QUALITY_DOMAIN_KEYS}"
                    )
        self.assertEqual(failures, [], f"Quality domain key failures:\n" + "\n".join(failures))

    def test_all_six_domains_present(self) -> None:
        """Each fixture must list all six delivery quality domains."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            domain_names = {d["name"] for d in data["quality_domains"]}
            for expected in ALL_QUALITY_DOMAINS:
                if expected not in domain_names:
                    failures.append(f"{rel}: missing quality domain '{expected}'")
        self.assertEqual(failures, [], f"Missing domains:\n" + "\n".join(failures))

    def test_core_domains_always_applicable(self) -> None:
        """functional, security, performance, delivery-smoke must always be applicable."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            domains_by_name = {d["name"]: d for d in data["quality_domains"]}
            for core in CORE_QUALITY_DOMAINS:
                if core not in domains_by_name:
                    failures.append(f"{rel}: missing '{core}'")
                elif not domains_by_name[core]["applicable"]:
                    failures.append(f"{rel}: '{core}' must be applicable")
        self.assertEqual(failures, [], f"Core domain failures:\n" + "\n".join(failures))

    def test_ui_domains_applicable_when_ui_required(self) -> None:
        """ui and accessibility must be applicable when capability ui is required."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            ui_required = data["capabilities"].get("ui", {}).get("status") == "required"
            domains_by_name = {d["name"]: d for d in data["quality_domains"]}
            for ui_domain in UI_QUALITY_DOMAINS:
                if ui_domain not in domains_by_name:
                    failures.append(f"{rel}: missing '{ui_domain}'")
                elif ui_required and not domains_by_name[ui_domain]["applicable"]:
                    failures.append(f"{rel}: '{ui_domain}' must be applicable when ui required")
                elif not ui_required and domains_by_name[ui_domain]["applicable"]:
                    failures.append(f"{rel}: '{ui_domain}' must not be applicable when ui not required")
        self.assertEqual(failures, [], f"UI domain failures:\n" + "\n".join(failures))

    def test_api_only_ui_domains_not_applicable(self) -> None:
        """API-only must mark ui and accessibility quality domains as not_applicable."""
        data = self._load_or_fail("api-only")
        rel = str(_expected_json_path("api-only").relative_to(ROOT))
        domains_by_name = {d["name"]: d for d in data["quality_domains"]}
        for name in UI_QUALITY_DOMAINS:
            self.assertIn(name, domains_by_name)
            self.assertFalse(
                domains_by_name[name]["applicable"],
                f"{rel}: '{name}' must not be applicable",
            )

    def test_api_only_ui_domain_reason_nonempty(self) -> None:
        """API-only not_applicable quality domains must have nonempty reasons."""
        data = self._load_or_fail("api-only")
        rel = str(_expected_json_path("api-only").relative_to(ROOT))
        for domain in data["quality_domains"]:
            if not domain["applicable"]:
                self.assertTrue(
                    domain["reason"] and str(domain["reason"]).strip(),
                    f"{rel}: {domain['name']} not_applicable reason must be nonempty",
                )


class TaskBoundsStopReasonTests(unittest.TestCase):
    """Task bounds and stop reasons from loaded fixtures must satisfy contract constraints."""

    def _load_or_fail(self, name: str) -> dict:
        try:
            return _load_expected_json(name)
        except FileNotFoundError as exc:
            self.fail(str(exc))

    def test_task_bounds_entries_have_required_keys(self) -> None:
        """Every task_bounds entry must have task_id, max_repair_attempts, and stop_reason."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            bounds = data["task_bounds"]
            if not isinstance(bounds, dict):
                failures.append(f"{rel}: task_bounds must be a dict")
                continue
            for task_id, bound in bounds.items():
                keys = set(bound.keys())
                if keys != TASK_BOUNDS_KEYS:
                    failures.append(
                        f"{rel}: task_bounds['{task_id}'] keys are {keys}, "
                        f"expected {TASK_BOUNDS_KEYS}"
                    )
        self.assertEqual(failures, [], f"Task bounds key failures:\n" + "\n".join(failures))

    def test_stop_reasons_subset_of_valid_set(self) -> None:
        """Every stop_reason in a fixture must belong to VALID_STOP_REASONS."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            for reason in data.get("stop_reasons", []):
                if reason not in VALID_STOP_REASONS:
                    failures.append(f"{rel}: invalid stop_reason '{reason}'")
        self.assertEqual(failures, [], f"Stop reason failures:\n" + "\n".join(failures))

    def test_task_bounds_stop_reasons_valid(self) -> None:
        """Each task_bounds entry's stop_reason must belong to VALID_STOP_REASONS."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            for task_id, bound in data["task_bounds"].items():
                if bound["stop_reason"] not in VALID_STOP_REASONS:
                    failures.append(
                        f"{rel}: task_bounds['{task_id}'].stop_reason "
                        f"'{bound['stop_reason']}' not in VALID_STOP_REASONS"
                    )
        self.assertEqual(failures, [], f"Task bounds stop reason failures:\n" + "\n".join(failures))

    def test_max_repair_within_budget(self) -> None:
        """Each task-level max_repair_attempts must not exceed 3."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            for task_id, bound in data["task_bounds"].items():
                mra = bound["max_repair_attempts"]
                if mra <= 0 or mra > 3:
                    failures.append(
                        f"{rel}: task_bounds['{task_id}'].max_repair_attempts={mra}, must be 1..3"
                    )
        self.assertEqual(failures, [], f"Repair budget failures:\n" + "\n".join(failures))


class DomainReferenceRoutingTests(unittest.TestCase):
    """Domain reference routing must direct each scenario to the correct reference file."""

    def test_geospatial_requires_exactly_geospatial_reference(self) -> None:
        """Geospatial fixture must route to exactly webbuilder/references/domains/geospatial.md."""
        rel = str(_expected_json_path("geospatial").relative_to(ROOT))
        try:
            data = _load_expected_json("geospatial")
        except FileNotFoundError as exc:
            self.fail(str(exc))
        ref = data["domain_reference"]
        self.assertEqual(
            ref, GEOSPATIAL_DOMAIN_REFERENCE,
            f"{rel}: domain_reference must be '{GEOSPATIAL_DOMAIN_REFERENCE}'",
        )

    def test_non_geospatial_forbid_geospatial_reference(self) -> None:
        """All non-geospatial fixtures must NOT reference the geospatial domain file."""
        failures: list[str] = []
        for name in NON_GEOSPATIAL_SCENARIOS:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            ref = data["domain_reference"]
            if ref == GEOSPATIAL_DOMAIN_REFERENCE:
                failures.append(f"{rel}: must not reference geospatial domain")
            elif ref is not None:
                failures.append(f"{rel}: domain_reference must be None, got {ref!r}")
        self.assertEqual(failures, [], f"Non-geospatial reference failures:\n" + "\n".join(failures))

    def test_geospatial_reference_path_format(self) -> None:
        """The geospatial domain reference path must use forward slashes and .md extension."""
        rel = str(_expected_json_path("geospatial").relative_to(ROOT))
        try:
            data = _load_expected_json("geospatial")
        except FileNotFoundError as exc:
            self.fail(str(exc))
        ref = data["domain_reference"]
        self.assertIsNotNone(ref)
        self.assertTrue(ref.endswith(".md"), f"{rel}: reference must end with .md: {ref}")
        self.assertIn("/", ref, f"{rel}: reference must use forward slashes")
        self.assertTrue(
            ref.startswith("webbuilder/references/"),
            f"{rel}: reference must start with webbuilder/references/: {ref}",
        )

    def test_geospatial_reference_file_must_exist(self) -> None:
        """webbuilder/references/domains/geospatial.md must exist on disk.

        This is the RED-phase assertion that will fail until the domain
        reference file is created in the implementation phase.
        """
        ref_path = ROOT / GEOSPATIAL_DOMAIN_REFERENCE
        self.assertTrue(
            ref_path.is_file(),
            f"domain reference file must exist: {GEOSPATIAL_DOMAIN_REFERENCE}",
        )


class ScenarioCompletenessTests(unittest.TestCase):
    """Each scenario fixture must be fully specified across all evaluation dimensions."""

    REQUIRED_CAPS = frozenset({
        "ui", "database", "authentication", "rbac", "audit",
        "docker", "accessibility", "performance", "security",
    })

    def _load_or_fail(self, name: str) -> dict:
        try:
            return _load_expected_json(name)
        except FileNotFoundError as exc:
            self.fail(str(exc))

    def test_every_fixture_has_capabilities(self) -> None:
        """Each fixture must have a capabilities dict with the 9 required capability names."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            caps = data["capabilities"]
            if not isinstance(caps, dict):
                failures.append(f"{rel}: capabilities must be a dict")
                continue
            missing = self.REQUIRED_CAPS - set(caps.keys())
            if missing:
                failures.append(f"{rel}: capabilities missing: {missing}")
        self.assertEqual(failures, [], f"Capabilities completeness failures:\n" + "\n".join(failures))

    def test_every_fixture_has_quality_domains(self) -> None:
        """Each fixture must have a nonempty quality_domains list."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            domains = data["quality_domains"]
            if not isinstance(domains, list):
                failures.append(f"{rel}: quality_domains must be a list")
            elif len(domains) == 0:
                failures.append(f"{rel}: quality_domains must be nonempty")
        self.assertEqual(failures, [], f"Quality domain completeness failures:\n" + "\n".join(failures))

    def test_all_capabilities_have_status(self) -> None:
        """Every capability entry in every fixture must have a status field."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            for cap_name, cap_entry in data["capabilities"].items():
                if "status" not in cap_entry:
                    failures.append(f"{rel}: '{cap_name}' missing status")
                elif cap_entry["status"] not in {"required", "not_applicable"}:
                    failures.append(
                        f"{rel}: '{cap_name}' invalid status: {cap_entry['status']}"
                    )
        self.assertEqual(failures, [], f"Status field failures:\n" + "\n".join(failures))

    def test_required_capabilities_with_profile(self) -> None:
        """Capabilities needing a profile must have one when required."""
        profile_caps = {"security", "performance"}
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            for cap_name in profile_caps:
                entry = data["capabilities"][cap_name]
                if entry["status"] == "required":
                    if "profile" not in entry:
                        failures.append(f"{rel}: '{cap_name}' required but missing profile")
                    elif entry["profile"] not in {"baseline", "standard", "strict"}:
                        failures.append(
                            f"{rel}: '{cap_name}' invalid profile: {entry['profile']}"
                        )
        self.assertEqual(failures, [], f"Profile failures:\n" + "\n".join(failures))

    def test_not_applicable_capabilities_have_reasons(self) -> None:
        """Capabilities marked not_applicable must have nonempty reasons."""
        failures: list[str] = []
        for name in SCENARIO_NAMES:
            rel = str(_expected_json_path(name).relative_to(ROOT))
            try:
                data = _load_expected_json(name)
            except FileNotFoundError as exc:
                failures.append(str(exc))
                continue
            for cap_name, entry in data["capabilities"].items():
                if entry["status"] == "not_applicable":
                    reason = entry.get("reason", "")
                    if not (reason and reason.strip()):
                        failures.append(
                            f"{rel}: '{cap_name}' not_applicable must have nonempty reason"
                        )
        self.assertEqual(failures, [], f"Reason failures:\n" + "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
