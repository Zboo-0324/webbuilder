"""Browser-driven end-to-end tests for the autonomous reference application.

Uses Playwright against a live Django dev server to verify authentication,
work-item CRUD, responsive layout, keyboard focus, console/network health,
accessibility baseline, and warm-page performance.

These tests depend on ``e2e.server`` (live Django process) and
``e2e.accessibility`` (baseline checks) which are implemented alongside
this module in the green phase.
"""

from __future__ import annotations

import time
import unittest

from playwright.sync_api import sync_playwright

from e2e.accessibility import baseline_accessibility_failures
from e2e.server import LiveServer


class PrimaryFlowTests(unittest.TestCase):
    """End-to-end browser tests for the primary authenticated flow."""

    server: LiveServer
    live_url: str
    pw: object
    browser: object
    context: object
    page: object

    console_errors: list[str]
    failed_requests: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = LiveServer()
        cls.live_url = cls.server.start()
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.pw.stop()
        cls.server.stop()

    def setUp(self) -> None:
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 720})
        self.page = self.context.new_page()
        self.console_errors = []
        self.failed_requests = []
        self.page.on(
            "console",
            lambda msg: self.console_errors.append(msg.text) if msg.type == "error" else None,
        )
        self.page.on("requestfailed", lambda req: self.failed_requests.append(req.url))

    def tearDown(self) -> None:
        self.context.close()

    # -- helpers -----------------------------------------------------------

    def login(self) -> None:
        """Navigate to the login page and authenticate as ``reviewer``."""
        self.console_errors.clear()
        self.failed_requests.clear()
        self.page.goto(self.live_url + "/accounts/login/")
        self.page.get_by_label("Username").fill("reviewer")
        self.page.get_by_label("Password").fill("review-pass")
        self.page.get_by_role("button", name="Sign in").click()
        self.page.wait_for_url(self.live_url + "/")

    # -- primary flow + responsive layout ----------------------------------

    def test_login_create_complete_and_responsive_layout(self) -> None:
        """Login, create a browser item, complete it, check focus, and
        verify no console errors or failed requests.  Then replay the
        primary structural assertions at 390, 768, and 1440 CSS-pixel
        widths."""
        # Login and drive the primary flow
        self.login()
        self.page.get_by_label("Title").fill("Browser-created item")
        self.page.get_by_role("button", name="Add item").click()
        self.page.get_by_role("button", name="Complete Browser-created item").click()

        # The completed item must show a "Completed" status.
        # Use .last to pick the most recently created item when prior runs
        # have left same-title rows in the persistent SQLite database.
        item_text = self.page.get_by_text("Browser-created item").last.locator("..").inner_text()
        self.assertIn("completed", item_text.lower())

        # Keyboard focus must move away from body on Tab
        self.page.keyboard.press("Tab")
        self.assertTrue(
            self.page.evaluate("document.activeElement !== document.body"),
            "Tab press should move focus to a focusable element",
        )

        # No console errors or failed network requests during the flow
        self.assertEqual(self.console_errors, [])
        self.assertEqual(self.failed_requests, [])

        # Responsive layout assertions at three widths
        for width in (390, 768, 1440):
            with self.subTest(width=width):
                self.page.set_viewport_size({"width": width, "height": 720})
                self.assertEqual(len(self.page.get_by_role("main").all()), 1)
                self.assertEqual(len(self.page.get_by_role("heading", level=1).all()), 1)
                self.assertTrue(
                    self.page.get_by_role("button", name="Sign out").is_visible(),
                )
                self.assertIn(
                    "completed",
                    self.page.get_by_text("Browser-created item").last.locator("..").inner_text().lower(),
                )

    # -- accessibility states ----------------------------------------------

    def test_accessibility_states(self) -> None:
        """Baseline accessibility checks must pass after login and after
        a validation error is rendered."""
        self.login()
        self.assertEqual(baseline_accessibility_failures(self.page), [])

        # Trigger a server-side validation error (bypass HTML5 required with whitespace)
        self.page.get_by_label("Title").fill("   ")
        self.page.get_by_role("button", name="Add item").click()
        self.assertTrue(self.page.get_by_text("Title is required").is_visible())
        self.assertEqual(baseline_accessibility_failures(self.page), [])

    # -- performance budget ------------------------------------------------

    def test_warm_primary_flow_under_budget(self) -> None:
        """A warm-page reload must complete within 2,000 ms."""
        self.login()
        self.page.goto(self.live_url + "/", wait_until="networkidle")
        started = time.perf_counter()
        self.page.reload(wait_until="networkidle")
        elapsed_ms = (time.perf_counter() - started) * 1000
        self.assertLess(elapsed_ms, 2000, f"warm primary flow took {elapsed_ms:.1f} ms")


if __name__ == "__main__":
    unittest.main()
