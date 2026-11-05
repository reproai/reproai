from __future__ import annotations

# noqa: SIZE_OK -- legacy static graph extractor; splitting it is outside the private Prep repair.

from typing import Any, override

import ast
import bisect
import re
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from .inventory import FileEntry

# --- Edge taxonomy -----------------------------------------------------------------------------
# kind is the specific verb class; status is the 3-tier resolution confidence. The edge CLASS
# (include / read / write) is derived from kind via the sets below — A5/A14 and the orphan
# detector key off the class, not the raw kind.
_INCLUDE_KINDS = frozenset({"do", "source", "import"})
_READ_KINDS = frozenset({"data_use", "read"})
_WRITE_KINDS = frozenset({"write"})


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    kind: str          # do | source | import | data_use | read | write
    status: str        # resolved | unresolved | ambiguous

    @property
    def resolved(self) -> bool:
        # back-compat: every existing consumer reads `.resolved` as a bool. A basename collision
        # (ambiguous) is deliberately NOT resolved — never silently pick the first hit.
        return self.status == "resolved"

    @property
    def edge_class(self) -> str:
        if self.kind in _INCLUDE_KINDS:
            return "include"
        if self.kind in _WRITE_KINDS:
            return "write"
        return "read"


# --- Stata: line-level patterns (do/run includes, use/import reads, save/export/graph writes) ---
_STATA_PRE = r'(?:cap(?:ture)?\s+|qui(?:etly)?\s+|noi(?:sily)?\s+)*'
# Stata lets `do X` omit the .do; 27 of 45 do/run calls in the workspace corpus do (`do PartA_Prelims`,
# `do merge_replication`), and an edge regex that required the suffix saw none of them — so master
# scripts had no callees, entry-point detection fell back to a guessed order, and unreferenced-script
# findings were wrong on every such package. The bare form is captured up to whitespace, a comma
# (options) or a comment opener, and _stata_do_target appends .do when it is missing.
_STATA_DO = re.compile(r'^\s*' + _STATA_PRE + r'(?:do|run)\s+(?:"([^"\r\n]+?)"|((?:(?!//|/\*)[^\s"\r\n,])+))', re.IGNORECASE | re.MULTILINE)


def _stata_do_target(match: "re.Match[str]") -> str:
    target = (match.group(1) or match.group(2) or "").strip()
    if target and not target.lower().endswith(".do"):
        target += ".do"
    return target
_STATA_USE = re.compile(r'^\s*' + _STATA_PRE + r'use\s+"?([^"\r\n,]+?\.dta)"?', re.IGNORECASE | re.MULTILINE)
# `use cohort, clear` reads cohort.dta: Stata adds the extension when the name has none. Only a
# lone file name (quoted or bare) followed by options or the end of the line, so a varlist with
# `using`, or an `if`/`in` qualifier, is never mistaken for one.
_STATA_USE_BARE = re.compile(r'^\s*' + _STATA_PRE + r'use\s+(?:"([^"\r\n,]+)"|([^\s",]+))\s*(?:,[^\r\n]*)?$',
                             re.IGNORECASE | re.MULTILINE)
_STATA_READ = re.compile(
    r'^\s*' + _STATA_PRE + r'(?:import\s+delimited|import\s+excel|insheet|infile)\b'
    r'[^\r\n]*?"?([\w./\\$' + "`'{}" + r' -]+?\.(?:csv|tab|txt|xlsx|xls|dat|dta))"?',
    re.IGNORECASE | re.MULTILINE,
)
# Path char class incl. the backtick+apostrophe that delimit a Stata local macro `x' and `$`/`{}` for
# globals, so a macro-parameterized literal (save "prefix`t'_wip.dta", use "${dirdta}/x.dta") is
# captured WHOLE rather than truncated at the macro; the loop-expansion / global-expansion below then
# resolves it to concrete paths (#29 writes, #41 reads).
_STATA_MACRO_PATH = r"[\w./\\$" + "`'{}" + r" -]"
_STATA_WRITE = re.compile(
    r'^\s*' + _STATA_PRE + r'(?:save|saveold|export\s+delimited|export\s+excel|outsheet|'
    r'graph\s+export|graph\s+save|esttab|estout|outreg2?|putexcel|putdocx|tabout)\b'
    r'[^\r\n]*?"?(' + _STATA_MACRO_PATH + r'+?\.(?:dta|csv|tab|txt|xlsx|xls|parquet|pdf|png|eps|ps|svg|gph|tex|rtf|doc|docx))"?',
    re.IGNORECASE | re.MULTILINE,
)

