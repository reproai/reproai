"""Promote a human-reviewed candidate rule into the shipped author_rules.yaml and bump rules_version. Run AFTER a maintainer has reviewed the candidate and written a final rule spec."""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any

import yaml

RULES_FILE = Path(__file__).resolve().parents[1] / "core/src/line1_core/rules/author_rules.yaml"
CHANGELOG = Path(__file__).resolve().parents[1] / "core/CHANGELOG.md"

_REQUIRED = ["id", "category", "kind", "priority", "rule", "detection", "languages", "source_lessons"]
_CATEGORIES = {"structural", "code-style", "environment", "normalization"}
_KINDS = {"defect", "normalization"}
_PRIORITIES = {"P0", "P1", "P2", "P3", "P4"}


def _load_rules() -> dict[str, Any]:
    return yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))


def _validate(rule: dict[str, Any], existing_ids: set[str]) -> list[str]:
    errs: list[str] = []
    for f in _REQUIRED:
        if f not in rule:
            errs.append(f"missing field: {f}")
    if rule.get("id") in existing_ids:
        errs.append(f"duplicate id: {rule.get('id')}")
    if rule.get("category") not in _CATEGORIES:
        errs.append(f"bad category: {rule.get('category')}")
    if rule.get("kind") not in _KINDS:
        errs.append(f"bad kind: {rule.get('kind')}")
    if rule.get("priority") not in _PRIORITIES:
        errs.append(f"bad priority: {rule.get('priority')}")
    if not isinstance(rule.get("languages"), list):
        errs.append("languages must be a list")
    if not isinstance(rule.get("source_lessons"), list) or not rule.get("source_lessons"):
        errs.append("source_lessons must be a non-empty list (traceability to Line 2)")
    return errs


def promote(rule: dict[str, Any], dry_run: bool) -> int:
    data = _load_rules()
    rules = data["rules"]
    existing_ids = {r["id"] for r in rules}  # type: ignore[index]
    errs = _validate(rule, existing_ids)
    if errs:
        print("REJECTED — fix the candidate spec:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 2

    new_version = datetime.date.today().strftime("%Y.%m.%d")
    if dry_run:
        print(f"[dry-run] would add rule '{rule['id']}' and bump rules_version -> {new_version}")
        return 0

    rules.append(rule)  # type: ignore[union-attr]
    data["rules_version"] = new_version
    RULES_FILE.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")

    entry = (
        f"\n## rules_version {new_version}\n\n"
        f"- Added `{rule['id']}` ({rule['kind']}, {rule['priority']}): {rule['rule']}\n"
        f"  promoted from Line 2 lesson(s): {', '.join(str(s) for s in rule['source_lessons'])}\n"
    )
    text = CHANGELOG.read_text(encoding="utf-8")
    marker = "<!-- Append new entries above this line."
    text = text.replace(marker, entry + "\n" + marker, 1) if marker in text else text + entry
    CHANGELOG.write_text(text, encoding="utf-8")

    print(f"PROMOTED '{rule['id']}' — rules_version is now {new_version}. Remember to bump the plugin version and publish.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Promote a reviewed candidate rule into author_rules.yaml.")
    ap.add_argument("rule_json", help="Path to a JSON file with the final rule spec (the 8 required fields).")
    ap.add_argument("--dry-run", action="store_true", help="Validate only; do not write.")
    args = ap.parse_args(argv)

    rule = json.loads(Path(args.rule_json).read_text(encoding="utf-8"))
    return promote(rule, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
