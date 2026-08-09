---
name: reproai-comply
description: Check a replication package against a target journal's replication-package rules (AEA, ...), without re-running the full pre-diagnose. Use when the author only wants the venue compliance checklist.
---

# reproai comply — venue compliance check (Codex)

Run the engine and present only the venue-compliance line.

## Steps

1. Confirm the package root and target venue (`aea`, `econsoc`, `apsr`, `ajps`, `jop`, `jasa`, `worldbank`, plus `generic_dataverse` / `generic_openicpsr` fallbacks).

2. Run (use the bundled core form if `reproai` is not on PATH —
   `PYTHONPATH="${REPROAI_CODEX_ROOT}/core/src" python3 -m line1_core.cli check ...`):

   ```bash
   reproai check <ROOT> --venue <VENUE> --out <ROOT>/.reproai/reports
   ```

3. Read `venue_compliance_report.json` and present the checklist: each requirement with its
   `pass` / `fail` / `needs_author_action` status, the deterministic detail, and the
   authoritative `source` URL.

4. Do not change any status. For `needs_author_action` items, explain what the author must do
   (requirements that cannot be verified statically, e.g. signing a data availability form).
