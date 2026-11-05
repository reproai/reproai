"""The handoff: where preparation stops, and what the next step needs.

Prep ends at a prepared copy. The handoff says what that copy is ready for and what is still
open, for the destination the author chose: a journal's own check (a venue), a certification
service (a target), or a manual deposit. For IQSS Certify it names the steps that only Certify's
own program may take (copying libraries in, declarations, recordings) and the commands to run
them; it never runs them.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any

from . import GENERATED_BY, coordinator, inventory, notes, rehearse
from .rule_engine import _R_LIB_CALL, _strip_comment_keep_strings

# R's base and recommended packages ship with R; Certify never copies them
_R_SHIPPED = {
    "base", "compiler", "datasets", "graphics", "grDevices", "grid", "methods", "parallel", "splines", "stats",
    "stats4", "tcltk", "tools", "utils", "boot", "class", "cluster", "codetools", "foreign", "KernSmooth",
    "lattice", "MASS", "Matrix", "mgcv", "nlme", "nnet", "rpart", "spatial", "survival",
}
_R_PACMAN = re.compile(r'\bp_load\s*\(([^)]*)\)')
_R_NAMESPACED = re.compile(r'(?<![\w.])([A-Za-z][\w.]*)::')
_PY_IMPORT = re.compile(r'^\s*(?:import\s+([\w.]+(?:\s*,\s*[\w.]+)*)|from\s+([\w.]+)\s+import\b)')
_OUTSIDE_FILE_RULES = ("B4-no-abs-paths", "CF5-climb-above-root", "CF6-network-read", "A14-missing-input")
_LEAVE_OUT_RULES = ("CF9-installation-folder", "CF10-startup-file")
_NOTEBOOK_RULES = ("CF2-notebook-only", "CF3-notebook-not-run")


def libraries(root: Path) -> dict[str, list[str]]:
    """Add-on libraries the scripts load, by language, from their text (a hint: a certification
    service finds the rest by running the scripts)."""
    entries = inventory.scan(root)
    local = {Path(e.path).stem for e in entries if e.path.endswith(".py")} | {p.name for p in root.rglob("*") if (p / "__init__.py").is_file()}
    found: dict[str, set[str]] = {"R": set(), "python": set()}
    for e in entries:
        if not e.path.lower().endswith((".r", ".py")):
            continue
        text = inventory.read_source(root, e.path)
        lang = "python" if e.path.endswith(".py") else "r"
        for line in text.splitlines():
            code = _strip_comment_keep_strings(line, lang)
            if lang == "r":
                found["R"].update(m.group(1) for m in _R_LIB_CALL.finditer(code))
                found["R"].update(m.group(1) for m in _R_NAMESPACED.finditer(code))
                for m in _R_PACMAN.finditer(code):
                    found["R"].update(x.strip().strip("'\"") for x in m.group(1).split(",") if "=" not in x and x.strip())
            else:
                m = _PY_IMPORT.match(code)
                if m:
                    names = m.group(1).split(",") if m.group(1) else [m.group(2)]
                    found["python"].update(n.strip().split(".")[0] for n in names if n.strip() and not n.strip().startswith("."))
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    return {
        "R": sorted(n for n in found["R"] if n and n not in _R_SHIPPED),
        "python": sorted(n for n in found["python"] if n and n not in stdlib and n not in local and n != "__future__"),
    }


def _evidence_files(items: list[dict[str, Any]], rule_ids: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    for it in items:
        if it["rule_id"] in rule_ids:
            for ev in it["evidence"]:
                where = ev["file"] + (f":{ev['line']}" if "line" in ev else "")
                if where not in out:
                    out.append(where)
    return out


def build(root: Path, venue: str | None = None, target: str | None = None, scripts: list[str] | None = None,
          rehearsal: dict[str, Any] | None = None) -> dict[str, Any]:
    root = root.resolve()
    result = coordinator.check(root, venue, target)
    items = result["advisory_plan"]["items"]
    order = rehearse.run_order(root, scripts)
    libs = libraries(root)
    readiness = result["target_readiness_report"]
    venue_block = result["venue_compliance_report"]

    open_items = [
        {"rule_id": it["rule_id"], "priority": it["priority"], "message": it["message"],
         **({"effect": it["target_effect"]} if it.get("target_effect") else {})}
        for it in items if it["priority"] in {"P0", "P1"}
    ]
    outside = _evidence_files(items, _OUTSIDE_FILE_RULES)
    services = _evidence_files(items, ("CF7-outside-service",))
    notebooks = _evidence_files(items, _NOTEBOOK_RULES)
    leave_out = _evidence_files(items, _LEAVE_OUT_RULES)
    restricted = _evidence_files(items, ("A10-commented-restricted-regression",))
    stata = _evidence_files(items, ("CF1-stata-not-runnable",))

    steps: list[dict[str, str]] = []
    if target == "certify":
        quoted = " ".join(f"--target {shlex.quote(s)}" for s in order) or "--target <script>"
        steps.append({"who": "you", "step": "Ask the author to approve the run order", "how": ", then ".join(order) or "(no R or Python script found)"})
        if stata:
            steps.append({"who": "author", "step": "Certify 0.2.0 does not run Stata", "how": "certify later, or leave the Stata scripts out and say so in CERTIFICATION-NOTES.txt"})
        steps.append({"who": "certify", "step": "Check the run order and what closing would refuse", "how": "certify targets <prepared copy>"})
        if libs["R"] or libs["python"]:
            steps.append({"who": "certify", "step": "Copy the libraries the scripts load into .certified/lib/",
                          "how": f"certify vendor <prepared copy> {quoted}"})
        if restricted:
            steps.append({"who": "author", "step": "Say which kind of confidential data this is (restricted, licensed, secure facility)",
                          "how": "then Certify's Step 2a: certify restrict, or certify declare --held"})
        if outside:
            steps.append({"who": "certify", "step": "Ship or declare each file read from outside the package", "how": "copy it in, or certify declare (Step 2)"})
        if services:
            steps.append({"who": "certify", "step": "Record the outside-service calls once", "how": f"certify record <prepared copy> {quoted} [--env-stdin KEY]"})
        steps.append({"who": "certify", "step": "Continue with Certify's own Step 3 (register) and Step 4 (close)",
                      "how": f"certify close <prepared copy> {quoted}; ReproAI Prep stops here"})
    else:
        if venue_block:
            pending = [c["requirement"] for c in venue_block.get("checks", []) if c.get("status") == "needs_author_action"]
            if pending:
                steps.append({"who": "author", "step": "Finish the venue items the engine cannot verify", "how": "; ".join(pending[:8])})
        steps.append({"who": "author", "step": "Deposit the prepared copy with the repository the journal names", "how": "include CERTIFICATION-NOTES.txt and the README"})

    return {
        "schema_version": 1,
        "generated_by": GENERATED_BY,
        "root": str(root),
        "destination": {"target": target, "venue": venue},
        "run_order": order,
        "libraries": libs,
        "readiness": {"status": readiness["status"], "summary": readiness["summary"]} if readiness else None,
        "rehearsal": {"grade": rehearsal["grade"], "meaning": rehearsal["meaning"],
                      "network_denied_by": rehearsal["network_denied_by"]} if rehearsal else None,
        "open_findings": open_items,
        "outside_files": outside,
        "outside_services": services,
        "notebooks": notebooks,
        "leave_out_of_prepared_copy": leave_out,
        "confidential_data_hints": restricted,
        "repairs_recorded": notes.read(root),
        "next_steps": steps,
        "boundary": ("ReproAI Prep stops at the prepared copy. It never runs a certification service's own steps "
                     "and never issues a reproducibility verdict."),
    }


def markdown(h: dict[str, Any]) -> str:
    lines = ["# Handoff", "", f"Package: `{h['root']}`"]
    dest = h["destination"]
    lines.append(f"Destination: {'IQSS Certify' if dest['target'] == 'certify' else (dest['venue'] or 'manual deposit')}")
    if h["readiness"]:
        lines.append(f"Static readiness: **{h['readiness']['status']}**")
    if h["rehearsal"]:
        lines.append(f"Rehearsal: **{h['rehearsal']['grade']}** ({h['rehearsal']['meaning']})")
    lines += ["", "## Run order", *[f"{i}. `{s}`" for i, s in enumerate(h["run_order"], 1)]]
    libs = h["libraries"]
    if libs["R"] or libs["python"]:
        lines += ["", "## Libraries the scripts load"]
        lines += [f"- R: {', '.join(libs['R'])}"] if libs["R"] else []
        lines += [f"- Python: {', '.join(libs['python'])}"] if libs["python"] else []
    for key, title in (("open_findings", "Still open (P0 and P1)"), ("outside_files", "Read from outside the package"),
                       ("outside_services", "Calls to outside services"), ("notebooks", "Notebooks"),
                       ("leave_out_of_prepared_copy", "Leave out of the prepared copy"),
                       ("confidential_data_hints", "Possibly confidential data"), ("repairs_recorded", "Repairs recorded")):
        values = h[key]
        if values:
            lines += ["", f"## {title}"]
            lines += [f"- {v['rule_id']} ({v['priority']}{', ' + v['effect'] if 'effect' in v else ''}): {v['message']}"
                      if isinstance(v, dict) else f"- {v}" for v in values]
    lines += ["", "## Next steps"]
    lines += [f"{i}. **{s['step']}** ({s['who']}): {s['how']}" for i, s in enumerate(h["next_steps"], 1)]
    lines += ["", f"_{h['boundary']}_", ""]
    return "\n".join(lines)


def write(h: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    j, m = out_dir / "handoff.json", out_dir / "HANDOFF.md"
    j.write_text(json.dumps(h, indent=2, ensure_ascii=False), encoding="utf-8")
    m.write_text(markdown(h), encoding="utf-8")
    return j, m
