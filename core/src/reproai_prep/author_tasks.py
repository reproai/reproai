"""Prep-owned author tasks and change summaries, reusable by any host.

No Portal or Cert imports. Optional caller requirements use plain dictionaries;
classification never changes those requirements or authorizes certification.
"""
from collections import Counter
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from . import ado_vendor


def _record(value: Any) -> dict[str, Any]:
    return asdict(value) if is_dataclass(value) else dict(value)


def preparation_tasks(root: Path, readiness: dict[str, Any] | None = None,
                      review: Any = None) -> dict[str, Any]:
    """Separate executable reviewed changes, required author input and advice.

    Pass a Review or its serialized plan. With no caller requirements, Prep
    derives external-dependency requirements itself. With requirements, only
    exact edits covering every occurrence can classify a dependency as planned.
    """
    plan = _record(review) if review is not None else {}
    changes = plan.get("changes", [])
    copies = plan.get("copied_files", [])
    manual = plan.get("manual_items", [])
    occurrences = ado_vendor.scan_package(root)
    if readiness is None:
        issues = {}
        for item in occurrences:
            key = (item.file, item.detail)
            issues[key] = {"code": "undeclared_external_read", "blocking": True,
                           "headline": "Code reads outside the replication dataset", "file": item.file,
                           "evidence": {"target": item.detail}}
        readiness = {"issues": list(issues.values())}
    automatic, required = [], []
    texts = {}
    for issue in readiness.get("issues", []):
        if not issue.get("blocking"):
            continue
        covered = False
        if issue.get("code") == "undeclared_external_read" and copies:
            file = issue.get("file", "")
            target = issue.get("evidence", {}).get("target")
            path = (root / file).resolve()
            matches = [item for item in occurrences if item.file == file and item.detail == target]
            if matches and path.is_relative_to(root.resolve()) and path.is_file():
                if file not in texts:
                    texts[file] = path.read_text(encoding="utf-8", errors="replace").splitlines()
                covered = all(any(
                    edit.get("file") == file and edit.get("line") == item.line
                    and edit.get("old") == texts[file][item.line - 1]
                    and str(edit.get("rule_id", "")).startswith("ADO-")
                    and (edit.get("new", "").lstrip().startswith("*") or '".certified/lib"' in edit.get("new", ""))
                    for edit in changes) for item in matches)
        (automatic if covered else required).append(issue)
    required_manual = [item for item in manual if item.get("priority") == "P0" and not (
        item.get("rule_id") == "A14-missing-input" and any(
            issue.get("code") == "missing_input" and issue.get("file") == item.get("file") for issue in required))]
    optional = [item for item in manual if item.get("priority") != "P0"]
    summaries = []
    vendor = [c for c in changes if str(c.get("rule_id", "")).startswith("ADO-")]
    if vendor or copies:
        packages = sorted({c.get("package") for c in copies if c.get("package")})
        detail = (f"Copy {len({c.get('path') for c in copies})} distinct dependency files into your prepared replication dataset and update {len(vendor)} "
                  "code references, so these add-ons can load from the replication dataset.")
        if packages:
            detail += " Includes " + ", ".join(packages) + "."
        summaries.append({"title": "Include the Stata add-ons your code needs", "detail": detail})
    labels = {"B11-rmd-chunk-in-r": "Remove Markdown formatting from the R script",
              "B9-suppressed-data-load": "Make data-loading messages visible"}
    counts = Counter(labels.get(c.get("rule_id"), "Make the planned code adjustments")
                     for c in changes if c not in vendor)
    for label, count in counts.items():
        summaries.append({"title": label, "detail": f"{count} line adjustment{'s' if count != 1 else ''}. You can inspect every change below."})
    return {"schema_version": 1, "automatic": automatic, "required": required,
            "required_manual": required_manual, "optional": optional, "change_summaries": summaries,
            "requires_approval": bool(changes or copies) and not plan.get("safe_auto_apply", False)}


