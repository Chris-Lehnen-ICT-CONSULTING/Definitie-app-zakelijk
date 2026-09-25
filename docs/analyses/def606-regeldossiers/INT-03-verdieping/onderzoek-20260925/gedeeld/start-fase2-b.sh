#!/bin/bash
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
REPO="$HOME/Projecten/Definitie-app"; W="docs/analyses/def606-regeldossiers/INT-03-verdieping/onderzoek-20260925"
cd "$REPO" || exit 2
PB="$(cat "$W/gedeeld/reviewopdracht-b-v1.md")"
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ) (run4; run3 mislukt op -s bij resume)" > "$W/onderzoek-b/codex-run4.status"
nohup codex exec resume -c sandbox_mode=workspace-write -c approval_policy=never -c model=gpt-6-astra -c model_reasoning_effort=high 01a0d782-026f-7a70-b451-84c5f82137dd "$PB" > "$W/onderzoek-b/codex-run4.log" 2> "$W/onderzoek-b/codex-run4.err" < /dev/null &
echo "pid=$! started $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$W/onderzoek-b/codex-run4.status"
echo gestart
