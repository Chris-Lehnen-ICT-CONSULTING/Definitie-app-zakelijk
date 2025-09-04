#!/bin/bash
# BMAD Core Initialization Script
# Dit wordt uitgevoerd wanneer een BMAD agent start

# ============================================
# BMAD CORE INITIALIZATION
# ============================================

echo "🚀 Initializing BMAD Core..."

# Bepaal BMAD root directory
export BMAD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$(cd "$BMAD_ROOT/.." && pwd)"

# ============================================
# LOAD CONFIGURATIONS
# ============================================

# Load agent environment (inclusief AI review setup)
if [[ -f "$BMAD_ROOT/config/agent-environment.sh" ]]; then
    source "$BMAD_ROOT/config/agent-environment.sh"
fi

# ============================================
# SETUP PATH
# ============================================

# Voeg project scripts toe aan PATH
export PATH="$PROJECT_ROOT/scripts:$PATH"

# ============================================
# AGENT REGISTRATION
# ============================================

# Registreer agent start in metrics
if command -v python3 &> /dev/null; then
    python3 "$PROJECT_ROOT/scripts/ai_metrics_tracker.py" record \
        --agent "$AI_AGENT_NAME" \
        --passed true \
        --iterations 0 \
        --issues 0 \
        --duration 0 \
        --files 0 \
        2>/dev/null || true
fi

# ============================================
# GIT HOOKS SETUP
# ============================================

# Zorg dat git hooks actief zijn voor deze sessie
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="core.hooksPath"
export GIT_CONFIG_VALUE_0="$PROJECT_ROOT/.git/hooks"

# ============================================
# ALIASES & SHORTCUTS
# ============================================

# Git aliases voor AI agents
alias gaic='ai_commit'
alias review='python scripts/ai_code_reviewer.py'

# ============================================
# READY MESSAGE
# ============================================

echo "✅ BMAD Core Initialized"
echo "   Project: $PROJECT_ROOT"
echo "   Agent: $AI_AGENT_NAME"
echo ""
echo "💡 Tips:"
echo "   - Use 'ai_commit \"message\"' for AI-aware commits"
echo "   - Use 'review' to run code review manually"
echo "   - All commits trigger automatic AI review"
