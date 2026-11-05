"""Measure the Certify target against Certify itself, on the same bytes.

For each package, run Prep's check with --target certify and Certify's own read-only
`certify targets` (it lists what closing would refuse and note, and runs no author code), map
Certify's messages to the profile's rule ids, and report where the two disagree:

  certify_only   Certify refuses or notes something Prep said nothing about  -> a Prep gap
  prep_only      Prep predicts something `targets` did not print; for a rule Certify only
                 enforces at closing this is expected, so those are listed apart

Certify is used only as an instrument, installed in its own environment; nothing of it is
imported here. Usage:

    PYTHONPATH=core/src python3 tools/certify_alignment.py --certify ~/certify-env/bin/certify \
        --scratch /tmp/align PKG [PKG ...] [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from reproai_prep import coordinator

# Certify's own wording (author_program 0.2.0) -> the profile rule that predicts it
_MESSAGES = (
    ("running stata is not built yet", "CF1-stata-not-runnable"),
    ("no script to run", "CF2-notebook-only"),
    ("symbolic link", "CF8-tree-paths"),
    ("is empty: packing carries only files", "CF8-tree-paths"),
    ("differ only in letter case", "CF8-tree-paths"),
    ("spell one name two ways", "CF8-tree-paths"),
    ("control character", "CF8-tree-paths"),
    ("dot component", "CF8-tree-paths"),
    ("installs a package while it runs", "CF14-runtime-install"),
    ("needs a person at the keyboard", "CF15-interactive-call"),
    ("an installed library, not the analysis", "CF9-installation-folder"),
    ("leftovers from unzipping", "CF9-installation-folder"),
    ("above the size ceiling", "D10-package-size-cap"),
    ("entries", "CF23-entry-count"),
)
# about this computer, not the package
_ENVIRONMENT = ("worker processes that talk over local sockets", "proxy settings alone", "is not installed", "not found")
# rules Certify enforces only when closing (the audit's refusals, the runs): `targets` cannot show them
CLOSING_ONLY = {
    "CF4-path-from-script-folder", "CF5-climb-above-root", "CF6-network-read", "CF7-outside-service",
    "CF10-startup-file", "CF11-reserved-name", "CF12-runtime-cache-write", "CF13-non-utf8-text-read",
    "CF16-hook-dropping-launch", "CF17-remote-launch", "CF18-certification-setting-named",
    "CF19-unremappable-seed", "CF20-socket-workers", "CF21-forked-workers-default-rng",
    "CF22-output-folder-missing", "CF3-notebook-not-run",
    # generic rules whose findings the profile gives an effect: the reading audit's refusal of an
    # outside reference, and a run that fails on a file the package does not hold
    "B4-no-abs-paths", "A14-missing-input",
}


def certify_messages(certify: str, pkg: Path, scratch: Path) -> tuple[list[str], int, bool]:
    env = dict(os.environ, TMPDIR=str(scratch), R_LIBS=str(scratch / "rlib"), R_LIBS_USER=str(scratch / "rlib"))
    (scratch / "rlib").mkdir(parents=True, exist_ok=True)
    r = subprocess.run([certify, "targets", str(pkg)], capture_output=True, text=True, timeout=600, env=env)
    lines = (r.stdout + r.stderr).splitlines()
    messages = []
    for line in lines:
        if line.startswith("Closing would stop."):
            messages.append(line.removeprefix("Closing would stop.").strip())    # one line, its parts joined by "; "
        elif line.startswith(("Note:", "Warning:")) or line.startswith("The R scripts load") or line.startswith("The Python scripts load"):
            messages.append(line)
    return messages, r.returncode, any(line.startswith("Closing would stop.") for line in lines)


def classify(messages: list[str]) -> tuple[set[str], list[str], bool]:
    """(rule ids, unmapped messages, whether libraries need vendoring)."""
    ids: set[str] = set()
    unmapped: list[str] = []
    vendor = False
    for m in messages:
        if "not in the dataset's library root yet" in m:
            vendor = True
            continue
        if any(token in m for token in _ENVIRONMENT):
            continue
        hits = {rule for token, rule in _MESSAGES if token in m}
        if hits:
            ids |= hits
        else:
            unmapped.append(m)
    return ids, unmapped, vendor


def prep_ids(pkg: Path) -> set[str]:
    items = coordinator.check(pkg, None, "certify")["advisory_plan"]["items"]
    return {it["rule_id"] for it in items if it.get("target_effect")}


def compare(certify: str, pkg: Path, scratch: Path) -> dict[str, Any]:
    messages, code, stopped = certify_messages(certify, pkg, scratch)
    seen, unmapped, vendor = classify(messages)
    predicted = prep_ids(pkg)
    unseen = (predicted - seen) - CLOSING_ONLY
    return {
        "package": str(pkg),
        "certify_exit": code,
        "certify_stopped": stopped,
        "both": sorted(seen & predicted),
        "certify_only": sorted(seen - predicted),
        # once closing would stop, `targets` prints no notes: a note Prep predicts is not contradicted
        "prep_only": [] if stopped else sorted(unseen),
        "prep_masked_by_stop": sorted(unseen) if stopped else [],
        "prep_closing_only": sorted((predicted - seen) & CLOSING_ONLY),
        "certify_unmapped": unmapped,
        "certify_wants_vendor": vendor,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Measure the Certify target against `certify targets`.")
    ap.add_argument("packages", nargs="+", type=Path)
    ap.add_argument("--certify", required=True, help="Path to Certify's `certify` command, installed in its own environment.")
    ap.add_argument("--scratch", required=True, type=Path, help="Scratch folder for Certify's temporary files and an empty R library.")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args(argv)
    rows = [compare(args.certify, pkg.resolve(), args.scratch.resolve()) for pkg in args.packages if pkg.is_dir()]
    gaps = [r for r in rows if r["certify_only"] or r["certify_unmapped"]]
    extras = [r for r in rows if r["prep_only"]]
    for r in rows:
        flag = "GAP " if r in gaps else ("XTRA" if r in extras else "ok  ")
        print(f"{flag} {Path(r['package']).parent.name}/{Path(r['package']).name}: both={r['both']} "
              f"certify_only={r['certify_only']} prep_only={r['prep_only']} unmapped={len(r['certify_unmapped'])}")
    print(f"\n{len(rows)} packages: {len(gaps)} with a Prep gap, {len(extras)} with a Prep prediction `targets` did not show")
    if args.json:
        args.json.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
