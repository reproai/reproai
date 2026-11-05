from __future__ import annotations

# noqa: SIZE_OK -- legacy reviewed-repair substrate; this scoped change preserves its public seam.

import difflib
import hashlib
import json
import shutil
import stat
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from collections.abc import Mapping
from typing import TypedDict

from . import ado_vendor, fix_planner, inventory


JsonValue = str | int | float | bool | None | Mapping[str, "JsonValue"] | list["JsonValue"]
JsonMap = Mapping[str, JsonValue]


class ReviewedRepairError(Exception):
    pass


class UnsafePathError(ReviewedRepairError):
    pass


class StaleSourceError(ReviewedRepairError):
    pass


class StalePlanError(ReviewedRepairError):
    pass


class ApplyValidationError(ReviewedRepairError):
    pass


@dataclass(frozen=True, slots=True)
class LineChange:
    file: str
    line: int
    old: str
    new: str
    rule_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class CopyEvidence:
    path: str
    source: str
    package: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class ManualItem:
    id: str
    rule_id: str
    priority: str
    message: str
    file: str | None = None
    line: int | None = None
    evidence: str = ""
    actions: tuple[str, ...] = ()


class FileRow(TypedDict):
    path: str
    sha256: str
    size_bytes: int


def assert_safe_root(root: Path) -> Path:
    resolved = root.resolve()
    if not resolved.is_dir():
        raise UnsafePathError(f"not a directory: {resolved}")
    for path in sorted(resolved.rglob("*")):
        mode = path.lstat().st_mode
        if path.is_symlink() or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise UnsafePathError(f"refusing symlink or special file: {path}")
    return resolved


def assert_safe_destination(root: Path, dest: Path) -> Path:
    resolved = dest.resolve(strict=False)
    if resolved.exists() or not resolved.parent.is_dir() or _is_within(resolved, root):
        raise UnsafePathError(f"unsafe destination: {resolved}")
    return resolved


def tree_fingerprint(root: Path) -> str:
    return _hash_json(_tree_files(root))


def entries_fingerprint(report: JsonValue) -> str:
    if not isinstance(report, Mapping):
        raise ApplyValidationError("architecture_report is not an object")
    files = report.get("files")
    if not isinstance(files, list):
        raise ApplyValidationError("architecture_report.files is not a list")
    rows = [_file_row(item) for item in files]
    return _hash_json(sorted(rows, key=lambda r: r["path"]))


def build_fix_plan(root: Path, advisory: JsonValue) -> fix_planner.FixPlan:
    if not isinstance(advisory, Mapping):
        raise ApplyValidationError("advisory_plan is not an object")
    entries = inventory.scan(root)
    file_texts = {
        e.path: (root / e.path).read_text(encoding="utf-8", errors="replace")
        for e in inventory.code_entries(entries)
    }
    return fix_planner.build(_mutable_json(advisory), file_texts)


def build_line_changes(root: Path, advisory: JsonValue) -> tuple[LineChange, ...]:
    plan = build_fix_plan(root, advisory)
    return tuple(LineChange(e.file, e.line, e.old, e.new, e.rule_id, e.reason) for e in plan.edits)


def build_vendor_parts(root: Path) -> tuple[tuple[LineChange, ...], tuple[CopyEvidence, ...], tuple[ManualItem, ...]]:
    try:
        plan = ado_vendor.resolve_fixes(ado_vendor.scan_package(root))
    except ado_vendor.UnsafeVendorPathError as exc:
        raise UnsafePathError(str(exc)) from exc
    changes = tuple(_ado_line_change(root, issue) for issue in plan.rewrite)
    copied = tuple(e for entry in plan.vendor for e in _copy_evidence(entry))
    manual = tuple(
        ManualItem("ADO-UNRESOLVED", str(u["issue"]["kind"]), "P1", str(u["why"]), actions=("Vendor the ado package inside .certified/lib or remove the external dependency.",))
        for u in plan.unresolved
    )
    return changes, copied, manual


def build_manual_items(advisory: JsonValue, fixed_changes: tuple[LineChange, ...] = ()) -> tuple[ManualItem, ...]:
    if not isinstance(advisory, Mapping):
        return ()
    items = advisory.get("items", [])
    if not isinstance(items, list):
        return ()
    manual: list[ManualItem] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        rule_id = item.get("rule_id")
        if _item_fully_fixed(item, fixed_changes):
            continue
        file, line, snippet = _manual_evidence(item)
        manual.append(ManualItem(str(item.get("id", "")), str(rule_id), str(item.get("priority", "")), str(item.get("message", "")), file, line, snippet, _manual_actions(item)))
    return tuple(manual)


