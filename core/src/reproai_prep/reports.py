from __future__ import annotations

# noqa: SIZE_OK -- legacy report assembler; safe-auto adds one backward-compatible field.

import re
from pathlib import Path
from typing import Any

from . import GENERATED_BY
from . import fix_planner, inventory
from .dependency_graph import Edge
from .inventory import FileEntry
from .orphan_detector import Orphans
from .rule_engine import Finding
from .stata_esttab_parser import TableExport
from .venue_engine import Check

_CANNOT_PREDICT = [
    "Numerical match of coefficients (random seeds, solver behavior, hidden transforms surface only at execution).",
    "Full environment reconstruction (external repos / OS libraries / licensed software may still fail).",
    "Diagnostic fidelity (instrument strength, model classification need real outputs).",
    "Runtime completeness (long scripts, memory, encoding, platform differences are execution-time facts).",
    "Repository acceptance (external validation and human review may add rules).",
]

_DISCLAIMER = (
    "Pre-diagnose maximizes the probability that the downstream reproducibility check passes "
    "on the first try by removing known avoidable failures. It does NOT guarantee a first-try pass."
)

_SEVERITY_BY_PRIORITY = {"P0": "blocker", "P1": "high", "P2": "medium", "P3": "low", "P4": "low"}
_RISK_KIND_BY_CATEGORY = {
    "structural": "structural", "code-style": "structural",
    "environment": "environment", "normalization": "expected_output",
}


def architecture_report(root, entries, edges, exports, orphans) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_by": GENERATED_BY,
        "root": str(root),
        "files": [e.as_dict() for e in entries],
        "entry_points": [],
        "dependency_edges": [
            {"from": e.src, "to": e.dst, "kind": e.kind, "resolved": e.resolved,
             "status": e.status, "edge_class": e.edge_class} for e in edges
        ],
        "table_map": [
            {
                "table": x.table,
                "source_file": x.source_file,
                "export_command": x.export_command,
                "line": x.line,
                "output_path": x.output_path,
            }
            for x in exports
        ],
        "orphans": orphans.as_dict(),
    }


_PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}

# Universal lossless contract every host-LLM rewrite must honor, regardless of rule.
_LOSSLESS_CONTRACT = [
    "Work on a COPY of the replication dataset; never modify the author's original files.",
    "The rewrite MUST be semantics-preserving: the code must compute exactly the same "
    "results (same coefficients, same sample, same data, same file targets).",
    "Formatting / structural normalization is allowed (e.g. unrolling a foreach loop into "
    "explicit per-model commands, reflowing a call) — changing what the code computes is NOT.",
    "If you cannot make the change without risking a semantic change, do NOT apply it — leave "
    "it as a written recommendation for the author instead.",
]


def _evidence_lines(evidence: list[dict[str, Any]]) -> str:
    parts = []
    for e in evidence:
        loc = e.get("file", "?")
        if e.get("line") is not None:
            loc += f":{e['line']}"
        snip = e.get("snippet")
        parts.append(f"{loc}  {snip}" if snip else loc)
    return "; ".join(parts)


def _fix_prompt(f: Finding) -> str:
    """A self-contained natural-language rewrite directive for the host LLM."""
    mode = (
        "PROPOSE ONLY — do not rewrite this on your own (it is too semantic to rewrite safely): "
        "describe the fix to the author, and change code only if the author approves that exact change."
        if f.propose_only
        else "REWRITE — apply this fix to the copy, honoring the lossless contract."
    )
    lines = [
        f"[{f.rule_id} | {f.priority} | {f.kind}] {mode}",
        f"PROBLEM: {f.message}",
        f"WHERE: {_evidence_lines(f.evidence)}",
        f"WHY IT HURTS DOWNSTREAM: {f.why_downstream or f.rationale}",
        f"TARGET FORM: {f.target_form}",
    ]
    if f.output_changing:
        lines.append(
            "OUTPUT-CHANGING: applying this fix DELIBERATELY changes the realized output (e.g. a seed "
            "fixes new random draws). This is an explicit exception to the lossless contract — never "
            "auto-apply; the author must re-run and update the reported numbers."
        )
    if f.lossless_note:
        lines.append(f"LOSSLESS BOUNDARY FOR THIS RULE: {f.lossless_note}")
    return "\n".join(lines)


