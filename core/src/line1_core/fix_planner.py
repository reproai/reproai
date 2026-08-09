from __future__ import annotations

import re
from dataclasses import dataclass, field

_AUTO_SAFE_RULES = {"B9-suppressed-data-load", "B11-rmd-chunk-in-r"}

_QUIET_PREFIX = re.compile(r'^(\s*)(qui(?:etly)?)(\s*:?\s+)(.*\b(?:use|import|insheet|infile)\b.*)$', re.IGNORECASE)
_RMD_FENCE = re.compile(r'^(\s*)(```.*)$')


@dataclass
class LineEdit:
    file: str
    line: int
    old: str
    new: str
    rule_id: str
    reason: str


@dataclass
class FixPlan:
    edits: list[LineEdit] = field(default_factory=list)
    skipped_propose_only: list[dict[str, object]] = field(default_factory=list)


def _plan_b9(file: str, lines: list[str], line_no: int) -> LineEdit | None:
    if not (1 <= line_no <= len(lines)):
        return None
    old = lines[line_no - 1]
    m = _QUIET_PREFIX.match(old)
    if not m:
        return None
    new = f"{m.group(1)}{m.group(4)}"
    if new == old:
        return None
    return LineEdit(file, line_no, old, new, "B9-suppressed-data-load",
                    "drop the `quietly` prefix so a missing-file failure is visible")


def _plan_b11(file: str, lines: list[str], line_no: int) -> LineEdit | None:
    if not (1 <= line_no <= len(lines)):
        return None
    old = lines[line_no - 1]
    m = _RMD_FENCE.match(old)
    if not m:
        return None
    new = f"{m.group(1)}# {m.group(2)}"
    return LineEdit(file, line_no, old, new, "B11-rmd-chunk-in-r",
                    "comment out the R Markdown fence so the .R file parses")


def build(advisory: dict[str, object], file_texts: dict[str, str]) -> FixPlan:
    plan = FixPlan()
    items = advisory.get("items", [])
    assert isinstance(items, list)
    for item in items:
        rule_id = item["rule_id"]
        if rule_id not in _AUTO_SAFE_RULES:
            plan.skipped_propose_only.append({
                "id": item["id"], "rule_id": rule_id, "priority": item["priority"],
                "message": item["message"],
            })
            continue
        for ev in item.get("evidence", []):
            file = ev.get("file")
            line_no = ev.get("line")
            if file is None or line_no is None or file not in file_texts:
                continue
            lines = file_texts[file].splitlines()
            edit = _plan_b9(file, lines, line_no) if rule_id == "B9-suppressed-data-load" else _plan_b11(file, lines, line_no)
            if edit is not None:
                plan.edits.append(edit)
    return plan
