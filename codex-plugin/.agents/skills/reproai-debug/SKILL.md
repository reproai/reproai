---
name: reproai-debug
description: Rehearse a replication package on a COPY the way a certification service will (R and Python run twice under fixed settings and the outputs compared; Stata run once) — confirm the code runs without errors, that the Table/Figure output commands actually produced files, and whether two runs agree. On a runtime error it does NOT auto-fix; it explains the root cause, offers a few fix options, and asks the author to choose, then applies the chosen fix and re-runs. It executes code but never compares coefficients and never issues a reproducibility verdict. Use after reproai-fix.
---

# reproai debug — rehearse the package on a copy, author decides every fix (Codex)

This is the one reproai workflow that **runs the author's code** — a **rehearsal**: confirm
(a) the package runs end-to-end without errors, and (b) the output commands (especially the ones
`reproai-fix` injected for D1) actually wrote their tables/figures to `output/tables` /
`output/figures`, and, for R and Python, whether two runs under a certification service's settings
write the same outputs. Then surface the generated artifacts for the author's eyeball test.

**It does NOT**: compare coefficients to the paper; issue any "reproducible/verified" verdict;
auto-fix errors silently. **Every fix is the author's decision.**

## Boundary

- Always operate on a **copy** (`<root>_fixed`, the output of `reproai-fix`, or a fresh copy).
  The original is never run-modified.
- You read two signals off the run: did it error, and did the expected output files appear.
  Nothing numerical is judged.

## Execution model (Codex)

- Interactive `codex`: run the scripts directly (sandbox `workspace-write`).
- `codex exec`: it is non-interactive — **do not wait for input**. Run the scripts; on an error,
  print the root cause + numbered options and STOP (emit a follow-up command for the author),
  rather than blocking.
- Use `--cd <copy>` so runs happen inside the copy; never run the original in place.

## Steps

0. PRECONDITION — run the static hard gate; if it fails, STOP and finish `reproai-fix`:
   `reproai gate <COPY>; echo "gate exit: $?"`. It exits nonzero while any Table/Figure lacks a
   valid output export. Do not run the package until it exits 0.

1. Pick the target copy (`<root>_fixed`, else `cp -r <ROOT> <ROOT>_debug`).
2. Determine run order: master script → README order → else ask the author. Do not guess a
   multi-script order.
3. Trial-run. For R and Python use the engine's rehearsal, which copies the package again and runs
   it the way a certification service will (from the root, network denied, private empty home,
   UTC and C.UTF-8, figures to files only, global random generators seeded), stopping at the first
   failure:
   `reproai rehearse <COPY> --script <first> --script <second> ... --out <COPY>/.reproai/rehearsal.json`.
   `--runs 2` (default) also compares two runs: `identical` / `numerically_close` / `different`
   predict T0 / T1 / T2 at IQSS Certify. Read each failed step's `tail` and `hints`, and report
   `network_denied_by` as it stands (`proxy` = proxy settings only).
   - Stata is not rehearsed: `stata -b do <script>.do`, then read `<script>.log` for `r(###)`.
4. **On a runtime error — STOP and consult the author. Do NOT auto-fix.**
   a. Read the failing step's `tail` and `hints` (or the Stata log); locate the failing command.
   b. State the **root cause** in 1–2 sentences.
   c. Compose **2–4 fix options**, each with its trade-off.
   d. **Ask the author to choose. Interaction adapter (graceful degradation):**
      - **Default (always works):** print a numbered block —
        ```
        Root cause: <...>
        Options:
          1. <option A>  — <trade-off>
          2. <option B>  — <trade-off>
          3. <option C>  — <trade-off>
        Recommended: <n>. Reply with the number (or describe your own fix).
        ```
        then wait for the author's next-turn reply.
      - **Enhanced (only if running under the Codex app-server):** you may use the
        `tool/requestUserInput` API to present the same options as a structured prompt. This is
        optional — never require it; the numbered-block path is the contract.
      - **Under `codex exec` (non-interactive):** print the numbered block and STOP; suggest the
        author re-run with their choice. Do not block waiting for input.
   e. Apply ONLY the chosen option, to the copy. Re-run from the failing script. Repeat step 4
      if it errors again.
5. When the package runs clean, run the runtime HARD GATE (completion authority):
   `reproai outputs <COPY> --since <RUN_START_EPOCH>; echo "outputs exit: $?"`. It checks every
   expected Table/Figure output file exists, is non-empty, and is fresh; exits nonzero with the
   `not_produced` list otherwise. You are NOT done until it exits 0 — paste its output. A missing
   artifact → step 4 (diagnose, ask author), fix, re-run, re-check the outputs. Do not declare "tables and
   figures produced" yourself; `reproai outputs` says so, or it isn't true.
6. Hand the author (only after `reproai outputs` exits 0): which scripts ran clean, the generated
   tables/figures (paths), the fixes applied (and which option they chose), the rehearsal grade if
   R or Python was rehearsed, and: "This is a rehearsal — the code runs and emits its artifacts. NOT
   a reproducibility verdict; eyeball against the paper."
7. If the copy is headed for IQSS Certify (the author said so, or it was checked with `--target
   certify`), end with the way in, as `reproai prepare` Step 6 does: run `reproai certify-start <copy>
   --out <copy's parent>/handoff` (if the engine answers that `certify-start` is unknown, update it
   first: `git -C "$REPROAI_CODEX_ROOT" pull && python3 -m pip install -e "$REPROAI_CODEX_ROOT/core"`).
   On `not_ready`, say what stops it and offer to fix it where a repair could clear it (if it is a
   Stata script the author keeps, say that Certify cannot start on this copy). Otherwise ask
   one numbered question, "Start IQSS Certify now? 1. Start now (recommended) 2. Just the steps
   3. Not now". Start now: give `CERTIFY_START.md`'s steps one at a time, up to filling in the copied form, wait
   for the pasted form, say "From here Certify's own instructions apply; ReproAI Prep stops here", then follow
   https://certify.iq.harvard.edu/CERTIFY_PROMPT.md exactly with this copy as the folder.

## Hard rules

- Run only the copy; never run-modify the original.
- Never auto-fix a runtime error — always present root cause + options and let the author choose.
- Never compare a produced number to the paper; never say the package "reproduces".
- If the runtime (Stata/R/Python) is not installed, say so and stop — do not fake a run.
