"""Deterministic ado vendoring: make a Stata package self-contained.

This is the engine-applied fix behind three environment rules:

  C2-vendor-ado            a user-written command ships no .ado
  C10-no-runtime-code-fetch  `ssc install` / `net install` fetches code from
                             the internet at run time
  C11-no-external-adopath  `adopath`/`sysdir` loads code from outside the
                             package

The doctrine is vendor-only, because the downstream certification line
(ReproAI Cert) refuses both idioms at its closure check: a certified run may
only read what is in the package, and may not fetch code from the network.
A guarded `ssc install` used to count as a fix here; it now counts as the
defect itself.

The fix is result-preserving by construction: the same commands run with the
same ado code, copied INTO the package (under .certified/lib/) from this machine's own
installed trees, and the lines that reached outside are rewritten to point at
the vendored copy. Nothing about the analysis changes; only where its
dependencies live.

Ground rules:

  * Never touch the author's original folder. apply_fixes() runs on a copy
    the caller made, and every change is returned as a change list.
  * Vendor from the installed trees the do-files themselves name, plus
    Stata's standard PLUS/personal trees, using the stata.trk manifest —
    it records the exact file list per package, including cross-package
    files like l/livreg2.mlib that filename guessing would never find.
    Filename matching is only a fallback, and is labelled as such.
  * When the rules cannot know what to do (an external adopath with no
    ssc lines naming what it provides, a package installed nowhere on this
    machine), say so and stop. Guessing is not preparing.
"""

from __future__ import annotations

import re
from importlib import import_module
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

vendor_paths = import_module("reproai_prep._ado_vendor_paths")

UnsafeVendorPathError = vendor_paths.UnsafeVendorPathError
safe_manifest_file = vendor_paths.safe_manifest_file
safe_manifest_rel = vendor_paths.safe_manifest_rel
safe_vendor_target = vendor_paths.safe_vendor_target

# spec-math sm:audit / constants.json library_root (2026-09-03): vendored
# add-ons live under this path inside the package. The certification line
# treats files under it as group u whatever their extension, never as
# closure targets, and exempt from the read audit; the search path may point
# here and nowhere outside. Both engines name the same string.
VENDOR_DIR = ".certified/lib"
MARK = "[reproai prepare]"
# The account of what Prep changed sits at the package root. `.certified/` holds only what a
# certifier reads (the library root above); IQSS Certify reserves the rest of that folder.
RECORD_NAME = "REPROAI-PREPARATION.txt"

# Shared with rule_engine: these three regexes ARE the detection for
# C10/C11's Stata side, so the scanner and the rules can never disagree.
SSC_INSTALL_RE = re.compile(
    r"^(?P<indent>\s*)(?:capture\s+|cap\s+)?(?:noisily\s+|noi\s+)?(?:quietly\s+|qui\s+)?"
    r"(?:ssc\s+inst(?:all)?|net\s+install)\s+(?P<pkg>[A-Za-z_]\w*)",
    re.IGNORECASE,
)
ADOPATH_RE = re.compile(
    r"^(?P<indent>\s*)(?:(?:capture|cap|quietly|qui|noisily|noi)\s+)*"
    r"(?:adopath\s*\+{1,2}|sysdir\s+set\s+\w+)\s*"
    r"(?P<quote>\"?)(?P<target>[^\"\n]+?)(?P=quote)\s*(?://[^\n]*)?$",
    re.IGNORECASE,
)


def is_external(target: str) -> bool:
    """A path that leaves the package: home, absolute, drive letter, or ..-escape."""
    t = target.strip()
    return (
        t.startswith(("~", "/", "\\"))
        or bool(re.match(r"^[A-Za-z]:[\\/]", t))
        or t.startswith("..")
    )


@dataclass
class Issue:
    kind: str  # "ssc_install" | "external_adopath"
    file: str  # path relative to package root
    line: int  # 1-based
    text: str  # the offending line, stripped
    detail: str  # package name or external path

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "file": self.file, "line": self.line,
                "text": self.text, "detail": self.detail}


def scan_package(root: Path) -> list[Issue]:
    """Static scan of every .do file for the two idioms. No code runs."""
    issues: list[Issue] = []
    for do in sorted(root.rglob("*.do")):
        rel = str(do.relative_to(root))
        try:
            lines = do.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for n, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if stripped.startswith("*") or stripped.startswith("//"):
                continue
            m = SSC_INSTALL_RE.match(raw)
            if m:
                issues.append(Issue("ssc_install", rel, n, stripped, m.group("pkg").lower()))
                continue
            m = ADOPATH_RE.match(raw)
            if m and is_external(m.group("target")):
                issues.append(Issue("external_adopath", rel, n, stripped, m.group("target").strip()))
    return issues


