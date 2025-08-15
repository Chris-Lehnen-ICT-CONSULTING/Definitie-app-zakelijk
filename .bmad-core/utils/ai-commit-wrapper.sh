#!/bin/bash
# BMAD AI Agent Commit Wrapper
# Automatisch detecteren en taggen van AI commits

# Detecteer of dit een BMAD AI agent is
if [[ -n "$BMAD_AGENT" ]] || [[ "$USER" == "bmad-agent" ]] || [[ -n "$AI_AGENT" ]]; then
    export AI_AGENT_COMMIT=1
    export AI_AGENT_NAME="${BMAD_AGENT:-${AI_AGENT:-bmad-default}}"
    echo "🤖 AI Agent gedetecteerd: $AI_AGENT_NAME"
fi

# Voer de normale git commit uit
git commit "$@"