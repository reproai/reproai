"""Detectors for the IQSS Certify target (targets/certify.yaml).

Each detector reads the package statically and returns evidence for one rule of the profile. The
patterns are ours, written from what Certify's published program refuses, fails, marks or notes;
none of Certify's code is copied or imported. A detector that cannot tell stays silent: Certify's
own closing is the authority, and Prep only warns ahead of it.
"""

from __future__ import annotations

import os
import posixpath
import re
import unicodedata
from pathlib import Path
from typing import Any

from .. import dependency_graph as dg
from ..dependency_graph import Edge
from ..inventory import FileEntry, read_source
from ..rule_engine import _STR_SPAN, _ev, _file_evidence, _strip_comment_keep_strings

LIBRARY_ROOT = ".certified/lib/"
_EXCLUDED_TOP = {".git"}
_INSTALLATION_DIRS = ("renv", ".venv", "venv", "env", "node_modules", "__MACOSX")
_STARTUP_FILES = {".Rprofile", ".Renviron", "Rprofile.site", "Renviron.site",
                  "sitecustomize.py", "usercustomize.py", "profile.do"}
_RESERVED_TEXT = (b".certified/step-", b"certified_salt.bin")
_NOTEBOOK_SUFFIXES = (".ipynb", ".rmd", ".qmd")
_SCRIPT_SUFFIXES = (".R", ".r", ".py", ".do")
_ENTRY_CEILING = 100_000
_PACK_PROPOSAL = 10_000
_TEXT_READ_CAP = 20_000_000

_CHDIR = re.compile(r'\bsetwd\s*\(|\bchdir\s*\(')
# a folder change that names its folder as a literal: setwd("x"), os.chdir("x")
_CWD_LITERAL = re.compile(r'\b(?:setwd|chdir)\s*\(\s*[rRbBuU]{0,2}(["\'])((?:\\.|(?!\1)[^\\\n])*)\1\s*\)')
_DEPENDENCY_ROOT = ".certified/deps/"
_ADDRESS = re.compile(r'^(?:https?|ftp)://', re.IGNORECASE)
_NET_READ_CALL = re.compile(
    r'(?<![\w])(?:read\.\w+|read_\w+|fread|vroom|source|load|readRDS|readLines|scan|download\.file|curl_download'
    r'|url|gzcon|pd\.read_\w+|urlretrieve|urlopen|np\.load\w*|open)\s*\(')
_PY_SERVICE = re.compile(r'^\s*(?:import\s+(?:requests|httpx|urllib\.request|urllib3)\b'
                         r'|from\s+(?:requests|httpx|urllib\.request|urllib3)\b|from\s+urllib\s+import\s+request\b)')
_R_SERVICE = re.compile(r'\b(?:library|require|requireNamespace)\s*\(\s*["\']?(?:httr2?|curl)\b|\b(?:httr2?|curl)::')
_PY_KEY_NO_DEFAULT = re.compile(r'\bos\.environ\s*\[\s*["\']')
_R_CACHE_WRITE = re.compile(r'\bsave\.image\s*\(\s*\)|\bsave\.image\s*\([^)]*["\']\.RData["\']'
                            r'|\bsave\s*\([^)]*\bfile\s*=\s*["\']\.RData["\']|\bsavehistory\s*\(')
_ENCODING_ARG = re.compile(r'\b(?:fileEncoding|encoding)\s*=')
_TEXT_DATA_SUFFIXES = (".csv", ".tsv", ".txt")
_R_INSTALL = re.compile(
    r'(?<![\w.])(?:install\.packages|install_(?:github|gitlab|bitbucket|version|cran|local)'
    r'|renv::(?:restore|install|activate|hydrate)|pak::(?:pak|pkg_install)|pkg_install'
    r'|BiocManager::install|p_install|p_load_gh)\s*\(')
