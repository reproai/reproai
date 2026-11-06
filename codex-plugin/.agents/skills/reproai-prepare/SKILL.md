---
name: reproai-prepare
description: The whole preparation in one pass, from a messy replication folder to a prepared copy with every approved repair recorded, a rehearsal run on a copy (with permission), and a handoff for the destination (a journal's check, a repository, or IQSS Certify); for Certify, it then offers to lead the author to the draft dataset's Certify button. Use when an author wants their package made ready, not only diagnosed.
---

# reproai prepare — from a folder to a prepared copy and a handoff (Codex)

Run the whole preparation, from a messy folder to a prepared copy and a handoff, following
`PREP_PROMPT.md` at the root of the ReproAI Prep repository (also at
https://raw.githubusercontent.com/reproai/reproai/main/PREP_PROMPT.md). In short:

1. **Ground.** Find the folder, the languages, the journal (`--venue`), and whether IQSS Certify
   will certify it: yes (then every command takes `--target certify`), no, or not sure (prepare for
   the journal only, and offer Certify at step 7). Make a work folder and copy the
   package to `<work>/<name>-prepared` (`<name>`: the package folder's name); never touch the original. Ask which kind of confidential data, if
   any.
2. **Check** (static): `reproai check <work>/<name>-prepared --venue <venue> [--target certify] --out <work>/reports`.
   Summarize by priority and, with the target, give the readiness status as a prediction.
3. **Run order.** Show the proposed order (`reproai handoff <work>/<name>-prepared` prints it) and get a yes.
4. **Repairs**, P0 first, each shown as before/after lines and applied only after the author agrees,
   to the prepared copy; record each with
   `reproai note <work>/<name>-prepared --change "<one sentence>" --approved-by "<author>"`. Re-check until no P0.
5. **Rehearse** (runs code, on a copy; ask first):
   `reproai rehearse <work>/<name>-prepared --script <first> ... --out <work>/rehearsal.json`.
   On a failure or a `different` grade, explain the cause, offer two to four repairs, let the author
   choose, record, rehearse again.
6. **Handoff**:
   `reproai handoff <work>/<name>-prepared --venue <venue> [--target certify] --script ... --rehearsal <work>/rehearsal.json --out <work>/handoff`.
   Show `HANDOFF.md` and say where the prepared copy is. Without `--target certify`, and unless
   the author was not sure about Certify, stop here.
7. **The way into IQSS Certify** (with `--target certify`, or when the author was not sure;
   `PREP_PROMPT.md` Step 6): `reproai certify-start <work>/<name>-prepared --out <work>/handoff`
   checks that Certify can start and writes `CERTIFY_START.md`, the author's steps from the draft
   dataset's Certify button. Add `--no-changes` if the author asked that nothing be changed. Before
   the question:
   - **Not sure:** say in two sentences what Certify gives (a certificate on the dataset's page that
     the results came from the exact files deposited) and takes (a repository account, three runs
     of the scripts on this computer, about five minutes and a wait of one to three hours). On
     `not_ready`, offer to go back to step 4 with `--target certify`.
   - **The author declined the rehearsal or said not to run the code:** say that Certify runs the
     scripts on this computer three times, and do not mark Start now as recommended.
   - **`not_ready`** (exit 1): do not offer to start. Say what stops it and offer to go back to step 4 or 5.
   - **Otherwise** (with `attention`, list the unticked checks first): ask one numbered question,
     "Start IQSS Certify now? 1. Start now (say recommended unless the author declined running the code): I walk you to your draft dataset's Certify
     button, then continue here under Certify's own instructions. 2. Just the steps
     (`CERTIFY_START.md`, for later or another chat). 3. Not now.", and wait for the answer.
   - **Start now**: give `CERTIFY_START.md`'s steps one at a time, offering a title, authors, a
     one-paragraph description and a subject for the draft, drafted from the README. Wait for the
     author to paste the form from the Certify page. Then say in one line "From here Certify's own
     instructions apply; ReproAI Prep stops here", fetch and follow
     https://certify.iq.harvard.edu/CERTIFY_PROMPT.md exactly (its checksum checks first), with the
     prepared copy as the replication dataset's folder. Run no `reproai` command after that, and keep
     the form's secret only where Certify's instructions put it. You may still say whether the run
     order Certify's Step 1 lists matches the one the author approved in step 3.
   - **Just the steps** or **Not now**: say where `CERTIFY_START.md` is, and stop.

If `reproai` is not on PATH, run the repository's engine:
`PYTHONPATH="${REPROAI_CODEX_ROOT}/core/src" python3 -m reproai_prep.cli ...`. If it answers that a
command used here is unknown (an engine older than these skills), update the clone and the engine
first: `git -C "$REPROAI_CODEX_ROOT" pull && python3 -m pip install -e "$REPROAI_CODEX_ROOT/core"`.
Never stand in for a missing command by doing its checks yourself.

ReproAI Prep itself never runs a certification service's steps: once the author pastes Certify's
form, you work under Certify's instructions, not these. Never modify the original, never change what
the code computes, and never say the package reproduces or is certified.
