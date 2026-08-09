"""Deterministic, code-level gates. Markdown cannot enforce anything; these exit nonzero.

- expected_artifacts(): for every Table N / Figure N section in the package, one record with
  whether it has a VALID export (an export command, inside that section, writing under
  output/tables or output/figures). A misnamed/elsewhere export does NOT count.
- gate_static(): exits nonzero while any expected artifact lacks a valid export. The fix loop
  is "done" only when this returns zero — not when a host LLM says so.
- verify_runtime(): after the package is run, checks each expected artifact's output file
  actually exists, is non-empty, and was modified after a start time. Exits nonzero otherwise.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from . import inventory
from .code_parse import (
    _TABLE_HEADER, _FIGURE_HEADER, _section_spans, _is_estimation, _GRAPH_CMD,
    _TABLE_EXPORT, _GRAPH_EXPORT, _mask_r_strings_comments,
    _PY_TABLE_BODY, _PY_GRAPH_BODY, _PY_TABLE_EXPORT,
    _toplevel_estimation_lines, _toplevel_graph_line,
    _toplevel_estimations_needing_table,
    _call_unit_from, _strip_label_opts,
)

# A VALID export must write under a designated `tables/`/`figures/` subfolder. Requiring that SEGMENT
# (not a bare filename) is what stops the "inject a misnamed esttab to silence the finding" bypass:
# `esttab using "mytable.csv"` has no `tables/` segment and still does not count.
#
# Follow-up D (recommend≡detect): broadened from the literal `output/tables(figures)/` to an optional
# leading path prefix `(?:[\w.\-]+[\\/])*`, matching rule_engine._OUT_TABLE_PATH/_OUT_FIGURE_PATH and
# the inline target-extractor in _section_export_targets below — so `output/tables/`,
# `results/tables/`, and bare `tables/` all satisfy D1 and the gate identically.
#
# Follow-up D fix: a left boundary `(?:^|[\\/])` prevents `.search` matching `tables/` as a SUBSTRING
# of a longer dir name (`mytables/`, `notes_tables/`, `vegetables/`, ...). The inline regex in
# _section_export_targets below is already quote-anchored (`["\']` before the path), so it is correct
# as-is and intentionally NOT changed; these two constants needed the boundary to match it.
_OUT_TABLE = re.compile(r'(?:^|[\\/])(?:[\w.\-]+[\\/])*tables[\\/]', re.IGNORECASE)
_OUT_FIGURE = re.compile(r'(?:^|[\\/])(?:[\w.\-]+[\\/])*figures[\\/]', re.IGNORECASE)

# A path SEGMENT in the gate's quote-anchored export extractor that may be a macro (${ROOT}, $ROOT,
# `c(pwd)') or a plain directory name. Each alternative forbids '/', so a macro substitutes for
# exactly ONE path component and can never swallow or fabricate the required tables//figures/ segment.
# This keeps the anchor+segment anti-bypass intact while crediting the macro-anchored export paths
# that A9-nested-cd itself steers authors toward (issue #35). D1's own .search()-form _OUT_TABLE_PATH
# already tolerates the prefix, so only the gate's stricter extractor needed this.
_MACRO_SEG = r'(?:\$\{[^}/]*\}|\$\w+|`[^`\n/]*\'|[\w.\-]+)'


@dataclass
class Artifact:
    artifact_id: str          # e.g. "Table 3" / "Figure 2"
    kind: str                 # "table" | "figure"
    source_file: str
    header_line: int
    has_valid_export: bool     # an export under output/{tables,figures} inside this section
    export_targets: list[str]  # the output/... paths this section writes (if any)


_STR_LIT = re.compile(r'''^["']([^"']*)["']$''')
_PATH_BUILDER = re.compile(
    r'\b(file\.path|paste0|paste)\s*\(([^()]*)\)', re.IGNORECASE)


def _split_top_args(arg_text: str) -> list[str]:
    parts, depth, cur = [], 0, []
    for ch in arg_text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur).strip())
    return parts


def _eval_literal_path_builders(text: str) -> str:
    """Issue #50: fold `paste("figures","f.pdf",sep="/")` / `file.path("figures","f.pdf")` /
    `paste0(...)` whose arguments are ALL string literals into a single quoted literal, so the
    quote-anchored extractor can read the computed path. If ANY argument is a variable/call/named
    option other than `sep=`, we leave the call untouched (extract nothing) — a wrongly-guessed
    path could otherwise be credited. Default `paste` sep is a SPACE, applied verbatim (so
    `paste("a","b")` becomes "a b", which simply will not be found — the safe, false-negative side)."""
    def repl(m: re.Match[str]) -> str:
        fn = m.group(1).lower()
        args = _split_top_args(m.group(2))
        sep = "" if fn == "paste0" else ("/" if fn == "file.path" else " ")
        literals: list[str] = []
        for a in args:
            sm = re.match(r'sep\s*=\s*(["\'][^"\']*["\'])', a, re.IGNORECASE)
            if sm and fn != "file.path":
                inner = _STR_LIT.match(sm.group(1))
                sep = inner.group(1) if inner else sep
                continue
            lit = _STR_LIT.match(a)
            if not lit:
                return m.group(0)  # a non-literal argument: bail, change nothing
            literals.append(lit.group(1))
        return '"' + sep.join(literals) + '"'
    return _PATH_BUILDER.sub(repl, text)


_SETWD = re.compile(r'\bsetwd\s*\(\s*(.*?)\s*\)', re.IGNORECASE)


def _literal_setwd_prefix(text: str) -> tuple[str, bool]:
    """Issue #51: fold LITERAL `setwd("results")` calls, in scan order, into one relative prefix so
    an export written after them (`ggsave("figures/f.pdf")`) is looked for at
    `results/figures/f.pdf` — the ONE explicit candidate, never a `**/` search (which the freshness
    check cannot make safe: a same-named file elsewhere could be wrongly credited). Returns
    (prefix, dynamic): `dynamic=True` when any `setwd(var)` / non-literal / absolute call appears, in
    which case we do NOT guess a prefix and the caller should treat the count as best-effort."""
    prefix = Path()
    dynamic = False
    for m in _SETWD.finditer(text):
        lit = _STR_LIT.match(m.group(1).strip())
        if not lit:
            dynamic = True
            continue
        arg = lit.group(1).replace("\\", "/")
        if arg.startswith("/") or re.match(r'^[A-Za-z]:', arg):
            dynamic = True
            continue
        prefix = prefix / arg
    return (prefix.as_posix() if prefix != Path() else ""), dynamic


def _section_export_targets(body: list[str], out_re: re.Pattern[str], cmd_re: re.Pattern[str]) -> list[str]:
    targets: list[str] = []
    i, n = 0, len(body)
    while i < n:
        masked = _mask_r_strings_comments(body[i])
        if not cmd_re.search(masked):
            i += 1
            continue
        # Issue #20: join the export command's whole (possibly multi-line) call before extracting
        # targets, so `texreg(..., file = "output/tables/x.txt")` with `file=` on a continuation line
        # is credited. Label-only options are stripped so a decoy path in a caption/note is not
        # recorded as an output target (which verify_runtime would then chase).
        # Follow-up D: broadened in lockstep with _OUT_TABLE/_OUT_FIGURE — an optional leading path
        # prefix before the required `tables/`/`figures/` segment, so `results/tables/x.csv` and bare
        # `tables/x.csv` count, while a bare filename (`mytable.csv`, no segment) still does not.
        unit, end = _call_unit_from(body, i)
        resolved = _eval_literal_path_builders(_strip_label_opts(unit))
        for m in re.finditer(r'["\']((?:' + _MACRO_SEG + r'[\\/])*(?:tables|figures)[\\/][^"\']+)["\']', resolved, re.IGNORECASE):
            targets.append(m.group(1).replace("\\", "/"))
        i = max(end, i + 1)
    return targets


def expected_artifacts(root: Path) -> list[Artifact]:
    root = root.resolve()
    out: list[Artifact] = []
    entries = inventory.scan(root)
    for e in inventory.code_entries(entries):
        if e.language not in {"stata", "r", "python"}:
            continue
        is_py = e.language == "python"
        # Anchored reader (issue #33): identical to read_text for .do/.R/.py; for .ipynb it joins
        # cell sources with markdown lines '#'-prefixed, so a `## Table 1` markdown anchor counts
        # but prose quoting an export path can never credit one.
        text = inventory.read_source_anchored(root, e.path)
        lines = text.splitlines()
        tbl_export = _PY_TABLE_EXPORT if is_py else _TABLE_EXPORT
        # Issue #51: a literal setwd("dir") in an R script relocates every later relative export;
        # add that ONE explicit directory prefix so verify looks at `dir/tables|figures/...`.
        sw_prefix = ""
        if e.language == "r":
            sw_prefix, _sw_dynamic = _literal_setwd_prefix(text)

        def _sw(tgts: list[str]) -> list[str]:
            if not sw_prefix:
                return tgts
            return [t if (t.startswith("/") or re.match(r'^[A-Za-z]:', t))
                    else f"{sw_prefix}/{t}" for t in tgts]

        table_spans = _section_spans(lines, _TABLE_HEADER)
        if table_spans:
            for label, start, end in table_spans:
                body = lines[start:end]
                if not any(_is_estimation(ln) or (is_py and _PY_TABLE_BODY.search(ln)) for ln in body):
                    continue
                tgts = _sw(_section_export_targets(body, _OUT_TABLE, tbl_export))
                out.append(Artifact(label, "table", e.path, start + 1, bool(tgts), tgts))
        elif not is_py:
            # no `* Table N` headers: an unlabeled script that builds a table is still one artifact,
            # UNLESS its estimations are already captured as a saved figure (issue #22) — then no
            # phantom table is demanded. Shares the D1 rule so the gate and D1 agree. Python is
            # labeled-anchor-only: no unlabeled fallback, else every helper .py becomes an artifact.
            tl = _toplevel_estimations_needing_table(text)
            if tl:
                tgts = _sw(_section_export_targets(lines, _OUT_TABLE, _TABLE_EXPORT))
                out.append(Artifact("Table (unlabeled)", "table", e.path, tl[0], bool(tgts), tgts))

        figure_spans = _section_spans(lines, _FIGURE_HEADER)
        if figure_spans:
            for label, start, end in figure_spans:
                body = lines[start:end]
                if not any(_GRAPH_CMD.search(ln) or (is_py and _PY_GRAPH_BODY.search(ln)) for ln in body):
                    continue
                tgts = _sw(_section_export_targets(body, _OUT_FIGURE, _GRAPH_EXPORT))
                out.append(Artifact(label, "figure", e.path, start + 1, bool(tgts), tgts))
        elif not is_py:
            gl = _toplevel_graph_line(text)
            if gl is not None:
                tgts = _sw(_section_export_targets(lines, _OUT_FIGURE, _GRAPH_EXPORT))
                out.append(Artifact("Figure (unlabeled)", "figure", e.path, gl, bool(tgts), tgts))
    return out


def gate_static(root: Path) -> tuple[int, dict[str, Any]]:
    arts = expected_artifacts(root)
    missing = [a for a in arts if not a.has_valid_export]
    report = {
        "gate": "static",
        "expected_total": len(arts),
        "with_export": len(arts) - len(missing),
        "missing_export": [asdict(a) for a in missing],
        "passed": len(missing) == 0,
    }
    return (0 if not missing else 1), report


def verify_runtime(root: Path, since_epoch: float | None = None) -> tuple[int, dict[str, Any]]:
    root = root.resolve()
    arts = expected_artifacts(root)
    produced: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for a in arts:
        ok_any = False
        detail = []
        for tgt in a.export_targets:
            fp = (root / tgt)
            exists = fp.is_file()
            size = fp.stat().st_size if exists else 0
            fresh = (exists and since_epoch is not None and fp.stat().st_mtime >= since_epoch) or (exists and since_epoch is None)
            ok = exists and size > 0 and fresh
            detail.append({"target": tgt, "exists": exists, "size": size, "fresh": fresh})
            ok_any = ok_any or ok
        rec = {"artifact_id": a.artifact_id, "kind": a.kind, "source_file": a.source_file,
               "has_valid_export": a.has_valid_export, "files": detail, "produced": ok_any}
        (produced if ok_any else failed).append(rec)
    report = {
        "gate": "verify",
        "expected_total": len(arts),
        "produced": len(produced),
        "not_produced": [r for r in failed],
        "passed": len(failed) == 0 and len(arts) > 0,
    }
    return (0 if report["passed"] else 1), report
