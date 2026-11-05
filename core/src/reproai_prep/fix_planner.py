from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, TypeGuard

R_FENCE_OPERATION_ID: Final = "r_script_fence_normalization_v1"
R_PARSE_POSTCHECK: Final = "r_parse_via_Rscript_vanilla"
_AUTO_SAFE_RULES = {"B9-suppressed-data-load", "B11-rmd-chunk-in-r"}

_QUIET_PREFIX = re.compile(r'^(\s*)(qui(?:etly)?)(\s*:?\s+)(.*\b(?:use|import|insheet|infile)\b.*)$', re.IGNORECASE)
_RMD_FENCE = re.compile(r'^(\s*)(```.*)$')
_R_RAW_START = re.compile(r'[rR]"(?P<dash>-*)\(')


@dataclass(frozen=True, slots=True)
class LineEdit:
    file: str
    line: int
    old: str
    new: str
    rule_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class Automation:
    eligible: bool
    operation_ids: list[str]
    reason: str
    postchecks: list[str]


@dataclass(frozen=True, slots=True)
class Operation:
    id: str
    before_hash: str
    edits: tuple[LineEdit, ...]
    postchecks: tuple[str, ...]


@dataclass(slots=True)
class FixPlan:
    edits: list[LineEdit] = field(default_factory=list)
    skipped_propose_only: list[dict[str, object]] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)
    automation: Automation = field(
        default_factory=lambda: Automation(False, [], "no supported safe-auto operation", [])
    )


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


def _r_fence_line(line: str) -> str | None:
    stripped = line.strip()
    if stripped == "```" or re.match(r"^```\s*\{[rR][^}]*}\s*$", stripped):
        return stripped
    return None


def r_standalone_fence_lines(text: str) -> tuple[tuple[int, str], ...] | str:
    fences: list[tuple[int, str]] = []
    quote: str | None = None
    raw_end: str | None = None
    for line_no, line in enumerate(text.splitlines(), start=1):
        if raw_end is not None:
            end_marker = raw_end
            end_at = line.find(end_marker)
            if end_at == -1:
                continue
            quote, raw_end = _scan_r_code(line[end_at + len(end_marker) :], quote)
            continue
        if quote is None:
            stripped = line.strip()
            fence = _r_fence_line(line)
            if fence is not None and not stripped.startswith("#"):
                fences.append((line_no, line))
                continue
        quote, raw_end = _scan_r_code(line, quote)
    if raw_end is not None:
        return "ambiguous raw string around R Markdown fence; manual review required"
    return tuple(fences)


def _scan_r_code(line: str, quote: str | None) -> tuple[str | None, str | None]:
    i = 0
    while i < len(line):
        if quote is None:
            if line[i] == "#":
                return None, None
            raw = _R_RAW_START.match(line, i)
            if raw is not None:
                end_marker = f'){raw.group("dash")}"'
                close_at = line.find(end_marker, raw.end())
                if close_at == -1:
                    return None, end_marker
                i = close_at + len(end_marker)
                continue
            if line[i] in {'"', "'", "`"}:
                quote = line[i]
        elif line[i] == quote and not _is_escaped(line, i):
            quote = None
        i += 1
    return quote, None


def _is_escaped(line: str, index: int) -> bool:
    slash_count = 0
    cursor = index - 1
    while cursor >= 0 and line[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def _r_parse_succeeds(rscript: str, file: str, text: str) -> bool:
    with TemporaryDirectory(prefix="reproai-r-parse-") as temp:
        target = Path(temp) / file
        target.parent.mkdir(parents=True, exist_ok=True)
        _ = target.write_text(text, encoding="utf-8")
        try:
            result = subprocess.run(
                [rscript, "--vanilla", "-e", f"parse(file={str(target.as_posix())!r})"],
                cwd=Path(temp),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False
    return result.returncode == 0


def _is_json_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _plan_r_fence_operation(file: str, text: str) -> Operation | str | None:
    rscript = shutil.which("Rscript")
    if rscript is None:
        return "Rscript unavailable; R parse postcheck cannot run"
    if _r_parse_succeeds(rscript, file, text):
        return None
    scan = r_standalone_fence_lines(text)
    if isinstance(scan, str):
        return scan
    edits: list[LineEdit] = []
    in_chunk = False
    for line_no, line in scan:
        fence = _r_fence_line(line)
        if fence is None:
            continue
        if fence == "```":
            if not in_chunk:
                return "ambiguous/unbalanced R Markdown fence; manual review required"
            in_chunk = False
        else:
            if in_chunk:
                return "ambiguous/unbalanced R Markdown fence; manual review required"
            in_chunk = True
        indent = line[: len(line) - len(line.lstrip())]
        edits.append(LineEdit(file, line_no, line, f"{indent}# {line.lstrip()}", "B11-rmd-chunk-in-r", "comment paired standalone R Markdown fences so the .R file parses"))
    if in_chunk:
        return "ambiguous/unbalanced R Markdown fence; manual review required"
    if not edits:
        return None
    return Operation(R_FENCE_OPERATION_ID, sha256(text.encode()).hexdigest(), tuple(edits), (R_PARSE_POSTCHECK,))


def _automation(operations: list[Operation], reason: str) -> Automation:
    if not operations:
        return Automation(False, [], reason, [])
    return Automation(True, sorted({op.id for op in operations}), "verified deterministic preconditions", sorted({check for op in operations for check in op.postchecks}))


def postcheck(root: Path, plan: FixPlan) -> bool:
    if not plan.operations:
        return True
    rscript = shutil.which("Rscript")
    if rscript is None:
        return False
    for op in plan.operations:
        file = op.edits[0].file
        source = root / file
        if not _r_parse_succeeds(rscript, file, source.read_text(encoding="utf-8", errors="replace")):
            return False
    return True


def build(advisory: dict[str, object], file_texts: dict[str, str]) -> FixPlan:
    plan = FixPlan()
    raw_items = advisory.get("items", [])
    if not _is_object_list(raw_items):
        return plan
    for item in raw_items:
        if not _is_json_object(item):
            continue
        rule_id = item.get("rule_id")
        if not isinstance(rule_id, str):
            continue
        if rule_id not in _AUTO_SAFE_RULES:
            plan.skipped_propose_only.append({
                "id": item.get("id", ""), "rule_id": rule_id, "priority": item.get("priority", ""),
                "message": item.get("message", ""),
            })
            continue
        if rule_id == "B11-rmd-chunk-in-r":
            reason = "no supported safe-auto operation"
            for file, text in sorted(file_texts.items()):
                if not file.lower().endswith(".r"):
                    continue
                operation = _plan_r_fence_operation(file, text)
                if isinstance(operation, Operation):
                    plan.operations.append(operation)
                    plan.edits.extend(operation.edits)
                elif isinstance(operation, str):
                    reason = operation
            plan.automation = _automation(plan.operations, reason)
            continue
        evidence = item.get("evidence", [])
        if not _is_object_list(evidence):
            continue
        for ev in evidence:
            if not _is_json_object(ev):
                continue
            file = ev.get("file")
            line_no = ev.get("line")
            if not isinstance(file, str) or not isinstance(line_no, int) or file not in file_texts:
                continue
            lines = file_texts[file].splitlines()
            edit = _plan_b9(file, lines, line_no) if rule_id == "B9-suppressed-data-load" else _plan_b11(file, lines, line_no)
            if edit is not None:
                plan.edits.append(edit)
    return plan
