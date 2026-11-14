#!/usr/bin/env bash
# Start the backend with the DeepSeek key from Taimour's Atuin secrets. Teammates: export DEEPSEEK_API_KEY yourself.
set -e
cd "$(dirname "$0")"
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-$(PYTHONPATH="$HOME/.config/atuin_inventory/sources/lib" python3 -c 'from atuin_common import keys; print(keys.get("DEEPSEEK_API_KEY"))')}"
exec uv run uvicorn app:app --port 8787
