from __future__ import annotations

import difflib
import shutil
from collections import defaultdict
from pathlib import Path

from .fix_planner import FixPlan, LineEdit


def unified_diff(root: Path, plan: FixPlan) -> str:
    by_file: dict[str, list[LineEdit]] = defaultdict(list)
    for e in plan.edits:
        by_file[e.file].append(e)

    chunks: list[str] = []
    for file, edits in sorted(by_file.items()):
        original = (root / file).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        patched = list(original)
        for e in edits:
            if 1 <= e.line <= len(patched):
                trailing = "\n" if patched[e.line - 1].endswith("\n") else ""
                patched[e.line - 1] = e.new + trailing
        diff = difflib.unified_diff(original, patched, fromfile=f"a/{file}", tofile=f"b/{file}")
        chunks.append("".join(diff))
    return "".join(chunks)


def apply_to_copy(root: Path, plan: FixPlan, dest: Path) -> Path:
    root = root.resolve()
    dest = dest.resolve()
    if dest.exists():
        raise FileExistsError(f"refusing to overwrite existing destination: {dest}")
    shutil.copytree(root, dest)

    by_file: dict[str, list[LineEdit]] = defaultdict(list)
    for e in plan.edits:
        by_file[e.file].append(e)

    for file, edits in by_file.items():
        target = dest / file
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        for e in edits:
            if 1 <= e.line <= len(lines):
                trailing = "\n" if lines[e.line - 1].endswith("\n") else ""
                lines[e.line - 1] = e.new + trailing
        target.write_text("".join(lines), encoding="utf-8")
    return dest
