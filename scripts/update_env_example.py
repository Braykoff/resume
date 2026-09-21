#!/usr/bin/env python3
"""Generate .env.example from .env by replacing every value with a placeholder.

Preserves comments, blank lines, and key names; only values are scrubbed.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"
ENV_EXAMPLE_FILE = REPO_ROOT / ".env.example"

PLACEHOLDER = "<INSERT VALUE HERE>"


def scrub_line(line: str) -> str:
    stripped = line.rstrip("\n")

    if not stripped.strip() or stripped.strip().startswith("#"):
        return stripped

    if "=" not in stripped:
        return stripped

    key, _, _ = stripped.partition("=")
    return f"{key}={PLACEHOLDER}"


def main() -> None:
    if not ENV_FILE.exists():
        raise SystemExit(f"No .env file found at {ENV_FILE}")

    lines = ENV_FILE.read_text().splitlines()
    scrubbed = [scrub_line(line) for line in lines]

    ENV_EXAMPLE_FILE.write_text("\n".join(scrubbed) + "\n")
    print(f"Wrote {ENV_EXAMPLE_FILE}")


if __name__ == "__main__":
    main()
