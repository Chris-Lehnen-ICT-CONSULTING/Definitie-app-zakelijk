#!/bin/bash
# Script om ai-code-reviewer package te bouwen en distribueren

set -e

echo "🧪 AI Code Reviewer Package Distributie Script"
echo "============================================"

# Versie ophalen
VERSION=$(python -c "from ai_code_reviewer import __version__; print(__version__)")
echo "📦 Huidige versie: $VERSION"

# Clean up oude builds
echo "🧹 Opschonen oude builds..."
rm -rf dist/ build/ *.egg-info

# Build package
echo "🔨 Package bouwen..."
python -m build

# Toon gebouwde bestanden
echo "\n✅ Gebouwde packages:"
ls -la dist/

echo "\n📋 Installatie opties:"
echo "1. Lokaal installeren in ander project:"
echo "   pip install /path/to/Definitie-app/ai_code_reviewer_package/dist/ai-code-reviewer-$VERSION-py3-none-any.whl"
echo ""
echo "2. Upload naar privé PyPI server:"
echo "   twine upload dist/*"
echo ""
echo "3. Kopieer naar shared network drive:"
echo "   cp dist/* /path/to/shared/packages/"
echo ""
echo "4. Maak GitHub release:"
echo "   gh release create v$VERSION dist/* --title \"AI Code Reviewer v$VERSION\" --notes \"Release van AI Code Reviewer v$VERSION\""