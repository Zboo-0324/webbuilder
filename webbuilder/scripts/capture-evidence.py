"""CLI to capture deterministic command evidence into an evidence manifest."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from evidence_core import capture_command_evidence  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture deterministic command evidence")
    parser.add_argument("--target", required=True, help="Project root directory")
    parser.add_argument("--run", required=True, help="Run identifier")
    parser.add_argument("--subject", required=True, help="Subject identifier")
    parser.add_argument("--attempt", required=True, type=int, help="Attempt number")
    parser.add_argument("--contract-revision", required=True, type=int, help="Contract revision")
    parser.add_argument(
        "--allowed-path",
        action="append",
        default=[],
        dest="allowed_paths",
        help="Project-relative paths for direct_apply_fingerprint (repeatable)",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command after --")

    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("no command supplied after --")

    project_root = Path(args.target).resolve()
    manifest_path = capture_command_evidence(
        project_root,
        command,
        run_id=args.run,
        subject_id=args.subject,
        attempt=args.attempt,
        contract_revision=args.contract_revision,
        allowed_paths=args.allowed_paths,
    )
    relative = manifest_path.relative_to(project_root).as_posix()
    print(f"manifest: {relative}")

    # Return the exit code from the captured command
    from evidence_core import load_manifest

    return int(load_manifest(manifest_path)["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
