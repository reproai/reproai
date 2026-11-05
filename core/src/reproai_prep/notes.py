"""CERTIFICATION-NOTES.txt: the record of every approved repair, kept inside the prepared copy.

IQSS Certify's instructions ask for one file at the prepared copy's root that names the
replication dataset and its version, the date, who approved, and each change in one sentence.
Prep writes it the same way whatever the destination, so a journal's data editor reads the same
account. Certify refuses any deposited text file that names its capture files or its salt file,
so those strings never reach the notes.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

NOTES_NAME = "CERTIFICATION-NOTES.txt"
# strings IQSS Certify's closing refuses in any deposited text file
RESERVED = (".certified/step-", "certified_salt.bin")


class NotesError(ValueError):
    pass


def _clean(text: str) -> str:
    one_line = " ".join(text.split())
    for token in RESERVED:
        if token in one_line:
            raise NotesError(f"a note may not contain {token!r}: IQSS Certify refuses a deposited file that names it")
    return one_line


def add(copy_root: Path, change: str, approved_by: str, dataset: str = "", version: str = "",
        today: _dt.date | None = None) -> Path:
    """Append one approved repair. The header (dataset, version) is written once, on first use."""
    if not change.strip() or not approved_by.strip():
        raise NotesError("a note needs the change and who approved it")
    path = copy_root / NOTES_NAME
    lines: list[str] = []
    if not path.exists():
        lines += [
            "Repairs made to prepare this replication dataset",
            f"Replication dataset: {_clean(dataset) or '[name]'}",
            f"Version: {_clean(version) or '[version or draft identifier]'}",
            "Each change below was shown to and approved by the author before it was made, in this",
            "prepared copy only; the author's original folder is unchanged.",
            "",
        ]
    when = (today or _dt.date.today()).isoformat()
    lines.append(f"- {when}, approved by {_clean(approved_by)}: {_clean(change)}")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return path


def read(copy_root: Path) -> list[str]:
    path = copy_root / NOTES_NAME
    if not path.exists():
        return []
    return [line[2:] for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- ")]
