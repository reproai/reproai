"""`reproai map` — overlay a manuscript's exhibit inventory on the package's output (write) nodes.

Deliberately OUTSIDE `reproai check`: it must never threaten the core's clean-pass credibility. It is
advisory only, LaTeX-only in v1, and degrades gracefully (it reports what it could and could not map).
It never issues a verdict and never blocks. A clean map does NOT mean "this will reproduce."
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import GENERATED_BY, dependency_graph, inventory

_FLOAT_RE = re.compile(r'\\begin\{(figure|table)\*?\}(.*?)\\end\{\1\*?\}', re.DOTALL | re.IGNORECASE)
_INCLUDEGRAPHICS = re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')
_INPUT_RE = re.compile(r'\\(?:input|include)\{([^}]+)\}')
_LABEL_RE = re.compile(r'\\label\{([^}]+)\}')
_APPENDIX_RE = re.compile(r'\\appendix\b')
_GRAPHICS_EXT = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps", ".tikz", ".pgf")


def _extract_caption(body: str) -> str:
    idx = body.lower().find("\\caption")
    if idx == -1:
        return ""
    brace = body.find("{", idx)
    if brace == -1:
        return ""
    depth = 0
    out: list[str] = []
    for ch in body[brace:]:
        if ch == "{":
            depth += 1
            if depth == 1:
                continue
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        out.append(ch)
    cap = re.sub(r'\\[a-zA-Z]+\*?', '', "".join(out))
    cap = re.sub(r'[{}~]', '', cap)
    return re.sub(r'\s+', ' ', cap).strip()[:160]


def _exhibits(tex: str) -> list[dict[str, Any]]:
    appendix_at = (_APPENDIX_RE.search(tex).start() if _APPENDIX_RE.search(tex) else None)
    counters = {"figure": 0, "table": 0}
    appendix_letters = {"figure": 0, "table": 0}
    exhibits: list[dict[str, Any]] = []
    for m in _FLOAT_RE.finditer(tex):
        kind = m.group(1).lower()
        body = m.group(2)
        in_appendix = appendix_at is not None and m.start() >= appendix_at
        if in_appendix:
            appendix_letters[kind] += 1
            number = f"A{appendix_letters[kind]}"
        else:
            counters[kind] += 1
            number = str(counters[kind])
        graphics = _INCLUDEGRAPHICS.findall(body)
        inputs = _INPUT_RE.findall(body)
        label_m = _LABEL_RE.search(body)
        exhibits.append({
            "kind": kind,
            "number": number,
            "label": label_m.group(1) if label_m else None,
            "caption": _extract_caption(body),
            "in_appendix": in_appendix,
            "files": [f.strip() for f in graphics + inputs],
            "n_panels": len(graphics) if kind == "figure" else max(1, len(inputs)),
        })
    return exhibits


def _basename_alts(ref: str) -> set[str]:
    """The basenames a LaTeX file reference might resolve to. \\includegraphics often omits the
    extension, so a bare `fig1` is also tried as fig1.pdf / fig1.png / ..."""
    bn = Path(ref.replace("\\", "/")).name.lower()
    alts = {bn}
    if "." not in bn:
        alts |= {bn + ext for ext in _GRAPHICS_EXT}
    return alts


def build(root: Path, manuscript: str | Path) -> dict[str, Any]:
    root = root.resolve()
    man = Path(manuscript)
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_by": GENERATED_BY,
        "root": str(root),
        "manuscript": str(man),
        "advisory": True,
        "disclaimer": "Advisory map only. A clean map does NOT mean the package reproduces; "
                      "reproai never issues a reproducibility verdict.",
    }
    if not man.is_file():
        report["status"] = "manuscript_not_found"
        report["note"] = f"No manuscript at {man}."
        return report
    if man.suffix.lower() != ".tex":
        report["status"] = "unsupported_format"
        report["note"] = ("v1 parses LaTeX (.tex) only. For a PDF, point --manuscript at the .tex "
                          "source; PDF/.Rnw/.qmd/Word support is future work.")
        return report

    tex = man.read_text(encoding="utf-8", errors="replace")
    exhibits = _exhibits(tex)

    entries = inventory.scan(root)
    edges = dependency_graph.build(root, entries)
    write_outputs = {Path(e.dst).name.lower(): e.dst for e in edges if e.kind == "write"}
    present = {Path(e.path).name.lower(): e.path for e in entries}

    referenced: set[str] = set()
    exhibit_rows: list[dict[str, Any]] = []
    exhibits_without_output: list[dict[str, Any]] = []
    panel_mismatches: list[dict[str, Any]] = []

    for ex in exhibits:
        mapped: list[str] = []
        unmapped: list[str] = []
        for ref in ex["files"]:
            alts = _basename_alts(ref)
            hit = next((write_outputs[a] for a in alts if a in write_outputs), None) \
                or next((present[a] for a in alts if a in present), None)
            if hit:
                mapped.append(ref)
                referenced.add(Path(hit).name.lower())
            else:
                unmapped.append(ref)
        row = {"kind": ex["kind"], "number": ex["number"], "label": ex["label"],
               "caption": ex["caption"], "in_appendix": ex["in_appendix"],
               "n_panels": ex["n_panels"], "n_mapped": len(mapped), "unmapped": unmapped}
        exhibit_rows.append(row)
        if ex["files"] and not mapped:
            exhibits_without_output.append({"kind": ex["kind"], "number": ex["number"],
                                            "label": ex["label"], "unmapped": unmapped})
        elif ex["kind"] == "figure" and mapped and len(mapped) < ex["n_panels"]:
            panel_mismatches.append({"number": ex["number"], "label": ex["label"],
                                     "n_panels": ex["n_panels"], "n_mapped": len(mapped),
                                     "unmapped": unmapped})

    outputs_without_exhibit = sorted(out for bn, out in write_outputs.items() if bn not in referenced)

    report.update({
        "status": "ok",
        "summary": {
            "exhibits": len(exhibit_rows),
            "package_outputs": len(write_outputs),
            "exhibits_without_output": len(exhibits_without_output),
            "outputs_without_exhibit": len(outputs_without_exhibit),
            "panel_mismatches": len(panel_mismatches),
        },
        "exhibits": exhibit_rows,
        "exhibits_without_output": exhibits_without_output,
        "outputs_without_exhibit": outputs_without_exhibit,
        "panel_mismatches": panel_mismatches,
    })
    if not write_outputs:
        report["note"] = ("No write/output nodes found in the package graph, so exhibits could not be "
                          "mapped to producing code. This is a partial map, not a finding.")
    return report
