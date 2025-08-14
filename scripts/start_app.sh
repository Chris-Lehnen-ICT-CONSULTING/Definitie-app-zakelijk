#!/bin/bash
# Start script voor DefinitieAgent met nieuwe services

echo "🚀 Starting DefinitieAgent..."
echo "ℹ️  Je kunt tussen oude en nieuwe services wisselen via de sidebar!"
echo ""

# Optioneel: forceer nieuwe services bij start
# export USE_NEW_SERVICES=true

# Start Streamlit
streamlit run src/app.py