def advisory_plan(root, findings: list[Finding]) -> dict[str, Any]:
    ordered = sorted(findings, key=lambda f: _PRIORITY_ORDER.get(f.priority, 9))
    items = []
    for i, f in enumerate(ordered, start=1):
        items.append({
            "id": f"ADV-{i:03d}",
            "rule_id": f.rule_id,
            "category": f.category,
            "kind": f.kind,
            "priority": f.priority,
            "message": f.message,
            "evidence": f.evidence,
            "rationale": f.rationale,
            "source_lessons": f.source_lessons,
            "why_downstream": f.why_downstream,
            "target_form": f.target_form,
            "rewrite": {
                "mode": "propose_only" if f.propose_only else "llm_rewrite",
                "lossless_note": f.lossless_note,
                "output_changing": f.output_changing,
                "fix_prompt": _fix_prompt(f),
            },
        })
        if f.target:
            items[-1]["target"] = f.target
            if f.target_effect:
                items[-1]["target_effect"] = f.target_effect
    by_priority = {p: sum(1 for it in items if it["priority"] == p) for p in ["P0", "P1", "P2", "P3", "P4"]}
    automation = _automation_payload(root, items)
    return {
        "schema_version": 3,
        "generated_by": GENERATED_BY,
        "root": str(root),
        "lossless_contract": _LOSSLESS_CONTRACT,
        "automation": automation,
        "summary": {
            "total": len(items),
            "by_priority": by_priority,
            "defect": sum(1 for it in items if it["kind"] == "defect"),
            "normalization": sum(1 for it in items if it["kind"] == "normalization"),
            "llm_rewrite": sum(1 for it in items if it["rewrite"]["mode"] == "llm_rewrite"),
            "propose_only": sum(1 for it in items if it["rewrite"]["mode"] == "propose_only"),
        },
        "items": items,
    }


def _automation_payload(root: Path, items: list[dict[str, Any]]) -> dict[str, Any]:
    entries = inventory.scan(root)
    file_texts = {
        e.path: (root / e.path).read_text(encoding="utf-8", errors="replace")
        for e in inventory.code_entries(entries)
    }
    plan = fix_planner.build({"items": items}, file_texts)
    return {
        "eligible": plan.automation.eligible,
        "operation_ids": plan.automation.operation_ids,
        "reason": plan.automation.reason,
        "postchecks": plan.automation.postchecks,
    }


def venue_compliance_report(root, meta: dict[str, Any], checks: list[Check]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_by": GENERATED_BY,
        "root": str(root),
        "venue": meta["venue"],
        "profile_version": meta["profile_version"],
        "standard": meta.get("standard", ""),
        "summary": meta["summary"],
        "checks": [_venue_check_item(c) for c in checks],
    }


def _venue_check_item(c: Check) -> dict[str, Any]:
    item: dict[str, Any] = {
        "check_id": c.check_id,
        "requirement": c.requirement,
        "status": c.status,
        "detail": c.detail,
        "evidence": c.evidence,
        "source": c.source,
    }
    for field in ("author_action", "how", "self_check", "needs_detector"):
        value = getattr(c, field, "")
        if value:
            item[field] = value
    return item


# --- README scaffold (issue #3 item 2) ---------------------------------------------------------
# Emit a README.md DRAFT assembled from the structured facts the engine already computes (file map,
# run order, table->command map, detected packages), so the author edits a scaffold instead of
# commissioning one from scratch. Fields the static scan cannot know are marked [CONFIRM].

_PKG_R = re.compile(r'\b(?:library|require)\s*\(\s*["\']?([A-Za-z][\w.]*)')
_PKG_STATA = re.compile(r'\b(?:ssc\s+install|net\s+install)\s+(\w+)', re.IGNORECASE)
_PKG_PY = re.compile(r'^\s*(?:import|from)\s+([A-Za-z_]\w*)', re.MULTILINE)
_LANG_LABEL = {"r": "R", "stata": "Stata", "python": "Python", "sas": "SAS"}


