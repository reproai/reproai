"""code_parse.py — code parsing/detection layer (DRAFT, extracted from rule_engine.py).
Pure Stata/R/Python source analysis (regressions, table/figure exports, sections).
Shared by Prep (rule_engine) and Cert (gate). No rule-evaluation logic here."""
from __future__ import annotations
import re

_STATA_PREFIX = r'(?:(?:cap(?:ture)?|qui(?:etly)?|noi(?:sily)?|xi|svy|eststo(?:\s+\w+)?|est(?:imates)?\s+sto(?:re)?(?:\s+\w+)?|estpost|by(?:sort)?\s+[^\r\n:]+)[\s:]+)*'

_ESTIMATION = re.compile(r'^\s*' + _STATA_PREFIX + r'(reg|regress|areg|xtreg|reghdfe|ivreg\w*|ivregress|logit|probit|tobit|glm|xtivreg\w*|melogit|mlogit)\b', re.IGNORECASE | re.MULTILINE)
# R estimators are almost always ASSIGNED (m <- lm(...), fit = ivreg(...)) so the verb is not at
# line start; match an optional `name <-`/`name =` then a known R estimator call.

_R_ESTIMATION = re.compile(r'(?:^|<-|=|\(|\s)\s*(lm|glm|lm_robust|iv_robust|ivreg|ivreg2|felm|feols|feglm|plm|lmer|glmer|polr|multinom|gam|coxph|survreg|rdrobust|rdd_reg)\s*\(', re.IGNORECASE)

_R_TABLE_CALL = re.compile(r'\b(stargazer|xtable|print\.xtable|texreg|htmlreg|screenreg)\s*\(', re.IGNORECASE)

_PROGRAM_DEF = re.compile(r'^\s*program\s+(?:define\s+)?(\w+)', re.IGNORECASE)

# D1 artifact-output coverage
# texreg-family writers all take `file=` and write a table file: texreg (LaTeX), htmlreg (HTML),
# screenreg (plain text), matrixreg (matrix), wordreg (Word). _R_TABLE_CALL already treats
# screenreg as a table-builder (line 43), so omitting it here credited the builder but never its
# export (issue #21). Kept in sync with _R_TABLE_CALL for the texreg family.

_TABLE_EXPORT = re.compile(r'\b(esttab|estout|outreg2?|putexcel|putdocx|tabout|stargazer|texreg|htmlreg|screenreg|matrixreg|wordreg|etable|modelsummary|xtable|kable|kableExtra|gtsave|write[._]csv|write[._]dta|saveRDS|export\s+delimited)\b', re.IGNORECASE)
# Follow-up A: a figure producer may be ASSIGNED (`p <- ggplot(...)`, `g = qplot(...)`), which the
# old `^\s*`-anchored pattern missed entirely. The optional assignment prefix
# `(?:[\w.$]+\s*(?:<-|<<-|=)\s*)?` admits `name <-`/`name <<-`/`name =` before the producer while the
# trailing producer alternation still gates (so `x <- mean(y)` does NOT match). Widening this makes
# D1/gate STRICTER (an assigned plot now expects an export), so only HIGH-CONFIDENCE producers were
# added: R `qplot(`/`autoplot(`. Base-R `hist(`/`boxplot(`/`barplot(`/`image(`/`contour(` were
# DEFERRED — they fire on incidental diagnostic plots (false-positive risk); Stata `saving()` graph
# option DEFERRED (ambiguous, appears in non-graph contexts).

_GRAPH_CMD = re.compile(r'^\s*(?:[\w.$]+\s*(?:<-|<<-|=)\s*)?(graph\s+(?:twoway|bar|box|matrix|combine|tw)|twoway|histogram|scatter|kdensity|coefplot|marginsplot|ggplot|qplot|autoplot|plot\()', re.IGNORECASE)
# A figure write-out: a graphics device open or an explicit graph-export verb. Single leading `\b`
# (NOT per-token) is deliberate — a per-token `\b` would false-match `foo.png(`. `(` is escaped.
# Kept a strict superset of the graphics-device subset of dependency_graph._WRITE_VERBS; the
# drift-guard test (test_graph_export_covers_dependency_graph_devices) fails CI if that ever breaks.

_GRAPH_EXPORT = re.compile(
    r'\b(graph\s+export|graph\s+save|ggsave|gr\s+export|dev\.copy|'
    r'pdf\(|png\(|jpe?g\(|tiff\(|bmp\(|svg\(|svglite\(|'
    r'cairo_pdf\(|cairo_ps\(|bitmap\(|'
    r'agg_png\(|agg_jpe?g\(|agg_tiff\(|'
    r'Cairo\(|CairoPNG\(|CairoPDF\(|CairoJPEG\(|CairoTIFF\(|'
    r'tikz\(|postscript\(|savefig\()',
    re.IGNORECASE)
