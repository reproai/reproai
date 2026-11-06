# ReproAI Prep

By Leo Yang Yang and Yiqing Xu.

**An author-facing pre-diagnose tool for replication packages.** Run it on your own
replication package *before* you submit, so the downstream reproducibility check passes on
the first try instead of bouncing back through round after round of fixes.

ReproAI Prep is a [Claude Code](https://docs.claude.com/en/docs/claude-code) / OpenAI Codex plugin.
A deterministic engine decides what is wrong; the host LLM explains it, drafts the fixes, and —
only when you ask — rehearses a copy of the package the way a certification service will.
Website: [reproai.org](https://reproai.org).

## What it does

You point it at a messy replication package (Stata / R / Python). It:

1. **Scans, statically** — file inventory, dependency graph, table↔command mapping, orphan
   files, an author rule set, a target-venue profile (AEA, Econometric Society, JASA, World Bank, APSR, AJPS, JOP, …),
   and, if you are headed for certification, a certification-target profile (IQSS Certify).
2. **Advises, by priority** — every finding is graded **P0–P4** by its downstream
   reproducibility cost (P0 = blocks the run; P4 = polish) and tagged **defect** ("this would
   cost the pipeline") vs **normalization** ("a more standard way to write it"). Each finding
   ships a self-contained fix prompt: the problem, why it hurts downstream, the target form,
   and the lossless boundary for the fix.
3. **Fixes, on a copy** — the host LLM rewrites a *copy* of your package under a
   semantics-preserving contract (your original is never touched), re-checks, and iterates
   until the findings clear. You review the diff.
4. **Rehearses, on request** — runs a copy of the fixed package twice, the way a certification
   service will (from the root, no network, a private home, fixed locale and time zone, seeded
   generators), and compares the outputs. On a runtime error it does **not** auto-fix: it
   explains the root cause, offers options, and asks you to decide.
5. **Hands off** — a prepared copy with every approved change recorded in
   `CERTIFICATION-NOTES.txt`, and a handoff that names the run order, the libraries, what is
   still open, and the next steps for your destination. For IQSS Certify, it then checks that
   Certify can start and offers to walk you to your draft dataset's Certify button.

> **Trust boundary.** ReproAI Prep never compares your coefficients to the paper and never issues a
> "reproducible / certified" verdict — that is a separate downstream step. The static commands
> (`check` / `comply` / `fix` / `map`) do not execute your code; only the opt-in rehearsal
> (`debug`, `prepare` with your permission, or `reproai rehearse`) runs it, and only on a copy.

## Commands

| Command | What it does |
|---|---|
| `/reproai:prepare` | The whole preparation in one pass: check, approved repairs on a copy, rehearsal (with permission), handoff, and for IQSS Certify the way in. |
| `/reproai:check` | One-shot static pre-diagnose → 4 JSON reports (architecture, advisory, venue compliance, risk register), plus a certification-readiness report with `--target certify`. |
| `/reproai:comply` | Just the target-journal replication-package checklist (AEA, …). |
| `/reproai:fix` | Apply the advisory fixes to a **copy** under a lossless contract; re-check; iterate. Chain: **A12 → N2 → D1** (anchor table comments → unroll loops → export per-table outputs). |
| `/reproai:debug` | Rehearse the (fixed) copy with `reproai rehearse`: run it twice under certification-like settings, confirm the table/figure outputs appear and agree; ask the author on a runtime error. |
| `/reproai:map` | **Advisory** overlay of the manuscript's figures/tables on the package's outputs (exhibits with no output, outputs with no exhibit, panel mismatches). LaTeX; never runs code; not part of `check`. |
| `/reproai:update` | Show the installed knowledge version and how to update the rule set. |
| `/reproai:contribute` | File a pre-filled GitHub issue for a missed rule, a false flag, or a new venue + its rules. You click Submit; reproai never posts. |

## What it checks (rule set)

55 author-preventable rules across four families, each with a fix prompt and a per-rule
lossless boundary:

- **Structural** — explicit data loads, stable includes, no mid-script `cd`, intermediate-data
  hygiene (`data/` + existence guards), explicit multi-script run order, per-table `→ Table N`
  anchor comments, per-table/figure output export, per-file documentation.
- **Code-style** — visible data-load failures, balanced table-output calls, no embedded
  foreign code, no cross-script `clear all`.
- **Environment** — user-written commands vendored inside the package (no runtime
  `ssc install` / `install.packages`, no adopath outside the package), declared
  Stata/package versions, modern merge syntax, no removed R packages.
- **Venue compliance** — README/forms/structure against the target journal's standard.

The rules distill recurring patterns from a large body of real replication work; the published
rule set is generic guidance and names no specific paper.

## With any AI assistant

Fill in [`PREP_INTAKE.txt`](PREP_INTAKE.txt) and paste it into your assistant (Claude, Codex, or
another that can run commands). It points the assistant at [`PREP_PROMPT.md`](PREP_PROMPT.md),
which takes it through the same steps as `/reproai:prepare`: the static check, approved repairs
on a copy, a rehearsal if you allow it, the handoff and, for IQSS Certify, the way in. The
engine's commands are `reproai check`, `fix`, `rehearse`, `note`, `handoff` and `certify-start`.

## Preparing for IQSS Certify

[Certify](https://certify.iq.harvard.edu) certifies a replication dataset at publication. Its
closing refuses packages that break its entry contract, and some breaks only show after a long
run. `reproai check <ROOT> --target certify` checks that contract statically first: 24 rules
read from Certify 0.2.0's published program (Stata scripts, notebooks-only code, paths written
from a script's folder or pointing outside the dataset, network reads, outside services, startup
files, run-time installs, interactive calls, cluster launchers, seeding forms Certify cannot
re-map, socket and forked workers, missing output folders, file-tree problems, entry counts).
It also re-words the generic advice Certify contradicts (doRNG, install lines, outside files)
and writes `target_readiness_report.json`: `blocked`, `needs_attention` or
`no_static_obstacle`, each finding with the effect it has at Certify (refuse, run fails, mark,
warning, note).

Certify is started from your draft dataset in the repository: Edit Dataset, Configure Options,
Certify, and that page gives a form you paste into your AI assistant, which then follows Certify's
own instructions. After the handoff, `reproai certify-start <prepared copy>` checks that Certify can
start (the static readiness, no Stata files, the runtimes, a Python 3.12 or newer for Certify's
program, the service answering, Certify's published checksums agreeing and unchanged since these
rules were read) and writes `CERTIFY_START.md`, the steps; `/reproai:prepare` then asks whether to
start now and, if you paste the form, hands over to Certify's instructions in the same chat.

ReproAI Prep is independent of Certify and shares no code with it. It never installs or runs
Certify's program, never sees the form's secret, and never runs Certify's own steps (`vendor`,
`restrict`, `declare`, `record`, `close`). Certify's closing is the only authority on whether a
package closes.

## Install

ReproAI has two parts: the **plugin** (the slash commands) and a small **Python engine, 3.10+**
(`reproai` CLI) that the commands call and that holds the rules and venue profiles. Install both.

**Install or update with your AI assistant:** an AI assistant can install *or update* ReproAI by
fetching `https://raw.githubusercontent.com/reproai/reproai/main/INSTALL_FOR_AI.md` and following
it. The manual steps follow below.

**Claude Code**

```
/plugin marketplace add reproai/reproai
/plugin install reproai@reproai                                          # plugin@marketplace
python3 -m pip install "git+https://github.com/reproai/reproai#subdirectory=core"  # the engine, on PATH
```

Both install globally — then run `/reproai:check` in any project that contains your replication package.

**OpenAI Codex**

```
git clone https://github.com/reproai/reproai
cd reproai
./codex-plugin/install.sh   # links the reproai skills into ~/.agents/skills
python3 -m pip install -e core         # put the reproai engine on PATH
```

Then ask Codex for `/reproai-check` in any project.

## Update

Rules and venue profiles live in the engine, so refresh **both** the plugin (commands) and the engine.

**Claude Code**

```
/plugin marketplace update reproai
/plugin update reproai                                                      # latest commands
/reload-plugins
python3 -m pip install -U "git+https://github.com/reproai/reproai#subdirectory=core"  # latest rules + venues
```

**OpenAI Codex**

```
git -C reproai pull
reproai/codex-plugin/install.sh                                             # relink skills
python3 -m pip install -U -e reproai/core                                              # latest rules + venues
```

`/reproai:update` reports your installed version and these steps; it does not update anything itself.

## Layout

```
claude-plugin/        the Claude Code plugin (commands/, agents/, .claude-plugin/plugin.json)
codex-plugin/         the OpenAI Codex adapter (.agents/skills/, install.sh) over the same engine
core/                 the deterministic engine (reproai_prep) + rules + venue profiles + schemas
tools/                maintainer tooling (build the public bundle, promote rules, bump version)
site/                 the reproai.org website
```

## Citing

Leo Yang Yang and Yiqing Xu. 2026. "ReproAI Prep: Preparing Replication Packages for
Reproducibility Checks and Certification." Software, https://github.com/reproai/reproai.
Machine-readable metadata is in [CITATION.cff](CITATION.cff).

## License

MIT — see [LICENSE](LICENSE).

## Recommended reading

We recommend Yusaku Horiuchi's [Replication Package Guide](https://github.com/yhoriuchi/replication-package-guide), a comprehensive guide for social science researchers, as a complementary read.