_PY_INSTALL = re.compile(r'\b(?:pip3?|conda|mamba|uv)\b["\']?\s*,?\s*["\']?install\b|\bensurepip\b')
_R_INTERACTIVE = re.compile(
    r'\brstudioapi::|\blibrary\s*\(\s*["\']?rstudioapi\b'
    r'|(?<![\w.])(?:View|file\.choose|choose\.files|choose\.dir|readline|menu|askYesNo|select\.list|winDialog)\s*\(')
_PY_INTERACTIVE = re.compile(
    r'(?<![\w.])(?:input|getpass|breakpoint)\s*\(|\bgetpass\.getpass\s*\(|\bpdb\.set_trace\s*\(|\bwebbrowser\.open\w*\s*\(')
_HOOK_DROPPING = (
    re.compile(r'--(?:vanilla|no-init-file)\b'),
    re.compile(r'\bpython[\d.]*\b[^\n]*?(?<![\w-])-(?=[A-Za-z]*[ISE])[A-Za-z]+\b'),
    re.compile(r'\benv\s+-i\b'),
    re.compile(r'\benv\s*=\s*(?:\{\s*\}|dict\s*\(\s*\))'),
)
_REMOTE_LAUNCH = re.compile(r'\b(?:sbatch|srun|salloc|qsub|bsub|mpirun|mpiexec)\b|\bssh\s+(?:-\S+\s+)*\S+@\S+')
# the run's own settings; CERTIFIED_ITEMS / CERTIFIED_ITEMS_OUT are the item-computation interface, read by design
_SETTING_NAME = re.compile(r'\b(?:CERTIFIED_(?:SEED|STEP|DEPTH|LOADED)|R_PROFILE_USER|R_ENVIRON_USER|PYTHONPATH|PYTHONNOUSERSITE|S_ADO)\b')
_R_UNREMAPPED_SEED = re.compile(
    r'\b(?:registerDoRNG|RNGseq|setSeed|set\.generator|dqset\.seed)\s*\(|%dorng%'
    r'|\bRNGkind\s*\([^)]*["\']user'
    r'|\.Random\.seed\s*(?:<<-|<-|=)(?!\s*(?:parallel::)?nextRNG(?:Sub)?Stream\s*\()'
    r'|\bassign\s*\(\s*["\']\.Random\.seed["\']|\btrainControl\s*\([^)]*\bseeds\s*=')
_PY_UNREMAPPED_SEED = re.compile(
    r'\b(?:random\.setstate|random\.SystemRandom|os\.urandom|torch\.Generator|torch\.set_rng_state'
    r'|torch\.cuda\.set_rng_state(?:_all)?)\s*\(|\.set_state\s*\(|\.bit_generator\.state\s*='
    r'|\b(?:jax\.random\.(?:key|PRNGKey)|(?:tf|tensorflow)\.random\.(?:set_seed|Generator)'
    r'|cupy\.random\.(?:seed|RandomState|default_rng))\b'
    r'|\b(?:LGBM\w+|lgb\.\w+|lightgbm\.\w+|CatBoost\w+|catboost\.\w+)\s*\([^)]*\b(?:random_state|random_seed|seed)\s*=')
_R_SOCKET_WORKERS = re.compile(r'(?<![\w.])(?:makeCluster|makePSOCKcluster)\s*\(|\bmultisession\b')
_FORK_TYPE = re.compile(r'type\s*=\s*["\']FORK["\']', re.IGNORECASE)
_R_FORKING = re.compile(r'(?<![\w.])(?:mclapply|mcmapply|mcMap|pvec|mcparallel|makeForkCluster)\s*\(')
_LECUYER = re.compile(r"L'Ecuyer")
_MAKES_FOLDERS = re.compile(r'\bdir\.create\s*\(|\bdir_create\s*\(|\bos\.makedirs\s*\(|\bos\.mkdir\s*\(|\.mkdir\s*\(')


# --- the tree, as Certify lists it -------------------------------------------------------------