def automation_payload(plan: fix_planner.FixPlan) -> JsonMap:
    return {
        "eligible": plan.automation.eligible,
        "operation_ids": [op_id for op_id in plan.automation.operation_ids],
        "reason": plan.automation.reason,
        "postchecks": [check for check in plan.automation.postchecks],
        "operation_proofs": [
            {
                "id": op.id,
                "before_hash": op.before_hash,
                "edits": [asdict(edit) for edit in op.edits],
                "preconditions": ["plain .R file", "balanced standalone R Markdown fence pair", "Rscript parse postcheck available"],
                "postchecks": [check for check in op.postchecks],
            }
            for op in plan.operations
        ],
    }


def require_postchecks(root: Path, plan: fix_planner.FixPlan) -> None:
    if not fix_planner.postcheck(root, plan):
        raise ApplyValidationError("safe-auto postcheck failed; reviewed source was not published")


def _manual_evidence(item: Mapping[str, JsonValue]) -> tuple[str | None, int | None, str]:
    evidence = item.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return None, None, ""
    first = evidence[0]
    if not isinstance(first, Mapping):
        return None, None, ""
    file = first.get("file")
    line = first.get("line")
    snippet = first.get("snippet")
    return file if isinstance(file, str) else None, line if isinstance(line, int) else None, snippet if isinstance(snippet, str) else ""


def _manual_actions(item: Mapping[str, JsonValue]) -> tuple[str, ...]:
    rule_id = item.get("rule_id")
    if isinstance(rule_id, str):
        known = {
            "B9-suppressed-data-load": "Make data-load failures visible by removing only the quietly prefix.",
            "B11-rmd-chunk-in-r": "Remove or comment only paired standalone R Markdown fence markers in the .R file.",
            "C10-no-runtime-code-fetch": "Vendor runtime-installed code inside the replication dataset and remove the install command.",
            "C11-no-external-adopath": "Point adopath/sysdir only at vendored package-local code.",
        }.get(rule_id)
        if known is not None:
            return (known,)
    rewrite = item.get("rewrite")
    if isinstance(rewrite, Mapping):
        prompt = rewrite.get("fix_prompt")
        if isinstance(prompt, str) and prompt:
            return (prompt,)
    target = item.get("target_form")
    if isinstance(target, str) and target:
        return (target,)
    return ()


def _item_fully_fixed(item: Mapping[str, JsonValue], fixed_changes: tuple[LineChange, ...]) -> bool:
    rule_id = item.get("rule_id")
    if not isinstance(rule_id, str):
        return False
    expected = {
        "B9-suppressed-data-load": "B9-suppressed-data-load",
        "B11-rmd-chunk-in-r": "B11-rmd-chunk-in-r",
        "C10-no-runtime-code-fetch": "ADO-ssc_install",
        "C11-no-external-adopath": "ADO-external_adopath",
    }.get(rule_id)
    evidence = item.get("evidence")
    if expected is None or not isinstance(evidence, list) or not evidence:
        return False
    fixed = {(c.file, c.line, c.old.strip(), c.rule_id) for c in fixed_changes}
    for ev in evidence:
        if not isinstance(ev, Mapping):
            return False
        file = ev.get("file")
        line = ev.get("line")
        snippet = ev.get("snippet")
        if not isinstance(file, str) or not isinstance(line, int) or not isinstance(snippet, str):
            return False
        if (file, line, snippet.strip(), expected) not in fixed:
            return False
    return True


def build_diff(root: Path, changes: tuple[LineChange, ...], copied: tuple[CopyEvidence, ...]) -> str:
    chunks: list[str] = []
    for rel in sorted({c.file for c in changes}):
        original = _safe_relative_target(root, rel).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        patched = list(original)
        for change in (c for c in changes if c.file == rel):
            _replace_line(patched, change)
        chunks.append("".join(difflib.unified_diff(original, patched, fromfile=f"a/{rel}", tofile=f"b/{rel}")))
    for evidence in copied:
        chunks.append(f"COPY {evidence.path} sha256={evidence.sha256} source={evidence.source}\n")
    return "".join(chunks)


def apply_review_changes(root: Path, dest: Path, changes: tuple[LineChange, ...], copied: tuple[CopyEvidence, ...]) -> None:
    copy_review_source(root, dest)
    apply_review_mutations(dest, changes, copied)


def copy_review_source(root: Path, dest: Path) -> None:
    _ = shutil.copytree(root, dest)


