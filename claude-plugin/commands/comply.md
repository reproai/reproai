---
name: reproai-comply
description: Check a replication package against a target journal's replication-package rules (AEA, ...), without re-running the full pre-diagnose. Use when the author only wants the venue compliance checklist.
---

# /reproai comply — venue compliance check

Run only the venue-compliance line of the deterministic engine.

## Steps

1. Confirm the package root and target venue (`aea`, `econsoc`, `apsr`, `ajps`, `jop`, `jasa`, `worldbank`, plus `generic_dataverse` / `generic_openicpsr` fallbacks).

2. Run:

   ```bash
   reproai check <ROOT> --venue <VENUE> --out <ROOT>/.reproai/reports
   ```

3. Read `venue_compliance_report.json` and present the checklist: each requirement with its
   `pass` / `fail` / `needs_author_action` status, the deterministic detail, and the authoritative
   `source` URL.

4. Do not change any status. For `needs_author_action` items, explain what the author must do
   (these are requirements that cannot be verified statically, e.g. signing a data availability form).