def _walk(root: Path) -> tuple[list[str], list[str], list[str]]:
    """(files, empty folders, symbolic links), as root-relative POSIX paths; .git is left out."""
    files: list[str] = []
    empty: list[str] = []
    links: list[str] = []
    for current, dirs, names in os.walk(root):
        rel_dir = Path(current).relative_to(root).as_posix()
        if rel_dir.split("/")[0] in _EXCLUDED_TOP:
            dirs[:] = []
            continue
        if rel_dir == ".":
            dirs[:] = [d for d in dirs if d not in _EXCLUDED_TOP]
        prefix = "" if rel_dir == "." else rel_dir + "/"
        for d in list(dirs):
            if os.path.islink(os.path.join(current, d)):
                links.append(prefix + d)
                dirs.remove(d)
        for name in names:
            if os.path.islink(os.path.join(current, name)):
                links.append(prefix + name)
            else:
                files.append(prefix + name)
        if not dirs and not names and rel_dir != ".":
            empty.append(rel_dir)
    return sorted(files), sorted(empty), sorted(links)


def _under_installation(path: str) -> bool:
    return any(part in _INSTALLATION_DIRS for part in path.split("/")[:-1])


def _authored(path: str) -> bool:
    return not path.startswith(LIBRARY_ROOT) and not _under_installation(path)


def _scripts(entries: list[FileEntry], languages: set[str]) -> list[FileEntry]:
    return [e for e in entries
            if e.language in languages and e.path.lower().endswith((".r", ".py")) and _authored(e.path)]


def _code_lines(text: str, lang: str):
    for number, line in enumerate(text.splitlines(), start=1):
        code = _strip_comment_keep_strings(line, lang)
        if code.strip():
            yield number, line, code


def _line_hits(root: Path, scripts: list[FileEntry], patterns: dict[str, re.Pattern[str]]) -> list[dict[str, Any]]:
    hits = []
    for e in scripts:
        pattern = patterns.get(e.language)
        if pattern is None:
            continue
        for number, line, code in _code_lines(read_source(root, e.path), e.language):
            if pattern.search(code):
                hits.append(_ev(e.path, number, line))
    return hits


def _plain(reference: str) -> str:
    return posixpath.normpath(reference[2:] if reference.startswith("./") else reference)


def _absolute(reference: str) -> bool:
    """A path no change of folder makes relative: absolute, home, drive, network share or address
    (backslashes already turned into slashes)."""
    return reference.startswith(("/", "~")) or "://" in reference or bool(re.match(r'^[A-Za-z]:/', reference))


def _leaves(reference: str) -> bool:
    """Outside the dataset as read from the root: one of the above, or a climb above the root."""
    if _absolute(reference):
        return True
    plain = _plain(reference)
    return plain == ".." or plain.startswith("../")


def _literal_calls(root: Path, e: FileEntry, whole: bool = False):
    """(class, literal target, line, line text) for each read/include/write call with a literal path;
    with `whole`, only calls whose path is the whole first argument, not a fragment of one being built."""
    text = read_source(root, e.path)
    clean = dg._strip_line_comments(text)
    lines = text.splitlines()
    for m in dg._VERB_RE.finditer(clean):
        if whole and not dg._first_argument_is_literal(clean, m.end()):
            continue
        klass = dg._VERB_CLASS[m.group(1)]
        target = dg._pick_filename(dg._call_literals(clean, m.end() - 1), dg._EXT_BY_CLASS[klass])
        if target is None:
            continue
        number = dg._line_of(clean, m.start())
        yield klass, target.strip().replace("\\", "/"), number, lines[number - 1] if number <= len(lines) else ""


# --- detectors -----------------------------------------------------------------------------------

def _cf1(files: list[str]) -> tuple[list[dict[str, Any]], str]:
    stata = [f for f in files if f.endswith(".do") and not f.startswith(LIBRARY_ROOT)]
    return _file_evidence(stata), f"{len(stata)} Stata script(s); Certify 0.2.0 runs R and Python only."


