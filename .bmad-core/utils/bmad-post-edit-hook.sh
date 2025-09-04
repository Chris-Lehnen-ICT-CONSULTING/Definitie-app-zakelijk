#!/bin/bash
# BMAD Post-Edit Hook - Triggers AI code review after any BMAD agent code changes
# Usage: Source this in any BMAD agent workflow after Edit/MultiEdit operations

# Colors voor output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to trigger AI code review
trigger_post_edit_review() {
    local agent_name="${1:-Unknown}"
    local files_changed="${2:-unknown}"

    echo -e "${BLUE}🔄 BMAD Post-Edit Hook Triggered${NC}"
    echo "Agent: $agent_name"
    echo "Files changed: $files_changed"

    # Set AI agent environment
    export AI_AGENT_COMMIT=1
    export AI_AGENT_NAME="$agent_name"

    echo -e "${YELLOW}🤖 Running automated code review...${NC}"

    # Run the AI code reviewer with reduced iterations for post-edit
    python scripts/ai_code_reviewer.py \
        --max-iterations 3 \
        --ai-agent "$agent_name" \
        --project-root .

    REVIEW_EXIT_CODE=$?

    if [ $REVIEW_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ Post-edit code review passed!${NC}"
        return 0
    else
        echo -e "${RED}⚠️  Post-edit code review found issues${NC}"
        echo "Review report: review_report.md"
        echo "Consider running full quality check before commit"
        return 1
    fi
}

# Auto-detect BMAD agent name from environment or context
detect_agent_name() {
    if [ -n "$BMAD_AGENT_NAME" ]; then
        echo "$BMAD_AGENT_NAME"
    elif [ -n "$AI_AGENT_NAME" ]; then
        echo "$AI_AGENT_NAME"
    else
        echo "BMAD-Agent"
    fi
}

# Main execution if script is called directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    AGENT_NAME=$(detect_agent_name)
    trigger_post_edit_review "$AGENT_NAME" "$@"
fi
