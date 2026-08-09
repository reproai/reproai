---
name: reproai-fix
description: Apply reproai's advisory fixes to a COPY of the package by reading the diagnostic report and rewriting the code yourself, then re-checking until the findings clear. You (the model) do the rewriting under a lossless contract; the deterministic engine only decides what is wrong and re-verifies. Never touches the original; never changes what the code computes. Use after reproai-check.
---

# reproai fix — read the report, rewrite to a copy, re-check, iterate (Codex)

You (the model) are the rewriter. The engine (`reproai check`) is the diagnostician and the
referee: it says *what* is wrong and *what the target form is*; you do the edit, on a **copy**,
under a **lossless contract**; then you re-run `reproai check` to confirm the finding cleared.
Repeat until it does or the round cap (3) is hit. Re-running check is a static re-scan, not
execution of the package.

## The lossless contract (every edit)

1. **Copy first.** Work in `<ROOT>_fixed/`. Never modify the author's original.
2. **Semantics-preserving only.** Same coefficients, sample, data, file targets. Structural
   normalization (unrolling a loop, reflowing a call, removing a stray `cd`) is fine; changing
   what the code computes is not.
3. **Respect `rewrite.mode`.** `llm_rewrite` → you may apply it to the copy within that finding's
   `rewrite.lossless_note`. `propose_only` → do NOT edit; write the recommendation for the author.
4. **When in doubt, don't.** If you cannot make a change without risking a semantic shift, leave
   it as a written recommendation.

## Steps

1. Get the report (run `reproai check <ROOT> --venue <VENUE> --out <ROOT>/.reproai/reports`, or the
   bundled-core form `PYTHONPATH="${REPROAI_CODEX_ROOT}/core/src" python3 -m line1_core.cli check ...`).
2. `cp -r <ROOT> <ROOT>_fixed` (stop and ask if `<ROOT>_fixed` exists).
3. Read `advisory_plan.json` — its `lossless_contract` and each item's `priority`, `rewrite.mode`,
   `rewrite.fix_prompt` (PROBLEM / WHERE / WHY DOWNSTREAM / TARGET FORM / LOSSLESS BOUNDARY).
4. Apply `llm_rewrite` items to the copy. **Order:**
   - **Dependency chain A12 → N2 → D1**: first add `* --> Table N` anchor comments
     (`A12`, placeholder numbers the author confirms — never invent a table number), then unroll
     any `foreach`/loop (`N2`), then inject per-table outputs to `output/tables` (`D1`).
   - Then the rest in priority order P0 → P4.
   - **Handle EVERY evidence entry**, not just the first. One finding can list many locations
     (e.g. D1 lists every `Table N` section). The re-check is the checklist enforcer: if a finding
     still fires, you are not done with it.
   - Skip `propose_only` items; collect them for the author summary.
5. Re-check, then run the HARD GATE (the real, code-level completion test):
   `reproai check <ROOT>_fixed --venue <VENUE> --out <ROOT>_fixed/.reproai/reports`
   then `reproai gate <ROOT>_fixed` — it exits NONZERO while ANY paper Table/Figure lacks a valid
   export under output/tables / output/figures (a misnamed/mislocated export does NOT count). You
   are NOT done until `reproai gate` exits 0; paste its output as proof. A transcript that proceeds
   with a nonzero gate is invalid.
6. Compare: a finding that disappeared succeeded; one that remains needs revision; a new
   higher-priority finding you introduced → revert that edit (it was not lossless).
7. Iterate steps 4–6, capped at 3 rounds, until `llm_rewrite` findings clear or only
   propose-only / judged-unsafe ones remain.
8. Hand the author: the diff (`diff -ru <ROOT> <ROOT>_fixed`, excluding `.reproai/`), which
   findings cleared, the propose-only recommendations, and any items you deliberately left.

## Hard rules

- Never edit in place; all edits go to `<ROOT>_fixed`.
- Never apply a `propose_only` finding as a code edit.
- Never change a coefficient, sample, variable, merge cardinality, or path resolution.
- Never claim the package is "reproducible"/"fixed" — you removed known avoidable smells; a
  first-try downstream pass is maximized, not guaranteed.
