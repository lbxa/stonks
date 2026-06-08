#!/usr/bin/env python3
"""Cursor hook: remind agents about repo checks after Python-relevant edits."""

from __future__ import annotations

import json
import sys

QUALITY_RELEVANT_SUFFIXES = (".py", ".toml", ".lock")
QUALITY_RELEVANT_NAMES = {"pyproject.toml", "uv.lock"}


def emit(message: str = "") -> None:
    payload: dict[str, object] = {"continue": True}
    if message:
        payload["agent_message"] = message
    print(json.dumps(payload))


def collect_paths(value: object) -> list[str]:
    paths: list[str] = []
    if isinstance(value, str):
        paths.append(value)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                paths.append(item)
            elif isinstance(item, dict):
                paths.extend(collect_paths(item.get("path")))
                paths.extend(collect_paths(item.get("file_path")))
    elif isinstance(value, dict):
        for key in ("path", "file_path", "files", "modified_files"):
            paths.extend(collect_paths(value.get(key)))
    return paths


def is_quality_relevant(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return name in QUALITY_RELEVANT_NAMES or path.endswith(QUALITY_RELEVANT_SUFFIXES)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        emit()
        return

    paths = collect_paths(payload)
    if any(is_quality_relevant(path) for path in paths):
        emit(
            "Python workspace files changed. Before finishing, run "
            "`uv run ruff check .` and the narrowest relevant "
            "`uv run pytest` target; use `uv run ruff format .` "
            "when formatting is needed."
        )
        return

    emit()


if __name__ == "__main__":
    main()
