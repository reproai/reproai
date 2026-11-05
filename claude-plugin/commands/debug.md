---
name: reproai-debug
description: Rehearse a replication package on a COPY the way a certification service will (R and Python run twice under fixed settings and the outputs compared; Stata run once) — confirm the code runs without errors, that the Table/Figure output commands actually produced files, and whether two runs agree. On a runtime error it does NOT auto-fix; it explains the root cause, offers a few fix options, and asks the author to choose (AskUserQuestion), then applies the chosen fix and re-runs. It executes code but never compares coefficients and never issues a reproducibility verdict. Use after /reproai-fix to confirm the fixed copy actually runs and emits its tables and figures.
allowed-tools: Read, Grep, Bash, Edit, Write, AskUserQuestion
---

# /reproai debug — rehearse the package on a copy, author decides every fix

This is the one reproai command that **runs the author's code**. Its purpose is narrow and explicit:
a **rehearsal** — confirm (a) the package runs end-to-end without errors, and (b) the output
commands (especially the ones `/reproai-fix` injected for D1) actually wrote their tables and figures
to `output/tables` / `output/figures`, and, for R and Python, (c) whether two runs under a
certification service's settings write the same outputs. Then surface every generated table and figure
for the author's eyeball test against the paper.

**What this command does NOT do** (still true, and important):
- It does **not** compare coefficients to the paper.
- It does **not** issue any "reproducible / verified / certified" verdict — that belongs to the
  journal's check or a certification service such as IQSS Certify.
- It does **not** auto-fix errors in a silent loop. **Every fix is the author's decision.**
- It does **not** change a venue check's status. If you surface venue results and the author says
  they completed a `needs_author_action` item, record it as a NOTE only; the deterministic engine
  owns every status, and an author's answer never flips `needs_author_action` to `pass`.

## Boundary

- Always operate on a **copy** (`<root>_fixed`, the output of `/reproai-fix`, or a fresh copy you
  make). The author's original package is never run-modified.
- You execute code, but you only read two things off the run: **did it error**, and **did the
  expected output files appear**. Nothing numerical is judged.

## Steps

1. **Pick the target copy.** Prefer the `<root>_fixed` produced by `/reproai-fix`. If none exists,
   make one: `cp -r <ROOT> <ROOT>_debug`. Never run the original in place.

1b. **PRECONDITION — run the static hard gate first. If it fails, STOP.**

    ```bash
    reproai gate <COPY>; echo "gate exit: $?"
    ```

    `reproai gate` exits nonzero while ANY paper Table/Figure still lacks a valid export under
    `output/tables` / `output/figures`. **Do not proceed to run the package until it exits 0** —
    debugging a package that isn't even instrumented to emit its artifacts is pointless. If the gate
    fails, go back to `/reproai-fix` and finish injecting the missing exports. Paste the gate output.

2. **Determine the run order.** Use the master script if present; else the README's documented order;
   else ask the author for the order (this is exactly the `A11-explicit-run-order` finding). Do not
   guess an order for a multi-script package.

3. **Trial-run.** For R and Python, use the engine's rehearsal. It copies the package again (the
   folder you pass is never run), runs the scripts in order from the copy's root the way a
   certification service will (network denied, a private empty home folder, UTC and the C.UTF-8
   locale, figures to files only, each step's global random generator seeded), and stops at the
   first failure:

   ```bash
   reproai rehearse <COPY> --script <first> --script <second> ... --out <COPY>/.reproai/rehearsal.json
   ```

   Pass the approved order with `--script`, one per script; without it the engine runs the entry
   scripts (those nothing else calls) in path order. `--runs 2` (the default) runs everything twice
   and compares the outputs: `identical`, `numerically_close` or `different` predicts how two
   practice runs at IQSS Certify will agree (T0, T1, T2); use `--runs 1` for a quick smoke run. Each
   failed step carries the last lines of its output and `hints` (path, library, network,
   session_state, permission). Report `network_denied_by` as it stands: `proxy` means a program
   that ignores proxy settings could still reach the network on this machine.
   - Stata is not rehearsed (`not_rehearsed` lists the scripts): run `stata -b do <script>.do` (or
     `stata-mp`/`StataSE`), read `<script>.log` for `r(###)` errors, and stop at the first one.

4. **On a runtime error — STOP and consult the author. Do NOT auto-fix.**
   a. Read the failing step's `tail` and `hints` (or the Stata log); locate the failing command and
      the error message.
   b. Determine the **root cause** in one or two sentences (missing package, undefined variable,
      missing intermediate file, path issue, version-specific syntax, etc.).
   c. Compose **2–4 concrete fix options**, each with its trade-off / risk.
   d. Call **`AskUserQuestion`** with a `questions` entry:
      - `header`: short label, e.g. "ivreg2 not found"
      - `question`: the root cause + what you propose
      - `options`: each `{label, description}` = one fix option (the host adds an "Other" free-text
        choice automatically)
   e. **Wait for the author's choice.** Apply ONLY the chosen option, to the copy. If the author
      picks "Other", follow their instruction.
   f. Re-run the rehearsal. Repeat from step 4 if it errors again.
   g. If the grade is `different`, the outputs changed between two runs: name the files and, for each,
      whether it `looks_like_clock`. Propose the fix for the cause (a time stamp written into an
      output, an unseeded draw from OS entropy or a library's own generator, forked workers without
      `RNGkind("L'Ecuyer-CMRG")`) through `AskUserQuestion` like any other repair.

5. **When the package runs clean, run the runtime HARD GATE (this is the completion authority):**

   ```bash
   reproai outputs <COPY> --since <RUN_START_EPOCH>; echo "outputs exit: $?"
   ```

   `reproai outputs` deterministically checks that EVERY expected Table/Figure output file actually
   exists, is non-empty, and (with `--since`) was created during this run. It exits nonzero with the
   `not_produced` list if any expected artifact is missing. **You are not done until `reproai outputs`
   exits 0.** Paste its output. A missing artifact means the output command didn't fire (or wrote
   elsewhere) → go to step 4 (diagnose, ask the author), fix, re-run, re-check the outputs. Do not declare
   "tables and figures produced" on your own say-so — `reproai outputs` says so, or it isn't true.

6. **Hand the author the rehearsal result** (only after `reproai outputs` exits 0):
   - which scripts ran clean,
   - the list of generated tables (paths under `output/tables/`) and figures (`output/figures/`),
   - any fixes applied (and which option the author chose for each),
   - the rehearsal grade (identical, numerically close, different) when R or Python was rehearsed,
   - an explicit note: "This is a rehearsal — the code runs and emits its artifacts. It is NOT a
     reproducibility verdict; eyeball the tables/figures against the paper. Certification, if you
     want it, is the certification service's own step."

## Hard rules

- Run only the copy; never run-modify the original.
- Never auto-fix a runtime error — always present root cause + options via `AskUserQuestion` and let
  the author choose.
- Never compare a produced number to the paper; never say the package "reproduces".
- If the runtime (Stata/R/Python) is not installed, say so and stop — do not fake a run.
- Respect the run order; for a multi-script package with no documented order, ask, don't guess.