def _file_role(path: str, language: str) -> str:
    name = Path(path).name.lower()
    if any(t in name for t in ("master", "run_all", "runall", "main", "00_", "_00")):
        return "master script (runs the full package)"
    if language == "data":
        return "data file"
    if language == "doc":
        return "documentation"
    if language in {"stata", "r", "python"}:
        if any(t in name for t in ("prepare", "clean", "build", "merge", "import", "01_", "1_")):
            return f"{_LANG_LABEL.get(language, language)} script (data preparation)"
        if any(t in name for t in ("analy", "estimat", "table", "figure", "result", "regress", "plot")):
            return f"{_LANG_LABEL.get(language, language)} script (analysis / outputs)"
        if any(t in name for t in ("function", "util", "helper", "lib")):
            return f"{_LANG_LABEL.get(language, language)} helper functions"
        return f"{_LANG_LABEL.get(language, language)} script"
    return language


def readme_scaffold(root, entries: list[FileEntry], edges: list[Edge], exports: list[TableExport]) -> str:
    from .dependency_graph import entry_points as _entry_points

    eps = _entry_points(entries, edges)
    scripts = [e for e in entries if e.language in {"stata", "r", "python"}]

    pkgs: set[str] = set()
    for e in scripts:
        try:
            text = (Path(root) / e.path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if e.language == "r":
            pkgs |= set(_PKG_R.findall(text))
        elif e.language == "stata":
            pkgs |= set(_PKG_STATA.findall(text))
        elif e.language == "python":
            pkgs |= set(_PKG_PY.findall(text))

    L: list[str] = []
    L.append("# Replication dataset for [CONFIRM: paper title]")
    L.append("")
    L.append("> Draft scaffolded by reproai from the replication dataset structure. Fields marked **[CONFIRM]** are")
    L.append("> author inputs the static scan cannot determine; fill them in and verify the rest.")
    L.append("")
    L.append("## Overview")
    L.append("[CONFIRM: one or two sentences on what the code does and what it produces.]")
    L.append("")
    L.append("## Data sources and availability")
    L.append("[CONFIRM: list each dataset with its source/citation and whether it is public.]")
    L.append("[CONFIRM: for any restricted dataset, note who owns it, why it is restricted, which scripts use it,")
    L.append(" which public file stands in for it here, and whether the published results can still be reproduced without it.]")
    L.append("")
    L.append("## Files")
    for e in sorted(entries, key=lambda x: x.path):
        if e.language in {"stata", "r", "python", "sas", "data", "doc"}:
            L.append(f"- `{e.path}` --- {_file_role(e.path, e.language)}")
    L.append("")
    L.append("## Software and dependencies")
    langs = sorted({e.language for e in scripts})
    lang_label = ", ".join(_LANG_LABEL.get(x, x) for x in langs) if langs else "[CONFIRM]"
    L.append(f"- Language(s) detected: {lang_label} --- [CONFIRM: exact version, e.g. R 4.4.2 / Stata 18]")
    if pkgs:
        L.append(f"- Packages detected: {', '.join(sorted(pkgs))} --- [CONFIRM: pin the versions used]")
    else:
        L.append("- Packages: [CONFIRM: list packages and the versions used]")
    L.append("- [CONFIRM: expected run-time, memory, and number of cores.]")
    L.append("")
    L.append("## How to run")
    if eps:
        for i, ep in enumerate(eps, start=1):
            L.append(f"{i}. Run `{ep['path']}` ({ep['reason']}).")
    else:
        L.append("[CONFIRM: state the run order --- a master script, or the numbered scripts in sequence.]")
        for e in sorted(scripts, key=lambda x: x.path):
            L.append(f"   - `{e.path}`")
    L.append("")
    if exports:
        L.append("## Results map")
        L.append("[CONFIRM the paper's table/figure number per row, and add a LaTeX label or log file if your venue asks for one.]")
        L.append("")
        L.append("| Output | Produced by | Saved to |")
        L.append("|---|---|---|")
        for x in sorted(exports, key=lambda t: str(t.table)):
            loc = f"{x.source_file}:{x.line}" if x.line else x.source_file
            out = f"`{x.output_path}`" if x.output_path else "[CONFIRM]"
            L.append(f"| {x.table} | `{loc}` | {out} |")
        L.append("")
    L.append("## License")
    L.append("[CONFIRM: state the license; include a LICENSE file in the replication dataset.]")
    L.append("")
    L.append("## Last verified")
    L.append("[CONFIRM: the date you last re-ran the whole package from a clean session, and that it reproduced these results.]")
    L.append("")
    L.append("## Notes")
    L.append("[CONFIRM: anything else a replicator needs --- seeds, hardware, known caveats.]")
    L.append("")
    return "\n".join(L)


def risk_register(root, advisory: dict[str, Any], checks: list[Check]) -> dict[str, Any]:
    risks = []
    idx = 1
    for item in advisory["items"]:
        sev = _SEVERITY_BY_PRIORITY.get(item["priority"], "medium")
        risks.append({
            "id": f"RISK-{idx:03d}",
            "severity": sev,
            "kind": _RISK_KIND_BY_CATEGORY.get(item["category"], "structural"),
            "message": item["message"],
            "predicts": item["rationale"],
            "evidence": [e["file"] for e in item["evidence"]],
            "from_advisory_ids": [item["id"]],
        })
        idx += 1
    for c in checks:
        if c.status == "fail":
            risks.append({
                "id": f"RISK-{idx:03d}",
                "severity": "blocker",
                "kind": "venue",
                "message": c.requirement,
                "predicts": c.detail,
                "evidence": c.evidence,
                "from_advisory_ids": [],
            })
            idx += 1

    summary = {"blocker": 0, "high": 0, "medium": 0, "low": 0}
    for r in risks:
        summary[r["severity"]] += 1

    return {
        "schema_version": 1,
        "generated_by": GENERATED_BY,
        "root": str(root),
        "disclaimer": _DISCLAIMER,
        "summary": summary,
        "risks": risks,
        "cannot_predict": _CANNOT_PREDICT,
    }


_TARGET_EFFECTS = ("refuse", "run_fails", "mark", "warning", "note")
_TARGET_DISCLAIMER = (
    "A static reading of the package against what the certification service is known to refuse, "
    "fail, mark or note. It runs no code and is not the service's verdict: only the service's own "
    "closing decides whether the package closes."
)


def target_readiness_report(root, profile: dict[str, Any], advisory: dict[str, Any]) -> dict[str, Any]:
    """One certification target's view of the advisory plan: its own findings by effect, and whether
    any of them stops the service from closing the package."""
    from .targets import BLOCKING_EFFECTS

    target = profile["target"]
    items = [
        {"advisory_id": it["id"], "rule_id": it["rule_id"], "effect": it["target_effect"],
         "priority": it["priority"], "message": it["message"], "evidence_count": len(it["evidence"])}
        for it in advisory["items"] if it.get("target") == target and it.get("target_effect")
    ]
    summary = {effect: sum(1 for it in items if it["effect"] == effect) for effect in _TARGET_EFFECTS}
    if any(summary[e] for e in BLOCKING_EFFECTS):
        status = "blocked"
    elif items:
        status = "needs_attention"
    else:
        status = "no_static_obstacle"
    return {
        "schema_version": 1,
        "generated_by": GENERATED_BY,
        "root": str(root),
        "target": target,
        "name": profile.get("name", target),
        "profile_version": str(profile.get("profile_version", "unknown")),
        "basis": profile.get("basis", {}),
        "status": status,
        "summary": summary,
        "items": items,
        "reworded_advice": sorted({it["rule_id"] for it in advisory["items"]
                                   if it.get("target") == target and not it.get("target_effect")}),
        "disclaimer": _TARGET_DISCLAIMER,
    }
