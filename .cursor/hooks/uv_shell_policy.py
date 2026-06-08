#!/usr/bin/env python3
"""Cursor hook: keep shell commands aligned with this uv workspace."""

from __future__ import annotations

import json
import shlex
import sys

UV_VERIFICATION_PREFIXES = (
    ("uv", "run", "pytest"),
    ("uv", "run", "ruff", "check"),
    ("uv", "run", "ruff", "format"),
    ("uv", "run", "--package", "notebooks", "python"),
)

UV_REVIEW_PREFIXES = (
    ("uv", "sync"),
    ("uv", "lock"),
    ("uv", "add"),
    ("uv", "remove"),
    ("uv", "run", "--package", "notebooks", "jupyter", "lab"),
)

PIP_INSTALL_PREFIXES = (
    ("pip", "install"),
    ("pip3", "install"),
    ("python", "-m", "pip", "install"),
    ("python3", "-m", "pip", "install"),
)

OTHER_PACKAGE_MANAGER_PREFIXES = (
    ("poetry", "add"),
    ("poetry", "install"),
    ("pipenv", "install"),
    ("conda", "install"),
)


def emit(permission: str, user_message: str = "", agent_message: str = "") -> None:
    payload: dict[str, object] = {
        "continue": True,
        "permission": permission,
    }
    if user_message:
        payload["user_message"] = user_message
    if agent_message:
        payload["agent_message"] = agent_message
    print(json.dumps(payload))


def command_from_input() -> str:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        emit(
            "ask",
            "Cursor hook could not parse the shell command payload.",
            "Ask before running this command because the uv policy hook could not parse its input.",
        )
        raise SystemExit(0) from None

    command = payload.get("command")
    if isinstance(command, str):
        return command
    emit(
        "ask",
        "Cursor hook did not receive a shell command string.",
        "Ask before running this command because the uv policy hook did "
        "not receive a command string.",
    )
    raise SystemExit(0)


def has_prefix(words: list[str], prefixes: tuple[tuple[str, ...], ...]) -> bool:
    return any(tuple(words[: len(prefix)]) == prefix for prefix in prefixes)


def main() -> None:
    command = command_from_input()
    try:
        words = shlex.split(command)
    except ValueError:
        emit(
            "ask",
            "Shell command needs review before running.",
            "The command could not be parsed safely by the uv policy hook, "
            "so ask before running it.",
        )
        return

    if not words:
        emit("allow")
        return

    if has_prefix(words, PIP_INSTALL_PREFIXES) or has_prefix(words, OTHER_PACKAGE_MANAGER_PREFIXES):
        emit(
            "deny",
            "Use uv for dependency management in this workspace.",
            "This repository is a uv workspace. Use `uv add` for dependency "
            "changes or `uv sync --all-packages` to install the workspace "
            "instead of direct package-manager installs.",
        )
        return

    if has_prefix(words, UV_VERIFICATION_PREFIXES):
        emit("allow")
        return

    if has_prefix(words, UV_REVIEW_PREFIXES):
        emit(
            "ask",
            "uv command changes dependencies, environment state, or starts a service.",
            "Ask before running this uv command because it may update the "
            "lockfile, install packages, change dependencies, or start Jupyter.",
        )
        return

    emit("allow")


if __name__ == "__main__":
    main()