def _cf2_cf3(files: list[str]) -> dict[str, tuple[list[dict[str, Any]], str]]:
    scripts = [f for f in files if f.endswith(_SCRIPT_SUFFIXES) and not f.startswith(LIBRARY_ROOT)]
    notebooks = [f for f in files if f.lower().endswith(_NOTEBOOK_SUFFIXES) and _authored(f)]
    if not notebooks:
        return {}
    if not scripts:
        return {"CF2-notebook-only": (_file_evidence(notebooks), "Code lives only in notebooks; no script to run.")}
    return {"CF3-notebook-not-run": (_file_evidence(notebooks),
                                      f"{len(notebooks)} notebook(s) beside {len(scripts)} script(s); notebooks are not run.")}


def _moved(scripts: list[FileEntry], texts: dict[str, str], edges: list[Edge]) -> set[str]:
    """Scripts that run from a folder they or a script sourcing them moved to: their paths are
    left to closing, which sees where the run stands."""
    moved = {e.path for e in scripts if _CHDIR.search(dg._strip_line_comments(texts[e.path]))}
    grew = True
    while grew:
        grew = False
        for edge in edges:
            if edge.kind in {"source", "import"} and edge.resolved and edge.src in moved and edge.dst not in moved:
                moved.add(edge.dst)
                grew = True
    return moved


def _cf4_cf22(root: Path, scripts: list[FileEntry], texts: dict[str, str],
              edges: list[Edge]) -> dict[str, list[dict[str, Any]]]:
    from_script: list[dict[str, Any]] = []
    missing_folder: list[dict[str, Any]] = []
    makes_folders = any(_MAKES_FOLDERS.search(t) for t in texts.values())
    moved = _moved(scripts, texts, edges)
    for e in scripts:
        if e.path in moved:
            continue
        here = posixpath.dirname(e.path)
        for klass, target, number, line in _literal_calls(root, e):
            if _absolute(target) or target.startswith("./"):
                continue
            # where the path lands read from the root (every step starts there), and from the script's folder
            at_root = None if _leaves(target) else _plain(target)
            beside = posixpath.normpath(posixpath.join(here, target))
            beside = None if not here or _leaves(beside) else beside
            if klass in {"read", "include"}:
                if beside and (root / beside).is_file() and not (at_root and (root / at_root).is_file()):
                    from_script.append(_ev(e.path, number, line))
                continue
            folder = posixpath.dirname(target)
            if folder in ("", "."):
                continue
            if beside and (root / beside).parent.is_dir() and not (at_root and (root / at_root).parent.is_dir()):
                from_script.append(_ev(e.path, number, line))
            elif not (at_root and (root / at_root).parent.is_dir()) and not makes_folders:
                missing_folder.append(_ev(e.path, number, line))
    return {"CF4-path-from-script-folder": from_script, "CF22-output-folder-missing": missing_folder}


def _cf5(root: Path, scripts: list[FileEntry], files: list[str]) -> list[dict[str, Any]]:
    """Reads, sources and folder changes that point outside the dataset, judged the way closing's
    reading audit judges them: only the path a read or a folder change names (not any string), read
    from the folder an earlier setwd()/chdir() moved to, then from the root, then from the script's
    own folder; outside only when none of those lands on a deposited file or folder."""
    present = set(files)
    folders = {""} | {posixpath.dirname(f) for f in files}
    for f in list(folders):
        while f:
            f = posixpath.dirname(f)
            folders.add(f)
    evidence: list[dict[str, Any]] = []
    for e in scripts:
        text = read_source(root, e.path)
        clean = dg._strip_line_comments(text)
        lines = text.splitlines()
        here = posixpath.dirname(e.path)
        events = [(dg._line_of(clean, m.start()), 0, "folder", m.group(2).strip().replace("\\", "/"))
                  for m in _CWD_LITERAL.finditer(clean)]
        events += [(number, 1, "read", target) for klass, target, number, _ in _literal_calls(root, e, whole=True)
                   if klass in {"read", "include"}]
        moved_to: str | None = None
        for number, _, kind, reference in sorted(events):
            if "://" in reference:
                continue                                       # an address: CF6
            from_root = reference if moved_to is None or _absolute(reference) else posixpath.join(moved_to, reference)
            candidates = (_plain(from_root), posixpath.normpath(posixpath.join(here, from_root)))
            line = lines[number - 1] if number <= len(lines) else ""
            if kind == "folder":
                if _leaves(from_root):
                    evidence.append(_ev(e.path, number, line))
                elif any(("" if c == "." else c) in folders for c in candidates if not _leaves(c)):
                    moved_to = _plain(from_root)
                continue
            if any(c in present for c in candidates) or _plain(from_root).startswith(_DEPENDENCY_ROOT):
                continue
            if _leaves(from_root):
                evidence.append(_ev(e.path, number, line))
    return evidence


