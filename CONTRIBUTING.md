# Contributing to ReproAI

ReproAI improves with use. When you run it on a real package and find something — a defect it missed, a
false flag, a fix you had to make by hand, or a journal we do not support yet — you can send that lesson
back as a structured GitHub issue.

## The easy way: `/reproai:contribute`

In Claude Code or OpenAI Codex, run `/reproai:contribute`. It walks you through one of:

- **A missed rule / a false flag / a fix that worked** — becomes a rule-lesson issue that may be promoted
  into the author rule set.
- **A new venue** — a journal not yet supported. You supply its official replication-policy URL and the
  requirements (each tied to a verbatim quote); ReproAI drafts and validates a `venues/<id>.yaml` profile
  and hands you a pre-filled issue.

ReproAI **never posts on your behalf** — it opens a pre-filled "new issue" URL and you click **Submit**,
so a contribution is always under your own GitHub account. It also never includes your data, results, or
file paths: a contribution is about the general pattern or the public policy, not your package.

## How a contribution becomes a release

Issues are triaged and reviewed by a maintainer. Rule lessons feed `rules-seedbank/candidates.json` and
are promoted via `tools/distill_rules.py` / `tools/promote_rule.py` into the author rule set. Venue
suggestions are merged as a new `venues/<id>.yaml` after a maintainer string-searches each quoted
requirement against the cited policy and confirms the journal is legitimate. Nothing ships without human
review; contributors are credited in the changelog.

## Filing by hand

Prefer not to use the command? Open an issue with the **Venue contribution** or **Lesson contribution**
template directly, and validate a drafted profile with `reproai contribute --venue <draft.yaml>`.
