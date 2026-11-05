from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from . import ado_vendor


def apply_fixes(package_copy: Path, plan: ado_vendor.Plan) -> dict[str, Any]:
    if plan.unresolved:
        raise ValueError("plan has unresolved issues; refuse to apply a partial fix")
    files_added: list[dict[str, str]] = []
    for entry in plan.vendor:
        src_root = Path(entry["root"])
        for rel in entry["files"]:
            safe_rel = ado_vendor.safe_manifest_rel(str(rel))
            src = ado_vendor.safe_manifest_file(src_root, safe_rel)
            dest = ado_vendor.safe_vendor_target(package_copy, ado_vendor.VENDOR_DIR, safe_rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            files_added.append({"path": f"{ado_vendor.VENDOR_DIR}/{safe_rel}", "source": str(src),
                                "package": entry["package"]})

    lines_changed: list[dict[str, Any]] = []
    by_file: dict[str, list[Any]] = {}
    for issue in plan.rewrite:
        by_file.setdefault(issue.file, []).append(issue)
    for rel, file_issues in sorted(by_file.items()):
        path = package_copy / rel
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        for issue in file_issues:
            idx = issue.line - 1
            original = lines[idx]
            ending = original[len(original.rstrip("\r\n")):]
            body = original.rstrip("\r\n")
            if issue.kind == "ssc_install":
                replacement = f"* {ado_vendor.MARK} vendored into {ado_vendor.VENDOR_DIR}/, was: {body.strip()}"
            else:
                indent = body[: len(body) - len(body.lstrip())]
                replacement = (f'{indent}adopath ++ "{ado_vendor.VENDOR_DIR}" '
                               f"// {ado_vendor.MARK} was: {body.strip()}")
            lines[idx] = replacement + ending
            lines_changed.append({"file": rel, "line": issue.line,
                                  "before": body.strip(), "after": replacement.strip()})
        path.write_text("".join(lines), encoding="utf-8")

    changes = {
        "files_added": files_added,
        "lines_changed": lines_changed,
        "vendored_packages": sorted({e["package"] for e in plan.vendor}),
    }
    _write_record(package_copy, changes)
    return changes


def _write_record(package_copy: Path, changes: dict[str, Any]) -> None:
    lines = [
        "This package was prepared for certification. The analysis code is",
        "unchanged; code it used to fetch from the internet or load from",
        "outside the package was copied into .certified/lib/ and the loading lines were",
        "rewritten to point there.",
        "",
        "Lines rewritten:",
    ]
    for c in changes["lines_changed"]:
        lines.append(f"  {c['file']}:{c['line']}")
        lines.append(f"    was: {c['before']}")
        lines.append(f"    now: {c['after']}")
    lines.append("")
    lines.append("Files vendored into .certified/lib/:")
    for f in changes["files_added"]:
        lines.append(f"  {f['path']}  ({f['package']}, from {f['source']})")
    record = package_copy / ado_vendor.RECORD_NAME
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("\n".join(lines) + "\n", encoding="utf-8")
