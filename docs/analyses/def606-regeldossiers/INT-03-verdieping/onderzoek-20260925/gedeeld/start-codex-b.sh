#!/bin/bash
# Start onderzoeker B (Codex CLI) op de achtergrond. Aangemaakt door onderzoeker A (Cowork), 25-09-2026.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
REPO="$HOME/Projecten/Definitie-app"
W="docs/analyses/def606-regeldossiers/INT-03-verdieping/onderzoek-20260925"
cd "$REPO" || exit 2
PROMPT="$(cat "$W/gedeeld/startopdracht-b-v1.md")"
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ) codex $(codex --version 2>/dev/null)" > "$W/onderzoek-b/codex-run2.status"
nohup codex exec -s workspace-write -c approval_policy=never --skip-git-repo-check -m gpt-6-astra -c model_reasoning_effort=high -o "$W/onderzoek-b/codex-laatste-bericht-run1.txt" "$PROMPT" > "$W/onderzoek-b/codex-run2.log" 2> "$W/onderzoek-b/codex-run2.err" < /dev/null &
echo "pid=$! started $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$W/onderzoek-b/codex-run2.status"
echo "gestart pid=$!"
