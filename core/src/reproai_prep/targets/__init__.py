"""Certification targets: what a downstream certification service requires of a package.

A target sits beside the venue profiles. Its rules (targets/<id>.yaml) add findings that only
matter for that service, and its overrides re-word, or drop, generic findings whose advice the
service contradicts. Prep never runs the service; a target only says what it will refuse.
"""

from __future__ import annotations

import importlib
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from ..dependency_graph import Edge
from ..inventory import FileEntry
from ..rule_engine import Finding

_DIR = Path(__file__).parent
TARGETS = ("certify",)

# How Certify's effect on a package ranks: anything here blocks closing.
BLOCKING_EFFECTS = ("refuse", "run_fails")


def load(target: str) -> dict[str, Any]:
    if target not in TARGETS:
        raise ValueError(f"unknown certification target {target!r}; known: {', '.join(TARGETS)}")
    return yaml.safe_load((_DIR / f"{target}.yaml").read_text(encoding="utf-8"))


def profile_versions() -> dict[str, str]:
    return {t: str(load(t).get("profile_version", "unknown")) for t in TARGETS}


def apply(target: str, root: Path, entries: list[FileEntry], edges: list[Edge],
          findings: list[Finding]) -> tuple[list[Finding], dict[str, Any]]:
    """The findings with the target's overrides applied and its own findings added, and the profile."""
    profile = load(target)
    overrides: dict[str, dict[str, Any]] = profile.get("overrides") or {}
    adjusted: list[Finding] = []
    for f in findings:
        o = overrides.get(f.rule_id)
        if o is None:
            adjusted.append(f)
        elif not o.get("suppress"):
            adjusted.append(replace(f, why_downstream=o.get("why_downstream", f.why_downstream),
                                    target_form=o.get("target_form", f.target_form), target=target,
                                    priority=o.get("priority", f.priority),
                                    target_effect=o.get("certify_effect", f.target_effect)))

    rules = {r["id"]: r for r in profile["rules"]}
    detectors = importlib.import_module(f".{target}", __name__)
    for rule_id, (evidence, rationale) in detectors.detect(root, entries, edges).items():
        r = rules[rule_id]
        adjusted.append(Finding(
            rule_id=rule_id, category=r["category"], kind=r["kind"], priority=r["priority"],
            message=r["rule"], evidence=evidence, rationale=rationale, source_lessons=[],
            why_downstream=r.get("why_downstream", ""), target_form=r.get("target_form", ""),
            lossless_note=r.get("lossless_note", ""), propose_only=bool(r.get("propose_only", False)),
            output_changing=bool(r.get("output_changing", False)),
            target=target, target_effect=r["certify_effect"],
        ))
    return adjusted, profile
