---
name: reproai-prepare
description: The whole preparation in one pass, from a messy replication folder to a prepared copy with every approved repair recorded, a rehearsal run on a copy (with permission), and a handoff for the destination (a journal's check, a repository, or IQSS Certify). Use when an author wants their package made ready, not only diagnosed.
---

# /reproai prepare — from a folder to a prepared copy and a handoff

Run the whole preparation, from a messy folder to a prepared copy and a handoff, following
`PREP_PROMPT.md` at the root of this plugin's repository (also at
https://raw.githubusercontent.com/reproai/reproai/main/PREP_PROMPT.md). In short:

1. **Ground.** Find the folder, the languages, the journal (`--venue`), and whether IQSS Certify
   will certify it (then every command takes `--target certify`). Make a work folder and copy the
   package to `<work>/prepared`; never touch the original. Ask which kind of confidential data, if
   any.
2. **Check** (static): `reproai check <work>/prepared --venue <venue> [--target certify] --out <work>/reports`.
   Summarize by priority and, with the target, give the readiness status as a prediction.
3. **Run order.** Show the proposed order (`reproai handoff <work>/prepared` prints it) and get a yes.
4. **Repairs**, P0 first, each shown as before/after lines and applied only after the author agrees,
   to the prepared copy; record each with
   `reproai note <work>/prepared --change "<one sentence>" --approved-by "<author>"`. Re-check until no P0.
5. **Rehearse** (runs code, on a copy; ask first):
   `reproai rehearse <work>/prepared --script <first> ... --out <work>/rehearsal.json`.
   On a failure or a `different` grade, explain the cause, offer two to four repairs, let the author
   choose, record, rehearse again.
6. **Handoff**, then stop:
   `reproai handoff <work>/prepared --venue <venue> [--target certify] --script ... --rehearsal <work>/rehearsal.json --out <work>/handoff`.
   Show `HANDOFF.md`. For IQSS Certify the next steps are Certify's own commands; never run them.

If `reproai` is not on PATH, run the bundled engine as `python3 -m reproai_prep.cli` with
`PYTHONPATH` set to the plugin's `core/src`.

Never modify the original, never change what the code computes, never run a certification
service's own steps, and never say the package reproduces or is certified.
