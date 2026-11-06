---
name: reproai-prepare
description: The whole preparation in one pass, from a messy replication folder to a prepared copy with every approved repair recorded, a rehearsal run on a copy (with permission), and a handoff for the destination (a journal's check, a repository, or IQSS Certify); for Certify, it then offers to lead the author to the draft dataset's Certify button. Use when an author wants their package made ready, not only diagnosed.
---

# reproai prepare — from a folder to a prepared copy and a handoff (Codex)

Run the whole preparation, from a messy folder to a prepared copy and a handoff, following
`PREP_PROMPT.md` at the root of the ReproAI Prep repository (also at
https://raw.githubusercontent.com/reproai/reproai/main/PREP_PROMPT.md). In short:

0. **Ground.** Find the folder, the languages, the journal (`--venue`), and whether IQSS Certify
   will certify it: yes (then every command takes `--target certify`), no, or not sure (prepare for
   the journal only, and offer Certify at Step 6). Make a work folder and copy the package to
   `<work>/<name>-prepared` (`<name>`: the package folder's name); never touch the original. If the
   form or the README says the data are confidential, ask which kind. If the package has Stata
   scripts and Certify is in view, say now that Certify 0.2.0 runs R and Python only; leaving them out
   is the author's choice, never recommended for a script that produces a reported result.
1. **Check** (static): `reproai check <work>/<name>-prepared --venue <venue> [--target certify] --out <work>/reports`.
   Summarize by priority and, with the target, give the readiness status as a prediction.
2. **Run order.** Show the proposed order (`reproai handoff <work>/<name>-prepared` prints it: every
   script nothing else calls, Stata included) and get a yes; if the README gives another order, the
   author chooses.
3. **Repairs**, P0 first, each shown as before/after lines and applied only after the author agrees,
   to the prepared copy; record each with
   `reproai note <work>/<name>-prepared --change "<one sentence>" --approved-by "<author>"`. Re-check
   until no P0 remains, or until each P0 left is one the author chose to keep. If the author asked
   that nothing be changed, make no repairs: hand over the reports and go on with Steps 4 and 5.
4. **Rehearse** (runs code, on a copy; ask first; skip it if the author said not to run the code):
   `reproai rehearse <work>/<name>-prepared --script <first> ... --out <work>/rehearsal.json`.
   On a failure or a `different` grade, explain the cause, offer two to four repairs, let the author
   choose, record, rehearse again.
5. **Handoff**:
   `reproai handoff <work>/<name>-prepared --venue <venue> [--target certify] --script ... [--rehearsal <work>/rehearsal.json] --out <work>/handoff`
   (`--rehearsal` only if Step 4 ran). Show `HANDOFF.md` and say where the prepared copy is. Without
   `--target certify`, and unless the author was not sure about Certify, stop here.
6. **The way into IQSS Certify** (with `--target certify`, or when the author was not sure;
   `PREP_PROMPT.md` Step 6): `reproai certify-start <work>/<name>-prepared --out <work>/handoff`
   checks that Certify can start and writes `CERTIFY_START.md`, the author's steps from the draft
   dataset's Certify button. Add `--no-changes` if the author asked that nothing be changed. If the
   machine is offline or the network checks are blocked, run it with `--offline` and say that the
   service and Certify's published files were not checked. Before the question:
   - **Not sure:** say in two sentences what Certify gives (a certificate on the dataset's page that
     the results came from the exact files deposited; during the beta it sits on Dataverse's test
     site, apart from the journal's deposit) and takes (a repository account, three runs of the
     scripts on this computer, about five minutes and a wait of one to three hours). On
     `not_ready`, offer to go back to Step 3 with `--target certify`.
   - **The author declined the rehearsal or said not to run the code:** say that Certify runs the
     scripts on this computer three times, and do not mark Start now as recommended.
   - **`not_ready`** (exit 1): do not offer to start. Say what stops it. Offer to go back only where
     that could clear it (a repair the author has not declined, Step 3; the rehearsal, Step 4, if
     the author allows running the code). If it is something the author chose to keep, such as a
     Stata script, say Certify cannot start on this copy until that changes, and stop.
   - **Otherwise** (with `attention`, list the unticked checks first): ask one numbered question,
     "Start IQSS Certify now? 1. Start now (say recommended unless the author declined running the
     code): I walk you to your draft dataset's Certify button, then continue here under Certify's
     own instructions. 2. Just the steps (`CERTIFY_START.md`, for later or another chat). 3. Not
     now.", and wait for the answer.
   - **Start now**: give `CERTIFY_START.md`'s steps one at a time, up to and including filling in
     the copied form (the prepared copy as the folder, and the "Do not change any of my files" box
     as `CERTIFY_START.md` says), offering a title, authors, a one-paragraph description and a
     subject for the draft, drafted from the README (ask for what it does not say). Wait for the
     author to paste the filled form. Then say in one line "From here Certify's own instructions
     apply; ReproAI Prep stops here", fetch and follow
     https://certify.iq.harvard.edu/CERTIFY_PROMPT.md exactly (its checksum checks first), with the
     prepared copy as the replication dataset's folder. Run no `reproai` command after that, and keep
     the form's secret only where Certify's instructions put it. You may still say whether the run
     order Certify's Step 1 lists matches the one the author approved in Step 2.
   - **Just the steps** or **Not now**: say where `CERTIFY_START.md` is, and stop.

If `reproai` is not on PATH, run the repository's engine:
`PYTHONPATH="${REPROAI_CODEX_ROOT}/core/src" python3 -m reproai_prep.cli ...`. If it answers that a
command used here is unknown (an engine older than these skills), update the clone and the engine
first: `git -C "$REPROAI_CODEX_ROOT" pull && python3 -m pip install -e "$REPROAI_CODEX_ROOT/core"`.
Never stand in for a missing command by doing its checks yourself.

ReproAI Prep itself never runs a certification service's steps: once the author pastes Certify's
form, you work under Certify's instructions, not these. Never modify the original, never change what
the code computes, and never say the package reproduces or is certified.
