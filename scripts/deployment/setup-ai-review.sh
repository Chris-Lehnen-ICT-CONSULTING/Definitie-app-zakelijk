#!/bin/bash
printf '%s\n' 'DEF-666-QUARANTINE-GUARD: scripts/deployment/setup-ai-review.sh is bij de bron uitgeschakeld.' >&2
return 92 2>/dev/null || exit 92
# DEF-666: de blokkade hierboven staat vóór elke instelling, functiedefinitie en
# opdracht. Gesourcet stopt zij het script zonder de aanroepende shell te doden;
# rechtstreeks uitgevoerd sluit zij af met status 92. De code hieronder blijft
# ongewijzigd staan en wordt niet meer bereikt.
# Setup script for AI code review automation

echo "🔧 Setting up AI Code Review Automation..."

# Create directories if needed
mkdir -p .git/hooks
mkdir -p .bmad/hooks

# Backup existing pre-commit if exists
if [ -f .git/hooks/pre-commit ]; then
    echo "📦 Backing up existing pre-commit hook..."
    mv .git/hooks/pre-commit .git/hooks/pre-commit.original
fi

# Install the AI check as pre-commit hook
echo "📝 Installing AI review hook..."
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook with AI review integration

# Check if this is an AI-generated commit
if [[ "$GIT_AUTHOR_NAME" == *"Claude"* ]] || \
   [[ "$GIT_AUTHOR_NAME" == *"BMAD"* ]] || \
   [[ -n "$AI_AGENT_COMMIT" ]] || \
   [[ -n "$CLAUDE_CODE_ACTIVE" ]]; then

    echo "🤖 AI-generated code detected, starting automatic review..."

    # Set environment variable
    export AI_AGENT_NAME="${AI_AGENT_NAME:-${GIT_AUTHOR_NAME:-Claude}}"

    # Run the AI review wrapper
    python scripts/ai-agent-wrapper.py

    # Check exit code
    if [ $? -ne 0 ]; then
        echo "❌ AI code review failed. Please fix issues before committing."
        echo "📝 Check ai_feedback.md for specific guidance."
        exit 1
    fi

    echo "✅ AI code review passed!"
fi

# Run normal pre-commit hooks if they exist
if [ -f .git/hooks/pre-commit.original ]; then
    .git/hooks/pre-commit.original
else
    # Run standard pre-commit if installed
    if command -v pre-commit &> /dev/null; then
        pre-commit run --all-files
    fi
fi
EOF

# Make hook executable
chmod +x .git/hooks/pre-commit

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
pip install ruff black mypy bandit pytest coverage pre-commit

# Initialize pre-commit if not already done
if [ ! -f .pre-commit-config.yaml ]; then
    echo "📝 Creating pre-commit config..."
    pre-commit install
fi

# Create initial metrics file
if [ ! -f ai_metrics.json ]; then
    echo "{}" > ai_metrics.json
fi

echo "✅ AI Code Review Automation Setup Complete!"
echo ""
echo "Usage:"
echo "  For AI commits: export AI_AGENT_COMMIT=1"
echo "  Or: git config user.name 'Claude AI'"
echo "  Then commit normally!"
echo ""
echo "Dashboard: python scripts/ai-metrics-dashboard.py"
