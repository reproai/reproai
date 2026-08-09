#!/usr/bin/env bash
# Install the reproai Codex adapter: make the skills discoverable, register the marketplace,
# and export REPROAI_CODEX_ROOT so the bundled engine is found. Idempotent.
set -euo pipefail

CODEX_PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CODEX_PLUGIN_DIR/.." && pwd)"   # repo root holds the shared core/ engine

echo "reproai Codex adapter"
echo "  repo root:   $REPO_ROOT"
echo "  codex plugin: $CODEX_PLUGIN_DIR"

# 1. Skills: link this adapter's skills into the user's Codex skill path.
SKILLS_SRC="$CODEX_PLUGIN_DIR/.agents/skills"
SKILLS_DST="$HOME/.agents/skills"
mkdir -p "$SKILLS_DST"
for skill in "$SKILLS_SRC"/reproai-*; do
  name="$(basename "$skill")"
  ln -sfn "$skill" "$SKILLS_DST/$name"
  echo "  linked skill: $name"
done

# 2. Engine: export REPROAI_CODEX_ROOT so SKILL.md's bundled-core fallback resolves.
#    (Best: `pip install -e core` so the `reproai` CLI is on PATH directly.)
PROFILE_LINE="export REPROAI_CODEX_ROOT=\"$REPO_ROOT\""
SHELL_RC="${HOME}/.$(basename "${SHELL:-bash}")rc"
if [ -f "$SHELL_RC" ] && ! grep -qF "REPROAI_CODEX_ROOT" "$SHELL_RC"; then
  echo "$PROFILE_LINE" >> "$SHELL_RC"
  echo "  added REPROAI_CODEX_ROOT to $SHELL_RC"
fi
export REPROAI_CODEX_ROOT="$REPO_ROOT"

# 3. Marketplace: register this repo's plugin so `codex plugin install reproai` works.
MARKET_DIR="$HOME/.agents/plugins"
mkdir -p "$MARKET_DIR"
echo "  marketplace dir: $MARKET_DIR (run: codex plugin marketplace add $REPO_ROOT)"

echo
echo "Done. To use the engine directly, also run:  pip install -e \"$REPO_ROOT/core\""
echo "Then in Codex: ask for /reproai-check (or invoke the reproai-check skill)."
