# tools — Line 1 self-upgrade pipeline

The half-automatic knowledge loop that keeps Line 1's rule set current as the downstream Line 2
reproducibility pipeline learns. **Maintainer tools, not part of the shipped plugin runtime.**

| Tool | Role |
|---|---|
| `distill_rules.py` | Scan Line 2 lessons (runner/janitor/matcher) → surface author-preventable ones not yet in Line 1 → write candidates to `rules-seedbank/candidates.json`. Over-inclusive on purpose. |
| `promote_rule.py` | Validate a human-reviewed final rule spec and append it to `author_rules.yaml`, bumping `rules_version` and updating `CHANGELOG.md`. Rejects malformed / duplicate / untraceable rules. |
| `bump_version.py` | After a knowledge update, bump the plugin version in lockstep across `plugin.json`, `marketplace.json`, `pyproject.toml`, and `__init__.py` so a marketplace `/plugin update` ships the new rules. |
| `build_public.py` | **Publish-time IP/anonymity gate.** Produce the anonymized public bundle (`dist/`) from the internal source: strips per-paper provenance (`source_lessons`), swaps the scrubbed rules into the engine, removes internal-only files (`CHANGELOG.md`, `VALIDATION.md`), and **refuses to build if any paper name leaks**. |

## Internal vs public boundary (IP red line)

The internal `author_rules.yaml` records `source_lessons` (which paper/lesson each rule came from)
for traceability. **The published rules must never name a specific paper or say what was wrong with
it** (SPEC.md IP guardrail). So:

- **Internal (this repo, source of truth):** full rules with `source_lessons`; `CHANGELOG.md`,
  `VALIDATION.md` (these name papers — internal only).
- **Public (`dist/`, what you publish):** `build_public.py` strips `source_lessons`, swaps the
  scrubbed rules into the engine copy, drops the internal-only docs, and runs a whole-tree paper-name
  scan that aborts the build on any leak. Rule bodies (rule/detection/priority/kind) are preserved
  verbatim — only the provenance is removed.

`dist/` and `public/` are generated; they are gitignored in the internal repo and are what you push
to the marketplace git repo.

## Publish flow

```bash
python3 tools/build_public.py --check      # CI gate: verify no paper names would leak
python3 tools/build_public.py              # build dist/ (anonymized, publishable)
# push dist/ to the marketplace git repo; tag the plugin version
```

## End-to-end

```bash
# 1. surface candidates from the latest Line 2 lessons
python3 tools/distill_rules.py

# 2. review rules-seedbank/candidates.json; write a final spec for an approved one, e.g. rule.json:
#    {"id":"A11-...","category":"structural","kind":"defect","priority":"P0",
#     "rule":"Author should ...","detection":"...","languages":["stata"],
#     "source_lessons":["runner: <lesson title>"]}

# 3. promote it (validates, appends, bumps rules_version, updates CHANGELOG)
python3 tools/promote_rule.py rule.json --dry-run   # check first
python3 tools/promote_rule.py rule.json

# 4. bump plugin version in lockstep, commit, publish the marketplace repo
python3 tools/bump_version.py minor

# 5. users get it: /plugin marketplace update statsclaw && /plugin update reproai
```

## Guardrails

- The distiller never writes to the shipped rule set — only to the seedbank.
- `promote_rule.py` enforces: required fields, valid category/kind/priority, unique id, and a
  non-empty `source_lessons` (traceability to the Line 2 lesson it came from).
- Pipeline-internal lessons (our parser/trace/marker bugs) are flagged by the distiller; promote
  them only if a normalized author writing-style sidesteps them, reframed as `kind: normalization`.
