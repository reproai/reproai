---
name: reproai-map
description: ADVISORY overlay of a manuscript's figures and tables on a replication package's output (write) nodes — which exhibits have no producing output, which outputs no exhibit uses, and panel/count mismatches. LaTeX-only, never runs author code, never issues a reproducibility verdict, and is deliberately NOT part of check. Use when an author wants to see whether every paper exhibit maps to a producing script and vice versa.
---

# /reproai map — map manuscript exhibits to package outputs

Overlay the paper's exhibit inventory on the package's **output nodes** (the files its code writes:
`graph export`, `ggsave`, `esttab`/`estout`/`stargazer`, `save`, ...). This is an **advisory map**,
not a check: it is kept OUT of `reproai check` so it can never affect the core's clean-pass
credibility. It never runs author code and **never issues a reproducibility verdict** — a clean map
does not mean the package reproduces.

## Steps

1. Determine the package root (default: current directory) and the manuscript **LaTeX source**
   (`.tex`). v1 is LaTeX-only; for a PDF, point `--manuscript` at the `.tex`.

2. Run the engine:

   ```bash
   reproai map <ROOT> --manuscript <PAPER.tex> --out <ROOT>/.reproai/output_map.json
   ```

   If `reproai` is not on PATH, run from the bundled core:

   ```bash
   PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/core/src" python3 -m line1_core.cli map <ROOT> --manuscript <PAPER.tex> --out <ROOT>/.reproai/output_map.json
   ```

3. Read `output_map.json`. If `status` is not `ok` (`manuscript_not_found`, `unsupported_format`),
   relay the `note` and stop — it degraded gracefully, it did not fail.

4. Present the three advisory lists as-is (the engine computed them; do not editorialize a verdict):
   - **`exhibits_without_output`** — a paper Figure/Table whose referenced file is produced by no
     script and is not in the package. The most actionable list: either the producing code is
     missing, or the `\includegraphics{}`/`\input{}` path is wrong.
   - **`outputs_without_exhibit`** — a file the code writes that no exhibit uses. Often an
     intermediate or a dropped figure; flag it, do not assume it is an error.
   - **`panel_mismatches`** — a figure whose subfigure panel count exceeds the number of panels that
     map to a produced output (a panel the code does not appear to draw).

5. Be explicit about limits every time: this is an **advisory map**, LaTeX-only, matched by file
   basename; it cannot see panels combined in one file, dynamically-named outputs, or exhibits built
   outside the parsed floats. Surface the report's `disclaimer`. Never call a clean map "reproducible."