def _cf6(root: Path, scripts: list[FileEntry]) -> list[dict[str, Any]]:
    network: list[dict[str, Any]] = []
    for e in scripts:
        for number, line, code in _code_lines(read_source(root, e.path), e.language):
            literals = [m.group(0)[1:-1] for m in _STR_SPAN.finditer(code)]
            if any(_ADDRESS.match(lit) for lit in literals) and _NET_READ_CALL.search(code):
                network.append(_ev(e.path, number, line))
    return network


def _cf7(root: Path, scripts: list[FileEntry]) -> tuple[list[dict[str, Any]], str]:
    evidence: list[dict[str, Any]] = []
    keyed: list[str] = []
    for e in scripts:
        pattern = _PY_SERVICE if e.language == "python" else _R_SERVICE
        text = read_source(root, e.path)
        hit = next(((n, line) for n, line, code in _code_lines(text, e.language) if pattern.search(code)), None)
        if hit is None:
            continue
        evidence.append(_ev(e.path, hit[0], hit[1]))
        if e.language == "python" and any(_PY_KEY_NO_DEFAULT.search(c) for _, _, c in _code_lines(text, e.language)):
            keyed.append(e.path)
    why = f"{len(evidence)} script(s) call an outside service; record them with certify record."
    if keyed:
        why += f" Read without a default (os.environ[...]): {', '.join(keyed)}."
    return evidence, why


def _cf8(files: list[str], empty: list[str], links: list[str]) -> tuple[list[dict[str, Any]], str]:
    problems: list[tuple[str, str]] = [(link, "symbolic link") for link in links]
    problems += [(folder, "empty folder") for folder in empty]
    seen_case: dict[str, str] = {}
    seen_form: dict[str, str] = {}
    for f in files:
        if any(ord(ch) < 0x20 for ch in f):
            problems.append((f, "control character in the name"))
        canonical = unicodedata.normalize("NFC", f)
        if canonical in seen_form and seen_form[canonical] != f:
            problems.append((f, f"same name as {seen_form[canonical]} in another Unicode form"))
        seen_form.setdefault(canonical, f)
        folded = canonical.casefold()
        if folded in seen_case and seen_case[folded] != canonical:
            problems.append((f, f"differs from {seen_case[folded]} only in letter case"))
        seen_case.setdefault(folded, canonical)
    evidence = [_ev(path, None, what) for path, what in problems[:50]]
    if len(problems) > 50:
        evidence.append(_ev(f"(+{len(problems) - 50} more)"))
    kinds = sorted({what.split(" ")[0] for _, what in problems})
    return evidence, f"{len(problems)} path problem(s) closing would refuse ({', '.join(kinds)})."


def _cf9(root: Path, files: list[str]) -> tuple[list[dict[str, Any]], str]:
    folders: dict[str, list[int]] = {}
    for f in files:
        parts = f.split("/")
        for i, part in enumerate(parts[:-1]):
            if part in _INSTALLATION_DIRS:
                top = "/".join(parts[: i + 1])
                folders.setdefault(top, []).append((root / f).stat().st_size)
                break
    evidence = [_ev(folder + "/", None, f"{len(sizes)} files, {sum(sizes) / 1_000_000:.1f} MB")
                for folder, sizes in sorted(folders.items())]
    return evidence, f"{len(folders)} installation or unzip folder(s) inside the dataset."


