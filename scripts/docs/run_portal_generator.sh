#!/usr/bin/env bash
set -euo pipefail

# Wrapper for pre-commit to generate the portal and stage updated files.

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")"/../.. && pwd)

echo "🛠  Generating portal index from docs..."
python3 "$ROOT_DIR/scripts/docs/generate_portal.py"

echo "➕ Staging generated portal artifacts (docs/portal)..."
git add docs/portal/index.html docs/portal/portal-index.json || true

echo "✅ Portal generation complete."
