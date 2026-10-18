#!/bin/bash
# Untested on a clean machine. Do not run it on a machine that already has a working ai-env: it replaces the symlinks.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ENVDIR="${MAKI_ENV:-$HOME/.maki-env}"
command -v ollama >/dev/null || { echo "Ollama not found: https://ollama.com"; exit 1; }
[ -d "$ENVDIR" ] || python3 -m venv "$ENVDIR"
"$ENVDIR/bin/pip" install -q -r "$HERE/requirements.txt"
mkdir -p "$HOME/.local/bin"
ln -sf "$HERE/bin/ai-env" "$HOME/.local/bin/ai-env"
ln -sf "$HERE/bin/maki-aider" "$HOME/.local/bin/maki-aider"
[ -f "$HOME/.ollama-env" ] || cp "$HERE/config/ollama-env.example" "$HOME/.ollama-env"
if [ "${1:-}" = "--models" ]; then
  ollama pull qwen2.5-coder:7b
  ollama pull qwen3:4b
  ollama pull nomic-embed-text
  ollama create qwen-coder-8k -f "$HERE/modelfiles/coder.Modelfile"
fi
echo "Done. Add to your shell profile: export MAKI_HOME=$HERE"