# D1/gate python-notebook vocabulary (issue #33). Python exhibit bodies are invisible to _ESTIMATION
# (Stata, line-anchored) and _R_ESTIMATION, and pandas writers to _TABLE_EXPORT, so a labeled
# notebook exhibit produced 0 expected artifacts and the gate phantom-PASSed. These are consulted
# ONLY when lang == "python" and ONLY inside labeled `# Table N` / `# Figure N` sections — the
# unlabeled fallbacks stay stata/r-only, so a plain helper .py never becomes a phantom artifact.
# Body regexes are case-SENSITIVE (Python class names are: OLS( is statsmodels, ols( would be a
# user helper). Figure export needs no python sibling: savefig( is already in _GRAPH_EXPORT.

_PY_TABLE_BODY = re.compile(
    r'\b(?:smf|sm)\.\w+\s*\(|\.fit\s*\(|\b(?:PanelOLS|IV2SLS|IVGMM|OLS|Logit|Probit|Poisson)\s*\(|'
    r'\bpd\.(?:pivot_table|crosstab)\s*\(|\.(?:groupby|pivot_table|describe|value_counts|agg|aggregate)\s*\(')

_PY_GRAPH_BODY = re.compile(
    r'\bplt\.\w+\s*\(|\bsns\.\w+\s*\(|\.plot\s*\(|\bggplot\s*\(|\bpx\.\w+\s*\(|\balt\.Chart\s*\(')

_PY_TABLE_EXPORT = re.compile(
    _TABLE_EXPORT.pattern + r'|\.to_(?:csv|latex|excel|html|markdown|string|stata|json)\s*\(|\bsavetxt\s*\(',
    re.IGNORECASE)
# D3 intermediate data write / read

_NUM_LABEL = r'([A-Za-z]{0,3}[-.]?\d+(?:[.\-]\d+)*[a-z]?)'

_TABLE_HEADER = re.compile(r'^\s*(?:\*+|//+|#+)\s*\**\s*(?:[-=]{1,2}>\s*)?\**\s*(?:[—–~]+\s*)?(Table|Tabla)\s+' + _NUM_LABEL + r'\b', re.IGNORECASE)

_FIGURE_HEADER = re.compile(r'^\s*(?:\*+|//+|#+)\s*\**\s*(?:[-=]{1,2}>\s*)?\**\s*(?:[—–~]+\s*)?(Figure|Fig\.?|Figura)\s+' + _NUM_LABEL + r'\b', re.IGNORECASE)

# A17 undefined R callable (issue #36). The detector is CONSERVATIVE by construction: it fires only
# when every library()/require() target is a package in the bundled export snapshot
# (rules/r_exports_db.json, regenerated via tools/gen_r_exports.R) — one unknown package silences
# the whole file, because that package's exports are unknowable statically. The callsite lookbehind
# excludes pkg::fn( / obj$fn( / S4 @slot( qualified calls; ANY name bound on an assignment LHS
# counts as defined (a variable may hold a function — `fmt <- make_formatter(...)` must never flag).

def _mask_r_strings_comments(s: str) -> str:
    out = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    out = re.sub(r"'(?:\\.|[^'\\])*'", "''", out)
    out = re.sub(r'#.*', '', out)
    return out

def _is_estimation(line: str) -> bool:
    return bool(_ESTIMATION.match(line) or _R_ESTIMATION.search(line))

def _toplevel_estimation_lines(text: str) -> list[int]:
    """1-based line numbers of estimations NOT inside an R function body or a Stata program.
    A pure helper library (only functions defining estimations) is not an analysis script."""
    out: list[int] = []
    brace_depth = 0
    in_stata_program = False
    for i, line in enumerate(text.splitlines(), start=1):
        if _PROGRAM_DEF.match(line):
            in_stata_program = True
        elif in_stata_program and re.match(r'^\s*end\b', line):
            in_stata_program = False
        if not in_stata_program and brace_depth == 0 and _is_estimation(line):
            out.append(i)
        masked = _mask_r_strings_comments(line)
        brace_depth += masked.count("{") - masked.count("}")
        if brace_depth < 0:
            brace_depth = 0
    return out

_OUT_FIGURE_PATH = re.compile(r'''(?:^|[\\/"'])(?:[\w.\-]+[\\/])*figures[\\/]''', re.IGNORECASE)


