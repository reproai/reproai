from __future__ import annotations

from typing import Any

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .inventory import FileEntry, code_entries, _pdftotext
from .dependency_graph import Edge, entry_points as _entry_points, build as _build_edges
from .rule_engine import abs_path_hits as _abs_path_hits

_VENUE_DIR = Path(__file__).parent / "venues"

_README_SECTION_HINTS = [
    "data availability",
    "computational requirement",
    "instructions",
    "data source",
]
# The absolute-path scan is rule_engine.abs_path_hits (imported above) — venue_engine keeps NO
# regex of its own, so the venue verdict and the B4 advisory cannot drift apart (issue #42).

# the closed set of venue-check detectors the engine knows how to run; the contribute-time
# validator rejects a profile that names any detector outside this set (run() itself stays lenient).
KNOWN_DETECTORS = frozenset({
    "readme_pdf_at_root", "readme_at_root", "readme_has_sections", "has_master_script",
    "env_declared", "no_absolute_paths", "rederive_from_raw", "file_count_limit",
    "license_at_root", "data_availability_statement", "data_citation", "seeded_rng",
    "manual_author_action", "unbuilt_detector",
})


@dataclass
class Check:
    check_id: str
    requirement: str
    status: str
    detail: str
    evidence: list[str]
    source: str
    # Optional guidance, never a verdict — the engine still owns `status`. author_action/how/self_check
    # describe an off-package action the static engine cannot verify; needs_detector names the detector a
    # not_implemented check awaits. (Anti-sycophancy: these inform the author, they do not change a status.)
    author_action: str = ""
    how: str = ""
    self_check: str = ""
    needs_detector: str = ""
    detector: str = ""  # the detector that produced this check; used by adversarial_reviewer, not reported


def load_profile(venue: str) -> dict[str, Any]:
    path = _VENUE_DIR / f"{venue}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No venue profile for '{venue}' at {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _root_readme(root: Path) -> Path | None:
    # Case-insensitive: JASA's own template ships "ReadMe.pdf", which a case-sensitive
    # filesystem (Linux CI, where reproducibility checks run) would otherwise miss.
    try:
        for child in root.iterdir():
            if child.is_file() and child.name.lower() == "readme.pdf":
                return child
    except OSError:
        return None
    return None


def _license_at_root(root: Path) -> str | None:
    names = {"license", "license.md", "license.txt", "licence", "licence.md", "licence.txt", "copying"}
    try:
        for child in root.iterdir():
            if child.is_file() and child.name.lower() in names:
                return child.name
    except OSError:
        return None
    return None


# _pdftotext moved to inventory (shared I/O helper, used by venue_engine and rule_engine); imported above.


def _has_master(entries: list[FileEntry], edges: list[Edge]) -> list[dict[str, Any]]:
    """Structural master detection (issue #23): an entry point is a script that runs other scripts and
    is run by none (or, with no include edges at all, one whose name marks it a runner). Delegates to
    dependency_graph.entry_points so this venue check and the architecture report cannot disagree about
    the same file, and so a non-conventionally-named run-all (e.g. meta.R) is recognised. Returns the
    entry-point records (empty list if none)."""
    return _entry_points(entries, edges)


def _file_count(entries: list[FileEntry]) -> int:
    return len(entries)


def _abs_path_files(root: Path, entries: list[FileEntry]) -> list[str]:
    """Files with absolute-path literals, from THE SAME comment-aware scan that produces the B4
    advisory (rule_engine.abs_path_hits). One source of truth (issue #42): the venue verdict and the
    B4 count can no longer contradict each other — previously this check re-scanned raw text with its
    own regex, so a comment-only path (e.g. reproai's own `# was: setwd("/Users/...")` fix output)
    read as venue-FAIL while the advisory count was zero."""
    return sorted({path for path, _line, _snippet in _abs_path_hits(root, entries)})


