#!/bin/bash
# BMAD Post Code Change Hook
# Automatically triggers code review after BMAD agents make changes

# This hook is called by BMAD agents after code modifications

echo "🤖 BMAD Agent code change detected..."

# Set environment variables for tracking
export AI_AGENT_COMMIT=1
export AI_AGENT_NAME="BMAD-${BMAD_AGENT_NAME:-Agent}"

# Stage the changes
git add -A

# Run the AI review wrapper directly (before commit)
python scripts/ai-agent-wrapper.py

# Check if review passed
if [ $? -eq 0 ]; then
    echo "✅ Code review passed, creating commit..."
    
    # Create commit with BMAD identifier
    git commit -m "🤖 BMAD: ${BMAD_COMMIT_MESSAGE:-Code update}"
    
    echo "✅ Changes committed successfully!"
else
    echo "❌ Code review failed. Changes not committed."
    echo "📝 Check ai_feedback.md for guidance."
    
    # Unstage changes
    git reset HEAD
    
    exit 1
fi