# --- Stata global macros (issue #41): `global dirdta "data"` in a run-all, then `use
# "${dirdta}/Tweets_MP_Database.dta"` in an analysis script. The matcher was macro-blind on the READ
# side (#29 fixed only writes), so a package whose data fully ships got a P0 missing-input.
# Definitions are collected across ALL .do files in build() — the run-all defines the roots that
# later scripts read through — and substituted into read/include/write targets before resolution.
# `gl`..`global` abbreviations accepted; value = quoted string or first bare token; a comment-only
# line never matches (the ^ anchor rejects `*`/`//` prefixes).
_STATA_GLOBAL_DEF = re.compile(
    r'^[ \t]*(?:qui(?:etly)?\s+)?gl(?:o|ob|oba|obal)?\s+(\w+)\s*=?\s*(?:"([^"\r\n]*)"|(?!//)(\S+))',
    re.IGNORECASE | re.MULTILINE,
)
_STATA_GLOBAL_REF = re.compile(r'\$\{(\w+)\}|\$(\w+)')
# any macro span still unexpanded after global substitution: undefined global or un-enumerable local
_MACRO_SPAN = re.compile(r'\$\{\w+\}|\$\w+|`\w+' + "'")
_WILDCARD_HIT_CAP = 200  # a macro-wildcard basename matching more shipped files than this is too vague


def _stata_globals(text: str) -> dict[str, str]:
    """name -> value for every enumerable `global` definition in one .do file."""
    out: dict[str, str] = {}
    for m in _STATA_GLOBAL_DEF.finditer(text):
        value = m.group(2) if m.group(2) is not None else m.group(3)
        out.setdefault(m.group(1), value)  # first definition wins — deterministic across redefinitions
    return out


def _expand_globals(target: str, globals_map: dict[str, str]) -> str:
    """Substitute `${name}`/`$name` spans with their defined values; undefined names are left intact
    (the wildcard fallback in _macro_resolve handles them). Bounded iteration for nested globals."""
    if not globals_map:
        return target
    for _ in range(5):
        new = _STATA_GLOBAL_REF.sub(
            lambda m: globals_map.get(m.group(1) or m.group(2), m.group(0)), target)
        if new == target:
            break
        target = new
    return target


def _macro_resolve(root: Path, rel: str, target: str, globals_map: dict[str, str]) -> list[tuple[str, str]]:
    """Resolve a Stata read/include target that may carry macro spans (issue #41). Usually one
    (dst, status); a macro-parameterized BASENAME (use "f`t'.dta") that matches several shipped files
    yields one resolved pair per match — the read-side mirror of the #29 write-side loop expansion.

    Order: (1) expand defined globals — exact, so `${dirdta}/x.dta` resolves to the exact shipped
    path even when the basename is ambiguous elsewhere in the tree; (2) plain _resolve; (3) only if
    still unresolved AND a macro span remains, match the macro-wildcarded basename against the
    shipped tree — a file the package plausibly provides must never fire a P0 missing-input, while a
    pattern matching NOTHING still does (anti-bypass: a bogus `use "${d}/ghost.dta"` stays A14)."""
    expanded = _expand_globals(target, globals_map)
    dst, status = _resolve(root, rel, expanded)
    if status != "unresolved" or not _MACRO_SPAN.search(expanded):
        return [(dst, status)]
    base_pat = Path(_MACRO_SPAN.sub("*", expanded.strip().replace("\\", "/"))).name.lower()
    hits = sorted(str(p.relative_to(root)) for p in root.rglob("*")
                  if p.is_file() and fnmatch(p.name.lower(), base_pat))
    if not hits:
        return [(expanded, "unresolved")]
    if len(hits) > _WILDCARD_HIT_CAP:
        return [(expanded, "ambiguous")]  # too vague to enumerate; advisory (A15), never a P0
    return [(h, "resolved") for h in hits]

