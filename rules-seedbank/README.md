# rules-seedbank — candidate rules awaiting review

Staging area for the **half-automatic** Line 1 knowledge loop (modeled on StatsClaw's
`brain-seedbank → brain` flow). Nothing here is shipped; everything here is a **candidate** that a
maintainer must review before it can become a Line 1 rule.

## The loop (Line 2 → Line 1 → user)

```
Line 2 fix-loop lessons (runner/janitor/matcher *.md, grows with every batch)
        │  tools/distill_rules.py   (automatic — surfaces author-preventable lessons not yet in Line 1)
        ▼
rules-seedbank/candidates.json      (this folder — human reviews these)
        │  maintainer writes a final rule spec (the 8 fields) and runs:
        │  tools/promote_rule.py rule.json
        ▼
core/.../rules/author_rules.yaml     (shipped rule set; rules_version bumped; CHANGELOG updated)
        │  bump plugin version, publish to marketplace
        ▼
user runs /plugin update             (gets the new rules)
```

## Why human-in-the-loop

A rule that cries wolf erodes author trust (our standing anti-sycophancy / no-noise principle). The
distiller is intentionally over-inclusive (better to surface too many candidates than miss one); the
human gate is where false positives and pipeline-internal lessons get filtered, and where a
class-C lesson gets reframed as a low-priority **normalization** advisory rather than a "defect".

## Review checklist (per candidate)

1. Is it **author-preventable**? (Not purely our parser/trace/marker bug.)
2. If it is pipeline-internal but a normalized writing-style sidesteps it → make it
   `kind: normalization`, low priority, worded as "a better way to write it".
3. Is it **statically detectable** without executing code? If not → it belongs in
   `risk_register.cannot_predict`, not a rule.
4. Will the detector be **low-false-positive**? If not, drop it.
5. Assign `priority` P0–P4 by **downstream reproducibility cost**.
6. Keep `source_lessons` so the rule stays traceable to its Line 2 origin.

## Regenerate candidates

```bash
python3 tools/distill_rules.py            # writes rules-seedbank/candidates.json
```

`candidates.json` is regenerated output — do not hand-edit it.
