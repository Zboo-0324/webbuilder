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
