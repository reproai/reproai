"""Automated plugin-integration checks runnable without a live Claude Code session: manifest validity, command/agent frontmatter, and that the path the command docs use to reach the engine actually resolves."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

LINE1 = Path(__file__).resolve().parents[1]
PLUGIN = LINE1 / "claude-plugin"
CORE_CLI = LINE1 / "core/src/line1_core/cli.py"

_FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.S)


def _fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def check_plugin_manifest(errors: list[str]) -> None:
    manifest = PLUGIN / ".claude-plugin/plugin.json"
    if not manifest.exists():
        _fail(f"missing {manifest}", errors)
        return
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("name") != "reproai":
        _fail(f"plugin name should be 'reproai', got {data.get('name')!r}", errors)
    if "version" not in data:
        _fail("plugin.json missing version", errors)
    if shutil.which("claude"):
        res = subprocess.run(["claude", "plugin", "validate", str(PLUGIN)], capture_output=True, text=True)
        if res.returncode != 0:
            _fail(f"`claude plugin validate` failed:\n{res.stdout}\n{res.stderr}", errors)
    else:
        errors.append("INFO: `claude` CLI not found; skipped `claude plugin validate`.")


def check_frontmatter(errors: list[str]) -> None:
    for md in sorted((PLUGIN / "commands").glob("*.md")) + sorted((PLUGIN / "agents").glob("*.md")):
        text = md.read_text(encoding="utf-8")
        m = _FRONTMATTER.match(text)
        if not m:
            _fail(f"{md.relative_to(LINE1)}: missing YAML frontmatter", errors)
            continue
        fm = yaml.safe_load(m.group(1))
        if "name" not in fm or "description" not in fm:
            _fail(f"{md.relative_to(LINE1)}: frontmatter needs name + description", errors)
        if md.parent.name == "commands" and not str(fm.get("name", "")).startswith("reproai"):
            _fail(f"{md.relative_to(LINE1)}: command name should start with 'reproai-', got {fm.get('name')!r}", errors)


def check_engine_path_resolves(errors: list[str]) -> None:
    import os
    if not CORE_CLI.exists():
        _fail("command docs reference the engine at core/src/line1_core/cli.py but it is missing", errors)
        return
    env = dict(os.environ)
    env["PYTHONPATH"] = str(LINE1 / "core/src")
    res = subprocess.run([sys.executable, "-m", "line1_core.cli", "--version"],
                         capture_output=True, text=True, env=env)
    if res.returncode != 0:
        _fail(f"engine not invokable via documented `python -m line1_core.cli`:\n{res.stderr}", errors)


def main() -> int:
    errors: list[str] = []
    check_plugin_manifest(errors)
    check_frontmatter(errors)
    check_engine_path_resolves(errors)

    info = [e for e in errors if e.startswith("INFO:")]
    real = [e for e in errors if not e.startswith("INFO:")]
    for e in info:
        print(e)
    if real:
        print("PLUGIN VALIDATION FAILED:")
        for e in real:
            print(f"  - {e}")
        return 1
    print("Plugin validation passed (manifest + frontmatter + engine path).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
