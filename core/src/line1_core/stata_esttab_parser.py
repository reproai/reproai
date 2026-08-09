from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .inventory import FileEntry

_EXPORT = re.compile(
    r'^\s*(esttab|estout|outreg2?|putexcel|putdocx|tabout)\b[^\r\n]*?'
    r'(?:using\s+)?["\']?([^\s"\',]+\.(?:csv|rtf|tex|xlsx?|txt|doc|html))["\']?',
    re.IGNORECASE | re.MULTILINE,
)

_TABLE_TOKEN = re.compile(r'tab(?:le)?[\s_-]*([0-9]+[A-Za-z]?)', re.IGNORECASE)


@dataclass(frozen=True)
class TableExport:
    table: str
    source_file: str
    export_command: str
    line: int
    output_path: str


def _infer_table_name(output_path: str) -> str:
    match = _TABLE_TOKEN.search(Path(output_path).name)
    if match:
        return f"Table {match.group(1).upper()}"
    return Path(output_path).stem


def parse(root: Path, entries: list[FileEntry]) -> list[TableExport]:
    root = root.resolve()
    exports: list[TableExport] = []
    for entry in entries:
        if entry.language not in {"stata", "r"}:
            continue
        try:
            text = (root / entry.path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in _EXPORT.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            output_path = match.group(2)
            exports.append(
                TableExport(
                    table=_infer_table_name(output_path),
                    source_file=entry.path,
                    export_command=match.group(1).lower(),
                    line=line_no,
                    output_path=output_path,
                )
            )
    return exports
