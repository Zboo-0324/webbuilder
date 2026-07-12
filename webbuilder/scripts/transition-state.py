from __future__ import annotations

import argparse
from pathlib import Path

from state_schema import resolve_state_dir, set_top_level_value, top_level_value
from state_transition import apply_transaction, recover_pending_transaction


def parse_update(value: str) -> tuple[str, str, str]:
    name, separator, assignment = value.partition(":")
    key, equals, field_value = assignment.partition("=")
    if not separator or not name or not equals or not key:
        raise ValueError(f"invalid --set value: {value}")
    return name, key, field_value


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply or recover a WebBuilder state transition.")
    parser.add_argument("--target", default=".", help="Project directory containing webbuilder state.")
    parser.add_argument("--recover", action="store_true", help="Recover a pending transition.")
    parser.add_argument("--event", help="Transition event name.")
    parser.add_argument("--set", dest="sets", action="append", default=[], help="file:key=value")
    args = parser.parse_args()

    if args.recover:
        if args.event or args.sets:
            parser.error("--recover cannot be combined with --event or --set")
    elif not args.event or not args.sets:
        parser.error("--event and at least one --set are required unless recovering")

    try:
        state_dir = resolve_state_dir(Path(args.target).resolve())
        if args.recover:
            transition_id = recover_pending_transaction(state_dir)
            if transition_id:
                print(f"recovered: {transition_id}")
            return 0

        updates: dict[str, str] = {}
        for raw_value in args.sets:
            name, key, field_value = parse_update(raw_value)
            text = updates.get(name, (state_dir / name).read_text(encoding="utf-8"))
            updates[name] = set_top_level_value(text, key, field_value)
        loop_text = (state_dir / "loop-state.md").read_text(encoding="utf-8")
        expected_revision = int(top_level_value(loop_text, "state_revision") or "0")
        transition_id = apply_transaction(
            state_dir, args.event, updates, expected_revision=expected_revision
        )
    except (OSError, ValueError) as exc:
        print(f"State transition failed: {exc}")
        return 1

    print(f"applied: {transition_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
