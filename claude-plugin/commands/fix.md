---
name: reproai-fix
description: Apply reproai's advisory fixes to a COPY of the package by reading the diagnostic report and rewriting the code yourself, then re-checking until the findings clear. You (the host LLM) do the rewriting under a lossless contract; the deterministic engine only decides what is wrong and re-verifies. Never touches the original; never changes what the code computes. Use after /reproai check when the author wants the recommended fixes applied.
---

# /reproai fix — read the report, rewrite to a copy, re-check, iterate

You (the host LLM) are the rewriter. The deterministic engine (`reproai check`) is the
diagnostician and the referee. It tells you *what* is wrong and *what the target form is*;
you do the actual code change, on a **copy**, honoring a **lossless contract**; then you
re-run `reproai check` on the copy to confirm the finding cleared. Repeat until it does or the
round cap is hit.

You never decide reproducibility and never execute the author's analysis code. Re-running
`reproai check` is a static re-scan, not an execution of the package.

## The lossless contract (non-negotiable — applies to every edit you make)

1. **Copy first.** Work in a fresh `<ROOT>_fixed/` copy. Never modify the author's original.
2. **Semantics-preserving only.** The code must compute exactly the same results — same
   coefficients, same sample, same data, same file targets. Structural normalization is
   allowed (unrolling a `foreach` into explicit per-model commands, reflowing a call,
   removing a stray `cd`); changing *what the code computes* is forbidden.
3. **Respect each finding's `rewrite.mode`.**
   - `llm_rewrite` → you may apply the edit to the copy, within that finding's
     `rewrite.lossless_note` boundary.
   - `propose_only` → **do NOT edit the code.** Write the recommendation for the author
     and move on. These are too semantic to change safely (data re-derivation, dead-fallback
     loads, sample/merge cardinality, estimator/formula, seeds, environment).
4. **When in doubt, don't.** If you cannot make a change without risking a semantic shift,
   leave it as a written recommendation instead of editing.

## Steps

1. **Get the report.** If `<ROOT>/.reproai/reports/advisory_plan.json` does not exist (or may
   be stale), run a fresh check:

   ```bash
   reproai check <ROOT> --venue <VENUE> --out <ROOT>/.reproai/reports
   ```

   If `reproai` is not on PATH, use the bundled core:

   ```bash
   PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/core/src" python3 -m line1_core.cli check <ROOT> --venue <VENUE> --out <ROOT>/.reproai/reports
   ```

2. **Make the working copy** (the original is never touched):

   ```bash
   cp -r <ROOT> <ROOT>_fixed
   ```

   If `<ROOT>_fixed` already exists, stop and ask the author (do not overwrite).

3. **Read `advisory_plan.json`.** Note `lossless_contract` (the universal rules above) and,
   for each item, its `priority`, `rewrite.mode`, and `rewrite.fix_prompt`. The `fix_prompt`
   is a self-contained directive: PROBLEM / WHERE / WHY IT HURTS DOWNSTREAM / TARGET FORM /
   LOSSLESS BOUNDARY. Treat it as your spec for that edit.

4. **Apply the `llm_rewrite` items to the copy.** Order matters in two ways:

   **(i) Dependency order among the table rules: A12 → N2 → D1.** Three rules form a chain and MUST
   be applied in this order:
   1. **`A12-table-comment-mapping` first** — if the code has no `* --> Table N` comments, the
      table<->command mapping is unknown. Add the (placeholder) table-anchor comments first, so the
      following steps know which regressions belong to which table. The table NUMBER is a paper fact
      the LLM must NOT invent: propose a grouping from code structure and insert
      `* --> Table ?? (reproai: author, confirm number)` placeholders for the author to fill.
   2. **`N2-explicit-table-commands` next** — unroll any `foreach`/loop that builds a table into
      explicit per-model commands. Inject an export before unrolling and you are capturing a table
      from inside a loop — the hard, error-prone case. After N2 unrolls Table A.1's
      `foreach x ... reg \`x'` into explicit `reg age`, `reg married`, ... lines, the next step is
      trivial.
   3. **`D1-output-artifact-coverage` last** — now that each table section is anchored (A12) and
      flattened (N2), inject `eststo`/`esttab ... using "output/tables/tableN.csv"` per table.

   By the time the package reaches `/reproai-debug`, there must be NO `foreach`/loop left building a
   reported table, and every table section must have an anchor comment + an export — debug runs
   already-anchored, already-unrolled, output-injected code.

   **(ii) Then priority order (P0 → P4)** for the rest. For each item:
   - Read the cited file:line in the copy.
   - Make the smallest edit that reaches the `TARGET FORM`, staying inside the
     `LOSSLESS BOUNDARY FOR THIS RULE`.
   - Do not touch anything the boundary forbids (basenames, datasets, samples, merge keys,
     estimation commands, options).
   - Skip every `propose_only` item — collect those for the author summary.

   **EVERY evidence entry, not just the first.** One finding can carry MANY locations in its
   `evidence` array — e.g. `D1-output-artifact-coverage` lists *every* `Table N` section that lacks
   an export (15 sections on a typical paper), and `N2` lists every loop. You MUST handle **each
   evidence entry**, not one representative. Do not stop after the first table/loop. The engine is
   the checklist: it already enumerated every instance deterministically; your job is to clear the
   whole list. The re-check in step 5 is what catches a half-done finding — if you injected an
   export for Table 1 but not Tables 2-15, the re-check still reports D1 with the remaining 14, and
   you must continue until the count reaches zero. Treat "the finding still fires" as "I am not done
   with this finding," never as "good enough."

