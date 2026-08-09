# Graph substrate and new detectors --- design note

Status: **Accepted — implemented in plugin 0.4.7 / rules_version 2026.06.27** (2026-06-27).
Originally drafted 2026-06-26 from lessons building an end-to-end replication package against
`reproai check`. See §7 for how the open decisions were resolved, and `core/CHANGELOG.md`
(plugin 0.4.7) for the shipped change list.

## 1. Why

A real package passed `reproai check` clean (0 P0, 0 defects) at several points
where it did not yet faithfully reproduce the paper. The work that actually
determined fidelity sat outside the engine's view: nondeterministic build steps,
a package-version API change that silently broke output, a covariate-centering
choice that shifted table numbers, and above all mapping every output to the
correct manuscript figure/table.

The engine today verifies a package is **well-formed**. It does not yet verify it
is **faithful** to the paper. The two biggest gains are (1) tightening the static
foundation so the engine's existing analyses are actually correct, and (2) adding
a manuscript-aware layer --- without breaking the determinism the tool's
credibility rests on.

## 2. What exists today (grounding)

- **`dependency_graph.py`** resolves paths with regex on **quoted string literals
  only**: `source("x.R")` matches, `source(file.path(CODE, "x.R"))` does not.
  Edges are R `source`, Stata `do`/`run` and `use`, Python `import`. There are
  **no R data-read/write edges** (`read_dta`, `write.csv`, `ggsave`).
  `_resolve` returns the **first `rglob(basename)` hit**, which is order-dependent.
- **`A5-stable-includes` (P0)** already flags a `do/source/import` target that does
  not resolve to a present file. **`A3-data-load` (P0)** already flags estimation
  with no preceding load. So "missing input" partly exists --- but only over the
  edge types the graph builds.
- **Seeds are already `propose_only`** by policy: `author_rules.yaml`'s legend
  groups "seeds" with data re-derivation and estimator/formula as too-semantic to
  auto-apply. The engine auto-applies only `_AUTO_SAFE_RULES` (`B9`, `B11`);
  everything else is propose-only to the host LLM under a lossless contract.
- Rules are **`author_rules.yaml` (schema v3) + a Python detector** calling
  `emit(rule_id, evidence, rationale)`, promoted through the
  seedbank / `distill_rules.py` / `promote_rule.py` pipeline and regression-tested.

**Implication:** the gaps are narrower than they look. The graph's literal-only
resolution is the keystone limit; several "new" checks are extensions of `A5`/`A3`
and the existing seed policy, not green-field work.

## 3. Plan (audit-revised, phased)

### Phase 1 --- Graph substrate (item A). Foundational.

In `dependency_graph.py`:

- Stop matching the whole `source("...")` call. Instead extract **string-literal
  filenames inside the call's balanced parens**, so `file.path()`, `paste0()`,
  `here()`, `glue()` wrappers resolve via their literal segment.
- Add **typed R/Python I/O edges**: reads (`read_dta`, `read_csv`, `read.csv`,
  `readRDS`, `load`, `fread`, `st_read`) and writes (`write.csv`, `saveRDS`,
  `write_dta`, `ggsave`, `pdf`/`png` + `dev.off`).
- Make `_resolve` **deterministic**: sort candidates; on a basename collision mark
  the edge `ambiguous` and surface it, never silently pick the first hit.
- Tag every edge `resolved | unresolved | ambiguous`.

This single change clears the false positives that motivated item E for free
(empty `entry_points`, `present_unreferenced` modules sourced via `file.path`),
and it extends `A5`'s reach to data reads, which is most of item D.

### Phase 2 --- Missing-input (item D) + remainder of item E.

- **D**: feed the new data-read edges into `A5`'s existing "unresolved target"
  logic. **P0 only on a high-confidence resolved-to-missing literal** (target is a
  literal, absent from the package, and produced by no write edge). A dynamic,
  unresolved, or ambiguous target degrades to **advisory**, never P0. This is the
  load-bearing correction: never block on a guess.
- **E**: `B4` (absolute path) must require real path structure (leading `/` or
  `~/`, a separator, not a string-escape context such as `gsub("\\|", ...)`).
  `D6` (README references a missing file) must ignore the package-root token,
  understand brace/ellipsis globs (`satisUS_{cn,us}.pdf`), and add a
  "documented-as-absent" exception. Each ships a **negative fixture**.

### Phase 3 --- Nondeterminism (item C) + codebook coverage (item G).

- **C**: a detector for stochastic operations with no preceding seed (`sample`,
  `rnorm`/`runif`, `boot`, `amelia`, `mice`; Stata `bootstrap`/`permute`/`ri`).
  Emit a **`propose_only: true`** rule, consistent with the existing seed policy:
  not auto-applied, and **not framed as lossless**. Its `lossless_note` must state
  plainly that adding a seed **changes the realized output** (an explicit
  exception to the usual semantics-preserving boundary; the author confirms). Its
  `target_form` carries **backend-aware** guidance, because the wrong template
  gives false confidence (a `set.seed` before a `%dopar%` does nothing):
  - serial R: `set.seed(N)` before the first draw
  - `foreach %dopar%`: `doRNG` (`registerDoRNG(N)` / `%dorng%`)
  - `future` / `furrr`: `future.seed = TRUE` (or a seed)
  - `parallel::mclapply` / parallel `boot`: `RNGkind("L'Ecuyer-CMRG")` + `set.seed`
  - `Amelia` / `mice`: the `seed` argument
  - Stata: `set seed` (and `set rngstream` under parallel)

  The detector must identify the backend; if it cannot, it presents the menu
  propose-only rather than a single template. The finding feeds `venue_engine`
  (a nondeterministic build makes "ship raw-to-analysis" the wrong advice; the
  right counsel is "ship the constructed analysis file and set a seed") and
  routes through `adversarial_reviewer` for the conflict check.
