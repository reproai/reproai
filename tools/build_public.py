"""Build the PUBLIC, anonymized rule set from the internal source of truth. Strips per-paper provenance (source_lessons) so the published rules never name a specific paper or say what was wrong with it. Rule bodies (rule/detection/priority/kind) are preserved verbatim."""
from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

LINE1 = Path(__file__).resolve().parents[1]
CORE = LINE1 / "core"
INTERNAL_RULES = CORE / "src/reproai_prep/rules/author_rules.yaml"
INTERNAL_STYLE = CORE / "src/reproai_prep/style_guide.md"
PUBLIC_DIR = LINE1 / "public"
DIST_DIR = LINE1 / "dist"

# Internal-only files that must NEVER appear in a published bundle (they name specific papers).
_INTERNAL_ONLY = {"CHANGELOG.md", "VALIDATION.md"}

# PRODUCT BOUNDARY. The published bundle is ReproAI Prep — the static, no-execution line.
# The Cert line (close/certify/deposit/submit/verify-cert) is a separate product in a separate
# repository and must never be published from here. This used to be true only by accident: the
# repo held Prep alone, so copying the whole tree happened to be safe. It is not safe now.
_CERT_MODULES = {
    "certify.py", "closure.py", "witness.py", "issuer_service.py", "package_verify.py",
    "protocol.py", "chainlog.py", "ledger.py", "deposit.py", "submit.py",
    "submission_verify.py", "badge.py", "freshness_bls.py", "instrument.py",
    "regout.py", "orchestrate.py",
}
_CERT_COMMANDS = {
    "certify.md", "close.md", "deposit.md", "publish.md", "submit.md", "verify-cert.md",
}
_CERT_EXCLUDED = _CERT_MODULES | _CERT_COMMANDS
# A certification target's detectors share a name with a Cert module (targets/certify.py reads
# what IQSS Certify will refuse; it certifies nothing) and are Prep's own: kept, by folder.
_TARGETS_DIR = "targets"


def _is_cert_file(path: Path) -> bool:
    return path.name in _CERT_EXCLUDED and path.parent.name != _TARGETS_DIR

# The published bundle is installed from the org repo, not from a maintainer's personal fork.
# build_public.py used to copy these strings verbatim, so the published plugin told users to
# install from, and file issues against, a PRIVATE repository.
_URL_REWRITES = (
    ("github.com/reproai/reproai", "github.com/reproai/reproai"),
    ("raw.githubusercontent.com/reproai/reproai", "raw.githubusercontent.com/reproai/reproai"),
    ("reproai/reproai", "reproai/reproai"),
    ("github.com/reproai/reproai", "github.com/reproai/reproai"),
    ("raw.githubusercontent.com/reproai/reproai", "raw.githubusercontent.com/reproai/reproai"),
    ("reproai/reproai", "reproai/reproai"),
)
_REWRITE_SUFFIXES = {".md", ".json", ".py", ".yaml", ".yml", ".txt", ".html"}
# The development repositories: a public file that names one points users at a repo they cannot read.
_PRIVATE_REPOS = ("reproai/reproai", "reproai/reproai")

_PUBLIC_RULE_FIELDS = [
    "id", "category", "kind", "priority", "rule", "detection", "languages",
    "why_downstream", "target_form", "lossless_note", "propose_only", "output_changing",
]

# Guard: refuse to ship if a paper-name pattern survives anywhere in the public output.
_PAPER_NAME = re.compile(r"\b[A-Z][A-Za-z]+\d{4}[a-z]?\b|\b[A-Z]{2,}\d{4}_[a-z0-9_]+\b")
_ALLOWED_TOKENS = {"CC0", "CC", "BY", "BSD", "DCAS", "SSDE", "TIER", "JETS"}


