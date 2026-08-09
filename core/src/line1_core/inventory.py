from __future__ import annotations

from typing import Any

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path

_LANG_BY_SUFFIX = {
    ".do": "stata",
    ".ado": "stata",
    ".sas": "sas",
    ".r": "r",
    ".rmd": "r",
    ".py": "python",
    ".ipynb": "python",
    ".dta": "data",
    ".csv": "data",
    ".tab": "data",
    ".rds": "data",
    ".rdata": "data",
    ".xlsx": "data",
    ".parquet": "data",
    ".pdf": "doc",
    ".md": "doc",
    ".txt": "doc",
    ".tex": "doc",
}

_SKIP_DIRS = {".git", ".github", "__pycache__", ".ipynb_checkpoints", "renv", ".Rproj.user"}

# Shared UNC absolute-path sub-pattern. A real UNC path is \\host\share\...: two backslashes, a
# hostname, then a path separator. The hostname class starts with [\w] (letter/digit/underscore) so
# an IP host like \\192.168.1.5\share still matches; requiring the trailing separator excludes LaTeX
# macros in R string literals ("\\tau", "\\alpha") and regex-escape literals (gsub("\\|")), which are
# two backslashes + a token with NO separator (issue #19). Imported by rule_engine._ABS_PATH — the
# ONE absolute-path regex; venue_engine consumes rule_engine.abs_path_hits rather than scanning (#42).
_UNC_ABS = r'\\\\[\w][\w.-]*[\\/]'


@dataclass(frozen=True)
class FileEntry:
    path: str
    language: str
    size_bytes: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _language_of(path: Path) -> str:
    return _LANG_BY_SUFFIX.get(path.suffix.lower(), "other")


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan(root: Path) -> list[FileEntry]:
    root = root.resolve()
    entries: list[FileEntry] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        entries.append(
            FileEntry(
                path=str(path.relative_to(root)),
                language=_language_of(path),
                size_bytes=path.stat().st_size,
                sha256=_sha256_of(path),
            )
        )
    return entries


def code_entries(entries: list[FileEntry]) -> list[FileEntry]:
    return [e for e in entries if e.language in {"stata", "r", "python"}]


def _ipynb_cells(raw: str) -> list[tuple[str, str]] | None:
    """(cell_type, source) pairs from notebook JSON, or None when the structure is not a readable
    notebook — the caller then falls back to the raw text rather than crashing or silently dropping
    a real path (anti-bypass on malformed notebooks, issue #34). Handles nbformat 4 (cells[].source)
    and nbformat 3 (worksheets[].cells[].input)."""
    try:
        nb = json.loads(raw)
        if not isinstance(nb, dict):
            return None
        cells = nb.get("cells")
        if not isinstance(cells, list):  # nbformat 3: cells nested under worksheets[]
            cells = []
            for ws in (nb.get("worksheets") or []):
                if isinstance(ws, dict) and isinstance(ws.get("cells"), list):
                    cells.extend(ws["cells"])
        out: list[tuple[str, str]] = []
        for cell in cells:
            if not isinstance(cell, dict):
                continue
            src = cell.get("source")
            if src is None:
                src = cell.get("input")  # nbformat 3 key
            if isinstance(src, list):
                out.append((str(cell.get("cell_type", "")), "".join(str(s) for s in src)))
            elif isinstance(src, str):
                out.append((str(cell.get("cell_type", "")), src))
        return out
    except (ValueError, TypeError, AttributeError):
        return None


def read_source(root: Path, rel: str) -> str:
    """Source text of a code file for pattern scanning. For a Jupyter .ipynb this returns the cell
    SOURCES (code + markdown + raw, newline-joined), not the raw notebook JSON — so a scanner never
    sees the JSON-escaped `\\n`/`\\t` that fabricate fake Windows paths (a comment ending in a colon
    reads as `e:\\n`, matching the drive-letter branch — issue #34). Any structural surprise falls
    back to the raw text rather than crashing or silently dropping a real path."""
    p = root / rel
    try:
        raw = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if p.suffix.lower() != ".ipynb":
        return raw
    cells = _ipynb_cells(raw)
    if cells is None:
        return raw
    return "\n".join(src for _t, src in cells)


