#!/bin/bash
# BMAD Agent Environment Configuration
# Dit bestand wordt automatisch geladen door alle BMAD agents

# ============================================
# AI CODE REVIEW CONFIGURATIE
# ============================================

# Markeer alle BMAD agents als AI agents voor code review
export AI_AGENT_COMMIT=1

# Detecteer agent naam dynamisch
if [[ -n "$BMAD_AGENT_NAME" ]]; then
    # Als BMAD agent naam is gezet, gebruik die
    export AI_AGENT_NAME="$BMAD_AGENT_NAME"
elif [[ -n "$AGENT_ID" ]]; then
    # Fallback naar agent ID
    export AI_AGENT_NAME="BMAD-$AGENT_ID"
else
    # Default voor onbekende agents
    export AI_AGENT_NAME="BMAD-Unknown"
fi

# ============================================
# AGENT IDENTIFICATIE
# ============================================

# Specifieke agent configuraties
case "$BMAD_AGENT_NAME" in
    "quinn"|"Quinn")
        export AI_AGENT_NAME="Quinn-QA"
        export AI_REVIEW_STRICT=true
        ;;
    "claude"|"Claude")
        export AI_AGENT_NAME="Claude"
        export AI_REVIEW_ITERATIONS=5
        ;;
    "copilot"|"Copilot")
        export AI_AGENT_NAME="GitHub-Copilot"
        ;;
    *)
        # Behoud default
        ;;
esac

# ============================================
# REVIEW PREFERENCES
# ============================================

# Standaard review configuratie voor alle agents
export AI_REVIEW_ENABLED=true
export AI_REVIEW_MAX_ITERATIONS=${AI_REVIEW_MAX_ITERATIONS:-3}
export AI_REVIEW_AUTO_FIX=${AI_REVIEW_AUTO_FIX:-true}

# ============================================
# GIT CONFIGURATIE
# ============================================

# Git author voor AI commits
export GIT_AUTHOR_NAME="${AI_AGENT_NAME}"
export GIT_AUTHOR_EMAIL="${AI_AGENT_NAME}@bmad.ai"
export GIT_COMMITTER_NAME="${AI_AGENT_NAME}"
export GIT_COMMITTER_EMAIL="${AI_AGENT_NAME}@bmad.ai"

# ============================================
# HELPER FUNCTIONS
# ============================================

# Functie voor AI-aware commits
ai_commit() {
    local message="$1"
    
    # Prefix message met AI indicator als die er nog niet is
    if [[ ! "$message" =~ ^AI: ]]; then
        message="AI: $message"
    fi
    
    # Zet environment en commit
    AI_AGENT_COMMIT=1 git commit -m "$message"
}

# Export de functie zodat subshells hem kunnen gebruiken
export -f ai_commit

# ============================================
# STARTUP MESSAGE
# ============================================

echo "🤖 BMAD Agent Environment Loaded"
echo "   Agent: $AI_AGENT_NAME"
echo "   AI Review: Enabled"
echo "   Auto-fix: $AI_REVIEW_AUTO_FIX"