# Label-only options carry human-readable text, never an output path. After multi-line call joining
# (issue #20) widened the window in which a `tables/`/`figures/` path can be seen, a decoy path inside
# one of these (e.g. caption="see output/tables/t1") must not count as an export target. Handles the
# `key = "..."` / `key = c("...")` and `key(...)` (one nested-paren level) forms.

_LABEL_OPT_STRIP = re.compile(
    r'\b(?:caption|title|subtitle|sub|note|addnote|label|mtitle|xtitle|ytitle|main|legend)\s*'
    r'(?:=\s*(?:c\s*\()?\s*["\'][^"\']*["\']|\((?:[^()]|\([^()]*\))*\))',
    re.IGNORECASE,
)

def _strip_label_opts(unit: str) -> str:
    return _LABEL_OPT_STRIP.sub(" ", unit)

def _call_unit_from(lines: list[str], start: int, cap: int = 30) -> tuple[str, int]:
    """Join lines[start:] into one logical unit spanning a single parenthesized call: accumulate until
    the running paren depth (measured on string/comment-masked text) returns to 0, capped at `cap`
    lines. Returns (joined_raw, end_exclusive). Idiomatic multi-line R calls put `file=` on a
    continuation line (issue #20); a per-line scan never saw the command and its path together. If the
    call never balances within `cap` (malformed / over-long), returns just the start line, so a later
    balanced call (e.g. a downstream read.csv INPUT) is never swallowed as this call's output."""
    depth = 0
    raw_parts: list[str] = []
    for j in range(start, min(len(lines), start + cap)):
        raw_parts.append(lines[j])
        masked = _mask_r_strings_comments(lines[j])
        depth += masked.count("(") - masked.count(")")
        if depth <= 0:
            return " ".join(raw_parts), j + 1
    return lines[start], start + 1

def _has_canonical_export(body: list[str], cmd_re: re.Pattern[str], out_re: re.Pattern[str]) -> bool:
    # Scan for an export command, then look for the canonical output path within that command's whole
    # (possibly multi-line) call, not just the command's physical line (issue #20). Single-line calls
    # collapse to the previous per-line behavior. Label-only options are stripped so a decoy path in a
    # caption/title/note never counts.
    i, n = 0, len(body)
    while i < n:
        masked = _mask_r_strings_comments(body[i])
        if cmd_re.search(masked):
            unit, end = _call_unit_from(body, i)
            if out_re.search(_strip_label_opts(unit)):
                return True
            i = max(end, i + 1)
            continue
        i += 1
    return False

def _toplevel_graph_line(text: str) -> int | None:
    brace_depth = 0
    for i, line in enumerate(text.splitlines(), start=1):
        if brace_depth == 0 and _GRAPH_CMD.search(line):
            return i
        masked = _mask_r_strings_comments(line)
        brace_depth += masked.count("{") - masked.count("}")
        if brace_depth < 0:
            brace_depth = 0
    return None

def _section_spans(lines: list[str], header_re: re.Pattern[str]) -> list[tuple[str, int, int]]:
    starts = [(i, header_re.search(ln)) for i, ln in enumerate(lines)]
    headers = [(i, f"{m.group(1)} {m.group(2)}") for i, m in starts if m]
    spans = []
    for k, (i, label) in enumerate(headers):
        end = headers[k + 1][0] if k + 1 < len(headers) else len(lines)
        spans.append((label, i, end))
    return spans

def _toplevel_estimations_needing_table(text: str) -> list[int]:
    """Top-level estimation lines that imply an unlabeled table because their output is NOT already
    captured as a saved figure (issue #22). Principle: every estimation needs a durable, comparable
    artifact, and a saved figure counts as one. So an estimation inside a `# Figure N` section that
    has a valid output/figures/ export is figure-served and demands no table; likewise, in a
    header-less script that produces a canonical figure export next to a graph command, the
    estimations feed that figure. A naked estimation with neither a table nor a figure export still
    needs a table, so the gate keeps its teeth. Shared by D1 and the static gate so they agree."""
    lines = text.splitlines()
    toplevel = _toplevel_estimation_lines(text)
    if not toplevel:
        return []
    fig_spans = [
        (s, e) for (_label, s, e) in _section_spans(lines, _FIGURE_HEADER)
        if _has_canonical_export(lines[s:e], _GRAPH_EXPORT, _OUT_FIGURE_PATH)
    ]
    if fig_spans:
        return [ln for ln in toplevel if not any(s <= ln - 1 < e for (s, e) in fig_spans)]
    if _toplevel_graph_line(text) is not None and _has_canonical_export(lines, _GRAPH_EXPORT, _OUT_FIGURE_PATH):
        return []
    return toplevel