# --- Stata loop expansion (issue #29): a save inside `forvalues t=1984/2020 { ... save "f`t'.dta" }`
# produces f1984.dta..f2020.dta. Enumerate the loop's ACTUAL values (numeric ranges + `foreach ... in`
# token lists) and emit one concrete write edge per value, so a later `use "f1984.dta"` matches a
# writer while an out-of-range `use "f9.dta"` or an unrelated `use "BRA_clean.dta"` still fires A14.
# Loops we cannot enumerate statically (`foreach x of local ...`) are left unexpanded (no suppression).
_STATA_LOOP_HEAD = re.compile(r'^[ \t]*(for(?:v\w*|each)\b[^\r\n{]*)\{', re.IGNORECASE | re.MULTILINE)
_LOOP_CAP = 2000    # skip enumeration of a single loop wider than this (pathological)
_EXPAND_CAP = 5000  # bail (leave path unexpanded) if the cartesian product exceeds this


def _loop_values(header: str) -> tuple[str, list[str]] | None:
    """(loop_var, [values]) for an enumerable Stata loop header, else None."""
    ms = re.match(r'\s*forv\w*\s+(\w+)\s*=\s*(-?\d+)\s*\(\s*(-?\d+)\s*\)\s*(-?\d+)', header, re.IGNORECASE)
    if ms:
        var, a, s, b = ms.group(1), int(ms.group(2)), int(ms.group(3)), int(ms.group(4))
        if s == 0:
            return None
        vals = [str(v) for v in range(a, b + (1 if s > 0 else -1), s)]
        return (var, vals) if 0 < len(vals) <= _LOOP_CAP else None
    mr = re.match(r'\s*forv\w*\s+(\w+)\s*=\s*(-?\d+)\s*/\s*(-?\d+)', header, re.IGNORECASE)
    if mr:
        var, a, b = mr.group(1), int(mr.group(2)), int(mr.group(3))
        vals = [str(v) for v in range(a, b + 1)]
        return (var, vals) if 0 < len(vals) <= _LOOP_CAP else None
    mf = re.match(r'\s*foreach\s+(\w+)\s+in\b(.*)', header, re.IGNORECASE | re.DOTALL)
    if mf:
        toks = [t.strip().strip('"').strip("'") for t in mf.group(2).split()]
        toks = [t for t in toks if t]
        return (mf.group(1), toks) if 0 < len(toks) <= _LOOP_CAP else None
    return None