def _env_declared(root: Path, entries: list[FileEntry]) -> bool:
    readme = _root_readme(root)
    if readme is None:
        for e in entries:
            if Path(e.path).name.lower() in {"readme.md", "readme.txt"}:
                return True
        return False
    return True


_DAS_SIGNALS = (
    "data availability",
    "all data publicly available",
    "some data restricted",
    "no data publicly available",
    "data are publicly available",
    "data is publicly available",
    "data availability statement",
)
_DOI_RE = re.compile(r'10\.\d{4,9}/\S+')
_PID_URL_RE = re.compile(
    r'(?:doi\.org/|hdl\.handle\.net/|dataverse\.|zenodo\.org/|openicpsr\.org/|'
    r'icpsr\.umich\.edu/|osf\.io/)',
    re.IGNORECASE,
)
# R parallel-loop shapes that draw random numbers; flagged only when no reproducible-RNG signal is near.
_PARALLEL_RE = re.compile(r'%dopar%|\bforeach\s*\(|\bmclapply\s*\(|\bparLapply\s*\(|\bparSapply\s*\(')
_RNG_SIGNAL_RE = re.compile(
    r'registerDoRNG|%dorng%|clusterSetRNGStream|set\.seed|RNGkind\s*\(\s*["\']L\'Ecuyer'
)


def _readme_texts(root: Path, entries: list[FileEntry]) -> list[tuple[str, str]]:
    """Return (filename, lowercased text) for each root README — plain text directly, PDF via pdftotext."""
    out: list[tuple[str, str]] = []
    for e in entries:
        name = Path(e.path).name
        if "/" in e.path or "\\" in e.path:
            continue
        if name.lower() in {"readme.md", "readme.txt"}:
            try:
                out.append((name, (root / e.path).read_text(encoding="utf-8", errors="replace").lower()))
            except OSError:
                continue
    pdf = _root_readme(root)
    if pdf is not None:
        extracted = _pdftotext(pdf)
        if extracted is not None:
            out.append((pdf.name, extracted.lower()))
    return out


def _data_availability_statement(root: Path, entries: list[FileEntry]) -> tuple[str, str, list[str]]:
    readmes = _readme_texts(root, entries)
    if not readmes:
        return "fail", "No README at the replication dataset root to carry a Data Availability Statement.", []
    for name, text in readmes:
        if any(sig in text for sig in _DAS_SIGNALS) or ("availability" in text and "data" in text):
            return "pass", f"Data Availability Statement signal found in {name}.", [name]
    names = [n for n, _ in readmes]
    return ("needs_author_action",
            "README present but no Data Availability Statement detected; add one summarizing data "
            "availability (all public / some restricted / none public) with per-dataset source and access.",
            names)


