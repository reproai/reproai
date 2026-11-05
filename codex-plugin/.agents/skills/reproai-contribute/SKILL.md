---
name: reproai-contribute
description: Contribute back to reproai — file a structured GitHub issue for a defect reproai missed, a false flag, a fix that worked, or a new journal venue and its rules. reproai never posts; it hands you a pre-filled issue URL you click Submit on.
---

# /reproai contribute — give your lessons back

Using reproai on a real package turns up lessons: a defect it should have caught, a false flag, a fix you
made by hand, or a journal we do not support yet. This turns one lesson into a clean GitHub issue a
maintainer can absorb into the rule set or a venue profile. **It never posts** — it builds a pre-filled
"new issue" URL and the user clicks **Submit**.

Invoke the engine as `reproai contribute ...` if `reproai` is on PATH, otherwise the bundled-core form:
`PYTHONPATH="${REPROAI_CODEX_ROOT}/core/src" python3 -m reproai_prep.cli contribute ...`.

## Privacy (non-negotiable)

The user's replication package is confidential. A contribution is about the GENERAL pattern or a public
journal policy — never their paper, data, results, or paths. Scrub every draft (`reproai contribute
--scrub <file>`) before producing a URL; a venue suggestion carries no package data.

## Step 1 — pick the mode

Ask the user: **a missed rule** (a defect reproai should have flagged; a hand-fix or runtime lesson
belongs here) · **a false flag** (it flagged something fine) · **a new venue** (an unsupported journal).

## Lesson modes (missed rule / false flag)

1. Gather the minimal GENERALIZED pattern — abstracted code shape, no data or paths.
2. Scrub: `reproai contribute --scrub <draftfile>`; remove anything it flags.
3. Draft the body from the `lesson-contribution` template (type · what happened · what reproai should do
   · minimal pattern · environment).
4. Preview; on confirm, open
   `https://github.com/reproai/reproai/issues/new?template=lesson-contribution.md&labels=contribution:lesson,needs-triage`
   and tell the user to review and click **Submit**.

## New-venue mode

- **Step 0 — dedup.** Shipped venues: `aea`, `econsoc`, `jasa`, `worldbank`, `apsr`, `ajps`, `jop`, `generic_dataverse`,
  `generic_openicpsr` (glob the installed `venues/*.yaml` if reachable). Matches an existing venue → stop
  (already supported). Checks ⊆ a generic profile → recommend `--venue generic_...`, do not mint a profile.
- **Step 1 — citation gate (hard).** Require the official replication/data-code policy URL. No URL → stop,
  do not draft. WebFetch it read-only (or have the user paste the text) to extract requirements.
- **Step 2 — requirements + verbatim quotes.** Each requirement carries the literal policy sentence
  (`policy_quote`); drop any requirement with no locatable quote. Map each to a detector from the closed
  set only: `readme_pdf_at_root`, `readme_at_root`, `readme_has_sections` (+ `readme_sections:`),
  `has_master_script`, `env_declared`, `no_absolute_paths`, `rederive_from_raw`, `file_count_limit`
  (+ `deposit.max_files`), `license_at_root`, `manual_author_action`, or `unbuilt_detector`
  (+ `needs_detector:`) for a statically-checkable requirement with no detector yet.
- **Step 3 — targeted confirmations.** Ask only about params a proposed check needs (README sections,
  file cap, deposit/license/verifier metadata), pre-filled from the policy.
- **Step 4 — gaps.** `unbuilt_detector` + a `needs_detector:` name; if it is "a named file at the package
  root," suggest a snake_case detector name, else just describe what it must check.
- **Step 5 — draft, validate, hand off.** Write `venues/<id>.yaml` to a temp file (`profile_version` =
  the policy's last-updated date). Run `reproai contribute --venue <tmp.yaml>` until it passes (it blocks
  on identifying content and checks schema + known detectors + a clean dry-run). Show a compact per-check
  table, get one confirm, then open
  `https://github.com/reproai/reproai/issues/new?template=venue-contribution.yml&labels=contribution:venue,needs-triage`
  and print the requirements+quotes block and the validated YAML for the user to paste. The user submits;
  a maintainer is the legitimacy gate.

## Never

Never post/submit (only open a pre-filled URL the user submits); never include the user's data/results/
paths; never invent a detector name or a policy quote.
