# Prepare a Replication Package with ReproAI Prep

Instructions for an AI assistant (Claude Code, Codex, or any assistant that can run commands). The
author may hand you `PREP_INTAKE.txt` filled in, paste its text, or give you no form at all.
Anything missing you ask for, one short question at a time. Follow this document; where it says
stop, stop and ask the author.

ReproAI Prep (Leo Yang Yang and Yiqing Xu) prepares a replication package so it runs from scratch on
a clean machine and meets its destination's entry requirements: a journal's own reproducibility
check, a repository, or IQSS Certify. It ends at a **prepared copy** and a **handoff**; for IQSS
Certify it then leads the author to Certify's own entry and steps back. It never compares results
to the paper, never says a package "reproduces", and never performs a certification service's own
steps.

## What you must not do

- **Never modify the author's original folder.** All work happens in a prepared copy.
- **Never change a computation, a seed, a data value or an output** to make something pass. A
  repair makes the code run as the author intended; if a script cannot run without changing the
  analysis, leave it out of the run order, say so in the notes, and report it to the author.
- **Every change is approved first.** Show the author the exact before and after lines and wait
  for a yes. Record each approved change with `reproai note` (Step 3).
- **Do not run the author's code** unless the form allows it and the author says yes at Step 4.
- **Do not run a certification service's commands** (`certify vendor`, `restrict`, `declare`,
  `record`, `close`, ...) under these instructions. If the author starts IQSS Certify at Step 6,
  they paste Certify's form and you follow Certify's own instructions from then on, not these.
- Never write a token or password into a file or a command line.

## Step 0. Read the form and check the ground

1. Confirm the folder exists and list its top level. Work out the languages from the file names
   (`.R`/`.r` R, `.py` Python, `.do` Stata) and read the README for the title and the run order.
2. Install the engine if `reproai --version` does not answer, and update it the same way if it
   answers that a command used below is unknown (an engine older than these instructions):
   `python3 -m pip install -U reproai-prep` (the stable release; Python 3.10 or newer). If a command is still
   unknown after that, these instructions are newer than the stable release: install the development
   version, `python3 -m pip install -U "git+https://github.com/reproai/reproai#subdirectory=core"`.
   Report the version. Never stand in for a missing command by doing its checks yourself.
3. Make a work folder outside the package (the form's, or `~/replication-prep/<name>-<date>/`) and
   copy the package into it as `<work>/<name>-prepared` (`<name>` is the package folder's name; IQSS
   Certify names its own work folder after the folder it is given). Say which folder you are making
   in your first progress line.
4. If the form says the data are confidential (or the README says restricted, licensed, or in a
   secure facility), ask which kind: (a) restricted: the repository may hold but not publish them;
   (b) licensed: the author may not deposit them; (c) in a secure facility. Record the answer.
5. If the package will be certified by IQSS Certify, every `reproai` command below takes
   `--target certify`. Certify 0.2.0 runs R and Python only: if the package has Stata scripts, say
   so now; the journal-side preparation still applies. Whether to leave them out of the copy is the
   author's choice: never recommend it for a script that produces a reported result, which the
   journal's deposit needs. If the form says **not sure**, prepare for
   the journal only (no `--target certify`) and offer Certify as an option at Step 6.

## Step 1. The static check

```bash
reproai check <work>/<name>-prepared --venue <venue> [--target certify] --out <work>/reports
```

Nothing runs. Read the reports and summarize for the author by priority (P0 blocks the run, P1 a
large downstream cost, P2 moderate, P3 minor, P4 polish; do not change a priority), and say which
items are defects and which are normalizations. With `--target certify`, give the readiness
status from `target_readiness_report.json` and each finding's effect at Certify (refuse, run
fails, mark, warning, note), as a prediction, never as Certify's verdict. Show the venue items the
engine cannot verify (`needs_author_action`) as a separate checklist.

## Step 2. Propose the run order

Show the order the engine proposes (`reproai handoff <work>/<name>-prepared` prints it: every script
nothing else calls, in path order, Stata included) in plain words, and wait for a yes. If the README describes
another order, or slow scripts whose results are saved, present the choice; the author decides.
Use the approved order everywhere below, one `--script` per script.

## Step 3. Repairs, only with approval

If the form says "do not change any of my files", make no repairs and hand the author the
reports, then go on with Step 4 (unless the form also says "do not run my code") and Step 5 on the
unchanged copy; at Step 6, if the package goes to IQSS Certify or the form says not sure, pass
`--no-changes`.

Otherwise, starting with P0: for each finding, read its `fix_prompt`, propose the smallest change
that fixes it without changing what the code computes, show the before and after lines, and wait.
Apply approved changes to `<work>/<name>-prepared` only. `reproai fix <work>/<name>-prepared --venue <venue>
[--target certify]` lists the edits the engine considers auto-safe, as a diff; show them like any
other change. After each approved change:

```bash
reproai note <work>/<name>-prepared --change "<the change, in one sentence>" --approved-by "<author>" \
  --dataset "<title>" --version "<version or draft>"
```

This keeps `CERTIFICATION-NOTES.txt` in the prepared copy, the record IQSS Certify asks for and a
journal's data editor reads. Re-run Step 1 until no P0 remains, or until each P0 left is one the
author chose to keep; say which, and go on.

## Step 4. Rehearse (runs code; ask first)

Skip this step if the form says "do not run my code". Otherwise explain in one sentence what it
does and ask:

```bash
reproai rehearse <work>/<name>-prepared --script <first> --script <second> ... --out <work>/rehearsal.json
```

