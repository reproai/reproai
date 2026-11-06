# ReproAI Prep — install instructions for an AI assistant

ReproAI Prep is an author-facing plugin that prepares replication packages (Stata / R / Python),
backed by a small Python engine. **This file is the install procedure for an AI assistant to run.**
Execute it deterministically: detect your host, run only that host's branch, then verify.

## Prerequisites

- **Python 3.10+** on PATH (`python3 --version`).
- **One host**: Claude Code **or** OpenAI Codex CLI.
- A shell you can run commands in.

## Step 1 — detect the host

Determine which host you are running inside, then follow ONLY that branch:

- **Claude Code** — you have `/plugin` slash commands. → use Branch A.
- **OpenAI Codex CLI** — you do not have `/plugin`; you install via the user's shell. → use Branch B.

If you cannot tell, ask the user which host this is. Do not run both branches.

## Step 2A — install in Claude Code

Run the first two commands **inside Claude Code** (slash commands), and the `pip` command in
**the user's shell**:

```
/plugin marketplace add reproai/reproai
/plugin install reproai@reproai                                          # plugin@marketplace
python3 -m pip install -U reproai-prep                                   # the engine (stable release), on PATH
```

- `/plugin marketplace add …` — runs in Claude Code. Success: the `reproai` marketplace is registered.
- `/plugin install reproai@reproai` — runs in Claude Code. Success: the `/reproai:*` commands appear.
- `python3 -m pip install …` — runs in the user's shell. Success: pip reports `reproai-prep` installed and `reproai --version` runs.
- Only if the user asks for the development version (the newest rules before they are released), install
  it from GitHub instead: `python3 -m pip install -U "git+https://github.com/reproai/reproai#subdirectory=core"`.

## Step 2B — install in OpenAI Codex CLI

Run all of these in **the user's shell**:

```
git clone https://github.com/reproai/reproai
cd reproai
./codex-plugin/install.sh   # links the reproai skills into ~/.agents/skills
python3 -m pip install -e core         # put the reproai engine on PATH
```

- `git clone …` — shell. Success: a `reproai/` directory exists.
- `cd reproai` — shell. Success: you are in the repo root.
- `./codex-plugin/install.sh` — shell. Success: it prints `linked skill: reproai-*` lines.
- `python3 -m pip install -e core` — shell. Success: pip reports the `reproai` engine installed (editable).

## Step 3 — verify

In **the user's shell**, confirm the engine is on PATH and importable:

```
reproai --version                                    # prints: reproai <version>
python3 -c "import reproai_prep; print('ok')"          # prints: ok
```

Then confirm the host has the commands:

- **Claude Code**: the `/reproai:check` command is listed/available (e.g. type `/reproai:` to see it).
- **Codex**: the `reproai-check` skill is available (linked under `~/.agents/skills/`).

If `reproai --version` is not found, the engine `python3 -m pip install` step did not complete — rerun it.

## Step 4 — stay current

ReproAI's rule set and venue profiles are **data that keeps evolving** as the downstream pipeline sees
more replication packages. A fresh install already ships the latest, so right after installing there is
nothing more to pull. But before a diagnose on an existing install, make sure you are current:

- Run `/reproai:update` (Claude Code) to **see** your installed versions — note that this command only
  reports; it does not change anything itself.
- To actually pull the latest rules + venue profiles, run the **Update** step below (the `python3 -m pip install -U`
  command refreshes the engine where the rules live).

## Update

Refresh **both** the plugin (commands) and the engine (rules + venue profiles).

**Claude Code** — first three inside Claude Code, last in the user's shell:

```
/plugin marketplace update reproai
/plugin update reproai          # latest commands
/reload-plugins
python3 -m pip install -U reproai-prep  # latest stable rules + venues
```

If the user runs the development version, update the engine with `python3 -m pip install -U "git+https://github.com/reproai/reproai#subdirectory=core"` instead.

**OpenAI Codex CLI** — in the user's shell (pull the repo, then):

```
reproai/codex-plugin/install.sh   # relink skills
python3 -m pip install -U -e reproai/core
```

---

Human install lives at https://reproai.org (Install section) and the README.
