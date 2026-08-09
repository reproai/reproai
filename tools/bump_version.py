"""Bump the plugin version in lockstep across the Claude + Codex plugin manifests, BOTH marketplace.json copies (root + .claude-plugin/ — the latter is the one Claude Code's `/plugin update` actually reads), pyproject.toml, and __init__.py after a knowledge update, so a marketplace `/plugin update` ships the new rules."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_JSON = ROOT / "claude-plugin/.claude-plugin/plugin.json"
CODEX_PLUGIN_JSON = ROOT / "codex-plugin/.codex-plugin/plugin.json"
# TWO marketplace manifests exist: the root copy and .claude-plugin/marketplace.json. The
# .claude-plugin/ one is what Claude Code's marketplace loader reads — it went stale at 0.4.7 while
# the root copy moved (users on /plugin update never saw 0.4.8–0.4.10), so both bump together now.
MARKETPLACES = (ROOT / "marketplace.json", ROOT / ".claude-plugin/marketplace.json")
PYPROJECT = ROOT / "core/pyproject.toml"
INIT_PY = ROOT / "core/src/line1_core/__init__.py"


def _bump_semver(v: str, part: str) -> str:
    major, minor, patch = (int(x) for x in v.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bump plugin version in lockstep across manifests.")
    ap.add_argument("part", choices=["major", "minor", "patch"], help="Which semver part to bump.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    plugin = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    old = plugin["version"]
    new = _bump_semver(old, args.part)

    if args.dry_run:
        print(f"[dry-run] {old} -> {new} in plugin.json, codex plugin.json, both marketplace.json copies, pyproject.toml, __init__.py")
        return 0

    plugin["version"] = new
    PLUGIN_JSON.write_text(json.dumps(plugin, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # the Codex manifest carries its own version string and must move in lockstep too
    codex = json.loads(CODEX_PLUGIN_JSON.read_text(encoding="utf-8"))
    codex["version"] = new
    CODEX_PLUGIN_JSON.write_text(json.dumps(codex, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for marketplace in MARKETPLACES:
        mkt = json.loads(marketplace.read_text(encoding="utf-8"))
        mkt.setdefault("metadata", {})["version"] = new
        marketplace.write_text(json.dumps(mkt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    py = PYPROJECT.read_text(encoding="utf-8")
    py = re.sub(r'^version = "[^"]+"', f'version = "{new}"', py, count=1, flags=re.MULTILINE)
    PYPROJECT.write_text(py, encoding="utf-8")

    init = INIT_PY.read_text(encoding="utf-8")
    init = re.sub(r'^__version__ = "[^"]+"', f'__version__ = "{new}"', init, count=1, flags=re.MULTILINE)
    INIT_PY.write_text(init, encoding="utf-8")

    print(f"bumped {old} -> {new}. Commit and publish the marketplace repo so users get it via /plugin update.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
