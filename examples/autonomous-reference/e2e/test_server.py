"""Test that LiveServer bootstraps a clean database with migrations and the
deterministic browser-E2E account.

This test backs up any existing ``db.sqlite3``, removes it, starts
``LiveServer``, then inspects the resulting SQLite file to confirm:

1. Django migration tables exist (schema was created).
2. The ``reviewer`` user with password ``review-pass`` exists.

The backup is always restored in ``tearDown`` so no local artifacts remain.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import unittest
from pathlib import Path

from e2e.server import LiveServer

# Resolve the project root (parent of e2e/) and the database path.
_E2E_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _E2E_DIR.parent
_DB_PATH = _PROJECT_ROOT / "db.sqlite3"
_DB_BACKUP = _PROJECT_ROOT / "db.sqlite3.bak"


class LiveServerCleanStartTest(unittest.TestCase):
    """Verify LiveServer creates schema and seed account from a clean slate."""

    server: LiveServer
    _had_db: bool

    def setUp(self) -> None:
        # Back up any existing database so the test starts clean.
        self._had_db = _DB_PATH.exists() and _DB_PATH.stat().st_size > 0
        if self._had_db:
            shutil.copy2(_DB_PATH, _DB_BACKUP)
        # Remove the database so LiveServer must run migrate from scratch.
        if _DB_PATH.exists():
            _DB_PATH.unlink()

        self.server = LiveServer()

    def tearDown(self) -> None:
        self.server.stop()
        # Close all Django database connections so Windows can release the
        # SQLite file lock before we move or delete it.
        import django.db
        django.db.connections.close_all()
        # Restore the original database (or remove any test-created artefact).
        if self._had_db and _DB_BACKUP.exists():
            shutil.move(str(_DB_BACKUP), str(_DB_PATH))
        elif _DB_PATH.exists():
            _DB_PATH.unlink()

    def test_clean_start_creates_schema_and_reviewer_account(self) -> None:
        """Starting LiveServer without db.sqlite3 must create the migrated
        schema and the deterministic ``reviewer`` / ``review-pass`` account."""
        # Start the server -- this triggers migrate + seed.
        self.server.start()

        # The database file must now exist and be non-empty.
        self.assertTrue(_DB_PATH.exists(), "db.sqlite3 was not created by LiveServer.start()")
        self.assertGreater(_DB_PATH.stat().st_size, 0, "db.sqlite3 is empty after server start")

        conn = sqlite3.connect(str(_DB_PATH))
        try:
            # 1. Verify migration tables exist (auth_user is created by Django
            #    migrations and is a reliable indicator that migrate ran).
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            self.assertIn("auth_user", tables, "auth_user table missing -- migrations did not run")
            self.assertIn("django_migrations", tables, "django_migrations table missing")

            # 2. Verify the deterministic reviewer account exists.
            rows = conn.execute(
                "SELECT username FROM auth_user WHERE username = 'reviewer'"
            ).fetchall()
            self.assertEqual(len(rows), 1, "reviewer account was not seeded")
        finally:
            conn.close()

        # 3. Verify the reviewer password is correct using Django's own
        #    password hasher so we don't duplicate hash logic.
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        import django  # noqa: E402
        django.setup()
        from django.contrib.auth.models import User  # noqa: E402

        reviewer = User.objects.get(username="reviewer")
        self.assertTrue(
            reviewer.check_password("review-pass"),
            "reviewer password does not match expected 'review-pass'",
        )


if __name__ == "__main__":
    unittest.main()