def read_source_anchored(root: Path, rel: str) -> str:
    """Like read_source, but every line of a NON-code notebook cell (markdown/raw) is prefixed with
    `#`. A markdown exhibit header (`## Table 1`) still matches the anchor regexes (their `#+` branch
    absorbs the extra hash), while markdown PROSE can never satisfy a producer pattern or credit an
    export target — code quoted in prose is not runnable code, so it must not clear the gate
    (anti-bypass, issue #33). Byte-identical to read_source for non-notebook files."""
    p = root / rel
    try:
        raw = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if p.suffix.lower() != ".ipynb":
        return raw
    cells = _ipynb_cells(raw)
    if cells is None:
        return raw
    parts: list[str] = []
    for ctype, src in cells:
        if ctype == "code":
            parts.append(src)
        else:
            parts.append("\n".join("#" + ln for ln in src.splitlines()))
    return "\n".join(parts)


def _blank_sas_comments(text: str) -> str:
    """Blank SAS comments while preserving strings and line structure, so a path scanner never fires
    on a commented-out path (issue #32). SAS has two comment forms, BOTH multi-line: `/* ... */`
    block comments, and `* ...;` / `%* ...;` STATEMENT comments — valid only where a statement can
    start (after a `;` or at file start); elsewhere `*` is multiplication (`y = a\\n * 2;` must not
    be eaten). Newlines are always kept so line/column indices are unchanged; string contents
    ('...'/"..." with doubled-quote escapes) are preserved verbatim and never open a comment; a star
    comment's terminating `;` is KEPT so statement-boundary state stays consistent; `prev_code`
    advances only in code state so `x=1; /* .. */ * comment;` still strips. A file with an unmatched
    quote degrades fail-open: later comments are not blanked (possible over-flag, never under-flag)."""
    out = list(text)
    n = len(text)
    i = 0
    state = "code"
    prev_code = ""  # last non-space char seen while in code state; "" == start of file
    while i < n:
        ch = text[i]
        if state == "code":
            if ch == "/" and i + 1 < n and text[i + 1] == "*":
                state = "block"
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if ch == "*" and prev_code in ("", ";"):
                state = "star"
                out[i] = " "
                i += 1
                continue
            if ch == "%" and i + 1 < n and text[i + 1] == "*" and prev_code in ("", ";"):
                state = "star"
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if ch == "'":
                state = "squote"
            elif ch == '"':
                state = "dquote"
            if not ch.isspace():
                prev_code = ch
            i += 1
        elif state == "squote":
            if ch == "'":
                if i + 1 < n and text[i + 1] == "'":
                    i += 2  # doubled-quote escape stays inside the string
                    continue
                state = "code"
            i += 1
        elif state == "dquote":
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    i += 2
                    continue
                state = "code"
            i += 1
        elif state == "block":
            if ch == "*" and i + 1 < n and text[i + 1] == "/":
                out[i] = out[i + 1] = " "
                state = "code"
                i += 2
                continue
            if ch != "\n":
                out[i] = " "
            i += 1
        else:  # star
            if ch == ";":
                state = "code"
                prev_code = ";"  # terminator kept: the next `*` may open a new statement comment
            elif ch != "\n":
                out[i] = " "
            i += 1
    return "".join(out)


def _pdftotext(path: Path) -> str | None:
    """Extract text from a PDF via poppler's `pdftotext`, when available. Reading a document is not
    executing author code. Returns None on any failure (no poppler, extraction error) so the caller
    falls back gracefully — no hard dependency is introduced. Shared by venue_engine (README section
    checks) and rule_engine (reading a PDF README for LLM-provenance signals, issue #9)."""
    import shutil
    import subprocess

    exe = shutil.which("pdftotext")
    if exe is None:
        return None
    try:
        proc = subprocess.run([exe, "-q", str(path), "-"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None
