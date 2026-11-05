from __future__ import annotations

# noqa: SIZE_OK -- legacy monolithic rule catalog; this edit only tightens one existing detector.

from typing import Any

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import dependency_graph
from .ado_vendor import ADOPATH_RE, SSC_INSTALL_RE, is_external
from .dependency_graph import Edge, _INCLUDE_KINDS, _READ_KINDS
from .fix_planner import r_standalone_fence_lines
from .inventory import FileEntry, _UNC_ABS, _pdftotext, read_source, read_source_anchored, _blank_sas_comments

_RULES_FILE = Path(__file__).parent / "rules" / "author_rules.yaml"

# B4 absolute path — the ONE abs-path regex (the venue no_absolute_paths check consumes
# abs_path_hits below, issue #42). The UNC branch requires a hostname followed by a path separator,
# so a regex-escape literal like gsub("\\|", ...) and a LaTeX macro like "\\tau_{1|2}" in texreg
# custom.coef.names (two backslashes then a token, no separator) are not mistaken for UNC (issue #19).
# The drive-letter alternative requires the letter NOT be preceded by another letter, so a real
# drive root (`"C:\dir"`, opened by a quote/space/paren) matches but an in-string escape like
# `"Jones:\nmore"` — where the letter before the colon is part of an English word — does not
# (issue #46: `word:\n` was mis-read as a `word:` drive). `\` after the drive must also start a
# path character, not an escape terminator.
_ABS_PATH = re.compile(r'["\']?((?:(?<![A-Za-z])[A-Za-z]:[\\/](?=[\w.])|' + _UNC_ABS + r'|/Users/|/home/|~/)[^"\'\r\n]+)["\']?')
# R and Python strings escape the backslash, so there a network share is spelled with four
# ("\\\\server\\share") and a drive root as "C:\\dir"; two backslashes are one escaped backslash
# ("\\hline\n", "^\\d\\d"), never a share. A drive root with one backslash (a raw string) or a
# forward slash still counts.
_ABS_PATH_ESCAPED = re.compile(r'["\']?((?:(?<![A-Za-z])[A-Za-z]:(?:\\{1,2}|/)(?=[\w.])'
                               r'|\\{4}[\w][\w.-]*(?:\\{2}|/)|/Users/|/home/|~/)[^"\'\r\n]+)["\']?')
# A quoted `../..` climb is the same escape as an absolute path — the certification audit's
# _is_escape treats a normalized target starting with `..` as leaving the replication dataset (Sahn 2025:
# `read("../../../data/analysis_data.Rdata")` from a script three folders deep). One `..` from a
# subfolder script is ordinary and stays inside; the climb has to be at least two levels.
_PARENT_ESCAPE = re.compile(r'["\']((?:\.\./){2,}[^"\'\r\n]*)["\']')
_LOOP_HEAD = re.compile(r'^\s*(foreach|forvalues|forv|while|for)\b', re.IGNORECASE)
_EXPORT_FIXED = re.compile(r'\b(esttab|estout|outreg2?|putexcel|tabout)\b[^\r\n]*using\s+["\']?([^\s"\'`,]+)', re.IGNORECASE)
_TS_OP = re.compile(r'(?<![\w.])([LDF]\d*\.\w+)')
_TSSET = re.compile(r'^\s*(tsset|xtset)\b', re.IGNORECASE | re.MULTILINE)
# Allow common Stata prefixes before the estimator: `xi:`, `by/bysort ... :`, `quietly`,
# `capture`, `noisily`, `svy:` — otherwise `xi: reg ...` / `bysort y: reg ...` are missed.
_STATA_PREFIX = r'(?:(?:cap(?:ture)?|qui(?:etly)?|noi(?:sily)?|xi|svy|eststo(?:\s+\w+)?|est(?:imates)?\s+sto(?:re)?(?:\s+\w+)?|estpost|by(?:sort)?\s+[^\r\n:]+)[\s:]+)*'
_ESTIMATION = re.compile(r'^\s*' + _STATA_PREFIX + r'(reg|regress|areg|xtreg|reghdfe|ivreg\w*|ivregress|logit|probit|tobit|glm|xtivreg\w*|melogit|mlogit)\b', re.IGNORECASE | re.MULTILINE)
# R estimators are almost always ASSIGNED (m <- lm(...), fit = ivreg(...)) so the verb is not at
# line start; match an optional `name <-`/`name =` then a known R estimator call.
_R_ESTIMATION = re.compile(r'(?:^|<-|=|\(|\s)\s*(lm|glm|lm_robust|iv_robust|ivreg|ivreg2|felm|feols|feglm|plm|lmer|glmer|polr|multinom|gam|coxph|survreg|rdrobust|rdd_reg)\s*\(', re.IGNORECASE)
_DATA_LOAD_STATA = re.compile(r'^\s*(use|import|insheet|infile|odbc)\b', re.IGNORECASE | re.MULTILINE)
_DATA_LOAD_R = re.compile(r'\b(read\.|read_|load\(|readRDS\(|fread\(|import\(|vroom\()', re.MULTILINE)
_GITHUB_INSTALL = re.compile(r'(install_github|pip install\s+git\+|remotes::install)', re.IGNORECASE)
_INSTALL_NOPIN = re.compile(r'^\s*(install\.packages|library|require)\b', re.IGNORECASE | re.MULTILINE)
_CLEAR_ALL = re.compile(r'^\s*clear\s+all\b', re.IGNORECASE | re.MULTILINE)
_VERSION_STMT = re.compile(r'^\s*version\s+\d', re.IGNORECASE | re.MULTILINE)
_VERSION_SENSITIVE = re.compile(r'\b(reghdfe|rdrobust|ivreghdfe|did2s|csdid|ivregress|ivreg2?|xtivreg\w*)\b', re.IGNORECASE)
_WIDE_WILDCARD = re.compile(r'\bi\.\w+\#i?\.\w+|\b\w+\*(?:\s|,|$)')
# A documentation file the inventory may classify as "other" when it has no extension
# (e.g. `0_readme`, `1_codebook`, `NOTES`): match by documentary stem so extensionless
# readmes are not invisible to the D4/A11 documentation scans (issue #55).
_DOC_NAMEISH = re.compile(r'(readme|codebook|read[._-]?me|notes?|guide|manifest|instructions?)', re.IGNORECASE)


def _is_doc_entry(path: str, language: str) -> bool:
    if language == "doc" or path.lower().endswith((".md", ".txt", ".rst")):
        return True
    stem = Path(path).name
    return "." not in stem and bool(_DOC_NAMEISH.search(stem))

_CAPTURE_USE = re.compile(r'^\s*(?:cap(?:ture)?|qui(?:etly)?|noi(?:sily)?)[\s:]+(?:.*?\s)?use\s+"?([^"\r\n,]+?\.dta)"?', re.IGNORECASE)
_RC_GUARD = re.compile(r'^\s*if\s+_rc\b', re.IGNORECASE)
_GUARD_USE = re.compile(r'\buse\s+"?([^"\r\n,]+?\.dta)"?', re.IGNORECASE)
_R_TABLE_CALL = re.compile(r'\b(stargazer|xtable|print\.xtable|texreg|htmlreg|screenreg)\s*\(', re.IGNORECASE)
_STATA_DROP = re.compile(r'^\s*drop\s+(.+)$', re.IGNORECASE)
# `drop if <exp>` / `drop in <range>` delete OBSERVATIONS, not variables — no variable leaves the
# dataset. Only `drop <varlist>` removes variables. The \b keeps `drop ifvar`/`drop invar` (variables
# literally named ifvar/invar) as real variable drops (issue #28).
_DROP_OBS = re.compile(r'^(?:if|in)\b', re.IGNORECASE)
_STATA_KEEP = re.compile(r'^\s*keep\s+(.+)$', re.IGNORECASE)
_STATA_RENAME = re.compile(r'^\s*rename?\s+(\w+)\s+(\w+)', re.IGNORECASE)
_DATA_REF = re.compile(r'^\s*(?:cap(?:ture)?\s+|qui(?:etly)?\s+|noi(?:sily)?\s+)*(use|import\s+delimited|insheet|infile)\s+(?:using\s+)?"?([^",\r\n]+?)"?\s*(?:,|$)', re.IGNORECASE)
_REL_CD = re.compile(r'^\s*cd\s+"?(?![A-Za-z]:\\|\\\\|/|~)([^"\r\n]+)"?', re.IGNORECASE)
_QUIET_LOAD = re.compile(r'^\s*(?:qui(?:etly)?[: ]).*\b(use|import|insheet|infile)\b', re.IGNORECASE)
_TABLE_C = re.compile(r'^\s*table\s+\w[^,\r\n]*,\s*c\(', re.IGNORECASE)
_TMPDIR = re.compile(r'\btmpdir\b', re.IGNORECASE)
_RDROBUST_DEPR = re.compile(r'\brdrobust\b[^\r\n]*bwselect\((?:CCT|IK)\)', re.IGNORECASE)
_REGHDFE_IV = re.compile(r'\breghdfe\b[^\r\n]*\([^)=\r\n]+=[^)\r\n]+\)', re.IGNORECASE)
_LEGACY_MIXED = re.compile(r'^\s*(?:xi:\s*)?(xtmelogit|xtmepoisson|meqrlogit|meqrpoisson|xtmixed)\b', re.IGNORECASE)
_CD_EMPTY = re.compile(r'^\s*cd\s+""\s*$', re.IGNORECASE)
_OLD_MERGE = re.compile(r'^\s*merge\s+(?![0-9m]+\s*:\s*[0-9m]+)([A-Za-z_]\w*)\b[^\r\n]*\busing\b', re.IGNORECASE)
_DEPRECATED_R_PKG = re.compile(r'\blibrary\s*\(\s*["\']?(rgdal|rgeos|maptools|ZeligMultilevel|Zelig|checkpoint|hrbrthemes|arm)\b', re.IGNORECASE)
# C7: non-reproducible parallel RNG. `%dopar%` advances a fresh stream per worker;
# doRNG (`%dorng%` or `registerDoRNG(seed)`) is what makes the loop reproducible.
_PAR_DOPAR = re.compile(r'%dopar%')
_PAR_REPRO = re.compile(r'%dorng%|registerDoRNG', re.IGNORECASE)
_RMD_CHUNK = re.compile(r'^\s*```\s*\{[rR][^}]*}\s*$')
_RMD_FENCE_CLOSE = re.compile(r'^\s*```\s*$')
_R_IN_DO = re.compile(r'(\blibrary\s*\([A-Za-z]|\b\w+\s*<-\s|\bcollin\b)')
# C9 console-transcript artifacts in a .do (issue #31). A `. ` console prompt (dot + space + a token)
# shifts the real command right so `do` halts with r(199); `. ` requires the trailing whitespace so
# `replace x = .` (missing value) and `.5` (numeric literal) are safe. A `#` at statement start is not
# a Stata comment token — EXCEPT the #delimit family (#d / #de / ... / #delimit, `;` or `cr`), the one
# legitimate leading-# construct, which the negative lookahead excludes across the whole abbreviation
# ladder so `#d ;` and `#d cr` do not false-fire.
_STATA_PROMPT = re.compile(r'^\s*\.\s+\S')
_STATA_HASH_STMT = re.compile(r'^\s*#(?!d(?:e(?:l(?:i(?:m(?:i(?:t)?)?)?)?)?)?\b)', re.IGNORECASE)
_KNOWN_USER_ADO = {
    "combomarginsplot", "coefplot", "winsor2", "binscatter", "grstyle", "xtabond2",
    "ranktest", "weakivtest", "boottest", "psmatch2", "kmatch", "synth", "eventdd",
    "parmest", "parmby", "spmap", "edvreg", "xtqmlp", "ivreg2", "ivreghdfe", "xtivreg2",
    "csdid", "did2s", "drdid", "rangestat", "carryforward", "mdesc", "fre", "estout", "outreg2",
}
_INSTALL_ADO = re.compile(r'\b(?:ssc\s+install|net\s+install|findit)\s+(\w+)', re.IGNORECASE)
_CMD_HEAD = re.compile(r'^\s*(?:cap(?:ture)?\s+|qui(?:etly)?\s+|noi(?:sily)?\s+|xi:\s*)*([a-z]\w+)', re.IGNORECASE)
_COMMENTED_REG = re.compile(r'^\s*(?:\*|//)\s*(reg|regress|areg|xtreg|reghdfe|ivreg\w*|ivregress|ivreghdfe|logit|probit|tobit)\b', re.IGNORECASE)
_RESTRICTED_WORD = re.compile(r'restrict|confidential|propriet|not\s+public|non-public|unavailable|cannot\s+share|under\s+embargo', re.IGNORECASE)
_DATA_EXTS = (".dta", ".tab", ".csv", ".rds", ".rdata", ".xlsx", ".parquet")
# GUI-analysis project files: the analysis lives inside a binary tool file, not a runnable script.
# Inventory maps these to language "other", so they neither count as code nor as data (issue #8).
_GUI_PROJECT_EXTS = (".splsm", ".sav", ".jasp", ".omv", ".mpj", ".mtb")
# A shipped path that lives under an output/results/tables/figures folder — evidence that result
# artifacts are present in the replication dataset (issue #10). Left boundary so `mytables/` etc. do not match.
_RESULT_DIR = re.compile(r'(?:^|[\\/])(?:output|results|figures|figs|tables|tabs|exhibits)[\\/]', re.IGNORECASE)
# LLM-generated-data provenance (issue #9). A file name or spreadsheet sheet name matching a STRONG
# LLM token marks the data as model-generated. `prompt` alone is deliberately EXCLUDED — it is a
# normal survey/experiment variable name (prompt_response.csv), so it over-fires; it only counts when
# a strong token is also present (already covered by the strong token). The boundaries are LETTER-only
# (`(?<![a-z])...(?![a-z])`) so digits and underscores count as delimiters: `gpt4_survey.csv` and
# `survey_gpt.csv` match, while `budgeting`/`allmusic` (token glued inside a word) do not.
_LLM_ARTIFACT_TOKEN = re.compile(
    r'(?<![a-z])(?:gpt|chatgpt|llm|claude|gemini|openai|anthropic|llama|mixtral|'
    r'large[\s_-]?language[\s_-]?model)(?![a-z])',
    re.IGNORECASE)
