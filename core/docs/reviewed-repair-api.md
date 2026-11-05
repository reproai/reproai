# Reviewed repair API

`reproai_prep.reviewed_repair` exposes the private Prep-to-Portal repair seam for Phase A. The API is deterministic and review-first: Prep builds a patch plan, the Portal shows that plan to a reviewer, and Prep applies it only when the caller sends back the exact approved source and plan fingerprints.

## Public functions

```python
from pathlib import Path
from reproai_prep.reviewed_repair import build_review, apply_review_to_copy

review = build_review(Path("replication_package"), venue="aea")
print(review.diff)

applied = apply_review_to_copy(
    Path("replication_package"),
    Path("replication_package.repaired"),
    approved_source_fingerprint=review.source_fingerprint,
    approved_plan_fingerprint=review.plan_fingerprint,
    venue="aea",
)
```

`build_review(root, venue=None)` returns a `Review` with the static precheck reports, a unified diff, the exact line edits, copied-file evidence, manual review items, and two approval tokens:

- `source_fingerprint`: SHA-256 over every file path, byte hash, and size in the reviewed package.
- `plan_fingerprint`: SHA-256 over the complete ordered repair plan, including line edits, manual items, and vendored ado file evidence.

`apply_review_to_copy(root, dest, approved_source_fingerprint, approved_plan_fingerprint, venue=None)` rebuilds the review, rejects stale approvals, reserves `dest` with an exclusive directory creation, copies the approved source into call-owned staging under that reservation, verifies the copied snapshot before mutation, applies only the approved low-risk changes, reruns the static check on the repaired copy, and returns `AppliedReview` with the applied-copy fingerprint and recheck reports. The reserved destination may be visible while apply is running; callers must treat success as established only when the function returns.

## Safety contract

The implementation deliberately keeps the original package immutable.

- The source root must be a plain directory tree: symlinks and special files are rejected.
- The destination must not already exist, must have an existing parent, and must not be inside the source root.
- Approval is invalid if either the source bytes or the computed repair plan changed after review.
- Every line edit is guarded by the exact old line text; a stale line aborts apply.
- Vendored ado files are copied only from plain files whose SHA-256 matches the reviewed evidence.
- If copying, vendoring, line editing, copied-snapshot validation, or static recheck fails, Prep removes only the destination reservation and staging tree created by that call; it never removes the original package, a pre-existing destination, or another process's concurrent destination.
- Before mutation, Prep verifies that the copied staging tree fingerprint equals the approved source fingerprint; after mutation, it reruns `coordinator.check()` on the repaired copy and verifies that the recheck file inventory fingerprint describes the applied snapshot.

Exceptions are exported from the public module: `UnsafePathError`, `StaleSourceError`, `StalePlanError`, and `ApplyValidationError`.

## Auto-safe and manual boundaries

Phase A only auto-applies reviewed low-risk rules with exact line guards:

- `B9-suppressed-data-load`: remove suppression around data loading so failures are visible. This can change failure behavior by surfacing a missing input instead of hiding it, so Prep treats it as reviewed low-risk repair rather than a blanket lossless rewrite.
- `B11-rmd-chunk-in-r`: comment R Markdown chunk fences embedded in plain `.R` scripts.
- Ado vendoring rewrite: comment `ssc install` calls and add package-local `adopath ++ ".certified/lib"` when the needed ado files are available with byte evidence.

All other advisory items are returned as `manual_items`. The Portal can display them, but this API will not silently apply them.

## Cert alignment matrix

| Downstream Cert need | Prep Phase A support | Evidence link |
|---|---|---|
| Cert must know whether the submitted bytes changed between author review and repair. | `source_fingerprint` binds approval to the full reviewed tree. `StaleSourceError` rejects changed inputs. | `reviewed_repair.tree_fingerprint()` and `apply_review_to_copy()` tests cover stale source rejection. |
| Portal must show exactly what will be changed before apply. | `Review.diff`, `changes`, `copied_files`, and `manual_items` are complete inputs to `plan_fingerprint`. | `plan_fingerprint()` hashes all ordered plan parts; tests mutate approved plans and expect rejection. |
| Repair must not alter the author original. | Apply always writes to a new copy and rejects destinations inside the source root or existing destinations. | `assert_safe_destination()` and reviewed-repair tests cover original immutability and unsafe destinations. |
| Cert dependency closure benefits from package-local Stata add-ons. | Available ado dependencies are vendored with source path, package name, SHA-256, and size evidence. | `build_vendor_parts()` delegates to existing `ado_vendor` scan/resolve code and includes copy evidence in the plan. |
| Line 1 must not issue a reproducibility or certification verdict. | The API only runs static `coordinator.check()`, computes diffs/fingerprints, and applies reviewed copy edits. | README trust boundary remains unchanged; no runner, coefficient matching, or certification result is invoked. |

## Current limits

This is a private Phase A seam, not a public CLI. It packages a reviewed copy for downstream Cert input; it does not execute author code, does not apply high-risk or output-changing repairs, and does not certify reproducibility. C13 is conservative: it detects literal top-level Stata `set seed N` in stochastic scripts, but leaves generalized seed refactoring to manual review.
