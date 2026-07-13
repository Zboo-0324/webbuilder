from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path

from state_schema import set_top_level_value, sha256_bytes, top_level_value


def atomic_write_text(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


@contextmanager
def state_lock(state_dir: Path) -> Iterator[None]:
    directory = state_dir / ".transitions"
    directory.mkdir(exist_ok=True)
    handle = (directory / ".lock").open("a+b")
    try:
        handle.seek(0)
        handle.write(b"\0")
        handle.flush()
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.01)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def transaction_path(state_dir: Path, name: str) -> Path:
    relative = Path(name)
    if not name or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"invalid transaction path: {name}")
    root = state_dir.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"invalid transaction path: {name}") from exc
    return path


def normalize_updates(state_dir: Path, updates: dict[str, str]) -> dict[str, str]:
    root = state_dir.resolve()
    normalized: dict[str, str] = {}
    for name, text in updates.items():
        canonical_name = transaction_path(state_dir, name).relative_to(root).as_posix()
        if canonical_name in normalized:
            raise ValueError(f"duplicate transaction path: {name}")
        normalized[canonical_name] = text
    return normalized


def build_journal(
    state_dir: Path,
    transition_id: str,
    event: str,
    expected_revision: int,
    next_revision: int,
    updates: dict[str, str],
    *,
    intermediate_loop_text: str | None = None,
) -> dict[str, object]:
    files = {}
    for name, target_text in sorted(updates.items()):
        current_bytes = transaction_path(state_dir, name).read_bytes()
        file_entry = {
            "original_sha256": sha256_bytes(current_bytes),
            "target_sha256": sha256_bytes(target_text.encode("utf-8")),
            "target_text": target_text,
        }
        if name == "loop-state.md" and intermediate_loop_text is not None:
            file_entry["intermediate_sha256"] = sha256_bytes(
                intermediate_loop_text.encode("utf-8")
            )
        files[name] = file_entry
    return {
        "transition_id": transition_id,
        "event": event,
        "expected_revision": expected_revision,
        "next_revision": next_revision,
        "status": "pending",
        "files": files,
    }


def write_journal(state_dir: Path, journal: dict[str, object]) -> None:
    directory = state_dir / ".transitions"
    directory.mkdir(exist_ok=True)
    path = directory / f"{journal['transition_id']}.json"
    atomic_write_text(path, json.dumps(journal, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def mark_journal_complete(state_dir: Path, transition_id: str) -> None:
    pending = state_dir / ".transitions" / f"{transition_id}.json"
    complete = pending.with_name(f"{transition_id}.complete.json")
    os.replace(pending, complete)


def replace_targets(
    state_dir: Path,
    journal: dict[str, object],
    *,
    skip_names: set[str],
    fail_after_replacements: int | None = None,
) -> None:
    files = journal["files"]
    assert isinstance(files, dict)
    replacements = 0
    for name in sorted(files):
        if name in skip_names:
            continue
        entry = files[name]
        assert isinstance(entry, dict)
        target_text = entry["target_text"]
        assert isinstance(target_text, str)
        atomic_write_text(transaction_path(state_dir, name), target_text)
        replacements += 1
        if fail_after_replacements is not None and replacements >= fail_after_replacements:
            raise RuntimeError("injected failure after replacement")


def apply_transaction(
    state_dir: Path,
    event: str,
    updates: dict[str, str],
    *,
    expected_revision: int,
    fail_after_replacements: int | None = None,
) -> str:
    target_updates = normalize_updates(state_dir, updates)
    with state_lock(state_dir):
        _recover_pending_transaction(state_dir)
        loop_path = transaction_path(state_dir, "loop-state.md")
        loop_text = loop_path.read_text(encoding="utf-8")
        actual_revision = int(top_level_value(loop_text, "state_revision") or "0")
        if actual_revision != expected_revision:
            raise ValueError(f"state revision changed: expected {expected_revision}, found {actual_revision}")
        transition_id = f"TX-{uuid.uuid4().hex}"
        next_revision = expected_revision + 1
        final_loop = target_updates.get("loop-state.md", loop_text)
        final_loop = set_top_level_value(final_loop, "state_revision", str(next_revision))
        final_loop = set_top_level_value(final_loop, "pending_transition", "null")
        target_updates["loop-state.md"] = final_loop
        intermediate_loop = set_top_level_value(loop_text, "pending_transition", transition_id)
        journal = build_journal(
            state_dir,
            transition_id,
            event,
            expected_revision,
            next_revision,
            target_updates,
            intermediate_loop_text=intermediate_loop,
        )
        write_journal(state_dir, journal)
        atomic_write_text(loop_path, intermediate_loop)
        replace_targets(
            state_dir,
            journal,
            skip_names={"loop-state.md"},
            fail_after_replacements=fail_after_replacements,
        )
        atomic_write_text(loop_path, final_loop)
        mark_journal_complete(state_dir, transition_id)
        return transition_id


def recover_pending_transaction(state_dir: Path) -> str | None:
    with state_lock(state_dir):
        return _recover_pending_transaction(state_dir)


def _recover_pending_transaction(state_dir: Path) -> str | None:
    directory = state_dir / ".transitions"
    if not directory.exists():
        return None
    pending = sorted(
        path for path in directory.glob("*.json") if not path.name.endswith(".complete.json")
    )
    if not pending:
        return None
    if len(pending) > 1:
        raise ValueError("multiple pending transitions require manual inspection")

    journal = json.loads(pending[0].read_text(encoding="utf-8"))
    transition_id = journal["transition_id"]
    files = journal["files"]
    assert isinstance(transition_id, str)
    assert isinstance(files, dict)
    if transition_id != pending[0].stem:
        raise ValueError("divergent transaction journal")

    loop_entry = files.get("loop-state.md")
    assert isinstance(loop_entry, dict)
    for name in sorted(files):
        if name == "loop-state.md":
            continue
        if not isinstance(name, str):
            raise ValueError("invalid transaction path")
        entry = files[name]
        assert isinstance(entry, dict)
        path = transaction_path(state_dir, name)
        current_hash = sha256_bytes(path.read_bytes())
        original_hash = entry["original_sha256"]
        target_hash = entry["target_sha256"]
        target_text = entry["target_text"]
        assert isinstance(original_hash, str)
        assert isinstance(target_hash, str)
        assert isinstance(target_text, str)
        if current_hash == target_hash:
            continue
        if current_hash == original_hash:
            atomic_write_text(path, target_text)
            continue
        raise ValueError(f"divergent transaction file: {name}")

    loop_path = transaction_path(state_dir, "loop-state.md")
    loop_hash = sha256_bytes(loop_path.read_bytes())
    original_hash = loop_entry["original_sha256"]
    target_hash = loop_entry["target_sha256"]
    intermediate_hash = loop_entry["intermediate_sha256"]
    target_text = loop_entry["target_text"]
    assert isinstance(original_hash, str)
    assert isinstance(target_hash, str)
    assert isinstance(intermediate_hash, str)
    assert isinstance(target_text, str)
    if loop_hash not in {original_hash, intermediate_hash, target_hash}:
        raise ValueError("divergent transaction file: loop-state.md")
    atomic_write_text(loop_path, target_text)
    mark_journal_complete(state_dir, transition_id)
    return transition_id