# A VERSIONED model id (a family + a version), not a bare mention: requiring the version makes an
# incidental "we used GPT" comment insufficient to clear the finding — the author must record which
# model snapshot generated the data.
_MODEL_ID = re.compile(
    r'\b(gpt[-\s]?\d[\w.]*|gpt-4o|o[134][-\s]?(?:mini|preview)|claude[-\s]?\d[\w.]*|claude-instant|'
    r'gemini[-\s]?\d[\w.]*|gemini-(?:pro|flash|ultra)|llama[-\s]?\d[\w.]*|mistral[-\s]?\w+|'
    r'text-davinci-\d|deepseek[-\s]?\w+)\b', re.IGNORECASE)
# A recorded generation parameter (what makes an LLM run reproducible) or the raw responses.
_GEN_PARAM = re.compile(
    r'\b(temperature|top[_\-\s]?p|top[_\-\s]?k|seed|random[_\-\s]?state)\b'
    r'|\braw\s+(?:api\s+)?response|\bapi\s+response|\bresponse[_\-\s]?id', re.IGNORECASE)
_DELIMIT = re.compile(r'^\s*#delimit\s*;|^\s*#d\s*;', re.IGNORECASE)
_R_TABLE_CALL_LONG = re.compile(r'\b(stargazer|xtable|texreg|htmlreg|screenreg)\s*\(', re.IGNORECASE)
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
_DATA_WRITE = re.compile(r'^\s*(?:cap(?:ture)?\s+|qui(?:etly)?\s+)*(save|saveold|export\s+delimited|outsheet|saveRDS|write[._]csv|write[._]dta|write[._]rds|haven::write_dta|saveRDS)\b[^\r\n]*?["\']?([\w./\\-]+\.(?:dta|csv|rds|rdata|tab|parquet))["\']?', re.IGNORECASE)
_FILE_EXISTS_GUARD = re.compile(r'(confirm\s+file|file\.exists|os\.path\.exists|assert\s+_rc|fileexists)', re.IGNORECASE)
# D1 table/figure section headers in comments (e.g. "* Table 3: ..." / "# Figure 2" / "# --> Table 1").
# The optional `(?:[-=]{1,2}>\s*)?` slot accepts the `-->`/`->`/`=>` anchor reproai itself recommends
# (A12/D1/A2 target_form), while the 1-2 char arrow-body rejects long arrows (`---->`), bullets
# (`# - Table`), and hrules (`# ----`). See test_table_header_matches_recommended_anchor.
#
# Follow-up B: the number group `_NUM_LABEL` captures the FULL label, not a truncated prefix.
#   - `[A-Za-z]{0,3}[-.]?` — appendix/SI prefixes: `A.1`, `E1`, `S1`, `SI-3`, `B2a` (1-3 letters,
#     optional `-`/`.` separator). 1-3 letters is deliberate: it admits `SI` but not whole words.
#   - `\d+(?:[.\-]\d+)*` — multi-segment numbers: `1`, `1.2`, `1-2`, `1.2.3`. This FIXES the old
#     `([A-Za-z]?\.?\d+)` silent partial-match where `Table 1.2` captured only `1`, MERGING
#     sub-tables 1.1 and 1.2 into one `_section_spans` group. They are now DISTINCT spans.
#   - `[a-z]?` — a trailing sub-table letter: `1a`, `B2a`.
# Known limitation: Roman-numeral labels (`Table II`) are not captured (rare; documented, not fixed).
_NUM_LABEL = r'([A-Za-z]{0,3}[-.]?\d+(?:[.\-]\d+)*[a-z]?)'
_TABLE_HEADER = re.compile(r'^\s*(?:\*+|//+|#+)\s*\**\s*(?:[-=]{1,2}>\s*)?\**\s*(?:[—–~]+\s*)?(Table|Tabla)\s+' + _NUM_LABEL + r'\b', re.IGNORECASE)
_FIGURE_HEADER = re.compile(r'^\s*(?:\*+|//+|#+)\s*\**\s*(?:[-=]{1,2}>\s*)?\**\s*(?:[—–~]+\s*)?(Figure|Fig\.?|Figura)\s+' + _NUM_LABEL + r'\b', re.IGNORECASE)

# A17 undefined R callable (issue #36). The detector is CONSERVATIVE by construction: it fires only
# when every library()/require() target is a package in the bundled export snapshot
# (rules/r_exports_db.json, regenerated via tools/gen_r_exports.R) — one unknown package silences
# the whole file, because that package's exports are unknowable statically. The callsite lookbehind
# excludes pkg::fn( / obj$fn( / S4 @slot( qualified calls; ANY name bound on an assignment LHS
# counts as defined (a variable may hold a function — `fmt <- make_formatter(...)` must never flag).
_R_LIB_CALL = re.compile(r'\b(?:library|require|requireNamespace|loadNamespace)\s*\(\s*["\']?([A-Za-z][\w.]*)')
_R_CALLSITE = re.compile(r'(?<![\w.$@:])([A-Za-z][\w.]*)\s*\(')
_R_DEF_ARROW = re.compile(r'\b([A-Za-z][\w.]*)\s*(?:<<?-|=(?![=<>]))')
_R_DEF_RIGHT = re.compile(r'->>?\s*([A-Za-z][\w.]*)')
_R_DEF_ASSIGN = re.compile(r'\bassign\s*\(\s*["\']([A-Za-z][\w.]*)["\']')
_R_FORMALS = re.compile(r'\bfunction\s*\(([^)]*)\)')
_R_FOR_VAR = re.compile(r'\bfor\s*\(\s*([A-Za-z][\w.]*)\s+in\b')
_R_KEYWORDS = frozenset({"if", "for", "while", "repeat", "function", "else", "break", "next",
                         "TRUE", "FALSE", "NULL", "NA", "Inf", "NaN", "in"})
# load()/attach() inject unseen names into the environment; Rcpp inline compiles new callables.
# Any of these makes the defined-set unknowable -> the file is skipped entirely.
_R_ENV_INJECTOR = re.compile(r'(?<![\w.])(?:load|attach|cppFunction|sourceCpp)\s*\(')
_R_BARE_SOURCE = re.compile(r'(?<![\w.$@:])(?:source|sys\.source)\s*\(')

_R_EXPORTS_FILE = Path(__file__).parent / "rules" / "r_exports_db.json"
_r_exports_cache: tuple[frozenset[str], dict[str, frozenset[str]], str] | None = None


def _r_exports() -> tuple[frozenset[str], dict[str, frozenset[str]], str]:
    """(base_names, {cran_pkg: exports}, snapshot_date) from the bundled snapshot; empty on any
    load failure, which silences A17 entirely (fail-open: never flag from a broken DB)."""
    global _r_exports_cache
    if _r_exports_cache is None:
        import json as _json
        try:
            db = _json.loads(_R_EXPORTS_FILE.read_text(encoding="utf-8"))
            base: set[str] = set()
            for names in db.get("base", {}).values():
                base.update(names)
            cran = {p: frozenset(n) for p, n in db.get("cran", {}).items()}
            _r_exports_cache = (frozenset(base), cran, str(db.get("generated", "")))
        except (OSError, ValueError, AttributeError):
            _r_exports_cache = (frozenset(), {}, "")
    return _r_exports_cache


# C8: stochastic operation with no seed (the generalization of C7, which owns the parallel %dopar%
# case). A seed FIXES the realized draws, so this is output-changing, not lossless.
_R_STOCHASTIC = re.compile(
    r'(?<![\w.])(sample|sample_n|slice_sample|rnorm|runif|rbinom|rpois|rbeta|rgamma|rexp|'
    r'rmultinom|rnbinom|rcauchy|rweibull|rchisq|rt|boot|amelia|mice)\s*\(', re.IGNORECASE)
_R_SEED_SIGNAL = re.compile(
    r'set\.seed\s*\(|registerDoRNG|%dorng%|clusterSetRNGStream|future\.seed\s*=|RNGkind\s*\(', re.IGNORECASE)
# `set.seed(as.numeric(Sys.time()))`, `set.seed(sample(1e6, 1))`: a seed drawn from the clock or from
# the RNG is no seed — the certification two-run test grades it T2 exactly like a bare draw. Such a
# line is stochastic evidence itself, and does not count as the seed signal above.
_R_CLOCK_SEED = re.compile(
    r'set\.seed\s*\(\s*[^)]*(?:Sys\.time|Sys\.Date|Sys\.getpid|sample\s*\(|runif\s*\(|as\.numeric\s*\(\s*Sys)', re.IGNORECASE)
_PY_CLOCK_SEED = re.compile(
    r'(?:random\.seed|np\.random\.seed|manual_seed|default_rng)\s*\(\s*[^)]*(?:time\.time|datetime|os\.getpid|urandom|uuid)', re.IGNORECASE)
_R_FUTURE_BACKEND = re.compile(r'\bfurrr\b|\bfuture_(?:map|lapply|apply|walk)\b|%<-%|\bfuture\s*\(', re.IGNORECASE)
_R_PARALLEL_BACKEND = re.compile(r'mclapply|makeCluster|parLapply|mcmapply|mcsapply', re.IGNORECASE)
_STATA_STOCHASTIC = re.compile(
    r'(?<![\w.])(bootstrap|bsample|permute|simulate)\b|runiform\s*\(|rnormal\s*\(|'
    r'rbinomial\s*\(|rpoisson\s*\(|rgamma\s*\(|rbeta\s*\(', re.IGNORECASE)
_STATA_SEED = re.compile(r'\bset\s+seed\b|\bset\s+rngstream\b', re.IGNORECASE)
# Python draws and the seed calls that tame them. `np.random.default_rng()` with no argument and
# `torch` without manual_seed draw OS entropy on every run; the certification prolog seeds
# `random` and the legacy `np.random` global but cannot reach a Generator built without a seed.
_PY_STOCHASTIC = re.compile(
    r'(?<![\w.])random\.(?:random|randint|choice|choices|sample|shuffle|gauss|uniform|normalvariate)\s*\(|'
    r'np\.random\.(?:default_rng|Generator|rand|randn|randint|choice|permutation|shuffle|normal|uniform|binomial)\s*\(|'
    r'numpy\.random\.\w+\s*\(|torch\.(?:rand|randn|randint|randperm|bernoulli|multinomial)\s*\(|'
    r'\bresample\s*\(|train_test_split\s*\(|KFold\s*\(|\.sample\s*\(\s*(?:frac|n)\s*=', re.IGNORECASE)
