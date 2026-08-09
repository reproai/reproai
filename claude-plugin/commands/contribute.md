---
name: reproai-contribute
description: Contribute back to reproai — file a structured GitHub issue for a defect reproai missed, a false flag, a fix that worked, or a new journal venue and its rules. reproai never posts; it hands you a pre-filled issue URL you click Submit on.
---

# /reproai contribute — give your lessons back

Using reproai on a real package turns up lessons: a defect it should have caught, a false flag, a fix
you made by hand, or a journal we do not support yet. This command turns one lesson into a clean GitHub
issue a maintainer can absorb into the rule set or a venue profile. **It never posts anything** — it
builds a pre-filled "new issue" URL and you click **Submit**. You are always the publisher.

## Privacy (non-negotiable)

Your replication package is confidential. A contribution is about the GENERAL pattern, or a public
journal policy — never your paper, data, results, or file paths. Scrub every draft before producing a
URL (`reproai contribute --scrub <file>`); a venue suggestion carries no package data at all.

## Step 1 — pick the mode

Use AskUserQuestion:

- **A missed rule** — a package defect reproai should have flagged but did not (a fix you had to make by
  hand, or a runtime lesson from running it, belong here).
- **A false flag** — reproai flagged something that was actually fine.
- **A new venue** — a journal not yet supported, with its replication policy.

## Lesson modes (missed rule / false flag)

1. Gather the minimal GENERALIZED pattern — the code shape, abstracted from the paper, with no data or
   paths.
2. Scrub it: `reproai contribute --scrub <draftfile>`; if it flags an absolute path, email, etc., remove
   it before going on.
3. Draft the issue body from the `lesson-contribution` template (type · what happened · what reproai
   should do · the minimal pattern · environment).
4. Preview to the user. On confirm, open:
   `https://github.com/reproai/reproai/issues/new?template=lesson-contribution.md&labels=contribution:lesson,needs-triage`
   Tell them to review and click **Submit**.

## New-venue mode

**Step 0 — dedup.** reproai already ships `aea`, `econsoc`, `jasa`, `worldbank`, `apsr`, `ajps`, `jop`, plus
`generic_dataverse` / `generic_openicpsr` (glob the installed `venues/*.yaml` if reachable to be current).
If the proposal matches a shipped venue's id, name, or `applies_to` → stop and say it is already supported
(a profile *update* is a separate path). If the proposed checks are a subset of a generic profile →
recommend `--venue generic_dataverse` / `generic_openicpsr` instead of minting a new one.

**Step 1 — citation gate (hard).** Ask for the journal and the URL of its official replication /
data-and-code policy. **No URL → stop; do not draft.** WebFetch the URL (read-only) to confirm it
resolves and to extract requirements; if it is PDF- or login-gated, have the user paste the policy text.

**Step 2 — extract requirements, each with a verbatim quote.** For every requirement, capture the literal
policy sentence it paraphrases (the `policy_quote`); a requirement with no locatable quote is dropped, not
invented. Propose a detector from this closed set only:

| Requirement | Detector |
|---|---|
| README at root, PDF required | `readme_pdf_at_root` |
| README at root, PDF preferred / MD ok | `readme_at_root` |
| README must contain sections X, Y, Z | `readme_has_sections` (+ a `readme_sections:` list) |
| Master / run-all script | `has_master_script` |
| State software / versions / cores | `env_declared` |
| No machine-specific absolute paths | `no_absolute_paths` |
| Ship raw→analysis preprocessing code | `rederive_from_raw` |
| Zip above N files | `file_count_limit` (+ `deposit.max_files: N`) |
| Include a LICENSE file | `license_at_root` |
| Form / deposit / timeline / seed / exemption (off-package author action) | `manual_author_action` |
| Statically checkable, but no detector inspects that artifact | `unbuilt_detector` (+ `needs_detector:`) |

**Step 3 — targeted confirmations.** Ask only about params a proposed check needs: README sections (if
`readme_has_sections`, pre-checked from the policy, user prunes), a file-count cap (if `file_count_limit`),
and a small metadata batch (deposit location, license default, verifier) pre-filled from the policy text.

**Step 4 — gaps.** A requirement that is statically checkable but has no detector ships as
`unbuilt_detector` with a `needs_detector:` name. If it is simply "a named file exists at the package
root," suggest a snake_case detector name (e.g. `codebook_at_root`) for the maintainer; otherwise just
describe what the detector must check — do not invent a build recipe.

**Step 5 — draft, validate, preview, hand off.**
1. Write the draft `venues/<id>.yaml` to a temp file. Fill `profile_version` with the policy's
   last-updated date (not today's).
2. Run `reproai contribute --venue <tmp.yaml>`. It blocks on any identifying content and checks schema +
   known detectors + a clean dry-run. If it reports errors, fix the draft and re-run until it passes.
3. Show the user a compact table — each check: id, detector, one-line requirement, and a marker
   (✓ auto-checked / ✎ author action / ⚠ needs a new detector). One confirm.
4. Open the pre-filled URL:
   `https://github.com/reproai/reproai/issues/new?template=venue-contribution.yml&labels=contribution:venue,needs-triage`
   Then print the long fields (the requirements+quotes block and the validated `venues/<id>.yaml`) for the
   user to paste into the form after it loads. Tell them: this posts under their GitHub account; reproai
   does not verify journal legitimacy — a maintainer does — so review and click **Submit**.

## What you never do

- Never post or submit — only ever open a pre-filled URL the user submits.
- Never put the user's data, results, or paths in any packet.
- Never invent a detector name or a policy quote.
