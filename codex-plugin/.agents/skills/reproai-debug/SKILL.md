---
name: reproai-debug
description: Trial-run a replication package (on a COPY) as a smoke test — confirm the code runs without errors and that the injected Table/Figure output commands actually produced files. On a runtime error it does NOT auto-fix; it explains the root cause, offers a few fix options, and asks the author to choose, then applies the chosen fix and re-runs. It executes code but never compares coefficients and never issues a reproducibility verdict. Use after reproai-fix.
---

# reproai debug — smoke-test the package, author decides every fix (Codex)

This is the one reproai workflow that **runs the author's code** — a **smoke test**: confirm
(a) the package runs end-to-end without errors, and (b) the output commands (especially the ones
`reproai-fix` injected for D1) actually wrote their tables/figures to `output/tables` /
`output/figures`. Then surface the generated artifacts for the author's eyeball test.

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
3. Trial-run one script at a time, capturing output to a log:
   - Stata: `stata -b do <script>.do` then read `<script>.log` for `r(###)`.
   - R: `Rscript <script>.R 2>&1 | tee <script>.log`.
   - Python: `python3 <script>.py 2>&1 | tee <script>.log`.
   Stop at the first script that errors.
4. **On a runtime error — STOP and consult the author. Do NOT auto-fix.**
   a. Read the log; locate the failing command and error code.
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
   `reproai verify <COPY> --since <RUN_START_EPOCH>; echo "verify exit: $?"`. It checks every
   expected Table/Figure output file exists, is non-empty, and is fresh; exits nonzero with the
   `not_produced` list otherwise. You are NOT done until it exits 0 — paste its output. A missing
   artifact → step 4 (diagnose, ask author), fix, re-run, re-verify. Do not declare "tables and
   figures produced" yourself; `reproai verify` says so, or it isn't true.
6. Hand the author (only after `reproai verify` exits 0): which scripts ran clean, the generated
   tables/figures (paths), the fixes applied (and which option they chose), and: "This is a smoke
   test — the code runs and emits its artifacts. NOT a reproducibility verdict; eyeball against the
   paper."

## Hard rules

- Run only the copy; never run-modify the original.
- Never auto-fix a runtime error — always present root cause + options and let the author choose.
- Never compare a produced number to the paper; never say the package "reproduces".
- If the runtime (Stata/R/Python) is not installed, say so and stop — do not fake a run.
