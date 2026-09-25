#!/bin/bash
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
REPO="$HOME/Projecten/Definitie-app"; W="docs/analyses/def606-regeldossiers/INT-03-verdieping/onderzoek-20260925"
cd "$REPO" || exit 2
PB="$(cat "$W/gedeeld/reviewopdracht-b-v1.md")"
PC="$(cat "$W/gedeeld/reviewopdracht-c-v1.md")"
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$W/onderzoek-b/codex-run3.status"
nohup codex exec resume 01a0d782-026f-7a70-b451-84c5f82137dd -s workspace-write -c approval_policy=never --skip-git-repo-check -m gpt-6-astra -c model_reasoning_effort=high -o "$W/onderzoek-b/codex-laatste-bericht-run3.txt" "$PB" > "$W/onderzoek-b/codex-run3.log" 2> "$W/onderzoek-b/codex-run3.err" < /dev/null &
echo "pid=$! started $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$W/onderzoek-b/codex-run3.status"
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ) model=claude-fable-5-1 effort=xhigh resume=90f43917-9578-48d1-ab42-a020077cd7dc" > "$W/onderzoek-c/claude-run3.status"
nohup claude --resume 90f43917-9578-48d1-ab42-a020077cd7dc --model claude-fable-5-1 --effort xhigh --permission-mode acceptEdits --max-turns 200 --add-dir "$HOME/Projecten/_claude-global-setup/skills" --allowedTools "Bash(.venv/bin/python *)" "Bash(python3 *)" "Bash(cat *)" "Bash(ls *)" "Bash(git log *)" "Bash(git diff *)" "Bash(git status *)" "Bash(git rev-parse *)" "Bash(shasum *)" "Bash(grep *)" "Bash(rg *)" "Bash(sed -n *)" "Bash(wc *)" "Bash(find *)" "Bash(mkdir *)" "Bash(cd *)" "Bash(head *)" "Bash(tail *)" "Bash(diff *)" --output-format stream-json --verbose -p "$PC" > "$W/onderzoek-c/claude-run3.jsonl" 2> "$W/onderzoek-c/claude-run3.err" < /dev/null &
echo "pid=$! started $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$W/onderzoek-c/claude-run3.status"
echo gestart