5. **Re-check the copy, then run the HARD GATE (this is the real, code-level completion test):**

   ```bash
   reproai check <ROOT>_fixed --venue <VENUE> --out <ROOT>_fixed/.reproai/reports
   reproai gate <ROOT>_fixed        # <-- exits NONZERO while ANY Table/Figure lacks a valid export
   echo "gate exit: $?"
   ```

   **`reproai gate` is the authority, not your judgment.** It lists every paper Table N / Figure N
   and exits 0 only when each has an export under `output/tables` / `output/figures`. A misnamed or
   mislocated export does NOT satisfy it. You are **not done** with fix until `reproai gate` exits 0.
   You MUST paste the `reproai gate` output (showing it exits 0) as the proof of completion — a
   transcript that proceeds with a nonzero gate is invalid. Do not hand-wave "I fixed the tables";
   show the gate passing.

   **Venue `needs_author_action` / `not_implemented` items are off-package and stay that way.** Do
   not auto-fix them and do not mark them done. If the author says "I already did it," record it as a
   NOTE next to the item only — the engine status NEVER changes from the author's answer, and a
   `needs_author_action` item is never converted to `pass`.

6. **Compare new advisory vs old.**
   - A finding that **disappeared** → that rewrite succeeded.
   - A finding that **remains** → read its (possibly updated) `fix_prompt`, understand why it
     still fires (your edit missed the target, or introduced a different smell), and revise
     your edit on the copy.
   - A **new, higher-priority** finding you introduced → revert that specific edit; your
     change was not lossless. Prefer leaving the original finding unfixed over shipping a
     riskier package.

7. **Iterate, capped at 3 rounds.** Repeat steps 4–6 only for findings that are still
   `llm_rewrite` and still present. Stop when either:
   - all `llm_rewrite` findings have cleared, or
   - 3 rounds are done, or
   - the only remaining findings are `propose_only` or ones you judged unsafe to auto-apply.

8. **Hand the author the result.** Show:
   - the unified diff of `<ROOT>` → `<ROOT>_fixed` (`diff -ru <ROOT> <ROOT>_fixed`, excluding
     `.reproai/`),
   - which findings cleared (with before/after `reproai check` priority counts),
   - the `propose_only` items as written recommendations they must apply by hand,
   - any `llm_rewrite` items you deliberately left unfixed, and why.

## Hard rules

- Never edit in place. All edits go to `<ROOT>_fixed`; the original stays byte-for-byte intact.
- Never apply a `propose_only` finding as a code edit.
- Never make a change that could alter a coefficient, sample, variable, merge cardinality, or
  path resolution. The per-finding `lossless_note` is the boundary; do not widen it.
- Never claim the package is "reproducible" or "fixed" — you removed known avoidable smells; a
  first-try downstream pass is maximized, not guaranteed.
- The engine decides what is a finding and whether it cleared. You do not overrule it.

## Tier-0 mechanical transforms (optional convenience)

A small set of edits are provably mechanical (B9: drop `quietly` before a `use`; B11: comment
an R-Markdown fence in a `.R` file). The engine can apply just those deterministically:

```bash
reproai fix <ROOT> --venue <VENUE>                       # dry-run: show the mechanical diff
reproai fix <ROOT> --venue <VENUE> --apply --out <ROOT>_fixed   # write them to a copy
```

This is a shortcut for the trivially-safe subset only. The full advisory-driven rewrite above
is what handles the rest.