_PY_SEED_SIGNAL = re.compile(
    r'random\.seed\s*\(|np\.random\.seed\s*\(|numpy\.random\.seed\s*\(|default_rng\s*\(\s*\d|'
    r'default_rng\s*\(\s*(?:seed|SEED)|torch\.manual_seed\s*\(|random_state\s*=\s*\d|'
    r'PYTHONHASHSEED|CERTIFIED_SEED', re.IGNORECASE)

# C12: the wall clock or a process-unique path written into an output. Two certification runs of
# the same package then differ on that line, and the replication dataset grades T2 no matter how well seeded
# the analysis is. Only lines that also look like they WRITE are evidence; a `Sys.time()` used to
# time a loop and never written is harmless.
_R_WALLCLOCK = re.compile(
    r'Sys\.time\s*\(|Sys\.Date\s*\(|\bdate\s*\(\s*\)|format\s*\(\s*Sys\.|tempdir\s*\(|tempfile\s*\(|'
    r'timestamp\s*\(', re.IGNORECASE)
_PY_WALLCLOCK = re.compile(
    r'time\.time\s*\(|time\.ctime\s*\(|time\.strftime\s*\(|datetime\.(?:datetime\.)?now\s*\(|'
    r'datetime\.(?:datetime\.)?today\s*\(|date\.today\s*\(|tempfile\.\w+\s*\(|'
    r'uuid\.uuid[14]\s*\(|os\.getpid\s*\(', re.IGNORECASE)
_STATA_WALLCLOCK = re.compile(
    r'c\(current_date\)|c\(current_time\)|\$S_DATE|\$S_TIME|\bc\(tmpdir\)', re.IGNORECASE)
_R_WRITE_LINE = re.compile(
    r'\b(?:write\.csv2?|write\.table|write_csv|write_tsv|write_delim|fwrite|writeLines|saveRDS|'
    r'save|write_rds|write_dta|write_xlsx|cat|sink|print|stargazer|texreg|modelsummary|'
    r'ggsave|pdf|png)\s*\(', re.IGNORECASE)
_PY_WRITE_LINE = re.compile(
    r'\.to_csv\s*\(|\.to_excel\s*\(|\.to_stata\s*\(|\.to_parquet\s*\(|\.to_json\s*\(|\.write\s*\(|'
    r'\.writelines\s*\(|savefig\s*\(|\bprint\s*\(|json\.dump\s*\(|np\.save\w*\s*\(', re.IGNORECASE)
_STATA_WRITE_LINE = re.compile(
    r'\b(?:file\s+write|display|di\b|putexcel|esttab|estout|outreg2?|save|export|graph\s+export|'
    r'label\s+data|note\b|notes\b)', re.IGNORECASE)

# A18: a read whose path is assembled at run time (paste0/sprintf/f-string/format/os.path.join with
# a variable inside). Static checks cannot confirm the file ships; the certification audit records
# these as unidentified reads. A literal string argument is fine; a variable or a call is not.
_R_READ_HEAD = re.compile(
    r'(?<![\w.])(?:read\.csv2?|read\.delim2?|read\.table|read_csv2?|read_tsv|read_delim|read_table|'
    r'read_dta|read\.dta(?:13)?|read_stata|readRDS|read_rds|load|fread|st_read|read_excel|read_xlsx|'
    r'read_sav|read_spss|read_parquet|read_feather|import)\s*\(\s*(?P<arg>[^,)]+)', re.IGNORECASE)
_PY_READ_HEAD = re.compile(
    r'(?<![\w.])(?:pd\.read_\w+|pandas\.read_\w+|open|np\.load\w*|json\.load|pickle\.load|'
    r'gpd\.read_file|xr\.open_dataset)\s*\(\s*(?P<arg>[^,)]+)', re.IGNORECASE)
_LITERAL_ARG = re.compile(r'^\s*[rRbBuU]*(["\']).*\1\s*$')
_ASSEMBLED_ARG = re.compile(
    r'paste0?\s*\(|sprintf\s*\(|file\.path\s*\(|glue\s*\(|here\s*\(|os\.path\.join\s*\(|'
    r'\.format\s*\(|^\s*f["\']|\bPath\s*\(|%\s*\(|\+\s*["\']|["\']\s*\+|'
    r'(?<![\w.])(?:gzfile|bzfile|xzfile|unz|url|pipe|file)\s*\(', re.IGNORECASE)

# D7: variables used in estimation but absent from a shipped codebook. Tolerant, advisory, never P0.
_CODEBOOK_NAME = re.compile(
    r'codebook|data[\s_-]?dictionar|variable[\s_-]?(?:list|definition|description|name)|var[\s_-]?list|datadict',
    re.IGNORECASE)
_CODEBOOK_EXT = {".md", ".txt", ".tex", ".csv", ".rst"}
_VAR_TOKEN = re.compile(r'[A-Za-z][A-Za-z0-9_]{2,}')
_STATA_EST_VARLIST = re.compile(
    r'^\s*' + _STATA_PREFIX + r'(?:reg|regress|areg|xtreg|reghdfe|ivreg\w*|ivregress|ivreghdfe|'
    r'logit|probit|tobit|glm|xtivreg\w*|melogit|mlogit|poisson|nbreg|xtpoisson)\s+([^,\r\n]+)',
    re.IGNORECASE | re.MULTILINE)
_STATA_FACTOR_PREFIX = re.compile(r'\b[ibco]*\d*\.(\w+)', re.IGNORECASE)
_R_FORMULA = re.compile(r'([A-Za-z_.][\w.]*)\s*~\s*([^,\)\r\n]+)')
_VAR_STOP = {
    "using", "cluster", "robust", "vce", "absorb", "weight", "weights", "fweight", "pweight",
    "aweight", "iweight", "subset", "data", "factor", "log", "exp", "sqrt", "poly", "true",
    "false", "null", "and", "the", "for", "with",
}


@dataclass
class Finding:
    rule_id: str
    category: str
    kind: str
    priority: str
    message: str
    evidence: list[dict[str, Any]]
    rationale: str
    source_lessons: list[str]
    why_downstream: str = ""
    target_form: str = ""
    lossless_note: str = ""
    propose_only: bool = False
    output_changing: bool = False
    # set when a certification target (targets/) added the finding or re-worded its advice
    target: str = ""
    target_effect: str = ""


def load_rules() -> list[dict[str, Any]]:
    return yaml.safe_load(_RULES_FILE.read_text(encoding="utf-8"))["rules"]


def _texts(root: Path, entries: list[FileEntry]) -> dict[str, str]:
    out: dict[str, str] = {}
    for entry in entries:
        if entry.language in {"stata", "r", "python"}:
            # read_source unwraps .ipynb cells so the abs-path scan sees code, not JSON escapes (#34)
            out[entry.path] = read_source(root, entry.path)
    return out


def _ev(path: str, line: int | None = None, snippet: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"file": path}
    if line is not None:
        item["line"] = line
    if snippet is not None:
        item["snippet"] = snippet.strip()[:200]
    return item


_EVIDENCE_CAP = 50  # per-finding file-evidence entries before an EXPLICIT remainder marker (issue #43)


def _file_evidence(paths: list[str]) -> list[dict[str, Any]]:
    """One evidence entry per affected file — ALL of them up to _EVIDENCE_CAP, then a single explicit
    remainder marker carrying the overflow count and names. The old silent [:8] truncation surfaced
    the rest in waves across check/fix rounds (issue #43: 19 undocumented files took three rounds to
    enumerate); the author must see the full set the first time."""
    ordered = sorted(paths)
    evidence = [_ev(p) for p in ordered[:_EVIDENCE_CAP]]
    rest = ordered[_EVIDENCE_CAP:]
    if rest:
        evidence.append(_ev(f"(+{len(rest)} more)", None, ", ".join(rest)))
    return evidence


def _lang_of(entries: list[FileEntry], path: str) -> str:
    for e in entries:
        if e.path == path:
            return e.language
    return "other"


# --- Comment-aware line scanning (FIX: B4 and the line-by-line detector class false-firing in comments) -
# The defective callers below scan for CODE patterns (abs paths, time-series ops, wildcards, GitHub
# installs, ...). A path/pattern left inside a `#`/`*`/`//` comment — including by reproai's OWN /fix
# output (`# was: setwd("/Users/...")`) — must NOT fire. The hard constraint: we must strip the
# COMMENT while PRESERVING string literals, because _ABS_PATH reads a path *inside a quoted string*
# (`setwd("/abs")`). Blanking string contents (the rejected _mask_r_strings_comments approach) would
# make B4 catch nothing on its real case. Technique: mask only string *contents* in a throwaway copy
# to locate the first UNQUOTED comment marker, then slice the ORIGINAL line there so strings survive.
_STR_SPAN = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')


def _mask_string_contents(line: str, lang: str = "r") -> str:
    """Replace the *contents* of every complete string literal with same-length filler (keeping the
    delimiters and length), so comment markers inside strings are hidden but column indices are
    unchanged. An unterminated string masks to end-of-line (a `#`/`//` after an open quote is still
    inside it).

    Language-aware string syntax:
    - R / Python: both `"..."` and `'...'` are strings.
    - Stata: ONLY `"..."` and the compound `` `"..."' `` form are strings. A bare `'` is macro-close
      syntax (`` `macro' ``), NOT a string delimiter, so it must NOT open a masked span — otherwise an
      odd number of macro apostrophes before an inline `//` masks the comment marker away."""
    if lang == "stata":
        return _mask_string_contents_stata(line)
    out: list[str] = []
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if ch in '"\'':
            m = _STR_SPAN.match(line, i)
            if m:
                out.append(ch + ("x" * (m.end() - i - 2)) + ch)
                i = m.end()
                continue
            # unterminated literal: mask the rest of the line as string interior
            out.append(ch + ("x" * (n - i - 1)))
            break
        out.append(ch)
        i += 1
    return "".join(out)


def _mask_string_contents_stata(line: str) -> str:
    """Stata variant of _mask_string_contents. Strings are `"..."` and compound `` `"..."' ``; a bare
    `'` is a macro close, never a string delimiter, so it is emitted verbatim (leaving any following
    `//` comment marker visible)."""
    out: list[str] = []
    i, n = 0, len(line)
    while i < n:
        # compound double-quote string: `" ... "'
        if line.startswith('`"', i):
            close = line.find('"\'', i + 2)
            if close == -1:  # unterminated -> mask to EOL
                out.append('`"' + ("x" * (n - i - 2)))
                break
            out.append('`"' + ("x" * (close - (i + 2))) + '"\'')
            i = close + 2
            continue
        ch = line[i]
        if ch == '"':  # simple double-quote string
            close = line.find('"', i + 1)
            if close == -1:  # unterminated -> mask to EOL
                out.append('"' + ("x" * (n - i - 1)))
                break
            out.append('"' + ("x" * (close - i - 1)) + '"')
            i = close + 1
            continue
        out.append(ch)  # backtick, apostrophe, and everything else: literal (NOT a string)
        i += 1
    return "".join(out)


def _strip_comment_keep_strings(line: str, lang: str) -> str:
    """Return the CODE portion of one physical line: comment removed, string literals intact.

    R / Python: `#` (only when unquoted).
    Stata (.do/.ado): a line-leading `*` (whole line is a comment), an inline `//` (unquoted), and a
    single-line `/* ... */` (the spanned region). Multi-line `/* */` blocks across physical lines are
    a noted limitation — left intact.
    Unknown languages: returned unchanged (no false-negative risk for non-script file types)."""
    masked = _mask_string_contents(line, lang)
    if lang == "stata":
        # whole-line comment: first non-whitespace char is `*`
        stripped = masked.lstrip()
        if stripped.startswith("*"):
            return line[: len(line) - len(stripped)]  # keep leading whitespace only
        # single-line /* ... */ (remove every same-line balanced span; ignore unterminated openers)
        while True:
            open_i = masked.find("/*")
            if open_i == -1:
                break
            close_i = masked.find("*/", open_i + 2)
            if close_i == -1:
                break  # opener with no same-line closer -> multi-line; leave as-is (noted limitation)
            line = line[:open_i] + " " * (close_i + 2 - open_i) + line[close_i + 2 :]
            masked = masked[:open_i] + " " * (close_i + 2 - open_i) + masked[close_i + 2 :]
        # inline // comment (unquoted)
        slash = masked.find("//")
        if slash != -1:
            return line[:slash]
        return line
    if lang in {"r", "python"}:
        hash_i = masked.find("#")
        if hash_i != -1:
            return line[:hash_i]
        return line
    return line