def _parse_trk(trk: Path) -> dict[str, list[str]]:
    """stata.trk -> {package name (lowercase, no .pkg): [relative file paths]}.

    Sections look like:  N ranktest.pkg / D date / U url / d description...
    / f r/ranktest.ado / f l/livreg2.mlib / ... / e
    """
    out: dict[str, list[str]] = {}
    current: str | None = None
    try:
        text = trk.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for raw in text.splitlines():
        if raw.startswith("N "):
            name = raw[2:].strip()
            if name.lower().endswith(".pkg"):
                name = name[:-4]
            current = name.lower()
            out.setdefault(current, [])
        elif raw.startswith("f ") and current is not None:
            out[current].append(raw[2:].strip())
        elif raw.strip() == "e":
            current = None
    return out


def _candidate_roots(issues: list[Issue]) -> list[Path]:
    roots: list[Path] = []
    for issue in issues:
        if issue.kind == "external_adopath":
            p = Path(issue.detail).expanduser()
            if p.is_dir():
                roots.append(p)
    home = Path.home()
    for standard in (home / "ado" / "plus", home / "ado" / "personal"):
        if standard.is_dir():
            roots.append(standard)
    seen: set[Path] = set()
    unique: list[Path] = []
    for r in roots:
        rp = r.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(rp)
    return unique


@dataclass
class Plan:
    vendor: list[dict[str, Any]] = field(default_factory=list)  # {package, root, files, via}
    rewrite: list[Issue] = field(default_factory=list)
    unresolved: list[dict[str, Any]] = field(default_factory=list)  # {issue, why}

    @property
    def fixable(self) -> bool:
        return not self.unresolved and bool(self.vendor or self.rewrite)


def resolve_fixes(issues: list[Issue]) -> Plan:
    """Decide, without changing anything, how each issue would be fixed."""
    plan = Plan()
    roots = _candidate_roots(issues)
    manifests = [(root, _parse_trk(root / "stata.trk")) for root in roots]
    ssc_names = {i.detail for i in issues if i.kind == "ssc_install"}

    for name in sorted(ssc_names):
        located = False
        for root, manifest in manifests:
            files = manifest.get(name)
            if files:
                present = [safe_manifest_rel(f) for f in files if safe_manifest_file(root, f).is_file()]
                if present:
                    plan.vendor.append({"package": name, "root": str(root),
                                        "files": present, "via": "stata.trk"})
                    located = True
                    break
        if not located:
            for root in roots:
                letter_dir = root / name[0]
                matches = sorted(
                    safe_manifest_rel(str(p.relative_to(root)).replace("\\", "/"))
                    for pattern in (f"{name}*.ado", f"{name}*.sthlp",
                                    f"{name}*.hlp", f"{name}*.mlib")
                    for p in letter_dir.glob(pattern)
                    if safe_manifest_file(root, str(p.relative_to(root)).replace("\\", "/")).is_file()
                )
                if matches:
                    plan.vendor.append({"package": name, "root": str(root),
                                        "files": matches, "via": "name match"})
                    located = True
                    break
        if not located:
            why = ("installed copy not found on this machine (searched: "
                   + ", ".join(str(r) for r in roots) + ")")
            plan.unresolved.append(
                {"issue": next(i for i in issues if i.detail == name).as_dict(), "why": why})

    for issue in issues:
        if issue.kind == "external_adopath":
            if ssc_names:
                plan.rewrite.append(issue)
            else:
                plan.unresolved.append({
                    "issue": issue.as_dict(),
                    "why": "no ssc install lines say which commands this directory provides;"
                           " deciding what to vendor needs the author or the host LLM",
                })
        elif issue.kind == "ssc_install":
            plan.rewrite.append(issue)
    return plan


def apply_fixes(package_copy: Path, plan: Plan) -> dict[str, Any]:
    """Vendor files and rewrite lines inside package_copy. Returns the change list.

    The caller is responsible for package_copy being a COPY, never the
    author's original folder. Refuses a partial fix: half-prepared is worse
    than honestly unprepared.
    """
    ado_vendor_apply = import_module("reproai_prep._ado_vendor_apply")

    return ado_vendor_apply.apply_fixes(package_copy, plan)
