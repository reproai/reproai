# ReproAI Prep

By Leo Yang Yang and Yiqing Xu.

ReproAI Prep audits and prepares a replication package so it runs from scratch on a clean
machine and meets the entry requirements of a journal's reproducibility check or of a
certification service such as [IQSS Certify](https://certify.iq.harvard.edu). It never compares
results with a paper and never issues a reproducibility verdict or a certificate: certification
is a separate, downstream step that Prep prepares a package for.

```bash
pip install reproai-prep
reproai check path/to/package --venue aea --out reports/
reproai check path/to/package --target certify --out reports/
```

## Commands

| Command | What it does |
|---|---|
| `reproai check` | Static audit: inventory, dependency graph, an author rule set, a venue profile (AEA, Econometric Society, APSR, AJPS, JOP, ...). Writes four JSON reports; with `--target certify`, also a certification-readiness report naming what Certify would refuse, fail on, mark or note. Never runs author code. |
| `reproai fix` | Applies the semantics-preserving fixes to a **copy** (dry run by default); the original is never touched. |
| `reproai rehearse` | **Runs code, on a copy, only when asked.** Runs the entry scripts twice the way a certification service will (from the root, network denied as far as the machine allows, a private empty home, fixed time zone and locale, figures to files, each step seeded) and compares the outputs: identical, numerically close, or different. |
| `reproai handoff` | Where preparation stops: the run order, the libraries to vendor, what is still open, files read from outside, and the next steps for the destination. |
| `reproai note` | Records one approved repair in the prepared copy's `CERTIFICATION-NOTES.txt`. |
| `reproai gate`, `outputs`, `map`, `readme`, `contribute` | Output-export gate (every table and figure has an export), runtime output check (every expected file was written by this run; formerly `verify`), manuscript exhibit map, README scaffold, and a pre-filled issue for a missed rule or a false flag. |

Every pass or fail, risk tier and fix eligibility is decided by deterministic code in this
package, never by an AI assistant driving it; assistants explain and draft, and the author
approves every change.

The same engine backs the Claude Code and Codex plugins, `PREP_PROMPT.md` for any other assistant,
and the command line. See the [repository](https://github.com/reproai/reproai) for the plugins, the
rule set and the venue profiles.

## Reports

- `architecture_report.json`: entry points, build order, dependency graph, orphans, table map
- `advisory_plan.json`: remediation items, each auto-applicable or propose-only
- `venue_compliance_report.json`: pass or fail per requirement of the venue profile
- `risk_register.json`: what would likely break a downstream reproducibility run
- `target_readiness_report.json` (with `--target`): blocked, needs attention, or no static obstacle

## Reviewed preparation from Python

```python
from pathlib import Path
from reproai_prep.reviewed_repair import build_review, apply_review_to_copy

review = build_review(Path("replication-package"))
tasks = review.author_tasks   # automatic, required, required_manual, optional, change_summaries
# Show the plan and its diff; obtain approval before applying it.
applied = apply_review_to_copy(review.root, Path("prepared-copy"), review.source_fingerprint,
                               review.plan_fingerprint, review.venue)
```

Source and plan fingerprints are rechecked when the plan is applied to a new copy, an unmatched
requirement is never assumed repaired, and `applied.explanation` gives an author-facing summary of
what changed and why. These are preparation results, not a certification verdict.

## Citing

Leo Yang Yang and Yiqing Xu. 2026. "ReproAI Prep: Preparing Replication Packages for
Reproducibility Checks and Certification." Software, https://github.com/reproai/reproai.

## License

MIT.
