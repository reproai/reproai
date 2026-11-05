from __future__ import annotations

from typing import Any

from .rule_engine import Finding
from .venue_engine import Check


def cross_check(findings: list[Finding], checks: list[Check]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []

    rule_says_regroup = any(f.rule_id == "A2-table-grouping" for f in findings)
    venue_flat = any(
        c.check_id == "AEA-FILE-COUNT" and c.status != "pass" for c in checks
    )
    if rule_says_regroup and venue_flat:
        conflicts.append({
            "kind": "rule_vs_venue",
            "detail": "Rule line suggests reorganizing/splitting by table while the venue flags a file-count concern; "
                      "reconcile grouping with the venue's packaging limit before applying.",
            "rule_ids": ["A2-table-grouping"],
            "check_ids": ["AEA-FILE-COUNT"],
        })

    rule_abs = any(f.rule_id == "B4-no-abs-paths" for f in findings)
    venue_abs_pass = any(
        c.check_id == "AEA-NO-ABS-PATHS" and c.status == "pass" for c in checks
    )
    if rule_abs and venue_abs_pass:
        conflicts.append({
            "kind": "rule_vs_venue_inconsistency",
            "detail": "Rule line found absolute paths but the venue absolute-path check passed; "
                      "detectors disagree — inspect before auto-fixing.",
            "rule_ids": ["B4-no-abs-paths"],
            "check_ids": ["AEA-NO-ABS-PATHS"],
        })

    # Constraint: do not flag a nondeterministic build (C8) and ALSO tell the author to ship
    # raw-to-analysis code as the reproducibility path — an unseeded rebuild won't reproduce. The
    # reconciled counsel is: seed the draw AND/OR ship the constructed analysis file.
    rule_unseeded = any(f.rule_id == "C8-unseeded-stochastic" for f in findings)
    rederive_checks = [c.check_id for c in checks if getattr(c, "detector", "") == "rederive_from_raw"]
    if rule_unseeded and rederive_checks:
        conflicts.append({
            "kind": "rule_vs_venue",
            "detail": "An unseeded stochastic step (C8) makes a raw-to-analysis rebuild non-reproducible, "
                      "while the venue asks for raw-to-analysis code. Reconcile before advising: seed the "
                      "draw so the rebuild is reproducible, and/or ship the constructed analysis file "
                      "alongside the code — do not rely on an unseeded rebuild to reproduce the numbers.",
            "rule_ids": ["C8-unseeded-stochastic"],
            "check_ids": rederive_checks,
        })

    return conflicts


def audit_priorities(findings: list[Finding]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    valid_priority = {"P0", "P1", "P2", "P3", "P4"}
    valid_kind = {"defect", "normalization"}
    for f in findings:
        if f.priority not in valid_priority:
            violations.append({
                "kind": "invalid_priority",
                "rule_id": f.rule_id,
                "detail": f"priority '{f.priority}' is not P0..P4.",
            })
        if f.kind not in valid_kind:
            violations.append({
                "kind": "invalid_kind",
                "rule_id": f.rule_id,
                "detail": f"kind '{f.kind}' is not defect/normalization.",
            })
    return violations
