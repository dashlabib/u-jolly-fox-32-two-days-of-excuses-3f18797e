#!/usr/bin/env python3
"""Publish the one-line entry for the make.fun bounty
"Two Days of Excuses".

The excuse lives in ``entry.txt`` next to this file: one line, under
200 characters, in the voice of an AI agent explaining a missed
deadline. This program reads the entry's raw bytes, runs every check
of the bounty gate over them (UTF-8 text, a single line, 1 to 200
characters, not only white space, no control characters, no hidden
leading or trailing white space), and reports every problem it finds
at once instead of stopping at the first. When the entry passes, it
publishes those exact bytes to ``entry.txt`` in the output directory,
then reads the published file back and compares it byte for byte with
the source. Standard library only: no network access, no clock reads,
no randomness, so two runs always produce identical output.

The output directory is ``--output-dir <dir>`` when given, else
``$MAKEFUN_OUTPUT_DIR`` when set, else ``/output``. Pass
``--verify-only`` to check the entry without writing anything. A gate
failure exits 2; any other failure exits 1.
"""

import argparse
import os
import sys
from pathlib import Path

MAX_CHARS = 200
GATE_EXIT = 2


class GateError(Exception):
    """The entry fails one or more checks of the bounty gate."""


def load_entry_bytes() -> bytes:
    here = Path(__file__).resolve().parent
    entry_path = here / "entry.txt"
    try:
        return entry_path.read_bytes()
    except FileNotFoundError as exc:
        raise SystemExit(f"entry.txt not found next to main.py: {entry_path}") from exc


def gate_problems(raw: bytes) -> list:
    """Return every gate problem in the raw entry bytes, or []."""
    problems = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"entry is not valid UTF-8: {exc}"]
    if not text or text.isspace():
        problems.append("entry is empty or only white space")
    if len(text) > MAX_CHARS:
        problems.append(
            f"entry is {len(text)} characters, over the {MAX_CHARS} limit"
        )
    if "\n" in text or "\r" in text:
        problems.append("entry must be a single line")
    if any(ord(ch) < 0x20 for ch in text):
        problems.append("entry contains a control character")
    if text != text.strip():
        problems.append("entry has leading or trailing white space")
    return problems


def validate(raw: bytes) -> str:
    problems = gate_problems(raw)
    if problems:
        raise GateError("\n".join(f"- {p}" for p in problems))
    return raw.decode("utf-8")


def resolve_output_dir(args) -> Path:
    if args.output_dir:
        return Path(args.output_dir)
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env_dir:
        return Path(env_dir)
    return Path("/output")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=None,
                        help="directory to write entry.txt into")
    parser.add_argument("--verify-only", action="store_true",
                        help="validate the entry without writing it")
    return parser.parse_args(argv)


def publish(raw: bytes, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "entry.txt"
    out_path.write_bytes(raw)
    published = out_path.read_bytes()
    if published != raw:
        raise SystemExit("published entry does not match entry.txt")
    return out_path


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        raw = load_entry_bytes()
        text = validate(raw)
    except GateError as exc:
        print(f"Gate failed:\n{exc}", file=sys.stderr)
        return GATE_EXIT
    if args.verify_only:
        print(f"Valid: {len(text)} characters, {len(raw)} bytes")
        return 0
    out_path = publish(raw, resolve_output_dir(args))
    print(f"Wrote {len(text)} characters ({len(raw)} bytes) to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