def _code_line_hits(text: str, regex: re.Pattern[str], lang: str) -> list[tuple[int, str]]:
    """Per-line regex scan that matches `regex` against the comment-stripped CODE portion of each line
    (string literals preserved) while RETURNING the original line and its real 1-based line number,
    so evidence still shows the true source line."""
    hits = []
    for i, line in enumerate(text.splitlines(), start=1):
        if regex.search(_strip_comment_keep_strings(line, lang)):
            hits.append((i, line))
    return hits


def _abs_path_file_hits(text: str, lang: str) -> list[tuple[int, str]]:
    """(line_no, original_line) absolute-path hits for ONE file, comment-aware per language. This is
    the single scanner behind BOTH the B4 advisory and the venue no_absolute_paths check (issue #42:
    the two used to scan differently — B4 comment-aware, venue raw — so a package could be advisory-
    clean and venue-FAILING on the same criterion at the same time)."""
    if lang == "sas":
        # SAS comments span lines (`* ...;` and /* */), so the per-line comment stripper cannot
        # serve; _blank_sas_comments blanks them block-wise keeping line indices, and evidence
        # shows the RAW line (the blanked text is match-only) — same contract as issue #32.
        raw_lines = text.splitlines()
        return [(i, raw_lines[i - 1])
                for i, ln in enumerate(_blank_sas_comments(text).splitlines(), start=1)
                if _ABS_PATH.search(ln)]
    hits = _code_line_hits(text, _ABS_PATH_ESCAPED if lang in {"r", "python"} else _ABS_PATH, lang)
    seen = {i for i, _ in hits}
    hits += [(i, ln) for i, ln in _code_line_hits(text, _PARENT_ESCAPE, lang) if i not in seen]
    return sorted(hits)


def abs_path_hits(root: Path, entries: list[FileEntry]) -> list[tuple[str, int, str]]:
    """(path, line_no, line) absolute-path hits across every scannable code file — venue_engine's
    no_absolute_paths check consumes this so its verdict can never contradict the B4 count (#42)."""
    hits: list[tuple[str, int, str]] = []
    for e in entries:
        if e.language in {"stata", "r", "python", "sas"}:
            for line_no, line in _abs_path_file_hits(read_source(root, e.path), e.language):
                hits.append((e.path, line_no, line))
    return hits


def _upstream_loads_data(path: str, edges: list[Edge], texts: dict[str, str], loader: re.Pattern[str]) -> bool:
    parents = [e.src for e in edges if e.kind in {"do", "source"} and e.resolved and e.dst == path]
    for parent in parents:
        ptext = texts.get(parent, "")
        marker = f'"{Path(path).name}"'
        idx = ptext.find(Path(path).name)
        prefix = ptext[:idx] if idx != -1 else ptext
        if loader.search(prefix):
            return True
        if _upstream_loads_data(parent, edges, texts, loader):
            return True
    return False


