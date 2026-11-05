# Normalized replication-package coding style guide

The reference behind Line 1's **normalization** advisories. Line 1 is **prescriptive, not a
defect checker**: the same analysis can be written hundreds of ways, and one normalized way is
easier for a downstream reproducibility pipeline (and an LLM reading the code) to understand —
fewer misreads, fewer parser/marker surprises, fewer fix-loop rounds.

> These are **"a better way to write it"**, not **"your code is wrong"**. Most of this code runs
> fine as-is. The goal is a package that the downstream Line 2 pipeline reproduces in one pass.

Each item: **prefer** (the normalized form) vs **avoid** (the form that costs the downstream more),
and **why it lowers downstream cost**.

## Stata

### Continuation: use `///`, avoid `#delimit ;`
- **Prefer:** break long commands with `///` line continuation.
- **Avoid:** `#delimit ;` blocks ending statements with `;`.
- **Why:** `#delimit ;` changes the statement terminator for a whole region; automated
  instrumentation and many parsers must special-case it, and a single missed `;` silently merges
  two commands. `///` is line-local and unambiguous.

### Tables: write one explicit command per model, avoid building a table inside a loop
- **Prefer:** one estimation command per reported model, grouped under a `* Table X` header.
- **Avoid:** `foreach`/`forvalues` that runs estimations and writes the same export file each
  iteration.
- **Why:** a loop hides which iteration produced which table cell; a fixed export filename inside
  the loop is overwritten every pass; loop-unrolling for output capture is error-prone. Explicit
  per-model commands make the model→cell mapping obvious to both the pipeline and an LLM.

### Variables: full names, no abbreviations
- **Prefer:** full variable and command names.
- **Avoid:** abbreviated varlists / commands (`reg y x1-x9` shorthand, `su`, truncated names).
- **Why:** abbreviations get truncated in stored output (`internet~100`) and shift coefficients
  during matching.

### One script = one job, with an explicit data load
- **Prefer:** each script begins with its own `use`/`import` and declares panel structure
  (`tsset`/`xtset`) before time-series operators.
- **Avoid:** scripts that assume an active dataset left by a previous interactive session.
- **Why:** batch execution starts each script clean; an assumed pre-load fails immediately.

### Estimation calls: standard, named, un-wrapped
- **Prefer:** call estimators directly (`reghdfe ...`, `ivreghdfe ...`).
- **Avoid:** hand-rolled scalar-wrapper programs around an estimator purely to reshape output.
- **Why:** output-capture and tracing recognize standard estimation commands; custom wrappers slip
  past capture and past a human skim.

### Paths and directories
- **Prefer:** relative paths from the package root; no mid-script `cd`.
- **Avoid:** absolute paths and `cd "subdir"` that breaks when run from the root.
- **Why:** a portable package runs anywhere; a `cd` mid-script breaks every later relative path.

### Keep `.do` files pure Stata
- **Prefer:** Stata-only content in `.do`; vendor user-written ado in the package.
- **Avoid:** embedded R fragments / `library(...)` inside `.do`; unshipped ado commands.
- **Why:** non-Stata content and missing ado halt execution before the regressions run.

## R

### Table-output calls: compact, one argument per line, balanced
- **Prefer:** `stargazer(...)`/`xtable(...)` with one argument per line and clearly balanced
  parentheses.
- **Avoid:** deeply nested multi-line table calls with parentheses spread across many lines.
- **Why:** an extra or missing paren in a sprawling table call halts the script, and automated
  comment-cleaning of multi-line calls can leave dangling arguments. Compact, balanced calls are
  robust to both.

### Explicit data loading
- **Prefer:** each script loads its inputs (`read_csv`, `readRDS`, `load`).
- **Avoid:** scripts that assume objects from a previous interactive session.
- **Why:** sourced/batch execution does not inherit an interactive workspace reliably.

### Pin dependencies; avoid install-from-source mid-script
- **Prefer:** declared, pinned package versions (renv).
- **Avoid:** `install_github(...)` / unpinned `install.packages` inside the analysis.
- **Why:** floating or source installs drift and can fail, zeroing out whole model families.

## Package organization (both languages)

### One master script
- **Prefer:** a single master script that runs prep-then-analysis in order.
- **Avoid:** relying on filename alphabetical order or manual run order.
- **Why:** the pipeline (and a new reader) needs an unambiguous entry point and build order.

### Group by table, comment the mapping
- **Prefer:** keep all commands that build one table together with a `this block -> Table X` comment.
- **Why:** the single highest-leverage normalization — it pre-aligns the paper's tables with the
  code that produces them, which is the most expensive step the downstream pipeline performs.

### Re-derive from raw
- **Prefer:** rebuild analysis variables from the rawest shipped source.
- **Avoid:** shipping opaque pre-computed derived columns an analysis would never re-derive.
- **Why:** a stale or mislabeled derived column silently corrupts results.
