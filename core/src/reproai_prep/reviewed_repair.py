from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from . import coordinator
from .author_tasks import preparation_tasks, preparation_explanation
from ._reviewed_repair_impl import (
    ApplyValidationError,
    CopyEvidence,
    JsonMap,
    LineChange,
    ManualItem,
    ReviewedRepairError,
    StalePlanError,
    StaleSourceError,
    UnsafePathError,
    apply_review_changes,
    assert_safe_destination,
    assert_safe_root,
    build_diff,
    build_fix_plan,
    copy_review_source,
    build_manual_items,
    build_vendor_parts,
    entries_fingerprint,
    apply_review_mutations,
    automation_payload,
    plan_fingerprint,
    require_postchecks,
    tree_fingerprint,
)

__all__ = (
    "AppliedReview",
    "ApplyValidationError",
    "Review",
    "ReviewedRepairError",
    "StalePlanError",
    "StaleSourceError",
    "UnsafePathError",
    "apply_review_to_copy",
    "build_review",
    "preparation_tasks",
    "preparation_explanation",
)


@dataclass(frozen=True, slots=True)
class AppliedReview:
    destination: Path
    source_fingerprint: str
    plan_fingerprint: str
    applied_fingerprint: str
    recheck_fingerprint: str
    changes: tuple[LineChange, ...]
    copied_files: tuple[CopyEvidence, ...]
    recheck: JsonMap

    @property
    def explanation(self) -> dict[str, object]:
        return preparation_explanation(self.changes, self.copied_files)


@dataclass(frozen=True, slots=True)
class Review:
    root: Path
    venue: str | None
    source_fingerprint: str
    plan_fingerprint: str
    diff: str
    changes: tuple[LineChange, ...]
    copied_files: tuple[CopyEvidence, ...]
    manual_items: tuple[ManualItem, ...]
    precheck: JsonMap
    automation: JsonMap | None = None

    @property
    def author_tasks(self) -> dict[str, object]:
        """Host-independent preparation plan, author requirements and summaries."""
        return preparation_tasks(self.root, review=self)

    def _apply_changes_to(self, dest: Path) -> None:
        apply_review_changes(self.root, dest, self.changes, self.copied_files)


def build_review(root: Path, venue: str | None = None) -> Review:
    source = assert_safe_root(root)
    source_fingerprint = tree_fingerprint(source)
    precheck: JsonMap = coordinator.check(source, venue)
    plan = build_fix_plan(source, precheck["advisory_plan"])
    line_changes = tuple(LineChange(e.file, e.line, e.old, e.new, e.rule_id, e.reason) for e in plan.edits)
    vendor_changes, copied_files, vendor_manual = build_vendor_parts(source)
    changes = tuple(sorted((*line_changes, *vendor_changes), key=lambda c: (c.file, c.line, c.rule_id)))
    manual_items = (*build_manual_items(precheck["advisory_plan"], changes), *vendor_manual)
    diff = build_diff(source, changes, copied_files)
    automation = automation_payload(plan)
    approved_plan = plan_fingerprint(changes, copied_files, manual_items, automation)
    return Review(source, venue, source_fingerprint, approved_plan, diff, changes, copied_files, manual_items, precheck, automation)


def apply_review_to_copy(
    root: Path,
    dest: Path,
    approved_source_fingerprint: str,
    approved_plan_fingerprint: str,
    venue: str | None = None,
    *, progress=None,
) -> AppliedReview:
    """Apply to a separate copy; optionally observe review/copy/changes/validate starts.

    Progress callbacks are best-effort observations, never approval or cancellation.
    Successful return remains the only indication that the copy is ready.
    """
    def notify(stage):
        # Progress is observation only: a disconnected UI cannot alter repairs.
        if progress is not None:
            try:
                progress(stage)
            except Exception:
                pass
    notify("review")
    review = build_review(root, venue)
    if review.source_fingerprint != approved_source_fingerprint:
        raise StaleSourceError("source fingerprint no longer matches approved review")
    if review.plan_fingerprint != approved_plan_fingerprint:
        raise StalePlanError("plan fingerprint no longer matches approved review")
    safe_plan = build_fix_plan(review.root, review.precheck["advisory_plan"])
    destination = assert_safe_destination(review.root, dest)
    staging_name = f".{destination.name}.reproai-{uuid4().hex}.tmp"
    published = False
    reserved = False
    try:
        try:
            destination.mkdir()
        except FileExistsError as exc:
            raise UnsafePathError(f"destination appeared during apply: {destination}") from exc
        reserved = True
        staged = destination / staging_name
        notify("copy")
        copy_review_source(review.root, staged)
        if tree_fingerprint(staged) != approved_source_fingerprint:
            raise StaleSourceError("copied source snapshot does not match approved review")
        notify("changes")
        apply_review_mutations(staged, review.changes, review.copied_files)
        notify("validate")
        require_postchecks(staged, safe_plan)
        for child in staged.iterdir():
            _ = child.rename(destination / child.name)
        staged.rmdir()
        applied_fingerprint = tree_fingerprint(destination)
        recheck: JsonMap = coordinator.check(destination, venue)
        recheck_fingerprint = entries_fingerprint(recheck["architecture_report"])
        if recheck_fingerprint != applied_fingerprint:
            raise ApplyValidationError("recheck did not describe the applied copy snapshot")
        published = True
        return AppliedReview(
            destination,
            review.source_fingerprint,
            review.plan_fingerprint,
            applied_fingerprint,
            recheck_fingerprint,
            review.changes,
            review.copied_files,
            recheck,
        )
    finally:
        if not published and reserved and destination.exists():
            rmtree(destination)