def apply_review_mutations(dest: Path, changes: tuple[LineChange, ...], copied: tuple[CopyEvidence, ...]) -> None:
    for rel in sorted({c.file for c in changes}):
        target = _safe_relative_target(dest, rel)
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        for change in (c for c in changes if c.file == rel):
            _replace_line(lines, change)
        target.write_text("".join(lines), encoding="utf-8")
    for evidence in copied:
        source = _safe_existing_file(Path(evidence.source))
        if _sha256(source) != evidence.sha256:
            raise StalePlanError(f"vendor source changed: {source}")
        target = _safe_relative_target(dest, evidence.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        _ = target.write_bytes(source.read_bytes())


def plan_fingerprint(changes: tuple[LineChange, ...], copied: tuple[CopyEvidence, ...], manual: tuple[ManualItem, ...], automation: JsonMap | None = None) -> str:
    return _hash_json(
        {
            "changes": [asdict(c) for c in changes],
            "copied_files": [asdict(c) for c in copied],
            "manual_items": [asdict(m) for m in manual],
            "automation": automation or {},
        }
    )


def _copy_evidence(entry: Mapping[str, object]) -> tuple[CopyEvidence, ...]:
    root = Path(str(entry["root"]))
    rels = entry["files"]
    if not isinstance(rels, list):
        return ()
    out: list[CopyEvidence] = []
    for raw_rel in rels:
        rel = str(raw_rel)
        try:
            safe_rel = ado_vendor.safe_manifest_rel(rel)
            source = ado_vendor.safe_manifest_file(root, safe_rel)
        except ado_vendor.UnsafeVendorPathError as exc:
            raise UnsafePathError(str(exc)) from exc
        source = _safe_existing_file(source)
        out.append(CopyEvidence(f"{ado_vendor.VENDOR_DIR}/{safe_rel}", str(source), str(entry["package"]), _sha256(source), source.stat().st_size))
    return tuple(out)


def _ado_line_change(root: Path, issue: ado_vendor.Issue) -> LineChange:
    path = _safe_relative_target(root, issue.file)
    old = path.read_text(encoding="utf-8", errors="replace").splitlines()[issue.line - 1]
    if issue.kind == "ssc_install":
        new = f"* {ado_vendor.MARK} vendored into {ado_vendor.VENDOR_DIR}/, was: {old.strip()}"
    else:
        indent = old[: len(old) - len(old.lstrip())]
        new = f'{indent}adopath ++ "{ado_vendor.VENDOR_DIR}" // {ado_vendor.MARK} was: {old.strip()}'
    return LineChange(issue.file, issue.line, old, new, f"ADO-{issue.kind}", "vendor Stata add-on code inside the replication dataset")


def _replace_line(lines: list[str], change: LineChange) -> None:
    if not 1 <= change.line <= len(lines):
        raise ApplyValidationError(f"line out of range for {change.file}:{change.line}")
    current = lines[change.line - 1].rstrip("\r\n")
    if current != change.old:
        raise ApplyValidationError(f"stale line for {change.file}:{change.line}")
    ending = lines[change.line - 1][len(current):]
    lines[change.line - 1] = change.new + ending


def _safe_relative_target(root: Path, rel: str) -> Path:
    pure = PurePosixPath(rel)
    if pure.is_absolute() or ".." in pure.parts or rel in {"", "."}:
        raise UnsafePathError(f"unsafe relative path: {rel}")
    target = (root / Path(*pure.parts)).resolve(strict=False)
    if not _is_within(target, root):
        raise UnsafePathError(f"path escapes root: {rel}")
    return target


def _safe_existing_file(path: Path) -> Path:
    resolved = path.resolve()
    if path.is_symlink() or not resolved.is_file() or not stat.S_ISREG(resolved.stat().st_mode):
        raise UnsafePathError(f"not a plain file: {path}")
    return resolved


def _tree_files(root: Path) -> list[JsonValue]:
    files: list[JsonValue] = []
    # Match entries_fingerprint's ordering of relative path strings. Path
    # component ordering differs for a directory beside its .zip archive.
    paths = (p for p in root.rglob("*") if p.is_file())
    for path in sorted(paths, key=lambda p: p.relative_to(root).as_posix()):
        files.append({"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": _sha256(path), "size_bytes": path.stat().st_size})
    return files


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_json(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _file_row(item: JsonValue) -> FileRow:
    if not isinstance(item, Mapping):
        raise ApplyValidationError("architecture file row is not an object")
    path = item.get("path")
    sha256 = item.get("sha256")
    size_bytes = item.get("size_bytes")
    if not isinstance(path, str) or not isinstance(sha256, str) or not isinstance(size_bytes, int):
        raise ApplyValidationError("architecture file row has invalid fields")
    return {"path": path, "sha256": sha256, "size_bytes": size_bytes}


def _mutable_json(advisory: Mapping[str, JsonValue]) -> dict[str, object]:
    return {str(key): value for key, value in advisory.items()}
