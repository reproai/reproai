# line1-core — Line 1 Pre-diagnose engine

Protocol-neutral, **static, no-execution** engine for the reproAI **Line 1 (pre-diagnose)** plugin.

It scans an author's working directory, applies an author rule set and a target-venue
profile, and emits JSON reports — **without running any of the author's code**. It is the
single core asset behind every distribution adapter (Claude Plugin, Codex plugin, CLI, MCP, Skill).

> This is **Line 1** only. The downstream **Line 2 reproducibility diagnosis** (which executes
> code, matches coefficients, certifies) is a separate SaaS and is out of scope here.

## What it does

| Step | Module | Output |
|---|---|---|
| File inventory + hashing | `inventory.py` | file list, languages, sizes |
| Dependency graph (static) | `dependency_graph.py` | `do`/`source`/`import` edges, entry points |
| Table↔command mapping | `stata_esttab_parser.py` | `esttab using "TableN"` → which commands build which table |
| Orphan detection | `orphan_detector.py` | referenced-but-missing, present-but-unreferenced |
| Rule line (author rules) | `rule_engine.py` | structural / code-style / environment findings |
| Compliance line (venue) | `venue_engine.py` | venue-compliance checklist |
| Adversarial cross-check | `adversarial_reviewer.py` | conflicts between rule line and compliance line |
| Report assembly | `reports.py` | 4 JSON reports |
| Orchestration + isolation | `coordinator.py` | runs the 5-agent static team in order |

## Reports emitted

- `architecture_report.json` — entry points, build order, dependency graph, orphans, table map
- `advisory_plan.json` — remediation items, each tagged `low` (auto-applicable) or `high` (propose-only)
- `venue_compliance_report.json` — per-requirement pass/fail against the venue profile
- `risk_register.json` — issues that would likely break a downstream reproducibility run

## Install & run

```bash
pip install -e .          # from this directory
reproai check . --venue aea --out reports/
```

`reproai check` is the one-shot self-check: inventory → rules + venue → reports. It **never executes
author code** and **never decides reproducibility** — it only advises.

## Anti-sycophancy

Every pass/fail, risk tier, and auto-fix-eligibility decision is made by deterministic code here —
never by a host LLM. The LLM-touch agents (Architect/Provisioner/Distiller in the plugin layer)
only propose, explain, and draft; they cannot change findings or apply high-risk fixes.
