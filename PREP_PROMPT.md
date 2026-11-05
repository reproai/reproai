# Prepare a Replication Package with ReproAI Prep

Instructions for an AI assistant (Claude Code, Codex, or any assistant that can run commands). The
author may hand you `PREP_INTAKE.txt` filled in, paste its text, or give you no form at all.
Anything missing you ask for, one short question at a time. Follow this document; where it says
stop, stop and ask the author.

ReproAI Prep (Leo Yang Yang and Yiqing Xu) prepares a replication package so it runs from scratch on
a clean machine and meets its destination's entry requirements: a journal's own reproducibility
check, a repository, or IQSS Certify. It ends at a **prepared copy** and a **handoff**. It never
compares results to the paper, never says a package "reproduces", and never performs a
certification service's own steps.

## What you must not do

- **Never modify the author's original folder.** All work happens in a prepared copy.
- **Never change a computation, a seed, a data value or an output** to make something pass. A
  repair makes the code run as the author intended; if a script cannot run without changing the
  analysis, leave it out of the run order, say so in the notes, and report it to the author.
- **Every change is approved first.** Show the author the exact before and after lines and wait
  for a yes. Record each approved change with `reproai note` (Step 3).
- **Do not run the author's code** unless the form allows it and the author says yes at Step 4.
- **Do not run a certification service's commands** (`certify vendor`, `restrict`, `declare`,
  `record`, `close`, ...). The handoff names them; the author, or the service's own instructions,
  run them.
- Never write a token or password into a file or a command line.

## Step 0. Read the form and check the ground

1. Confirm the folder exists and list its top level. Work out the languages from the file names
   (`.R`/`.r` R, `.py` Python, `.do` Stata) and read the README for the title and the run order.
2. Install the engine if `reproai --version` does not answer:
   `python3 -m pip install reproai-prep` (Python 3.10 or newer). Report the version.
3. Make a work folder outside the package (the form's, or `~/replication-prep/<name>-<date>/`) and
   copy the package into it as `<work>/prepared`. Say which folder you are making in your first
   progress line.
4. If the form says the data are confidential (or the README says restricted, licensed, or in a
   secure facility), ask which kind: (a) restricted: the repository may hold but not publish them;
   (b) licensed: the author may not deposit them; (c) in a secure facility. Record the answer.
5. If the package will be certified by IQSS Certify, every `reproai` command below takes
   `--target certify`. Certify 0.2.0 runs R and Python only: if the package has Stata scripts, say
   so now; the journal-side preparation still applies.

## Step 1. The static check

```bash
reproai check <work>/prepared --venue <venue> [--target certify] --out <work>/reports
```

Nothing runs. Read the reports and summarize for the author by priority (P0 blocks the run, P1 a
large downstream cost, P2 moderate, P3 minor, P4 polish; do not change a priority), and say which
items are defects and which are normalizations. With `--target certify`, give the readiness
status from `target_readiness_report.json` and each finding's effect at Certify (refuse, run
fails, mark, warning, note), as a prediction, never as Certify's verdict. Show the venue items the
engine cannot verify (`needs_author_action`) as a separate checklist.

## Step 2. Propose the run order

Show the order the engine proposes (`reproai handoff <work>/prepared` prints it: every script
nothing else calls, in path order) in plain words, and wait for a yes. If the README describes
another order, or slow scripts whose results are saved, present the choice; the author decides.
Use the approved order everywhere below, one `--script` per script.

## Step 3. Repairs, only with approval

If the form says "do not change any of my files", stop here and hand the author the reports.

Otherwise, starting with P0: for each finding, read its `fix_prompt`, propose the smallest change
that fixes it without changing what the code computes, show the before and after lines, and wait.
Apply approved changes to `<work>/prepared` only. `reproai fix <work>/prepared --venue <venue>
[--target certify]` lists the edits the engine considers auto-safe, as a diff; show them like any
other change. After each approved change:

```bash
reproai note <work>/prepared --change "<the change, in one sentence>" --approved-by "<author>" \
  --dataset "<title>" --version "<version or draft>"
```

This keeps `CERTIFICATION-NOTES.txt` in the prepared copy, the record IQSS Certify asks for and a
journal's data editor reads. Re-run Step 1 until no P0 remains.

## Step 4. Rehearse (runs code; ask first)

Skip this step if the form says "do not run my code". Otherwise explain in one sentence what it
does and ask:

```bash
reproai rehearse <work>/prepared --script <first> --script <second> ... --out <work>/rehearsal.json
```

It copies the prepared copy again and runs that copy twice, from its root, the way a certification
service will: no network, a private empty home folder, UTC and the C.UTF-8 locale, figures to
files only, each step's random generator seeded. Report what it says, including how the network
was denied (`proxy` means only by proxy settings). On a failed step, read its `tail` and `hints`,
state the root cause in one or two sentences, offer two to four repairs with their trade-offs, and
let the author choose; apply, record with `reproai note`, and rehearse again. If two runs
`different`, name the files that changed and whether a change looks like a clock reading, and
propose the fix for its cause the same way. Stata scripts are not rehearsed; say so.

## Step 5. The handoff, then stop

```bash
reproai handoff <work>/prepared --venue <venue> [--target certify] --script <first> ... \
  --rehearsal <work>/rehearsal.json --out <work>/handoff
```

Show the author `HANDOFF.md`: the approved run order, the libraries the scripts load, what is
still open, files read from outside the package, calls to outside services, and the next steps for
the destination. For IQSS Certify, those are Certify's own commands (`certify targets`,
`certify vendor`, and when needed `restrict`, `declare`, `record`), then Certify's own
instructions from its registration step on. Tell the author where the prepared copy is, and stop.

## Deliverables

- `<work>/prepared`: the prepared copy, with `CERTIFICATION-NOTES.txt` listing every approved change
- `<work>/reports`: the static check's reports
- `<work>/rehearsal.json`: the rehearsal, if the author allowed it
- `<work>/handoff/HANDOFF.md` and `handoff.json`