def _scrub_rules(internal: dict[str, Any]) -> dict[str, Any]:
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

    # build/ and dist/ are local build output: a stale copy of the internal rules lives there
    common = shutil.ignore_patterns(
        "__pycache__", "*.pyc", "*.egg-info", "tests", ".gitignore", ".pytest_cache", "build", "dist",
        *_INTERNAL_ONLY,
    )

    def ignore(directory: str, names: list[str]) -> set[str]:
        return set(common(directory, names)) | {n for n in names if _is_cert_file(Path(directory) / n)}
    shutil.copytree(LINE1 / "claude-plugin", DIST_DIR / "claude-plugin", ignore=ignore)
    shutil.copytree(CORE, DIST_DIR / "claude-plugin/core", ignore=ignore)
    (DIST_DIR / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    shutil.copy2(LINE1 / "marketplace.json", DIST_DIR / ".claude-plugin/marketplace.json")

    (DIST_DIR / "claude-plugin/core/src/reproai_prep/rules/author_rules.yaml").write_text(public_rules_yaml, encoding="utf-8")
    (DIST_DIR / "README.md").write_text(public_readme, encoding="utf-8")
    for name in ("LICENSE", "CITATION.cff"):
        if (LINE1 / name).exists():
            shutil.copy2(LINE1 / name, DIST_DIR / name)

    _rewrite_urls()

    for label, problems in (
        ("paper names leaked into dist/", _find_paper_names()),
        ("Cert-line files leaked into dist/", _find_cert_files()),
        ("dist/ points at the private development repo", _find_private_urls()),
        ("dist/ imports a module it does not ship", _find_dangling_imports()),
    ):
        if problems:
            shutil.rmtree(DIST_DIR)
            raise RuntimeError(f"{label} — aborted:\n  " + "\n  ".join(problems[:20]))


def _rewrite_urls(root: Path = DIST_DIR) -> None:
    for f in root.rglob("*"):
        if not f.is_file() or f.suffix not in _REWRITE_SUFFIXES:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        new = text
        for old, repl in _URL_REWRITES:
            new = new.replace(old, repl)
        if new != text:
            f.write_text(new, encoding="utf-8")


_SCANNED_SUFFIXES = {".yaml", ".md", ".json", ".py", ".do", ".R"}


def _find_paper_names(root: Path = DIST_DIR, suffixes: set[str] = _SCANNED_SUFFIXES) -> list[str]:
    out = []
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in suffixes:
            for tok in _has_paper_name(f.read_text(encoding="utf-8", errors="replace")):
                out.append(f"{f.relative_to(root)}: {tok}")
    return out


def _find_cert_files(root: Path = DIST_DIR) -> list[str]:
    return [
        str(f.relative_to(root))
        for f in root.rglob("*")
        if f.is_file() and _is_cert_file(f)
    ]


def _find_private_urls(root: Path = DIST_DIR) -> list[str]:
    out = []
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in _REWRITE_SUFFIXES:
            text = f.read_text(encoding="utf-8", errors="replace")
            if any(repo in text for repo in _PRIVATE_REPOS):
                out.append(str(f.relative_to(root)))
    return out


def _find_dangling_imports() -> list[str]:
    """Excluding a Cert module is only safe if nothing shipped still imports it.

    `cli.py` imports the Cert modules at module scope, so dropping them without
    splitting the CLI produces a bundle that installs cleanly and then raises
    ImportError on the user's first command.
    """
    return _dangling_imports(DIST_DIR / "claude-plugin/core/src/reproai_prep")


def _dangling_imports(pkg: Path) -> list[str]:
    if not pkg.is_dir():
        return []
    shipped = {p.stem for p in pkg.glob("*.py")}
    out = []
    for p in sorted(pkg.glob("*.py")):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            out.append(f"{p.name}: unparseable ({exc})")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.level != 1:
                continue
            names = {node.module.split(".")[0]} if node.module else {a.name for a in node.names}
            for n in sorted(names - shipped):
                if (CORE / "src/reproai_prep" / f"{n}.py").is_file():
                    out.append(f"{p.name} imports .{n}, which the bundle excludes")
    return out


# The public repository is a whole-tree copy of the tracked files minus what is internal: tests
# (their fixtures name papers), the internal-only files, the Cert line, and docs/ apart from the
# design notes (docs/ also holds a journal's own submission material and test-bench measurements).
_MIRROR_DOCS = ("docs/design/",)
# the development repository's own CI: its tests are not published and the public branch is main
_MIRROR_SKIP = (".github/workflows/",)
# the mirror carries the site and the plugin text, so more kinds of file are read for paper names
_MIRROR_SCANNED = _SCANNED_SUFFIXES | {".txt", ".js", ".html", ".toml", ".cff", ".sh", ".yml"}


def _mirror_files() -> list[str]:
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=LINE1, capture_output=True, check=True).stdout
    keep = []
    for rel in listed.decode("utf-8").split("\0"):
        if not rel:
            continue
        parts = rel.split("/")
        if "tests" in parts[:-1] or parts[-1] in _INTERNAL_ONLY or _is_cert_file(Path(rel)):
            continue
        if (parts[0] == "docs" and not rel.startswith(_MIRROR_DOCS)) or rel.startswith(_MIRROR_SKIP):
            continue
        keep.append(rel)
    return keep


