"""The entry to IQSS Certify after preparation: can the author start it, and how.

Certify's entry is not a command Prep could call. The author presses Certify on a draft dataset
in the repository (Edit Dataset, Configure Options, Certify); that page gives a form carrying the
archive's address, the dataset's identifier and a time-limited uploader secret for that one draft;
the author pastes it into an AI assistant, which follows Certify's own instructions from there.
So this module checks what can be checked before that, the static readiness, the runtimes, and
the service with its published files, and writes CERTIFY_START.md, the steps the author takes.
It never installs or runs Certify's program and never sees the form's secret or a repository token.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import GENERATED_BY, __version__, coordinator, inventory, targets

Fetch = Callable[[str], str]
Which = Callable[[str], "str | None"]
PythonVersion = Callable[[list[str]], "tuple[int, int] | None"]

START_NAME = "CERTIFY_START.md"
_LIB_ROOT = ".certified/lib/"


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": f"reproai-prep/{__version__}"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8")


def _python_version(cmd: list[str]) -> tuple[int, int] | None:
    try:
        out = subprocess.run([*cmd, "-c", "import sys; print('%d %d' % sys.version_info[:2])"],
                             capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    parts = out.stdout.split()
    return (int(parts[0]), int(parts[1])) if out.returncode == 0 and len(parts) == 2 else None


def parse_sums(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2:
            out[parts[1]] = parts[0]
    return out


def changes_since(recorded: dict[str, str], live: dict[str, str]) -> list[str]:
    """What changed in Certify's published files since the profile was read, in words."""
    out = []
    for name, digest in sorted(recorded.items()):
        if name not in live:
            out.append(f"{name} is no longer published")
        elif live[name] != digest:
            out.append(f"{name} changed")
    out += [f"{n} is new" for n in sorted(live) if n.startswith("dist/") and n.endswith(".whl") and n not in recorded]
    return out


def _check(cid: str, ok: bool | None, severity: str, message: str) -> dict[str, Any]:
    return {"id": cid, "ok": ok, "severity": severity, "message": message}


def local_checks(root: Path, readiness: dict[str, Any], profile: dict[str, Any],
                 which: Which | None = None, python_version: PythonVersion | None = None) -> list[dict[str, Any]]:
    which, python_version = which or shutil.which, python_version or _python_version
    entries = inventory.scan(root)
    outside_lib = [e for e in entries if not e.path.replace(os.sep, "/").startswith(_LIB_ROOT)]
    langs = {e.language for e in outside_lib}
    do_files = [e.path for e in outside_lib if e.path.endswith(".do")]  # what Certify 0.2.0 stops on (CF1)
    checks = []

    status = readiness["status"]
    blocking = [it for it in readiness["items"] if it["effect"] in targets.BLOCKING_EFFECTS]
    if status == "blocked":
        names = ", ".join(sorted({it["rule_id"] for it in blocking}))
        checks.append(_check("readiness", False, "stop",
                             f"The static check predicts Certify would refuse the package or a run would fail ({names}). Repair these first."))
    elif status == "needs_attention":
        names = ", ".join(sorted({it["rule_id"] for it in readiness["items"]}))
        checks.append(_check("readiness", False, "warn", f"Nothing predicted to stop Certify, but read these first: {names}."))
    else:
        checks.append(_check("readiness", True, "stop", "No static obstacle (a prediction; only Certify's closing decides)."))

    if do_files:
        shown = ", ".join(do_files[:3]) + (" ..." if len(do_files) > 3 else "")
        checks.append(_check("stata", False, "stop",
                             f"The copy holds Stata scripts ({shown}). Certify 0.2.0 stops on any .do file: leave them out "
                             "of the copy and say so in CERTIFICATION-NOTES.txt, or certify later."))
    else:
        checks.append(_check("stata", True, "stop", "No Stata scripts (Certify 0.2.0 runs R and Python only)."))

    if not langs & {"r", "python"}:
        checks.append(_check("scripts", False, "stop", "No R or Python script to run."))
    windows = os.name == "nt"
    if "r" in langs:
        found = which("Rscript")
        checks.append(_check("runtime_r", bool(found), "warn" if windows else "stop",
                             f"R found: {found}" if found else
                             "Rscript is not on the PATH. The analysis must run on this computer; on Windows, tell the assistant where Rscript.exe is."))
    if "python" in langs:
        found = which("python3") or which("python")
        checks.append(_check("runtime_python", bool(found), "stop",
                             f"Python found: {found}" if found else "No python3 on the PATH for the analysis."))

    need = tuple(profile.get("entry", {}).get("program_python", [3, 12]))
    candidates = [[f"python3.{m}"] for m in range(20, need[1] - 1, -1)] + [["python3"], ["python"]] + ([["py", f"-{need[0]}.{need[1]}"]] if windows else [])
    program_python = None
    for cmd in candidates:
        if which(cmd[0]):
            v = python_version(cmd)
            if v and v >= need:
                program_python = (" ".join(cmd), v)
                break
    want = f"{need[0]}.{need[1]}"
    checks.append(_check("program_python", bool(program_python), "stop",
                         f"Python {program_python[1][0]}.{program_python[1][1]} for Certify's own program: {program_python[0]}"
                         if program_python else f"Certify's own program needs Python {want} or newer, and none was found (python.org has it)."))
    return checks


