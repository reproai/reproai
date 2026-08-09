---
name: reproai-update
description: Show the installed reproai knowledge version and how to update to the latest rule set. Use when the author asks whether their rules are current, or how reproai stays up to date.
---

# reproai update — knowledge version & update (Codex)

reproai ships a knowledge base (author rule set + venue profiles + style guide) that grows over
time. The rules are data, not code.

## Show what's installed

```bash
reproai check . --json | python3 -c "import json,sys;print(json.load(sys.stdin)['knowledge_versions'])"
```

It reports `engine` (code version), `rules_version` (date-based), and each venue profile version.
The `reproai check` summary line also prints `knowledge: engine X, rules Y`.

## Update to the latest

reproai is distributed through the Codex plugin marketplace; a new rules_version ships as a new
plugin version:

```
codex plugin marketplace update reproai
codex plugin update reproai
```

Then restart Codex (or reload) so the new rules load.

## How new rules get in (for maintainers)

Two sources feed the front of this pipeline: internal Line 2 telemetry, and user contributions filed via
`/reproai:contribute` (GitHub issues; venue suggestions merge as a new `venues/<id>.yaml` after review).

```
Line 2 lessons → tools/distill_rules.py → rules-seedbank/candidates.json → human review →
tools/promote_rule.py → author_rules.yaml (rules_version bumped) →
tools/bump_version.py → versions in lockstep → publish
```

Nothing enters the shipped rule set without human review. See `rules-seedbank/README.md`.
