---
name: reproai-check
description: One-shot static pre-diagnose of a replication package. Scans the working directory, applies the author rule set and a venue profile, and writes 4 JSON reports. Never runs author code. Use when an author wants to know if their replication package is ready to submit, or what to fix before a reproducibility check.
---

# reproai check — pre-diagnose a replication package (Codex)

Run the **deterministic** reproai engine on the author's package. You (the model) orchestrate;
the engine makes every pass/fail and risk-tier decision. You never decide reproducibility and
never execute the author's code.

## Steps

1. Determine the package root (default: current directory) and target venue (ask the author if
   unknown). Shipped venue profiles: `aea`, `econsoc`, `apsr`, `ajps`, `jop`, `jasa`, `worldbank`, plus `generic_dataverse` and `generic_openicpsr` fallbacks.

2. Run the engine. If `reproai` is on PATH:

   ```bash
   reproai check <ROOT> --venue <VENUE> --out <ROOT>/.reproai/reports
   ```

   Otherwise run from the bundled core:

   ```bash
   PYTHONPATH="${REPROAI_CODEX_ROOT}/core/src" python3 -m line1_core.cli check <ROOT> --venue <VENUE> --out <ROOT>/.reproai/reports
   ```

3. Read the 4 reports:
   - `architecture_report.json` — entry points, dependency graph, table→command map, orphans
   - `advisory_plan.json` — remediation items, each `low` (auto-applicable) / `high` (propose-only),
     and each with a `rewrite.fix_prompt`
   - `venue_compliance_report.json` — per-requirement pass/fail vs the venue
   - `risk_register.json` — what would likely break a downstream reproducibility run
   Also read the `adversarial_review` block (the engine's deterministic cross-check): surface any
   `conflicts` and risk-tier over-reach as-is; do not pick a side or override them.

3b. Environment reproducibility note. From the dependency findings (`C1` unpinned, `C2` unvendored
   user commands, `C3` missing version), tell the author what a pinned environment needs — and if
   asked, draft a `renv.lock` / `requirements.txt` / Stata `version` + ado manifest to review.
   Explicit proposals to confirm; never silently chosen; nothing installed or run.

4. Summarize by **priority** (the engine assigns P0–P4; do NOT change priority or kind):
   P0 blocks reproduction · P1 large downstream cost · P2 moderate misread risk · P3 minor ·
   P4 venue/polish. Distinguish `defect` (would cost the downstream) vs `normalization` (a more
   standard way to write it).

5. Offer a tiered plan: "fix P0 only", "P0+P1", or "all". The next step is `reproai-fix`.

5b. **Pre-submission author actions.** Present every venue `needs_author_action` item as a SEPARATE
   checklist (not in the pass/fail counts), each with `author_action` / `how` / `self_check` / the
   official `source` and the line "the static engine cannot verify this; complete it before
   submission." Show `not_implemented` items as "reproai can't check this yet" (name `needs_detector`).
   NEVER mark such an item `pass`; the engine owns every status, and an author's "I did it" is a NOTE
   only — it never changes a status.

6. Be honest: pre-diagnose maximizes the chance of a first-try pass; it does not guarantee it.
   Surface the `cannot_predict` list from `risk_register.json`.
