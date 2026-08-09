"""Distill candidate Line 1 rules from Line 2 lessons. Generates CANDIDATES ONLY — human review + promote_rule.py required before anything enters the shipped rule set."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
LESSON_DIRS = [
    REPO / ".claude/skills/runner-agent/references/lessons.md",
    REPO / ".claude/skills/janitor-agent/references/lessons.md",
    REPO / ".claude/skills/matcher-agent/references/lessons.md",
]
RULES_FILE = Path(__file__).resolve().parents[1] / "core/src/line1_core/rules/author_rules.yaml"
SEEDBANK = Path(__file__).resolve().parents[1] / "rules-seedbank"

# Signals that a lesson is PIPELINE-INTERNAL (our tooling) — author cannot prevent by rewriting.
# These must NOT become author rules (anti-blame principle).
_PIPELINE_INTERNAL = re.compile(
    r"REGOUT|regout|trace\(\)|prolog|parser|recovery mapper|cmd_id|end_map|"
    r"classifier|graduat|marker injection|debug_runner|jsonl|e\(b\)\s+ordering|"
    r"THRASHING|TIMEOUT|MAX_ITERATIONS|NO_OUTPUT|FIX_FAILED|dedup",
    re.IGNORECASE,
)
# Signals that a lesson is AUTHOR-side and a rewrite/structure change could prevent it.
_AUTHOR_PREVENTABLE = re.compile(
    r"author|use\s+command|data.?load|\bpath\b|absolute|rename|drop |keep |"
    r"version|ssc install|ado|library\(|#delimit|foreach|loop|abbrev|truncat|"
    r"missing|not shipped|restricted|deprecat|cd |master|entry|filename",
    re.IGNORECASE,
)


def _parse_lessons(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    out: list[dict[str, str]] = []
    for block in re.split(r"\n### ", text)[1:]:
        title = block.split("\n", 1)[0].strip()
        fields: dict[str, str] = {"title": title, "agent": path.parent.parent.name}
        for fname in ("Occurrences", "Status", "Problem", "Fix", "Fix_type"):
            m = re.search(rf"\*\*{fname}\*\*:\s*([^\n]+)", block)
            if m:
                fields[fname.lower()] = m.group(1).strip()
        fields["_body"] = block[:1500]
        out.append(fields)
    return out


def _existing_source_lessons() -> set[str]:
    data = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for rule in data["rules"]:
        for s in rule.get("source_lessons", []):
            seen.add(_norm(s))
    return seen


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())[:40]


def _already_covered(lesson: dict[str, str], existing: set[str]) -> bool:
    title_key = _norm(lesson["title"])
    if any(title_key[:20] in e or e[:20] in title_key for e in existing if len(e) > 12):
        return True
    occ = lesson.get("occurrences", "")
    for paper in re.findall(r"\b[A-Z][A-Za-z]+\d{4}[a-z]?\b", occ):
        if any(_norm(paper) in e for e in existing):
            return True
    return False


def distill() -> list[dict[str, object]]:
    existing = _existing_source_lessons()
    candidates: list[dict[str, object]] = []
    for path in LESSON_DIRS:
        for lesson in _parse_lessons(path):
            body = lesson.get("_body", "")
            if _PIPELINE_INTERNAL.search(body) and not _AUTHOR_PREVENTABLE.search(body):
                continue
            if not _AUTHOR_PREVENTABLE.search(body):
                continue
            if _already_covered(lesson, existing):
                continue
            candidates.append({
                "agent": lesson["agent"],
                "title": lesson["title"],
                "occurrences": lesson.get("occurrences", ""),
                "status": lesson.get("status", ""),
                "problem": lesson.get("problem", "")[:400],
                "fix": lesson.get("fix", "")[:400],
                "pipeline_internal_signal": bool(_PIPELINE_INTERNAL.search(body)),
            })
    return candidates


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Distill candidate Line 1 rules from Line 2 lessons (review required).")
    ap.add_argument("--out", default=str(SEEDBANK / "candidates.json"), help="Where to write candidates.")
    ap.add_argument("--limit", type=int, default=0, help="Cap candidates (0 = all).")
    args = ap.parse_args(argv)

    cands = distill()
    if args.limit:
        cands = cands[: args.limit]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"count": len(cands), "candidates": cands}, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"distilled {len(cands)} candidate rule(s) NOT yet covered by Line 1")
    print(f"  written to {out_path}")
    print("  REVIEW each, then run promote_rule.py to add approved ones to author_rules.yaml.")
    for c in cands[:15]:
        flag = " [pipeline-internal — consider normalization framing]" if c.get("pipeline_internal_signal") else ""
        title = str(c.get("title", ""))[:70]
        print(f"  - [{c.get('agent')}] {title}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
