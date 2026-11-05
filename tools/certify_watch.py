"""Has IQSS Certify changed since the target profile was read?

The profile (core/src/reproai_prep/targets/certify.yaml, `watch`) records the SHA-256 of the
Certify files it was read from. This fetches Certify's published SHA256SUMS and compares. Any
difference (a new program version, revised instructions) means: re-read Certify, update the
profile and its `basis`, and re-run tools/certify_alignment.py. Exit 0 when nothing changed, 1
when something did, 2 when the list cannot be fetched.

    python3 tools/certify_watch.py [--sums FILE]
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

import yaml

PROFILE = Path(__file__).resolve().parents[1] / "core/src/reproai_prep/targets/certify.yaml"


def parse_sums(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2:
            out[parts[1]] = parts[0]
    return out


def compare(recorded: dict[str, str], live: dict[str, str]) -> list[str]:
    """What changed, in words; empty when the files the profile was read from are unchanged."""
    changes = []
    for name, digest in sorted(recorded.items()):
        if name not in live:
            changes.append(f"{name} is no longer published")
        elif live[name] != digest:
            changes.append(f"{name} changed")
    recorded_programs = {n for n in recorded if n.startswith("dist/") and n.endswith(".whl")}
    for name in sorted(live):
        if name.startswith("dist/") and name.endswith(".whl") and name not in recorded_programs:
            changes.append(f"{name} is new")
    return changes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Report whether IQSS Certify changed since the target profile was read.")
    ap.add_argument("--sums", type=Path, default=None, help="Compare with a saved SHA256SUMS instead of fetching it.")
    args = ap.parse_args(argv)
    watch = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))["watch"]
    try:
        if args.sums:
            text = args.sums.read_text(encoding="utf-8")
        else:
            with urllib.request.urlopen(watch["sums_url"], timeout=30) as response:
                text = response.read().decode("utf-8")
    except OSError as exc:
        print(f"cannot read the published list: {exc}", file=sys.stderr)
        return 2
    changes = compare(watch["files"], parse_sums(text))
    if not changes:
        print("IQSS Certify is unchanged since the profile was read.")
        return 0
    print("IQSS Certify changed since the profile was read:")
    for c in changes:
        print(f"  {c}")
    print("Re-read Certify, update targets/certify.yaml (rules, basis, watch), and re-run tools/certify_alignment.py.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