def online_checks(profile: dict[str, Any], fetch: Fetch | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fetch = fetch or _fetch
    entry, watch = profile["entry"], profile["watch"]
    service = entry["service"].rstrip("/")
    checks, found = [], {}

    try:
        health = json.loads(fetch(f"{service}/health"))
    except (OSError, ValueError) as exc:
        health = None
        checks.append(_check("service", False, "stop", f"The certification service did not answer ({exc}). Certify has no offline mode; try again later."))
    if health is not None:
        ok = health.get("ok") is True
        checks.append(_check("service", ok, "stop", "The certification service answers." if ok else "The certification service answered, but not ok."))
        found["service_version"] = health.get("version")
        if health.get("dataverse"):
            found["repository"] = health["dataverse"]
        basis = str(profile["basis"]["author_program"])
        if ok and health.get("version") and str(health["version"]) != basis:
            checks.append(_check("service_version", False, "warn",
                                 f"The service runs Certify {health['version']}; ReproAI Prep's Certify rules were read for {basis}, so its prediction may be out of date."))

    try:
        site, mirror = parse_sums(fetch(f"{service}/SHA256SUMS")), parse_sums(fetch(entry["sums_mirror"]))
    except OSError as exc:
        checks.append(_check("checksums", False, "stop", f"Certify's published checksum list could not be read ({exc}); its instructions install nothing without it."))
        return checks, found
    if not site or site != mirror:
        checks.append(_check("checksums", False, "stop",
                             "Certify's two published checksum lists (its site and its GitHub mirror) differ; its instructions stop here and install nothing."))
        return checks, found
    checks.append(_check("checksums", True, "stop", "Certify's two published checksum lists agree."))
    changed = changes_since(watch["files"], site)
    checks.append(_check("unchanged", not changed, "warn",
                         "Certify is unchanged since ReproAI Prep's Certify rules were read." if not changed else
                         "Certify has changed since ReproAI Prep's Certify rules were read (" + "; ".join(changed) + "), so its prediction may be out of date."))
    return checks, found


def assess(root: Path, venue: str | None = None, online: bool = True, fetch: Fetch | None = None,
           which: Which | None = None, python_version: PythonVersion | None = None,
           no_changes: bool = False) -> dict[str, Any]:
    """`no_changes`: the author asked that nothing in the package be changed, even in a copy."""
    root = root.resolve()
    profile = targets.load("certify")
    readiness = coordinator.check(root, venue, "certify")["target_readiness_report"]
    checks = local_checks(root, readiness, profile, which, python_version)
    found: dict[str, Any] = {}
    if online:
        more, found = online_checks(profile, fetch)
        checks += more
    else:
        checks.append(_check("online", None, "warn", "The service and its published files were not checked (--offline)."))
    if any(c["ok"] is False and c["severity"] == "stop" for c in checks):
        status = "not_ready"
    elif any(c["ok"] is False for c in checks):
        status = "attention"
    else:
        status = "ready"
    entry = profile["entry"]
    return {
        "schema_version": 1,
        "generated_by": GENERATED_BY,
        "prepared_copy": str(root),
        "status": status,
        "readiness": readiness["status"],
        "no_changes": no_changes,
        "checks": checks,
        "service": entry["service"],
        "repository": found.get("repository", entry["repository"]),
        "instructions": entry["instructions"],
        "beta": entry.get("beta", ""),
        "boundary": ("ReproAI Prep stops here. It never installs or runs Certify's program and never sees the form's "
                     "secret or a repository token; only Certify's closing and certificate say whether a package is certified."),
    }


_STATUS_WORDS = {"ready": "yes", "attention": "yes, after reading the notes below", "not_ready": "not yet"}


def markdown(a: dict[str, Any]) -> str:
    mark = {True: "x", False: " ", None: "?"}
    lines = ["# Starting IQSS Certify", "", f"Prepared copy: `{a['prepared_copy']}`",
             f"Can start: **{_STATUS_WORDS[a['status']]}**", "", "## Checks"]
    lines += [f"- [{mark[c['ok']]}] {c['message']}" for c in a["checks"]]
    if a["status"] == "not_ready":
        lines += ["", "## First", "Repair what is unticked above (`/reproai:fix`, or the repairs step of `/reproai:prepare`), "
                  "then run `reproai certify-start` again. If what stops it is something you chose to keep, such as a "
                  "Stata script, Certify cannot start on this copy; the preparation for your journal still stands."]
    else:
        repo = a["repository"].rstrip("/")
        lines += ["", "## Start (about five minutes, then a wait of one to three hours)"]
        if a["beta"]:
            lines.append(a["beta"] + " That certificate is separate from the deposit your journal asks for; "
                         "deposit with the journal as it says.")
        lines.append("Certify runs your scripts on this computer three times: two practice runs and the certified run.")
        box = ("tick [x] \"Do not change any of my files, even in a copy\", as you asked here: Certify then stops and "
               "tells you instead of proposing repairs" if a["no_changes"] else
               "leave \"Do not change any of my files, even in a copy\" unticked, so Certify can still propose its own repairs")
        lines += [
            "",
            f"1. Open {repo} and log in, or create an account.",
            "2. Make a collection: Add Data, then New Dataverse.",
            "3. Inside it, make a draft dataset: Add Data, then New Dataset. Give it a title (for example "
            "\"Replication Data for: <your paper's title>\"), the authors, a contact, a one-paragraph description "
            "and a subject, and save it. Nothing is public until you publish.",
            "4. On the draft's page, click Edit Dataset, then Certify under Configure Options. A page called Certify opens.",
            "5. Click Copy the form. Before you paste it, fill in the copied text: after \"Your replication dataset's "
            f"folder on this computer:\" write the prepared copy, `{a['prepared_copy']}`; {box}; and leave \"Publish as "
            "soon as it is certified\" unticked, so the dataset stays a draft until you say \"publish\".",
            "6. Paste the filled form into a chat with an AI assistant that can run commands on this computer (the chat "
            f"where you ran ReproAI Prep will do). It follows Certify's own instructions from there ({a['instructions']}).",
            "7. Do not click Publish Dataset until the assistant tells you the certificate is sealed.",
            "",
            "The form carries a secret for your draft. Paste it only into the assistant's chat, never into a file or an email.",
        ]
    lines += ["", f"_{a['boundary']}_", ""]
    return "\n".join(lines)


def write(a: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    j, m = out_dir / "certify_start.json", out_dir / START_NAME
    j.write_text(json.dumps(a, indent=2, ensure_ascii=False), encoding="utf-8")
    m.write_text(markdown(a), encoding="utf-8")
    return j, m
