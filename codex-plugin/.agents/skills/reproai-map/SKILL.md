---
name: reproai-map
description: ADVISORY overlay of a manuscript's figures and tables on a replication package's output (write) nodes — which exhibits have no producing output, which outputs no exhibit uses, and panel/count mismatches. LaTeX-only, never runs author code, never issues a reproducibility verdict, and is deliberately NOT part of check. Use when an author wants to see whether every paper exhibit maps to a producing script and vice versa.
---

# reproai map — map manuscript exhibits to package outputs (Codex)

Overlay the paper's exhibit inventory on the package's **output nodes** (files its code writes:
`graph export`, `ggsave`, `esttab`/`estout`/`stargazer`, `save`, ...). An **advisory map**, not a
check: kept OUT of `reproai check` so it can never dent the core's clean-pass credibility. It never
runs author code and **never issues a reproducibility verdict** — a clean map is not "reproduces."

## Steps

1. Determine the package root (default: current directory) and the manuscript **LaTeX source**
   (`.tex`). v1 is LaTeX-only; for a PDF, point `--manuscript` at the `.tex`.

2. Run the engine. If `reproai` is on PATH:

   ```bash
   reproai map <ROOT> --manuscript <PAPER.tex> --out <ROOT>/.reproai/output_map.json
   ```

   Otherwise run from the bundled core:

   ```bash
   PYTHONPATH="${REPROAI_CODEX_ROOT}/core/src" python3 -m line1_core.cli map <ROOT> --manuscript <PAPER.tex> --out <ROOT>/.reproai/output_map.json
   ```

3. Read `output_map.json`. If `status` is not `ok` (`manuscript_not_found`, `unsupported_format`),
   relay the `note` and stop — it degraded gracefully, it did not fail.

4. Present the three advisory lists as-is (do not editorialize a verdict):
   - **`exhibits_without_output`** — a paper Figure/Table whose file is produced by no script and is
     not in the package (missing producing code, or a wrong `\includegraphics{}`/`\input{}` path).
   - **`outputs_without_exhibit`** — a file the code writes that no exhibit uses (often an
     intermediate or dropped figure; flag, do not assume an error).
   - **`panel_mismatches`** — a figure whose subfigure panel count exceeds the panels that map to a
     produced output.

5. State the limits every time: advisory, LaTeX-only, basename-matched; blind to panels combined in
   one file, dynamically-named outputs, and exhibits built outside the parsed floats. Surface the
   report's `disclaimer`. Never call a clean map "reproducible."
