# Venue profiles — engine semantics & honesty taxonomy

Each `venues/<id>.yaml` is a target-journal replication-package profile. The deterministic engine
(`venue_engine.py`) reads it and emits one `Check` per `checks[]` entry. **The engine owns every
`status`.** No host LLM and no author answer ever changes a status — that is the anti-sycophancy
boundary, and it is non-negotiable.

## Status vocabulary (three-tier honesty taxonomy)

| status | meaning |
|---|---|
| `pass` / `fail` | A static, no-execution detector has package evidence to decide. |
| `needs_author_action` | A genuine OFF-package action the engine cannot verify (sign a form, deposit to a repository, request verification, editor approval, a timing/deadline, legal authority, a manuscript-stage process). |
| `not_implemented` | Statically checkable IN PRINCIPLE, but the detector is not built yet. Carries `needs_detector`. (`test_no_unbuilt_detectors_in_shipped_profiles` keeps a shipped profile from parking one of these forever.) |
| `not_applicable` | Reserved for a genuinely inapplicable conditional requirement (or an unknown detector). |

## Detectors

A check names a `detector` from the closed `KNOWN_DETECTORS` set. Static, evidence-returning
detectors include: `readme_pdf_at_root`, `readme_at_root`, `readme_has_sections`,
`has_master_script`, `env_declared`, `no_absolute_paths`, `rederive_from_raw`, `file_count_limit`,
`license_at_root`, `data_availability_statement`, `data_citation`, `seeded_rng`. Two non-detector
tiers: `manual_author_action` (emits `needs_author_action`) and `unbuilt_detector` (emits
`not_implemented`).

- `data_availability_statement` — scans the root README (Markdown/text, or a PDF README via
  `pdftotext`) for a Data Availability Statement signal. `pass` if found; `needs_author_action` if a
  README exists without one; `fail` if there is no README to carry it.
- `data_citation` — scans the README and code/text files for a persistent identifier (a DOI, or a
  handle / Dataverse / Zenodo / ICPSR / OSF URL). `pass` if any is found; else `needs_author_action`.
- `seeded_rng` — a code-shape scan (never execution): flags an R parallel loop (`%dopar%` / `foreach`
  / `mclapply` / `parLapply`) with no reproducible-RNG signal (`registerDoRNG` / `%dorng%` /
  `clusterSetRNGStream` / `set.seed`) as `needs_author_action`; otherwise `pass`.

## Guidance fields (never a verdict)

A `manual_author_action` (or any) check may add three optional, author-facing guidance fields. They
are concrete help grounded in the requirement + source — **they are NOT policy quotes and never
change the status**:

- `author_action` — what the author must do. When present it becomes the check's `detail`.
- `how` — how to do it.
- `self_check` — how the author confirms it is done (the engine never re-checks this).

`policy_quote` (where present) must stay a verbatim quote from the cited `source`. Do not fabricate
one; if a venue gives no exact wording for an item, omit `policy_quote` and rely on `requirement`.

## Adding / changing a profile

- A new `venues/<id>.yaml` is auto-discovered by the test matrix (`venues/*.yaml` glob).
- Use a real detector when a static check is possible; use `manual_author_action` (with
  `author_action`/`how`/`self_check`) for off-package items; use `unbuilt_detector` + `needs_detector`
  only as a deliberate, CI-guarded placeholder for a checkable-in-principle item.