def preparation_explanation(changes: Any, copied_files: Any) -> dict[str, Any]:
    """Explain an applied plan without claiming scientific equivalence.

    This summarizes recorded operations, not a comparison with the author's
    results. Unknown operations never inherit the known packaging assurances.
    Deduplicate displayed copy evidence while retaining the full apply record.
    """
    edits = [_record(c) for c in changes]
    copies = list({(c['path'], c.get('sha256')): c for c in map(_record, copied_files)}.values())
    descriptions = {
        'ADO-external_adopath': (
            'Use add-ons included with the replication dataset',
            'Updated add-on search paths to the prepared replication dataset.',
            'The scripts can find their Stata add-ons without relying on a folder on your computer.'),
        'ADO-ssc_install': (
            'Keep the required add-ons available for every run',
            'Replaced installation during the analysis with the packaged add-on files.',
            'The analysis no longer needs to download this add-on each time it runs.'),
        'B9-suppressed-data-load': (
            'Make input problems visible',
            'Removed the quietly prefix from data-loading commands.',
            'A data-loading message is visible instead of being suppressed.'),
        'B11-rmd-chunk-in-r': (
            'Make the R script readable by R',
            'Removed Markdown formatting from the R script by commenting out standalone chunk fences.',
            'R can parse the script; the analysis commands inside the fences remain in place.'),
    }
    known = all(c.get('rule_id') in descriptions for c in edits)
    rules = list(dict.fromkeys(c.get('rule_id') for c in edits))
    principles = [{'title': descriptions[r][0], 'purpose': descriptions[r][2]} for r in rules if r in descriptions]
    if any(str(r).startswith('ADO-') for r in rules):
        principles = [{'title': descriptions[r][0], 'purpose': descriptions[r][2]}
                      for r in rules if r in descriptions and not str(r).startswith('ADO-')]
        principles.insert(0, {'title': 'Make the replication dataset independent of your computer',
                              'purpose': 'Use the included Stata add-ons instead of personal folder paths or downloads during the analysis.'})
    if copies and not any(str(r).startswith('ADO-') for r in rules):
        principles.append({'title': 'Keep a copy of the required dependencies',
                           'purpose': 'Include the dependency files selected by the approved plan so the prepared replication dataset can use them.'})
    if not known:
        principles.append({'title': 'Apply only the reviewed plan',
                           'purpose': 'The remaining edits are listed with their recorded reasons. Review their intended effect before certification.'})
    if not edits and not copies:
        scope = 'No file changes were needed.'
        impact = 'Preparation checked the replication dataset without editing its files.'
    elif known and edits and all(str(c.get('rule_id', '')).startswith('ADO-') for c in edits):
        scope = 'We changed how your scripts find their Stata add-ons.'
        impact = ('The recorded edits change add-on paths and installation steps, not data values or statistical commands. '
                  'The packaged add-on versions can still affect results; preparation has not compared them with your original run.')
    elif known and not copies:
        scope = 'We made the code adjustments listed below.'
        impact = ('These edits are intended to preserve the analysis commands while fixing script formatting or making loading messages visible. '
                  'Preparation has not compared results with your original run.')
    else:
        scope = 'We applied the approved changes to a separate copy.'
        impact = 'Review the purposes below. Preparation alone does not establish that these changes preserve your original results.'
    files = []
    for file in dict.fromkeys(c['file'] for c in edits):
        file_edits = [c for c in edits if c['file'] == file]
        explanations = []
        for rule in dict.fromkeys(c.get('rule_id') for c in file_edits):
            matching = [c for c in file_edits if c.get('rule_id') == rule]
            if rule in descriptions:
                title, change, purpose = descriptions[rule]
            else:
                title, change, purpose = 'Reviewed adjustment', 'Applied the recorded line changes.', '; '.join(dict.fromkeys(c.get('reason') or 'No purpose was supplied for this edit.' for c in matching))
            explanations.append({'change': change, 'purpose': purpose})
        files.append({'file': file, 'explanations': explanations, 'edits': file_edits})
    dependency_groups = []
    for package in dict.fromkeys(c.get('package') or 'Dependency files' for c in copies):
        members = [c for c in copies if (c.get('package') or 'Dependency files') == package]
        dependency_groups.append({'package': package, 'file_count': len(members), 'files': members,
                                  'change': f'Included {len(members)} distinct dependency files.',
                                  'purpose': 'These are the add-on code and accompanying files used by the prepared scripts.'})
    if not edits and not copies:
        summary = 'No file changes were needed.'
        result_note = 'You can now start the closure runs and certification.'
    elif known and edits and all(str(c.get('rule_id', '')).startswith('ADO-') for c in edits):
        summary = 'We included the Stata add-ons your scripts need, so they can run from this replication dataset.'
        result_note = ('Data and analysis commands were not edited. Add-on versions may affect results; '
                       'we have not compared them with your original run.')
    elif known and not copies:
        summary = ('We made the R script readable by R in a separate copy.' if rules == ['B11-rmd-chunk-in-r']
                   else 'We made data-loading messages visible in a separate copy.' if rules == ['B9-suppressed-data-load']
                   else 'We adjusted script formatting and loading messages in a separate copy.')
        result_note = 'The edits are intended to preserve your analysis. Results have not been compared with your original run.'
    else:
        summary = 'We applied the approved changes to a separate copy.'
        result_note = 'Their effect on your results has not been verified. Review the details below.'
    file_summary = (f'{len(files)} script' + ('s' if len(files) != 1 else '') + ' adjusted') if files else 'No existing scripts edited'
    if copies:
        file_summary += f'; {len(copies)} distinct dependency files included'
    return {'schema_version': 1, 'summary': summary, 'result_note': result_note, 'file_summary': file_summary + '.', 'scope': scope, 'impact': impact, 'principles': principles,
            'verification': 'Next, two closure runs check readiness. The certified run then records the outputs. It does not compare the results with your paper or a previous original run.',
            'original': 'Your original folder is unchanged.', 'files': files, 'dependencies': dependency_groups,
            'counts': {'edited_files': len(files), 'line_changes': len(edits), 'included_files': len(copies)}}
