from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__, contribute, coordinator, inventory, targets
from . import certify_start as certify_start_mod
from . import fix_applier
from . import fix_planner
from . import gate as gate_mod
from . import handoff as handoff_mod
from . import notes as notes_mod
from . import rehearse as rehearse_mod

_REPORT_FILES = {
    "architecture_report": "architecture_report.json",
    "advisory_plan": "advisory_plan.json",
    "venue_compliance_report": "venue_compliance_report.json",
    "target_readiness_report": "target_readiness_report.json",
    "risk_register": "risk_register.json",
}


def _cmd_check(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    result = coordinator.check(root, args.venue, args.target)

    if args.out:
        out_dir = Path(args.out).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        for key, filename in _REPORT_FILES.items():
            payload = result[key]
            if payload is None:
                continue
            (out_dir / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    adv = result["advisory_plan"]["summary"]
    risk = result["risk_register"]["summary"]
    conflicts = result["adversarial_review"]["conflicts"]

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        bp = adv["by_priority"]
        kv = result["knowledge_versions"]
        print(f"reproai check — {root}")
        print(f"  knowledge: engine {kv['engine']}, rules {kv['rules_version']}")
        print(f"  advisory: {adv['total']} items "
              f"(P0={bp['P0']} P1={bp['P1']} P2={bp['P2']} P3={bp['P3']} P4={bp['P4']}; "
              f"{adv['defect']} defect / {adv['normalization']} normalization)")
        if result["venue_compliance_report"] is not None:
            vc = result["venue_compliance_report"]["summary"]
            print(f"  venue ({args.venue}): {vc['pass']} pass / {vc['fail']} fail / "
                  f"{vc['needs_author_action']} need author action")
        if result["target_readiness_report"] is not None:
            tr = result["target_readiness_report"]
            counts = ", ".join(f"{n} {effect}" for effect, n in tr["summary"].items() if n)
            print(f"  target ({tr['name']}, profile {tr['profile_version']}): {tr['status']}"
                  + (f" ({counts})" if counts else ""))
        print(f"  risk: {risk['blocker']} blocker / {risk['high']} high / "
              f"{risk['medium']} medium / {risk['low']} low")
        if conflicts:
            print(f"  adversarial review: {len(conflicts)} conflict(s) flagged")
        if args.out:
            print(f"  reports written to: {args.out}")
    return 0


def _cmd_fix(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    result = coordinator.check(root, args.venue, args.target)
    entries = inventory.scan(root)
    file_texts = {
        e.path: (root / e.path).read_text(encoding="utf-8", errors="replace")
        for e in inventory.code_entries(entries)
    }
    plan = fix_planner.build(result["advisory_plan"], file_texts)

    if not plan.edits:
        print("No auto-safe fixes available.")
        print(f"  {len(plan.skipped_propose_only)} advisory item(s) are propose-only — review and apply manually.")
        return 0

    diff = fix_applier.unified_diff(root, plan)
    if not args.apply:
        print(f"[dry-run] {len(plan.edits)} auto-safe edit(s) across {len({e.file for e in plan.edits})} file(s):")
        for e in plan.edits:
            print(f"  {e.file}:{e.line}  [{e.rule_id}] {e.reason}")
        print()
        print(diff)
        print("Run with --apply --out <DIR> to write fixes to a COPY (the original is never touched).")
        return 0

    if not args.out:
        print("error: --apply requires --out <DIR> (fixes are written to a copy, never in place)", file=sys.stderr)
        return 2
    try:
        dest = fix_applier.apply_to_copy(root, plan, Path(args.out))
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Applied {len(plan.edits)} auto-safe fix(es) to a copy at: {dest}")
    print(f"  {len(plan.skipped_propose_only)} propose-only item(s) left for manual review.")
    return 0


def _cmd_rehearse(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    interpreters = {}
    for spec in args.interpreter or []:
        name, _, path = spec.partition("=")
        interpreters["R" if name.lower() == "r" else name.lower()] = path
    try:
        report = rehearse_mod.rehearse(root, scripts=args.script, runs=args.runs, timeout=args.timeout,
                                       interpreters=interpreters, workdir=Path(args.workdir) if args.workdir else None,
                                       keep=args.keep)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["grade"] in {"identical", "numerically_close", "ran"} else 1
    print(f"reproai rehearse — {root} (a COPY was run; the original is untouched)")
    print(f"  order: {', '.join(report['run_order']) or '(no R or Python script)'}")
    print(f"  network denied by: {report['network_denied_by']}")
    for i, run in enumerate(report["runs"], start=1):
        for s in run["steps"]:
            state = "TIMED OUT" if s["timed_out"] else ("left " + ", ".join(s["cache_left"]) if s["cache_left"] else f"exit {s['exit_code']}")
            print(f"  run {i}: {s['script']}: {state} ({s['seconds']}s)")
            for h in s["hints"]:
                print(f"      {h['kind']}: {h['hint']}")
    for d in report["differences"] or []:
        extra = " (looks like a clock reading)" if d.get("looks_like_clock") else ""
        print(f"  differs between runs: {d['path']}: {d['difference']}{extra}")
    if report["not_rehearsed"]:
        print(f"  not rehearsed (Stata): {len(report['not_rehearsed'])} script(s)")
    print(f"  grade: {report['grade']} — {report['meaning']}")
    return 0 if report["grade"] in {"identical", "numerically_close", "ran"} else 1


def _cmd_handoff(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    rehearsal = json.loads(Path(args.rehearsal).read_text(encoding="utf-8")) if args.rehearsal else None
    try:
        h = handoff_mod.build(root, venue=args.venue, target=args.target, scripts=args.script, rehearsal=rehearsal,
                              out_dir=Path(args.out) if args.out else None)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.out:
        j, m = handoff_mod.write(h, Path(args.out))
        print(f"handoff written: {m} and {j.name}")
    if args.json:
        print(json.dumps(h, indent=2, ensure_ascii=False))
    elif not args.out:
        print(handoff_mod.markdown(h))
    return 0


def _cmd_certify_start(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    a = certify_start_mod.assess(root, venue=args.venue, online=not args.offline, no_changes=args.no_changes)
    if args.out:
        _, m = certify_start_mod.write(a, Path(args.out))
        print(f"written: {m}")
    if args.json:
        print(json.dumps(a, indent=2, ensure_ascii=False))
    elif not args.out:
        print(certify_start_mod.markdown(a))
    else:
        print(f"can start: {a['status']}")
    return 1 if a["status"] == "not_ready" else 0


def _cmd_notes(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    try:
        path = notes_mod.add(root, args.change, args.approved_by, dataset=args.dataset or "", version=args.version or "")
    except notes_mod.NotesError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"recorded in {path}")
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    code, report = gate_mod.gate_static(root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"reproai gate (static) — {root}")
        print(f"  expected artifacts: {report['expected_total']}  "
              f"with valid export: {report['with_export']}  missing: {len(report['missing_export'])}")
        for a in report["missing_export"]:
            print(f"  MISSING EXPORT  {a['artifact_id']:12s} [{a['kind']}]  {a['source_file']}:{a['header_line']}")
        print(f"  GATE {'PASS' if report['passed'] else 'FAIL'} (exit {code})")
    return code


def _cmd_outputs(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    code, report = gate_mod.verify_runtime(root, since_epoch=args.since)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"reproai outputs (runtime artifacts) — {root}")
        print(f"  expected: {report['expected_total']}  produced: {report['produced']}  "
              f"not produced: {len(report['not_produced'])}")
        for r in report["not_produced"]:
            print(f"  NOT PRODUCED  {r['artifact_id']:12s} [{r['kind']}]  {r['source_file']}"
                  f"  (valid_export={r['has_valid_export']})")
        print(f"  OUTPUTS {'PASS' if report['passed'] else 'FAIL'} (exit {code})")
    return code


def _cmd_verify_renamed(args: argparse.Namespace) -> int:
    # `verify` is the old name of `outputs`, kept for one release: the name suggested a check of
    # results against the paper, which Prep never makes.
    print("note: `reproai verify` is now `reproai outputs`; the old name will be removed in a later "
          "release.", file=sys.stderr)
    return _cmd_outputs(args)


def _cmd_map(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    report = coordinator.output_map(root, args.manuscript)
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    print(f"reproai map (advisory) — {root}")
    if report["status"] != "ok":
        print(f"  {report['status']}: {report.get('note', '')}")
        return 0
    s = report["summary"]
    print(f"  manuscript: {report['manuscript']}")
    print(f"  exhibits: {s['exhibits']}   package outputs: {s['package_outputs']}")
    print(f"  exhibits with no producing output: {s['exhibits_without_output']}")
    print(f"  outputs not used by any exhibit:   {s['outputs_without_exhibit']}")
    print(f"  panel/count mismatches:            {s['panel_mismatches']}")
    for e in report["exhibits_without_output"]:
        label = f" ({e['label']})" if e.get("label") else ""
        print(f"  NO OUTPUT   {e['kind'].title()} {e['number']}{label}: {', '.join(e['unmapped']) or '—'}")
    for p in report["panel_mismatches"]:
        print(f"  PANELS      Figure {p['number']}: {p['n_panels']} panel(s) drawn, {p['n_mapped']} mapped")
    print("  (advisory only — reproai never issues a reproducibility verdict)")
    if args.out:
        print(f"  report written to: {args.out}")
    return 0


def _cmd_readme(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    if args.render:
        return _render_readme(root, args.out)
    text = coordinator.readme_scaffold(root)  # default action: scaffold a draft
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote README scaffold to {args.out}")
    else:
        print(text)
    return 0


def _render_readme(root: Path, out: str | None) -> int:
    import shutil
    import subprocess

    src = next((p for p in root.iterdir() if p.is_file() and p.name.lower() == "readme.md"), None)
    if src is None:
        print("error: no README.md found at the package root to render.", file=sys.stderr)
        return 2
    dest = Path(out) if out else src.with_suffix(".pdf")
    exe = shutil.which("pandoc")
    if exe is None:
        print("pandoc not found. Install pandoc, then run:")
        print(f'  pandoc "{src.name}" -o "{dest.name}" --pdf-engine=xelatex')
        return 1
    proc = subprocess.run(
        [exe, str(src), "-o", str(dest), "--pdf-engine=xelatex"], capture_output=True, text=True
    )
    if proc.returncode != 0:
        print(f"error: pandoc failed: {proc.stderr.strip()[:200]}", file=sys.stderr)
        return 1
    print(f"Rendered {src.name} -> {dest}")
    return 0


def _cmd_contribute(args: argparse.Namespace) -> int:
    if args.venue:
        path = Path(args.venue)
        if not path.is_file():
            print(f"error: draft file not found: {path}", file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8", errors="replace")
        leaks = contribute.scrub_leaks(text)
        if leaks:  # a venue suggestion is about the journal, not your package — block, don't redact
            print("BLOCKED: the draft contains identifying content that must not be posted:")
            for lk in leaks:
                print(f"  {lk['label']}: {lk['match']}")
            print("Remove these (a venue suggestion needs no package data) and re-run.")
            return 1
        report = contribute.validate_venue_draft(text)
        if report["ok"]:
            dr = report["dry_run"] or {}
            print(f"OK: venue draft '{report['venue_id']}' is well-formed "
                  f"({dr.get('checks', 0)} checks; runs clean on a fixture).")
            print("Mechanical checks pass. A maintainer still verifies each check against your policy quotes.")
            return 0
        print(f"NOT READY: {len(report['errors'])} issue(s) in the venue draft:")
        for e in report["errors"]:
            print(f"  - {e}")
        return 1
    if args.scrub:
        path = Path(args.scrub)
        if not path.is_file():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2
        leaks = contribute.scrub_leaks(path.read_text(encoding="utf-8", errors="replace"))
        if not leaks:
            print("OK: no identifying content detected.")
            return 0
        print(f"Found {len(leaks)} item(s) to remove before contributing:")
        for lk in leaks:
            print(f"  {lk['label']}: {lk['match']}")
        return 1
    print("error: pass --venue <draft.yaml> to validate a venue draft, or --scrub <file>.", file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reproai",
        description="ReproAI Prep: audit and prepare a replication package. The static commands never run author code; rehearse runs a copy, and only when asked.",
    )
    parser.add_argument("--version", action="version", version=f"reproai {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="One-shot static self-check: scan + rules + venue -> JSON reports.")
    check.add_argument("path", help="Path to the replication package working directory.")
    check.add_argument("--venue", default=None, help="Venue profile id (e.g. aea).")
    check.add_argument("--target", default=None, choices=targets.TARGETS,
                       help="Certification target whose entry requirements to check (certify = IQSS Certify).")
    check.add_argument("--out", default=None, help="Directory to write the JSON reports.")
    check.add_argument("--json", action="store_true", help="Print the full result JSON to stdout.")
    check.set_defaults(func=_cmd_check)

    fix = sub.add_parser("fix", help="Apply auto-safe (semantics-preserving) fixes to a COPY. Dry-run by default.")
    fix.add_argument("path", help="Path to the replication package working directory.")
    fix.add_argument("--venue", default=None, help="Venue profile id (e.g. aea).")
    fix.add_argument("--target", default=None, choices=targets.TARGETS,
                     help="Certification target whose advice to follow (certify = IQSS Certify).")
    fix.add_argument("--apply", action="store_true", help="Write fixes to a copy (requires --out). Without this, dry-run.")
    fix.add_argument("--out", default=None, help="Destination directory for the fixed copy (must not exist).")
    fix.set_defaults(func=_cmd_fix)

    rehearse = sub.add_parser("rehearse", help="RUNS CODE, on a copy: run the entry scripts the way a certification service will (from the root, network denied, fixed settings), twice, and compare the outputs.")
    rehearse.add_argument("path", help="Path to the (prepared copy of the) replication package. It is copied; the given folder is never run.")
    rehearse.add_argument("--script", action="append", default=None, help="A script to run, relative to the root; repeat in run order. Default: the entry scripts, in path order.")
    rehearse.add_argument("--runs", type=int, default=2, help="1 for a smoke run, 2 (default) to compare two runs.")
    rehearse.add_argument("--timeout", type=int, default=rehearse_mod.DEFAULT_TIMEOUT, help="Seconds per script (default 3600).")
    rehearse.add_argument("--interpreter", action="append", default=None, metavar="R=PATH|python=PATH", help="The Rscript or python to use.")
    rehearse.add_argument("--workdir", default=None, help="Where to make the copies (default: the system temp folder).")
    rehearse.add_argument("--keep", action="store_true", help="Keep the run copies for inspection.")
    rehearse.add_argument("--out", default=None, help="Write the rehearsal report as JSON to this file.")
    rehearse.add_argument("--json", action="store_true", help="Print the full report as JSON.")
    rehearse.set_defaults(func=_cmd_rehearse)

    handoff = sub.add_parser("handoff", help="Where preparation stops: the run order, the libraries, what is still open, and the next steps for the chosen destination (a venue, IQSS Certify, or a manual deposit). Static.")
    handoff.add_argument("path", help="Path to the prepared copy.")
    handoff.add_argument("--venue", default=None, help="Venue profile id (e.g. aea).")
    handoff.add_argument("--target", default=None, choices=targets.TARGETS, help="Certification target (certify = IQSS Certify).")
    handoff.add_argument("--script", action="append", default=None, help="The approved run order, one script per flag.")
    handoff.add_argument("--rehearsal", default=None, help="A rehearsal report (reproai rehearse --out) to include.")
    handoff.add_argument("--out", default=None, help="Directory to write HANDOFF.md and handoff.json.")
    handoff.add_argument("--json", action="store_true", help="Print the handoff as JSON.")
    handoff.set_defaults(func=_cmd_handoff)

    cstart = sub.add_parser("certify-start", help="After preparation for IQSS Certify: check that Certify can start (static readiness, runtimes, the service and its published files) and write CERTIFY_START.md, the steps from your draft dataset's Certify button. Never runs Certify.")
    cstart.add_argument("path", help="Path to the prepared copy.")
    cstart.add_argument("--venue", default=None, help="Venue profile id (e.g. aea).")
    cstart.add_argument("--offline", action="store_true", help="Skip the service and checksum checks (no network).")
    cstart.add_argument("--no-changes", action="store_true", help="The author asked that nothing be changed: the steps say to tick the same box in Certify's form.")
    cstart.add_argument("--out", default=None, help="Directory to write CERTIFY_START.md and certify_start.json.")
    cstart.add_argument("--json", action="store_true", help="Print the result as JSON.")
    cstart.set_defaults(func=_cmd_certify_start)

    note = sub.add_parser("note", help="Record one approved repair in the prepared copy's CERTIFICATION-NOTES.txt.")
    note.add_argument("path", help="Path to the prepared copy.")
    note.add_argument("--change", required=True, help="The change, in one sentence.")
    note.add_argument("--approved-by", required=True, help="Who approved it (the author's name).")
    note.add_argument("--dataset", default=None, help="The replication dataset's name (written once, in the header).")
    note.add_argument("--version", default=None, help="Its version or draft identifier (written once).")
    note.set_defaults(func=_cmd_notes)

    gate = sub.add_parser("gate", help="HARD GATE: exit nonzero while any paper Table/Figure lacks a valid output export. The fix loop is done only when this exits 0.")
    gate.add_argument("path", help="Path to the (fixed copy of the) replication package.")
    gate.add_argument("--json", action="store_true", help="Print the full gate report as JSON.")
    gate.set_defaults(func=_cmd_gate)

    for name, func, help_text in (
        ("outputs", _cmd_outputs, "HARD GATE: after running the package, exit nonzero unless every expected Table/Figure output file actually exists, is non-empty (and fresh with --since)."),
        ("verify", _cmd_verify_renamed, "Old name of `outputs`, kept for one release."),
    ):
        outputs = sub.add_parser(name, help=help_text)
        outputs.add_argument("path", help="Path to the (run) fixed copy of the replication package.")
        outputs.add_argument("--since", type=float, default=None, help="Epoch seconds; require artifacts modified at/after this time (run freshness).")
        outputs.add_argument("--json", action="store_true", help="Print the full outputs report as JSON.")
        outputs.set_defaults(func=func)

    mapper = sub.add_parser("map", help="ADVISORY: overlay a manuscript's figures/tables on the package's output nodes (outputs with no exhibit, exhibits with no output, panel mismatches). LaTeX-only; never a verdict, never in `check`.")
    mapper.add_argument("path", help="Path to the replication package working directory.")
    mapper.add_argument("--manuscript", required=True, metavar="TEX", help="Path to the manuscript LaTeX source (.tex).")
    mapper.add_argument("--out", default=None, help="Write the full map report as JSON to this file.")
    mapper.add_argument("--json", action="store_true", help="Print the full map report as JSON.")
    mapper.set_defaults(func=_cmd_map)

    readme = sub.add_parser("readme", help="Scaffold a README draft from the package structure, or render README.md to PDF.")
    readme.add_argument("path", help="Path to the replication package working directory.")
    readme.add_argument("--scaffold", action="store_true", help="Print a README.md draft assembled from the package facts (default action).")
    readme.add_argument("--render", action="store_true", help="Render README.md to PDF via pandoc (or print the one-liner if pandoc is absent).")
    readme.add_argument("--out", default=None, help="Output file (scaffold: default stdout; render: default <path>/README.pdf).")
    readme.set_defaults(func=_cmd_readme)

    contrib = sub.add_parser("contribute", help="Vet a contribution before you file it: validate a drafted venue profile, or scrub a file for identifying content.")
    contrib.add_argument("--venue", default=None, metavar="DRAFT.yaml", help="Validate a drafted venues/<id>.yaml: schema, known detectors, a clean dry-run.")
    contrib.add_argument("--scrub", default=None, metavar="FILE", help="Report identifying content (absolute paths, emails) in a file before you post it.")
    contrib.set_defaults(func=_cmd_contribute)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
