---
name: reproai-update
description: Show the installed reproai knowledge version and how to update to the latest rule set. Use when the author asks whether their rules are current, or how reproai stays up to date.
---

# /reproai update — knowledge version & update

reproai ships a **knowledge base** (author rule set + venue profiles + style guide) that grows as the
downstream reproducibility pipeline (Line 2) learns from new replication packages. The rules are
data, not code, so they update independently of how a single package is diagnosed.

## Show what's installed

Run a check and read the `knowledge_versions` block of the result, or:

```bash
reproai check . --json | python3 -c "import json,sys;print(json.load(sys.stdin)['knowledge_versions'])"
```

It reports `engine` (code version), `rules_version` (date-based, e.g. 2026.06.15), and each venue
profile version. The `reproai check` summary line also prints `knowledge: engine X, rules Y`.

## Update to the latest

reproai has **two parts**: the plugin *commands* (shipped through the Marketplace) and the Python
*engine* that holds the rules and venue profiles (the `reproai-prep` package). The rules live in the
engine, so updating the plugin alone does **not** refresh them — update both.

First, the commands:

```
/plugin marketplace update reproai        # refresh the marketplace listing
/plugin update reproai                      # latest commands
/reload-plugins                             # (or restart) so the new commands load
```

Then the engine, where the rules and venue profiles actually live:

```bash
python3 -m pip install -U reproai-prep                                   # the stable release
```

The development version, with the newest rules and venue profiles before they are released, comes from
GitHub:

```bash
python3 -m pip install -U "git+https://github.com/reproai/reproai#subdirectory=core"  # development version
```

A development install keeps the last release's version number until the next release, so
`python3 -m pip install -U reproai-prep` does not move it back; `python3 -m pip install --force-reinstall reproai-prep`
does.

Re-run a check and read `knowledge_versions` to confirm the new `rules_version` loaded.

## How new rules get in (for maintainers)

Two sources feed the front of this pipeline: internal Line 2 telemetry, and **user contributions filed
via `/reproai:contribute`** (GitHub issues). Venue suggestions arrive the same way and merge as a new
`venues/<id>.yaml` after maintainer review.

```
Line 2 lessons  ──tools/distill_rules.py──▶  rules-seedbank/candidates.json  ──human review──▶
tools/promote_rule.py  ──▶  author_rules.yaml (rules_version bumped, CHANGELOG updated)  ──▶
tools/bump_version.py  ──▶  plugin/marketplace/pyproject versions in lockstep  ──▶  publish
```

Nothing enters the shipped rule set without human review (anti-noise principle). See
`rules-seedbank/README.md`.
