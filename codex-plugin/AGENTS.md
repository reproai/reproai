# ReproAI — Codex adapter

This is the OpenAI Codex adapter for **reproai**, an author-facing pre-diagnose tool for
replication packages. It is a thin host adapter over the SAME deterministic Python engine
(`core/`, the `reproai` CLI) that the Claude Code plugin uses — one engine, two adapters.

## What ships here

- `.agents/skills/reproai-*/SKILL.md` — the six workflows (recommended reusable layer):
  - `reproai-check` — static pre-diagnose → 4 JSON reports
  - `reproai-comply` — venue compliance checklist only
  - `reproai-fix` — LLM rewrites a COPY under a lossless contract; re-check; iterate (A12→N2→D1)
  - `reproai-debug` — smoke-test the fixed copy; ask the author on a runtime error
  - `reproai-map` — advisory overlay of manuscript exhibits on package outputs (LaTeX; outside check)
  - `reproai-update` — knowledge version + update path
- `.codex-plugin/plugin.json` — Codex plugin manifest
- `install.sh` — register the marketplace / link skills
- `codex-config.example.toml` — sandbox/approval defaults

## Engine (shared, not duplicated)

The engine lives at the repo's top-level `core/` and is invoked as `reproai check` / `reproai fix`,
or via the bundled core: `PYTHONPATH="${REPROAI_CODEX_ROOT}/core/src" python3 -m line1_core.cli ...`.
`${REPROAI_CODEX_ROOT}` is set by `install.sh` to this repo root. Nothing in the engine is
Codex-specific; the adapter only changes how commands are discovered and how the author is asked
a question.

## Trust boundary (same as the Claude adapter)

- The static skills (`check` / `comply` / `fix`) do not execute author code.
- `debug` runs the package only as a smoke test (does it run, did the outputs appear).
- reproai NEVER compares coefficients to the paper and NEVER issues a reproducibility verdict.

## Interaction (Codex specifics)

The only interactive workflow is `debug` (on a runtime error it asks the author to choose a fix).
Interaction is an adapter detail with graceful degradation:
- default: print a numbered options block, author replies next turn (works in `codex` and stops
  cleanly under `codex exec`);
- optional enhancement under the Codex app-server: `tool/requestUserInput`.
The engine itself stays interaction-agnostic — it emits diagnosis + options, never blocks on input.
