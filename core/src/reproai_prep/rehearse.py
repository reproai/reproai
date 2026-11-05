"""Rehearse: run a COPY of the package the way a certification service will, before it does.

The one engine command that executes author code. It copies the package (the original is never
run or touched), runs the entry scripts in order from the copy's root under fixed settings (UTC,
the C locale with UTF-8, figures to files only, a private empty home folder, the network denied
as far as this machine allows, every step's global random generator seeded), and, with two runs,
compares what each run wrote. The result predicts what a certification service's closing will
find at run time: a failing step, a runtime-cache file left behind, outputs that differ between
two honest runs, a number that moved with the clock. It is a rehearsal: the service's own closing
decides, and nothing here is a reproducibility verdict.

R and Python scripts are rehearsed. The author's own installed libraries are used, since Prep
never vendors them; the service copies them in with its own tool.
"""

from __future__ import annotations

import hashlib
import io
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
import zlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import GENERATED_BY, dependency_graph, inventory

SEED = 20261105
DEFAULT_TIMEOUT = 3600            # a certification service's per-script cap at closing
_TAIL_LINES = 25
_LOCALE = "C.UTF-8"
_DEAD_PROXY = "http://127.0.0.1:9"
_RUNTIME_CACHE_NAMES = {".RData", ".Rhistory", ".DS_Store", "Thumbs.db"}
_RUNTIME_CACHE_DIRS = {"__pycache__", ".Rproj.user", ".ipynb_checkpoints"}
_NUMBER = re.compile(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?')
_CLOSE_ENOUGH = 5e-5              # four significant figures, what a printed table carries
# stamps that change with every run and say nothing about the result
_PDF_STAMPS = re.compile(rb'/(?:CreationDate|ModDate)\s*\([^)]*\)|/ID\s*\[[^\]]*\]')
_DTA_STAMP = re.compile(rb'<timestamp>.*?</timestamp>', re.DOTALL)
# a PDF's streams, with the dictionary before each, and the parts that only record where objects sit
_PDF_STREAM = re.compile(rb'<<(.*?)>>\s*stream\r?\n(.*?)endstream', re.DOTALL)
_PDF_LAYOUT = re.compile(rb'/Length\s+\d+(?:\s+\d+\s+R)?|\bxref\b.*?(?=\btrailer\b)|startxref\s+\d+', re.DOTALL)
_PDF_LENGTH_REF = re.compile(rb'/Length\s+(\d+)\s+\d+\s+R')
_PDF_NUMBER_OBJ = re.compile(rb'\b(\d+)\s+\d+\s+obj\s*\d+\s*endobj')
# stargazer's '% Date and time: ...' and xtable's '% Tue Nov  5 ...' stamps, up to the time of day,
# wherever they sit (an author's code that pastes a table's lines together leaves them mid-line);
# then other stamp comment lines, whole, only when the line holds no LaTeX of the table itself
_TEXT_STAMPS = re.compile(r'%[ \t]*(?:Date and time|Created on|Generated on):?[^\n\\]*?\d{1,2}:\d{2}(?::\d{2})?'
                          r'|%[ \t]*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) [A-Z][a-z]{2} +\d{1,2} \d{2}:\d{2}:\d{2} \d{4}'
                          r'|^(?:%|#|\*)\s*(?:Date and time|Created on|Generated on)\b[^\n\\]*$'
                          r'|^% (?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) [^\n\\]*$', re.MULTILINE)
_ZIP_SUFFIXES = {".xlsx", ".docx", ".pptx"}

_FAILURE_HINTS = (
    (re.compile(r"cannot open (?:the )?(?:file|connection)|No such file or directory|FileNotFoundError|does not exist|cannot change working directory", re.I),
     "path", "A file the step reads is not where the path says, counted from the package root. Spell the path from the root, or ship the file."),
    (re.compile(r"there is no package called|No module named|ModuleNotFoundError|could not find function", re.I),
     "library", "A library is not installed here, or a script relied on one attached in an earlier session. Load it in the script itself (library(x) or import x); a certification service copies installed libraries in with its own tool."),
    (re.compile(r"Could not resolve host|Temporary failure in name resolution|Network is unreachable|Connection refused|ProxyError|cannot open URL|Failed to connect", re.I),
     "network", "The step reached for the network, which the run denies. Download the file beforehand and ship it, declare it with the certification service, or record service calls with its tool."),
    (re.compile(r"object '.*' not found|NameError: name", re.I),
     "session_state", "The step uses an object an earlier script or an interactive session defined. Each script runs as its own process: define or load it in the script."),
    (re.compile(r"Permission denied", re.I),
     "permission", "The step writes outside the package or into a read-only place. Write under the package root."),
)


@dataclass
class StepResult:
    script: str
    exit_code: int | None
    seconds: float
    timed_out: bool
    tail: str
    cache_left: list[str] = field(default_factory=list)
    hints: list[dict[str, str]] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return self.timed_out or self.exit_code != 0 or bool(self.cache_left)


@dataclass
class RunResult:
    started: float
    steps: list[StepResult]
    outputs: dict[str, str]           # path the run wrote -> sha256 of its normalized bytes

    @property
    def failed(self) -> bool:
        return any(s.failed for s in self.steps)


# --- what runs, and how ----------------------------------------------------------------------

def run_order(root: Path, explicit: list[str] | None = None) -> list[str]:
    """The scripts to run, in order: the author's list, or the R and Python entry scripts (scripts
    nothing else calls) in path order, which is what a certification service proposes."""
    if explicit:
        for rel in explicit:
            p = (root / rel).resolve()
            if not p.is_file() or root.resolve() not in p.parents:
                raise ValueError(f"not a script inside the package: {rel}")
        return list(explicit)
    entries = inventory.scan(root)
    edges = dependency_graph.build(root, entries)
    # every script nothing else calls, in path order (not only the orchestrators: a package of
    # independent scripts runs them all)
    called = {e.dst for e in edges if e.edge_class == "include" and e.resolved}
    scripts = [e.path for e in entries if e.path.lower().endswith((".r", ".py")) and not e.path.startswith(".certified/")]
    return sorted(s for s in scripts if s not in called)


def network_means() -> str:
    """How this machine can deny a run the network: a network namespace, the macOS sandbox, or
    proxy settings alone (which a program that ignores proxies can get past)."""
    if platform.system() == "Linux" and shutil.which("unshare"):
        try:
            if subprocess.run(["unshare", "-rn", "true"], capture_output=True, timeout=20).returncode == 0:
                return "namespace"
        except (OSError, subprocess.TimeoutExpired):
            pass
    if platform.system() == "Darwin" and shutil.which("sandbox-exec"):
        return "sandbox"
    return "proxy"


def _wrap(cmd: list[str], means: str) -> list[str]:
    if means == "namespace":
        return ["unshare", "-rn", *cmd]
    if means == "sandbox":
        profile = '(version 1)(allow default)(deny network*)(allow network* (local ip "localhost:*"))'
        return ["sandbox-exec", "-p", profile, *cmd]
    return cmd


def _author_paths(interpreters: dict[str, str]) -> dict[str, str]:
    """The author's library locations, read under their real home before the run's is replaced."""
    paths: dict[str, str] = {}
    try:
        r = subprocess.run([interpreters["R"], "-e", "cat(.libPaths(), sep='\\n')"], capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            paths["R_LIBS"] = os.pathsep.join(r.stdout.split())
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        r = subprocess.run([interpreters["python"], "-c", "import site; print(site.getuserbase())"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            paths["PYTHONUSERBASE"] = r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return paths


def _hooks(folder: Path, step: int) -> dict[str, str]:
    """Startup files that seat a fixed seed for the step, as a certification service seats its own."""
    folder.mkdir(parents=True, exist_ok=True)
    seed = SEED + step
    (folder / "Rprofile").write_text(f"set.seed({seed})\n", encoding="utf-8")
    py = folder / "py"
    py.mkdir(exist_ok=True)
    (py / "sitecustomize.py").write_text(
        "import random\n"
        f"random.seed({seed})\n"
        "try:\n    import numpy\n    numpy.random.seed(" + str(seed) + ")\nexcept Exception:\n    pass\n",
        encoding="utf-8")
    (folder / "matplotlibrc").write_text("backend: Agg\nsvg.hashsalt: reproai\n", encoding="utf-8")
    return {"R_PROFILE_USER": str(folder / "Rprofile"), "PYTHONPATH": str(py), "MPLCONFIGDIR": str(folder)}


def _env(home: Path, hooks: dict[str, str], author: dict[str, str]) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k in {"PATH", "SYSTEMROOT", "COMSPEC"}}
    env.update(author)
    # a throwaway library first: anything a script installs lands there, never in the author's own
    scratch_lib = home / "R-library"
    scratch_lib.mkdir(parents=True, exist_ok=True)
    env["R_LIBS"] = os.pathsep.join(p for p in (str(scratch_lib), author.get("R_LIBS", "")) if p)
    env["R_LIBS_USER"] = str(scratch_lib)
    env.update(hooks)
    env.update({
        "HOME": str(home), "USERPROFILE": str(home), "TMPDIR": str(home / "tmp"),
        "TZ": "UTC", "LC_ALL": _LOCALE, "LANG": _LOCALE, "PYTHONUTF8": "1", "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1", "MPLBACKEND": "Agg", "SOURCE_DATE_EPOCH": "1717200000",
        "R_ENVIRON_USER": str(home / ".Renviron-none"),
    })
    for name in ("http_proxy", "https_proxy", "ftp_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "FTP_PROXY", "ALL_PROXY"):
        env[name] = _DEAD_PROXY
    env["no_proxy"] = env["NO_PROXY"] = "localhost,127.0.0.1,::1"
    (home / "tmp").mkdir(parents=True, exist_ok=True)
    return env


# --- one run ---------------------------------------------------------------------------------

def _snapshot(root: Path) -> dict[str, tuple[int, str]]:
    """path -> (modification time, fingerprint of the normalized bytes)."""
    out: dict[str, tuple[int, str]] = {}
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in names:
            p = Path(current) / name
            if p.is_symlink() or not p.is_file():
                continue
            out[p.relative_to(root).as_posix()] = (p.stat().st_mtime_ns, _fingerprint(p))
    return out


def _pdf_normalized(data: bytes) -> bytes:
    """Streams are inflated before the stamps come out (cairo keeps the creation date in a
    compressed object stream); cross-reference data and lengths, which only say where objects sit
    and move when a stamp's compressed size does, are left out."""
    parts = []
    for m in _PDF_STREAM.finditer(data):
        head, body = m.group(1), m.group(2)
        if re.search(rb'/Type\s*/XRef\b', head):
            continue
        try:
            body = zlib.decompressobj().decompress(body)
        except zlib.error:
            pass
        parts.append(_PDF_LAYOUT.sub(b"", head) + b"\n" + body)
    # a length written as its own object ('/Length 18 0 R'; object 18 holds the number) goes too
    length_objects = set(_PDF_LENGTH_REF.findall(data))
    skeleton = _PDF_NUMBER_OBJ.sub(lambda m: b"" if m.group(1) in length_objects else m.group(0),
                                   _PDF_STREAM.sub(b"", data))
    parts.append(_PDF_LAYOUT.sub(b"", skeleton))
    return _PDF_STAMPS.sub(b"", b"\n".join(parts))


def _normalized(path: Path) -> bytes:
    data = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _pdf_normalized(data)
    if suffix == ".dta":
        return _DTA_STAMP.sub(b"", data)
    if suffix in _ZIP_SUFFIXES:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                return b"".join(n.encode() + z.read(n) for n in sorted(z.namelist()) if not n.startswith("docProps/"))
        except zipfile.BadZipFile:
            return data
    if suffix == ".tex":
        # only in LaTeX tables, as IQSS Certify sets them aside: the same line in a .txt file or a
        # sink() log is an output that differs, and it grades T2 there
        return _TEXT_STAMPS.sub("", data.decode("utf-8", errors="replace")).encode("utf-8")
    return data


def _fingerprint(path: Path) -> str:
    try:
        return hashlib.sha256(_normalized(path)).hexdigest()
    except OSError:
        return "unreadable"


def _hints(text: str) -> list[dict[str, str]]:
    return [{"kind": kind, "hint": hint} for pattern, kind, hint in _FAILURE_HINTS if pattern.search(text)]


def _run_once(source: Path, where: Path, order: list[str], interpreters: dict[str, str], author: dict[str, str],
              timeout: int, means: str) -> RunResult:
    pkg = where / "package"
    shutil.copytree(source, pkg, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    before = _snapshot(pkg)
    started = time.time()
    steps: list[StepResult] = []
    for index, script in enumerate(order):
        language = "python" if script.lower().endswith(".py") else "R"
        home = where / f"home-{index}"
        env = _env(home, _hooks(where / f"hooks-{index}", index), author)
        cmd = _wrap([interpreters[language], script], means)
        t0 = time.time()
        try:
            r = subprocess.run(cmd, cwd=pkg, env=env, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL)
            code, timed_out = r.returncode, False
            transcript = (r.stdout + r.stderr).decode("utf-8", errors="replace")
        except subprocess.TimeoutExpired as exc:
            code, timed_out = None, True
            transcript = ((exc.stdout or b"") + (exc.stderr or b"")).decode("utf-8", errors="replace")
        tail = "\n".join(transcript.splitlines()[-_TAIL_LINES:])
        cache = sorted(p for p in _paths(pkg) if p not in before and _is_runtime_cache(p))
        step = StepResult(script, code, round(time.time() - t0, 2), timed_out, tail, cache)
        if step.failed:
            step.hints = _hints(transcript)
        steps.append(step)
        if step.failed:
            break
    after = _snapshot(pkg)
    # what the run wrote: new files and files rewritten, even with the bytes they already had
    outputs = {p: h for p, (m, h) in after.items() if before.get(p, (None, None))[0] != m and not _is_runtime_cache(p)}
    return RunResult(started, steps, outputs)


def _paths(root: Path) -> list[str]:
    return [(Path(current) / name).relative_to(root).as_posix()
            for current, dirs, names in os.walk(root) if ".git" not in Path(current).relative_to(root).parts
            for name in names]


def _is_runtime_cache(path: str) -> bool:
    parts = path.split("/")
    return parts[-1] in _RUNTIME_CACHE_NAMES or any(p in _RUNTIME_CACHE_DIRS for p in parts[:-1]) or path.endswith(".pyc")


# --- two runs, compared ------------------------------------------------------------------------

_TIME_OF_DAY = re.compile(r'\b\d{1,2}:\d{2}:\d{2}\b|\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}')


def _looks_like_clock(text_a: str, text_b: str, pairs: list[tuple[float, float]], elapsed: float) -> bool:
    changed = [(x, y) for x, y in zip(text_a.splitlines(), text_b.splitlines()) if x != y]
    if any(_TIME_OF_DAY.search(x) or _TIME_OF_DAY.search(y) for x, y in changed):
        return True
    for unit in (1, 1000):          # seconds or milliseconds since 1970, moved by about the time between runs
        if any(1.0e9 * unit <= abs(x) <= 4.0e9 * unit and abs(x - y) <= (elapsed * 1.5 + 5) * unit for x, y in pairs):
            return True
    return False


def _numbers(path: Path) -> tuple[str, list[float]] | None:
    try:
        text = _normalized(path).decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return _NUMBER.sub("#", text), [float(m) for m in _NUMBER.findall(text)]


def _compare(a_root: Path, b_root: Path, a: RunResult, b: RunResult) -> list[dict[str, Any]]:
    elapsed = abs(b.started - a.started)
    diffs: list[dict[str, Any]] = []
    for path in sorted(set(a.outputs) | set(b.outputs)):
        if path not in a.outputs or path not in b.outputs:
            diffs.append({"path": path, "difference": "written by one run only"})
            continue
        if a.outputs[path] == b.outputs[path]:
            continue
        na, nb = _numbers(a_root / path), _numbers(b_root / path)
        if na is None or nb is None or na[0] != nb[0] or len(na[1]) != len(nb[1]):
            diffs.append({"path": path, "difference": "different content"})
            continue
        pairs = [(x, y) for x, y in zip(na[1], nb[1]) if x != y]
        if not pairs:
            diffs.append({"path": path, "difference": "different content"})
            continue
        worst = max(abs(x - y) / max(abs(x), abs(y), 1e-300) for x, y in pairs)
        clock = _looks_like_clock(_normalized(a_root / path).decode("utf-8", "replace"),
                                  _normalized(b_root / path).decode("utf-8", "replace"), pairs, elapsed)
        diffs.append({"path": path, "difference": "numbers moved", "largest_relative_change": worst,
                      "looks_like_clock": clock, "numbers_changed": len(pairs)})
    return diffs


def _grade(runs: list[RunResult], diffs: list[dict[str, Any]] | None) -> str:
    if any(r.failed for r in runs):
        return "failed"
    if not any(r.outputs for r in runs):
        return "no_outputs"
    if diffs is None:
        return "ran"
    if not diffs:
        return "identical"
    if all(d["difference"] == "numbers moved" and d["largest_relative_change"] < _CLOSE_ENOUGH and not d["looks_like_clock"]
           for d in diffs):
        return "numerically_close"
    return "different"


_MEANING = {
    "failed": "A step failed, timed out, or left a runtime-cache file; a certification service's closing stops here too.",
    "no_outputs": "The steps ran but wrote no file; there is nothing for a certification to compare or certify.",
    "ran": "Every step ran (one run; pass --runs 2 to check that two runs agree).",
    "identical": "Two runs wrote the same outputs, apart from known stamps (expected to grade T0 at IQSS Certify).",
    "numerically_close": "Two runs differ only beyond the fourth significant figure (expected to grade T1 at IQSS Certify).",
    "different": "Two runs wrote different outputs (expected to grade T2 at IQSS Certify, which refuses unless disclosed). Find the source: an unseeded draw, the clock, worker processes, file order.",
}


def rehearse(root: Path, scripts: list[str] | None = None, runs: int = 2, timeout: int = DEFAULT_TIMEOUT,
             interpreters: dict[str, str] | None = None, workdir: Path | None = None, keep: bool = False) -> dict[str, Any]:
    root = root.resolve()
    order = run_order(root, scripts)
    chosen = {"R": shutil.which("Rscript") or "Rscript", "python": shutil.which("python3") or "python3"}
    chosen.update(interpreters or {})
    means = network_means()
    author = _author_paths(chosen)
    base = Path(tempfile.mkdtemp(prefix="reproai-rehearse-", dir=workdir))
    results: list[RunResult] = []
    try:
        for k in range(max(1, runs)):
            results.append(_run_once(root, base / f"run-{k + 1}", order, chosen, author, timeout, means))
            if results[-1].failed:
                break
        diffs = None
        if len(results) >= 2:
            diffs = _compare(base / "run-1/package", base / "run-2/package", results[0], results[1])
    finally:
        if not keep:
            shutil.rmtree(base, ignore_errors=True)
    grade = _grade(results, diffs)
    skipped = sorted(e.path for e in inventory.scan(root) if e.language == "stata")
    return {
        "schema_version": 1,
        "generated_by": GENERATED_BY,
        "root": str(root),
        "workdir": str(base) if keep else None,
        "run_order": order,
        "network_denied_by": means,
        "settings": {"TZ": "UTC", "LC_ALL": _LOCALE, "MPLBACKEND": "Agg", "seeded_from": SEED, "timeout_seconds": timeout},
        "runs": [{"steps": [{**asdict(s), "failed": s.failed} for s in r.steps], "outputs": sorted(r.outputs)} for r in results],
        "differences": diffs,
        "grade": grade,
        "meaning": _MEANING[grade],
        "not_rehearsed": skipped,
        "disclaimer": ("A rehearsal on this machine, with the author's installed libraries. A certification "
                       "service's own closing, with its own copy of the libraries, is the authority."),
    }
