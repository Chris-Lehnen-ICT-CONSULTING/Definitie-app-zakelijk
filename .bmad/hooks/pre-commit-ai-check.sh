#!/bin/bash
# BMAD/Claude Auto Review Hook
# This hook automatically triggers code review for AI-generated changes

# Check if this is an AI-generated commit
if [[ "$GIT_AUTHOR_NAME" == *"Claude"* ]] || [[ "$GIT_AUTHOR_NAME" == *"BMAD"* ]] || [[ -n "$AI_AGENT_COMMIT" ]]; then
    echo "🤖 AI-generated code detected, starting automatic review..."
    
    # Set environment variable
    export AI_AGENT_NAME="${GIT_AUTHOR_NAME:-Claude}"
    
    # Run the AI review wrapper
    python scripts/ai-agent-wrapper.py
    
    # Check exit code
    if [ $? -ne 0 ]; then
        echo "❌ AI code review failed. Please fix issues before committing."
        echo "Check ai_feedback.md for specific guidance."
        exit 1
    fi
    
    echo "✅ AI code review passed!"
fi

# Continue with normal pre-commit hooks
if [ -f .git/hooks/pre-commit ]; then
    .git/hooks/pre-commit.original
fi