def mirror(out: Path) -> int:
    """Write the public repository's tree to `out`: the tracked files it may hold, with the scrubbed
    rule set swapped in and the development repository's addresses rewritten. Refuses (and removes
    `out`) when a paper name, a Cert-line file, a private address or a dangling import survives."""
    internal = yaml.safe_load(INTERNAL_RULES.read_text(encoding="utf-8"))
    public_yaml = yaml.safe_dump(_scrub_rules(internal), sort_keys=False, allow_unicode=True, width=120)
    if out.exists():
        shutil.rmtree(out)
    files = _mirror_files()
    for rel in files:
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LINE1 / rel, dst)
    (out / "core/src/reproai_prep/rules/author_rules.yaml").write_text(public_yaml, encoding="utf-8")
    _rewrite_urls(out)
    problems = [
        (label, found) for label, found in (
            ("paper names", _find_paper_names(out, _MIRROR_SCANNED)),
            ("Cert-line files", _find_cert_files(out)),
            ("addresses of the private development repo", _find_private_urls(out)),
            ("imports of modules the mirror does not hold", _dangling_imports(out / "core/src/reproai_prep")),
        ) if found
    ]
    if problems:
        shutil.rmtree(out)
        for label, found in problems:
            print(f"REFUSING to mirror: {label}:", file=sys.stderr)
            for x in found[:20]:
                print(f"  {x}", file=sys.stderr)
        return 2
    print(f"Mirrored {len(files)} files to {out}: scrubbed rules, no paper names, no Cert line, no private addresses.")
    return 0


PUBLIC_REPO = "https://github.com/reproai/reproai.git"



def audit_published() -> int:
    """Run the publish guards against what is ACTUALLY public, not against dist/.

    dist/ and the public repo are different shapes — dist/ is the plugin bundle,
    the public repo is a whole-tree copy — so asserting they are equal would fail
    for the wrong reason. What must hold either way is that nothing public names a
    paper, ships the Cert line, or points at the private development repo.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "public"
        r = subprocess.run(["git", "clone", "--depth", "1", "-q", PUBLIC_REPO, str(root)],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            print(f"cannot clone {PUBLIC_REPO}:\n{r.stderr.strip()}", file=sys.stderr)
            return 2

        findings: list[str] = []
        for f in sorted(root.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(root).as_posix()
            if rel.startswith(".git/") or "node_modules/" in rel:
                continue
            if _is_cert_file(f):
                findings.append(f"Cert-line file published: {rel}")
            if f.suffix in _REWRITE_SUFFIXES and any(
                repo in f.read_text(encoding="utf-8", errors="replace") for repo in _PRIVATE_REPOS
            ):
                findings.append(f"points at the private repo: {rel}")
            if f.suffix in {".yaml", ".md", ".json", ".py", ".do", ".R"}:
                for tok in _has_paper_name(f.read_text(encoding="utf-8", errors="replace")):
                    findings.append(f"paper name published: {rel}: {tok}")

        if findings:
            print(f"{PUBLIC_REPO} is not clean:", file=sys.stderr)
            for x in findings[:40]:
                print(f"  {x}", file=sys.stderr)
            if len(findings) > 40:
                print(f"  … and {len(findings) - 40} more", file=sys.stderr)
            return 1
        print(f"{PUBLIC_REPO} is clean: no paper names, no Cert line, no private URLs")
        return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the anonymized public rule set from the internal source.")
    ap.add_argument("--check", action="store_true", help="Only verify no paper names would leak; write nothing.")
    ap.add_argument("--audit-published", action="store_true",
                    help="Clone the live public repo and run the publish guards against it. Writes nothing.")
    ap.add_argument("--mirror", type=Path, metavar="DIR",
                    help="Write the public repository's tree (a whole-tree copy, scrubbed) to DIR.")
    args = ap.parse_args(argv)
    if args.audit_published:
        return audit_published()
    if args.mirror:
        return mirror(args.mirror.resolve())
    return build(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
