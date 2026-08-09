# ReproAI plugin — manual end-to-end smoke test

What the automated checks (`tools/validate_plugin.py`, `pytest core/tests/`) **cannot** verify is the
one thing only a live Claude Code (or Codex) session can: actually installing the plugin from the
marketplace and triggering its commands. Run this checklist once per release, after
`tools/validate_plugin.py` and `pytest` pass.

## Pre-req (automated — must be green first)

```bash
cd plugins/reproai
python3 -m pytest core/tests/ -q          # rule regression + schema + anonymity
python3 tools/validate_plugin.py          # manifest + frontmatter + engine path
python3 tools/build_public.py --check     # publish anonymity gate
```

## A. Install from the marketplace (Claude Code)

1. In a project dir, start `claude`.
2. `/plugin marketplace add <org>/reproai` (the published marketplace repo).
3. `/plugin install reproai@reproai --scope project`.
4. Confirm: `/plugin` lists `reproai` as installed and enabled.
   - [ ] plugin appears, no errors in the `/plugin` Errors tab.

## B. Commands appear and trigger

5. Type `/` and confirm these commands are offered:
   - [ ] `/reproai:check`
   - [ ] `/reproai:comply`
   - [ ] `/reproai:fix`
   - [ ] `/reproai:update`
6. Run `/reproai:check` on a small replication package (e.g. a copy of one IV paper's
   `replication_files/`).
   - [ ] It runs `reproai check` (or the bundled `python -m line1_core.cli`) and reports a
         priority-graded advisory (P0–P4) + venue compliance + risk register.
   - [ ] It prints the `knowledge: engine X, rules YYYY.MM.DD` line.
   - [ ] It does NOT execute any of the package's code, and does NOT state a reproducibility verdict.

## C. Fix command (dry-run + apply)

7. Run `/reproai:fix` (dry-run) on the same package.
   - [ ] Shows a unified diff of only auto-safe edits (B9/B11), or "No auto-safe fixes available".
8. Run `/reproai:fix ... --apply --out <copy>`.
   - [ ] Writes a fixed copy; the original is byte-for-byte unchanged.

## D. Update path

9. `/plugin marketplace update <org>/reproai` then `/plugin update reproai`.
   - [ ] After `/reload-plugins`, `/reproai:check` reports the new `rules` version.

## E. Codex parity (if shipping the Codex runtime)

10. Install per the Codex runtime instructions; repeat B6 and confirm `/reproai:check` runs.

## Sign-off

- Tester: __________   Date: __________   Plugin version: __________   rules_version: __________
- All boxes checked → release is good. Any failure → file against the relevant component and do not publish.
