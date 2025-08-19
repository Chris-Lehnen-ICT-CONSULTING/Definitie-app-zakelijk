#!/bin/bash
# Ga naar de map waar het script zich bevindt
cd "$(dirname "$0")"

# Activeer de virtuele omgeving
source venv/bin/activate

# Start de Streamlit-app
streamlit run definitie_agent_webinterface_logging.py