def _detect_guarded_fallback(root: Path, path: str, text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        m = _CAPTURE_USE.search(line)
        if not m:
            continue
        file_a = m.group(1).strip()
        for j in range(i + 1, min(i + 4, len(lines))):
            if _RC_GUARD.search(lines[j]):
                block = "\n".join(lines[j:j + 6])
                gm = _GUARD_USE.search(block)
                if gm:
                    file_b = gm.group(1).strip()
                    a_exists = (root / Path(file_a).name).exists() or any(p.name == Path(file_a).name for p in root.rglob(Path(file_a).name))
                    b_exists = (root / Path(file_b).name).exists() or any(p.name == Path(file_b).name for p in root.rglob(Path(file_b).name))
                    if a_exists and b_exists and Path(file_a).name != Path(file_b).name:
                        hits.append(_ev(path, i + 1, line))
                break
    return hits


def _mask_r_strings_comments(s: str) -> str:
    out = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    out = re.sub(r"'(?:\\.|[^'\\])*'", "''", out)
    out = re.sub(r'#.*', '', out)
    return out


_R_ORPHAN_ARG = re.compile(r'^\s*[A-Za-z_][\w.]*\s*=')


def _detect_r_table_syntax(path: str, text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        if not _R_TABLE_CALL.search(line):
            continue
        window = lines[i:i + 40]
        depth = 0
        started = False
        balanced_at = None
        went_negative = False
        for k, w in enumerate(window):
            masked = _mask_r_strings_comments(w)
            for ch in masked:
                if ch == "(":
                    depth += 1
                    started = True
                elif ch == ")":
                    depth -= 1
                    if started and depth < 0:
                        went_negative = True
            if started and depth <= 0:
                balanced_at = k
                break
        if started and balanced_at is None:
            hits.append(_ev(path, i + 1, line))
            continue
        if went_negative:
            hits.append(_ev(path, i + 1, line))
            continue
        if started and balanced_at is not None:
            for w in window[balanced_at + 1: balanced_at + 3]:
                masked = _mask_r_strings_comments(w).strip()
                if _R_ORPHAN_ARG.match(masked):
                    hits.append(_ev(path, i + 1 + balanced_at, w))
                    break
    return hits


def _detect_lifecycle_contradiction(path: str, text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    dropped: dict[str, int] = {}
    renamed_away: dict[str, int] = {}
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(lines, start=1):
        dm = _STATA_DROP.match(line)
        if dm:
            if _DROP_OBS.match(dm.group(1)):
                continue  # `drop if`/`drop in` deletes rows, not columns — no variable leaves
            for v in re.findall(r'\b[A-Za-z_]\w*\b', dm.group(1)):
                dropped[v] = i
            continue
        rn = _STATA_RENAME.match(line)
        if rn:
            renamed_away[rn.group(1)] = i
            dropped.pop(rn.group(2), None)
            renamed_away.pop(rn.group(2), None)
            continue
        gen = re.match(r'^\s*(?:gen(?:erate)?|egen|clonevar|recode)\b.*?\b([A-Za-z_]\w*)\s*=', line, re.IGNORECASE)
        if gen:
            dropped.pop(gen.group(1), None)
            renamed_away.pop(gen.group(1), None)
        if _ESTIMATION.match(line):
            for v in re.findall(r'\b[A-Za-z_]\w*\b', line):
                if v in dropped:
                    hits.append(_ev(path, i, f"uses '{v}' dropped at line {dropped[v]}: {line.strip()[:120]}"))
                elif v in renamed_away:
                    hits.append(_ev(path, i, f"uses '{v}' renamed away at line {renamed_away[v]}: {line.strip()[:120]}"))
    return hits


def _shipped_stems(root: Path) -> dict[str, list[str]]:
    stems: dict[str, list[str]] = {}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in _DATA_EXTS:
            stems.setdefault(path.stem.lower(), []).append(path.name)
    return stems


def _detect_data_ref_mismatch(root: Path, path: str, text: str, stems: dict[str, list[str]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        m = _DATA_REF.match(line)
        if not m:
            continue
        target = m.group(2).strip().replace("\\", "/")
        name = Path(target).name
        stem = Path(name).stem.lower()
        suffix = Path(name).suffix.lower()
        # Stata's `use dataset` implicitly loads dataset.dta. An exact
        # packaged path is sufficient; another folder's basename is not.
        if not suffix and m.group(1).lower() == "use" and (root / (target + ".dta")).is_file():
            continue
        resolved = (root / name).exists() or any(p.name == name for p in root.rglob(name))
        if resolved:
            continue
        shipped = stems.get(stem)
        if shipped and (not suffix or all(Path(s).suffix.lower() != suffix for s in shipped)):
            hits.append(_ev(path, i, f"references '{name}' but package ships {shipped}"))
    return hits


def _detect_relative_cd(path: str, text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        match = _REL_CD.match(line)
        if match and match.group(1).strip().rstrip("/") != ".":
            hits.append(_ev(path, i, line))
    return hits


def _detect_compat_signatures(path: str, text: str, has_version: bool) -> list[dict[str, Any]]:
    # Follow-up C: every scanner here is comment-blind unless it reads the comment-stripped CODE
    # portion. `_detect_compat_signatures` is only ever called on Stata (.do/.ado) — see the
    # `if lang == "stata":` dispatch — so strip with lang="stata". A commented `tmpdir`
    # (`* note: tmpdir` / `// tmpdir`) or any of the other commented signatures must stay silent,
    # while real code still fires. Evidence snippets keep the ORIGINAL line.
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        code = _strip_comment_keep_strings(line, "stata")
        if _REGHDFE_IV.search(code):
            hits.append(_ev(path, i, f"reghdfe IV-syntax (use ivreghdfe or pin version): {line.strip()[:90]}"))
        elif _RDROBUST_DEPR.search(code):
            hits.append(_ev(path, i, f"rdrobust deprecated bwselect(): {line.strip()[:90]}"))
        elif _TABLE_C.match(code):
            hits.append(_ev(path, i, f"`table var, c(...)` removed in Stata 17: {line.strip()[:90]}"))
        elif _TMPDIR.search(code) and not has_version:
            hits.append(_ev(path, i, f"tmpdir needs Stata 17+; declare version: {line.strip()[:90]}"))
        elif _LEGACY_MIXED.match(code):
            hits.append(_ev(path, i, f"legacy mixed-model command (hangs/removed on modern Stata; use me-prefix): {line.strip()[:90]}"))
        elif _CD_EMPTY.match(code):
            hits.append(_ev(path, i, "`cd \"\"` switches to HOME and breaks relative data paths"))
    return hits


def _detect_old_merge(path: str, text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if _OLD_MERGE.match(line):
            hits.append(_ev(path, i, line))
    return hits


def _detect_deprecated_r_pkg(path: str, text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        m = _DEPRECATED_R_PKG.search(line)
        if m:
            hits.append(_ev(path, i, f"{m.group(1)} is removed/deprecated and halts the script if loaded"))
    return hits


def _detect_nonreproducible_parallel_rng(path: str, text: str) -> list[dict[str, Any]]:
    masked = _mask_r_strings_comments(text)
    if not _PAR_DOPAR.search(masked) or _PAR_REPRO.search(masked):
        return []
    for i, line in enumerate(text.splitlines(), start=1):
        if _PAR_DOPAR.search(_mask_r_strings_comments(line)):
            return [_ev(path, i, line)]
    return []


def _detect_unseeded_stochastic(path: str, text: str, lang: str) -> list[dict[str, Any]]:
    if lang == "r":
        masked = _mask_r_strings_comments(text)
        if _PAR_DOPAR.search(masked):
            return []  # the parallel %dopar% case is C7's, not C8's
        clock_seed = _R_CLOCK_SEED.search(masked)
        if clock_seed:
            line_no = masked[:clock_seed.start()].count("\n") + 1
            return [_ev(path, line_no, "the seed is drawn from the clock or the RNG, so it is no seed --- set.seed(N) with a fixed integer")]
        if _R_SEED_SIGNAL.search(masked) or not _R_STOCHASTIC.search(masked):
            return []
        if _R_FUTURE_BACKEND.search(masked):
            hint = "future/furrr backend: set future.seed = TRUE (or a seed)"
        elif _R_PARALLEL_BACKEND.search(masked):
            hint = "parallel backend: RNGkind(\"L'Ecuyer-CMRG\") then set.seed(N)"
        elif re.search(r'(?<![\w.])amelia\s*\(', masked, re.IGNORECASE):
            hint = "Amelia: pass the seed= argument"
        elif re.search(r'(?<![\w.])mice\s*\(', masked, re.IGNORECASE):
            hint = "mice: pass the seed= argument"
        else:
            hint = "serial draw: set.seed(N) before the first draw"
        for i, line in enumerate(text.splitlines(), start=1):
            if _R_STOCHASTIC.search(_mask_r_strings_comments(line)):
                return [_ev(path, i, f"stochastic draw with no seed set --- {hint}")]
        return []
    if lang == "python":
        code_lines = [(i, ln) for i, ln in enumerate(text.splitlines(), start=1)
                      if not ln.strip().startswith("#")]
        code = "\n".join(ln for _, ln in code_lines)
        clock_seed = _PY_CLOCK_SEED.search(code)
        if clock_seed:
            line_no = code[:clock_seed.start()].count("\n")
            return [_ev(path, code_lines[line_no][0], "the seed is drawn from the clock or the OS, so it is no seed --- seed with a fixed integer")]
        if _PY_SEED_SIGNAL.search(code) or not _PY_STOCHASTIC.search(code):
            return []
        for i, line in code_lines:
            if _PY_STOCHASTIC.search(line):
                if "default_rng" in line or "Generator" in line:
                    hint = "np.random.default_rng(N): a Generator built without a seed draws OS entropy every run"
                elif "torch." in line:
                    hint = "torch.manual_seed(N) before the first draw"
                elif "random_state" in line or "train_test_split" in line or "KFold" in line:
                    hint = "pass random_state=N"
                else:
                    hint = "random.seed(N) / np.random.seed(N) before the first draw"
                return [_ev(path, i, f"stochastic draw with no seed set --- {hint}")]
        return []
    # stata
    if _STATA_SEED.search(text) or not _STATA_STOCHASTIC.search(text):
        return []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("*") or stripped.startswith("//"):
            continue
        if _STATA_STOCHASTIC.search(line):
            return [_ev(path, i, "stochastic command with no `set seed` --- set seed N (set rngstream under parallel)")]
    return []


_CERT_SIZE_CAP_MB = 1000  # reproai-cert issuer_service C_size_bytes: one ceiling, decimal MB


def _detect_package_size(entries: list[FileEntry]) -> list[dict[str, Any]]:
    total = sum(e.size_bytes for e in entries)
    if total <= _CERT_SIZE_CAP_MB * 1_000_000:
        return []
    biggest = sorted(entries, key=lambda e: -e.size_bytes)[:5]
    return [_ev(e.path, None, f"{e.size_bytes / 1_000_000:.0f} MB of {total / 1_000_000:.0f} MB total")
            for e in biggest]


def _detect_wallclock_in_output(path: str, text: str, lang: str) -> list[dict[str, Any]]:
    clock, write = {
        "r": (_R_WALLCLOCK, _R_WRITE_LINE),
        "python": (_PY_WALLCLOCK, _PY_WRITE_LINE),
        "stata": (_STATA_WALLCLOCK, _STATA_WRITE_LINE),
    }[lang]
    lines = text.splitlines()
    clock_names: set[str] = set()
    hits: list[dict[str, Any]] = []
    for i, raw in enumerate(lines, start=1):
        code = _strip_comment_keep_strings(raw, lang)
        if not code.strip():
            continue
        has_clock = bool(clock.search(code))
        if has_clock and write.search(code):
            hits.append(_ev(path, i, raw.strip()[:120]))
            continue
        if has_clock:
            m = re.match(r'\s*([A-Za-z_][\w.]*)\s*(?:<-|=|:=)', code)
            if m:
                clock_names.add(m.group(1))
            continue
        if clock_names and write.search(code) and any(
                re.search(rf'(?<![\w.]){re.escape(n)}(?!\w)', code) for n in clock_names):
            hits.append(_ev(path, i, raw.strip()[:120]))
    return hits[:6]


def _detect_runtime_assembled_read(path: str, text: str, lang: str) -> list[dict[str, Any]]:
    head = _R_READ_HEAD if lang == "r" else _PY_READ_HEAD
    hits: list[dict[str, Any]] = []
    for i, raw in enumerate(text.splitlines(), start=1):
        code = _strip_comment_keep_strings(raw, lang)
        for m in head.finditer(code):
            arg = m.group("arg").strip()
            if not arg or _LITERAL_ARG.match(arg):
                continue
            if arg.startswith(("file", "con", "text", "url")) and "=" in arg:
                continue
            if _ASSEMBLED_ARG.search(arg) or re.match(r'^[A-Za-z_][\w.]*$', arg):
                hits.append(_ev(path, i, f"{raw.strip()[:100]} --- path is `{arg[:40]}`, not a literal"))
                break
    return hits[:6]


def _used_variables(text: str, lang: str) -> set[str]:
    used: set[str] = set()
    if lang == "stata":
        for m in _STATA_EST_VARLIST.finditer(text):
            varlist = _STATA_FACTOR_PREFIX.sub(r'\1', m.group(1))
            used |= {t.lower() for t in _VAR_TOKEN.findall(varlist)}
    elif lang == "r":
        for m in _R_FORMULA.finditer(text):
            for side in (m.group(1), m.group(2)):
                cleaned = re.sub(r'[A-Za-z_.][\w.]*\s*\(', ' ', side)  # drop function-call heads, keep their args
                used |= {t.lower() for t in _VAR_TOKEN.findall(cleaned)}
    return used


def _detect_codebook_coverage(root: Path, entries: list[FileEntry], texts: dict[str, str]) -> list[dict[str, Any]]:
    cb_text: str | None = None
    cb_path: str | None = None
    for e in entries:
        name = Path(e.path).name
        if _CODEBOOK_NAME.search(name) and Path(name).suffix.lower() in _CODEBOOK_EXT:
            try:
                cb_text = (root / e.path).read_text(encoding="utf-8", errors="replace").lower()
                cb_path = e.path
                break
            except OSError:
                continue
    if cb_text is None:  # no readable codebook -> D7 is silent (D4 owns "no documentation at all")
        return []
    used: set[str] = set()
    for path, text in texts.items():
        used |= _used_variables(text, _lang_of(entries, path))
    undocumented = sorted(v for v in used if v not in _VAR_STOP and v not in cb_text)
    if not undocumented:
        return []
    evidence_path = cb_path or "(codebook)"
    return [_ev(evidence_path, None,
                f"{len(undocumented)} analysis variable(s) absent from the codebook: {', '.join(undocumented[:12])}")]


def _detect_rmd_chunk(path: str, text: str) -> list[dict[str, Any]]:
    in_chunk = False
    opener: tuple[int, str] | None = None
    scan = r_standalone_fence_lines(text)
    if isinstance(scan, str):
        return []
    for i, line in scan:
        if _RMD_CHUNK.match(line):
            if in_chunk:
                return [_ev(path, i, line)]
            in_chunk = True
            opener = (i, line)
            continue
        if _RMD_FENCE_CLOSE.match(line):
            if not in_chunk:
                return [_ev(path, i, line)]
            return [_ev(path, i, line)]
    if opener is not None:
        return [_ev(path, opener[0], opener[1])]
    return []


def _detect_embedded_foreign(path: str, text: str) -> list[dict[str, Any]]:
    est = _ESTIMATION.search(text)
    cutoff = est.start() if est else len(text)
    head = text[:cutoff]
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(head.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("*") or stripped.startswith("//"):
            continue
        if _R_IN_DO.search(line):
            hits.append(_ev(path, i, line))
            break
    return hits


def _detect_stata_transcript(path: str, text: str) -> list[dict[str, Any]]:
    """A .do that is a pasted interactive-session transcript: command lines keep their `. ` console
    prompt and/or comment lines start with `#`. Either makes `do` halt with r(199) on the first such
    line, so a package whose only entry point is a transcript would otherwise pass check silently
    (issue #31). Statement-start anchored; `*`/`//` comments skipped; #delimit excluded by the regex."""
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("*", "//")):
            continue
        if _STATA_PROMPT.match(line) or _STATA_HASH_STMT.match(line):
            hits.append(_ev(path, i, stripped[:120]))
            if len(hits) >= 5:
                break
    return hits


def _r_code_lines(text: str) -> list[tuple[int, str]]:
    """(line_no, code) pairs with comments stripped and string CONTENTS masked — a callable name
    inside a message() string or a comment must never count as a callsite or a definition."""
    out: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        out.append((i, _mask_string_contents(_strip_comment_keep_strings(line, "r"), "r")))
    return out


def _r_defined_names(texts: dict[str, str], lang_of) -> set[str]:
    """Every name bound anywhere in the replication dataset's R files: assignment LHS (<-, =, <<-, ->, assign),
    formal parameters, for-loop variables. Pooled GLOBALLY across files — over-suppression only
    costs missed detections on an advisory rule; there is no credit pathway, so both invariants
    hold. Named call arguments (foo(x=3)) over-define x — deliberate and conservative."""
    defined: set[str] = set()
    for p, t in texts.items():
        if lang_of(p) != "r":
            continue
        for _i, code in _r_code_lines(t):
            for rx in (_R_DEF_ARROW, _R_DEF_RIGHT, _R_DEF_ASSIGN, _R_FOR_VAR):
                defined.update(m.group(1) for m in rx.finditer(code))
            for m in _R_FORMALS.finditer(code):
                for arg in m.group(1).split(","):
                    name = arg.split("=")[0].strip()
                    if re.fullmatch(r"[A-Za-z][\w.]*", name):
                        defined.add(name)
    return defined


def _r_callable_allow_set(texts: dict[str, str], edges: list[Edge], lang_of, skip: set[str]) -> set[str] | None:
    """The replication dataset-level allow set for A17, or None when the replication dataset is not assessable. Computed
    ONCE over all R files (minus `skip`): library() and load()/attach() act on R's GLOBAL
    environment, so a helper file sourced by a master that loads CVXR sees CVXR's exports — libs,
    env-injectors, and source-resolution must all be judged package-globally, not per file.
    Not assessable when: any loaded package is outside the snapshot (its exports are unknowable),
    any load()/attach()/Rcpp-inline injects unseen names, or any source() call has no resolved
    include edge (a source(sprintf(...)) target's definitions are unknowable)."""
    base, cran, _generated = _r_exports()
    if not base:
        return None
    libs: set[str] = set()
    bare_sources = 0
    for p, t in texts.items():
        if lang_of(p) != "r" or p in skip:
            continue
        for _i, code in _r_code_lines(t):
            libs.update(m.group(1) for m in _R_LIB_CALL.finditer(code))
            if _R_ENV_INJECTOR.search(code):
                return None
            bare_sources += len(_R_BARE_SOURCE.findall(code))
    if any(lib not in cran for lib in libs):
        return None
    resolved_includes = sum(1 for e in edges if e.kind == "source" and e.resolved and e.src not in skip)
    if bare_sources > resolved_includes:
        return None
    allow = set(base) | _R_KEYWORDS
    for lib in libs:
        allow |= cran[lib]
    return allow


def _detect_undefined_r_callable(path: str, text: str, allow: set[str] | None) -> list[dict[str, Any]]:
    """A17 (issue #36): a called name that is defined nowhere in the replication dataset and exported by no
    declared library halts R at that line with 'could not find function'. `allow` is the
    package-level set (snapshot exports of every loaded lib + every LHS-bound name + keywords);
    None means the replication dataset is not assessable and the rule stays silent."""
    if allow is None:
        return []
    raw_lines = text.splitlines()
    hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, code in _r_code_lines(text):
        for m in _R_CALLSITE.finditer(code):
            name = m.group(1)
            if name in allow or name in seen:
                continue
            seen.add(name)
            hits.append(_ev(path, i, f"'{name}' called but defined nowhere: {raw_lines[i - 1].strip()[:100]}"))
            if len(hits) >= 8:
                return hits
    return hits


def _detect_unvendored_ado(root: Path, path: str, text: str) -> list[dict[str, Any]]:
    # An `ssc install` line used to silence this rule. It no longer does: the
    # downstream certification line refuses runtime code fetch outright (its
    # closure check forbids network and out-of-package reads), so the only
    # form that survives is the .ado shipped inside the replication dataset. The install
    # line itself is now C10's defect.
    shipped_ado = {p.stem.lower() for p in root.rglob("*.ado")}
    hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("*") or stripped.startswith("//"):
            continue
        m = _CMD_HEAD.match(line)
        if not m:
            continue
        cmd = m.group(1).lower()
        if cmd in _KNOWN_USER_ADO and cmd not in shipped_ado and cmd not in seen:
            seen.add(cmd)
            hits.append(_ev(path, i, f"uses user-written '{cmd}' (not base Stata, no .ado shipped)"))
    return hits


def _detect_runtime_code_fetch(path: str, text: str, lang: str) -> list[dict[str, Any]]:
    """C10: a script line that downloads code from the internet at run time.

    Stata: `ssc install` / `net install`. R: `install.packages` and the
    devtools/remotes/pak family. The certified run is closed — it may not
    reach the network — so these lines make the replication dataset uncertifiable no
    matter how they are guarded."""
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith(("*", "//", "#")):
            continue
        if lang == "stata" and SSC_INSTALL_RE.match(line):
            hits.append(_ev(path, i, stripped[:120]))
        elif lang == "r" and _R_RUNTIME_INSTALL.search(line):
            hits.append(_ev(path, i, stripped[:120]))
    return hits


_R_RUNTIME_INSTALL = re.compile(
    r'\b(?:install\.packages|(?:devtools|remotes)::install_\w+|pak::pak|pak::pkg_install)\s*\(')


def _detect_external_adopath(path: str, text: str) -> list[dict[str, Any]]:
    """C11: adopath/sysdir pointing outside the replication dataset. On any other machine
    that directory does not exist, and downstream the closure check refuses
    the read; code the script needs must ship inside the replication dataset."""
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("*") or stripped.startswith("//"):
            continue
        m = ADOPATH_RE.match(line)
        if m and is_external(m.group("target")):
            hits.append(_ev(path, i, stripped[:120]))
    return hits


def _detect_commented_restricted(path: str, text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        if not _COMMENTED_REG.match(line):
            continue
        window = "\n".join(lines[max(0, i - 3): i + 4])
        if _RESTRICTED_WORD.search(window):
            hits.append(_ev(path, i + 1, line))
    return hits


def _detect_delimit(path: str, text: str) -> list[dict[str, Any]]:
    for i, line in enumerate(text.splitlines(), start=1):
        if _DELIMIT.match(line):
            return [_ev(path, i, line)]
    return []


def _detect_long_r_table_call(path: str, text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        if not _R_TABLE_CALL_LONG.search(line):
            continue
        depth = 0
        started = False
        span = 0
        for w in lines[i:i + 60]:
            masked = _mask_r_strings_comments(w)
            for ch in masked:
                if ch == "(":
                    depth += 1
                    started = True
                elif ch == ")":
                    depth -= 1
            span += 1
            if started and depth <= 0:
                break
        if span > 15:
            hits.append(_ev(path, i + 1, f"{line.strip()[:60]} ... spans {span} lines"))
    return hits


def _detect_wrapper_estimation(path: str, text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    hits: list[dict[str, Any]] = []
    in_program = None
    depth = 0
    for i, line in enumerate(lines, start=1):
        pm = _PROGRAM_DEF.match(line)
        if pm:
            in_program = pm.group(1)
            continue
        if in_program and re.match(r'^\s*end\b', line):
            in_program = None
            continue
        if in_program and _ESTIMATION.match(line):
            hits.append(_ev(path, i, f"estimation inside program '{in_program}': {line.strip()[:90]}"))
    return hits


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


def _has_toplevel_estimation(text: str) -> bool:
    return len(_toplevel_estimation_lines(text)) > 0


# A table/figure export only counts for D1 if it writes under a designated `tables/`/`figures/`
# subfolder — same rule as `reproai gate`, so `reproai check` (D1) and the gate agree on what is
# "exported". Keep this in lockstep with gate._OUT_TABLE/_OUT_FIGURE and the inline target-extractor
# in gate._section_export_targets.
#
# Follow-up D (recommend≡detect): D1's `rule` advises "a designated relative output folder (e.g.
# output/tables, output/figures)", but the detector hard-required the literal `output/` prefix, so
# `results/tables/`, `tables/`, etc. failed. The optional `(?:[\w.\-]+[\\/])*` prefix now accepts any
# (or no) leading path before the `tables/`/`figures/` segment, so `output/tables/`,
# `results/tables/`, and bare `tables/` all satisfy the intent. The `tables/`/`figures/` SEGMENT is
# still required, so the misnamed-export bypass (`esttab using "mytable.csv"`) is still rejected.
#
# Follow-up D fix: a left boundary `(?:^|[\\/])` is REQUIRED before the `tables/`/`figures/` segment.
# Without it, `.search` matched `tables/` as a SUBSTRING of a longer directory name (`mytables/`,
# `notes_tables/`, `vegetables/`, ...), wrongly clearing a "no canonical output folder" case (D1
# false negative) and disagreeing with the gate's quote-anchored inline regex. The boundary forces
# `tables`/`figures` to start at the path head or right after a separator.
_OUT_TABLE_PATH = re.compile(r'''(?:^|[\\/"'])(?:[\w.\-]+[\\/])*tables[\\/]''', re.IGNORECASE)
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


def _detect_uncaptured_artifacts(path: str, text: str, lang: str = "stata") -> list[dict[str, Any]]:
    # lang == "python" is LABELED-ANCHOR-ONLY (issue #33): python bodies use the _PY_* vocabulary
    # inside `# Table N`/`# Figure N` sections, and the unlabeled fallbacks are skipped entirely —
    # otherwise every helper .py with an estimation-looking call would become a phantom artifact.
    lines = text.splitlines()
    hits: list[dict[str, Any]] = []
    is_py = lang == "python"
    tbl_export = _PY_TABLE_EXPORT if is_py else _TABLE_EXPORT

    table_spans = _section_spans(lines, _TABLE_HEADER)
    if table_spans:
        for label, start, end in table_spans:
            body = lines[start:end]
            has_est = any(_is_estimation(ln) or (is_py and _PY_TABLE_BODY.search(ln)) for ln in body)
            has_exp = _has_canonical_export(body, tbl_export, _OUT_TABLE_PATH)
            if has_est and not has_exp:
                hits.append(_ev(path, start + 1, f"{label}: estimations build this table but no export saves it to output/tables/"))
    elif not is_py:
        needing = _toplevel_estimations_needing_table(text)
        has_exp = _has_canonical_export(lines, _TABLE_EXPORT, _OUT_TABLE_PATH)
        if needing and not has_exp:
            hits.append(_ev(path, needing[0], "estimations build a table but no export saves coefficients to output/tables/"))

    figure_spans = _section_spans(lines, _FIGURE_HEADER)
    if figure_spans:
        for label, start, end in figure_spans:
            body = lines[start:end]
            has_graph = any(_GRAPH_CMD.search(ln) or (is_py and _PY_GRAPH_BODY.search(ln)) for ln in body)
            has_exp = _has_canonical_export(body, _GRAPH_EXPORT, _OUT_FIGURE_PATH)
            if has_graph and not has_exp:
                hits.append(_ev(path, start + 1, f"{label}: figure produced but no graph-export saves it to output/figures/"))
    elif not is_py:
        gline = _toplevel_graph_line(text)
        has_exp = _has_canonical_export(lines, _GRAPH_EXPORT, _OUT_FIGURE_PATH)
        if gline is not None and not has_exp:
            hits.append(_ev(path, gline, "figure produced but no graph-export saves it to output/figures/"))
    return hits


def _detect_missing_table_comments(path: str, text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    est_lines = _toplevel_estimation_lines(text)
    if len(est_lines) < 2:
        return []
    has_table_comment = any(_TABLE_HEADER.search(ln) or _FIGURE_HEADER.search(ln) for ln in lines)
    if has_table_comment:
        return []
    return [_ev(path, est_lines[0], f"{len(est_lines)} estimation commands, none anchored by a `* --> Table N` comment")]


def _detect_intermediate_data(root: Path, path: str, text: str, edges: list[Edge], texts: dict[str, str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        m = _DATA_WRITE.search(line)
        if not m:
            continue
        target = m.group(2).strip().replace("\\", "/")
        name = Path(target).name
        read_elsewhere = any(name in t for p, t in texts.items() if p != path)
        if not read_elsewhere:
            continue
        in_data_dir = "data/" in target.lower() or target.lower().startswith("data")
        if not in_data_dir:
            hits.append(_ev(path, i, f"writes intermediate '{name}' read by another script, but not under a canonical data/ folder"))
    return hits


def _detect_duplicate_readmes(root: Path) -> list[dict[str, Any]]:
    # group README-like files by (folder, stem): a same-name README.md + README.pdf is ONE document
    # in two formats (not flagged); distinct names or folders are separate drafts that can diverge.
    groups: dict[tuple[str, str], list[str]] = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if "readme" in p.name.lower() and p.suffix.lower() in {".md", ".txt", ".pdf", ".rst"}:
            groups.setdefault((rel.parent.as_posix(), p.stem.lower()), []).append(rel.as_posix())
    if len(groups) <= 1:
        return []
    return [_ev(sorted(paths)[0]) for paths in groups.values()]


# D6: README references a path that isn't in the replication dataset. Conservative — only backtick-quoted path
# tokens in a markdown/text README (an author who writes `code/x.R` or `data/` in backticks means a
# real path). Folder-tree diagrams, prose, and PDF-extracted text never trigger it, so an illustrative
# tree root like `replication/` is not mistaken for a missing folder.
_README_PATHISH_EXT = (
    ".r", ".do", ".py", ".csv", ".dta", ".rds", ".rdata", ".xlsx", ".xls", ".sav",
    ".txt", ".tsv", ".parquet", ".ipynb", ".sql", ".rmd", ".qmd",
)
_README_BACKTICK = re.compile(r'`([^`\n]{1,80})`')


def _readme_pathish(tok: str) -> bool:
    tok = tok.strip()
    if not tok or " " in tok or "://" in tok:
        return False
    if tok.startswith(("http", "www.", "#", "@", "-", "$", "~")):
        return False
    if any(c in tok for c in "()=*<>|\"'{}!?,;"):
        return False
    return tok.endswith("/") or tok.lower().endswith(_README_PATHISH_EXT)


# README wording that documents a path as deliberately absent (restricted/not shipped). When it sits
# near a backtick path token, the token is a known omission, not a packaging mistake — do not flag it.
_ABSENT_WORDING = re.compile(
    r'not\s+(?:included|provided|shipped|available|public|distribut\w*|part\s+of)|'
    r'restrict\w*|confidential|propriet\w*|available\s+(?:up)?on\s+request|by\s+request|'
    r'cannot\s+be\s+(?:shared|included)|excluded|obtain\w*\s+(?:from|separately)',
    re.IGNORECASE,
)
_BRACE = re.compile(r'\{([^{}]*)\}')
_BRACE_RANGE = re.compile(r'^(\d+)\.\.(\d+)$')


def _expand_braces(tok: str) -> list[str]:
    """Expand a brace/ellipsis glob like `wave_{1,2,3}.dta` or `fig_{1..3}.pdf` into concrete names,
    so each member is checked against the replication dataset rather than the literal token being rejected."""
    m = _BRACE.search(tok)
    if not m:
        return [tok]
    opts: list[str] = []
    for opt in m.group(1).split(","):
        opt = opt.strip()
        rng = _BRACE_RANGE.match(opt)
        if rng and int(rng.group(1)) <= int(rng.group(2)) <= int(rng.group(1)) + 64:
            opts.extend(str(i) for i in range(int(rng.group(1)), int(rng.group(2)) + 1))
        else:
            opts.append(opt)
    prefix, suffix = tok[:m.start()], tok[m.end():]
    out: list[str] = []
    for p in opts:
        out.extend(_expand_braces(prefix + p + suffix))
    return out


def _detect_readme_missing_paths(root: Path) -> list[dict[str, Any]]:
    readme = None
    try:
        for p in root.iterdir():
            if p.is_file() and p.name.lower() in {"readme.md", "readme.txt"}:
                readme = p
                break
    except OSError:
        return []
    if readme is None:
        return []
    try:
        text = readme.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    rels: set[str] = set()
    names: set[str] = set()
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        rels.add(rel.as_posix().lower())
        names.add(p.name.lower())

    def resolves(tok: str) -> bool:
        rel = tok.strip().strip("`").lstrip("./").rstrip("/").lower()
        return not rel or rel in rels or Path(rel).name in names

    root_token = root.name.lower()
    seen: set[str] = set()
    hits: list[dict[str, Any]] = []
    for m in _README_BACKTICK.finditer(text):
        tok = m.group(1).strip()
        if tok in seen:
            continue
        seen.add(tok)
        if tok.lower().rstrip("/") == root_token:
            continue  # the replication dataset's own root folder, not a missing sub-path
        if _ABSENT_WORDING.search(text[max(0, m.start() - 200): m.start() + 200]):
            continue  # documented as deliberately not shipped
        candidates = _expand_braces(tok) if ("{" in tok and "}" in tok) else [tok]
        for cand in candidates:
            if _readme_pathish(cand) and not resolves(cand):
                hits.append(_ev(readme.name, None, f"README references `{tok}` but it is not in the replication dataset"))
                break
    return hits[:8]


# A13: a code file that nothing runs, once a master/sourcing structure is present.
def _detect_unreferenced_scripts(entries: list[FileEntry], edges: list[Edge], texts: dict[str, str]) -> list[dict[str, Any]]:
    callers = {e.src for e in edges if e.kind in {"do", "source"}}
    if not callers:  # no run structure at all -> A1/A11 own that case, not this rule
        return []
    referenced = {e.dst for e in edges if e.kind in {"do", "source"} and e.resolved}
    hits: list[dict[str, Any]] = []
    for path in sorted(p for p in texts):
        if path in referenced or path in callers:
            continue
        base = Path(path).name
        # a helper sourced via a path the graph could not resolve still has its name typed elsewhere
        if any(base in other for q, other in texts.items() if q != path):
            continue
        hits.append(_ev(path))
    return hits[:8]


# N5: a filename a shell or another tool will choke on.
_UNSAFE_FILENAME = re.compile(r"""[ &;|()$`'"*?<>]""")


def _detect_unsafe_filenames(root: Path, entries: list[FileEntry]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for e in entries:
        if e.language in {"stata", "r", "python", "sas", "data"}:
            name = Path(e.path).name
            if _UNSAFE_FILENAME.search(name):
                hits.append(_ev(e.path, None, "filename has a space or a shell-unsafe character"))
    return hits[:8]


# A5 / A14 / A15: missing-input detection over the dependency graph, confidence-gated.
#   A5  (P0): an unresolved INCLUDE target (do/source/import literal that resolves to no file).
#   A14 (P0): an unresolved data READ literal, absent and produced by NO write edge — relative OR
#             absolute. An unresolved status already means the basename ships nowhere (_resolve
#             rglobs it), so an absolute read of a file that ships nowhere is a genuine missing input,
#             not merely a portability nit; B4 flags the abs path but says nothing about existence,
#             so the two are complementary and both fire (issue #30). B4 also misses Unix absolutes
#             (/mnt, /scratch, /restricted) entirely, which A14 now surfaces.
#   A15 (P2): a basename-collision (ambiguous) include/read — never a P0, surfaced as advisory.
# A target produced by a write edge is a pipeline intermediate, not a missing input (D3 owns it).
# A dynamic path (no literal) never reaches here — it has no edge.
def _missing_inputs(edges: list[Edge], lang_of) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    write_basenames = {Path(e.dst).name.lower() for e in edges if e.kind == "write"}
    a5: list[dict[str, Any]] = []
    a14: list[dict[str, Any]] = []
    a15: list[dict[str, Any]] = []
    for e in edges:
        base = Path(e.dst).name
        if e.status == "ambiguous":
            if e.kind in _INCLUDE_KINDS or e.kind in _READ_KINDS:
                a15.append(_ev(e.src, None, f"references '{base}' but the replication dataset ships more than one file with that name"))
            continue
        if e.status != "unresolved":
            continue
        if base.lower() in write_basenames:
            continue  # produced elsewhere by a write edge -> intermediate, not a missing input
        if e.kind in _INCLUDE_KINDS:
            a5.append(_ev(e.src, None, f"includes '{e.dst}' but no such file ships in the replication dataset"))
        elif e.kind in _READ_KINDS:
            if lang_of(e.src) not in {"stata", "r", "python"}:
                continue  # Julia and friends: best-effort graph only -> never P0
            a14.append(_ev(e.src, None, f"reads '{e.dst}' but no such file ships and no script writes it"))
    return a5, a14, a15


def _has_substantive_code(texts: dict[str, str]) -> bool:
    """True if any shipped code file has at least one line that is not blank and not a comment. An
    empty or comment-only .do/.R/.py is not runnable, so it must not silence the no-code finding
    (issue #8). `texts` holds only code files (see _texts)."""
    for t in texts.values():
        for ln in t.splitlines():
            s = ln.strip()
            if not s or s.startswith(("*", "//", "#")):
                continue
            return True
    return False


def _xlsx_sheet_names(path: Path) -> list[str]:
    """Sheet names inside an .xlsx (a zip) read from xl/workbook.xml with stdlib only — no openpyxl
    dependency. Used to spot an LLM/prompt sheet in an otherwise innocuously named workbook (issue #9).
    Returns [] on any failure (not a zip, missing part, parse error)."""
    import zipfile

    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("xl/workbook.xml").decode("utf-8", errors="replace")
    except (OSError, KeyError, zipfile.BadZipFile):
        return []
    return re.findall(r'<sheet[^>]*\bname="([^"]+)"', xml)


def _detect_llm_provenance(root: Path, entries: list[FileEntry], texts: dict[str, str]) -> list[dict[str, Any]]:
    """D9: data generated by an LLM must record its provenance (which model snapshot, and the
    parameters that make a stochastic run reproducible) or it cannot be regenerated (issue #9).
    Fires when an LLM artifact is shipped (a file name or .xlsx sheet name with a strong LLM token)
    but the replication dataset records no versioned model id together with a generation parameter or the raw
    responses. Provenance is looked for across READMEs (.md/.txt/.tex/.rst and .pdf) and code.

    Scope: provenance presence is checked package-wide, not bound to each artifact — a v1 advisory
    heuristic. It deliberately ignores the bare token `prompt` (a common survey variable name) and
    requires a VERSIONED model id (not an incidental 'we used GPT' mention) to clear the finding."""
    artifacts: list[str] = []
    for e in entries:
        if e.language in {"stata", "r", "python", "sas"}:
            continue  # the rule is about generated DATA, not a gpt-querying script
        if _LLM_ARTIFACT_TOKEN.search(Path(e.path).name):
            artifacts.append(e.path)
            continue
        if e.path.lower().endswith(".xlsx"):
            if any(_LLM_ARTIFACT_TOKEN.search(s) for s in _xlsx_sheet_names(root / e.path)):
                artifacts.append(e.path)
    if not artifacts:
        return []

    prov_parts: list[str] = list(texts.values())  # code files
    for e in entries:
        low = e.path.lower()
        if low.endswith((".md", ".txt", ".tex", ".rst")):
            prov_parts.append((root / e.path).read_text(encoding="utf-8", errors="replace"))
        elif low.endswith(".pdf"):
            extracted = _pdftotext(root / e.path)
            if extracted:
                prov_parts.append(extracted)
    blob = "\n".join(prov_parts)
    if _MODEL_ID.search(blob) and _GEN_PARAM.search(blob):
        return []
    return [_ev(p) for p in sorted(set(artifacts))][:8]


def run(root: Path, entries: list[FileEntry], edges: list[Edge], table_exports) -> list[Finding]:
    root = root.resolve()
    rules = {r["id"]: r for r in load_rules()}
    texts = _texts(root, entries)
    stems = _shipped_stems(root)
    findings: list[Finding] = []

    def emit(rule_id: str, evidence: list[dict[str, Any]], rationale: str) -> None:
        if not evidence:
            return
        r = rules[rule_id]
        findings.append(
            Finding(
                rule_id=rule_id,
                category=r["category"],
                kind=r["kind"],
                priority=r["priority"],
                message=r["rule"],
                evidence=evidence,
                rationale=rationale,
                source_lessons=r.get("source_lessons", []),
                why_downstream=r.get("why_downstream", ""),
                target_form=r.get("target_form", ""),
                lossless_note=r.get("lossless_note", ""),
                propose_only=bool(r.get("propose_only", False)),
                output_changing=bool(r.get("output_changing", False)),
            )
        )

    callers = {e.src for e in edges if e.kind in {"do", "source"}}
    script_paths = [e.path for e in entries if e.language in {"stata", "r", "python"}]
    # The certification line picks entry points with dependency_graph.entry_points and, finding
    # none, runs every script in a guessed order. A package with SOME call edges but no single
    # script that reaches the rest is in the same position as one with none — the old
    # `not callers` test only saw the latter (Tajima 2013: three scripts each `do` one helper,
    # nothing ties the eight together; Urpelainen 2022: 26 scripts, two call edges).
    _entry = [p["path"] for p in dependency_graph.entry_points(entries, edges)]
    if len(script_paths) > 1 and (not callers or len(_entry) != 1):
        emit("A1-master-entry", [_ev(p) for p in sorted(texts)][:1],
             "No script sources/does any other; build order is implicit."
             if not callers else
             f"{len(_entry) or 'No'} entry script(s) reach the rest ({len(script_paths)} scripts); "
             "build order is implicit.")
        readme_has_order = any(
            re.search(r'(run|execut|order|step\s*\d|^\s*\d+[.)]\s)', (root / e.path).read_text(encoding="utf-8", errors="replace"), re.IGNORECASE | re.MULTILINE)
            for e in entries if _is_doc_entry(e.path, e.language)
        )
        if not readme_has_order:
            emit("A11-explicit-run-order", [_ev(p) for p in sorted(script_paths)][:1],
                 f"{len(script_paths)} analysis scripts, no master script and no README run-order.")

    doc_files = [e.path for e in entries if _is_doc_entry(e.path, e.language)]
    data_files = [e.path for e in entries if e.language == "data"]

    # Issue #8: a package with analysis material but no runnable code cannot be reproducibility-checked.
    # Trigger on data files OR a GUI-analysis project file (so a SmartPLS .splsm whose data is embedded
    # in the binary still fires) AND no substantive code (an empty/comment-only script does not count).
    # A document-only deposit with no data/GUI file is left silent — a qualitative corpus expects no
    # code, and nagging it is the false expectation issue #24 warns about.
    gui_projects = [e.path for e in entries if Path(e.path).suffix.lower() in _GUI_PROJECT_EXTS]
    analysis_material = sorted(set(data_files) | set(gui_projects))
    code_is_substantive = _has_substantive_code(texts)
    if analysis_material and not code_is_substantive:
        emit("A16-no-executable-code", [_ev(p) for p in analysis_material][:8],
             f"{len(analysis_material)} data/analysis file(s) but no runnable .do/.R/.py script; "
             "computational reproducibility cannot be assessed from a static scan.")
        # Issue #10: for a no-code deposit that also ships no result artifacts, a reproduction has
        # nothing to diff against. Only fires without code (with code, D1 + the gate own coverage) and
        # only with data present (a doc-only qualitative deposit expects no results, per #24).
        if data_files and not any(_RESULT_DIR.search(e.path) for e in entries):
            emit("D8-results-not-shipped", _file_evidence(sorted(data_files)),
                 "Package ships data but no runnable code and no result tables/figures under an "
                 "output/ folder; a reproduction has nothing to compare against.")

    # Issue #57: files under an output/results/tables/figures folder are RUN-GENERATED, not source
    # inputs the author must document; demanding a codebook entry for `output/tables/Table_1.csv`
    # (which the run itself writes, sometimes a file D1 just required) is a false flag.
    source_data = [fp for fp in data_files if not _RESULT_DIR.search(fp)]
    docable = script_paths + source_data
    n_files = len(docable)
    if n_files > 1:
        documented = set()
        for d in doc_files:
            dtext = (root / d).read_text(encoding="utf-8", errors="replace")
            for fp in docable:
                if Path(fp).name in dtext:
                    documented.add(fp)
        undocumented = [fp for fp in docable if fp not in documented]
        if undocumented:
            detail = "no README" if not doc_files else f"{len(undocumented)} of {n_files} files not described in any README"
            emit("D4-per-file-documentation", _file_evidence(undocumented),
                 f"{detail}; per-file documentation (purpose, inputs/outputs, codebook) missing.")

    emit("D5-duplicate-readme", _detect_duplicate_readmes(root),
         "Multiple distinct README documents (different names or folders) that can diverge and mislead a replicator.")

    emit("D10-package-size-cap", _detect_package_size(entries),
         f"The replication dataset is larger than the {_CERT_SIZE_CAP_MB} MB the certification archive accepts; "
         "certification stops at preflight before anything runs.")

    emit("D6-readme-missing-paths", _detect_readme_missing_paths(root),
         "README references files or folders that are not present in the replication dataset.")

    emit("A13-unreferenced-script", _detect_unreferenced_scripts(entries, edges, texts),
         "A code file is never run by the master or any other script and is not named anywhere else.")

    emit("N5-unsafe-filename", _detect_unsafe_filenames(root, entries),
         "A script or data filename contains a space or a character that breaks shells and tools.")

    a5_ev, a14_ev, a15_ev = _missing_inputs(edges, lambda p: _lang_of(entries, p))
    emit("A5-stable-includes", a5_ev,
         "A do/source/import target does not resolve to any file shipped in the replication dataset.")
    emit("A14-missing-input", a14_ev,
         "A relative data read points at a file that is absent and that no script in the replication dataset writes.")
    emit("A15-ambiguous-input-path", a15_ev,
         "An include/read names a file by a basename that more than one shipped file matches, so which one loads depends on the working directory.")

    emit("D7-codebook-coverage", _detect_codebook_coverage(root, entries, texts),
         "A shipped codebook exists but some variables used in estimation commands are not documented in it.")

    emit("D9-llm-data-provenance", _detect_llm_provenance(root, entries, texts),
         "LLM-generated data is shipped with no recorded model version, generation parameters, or raw responses.")

    # A17 package-level context (issue #36), computed once. Two pieces: (1) R-package SOURCE trees
    # are exempt — package internals resolve callables via NAMESPACE imports and test files via the
    # testthat runner, neither through library() calls, so a deposit that vendors package source
    # must not be flagged for it; (2) the allow set is package-GLOBAL, because library() and
    # source() act on R's global environment — a helper file sourced by a master that loads CVXR
    # legitimately calls CVXR exports without any library() line of its own.
    _r_pkg_dirs = {str(p.parent.relative_to(root))
                   for name in ("NAMESPACE", "DESCRIPTION") for p in root.rglob(name)}
    _r_skip = {p for p in texts if _lang_of(entries, p) == "r" and (
        any(part in {"tests", "testthat"} for part in Path(p).parts)
        or any(d == "." or str(Path(p)).startswith(d + "/") for d in _r_pkg_dirs)
    )}
    _r_allow = _r_callable_allow_set(texts, edges, lambda p: _lang_of(entries, p), _r_skip)
    if _r_allow is not None:
        _r_allow |= _r_defined_names(texts, lambda p: _lang_of(entries, p))
    _snapshot = _r_exports()[2]

    for path, text in texts.items():
        lang = _lang_of(entries, path)

        for line_no, line in _abs_path_file_hits(text, lang):
            emit("B4-no-abs-paths", [_ev(path, line_no, line)], "Absolute path literal found.")

        if lang in {"stata", "r"}:
            emit("A12-table-comment-mapping", _detect_missing_table_comments(path, text),
                 "Multiple estimations with no `-> Table N` comments anchoring the table<->command mapping.")
            emit("D1-output-artifact-coverage", _detect_uncaptured_artifacts(path, text, lang),
                 "Estimation/figure present but no export saves the artifact to a relative output/ folder.")
            emit("D3-intermediate-data-hygiene", _detect_intermediate_data(root, path, text, edges, texts),
                 "Intermediate dataset written outside a canonical data/ folder is read by another script.")
            emit("C8-unseeded-stochastic", _detect_unseeded_stochastic(path, text, lang),
                 "Stochastic operation with no seed; a re-run draws different numbers than the paper reports.")

        if lang == "python":
            # Labeled-anchor D1 for .py/.ipynb (issue #33). Re-read with the ANCHORED reader: _texts
            # uses plain read_source (B4's #34 semantics must not change), but D1/gate must see
            # markdown lines '#'-prefixed so prose can neither produce a body hit nor credit an
            # export — a to_csv("tables/x.csv") quoted in markdown prose is not runnable code.
            emit("D1-output-artifact-coverage",
                 _detect_uncaptured_artifacts(path, read_source_anchored(root, path), lang),
                 "Estimation/figure present but no export saves the artifact to a relative output/ folder.")
            emit("C8-unseeded-stochastic", _detect_unseeded_stochastic(path, text, lang),
                 "Stochastic operation with no seed; a re-run draws different numbers than the paper reports.")

        if lang in {"stata", "r", "python"}:
            emit("C12-no-wallclock-in-output", _detect_wallclock_in_output(path, text, lang),
                 "The wall clock or a process-unique path is written into an output; two runs of the same code then differ on that line.")
        if lang in {"r", "python"}:
            emit("A18-runtime-assembled-path", _detect_runtime_assembled_read(path, text, lang),
                 "A data read whose path is built at run time cannot be checked statically; name the file literally so a reader can see it ships.")

        if lang in {"stata", "r"}:
            loop_depth = 0
            for line_no, line in enumerate(text.splitlines(), start=1):
                code = _strip_comment_keep_strings(line, lang)
                if _LOOP_HEAD.search(code):
                    loop_depth += 1
                if loop_depth > 0 and _EXPORT_FIXED.search(code):
                    emit("B1-minimize-loops", [_ev(path, line_no, line)],
                         "Fixed-filename table export inside a loop overwrites per iteration.")
                if loop_depth > 0 and _is_estimation(code):
                    emit("N2-explicit-table-commands", [_ev(path, line_no, line)],
                         "Estimation inside a loop hides the model->table-cell mapping from the pipeline.")
                if re.match(r'^\s*\}', code) and loop_depth > 0:
                    loop_depth -= 1

        if lang == "stata":
            # An ado command is invoked with the caller's data already in
            # memory; it is not an analysis entry script. In particular,
            # vendoring estadd must not create a new "author must load data"
            # blocker. Read-side dependency checks still inspect ado files.
            if Path(path).suffix.lower() != ".ado" and _ESTIMATION.search(text) and not _DATA_LOAD_STATA.search(text):
                if not _upstream_loads_data(path, edges, texts, _DATA_LOAD_STATA):
                    emit("A3-data-load", [_ev(path)],
                         "Estimation present but no use/import in this script, and no upstream script loads data first.")
            ts_hits = _code_line_hits(text, _TS_OP, lang)
            if ts_hits and not _TSSET.search(text):
                emit("A4-panel-declare", [_ev(path, ts_hits[0][0], ts_hits[0][1])],
                     "Time-series operators without a prior tsset/xtset.")
            for line_no, line in _code_line_hits(text, _CLEAR_ALL, lang):
                if path not in callers:
                    emit("B7-no-cross-script-clearall", [_ev(path, line_no, line)],
                         "clear all in a non-master script drops programs later scripts need.")
            for line_no, line in _code_line_hits(text, _WIDE_WILDCARD, lang):
                emit("B3-no-wide-wildcard", [_ev(path, line_no, line)],
                     "Wildcard varlist may expand past 20 columns.")
            if _VERSION_SENSITIVE.search(text) and not _VERSION_STMT.search(text):
                emit("C3-declare-stata-version", [_ev(path)],
                     "Version-sensitive command without a `version NN` declaration.")
            emit("A6-guarded-fallback-load", _detect_guarded_fallback(root, path, text),
                 "Guarded `capture use A` + `if _rc!=0 {use B}`; A ships so the fallback to B never runs.")
            emit("A7-var-lifecycle-contradiction", _detect_lifecycle_contradiction(path, text),
                 "Variable used after it was dropped or renamed away.")
            emit("A8-data-ref-extension-mismatch", _detect_data_ref_mismatch(root, path, text, stems),
                 "Data reference does not resolve, but a same-stem file with a different extension ships.")
            emit("A9-nested-cd", _detect_relative_cd(path, text),
                 "Relative `cd` mid-script breaks relative paths when run from the replication dataset root.")
            emit("C4-deprecated-syntax-signature", _detect_compat_signatures(path, text, bool(_VERSION_STMT.search(text))),
                 "Version-fragile command syntax without a declared version.")
            emit("B10-embedded-foreign-code", _detect_embedded_foreign(path, text),
                 "Non-Stata (R-style) code in a .do file halts Stata before regressions.")
            emit("C9-console-transcript", _detect_stata_transcript(path, text),
                 "Console-session transcript: `. ` prompts / `#` comment lines are not runnable Stata (r(199)).")
            for line_no, line in _code_line_hits(text, _QUIET_LOAD, lang):
                emit("B9-suppressed-data-load", [_ev(path, line_no, line)],
                     "quietly around use/import hides a missing-file failure.")
            emit("N1-no-delimit-semicolon", _detect_delimit(path, text),
                 "#delimit ; changes the statement terminator for a whole region; `///` is line-local and unambiguous.")
            emit("N4-named-estimation-calls", _detect_wrapper_estimation(path, text),
                 "Estimation inside a user program slips past output capture and is harder to read; call estimators directly.")
            emit("C2-vendor-ado", _detect_unvendored_ado(root, path, text),
                 "User-written ado command used but no .ado ships in the replication dataset.")
            emit("C10-no-runtime-code-fetch", _detect_runtime_code_fetch(path, text, lang),
                 "ssc/net install fetches code from the internet at run time; the certified run is closed and cannot.")
            emit("C11-no-external-adopath", _detect_external_adopath(path, text),
                 "adopath/sysdir points outside the replication dataset; on any other machine that directory does not exist.")
            emit("C6-old-stata-merge-syntax", _detect_old_merge(path, text),
                 "Pre-Stata-11 `merge varlist using` syntax fails on modern Stata; use `merge m:1`/`1:1`.")
            emit("A10-commented-restricted-regression", _detect_commented_restricted(path, text),
                 "Commented-out regression with nearby restricted-data wording.")

        if lang == "r":
            if _has_toplevel_estimation(text) and not _DATA_LOAD_R.search(text):
                if not _upstream_loads_data(path, edges, texts, _DATA_LOAD_R):
                    emit("A3-data-load", [_ev(path)],
                         "Estimation present but no read/load in this script, and no upstream script loads data first.")
            for line_no, line in _code_line_hits(text, _GITHUB_INSTALL, lang):
                emit("C1-pin-deps", [_ev(path, line_no, line)], "Unpinned direct-from-source install.")
            emit("C10-no-runtime-code-fetch", _detect_runtime_code_fetch(path, text, lang),
                 "install.packages in a script fetches code from the internet at run time; the certified run is closed and cannot.")
            emit("C5-deprecated-r-packages", _detect_deprecated_r_pkg(path, text),
                 "Removed/deprecated R package loaded at top halts the whole script.")
            emit("C7-nonreproducible-parallel-rng", _detect_nonreproducible_parallel_rng(path, text),
                 "Parallel %dopar% loop without doRNG/registerDoRNG draws a different RNG stream each run.")
            # B11 is a parse-error rule for PLAIN .R scripts only: inventory maps .rmd to lang "r",
            # but chunk markers are the NORMAL syntax of a knitr source, so a genuine .Rmd (or .qmd,
            # should it ever map here) must never fire it (issue #40).
            if not path.lower().endswith((".rmd", ".qmd")):
                emit("B11-rmd-chunk-in-r", _detect_rmd_chunk(path, text),
                     "R Markdown ```{r} chunk markers in a .R file cause a parse error.")
            emit("B8-r-table-call-syntax", _detect_r_table_syntax(path, text),
                 "stargazer/xtable call has unbalanced delimiters across its span.")
            emit("N3-compact-r-table-calls", _detect_long_r_table_call(path, text),
                 "A sprawling multi-line table call is fragile to comment-cleaning and hard to read.")
            emit("A10-commented-restricted-regression", _detect_commented_restricted(path, text),
                 "Commented-out regression with nearby restricted-data wording.")
            emit("A17-undefined-r-callable",
                 [] if path in _r_skip else _detect_undefined_r_callable(path, text, _r_allow),
                 f"Function called but defined nowhere in the replication dataset and exported by no declared "
                 f"library (per reproai's export snapshot {_snapshot or 'n/a'}) — R halts with "
                 f"'could not find function' at that line.")

    # SAS tier-1 pass (issue #32): abs-path scan ONLY. Deliberately a separate loop over entries,
    # NOT an addition to _texts — adding "sas" there would false-flag lonely .sas files via A13,
    # silently suppress A16 through _has_substantive_code, and let A1 name a .sas as master
    # evidence. SAS comments are multi-line (`* ...;` and /* */ both span lines), so the per-line
    # _strip_comment_keep_strings cannot serve; _blank_sas_comments blanks them block-wise while
    # keeping line indices, and evidence shows the RAW line (the blanked text is match-only).
    # Missing-input/output-coverage/master detection for SAS need a libref resolver — tier 2.
    for e in entries:
        if e.language != "sas":
            continue
        for i, ln in _abs_path_file_hits(read_source(root, e.path), "sas"):
            emit("B4-no-abs-paths", [_ev(e.path, i, ln)], "Absolute path literal found.")

    return _dedupe(findings)


def _dedupe(findings: list[Finding]) -> list[Finding]:
    merged: dict[str, Finding] = {}
    for f in findings:
        if f.rule_id not in merged:
            merged[f.rule_id] = f
        else:
            merged[f.rule_id].evidence.extend(f.evidence)
    return list(merged.values())
