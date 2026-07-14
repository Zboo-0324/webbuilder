"""Manage a live Django dev server for end-to-end tests.

``LiveServer`` starts ``manage.py runserver`` on a free port, waits for the
login page to become reachable, and exposes the base URL.  ``stop()`` always
terminates the child process.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _free_port() -> int:
    """Return a TCP port currently unused on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class LiveServer:
    """Start and manage a Django development server process."""

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None
        self._port: int = 0
        self._url: str = ""

    @property
    def url(self) -> str:
        return self._url

    def start(self, timeout: float = 20.0) -> str:
        """Start the dev server and return its base URL.

        Waits up to *timeout* seconds for the login page to respond with
        HTTP 200 before raising ``TimeoutError``.
        """
        self._port = _free_port()
        self._url = f"http://127.0.0.1:{self._port}"

        manage_py = str(Path(__file__).resolve().parent.parent / "manage.py")
        self._process = subprocess.Popen(
            [
                sys.executable,
                manage_py,
                "runserver",
                f"127.0.0.1:{self._port}",
                "--noreload",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        login_url = f"{self._url}/accounts/login/"
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise RuntimeError(
                    f"Django dev server exited prematurely with code {self._process.returncode}"
                )
            try:
                resp = urllib.request.urlopen(login_url, timeout=2)
                if resp.status == 200:
                    return self._url
            except (urllib.error.URLError, OSError, ConnectionError):
                pass
            time.sleep(0.25)

        self.stop()
        raise TimeoutError(
            f"Dev server did not become ready within {timeout}s (checked {login_url})"
        )

    def stop(self) -> None:
        """Terminate the dev server process if still running."""
        if self._process is None:
            return
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        self._process = None