- **G**: extract variable names referenced in the analysis scripts and
  cross-reference a codebook artifact (`codebook.md`/`.txt`/`.tex`, or a data
  dictionary). Advisory gap report (used-but-undocumented). Tolerant matching;
  never P0.

### Phase 4 --- Output/manuscript map as a separate command (item B).

A new command, `reproai map`, kept out of `check` so it cannot threaten the
core's clean-pass credibility. Input `--manuscript <tex|pdf>`. Parse the exhibit
inventory (`\includegraphics`, `\input`, `\caption`, `\label`, `\appendix`
numbering, subfigures) and overlay it on the graph's **write** nodes. Report:
outputs with no exhibit, exhibits with no producing output, count/panel
mismatches. **Advisory only; v1 LaTeX-only; degrade gracefully** (report what it
could and could not map). Never a verdict, never a blocker.

## 4. Cross-cutting robustness constraints (binding)

1. **Confidence-gating.** A P0/blocker fires only on a high-confidence fact.
   Dynamic, unresolved, or ambiguous evidence is advisory at most. A false "your
   code reads a missing file" on a path that actually exists is the worst possible
   output for a credibility tool.
2. **Determinism.** The engine must be order-stable. Sort candidates; flag
   basename collisions; remove first-`rglob`-hit nondeterminism. A reproducibility
   checker that answers differently across runs is self-undermining.
3. **Fixtures.** Every new or changed detector ships a positive fixture (should
   fire) and a negative fixture (should stay silent). The negative fixtures are
   the real deliverable; they are what catch the next false positive in CI.
4. **Identity.** Static, deterministic, advisory; keep `cannot_predict`. The
   moment a clean `reproai map` or a green C reads as "this will reproduce," the
   tool has over-promised.
5. **Language honesty.** R and Stata are first-class; Python and Julia are
   best-effort. Do not raise a P0 for a language the graph parses poorly.
6. **No contradictory advice.** C must update the venue raw-to-analysis logic and
   route through `adversarial_reviewer`; the engine should not flag a
   nondeterministic build and also tell the author to ship raw-to-analysis code.

## 5. Sequencing and rationale

A + E (foundation and trust) -> D (cheap and high-value once A is solid,
confidence-gated) -> C as detection-only first -> G -> B last, as an isolated
command. The instinct to add capability is right; the correction from the audit
is that **A's confidence-tiering and C's contract-quarantine are load-bearing**.
Get those two wrong and the new power becomes new ways to be confidently wrong.

## 6. Open decisions

- Confidence model: two tiers (`resolved`/`unresolved`) or three (`+ambiguous`)?
  How to score `paste0`-with-a-literal versus a fully dynamic path.
- Seed rule: encode the output-changing nature in `lossless_note` prose, or add a
  schema field (e.g. `output_changing: true`) so the host-LLM fix contract can key
  on it explicitly.
- `reproai map`: final command name, and manuscript scope (LaTeX only in v1;
  `.Rnw`/`.qmd`/Word later?).
- G: require a recognized codebook format, or tolerant free-text matching?

## 7. Resolution (as shipped in 0.4.7)

- **Confidence model:** three tiers (`resolved` / `unresolved` / `ambiguous`). A basename collision is
  `ambiguous` and never raises a P0 (surfaced as advisory A15); a partial-dynamic path like
  `paste0(dir,"x.R")` resolves via its literal segment; a fully dynamic path (no literal) emits no
  edge rather than a guessed one.
- **Seed rule:** added an explicit `output_changing: true` schema field (set on C7 and C8), not prose
  alone, so the host-LLM fix contract keys on it directly. It always pairs with `propose_only: true`,
  and the advisory `fix_prompt` carries an explicit OUTPUT-CHANGING line.
- **`reproai map`:** final command name `map`; LaTeX-only in v1; `.Rnw`/`.qmd`/Word deferred. Kept out
  of `check`; advisory; degrades gracefully (`manuscript_not_found` / `unsupported_format`).
- **G (codebook):** a readable codebook artifact (`codebook`/`data dictionary`/... with a text
  extension) must be present; matching is tolerant (lowercased substring), advisory (P3), never P0.

Item-A confidence-tiering and item-C contract-quarantine were treated as load-bearing per §5: a P0
fires only on a high-confidence fact, every new/changed detector ships a positive **and** a negative
fixture, and C8 routes through `adversarial_reviewer` so the engine never flags a nondeterministic
build while also advising a raw-to-analysis rebuild.
