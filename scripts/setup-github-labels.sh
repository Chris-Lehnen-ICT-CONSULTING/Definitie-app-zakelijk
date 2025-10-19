#!/bin/bash
# Setup GitHub labels for the repository
# Run this script once to create all necessary labels

set -e

echo "🏷️  Setting up GitHub labels..."
echo ""

# Type labels
gh label create "type: documentation" --description "Documentation changes" --color "0075ca" --force
gh label create "type: tests" --description "Test changes" --color "0e8a16" --force
gh label create "type: ci" --description "CI/CD changes" --color "fbca04" --force
gh label create "type: configuration" --description "Configuration changes" --color "d4c5f9" --force

# Area labels
gh label create "area: security" --description "Security related" --color "d73a4a" --force
gh label create "area: database" --description "Database changes" --color "006b75" --force
gh label create "area: ui" --description "UI/Frontend changes" --color "bfdadc" --force
gh label create "area: services" --description "Service layer changes" --color "c2e0c6" --force
gh label create "area: validation" --description "Validation logic" --color "fef2c0" --force

# Priority labels
gh label create "priority: high" --description "High priority" --color "b60205" --force
gh label create "priority: medium" --description "Medium priority" --color "fbca04" --force
gh label create "priority: low" --description "Low priority" --color "0e8a16" --force

# Size labels
gh label create "size: XS" --description "< 10 lines changed" --color "3CBF00" --force
gh label create "size: S" --description "10-100 lines changed" --color "5D9801" --force
gh label create "size: M" --description "100-500 lines changed" --color "7F7203" --force
gh label create "size: L" --description "500-1000 lines changed" --color "A14C05" --force
gh label create "size: XL" --description "> 1000 lines changed" --color "C32607" --force

# Status labels  
gh label create "needs-triage" --description "Needs triage" --color "d876e3" --force
gh label create "automated" --description "Automated PR" --color "ededed" --force

# Dependency labels
gh label create "dependencies" --description "Dependency updates" --color "0366d6" --force
gh label create "python" --description "Python dependencies" --color "3572A5" --force
gh label create "github-actions" --description "GitHub Actions updates" --color "000000" --force

# Other standard labels
gh label create "backlog" --description "Backlog item" --color "c5def5" --force
gh label create "architecture" --description "Architecture changes" --color "1d76db" --force

echo ""
echo "✅ All labels created successfully!"
echo ""
echo "You can view them at: https://github.com/ChrisLehnen/Definitie-app/labels"