It copies the prepared copy again and runs that copy twice, from its root, the way a certification
service will: no network, a private empty home folder, UTC and the C.UTF-8 locale, figures to
files only, each step's random generator seeded. Report what it says, including how the network
was denied (`proxy` means only by proxy settings). On a failed step, read its `tail` and `hints`,
state the root cause in one or two sentences, offer two to four repairs with their trade-offs, and
let the author choose; apply, record with `reproai note`, and rehearse again. If two runs
`different`, name the files that changed and whether a change looks like a clock reading, and
propose the fix for its cause the same way. Stata scripts are not rehearsed; say so.

## Step 5. The handoff

```bash
reproai handoff <work>/<name>-prepared --venue <venue> [--target certify] --script <first> ... \
  [--rehearsal <work>/rehearsal.json] --out <work>/handoff
```

Pass `--rehearsal` only if Step 4 ran.

Show the author `HANDOFF.md`: the approved run order, the libraries the scripts load, what is
still open, files read from outside the package, calls to outside services, and the next steps for
the destination. Tell the author where the prepared copy is. Unless the package goes to IQSS
Certify or the form says not sure, stop here.

## Step 6. The way into IQSS Certify (with `--target certify`, or when the form says not sure)

IQSS Certify is not started by a command. The author presses **Certify** on a draft dataset in the
repository (Edit Dataset, then Configure Options); that page gives a form with the archive's address,
the dataset's identifier and a time-limited secret for that one draft, which the author pastes into
an AI assistant. First check that Certify can start:

```bash
reproai certify-start <work>/<name>-prepared --out <work>/handoff
```

It checks the static readiness, that the copy holds no Stata files (Certify 0.2.0 stops on any
`.do` file), the runtimes the scripts need, a Python 3.12 or newer for Certify's own program, that
the service answers, and that Certify's two published checksum lists agree and still match what
ReproAI Prep's Certify rules were read from. It writes `CERTIFY_START.md`, the author's steps, and
exits 1 when Certify cannot start yet. It judges the copy against Certify's rules even when the
preparation did not use them. If the machine is offline or your host blocks its network checks, run
it again with `--offline` and tell the author that the service and Certify's published files were
not checked.

Before the question, say what the form's answers change:

- **Not sure about Certify:** say in two sentences what Certify gives and takes: a certificate on
  the dataset's page that the results were produced from the exact files deposited; it needs an
  account at the repository, runs the scripts on this computer three times, and takes about five
  minutes of the author's time and a wait of one to three hours. While Certify is in beta the
  certificate sits on Dataverse's test site, apart from the deposit the journal asks for. If
  `certify-start` says `not_ready`, say what Certify would need and offer to go back to Step 3 with
  `--target certify`.
- **"Do not run my code":** Certify runs the scripts on this computer three times (two practice
  runs and the certified run). Say so plainly, and do not mark Start now as recommended; the author
  chooses again.
- **"Do not change any of my files":** pass `--no-changes`. `CERTIFY_START.md` then tells the author
  to tick the same box in Certify's form, so that Certify stops and reports instead of proposing
  repairs.

- **Cannot start yet** (`not_ready`): do not offer to start. Say what stops it, in plain words.
  Offer to go back only where that could clear it: to a repair the author has not declined (Step 3),
  or to the rehearsal (Step 4) if the form allows running the code. If what stops it is something the
  author chose to keep, such as a Stata script, say that Certify cannot start on this copy until that
  changes, and stop.
- **Otherwise** (`ready`, or `attention`, whose unticked checks you list first): ask one question,
  "Start IQSS Certify now?", with three answers: **Start now** (recommended unless the form said
  "do not run my code": you walk the author to
  the draft's Certify button and continue in this chat under Certify's instructions), **Just the
  steps** (`CERTIFY_START.md`, for later or for another chat), **Not now**. Use your host's question
  tool if it has one (in Claude Code, AskUserQuestion); otherwise ask it as a numbered question.
- **Start now.** Give the steps of `CERTIFY_START.md` one at a time, up to and including filling in
  the copied form (the prepared copy as the folder, and the "Do not change any of my files" box as
  `CERTIFY_START.md` says). For the draft dataset, offer a title ("Replication Data for: <the
  paper's title>"), the authors, a one-paragraph description and a subject, drafted from the README
  for the author to copy; ask for what the README does not say. Then wait for the filled form. When
  the author pastes it, say in one line: "From here Certify's own instructions apply; ReproAI Prep stops here."
  Fetch and follow https://certify.iq.harvard.edu/CERTIFY_PROMPT.md exactly, starting with its own
  checksum checks, with the prepared copy as the replication dataset's folder. After that, run no
  `reproai` command, and keep the form's secret only where Certify's instructions put it. One thing
  you may still say: when Certify's Step 1 lists the scripts it would run, whether that order matches
  the one the author approved in Step 2.
- **Just the steps** or **Not now**: say where `CERTIFY_START.md` is, and stop.

## Deliverables

- `<work>/<name>-prepared`: the prepared copy, with `CERTIFICATION-NOTES.txt` listing every approved
  change (there is no notes file when nothing was changed)
- `<work>/reports`: the static check's reports
- `<work>/rehearsal.json`: the rehearsal, if the author allowed it
- `<work>/handoff/HANDOFF.md` and `handoff.json`
- For IQSS Certify, or when the form says not sure: `<work>/handoff/CERTIFY_START.md` and `certify_start.json`
