# ReproAI Prep

**An author-facing pre-diagnose tool for replication packages.** Run it on your own
replication package *before* you submit, so the downstream reproducibility check passes on
the first try instead of bouncing back through round after round of fixes.

ReproAI Prep is a [Claude Code](https://docs.claude.com/en/docs/claude-code) / OpenAI Codex plugin.
A deterministic engine decides what is wrong; the host LLM explains it, drafts the fixes, and —
only when you ask — runs the package as a smoke test. Website: [reproai.org](https://reproai.org).

> **ReproAI Prep is one of two components.** ReproAI Prep *prepares* a replication package
> (this repository); **ReproAI Cert** then *certifies* the prepared package — closing the
> computation, running one traced certification run, and issuing a signed reproducibility
> certificate. The two are hot-swappable, independently versioned components under the ReproAI
> brand: you can use Prep without Cert, or Cert on any package that meets its input contract.

## What it does

You point it at a messy replication package (Stata / R / Python). It:

1. **Scans, statically** — file inventory, dependency graph, table↔command mapping, orphan
   files, an author rule set, and a target-venue profile (AEA, Econometric Society, JASA, World Bank, APSR, AJPS, JOP, …).
2. **Advises, by priority** — every finding is graded **P0–P4** by its downstream
   reproducibility cost (P0 = blocks the run; P4 = polish) and tagged **defect** ("this would
   cost the pipeline") vs **normalization** ("a more standard way to write it"). Each finding
   ships a self-contained fix prompt: the problem, why it hurts downstream, the target form,
   and the lossless boundary for the fix.
3. **Fixes, on a copy** — the host LLM rewrites a *copy* of your package under a
   semantics-preserving contract (your original is never touched), re-checks, and iterates
   until the findings clear. You review the diff.
4. **Smoke-tests, on request** — optionally runs the fixed copy to confirm it executes and
   that the table/figure outputs actually appear. On a runtime error it does **not** auto-fix:
   it explains the root cause, offers options, and asks you to decide.

> **Trust boundary.** ReproAI never compares your coefficients to the paper and never issues a
> "reproducible / certified" verdict — that is a separate downstream step. The static commands
> (`check` / `comply` / `fix`) do not execute your code; only the opt-in `debug` command runs
> it, and only as a smoke test (does it run, did the outputs appear).

## Commands

| Command | What it does |
|---|---|
| `/reproai:check` | One-shot static pre-diagnose → 4 JSON reports (architecture, advisory, venue compliance, risk register). |
| `/reproai:comply` | Just the target-journal replication-package checklist (AEA, …). |
| `/reproai:fix` | Apply the advisory fixes to a **copy** under a lossless contract; re-check; iterate. Chain: **A12 → N2 → D1** (anchor table comments → unroll loops → export per-table outputs). |
| `/reproai:debug` | Smoke-test the (fixed) copy: run it, confirm injected table/figure outputs appear; ask the author on a runtime error. |
| `/reproai:map` | **Advisory** overlay of the manuscript's figures/tables on the package's outputs (exhibits with no output, outputs with no exhibit, panel mismatches). LaTeX; never runs code; not part of `check`. |
| `/reproai:update` | Show the installed knowledge version and how to update the rule set. |
| `/reproai:contribute` | File a pre-filled GitHub issue for a missed rule, a false flag, or a new venue + its rules. You click Submit; reproai never posts. |

## What it checks (rule set)

45 author-preventable rules across four families, each with a fix prompt and a per-rule
lossless boundary:

- **Structural** — explicit data loads, stable includes, no mid-script `cd`, intermediate-data
  hygiene (`data/` + existence guards), explicit multi-script run order, per-table `→ Table N`
  anchor comments, per-table/figure output export, per-file documentation.
- **Code-style** — visible data-load failures, balanced table-output calls, no embedded
  foreign code, no cross-script `clear all`.
- **Environment** — vendored / `ssc install`-ed user commands, declared Stata/package
  versions, modern merge syntax, no removed R packages.
- **Venue compliance** — README/forms/structure against the target journal's standard.

The rules distill recurring patterns from a large body of real replication work; the published
rule set is generic guidance and names no specific paper.

## Install

ReproAI has two parts: the **plugin** (the slash commands) and a small **Python engine, 3.10+**
(`reproai` CLI) that the commands call and that holds the rules and venue profiles. Install both.

**Install or update with your AI assistant:** an AI assistant can install *or update* ReproAI by
fetching `https://raw.githubusercontent.com/reproai/reproai/master/INSTALL_FOR_AI.md` and following
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
core/                 the deterministic Prep engine (line1_core) + rules + venue profiles + schemas
tools/                maintainer tooling (build the public bundle, promote rules, bump version)
site/                 the reproai.org website
```

The certification component lives in a separate repository (**ReproAI Cert**); this repository
is Prep only.

## License

MIT — see [LICENSE](LICENSE).

## Recommended reading

We recommend Yusaku Horiuchi's [Replication Package Guide](https://github.com/yhoriuchi/replication-package-guide), a comprehensive guide for social science researchers, as a complementary read.
