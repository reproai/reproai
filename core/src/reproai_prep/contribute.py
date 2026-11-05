"""Engine support for /reproai:contribute.

Two thin, testable primitives the contribute command calls before it hands the user a pre-filled
GitHub issue URL (the user always clicks Submit; reproai never posts):

- `scrub_leaks` — find identifying strings a contribution must never carry (absolute/home paths,
  emails, ORCIDs). Lesson mode redacts-and-proceeds; venue mode blocks (it carries no package data).
- `validate_venue_draft` — mechanically vet a DRAFT venue profile (valid YAML, required keys, a
  filename-safe id, every detector in the known set, a clean dry-run on a synthetic fixture). Fidelity
  (does the profile faithfully transcribe the cited policy) is the maintainer's human job, not this.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

import yaml

from . import inventory, venue_engine

_LEAK_PATTERNS = [
    (re.compile(r'(?:/Users/|/home/|/root/|[A-Za-z]:\\Users\\)[^\s"\'`)]+'), "absolute home path"),
    (re.compile(r'(?<![\w.])~[/\\][^\s"\'`)]+'), "home-relative path"),
    (re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b'), "email address"),
    (re.compile(r'\b\d{4}-\d{4}-\d{4}-\d{3}[\dXx]\b'), "ORCID"),
]


def scrub_leaks(text: str) -> list[dict[str, str]]:
    """Return identifying strings found in `text`. The caller decides what to do with them: lesson
    mode redacts and proceeds; venue mode blocks and refuses (a venue suggestion is about the journal,
    not the user's package)."""
    findings: list[dict[str, str]] = []
    seen: set[str] = set()
    for pat, label in _LEAK_PATTERNS:
        for m in pat.finditer(text):
            tok = m.group(0)
            if tok not in seen:
                seen.add(tok)
                findings.append({"label": label, "match": tok})
    return findings


_REQUIRED_PROFILE_KEYS = ("venue", "profile_version", "checks")
_REQUIRED_CHECK_KEYS = ("check_id", "requirement", "detector")
_VENUE_ID = re.compile(r'[a-z0-9_]+')


def _write_fixture(root: Path) -> Path:
    """A minimal but non-empty package so every detector has something to inspect during the dry-run."""
    (root / "README.md").write_text(
        "# readme\ndata availability\ncomputational requirements\nresults to be replicated\ndata source\n",
        encoding="utf-8")
    (root / "master.R").write_text("source('analysis.R')\n", encoding="utf-8")
    (root / "analysis.R").write_text("x <- 1\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (root / "data").mkdir()
    (root / "data" / "d.csv").write_text("a\n1\n", encoding="utf-8")
    return root


def validate_venue_draft(draft_text: str) -> dict[str, Any]:
    """Mechanically vet a DRAFT venue profile. Returns {ok, errors, dry_run, venue_id}. This proves the
    profile is well-formed and runnable; it does NOT judge whether the checks faithfully transcribe the
    journal's policy — that is the maintainer's human review against the cited quotes."""
    errors: list[str] = []
    try:
        profile = yaml.safe_load(draft_text)
    except yaml.YAMLError as exc:
        return {"ok": False, "errors": [f"YAML did not parse: {exc}"], "dry_run": None, "venue_id": None}
    if not isinstance(profile, dict):
        return {"ok": False, "errors": ["top level is not a YAML mapping"], "dry_run": None, "venue_id": None}

    for k in _REQUIRED_PROFILE_KEYS:
        if k not in profile:
            errors.append(f"missing top-level key: {k}")
    vid = str(profile.get("venue", ""))
    if not _VENUE_ID.fullmatch(vid):
        errors.append(f"venue id '{vid}' must be lowercase letters, digits, and underscores only")

    checks = profile.get("checks") or []
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty list")
        checks = []
    for i, c in enumerate(checks, start=1):
        if not isinstance(c, dict):
            errors.append(f"check #{i} is not a mapping")
            continue
        for k in _REQUIRED_CHECK_KEYS:
            if k not in c:
                errors.append(f"check #{i} ({c.get('check_id', '?')}) missing '{k}'")
        det = c.get("detector")
        if det is not None and det not in venue_engine.KNOWN_DETECTORS:
            errors.append(f"check '{c.get('check_id', '?')}' names an unknown detector '{det}' "
                          "(use a supported detector, or 'unbuilt_detector' for a not-yet-built one)")
        if det == "unbuilt_detector" and not c.get("needs_detector"):
            errors.append(f"check '{c.get('check_id', '?')}' is unbuilt_detector but names no "
                          "'needs_detector:' target")

    dry_run = None
    if not errors:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = _write_fixture(Path(tmp))
                meta, ran = venue_engine.run_profile(root, inventory.scan(root), profile)
                dry_run = {"venue": meta["venue"], "checks": len(ran)}
        except Exception as exc:  # a draft profile must never crash the engine
            errors.append(f"dry-run against a fixture failed: {exc}")

    return {"ok": not errors, "errors": errors, "dry_run": dry_run, "venue_id": vid or None}