def _cf10_cf11(root: Path, files: list[str]) -> dict[str, list[dict[str, Any]]]:
    startup = [f for f in files if Path(f).name in _STARTUP_FILES and not f.startswith(LIBRARY_ROOT)]
    reserved: list[str] = []
    for f in files:
        if f.startswith(LIBRARY_ROOT):
            continue
        path = root / f
        try:
            if path.stat().st_size > _TEXT_READ_CAP:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in data[:8192]:
            continue
        if any(token in data for token in _RESERVED_TEXT):
            reserved.append(f)
    return {"CF10-startup-file": _file_evidence(startup), "CF11-reserved-name": _file_evidence(reserved)}


def _cf13_cf24(root: Path, edges: list[Edge], texts: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    """A text file that is not UTF-8, read without naming its encoding: R reads on and garbles the
    characters (CF13), Python stops with a decode error (CF24), since the runs read text as UTF-8."""
    out: dict[str, list[dict[str, Any]]] = {"CF13-non-utf8-text-read": [], "CF24-non-utf8-text-read-python": []}
    readers: dict[str, list[str]] = {}
    for edge in edges:
        if edge.edge_class == "read" and edge.resolved and edge.dst.lower().endswith(_TEXT_DATA_SUFFIXES):
            readers.setdefault(edge.dst, []).append(edge.src)
    for data_path, sources in sorted(readers.items()):
        if _is_utf8(root / data_path):
            continue
        undeclared = sorted({s for s in sources if s in texts and not _ENCODING_ARG.search(texts[s])})
        for rule_id, wanted in (("CF13-non-utf8-text-read", False), ("CF24-non-utf8-text-read-python", True)):
            by = [s for s in undeclared if s.lower().endswith(".py") is wanted]
            if by:
                out[rule_id].append(_ev(data_path, None, f"not UTF-8; read by {', '.join(by)} with no encoding named"))
    return out


def _is_utf8(path: Path) -> bool:
    cap = 2_000_000
    try:
        with path.open("rb") as handle:
            data = handle.read(cap)
    except OSError:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        # a character cut where the read stopped is not an error; anywhere else it is
        return len(data) == cap and exc.start >= len(data) - 3
    return True


def _cf16(root: Path, entries: list[FileEntry]) -> list[dict[str, Any]]:
    evidence = []
    for e in entries:
        if not e.path.endswith(_SCRIPT_SUFFIXES) or not _authored(e.path):
            continue
        for number, line in enumerate(read_source(root, e.path).splitlines(), start=1):
            if any(p.search(line) for p in _HOOK_DROPPING):
                evidence.append(_ev(e.path, number, line))
    return evidence


def _cf21(scripts: list[FileEntry], texts: dict[str, str]) -> list[dict[str, Any]]:
    evidence = []
    for e in scripts:
        if e.language != "r" or _LECUYER.search(texts[e.path]):
            continue
        hit = next(((n, line) for n, line, code in _code_lines(texts[e.path], "r") if _R_FORKING.search(code)), None)
        if hit is not None:
            evidence.append(_ev(e.path, hit[0], hit[1]))
    return evidence


def _cf23(files: list[str]) -> tuple[list[dict[str, Any]], str]:
    if len(files) <= _ENTRY_CEILING:
        return [], ""
    counts: dict[str, int] = {}
    for f in files:
        parts = f.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            counts["/".join(parts[:i])] = counts.get("/".join(parts[:i]), 0) + 1
    big = sorted(folder for folder, n in counts.items() if n >= _PACK_PROPOSAL)
    top = [f for f in big if not any(f.startswith(other + "/") for other in big if other != f)]
    evidence = [_ev(folder + "/", None, f"{counts[folder]} files: pack as one entry") for folder in top] or [_ev(".")]
    return evidence, f"{len(files)} files, above Certify's ceiling of {_ENTRY_CEILING} entries."


def detect(root: Path, entries: list[FileEntry], edges: list[Edge]) -> dict[str, tuple[list[dict[str, Any]], str]]:
    """Evidence and a one-line rationale per rule id; a rule with no evidence is absent."""
    files, empty, links = _walk(root)
    scripts = _scripts(entries, {"r", "python"})
    r_scripts = [e for e in scripts if e.language == "r"]
    texts = {e.path: read_source(root, e.path) for e in scripts}
    out: dict[str, tuple[list[dict[str, Any]], str]] = {}

    def put(rule_id: str, evidence: list[dict[str, Any]], why: str) -> None:
        if evidence:
            out[rule_id] = (evidence, why)

    put("CF1-stata-not-runnable", *_cf1(files))
    out.update(_cf2_cf3(files))
    for rule_id, evidence in _cf4_cf22(root, scripts, texts, edges).items():
        put(rule_id, evidence, f"{len(evidence)} path(s) that fail when every step starts at the root."
            if rule_id.startswith("CF4") else f"{len(evidence)} write(s) into a folder that neither ships nor is created.")
    put("CF5-outside-reference", _cf5(root, scripts, files),
        "Reads or folder changes that point outside the dataset, however the run's folder is reckoned.")
    put("CF6-network-read", _cf6(root, scripts), "Reads from a web address; the runs have no network.")
    put("CF7-outside-service", *_cf7(root, scripts))
    put("CF8-tree-paths", *_cf8(files, empty, links))
    put("CF9-installation-folder", *_cf9(root, files))
    for rule_id, evidence in _cf10_cf11(root, files).items():
        put(rule_id, evidence, f"{len(evidence)} file(s) closing refuses.")
    put("CF12-runtime-cache-write", _line_hits(root, r_scripts, {"r": _R_CACHE_WRITE}),
        "Writes R's workspace or history file, which fails the step.")
    for rule_id, evidence in _cf13_cf24(root, edges, texts).items():
        put(rule_id, evidence, "Text data in another encoding, read without naming it; the runs read UTF-8.")
    put("CF14-runtime-install", _line_hits(root, scripts, {"r": _R_INSTALL, "python": _PY_INSTALL}),
        "Installs a package while running; the runs have no network.")
    put("CF15-interactive-call", _line_hits(root, scripts, {"r": _R_INTERACTIVE, "python": _PY_INTERACTIVE}),
        "Waits for a person or a desktop program; the runs have input closed.")
    put("CF16-hook-dropping-launch", _cf16(root, entries),
        "Launches a runtime that skips its startup files (comments count here).")
    put("CF17-remote-launch", _line_hits(root, scripts, {"r": _REMOTE_LAUNCH, "python": _REMOTE_LAUNCH}),
        "Sends work to another machine.")
    put("CF18-certification-setting-named", _line_hits(root, scripts, {"r": _SETTING_NAME, "python": _SETTING_NAME}),
        "Names a setting the certified run rests on; the certificate is marked.")
    put("CF19-unremappable-seed", _line_hits(root, scripts, {"r": _R_UNREMAPPED_SEED, "python": _PY_UNREMAPPED_SEED}),
        "A seeding form Certify cannot re-map; the certificate is marked.")
    socket = [ev for ev in _line_hits(root, r_scripts, {"r": _R_SOCKET_WORKERS})
              if not _FORK_TYPE.search(ev.get("snippet", ""))]
    put("CF20-socket-workers", socket, "Socket workers, which cannot start where local addresses are denied.")
    put("CF21-forked-workers-default-rng", _cf21(scripts, texts),
        "Forked workers under R's default generator: the two practice runs differ.")
    put("CF23-entry-count", *_cf23(files))
    return out
