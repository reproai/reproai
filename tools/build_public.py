"""Build the PUBLIC, anonymized rule set from the internal source of truth. Strips per-paper provenance (source_lessons) so the published rules never name a specific paper or say what was wrong with it. Rule bodies (rule/detection/priority/kind) are preserved verbatim."""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import yaml

LINE1 = Path(__file__).resolve().parents[1]
CORE = LINE1 / "core"
INTERNAL_RULES = CORE / "src/line1_core/rules/author_rules.yaml"
INTERNAL_STYLE = CORE / "src/line1_core/style_guide.md"
PUBLIC_DIR = LINE1 / "public"
DIST_DIR = LINE1 / "dist"

# Internal-only files that must NEVER appear in a published bundle (they name specific papers).
_INTERNAL_ONLY = {"CHANGELOG.md", "VALIDATION.md"}

_PUBLIC_RULE_FIELDS = [
    "id", "category", "kind", "priority", "rule", "detection", "languages",
    "why_downstream", "target_form", "lossless_note", "propose_only", "output_changing",
]

# Guard: refuse to ship if a paper-name pattern survives anywhere in the public output.
_PAPER_NAME = re.compile(r"\b[A-Z][A-Za-z]+\d{4}[a-z]?\b|\b[A-Z]{2,}\d{4}_[a-z0-9_]+\b")
_ALLOWED_TOKENS = {"CC0", "CC", "BY", "BSD", "DCAS", "SSDE", "TIER", "JETS"}


def _scrub_rules(internal: dict) -> dict:
    public_rules = []
    for r in internal["rules"]:
        public_rules.append({k: r[k] for k in _PUBLIC_RULE_FIELDS if k in r})
    return {
        "schema_version": internal["schema_version"],
        "rules_version": internal["rules_version"],
        "fields": "id | category | kind | priority(P0..P4) | rule | detection | languages | why_downstream | target_form | lossless_note | propose_only | output_changing",
        "rules": public_rules,
    }


def _has_paper_name(text: str) -> list[str]:
    hits = []
    for m in _PAPER_NAME.finditer(text):
        tok = m.group(0)
        if tok in _ALLOWED_TOKENS:
            continue
        hits.append(tok)
    return hits


_PUBLIC_README = """# ReproAI — replication-package pre-diagnose (rule set)

ReproAI is a static, no-execution helper that audits a replication package and advises how to make it
cleaner and more reproducible **before** submission. It never runs your code and never judges the
correctness of your results — it points out organization, packaging, and writing-style issues that
commonly make a downstream reproducibility check harder than it needs to be.

Findings are graded **P0–P4** by how much they tend to cost a downstream reproducibility run
(P0 = blocks it; P4 = polish), and tagged **defect** (would cost the pipeline) vs **normalization**
(a more standard way to write it). Auto-safe, semantics-preserving fixes can be applied to a copy;
everything else is propose-only.

These rules distill recurring, **author-preventable** patterns observed across a large body of
replication work. They are generic guidance — no rule names, references, or describes any specific
paper.

- `author_rules.yaml` — the rule set (rules_version {ver}).
- `style_guide.md` — the normalized coding-style reference behind the normalization rules.
"""


def build(check_only: bool) -> int:
    internal = yaml.safe_load(INTERNAL_RULES.read_text(encoding="utf-8"))
    public = _scrub_rules(internal)
    public_yaml = yaml.safe_dump(public, sort_keys=False, allow_unicode=True, width=120)
    style = INTERNAL_STYLE.read_text(encoding="utf-8")
    readme = _PUBLIC_README.replace("{ver}", str(internal["rules_version"]))

    leaks: dict[str, list[str]] = {}
    for name, text in (("author_rules.yaml", public_yaml), ("style_guide.md", style), ("README.md", readme)):
        hits = _has_paper_name(text)
        if hits:
            leaks[name] = sorted(set(hits))

    if leaks:
        print("REFUSING to build public: paper-name-like tokens found in public output:")
        for name, hits in leaks.items():
            print(f"  {name}: {hits}")
        print("Fix the internal source (move provenance to source_lessons only) and retry.")
        return 2

    if check_only:
        print(f"OK — public build is clean ({len(public['rules'])} rules, no paper names).")
        return 0

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    (PUBLIC_DIR / "author_rules.yaml").write_text(public_yaml, encoding="utf-8")
    (PUBLIC_DIR / "style_guide.md").write_text(style, encoding="utf-8")
    (PUBLIC_DIR / "README.md").write_text(readme, encoding="utf-8")

    _assemble_dist(public_yaml, readme)

    print(f"Built public/ + dist/ — {len(public['rules'])} rules, scrubbed of provenance, no paper names.")
    print("  dist/ is the publishable bundle (scrubbed rules swapped into the engine; internal files removed).")
    print("  Publish dist/ to the marketplace git repo.")
    return 0


def _assemble_dist(public_rules_yaml: str, public_readme: str) -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    ignore = shutil.ignore_patterns(
        "__pycache__", "*.pyc", "*.egg-info", "tests", ".gitignore", ".pytest_cache", *_INTERNAL_ONLY,
    )
    shutil.copytree(LINE1 / "claude-plugin", DIST_DIR / "claude-plugin", ignore=ignore)
    shutil.copytree(CORE, DIST_DIR / "claude-plugin/core", ignore=ignore)
    (DIST_DIR / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    shutil.copy2(LINE1 / "marketplace.json", DIST_DIR / ".claude-plugin/marketplace.json")

    (DIST_DIR / "claude-plugin/core/src/line1_core/rules/author_rules.yaml").write_text(public_rules_yaml, encoding="utf-8")
    (DIST_DIR / "README.md").write_text(public_readme, encoding="utf-8")
    license_src = LINE1 / "LICENSE"
    if license_src.exists():
        shutil.copy2(license_src, DIST_DIR / "LICENSE")

    leaks: list[str] = []
    for f in DIST_DIR.rglob("*"):
        if f.is_file() and f.suffix in {".yaml", ".md", ".json", ".py", ".do", ".R"}:
            for tok in _has_paper_name(f.read_text(encoding="utf-8", errors="replace")):
                leaks.append(f"{f.relative_to(DIST_DIR)}: {tok}")
    if leaks:
        shutil.rmtree(DIST_DIR)
        raise RuntimeError("paper names leaked into dist/ — aborted:\n  " + "\n  ".join(leaks[:20]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the anonymized public rule set from the internal source.")
    ap.add_argument("--check", action="store_true", help="Only verify no paper names would leak; write nothing.")
    args = ap.parse_args(argv)
    return build(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