def _stata_loops(text: str) -> list[tuple[str, list[str], int, int]]:
    """[(var, [values], body_start, body_end)] for each enumerable loop, body span via brace match."""
    loops: list[tuple[str, list[str], int, int]] = []
    for m in _STATA_LOOP_HEAD.finditer(text):
        brace = m.end() - 1  # index of the opening '{'
        depth, end = 0, None
        for j in range(brace, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        if end is None:
            continue
        parsed = _loop_values(m.group(1))
        if parsed:
            loops.append((parsed[0], parsed[1], brace, end))
    return loops


def _expand_write_path(raw: str, pos: int, loops: list[tuple[str, list[str], int, int]]) -> list[str]:
    """Expand `var' local-macro references in a save path over every enclosing loop's values.
    Returns [raw] when the path has no enclosing-loop macro (or expansion would explode)."""
    active = [(var, vals) for (var, vals, bs, be) in loops
              if bs < pos < be and re.search(r'`' + re.escape(var) + r"'", raw)]
    if not active:
        return [raw]
    paths = [raw]
    for var, vals in active:
        pat = re.compile(r'`' + re.escape(var) + r"'")
        paths = [pat.sub(v, p) for p in paths for v in vals]
        if len(paths) > _EXPAND_CAP:
            return [raw]  # safe fallback: no suppression, never a bypass
    return paths

# --- R / Python: call-based extraction (the keystone fix) --------------------------------------
# Old engine matched only `source("literal")` — a `source(file.path(CODE,"x.R"))` slipped past. We
# now find the verb, walk its balanced parens, and pick the path-shaped string literal inside, so
# file.path()/paste0()/here()/glue() wrappers resolve via their literal segment.
_INCLUDE_VERBS = ("source", "sys.source")
_READ_VERBS = (
    "read.csv", "read.csv2", "read.delim", "read.delim2", "read.table", "read_csv", "read_csv2",
    "read_tsv", "read_delim", "read_table", "read_dta", "read.dta", "read.dta13", "read_stata",
    "readRDS", "read_rds", "load", "fread", "st_read", "read_excel", "read_xlsx", "read_sav",
    "read_spss", "read_parquet", "read_feather", "read_pickle", "read_json",
)
_WRITE_VERBS = (
    "write.csv", "write.csv2", "write.table", "write_csv", "write_tsv", "write_delim", "fwrite",
    "saveRDS", "save", "write_rds", "write_dta", "write.dta", "write.dta13", "write_xlsx",
    "st_write", "ggsave", "pdf", "png", "jpeg", "tiff", "bmp", "svg", "postscript", "cairo_pdf",
    "dev.copy2pdf", "stargazer", "etable", "texreg", "htmlreg", "modelsummary",
    "to_csv", "to_stata", "to_parquet", "to_excel", "to_pickle", "savefig",
)
_VERB_CLASS: dict[str, str] = {}
for _v in _INCLUDE_VERBS:
    _VERB_CLASS[_v] = "include"
for _v in _READ_VERBS:
    _VERB_CLASS[_v] = "read"
for _v in _WRITE_VERBS:
    _VERB_CLASS[_v] = "write"
# longest-first so `read.csv2` wins over `read.csv`; lookbehind blocks `myread_csv`, allows `pd.read_csv`.
_VERB_RE = re.compile(
    r'(?<![\w])(' + '|'.join(re.escape(v) for v in sorted(_VERB_CLASS, key=len, reverse=True)) + r')\s*\('
)
_KIND_BY_CLASS = {"include": "source", "read": "read", "write": "write"}

_CODE_EXT = (".r", ".do", ".py")
_DATA_EXT = (
    ".csv", ".dta", ".rds", ".rdata", ".tab", ".parquet", ".xlsx", ".xls", ".sav",
    ".tsv", ".dat", ".txt", ".feather", ".json", ".pkl",
)
_GRAPHIC_EXT = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps", ".svg", ".tex", ".html", ".tiff", ".bmp", ".gph")
_EXT_BY_CLASS = {"include": _CODE_EXT, "read": _DATA_EXT, "write": _DATA_EXT + _GRAPHIC_EXT}

_STR_LIT = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
_PY_IMPORT_LOCAL = re.compile(r'^\s*(?:from|import)\s+([A-Za-z_][\w.]*)', re.MULTILINE)
_PY_OPEN_DATA_EXT = _DATA_EXT


def _read_text(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _strip_line_comments(text: str) -> str:
    """Blank trailing `#` comments per physical line while preserving string literals, so the verb
    scan never trips on a verb name written inside a comment, but still sees real path literals."""
    out: list[str] = []
    for line in text.splitlines():
        i = 0
        n = len(line)
        while i < n:
            ch = line[i]
            if ch in '"\'':
                m = _STR_LIT.match(line, i)
                if m:
                    i = m.end()
                    continue
                i += 1
                continue
            if ch == '#':
                line = line[:i]
                break
            i += 1
        out.append(line)
    return "\n".join(out)


def _resolve(root: Path, from_rel: str, target: str) -> tuple[str, str]:
    """Return (dst, status) where status is resolved | unresolved | ambiguous. Deterministic:
    candidates are sorted, and a basename collision with no exact path match is `ambiguous` — we
    never silently return the first rglob hit."""
    target_clean = target.strip().replace("\\", "/")
    if target_clean.startswith("./"):
        target_clean = target_clean[2:]
    if not target_clean:
        return target.strip(), "unresolved"
    base = Path(target_clean).name
    caller_dir = (root / from_rel).parent
    for cand in ((root / target_clean), (caller_dir / target_clean)):
        if cand.is_file():
            try:
                return str(cand.resolve().relative_to(root)), "resolved"
            except ValueError:
                pass
    hits = sorted(str(p.relative_to(root)) for p in root.rglob(base) if p.is_file())
    if not hits:
        return target_clean, "unresolved"
    if len(hits) == 1:
        return hits[0], "resolved"
    return target_clean, "ambiguous"


_FIRST_ARG = re.compile(r'\s*(?:file\s*=\s*|path\s*=\s*|filepath_or_buffer\s*=\s*)?([rRbBuU]{0,2}["\']|[^\s])')


def _first_argument_is_literal(text: str, after_paren: int) -> bool:
    m = _FIRST_ARG.match(text, after_paren)
    return bool(m) and m.group(1)[-1] in "\"'"


def _call_literals(text: str, open_paren: int) -> list[str]:
    """String literals inside the balanced parens of a call whose `(` is at index open_paren."""
    depth = 0
    i = open_paren
    n = len(text)
    lits: list[str] = []
    while i < n:
        ch = text[i]
        if ch in '"\'':
            m = _STR_LIT.match(text, i)
            if m:
                lits.append(m.group(0)[1:-1])
                i = m.end()
                continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    return lits


def _pick_filename(lits: list[str], exts: tuple[str, ...]) -> str | None:
    """The last string literal whose basename ends with an expected extension (the filename is
    usually the last path segment, e.g. file.path(dir, "x.R"))."""
    chosen = None
    for lit in lits:
        name = Path(lit.strip().replace("\\", "/")).name.lower()
        if name.endswith(exts):
            chosen = lit
    return chosen


def _line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def _string_spans(text: str) -> list[tuple[int, int]]:
    """Where the string literals are, in order, so a call written inside a string (code an
    author builds as text, `paste0("read_dta('", ...)`) is not taken for a call."""
    spans: list[tuple[int, int]] = []
    i, n = 0, len(text)
    while i < n:
        if text[i] in '"\'':
            m = _STR_LIT.match(text, i)
            if m:
                spans.append((m.start(), m.end()))
                i = m.end()
                continue
        i += 1
    return spans


def _inside(spans: list[tuple[int, int]], pos: int) -> bool:
    k = bisect.bisect_right(spans, (pos, float("inf"))) - 1
    return k >= 0 and spans[k][0] < pos < spans[k][1]


# a name given a string literal on a line of its own (R `f <- "out/x.csv"`, Python `f = "out/x.csv"`);
# followed only when the name is assigned once in the file and is no loop variable
_ASSIGN_LITERAL = re.compile(r'^[ \t]*([A-Za-z_.][\w.]*)[ \t]*(?:<-|=)[ \t]*[rRbBuU]{0,2}'
                             r'("(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\')[ \t]*;?[ \t]*$', re.MULTILINE)
_ASSIGN_ANY = re.compile(r'^[ \t]*([A-Za-z_.][\w.]*)[ \t]*(?:<<?-|=(?!=))', re.MULTILINE)
_LOOP_NAME = re.compile(r'\bfor\s*\(?\s*([A-Za-z_.][\w.]*)\s+in\b')
_BARE_NAME = re.compile(r'(?<![\w.$@])([A-Za-z_.][\w.]*)(?![\w.])(?!\s*(?:\(|=(?!=)))')


def _literal_names(text: str) -> dict[str, str]:
    counts: dict[str, int] = {}
    for m in _ASSIGN_ANY.finditer(text):
        counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    loops = set(_LOOP_NAME.findall(text))
    return {m.group(1): m.group(2)[1:-1] for m in _ASSIGN_LITERAL.finditer(text)
            if counts.get(m.group(1)) == 1 and m.group(1) not in loops}


def _call_names(text: str, open_paren: int) -> list[str]:
    """Bare names passed to a call: no string literal, no called function, no keyword name."""
    depth = 0
    i = open_paren
    n = len(text)
    parts: list[str] = []
    start = open_paren + 1
    while i < n:
        ch = text[i]
        if ch in '"\'':
            m = _STR_LIT.match(text, i)
            if m:
                parts.append(text[start:i])
                i = start = m.end()
                continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    parts.append(text[start:i])
    return [m.group(1) for part in parts for m in _BARE_NAME.finditer(part)]


def _call_edges(root: Path, rel: str, text: str) -> list[Edge]:
    clean = _strip_line_comments(text)
    spans = _string_spans(clean)
    names = _literal_names(clean)
    edges: list[Edge] = []
    for m in _VERB_RE.finditer(clean):
        if _inside(spans, m.start()):
            continue
        verb = m.group(1)
        klass = _VERB_CLASS[verb]
        lits = _call_literals(clean, m.end() - 1)
        target = _pick_filename(lits, _EXT_BY_CLASS[klass])
        held = False
        if target is None and klass != "include":
            # reads and writes only: which scripts call which stays as a certification service sees it
            target = _pick_filename([names[k] for k in _call_names(clean, m.end() - 1) if k in names],
                                    _EXT_BY_CLASS[klass])
            held = target is not None
        if target is None:
            continue
        dst, status = _resolve(root, rel, target)
        if (status == "unresolved" and klass == "read" and not held
                and not _first_argument_is_literal(clean, m.end())):
            # `read_csv(name + "put.csv")`: the fragment is not the path. When it happens
            # to name a shipped file the optimistic edge is kept (it feeds orphan/A13);
            # when it does not, an unresolved edge here would be an A14 false alarm —
            # the assembled path is A18's case, not a missing input.
            continue
        edges.append(Edge(src=rel, dst=dst, kind=_KIND_BY_CLASS[klass], status=status))
    return edges


def _py_literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _py_open_mode(node: ast.Call) -> str:
    if len(node.args) >= 2:
        mode = _py_literal_string(node.args[1])
        return mode or ""
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode = _py_literal_string(keyword.value)
            return mode or ""
    return "r"


def _py_open_kind(node: ast.Call) -> str | None:
    path = _py_literal_string(node.args[0]) if node.args else None
    if path is None or not Path(path).name.lower().endswith(_PY_OPEN_DATA_EXT):
        return None
    mode = _py_open_mode(node)
    if mode.startswith(("w", "a", "x")):
        return "write"
    if mode == "" or "r" in mode or "+" in mode:
        return "read"
    return None


def _py_exists_guard_mentions(test: ast.AST, target: str) -> bool:
    for node in ast.walk(test):
        if isinstance(node, ast.Call) and node.args:
            func = node.func
            name = ""
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            if name in {"exists", "isfile"} and _py_literal_string(node.args[0]) == target:
                return True
    return False


class _TopLevelCalls(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    @override
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    @override
    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            self.names.add(node.func.id)
        self.generic_visit(node)


class _PythonOpenEdges(ast.NodeVisitor):
    def __init__(self, root: Path, rel: str) -> None:
        self.root: Path = root
        self.rel: str = rel
        self.edges: list[Edge] = []
        self.guards: list[ast.AST] = []

    @override
    def visit_If(self, node: ast.If) -> None:
        self.guards.append(node.test)
        for child in node.body:
            self.visit(child)
        _ = self.guards.pop()
        for child in node.orelse:
            self.visit(child)

    @override
    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "open" and node.args:
            target = _py_literal_string(node.args[0])
            kind = _py_open_kind(node)
            if target is not None and kind is not None and not any(_py_exists_guard_mentions(g, target) for g in self.guards):
                dst, status = _resolve(self.root, self.rel, target)
                self.edges.append(Edge(src=self.rel, dst=dst, kind=kind, status=status))
        self.generic_visit(node)


def _python_open_edges(root: Path, rel: str, text: str) -> list[Edge]:
    try:
        module = ast.parse(text)
    except SyntaxError:
        return []
    calls = _TopLevelCalls()
    for stmt in module.body:
        calls.visit(stmt)
    visitor = _PythonOpenEdges(root, rel)
    for stmt in module.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name not in calls.names:
            continue
        visitor.visit(stmt)
    return visitor.edges


def _py_import_edges(root: Path, rel: str, text: str) -> list[Edge]:
    """Python local-module imports only: emit an edge ONLY when the imported name resolves to a
    sibling .py in the package. Library imports (numpy, pandas) never become unresolved includes."""
    edges: list[Edge] = []
    seen: set[str] = set()
    for m in _PY_IMPORT_LOCAL.finditer(text):
        mod = m.group(1).split(".")[0]
        if mod in seen:
            continue
        seen.add(mod)
        dst, status = _resolve(root, rel, mod + ".py")
        if status == "resolved":
            edges.append(Edge(src=rel, dst=dst, kind="import", status=status))
    return edges


def _stata_edges(root: Path, rel: str, text: str, globals_map: dict[str, str] | None = None) -> list[Edge]:
    globals_map = globals_map or {}
    edges: list[Edge] = []
    for regex, kind in [(_STATA_DO, "do"), (_STATA_USE, "data_use"), (_STATA_READ, "data_use")]:
        for match in regex.finditer(text):
            target = _stata_do_target(match) if regex is _STATA_DO else match.group(1)
            if regex is _STATA_USE:
                # `use var1 var2 using data/x.dta`: the file is what follows `using`
                target = re.split(r'\busing\s+', target, flags=re.IGNORECASE)[-1].strip().strip('"')
            for dst, status in _macro_resolve(root, rel, target, globals_map):
                edges.append(Edge(src=rel, dst=dst, kind=kind, status=status))
    for match in _STATA_USE_BARE.finditer(text):
        target = (match.group(1) or match.group(2) or "").strip()
        if not target or Path(target).suffix or target.lower() == "using":
            continue
        for dst, status in _macro_resolve(root, rel, target + ".dta", globals_map):
            edges.append(Edge(src=rel, dst=dst, kind="data_use", status=status))
    loops = _stata_loops(text)
    for match in _STATA_WRITE.finditer(text):
        for path in _expand_write_path(match.group(1), match.start(1), loops):
            dst, status = _resolve(root, rel, _expand_globals(path, globals_map))
            edges.append(Edge(src=rel, dst=dst, kind="write", status=status))
    return edges


def build(root: Path, entries: list[FileEntry]) -> list[Edge]:
    root = root.resolve()
    # Pre-pass (issue #41): collect global-macro definitions across ALL .do files, since the run-all
    # conventionally defines the directory roots that every later script reads through. Entries are
    # sorted by scan(), so first-definition-wins is deterministic.
    globals_map: dict[str, str] = {}
    for entry in entries:
        if entry.language == "stata":
            for name, value in _stata_globals(_read_text(root, entry.path)).items():
                globals_map.setdefault(name, value)
    edges: list[Edge] = []
    for entry in entries:
        if entry.language not in {"stata", "r", "python"}:
            continue
        text = _read_text(root, entry.path)
        if entry.language == "stata":
            edges.extend(_stata_edges(root, entry.path, text, globals_map))
        else:
            edges.extend(_call_edges(root, entry.path, text))
            if entry.language == "python":
                edges.extend(_python_open_edges(root, entry.path, text))
                edges.extend(_py_import_edges(root, entry.path, text))
    return edges


def entry_points(entries: list[FileEntry], edges: list[Edge]) -> list[dict[str, Any]]:
    code = {e.path for e in entries if e.language in {"stata", "r", "python"}}
    # `callers` requires e.resolved: a script whose only includes are dangling (e.g. source('missing.R'))
    # is NOT a real orchestrator, so it must not be manufactured into an entry point / master (issue #23).
    # This deliberately differs from orphan_detector's caller set, which counts ALL include sources
    # (resolved or not) because for dead-script detection a script that *attempts* to run something is
    # not "unreferenced" — its brokenness is reported separately as referenced_missing.
    callers = {e.src for e in edges if e.kind in _INCLUDE_KINDS and e.resolved}
    called = {e.dst for e in edges if e.kind in _INCLUDE_KINDS and e.resolved}
    points: list[dict[str, Any]] = []
    for path in sorted(callers - called):
        points.append({"path": path, "reason": "runs other scripts but is not run by any"})
    if not callers:
        for path in sorted(code):
            name = Path(path).name.lower()
            if any(token in name for token in ("master", "main", "run_all", "runall", "00_", "_00")):
                points.append({"path": path, "reason": "name suggests a master/entry script"})
    return points
