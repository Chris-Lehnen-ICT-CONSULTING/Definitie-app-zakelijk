#!/bin/bash
# Start onderzoeker C (Claude Code CLI, claude-fable-5-1, effort xhigh) op de achtergrond. Aangemaakt door onderzoeker A (Cowork), 25-09-2026.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
REPO="$HOME/Projecten/Definitie-app"
W="docs/analyses/def606-regeldossiers/INT-03-verdieping/onderzoek-20260925"
cd "$REPO" || exit 2
PROMPT="Lees en voer uit: $REPO/$W/gedeeld/startopdracht-c-v1.md

Aanvullende toegang: de skills staan ook leesbaar onder $HOME/Projecten/_claude-global-setup/skills/ (definitie-toetsregels, definitie-nederlandse-definities, toetsregel-onderzoek). Werk uitsluitend in het Nederlands en lever alle bestanden op in onderzoek-c/ zoals de startopdracht vraagt. Maak geen git-commits. Je draait als claude-fable-5-1 met effort xhigh; vermeld dat in je bewijsmanifest."
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ) claude $(claude --version 2>/dev/null) model=claude-fable-5-1 effort=xhigh" > "$W/onderzoek-c/claude-run2.status"
nohup claude --model claude-fable-5-1 --effort xhigh --permission-mode acceptEdits --max-turns 200 \
  --add-dir "$HOME/Projecten/_claude-global-setup/skills" \
  --allowedTools "Bash(.venv/bin/python *)" "Bash(python3 *)" "Bash(cat *)" "Bash(ls *)" "Bash(git log *)" "Bash(git diff *)" "Bash(git status *)" "Bash(git rev-parse *)" "Bash(shasum *)" "Bash(grep *)" "Bash(rg *)" "Bash(sed -n *)" "Bash(wc *)" "Bash(find *)" "Bash(mkdir *)" "Bash(cd *)" "Bash(head *)" "Bash(tail *)" "Bash(diff *)" \
  --output-format stream-json --verbose -p "$PROMPT" > "$W/onderzoek-c/claude-run2.jsonl" 2> "$W/onderzoek-c/claude-run2.err" < /dev/null &
echo "pid=$! started $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$W/onderzoek-c/claude-run2.status"
echo "gestart pid=$!"
