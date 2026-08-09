from __future__ import annotations

from typing import Any

from pathlib import Path

from . import dependency_graph, inventory, orphan_detector, output_map as _output_map, reports, rule_engine, stata_esttab_parser, venue_engine, versions
from .adversarial_reviewer import audit_priorities, cross_check


def check(root: Path, venue: str | None) -> dict[str, Any]:
    root = root.resolve()
    entries = inventory.scan(root)
    edges = dependency_graph.build(root, entries)
    exports = stata_esttab_parser.parse(root, entries)
    orphans = orphan_detector.detect(entries, edges)

    arch = reports.architecture_report(root, entries, edges, exports, orphans)
    arch["entry_points"] = dependency_graph.entry_points(entries, edges)

    findings = rule_engine.run(root, entries, edges, exports)
    advisory = reports.advisory_plan(root, findings)

    venue_block = None
    checks: list[venue_engine.Check] = []
    if venue:
        meta, checks = venue_engine.run(root, entries, venue, edges)
        venue_block = reports.venue_compliance_report(root, meta, checks)

    risk = reports.risk_register(root, advisory, checks)

    conflicts = cross_check(findings, checks)
    priority_violations = audit_priorities(findings)

    return {
        "knowledge_versions": versions.knowledge_versions(),
        "architecture_report": arch,
        "advisory_plan": advisory,
        "venue_compliance_report": venue_block,
        "risk_register": risk,
        "adversarial_review": {
            "conflicts": conflicts,
            "priority_violations": priority_violations,
        },
    }


def output_map(root: Path, manuscript: str) -> dict[str, Any]:
    """Overlay a manuscript's exhibit inventory on the package's output nodes. Advisory, LaTeX-only,
    kept OUT of check() so it can never affect the core's clean-pass credibility."""
    return _output_map.build(root.resolve(), manuscript)


def readme_scaffold(root: Path) -> str:
    """Assemble a README.md draft from the package's structure (file map, run order, table map,
    detected packages), with [CONFIRM] markers for author-only fields. Static; runs no author code."""
    root = root.resolve()
    entries = inventory.scan(root)
    edges = dependency_graph.build(root, entries)
    exports = stata_esttab_parser.parse(root, entries)
    return reports.readme_scaffold(root, entries, edges, exports)
