from __future__ import annotations

from typing import Any

from dataclasses import dataclass

from .dependency_graph import Edge, _INCLUDE_KINDS
from .inventory import FileEntry


@dataclass(frozen=True)
class Orphans:
    referenced_missing: list[dict[str, Any]]
    present_unreferenced: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "referenced_missing": self.referenced_missing,
            "present_unreferenced": self.present_unreferenced,
        }


def detect(entries: list[FileEntry], edges: list[Edge]) -> Orphans:
    # referenced_missing is INCLUDE-level only: a do/source/import target that does not resolve.
    # Unresolved data reads are NOT piled in here — they are confidence-gated by A14, so a relative
    # read that is genuinely missing is a P0 while a dynamic/ambiguous one stays advisory.
    referenced_missing = [
        {"target": edge.dst, "referenced_by": edge.src}
        for edge in edges
        if edge.kind in _INCLUDE_KINDS and edge.status == "unresolved"
    ]

    code_paths = {e.path for e in entries if e.language in {"stata", "r", "python"}}
    referenced = {edge.dst for edge in edges if edge.kind in _INCLUDE_KINDS and edge.resolved}
    callers = {edge.src for edge in edges if edge.kind in _INCLUDE_KINDS}
    unreferenced = sorted(
        path for path in code_paths
        if path not in referenced and path not in callers
    )

    return Orphans(referenced_missing=referenced_missing, present_unreferenced=unreferenced)