def _data_citation(root: Path, entries: list[FileEntry]) -> tuple[str, str, list[str]]:
    for name, text in _readme_texts(root, entries):
        if _DOI_RE.search(text) or _PID_URL_RE.search(text):
            return "pass", f"Persistent identifier (DOI/handle/repository URL) found in {name}.", [name]
    for e in entries:
        if e.language not in {"stata", "r", "python", "doc"}:
            continue
        try:
            text = (root / e.path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _DOI_RE.search(text) or _PID_URL_RE.search(text):
            return "pass", f"Persistent identifier (DOI/handle/repository URL) found in {e.path}.", [e.path]
    return ("needs_author_action",
            "No persistent identifier found; cite each dataset with a DOI or handle (a Dataverse/Zenodo/"
            "ICPSR link) so a replicator can retrieve the exact data.", [])


def _seeded_rng(root: Path, entries: list[FileEntry]) -> tuple[str, str, list[str]]:
    for e in entries:
        if e.language != "r":
            continue
        try:
            text = (root / e.path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _PARALLEL_RE.search(text) and not _RNG_SIGNAL_RE.search(text):
            return ("needs_author_action",
                    "Parallel loop without a reproducible-RNG signal (registerDoRNG/%dorng%/"
                    "clusterSetRNGStream/set.seed); make parallel RNG reproducible (doRNG) and regenerate "
                    f"the affected tables. Code-shape scan only, no execution — see {e.path}.", [e.path])
    return "pass", "No non-reproducible parallel RNG pattern detected.", []


def run(root: Path, entries: list[FileEntry], venue: str, edges: list[Edge] | None = None) -> tuple[dict[str, Any], list[Check]]:
    return run_profile(root, entries, load_profile(venue), edges)


# Code-presuming detectors: each verifies a property of executable code. On a deposit with no code
# (a qualitative/document-only corpus) they can never be satisfied, so emitting them as author actions
# is noise that dilutes the checks that DO apply (README, data citation, license). Issue #24.
_CODE_PRESUMING_DETECTORS = frozenset({
    "has_master_script", "env_declared", "rederive_from_raw", "no_absolute_paths", "seeded_rng",
})


def run_profile(root: Path, entries: list[FileEntry], profile: dict[str, Any], edges: list[Edge] | None = None) -> tuple[dict[str, Any], list[Check]]:
    """Run a profile that is already loaded — lets the contribute validator dry-run a DRAFT profile
    that is not installed in venues/ yet."""
    root = root.resolve()
    if edges is None:
        edges = _build_edges(root, entries)
    # SAS counts as code HERE even though inventory.code_entries excludes it (tier 1, issue #32):
    # a pure-SAS deposit is a code package, and no_absolute_paths CAN assess it — reporting
    # not_applicable would be the same phantom-pass the issue complains about, one level up.
    has_code = bool(code_entries(entries)) or any(e.language == "sas" for e in entries)
    checks: list[Check] = []

    def add(spec: dict[str, Any], status: str, detail: str, evidence: list[str]) -> None:
        checks.append(
            Check(
                check_id=spec["check_id"],
                requirement=spec["requirement"],
                status=status,
                detail=detail,
                evidence=evidence,
                source=spec.get("source", ""),
                author_action=spec.get("author_action", "") or "",
                how=spec.get("how", "") or "",
                self_check=spec.get("self_check", "") or "",
                needs_detector=spec.get("needs_detector", "") or "",
                detector=spec.get("detector", "") or "",
            )
        )

    for spec in profile.get("checks", []):
        detector = spec.get("detector")
        if detector in _CODE_PRESUMING_DETECTORS and not has_code:
            add(spec, "not_applicable",
                "Deposit contains no executable code; this code-level check does not apply.", [])
            continue
        if detector == "readme_pdf_at_root":
            readme = _root_readme(root)
            add(spec, "pass" if readme else "fail",
                "README.pdf at root" if readme else "No README.pdf in the uppermost directory.",
                [readme.name] if readme else [])
        elif detector == "readme_at_root":
            # softer than readme_pdf_at_root: any README at root passes; PDF is recommended, not required
            pdf = _root_readme(root)
            md = next((e.path for e in entries if Path(e.path).name.lower() in {"readme.md", "readme.txt"}), None)
            if pdf:
                add(spec, "pass", f"README present at root ({pdf.name}).", [pdf.name])
            elif md:
                add(spec, "needs_author_action", "README present, but the JASA template ships ReadMe.pdf; export a PDF copy.", [md])
            else:
                add(spec, "fail", "No README at the replication dataset root.", [])
        elif detector == "readme_has_sections":
            # a profile may override the section hints to match its own README template
            hints = profile.get("readme_sections") or _README_SECTION_HINTS
            readme = _root_readme(root)
            md = next((e.path for e in entries if Path(e.path).name.lower() in {"readme.md", "readme.txt"}), None)
            # prefer a plain-text README; otherwise read the PDF's text so its sections count too
            text = None
            src = None
            if md is not None:
                text = (root / md).read_text(encoding="utf-8", errors="replace").lower()
                src = md
            elif readme is not None:
                extracted = _pdftotext(readme)
                if extracted is not None:
                    text = extracted.lower()
                    src = readme.name
            if text is not None:
                missing = [h for h in hints if h not in text]
                add(spec, "pass" if not missing else "needs_author_action",
                    "All key sections present." if not missing else f"Missing sections: {', '.join(missing)}.",
                    [src])
            elif readme is not None:
                add(spec, "needs_author_action",
                    "README.pdf present but its text could not be extracted (install poppler's pdftotext to auto-check sections).",
                    [readme.name])
            else:
                add(spec, "fail", "No README found to check sections.", [])
        elif detector == "has_master_script":
            eps = _has_master(entries, edges)
            if eps:
                paths = [p["path"] for p in eps]
                add(spec, "pass", f"Master/entry script detected: {', '.join(paths)}.", paths)
            else:
                add(spec, "needs_author_action",
                    "No master/run-all script found (no script runs the others).", [])
        elif detector == "env_declared":
            ok = _env_declared(root, entries)
            add(spec, "pass" if ok else "needs_author_action",
                "README present to carry environment statement." if ok else "No README to declare software/versions.", [])
        elif detector == "no_absolute_paths":
            bad_files = _abs_path_files(root, entries)
            add(spec, "fail" if bad_files else "pass",
                "Absolute paths present (exceeds single-path-edit tolerance)." if bad_files
                else "No absolute paths detected.", bad_files)
        elif detector == "rederive_from_raw":
            add(spec, "needs_author_action", "Static check cannot confirm raw-to-analysis re-derivation; author must confirm.", [])
        elif detector == "file_count_limit":
            n = _file_count(entries)
            limit = profile.get("deposit", {}).get("max_files")
            if limit is None:
                add(spec, "needs_author_action", f"{n} files; this venue sets no explicit file-count limit but keep the deposit navigable.", [])
            else:
                add(spec, "pass" if n <= limit else "needs_author_action",
                    f"{n} files (limit {limit}; zip if exceeded).", [])
        elif detector == "license_at_root":
            lic = _license_at_root(root)
            add(spec, "pass" if lic else "fail",
                f"License file present ({lic})." if lic else "No LICENSE file at the replication dataset root.",
                [lic] if lic else [])
        elif detector == "data_availability_statement":
            status, detail, evidence = _data_availability_statement(root, entries)
            add(spec, status, detail, evidence)
        elif detector == "data_citation":
            status, detail, evidence = _data_citation(root, entries)
            add(spec, status, detail, evidence)
        elif detector == "seeded_rng":
            status, detail, evidence = _seeded_rng(root, entries)
            add(spec, status, detail, evidence)
        elif detector == "manual_author_action":
            # carry the specific requirement (or its author_action) as detail, not a generic stub.
            detail = spec.get("author_action") or spec["requirement"]
            add(spec, "needs_author_action", detail, [])
        elif detector == "unbuilt_detector":
            # an honest, CI-guarded placeholder: a statically-checkable requirement whose detector has
            # not been built yet. not_implemented (not not_applicable) + named, so it is never mistaken
            # for a permanent manual stub and is found by test_no_unbuilt_detectors_in_shipped_profiles.
            target = spec.get("needs_detector", "?")
            add(spec, "not_implemented",
                f"Check '{spec['check_id']}' awaits a new detector '{target}'; reproai cannot verify it yet.", [])
        else:
            add(spec, "not_applicable", f"Unknown detector '{detector}'.", [])

    summary = {
        "total": len(checks),
        "pass": sum(1 for c in checks if c.status == "pass"),
        "fail": sum(1 for c in checks if c.status == "fail"),
        "needs_author_action": sum(1 for c in checks if c.status == "needs_author_action"),
        "not_implemented": sum(1 for c in checks if c.status == "not_implemented"),
        "not_applicable": sum(1 for c in checks if c.status == "not_applicable"),
    }
    meta = {
        "venue": profile["venue"],
        "profile_version": profile["profile_version"],
        "standard": profile.get("standard", ""),
        "summary": summary,
    }
    return meta, checks
