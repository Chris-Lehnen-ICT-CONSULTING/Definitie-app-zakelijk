#!/bin/bash

# Real-time log monitoring script voor Claude
# Start de applicatie en toon logs

echo "Starting application with real-time logging..."

# Optie 1: Streamlit app met verbose logging
python -m streamlit run src/main.py 2>&1 | tee app_output.log &
APP_PID=$!

# Tail de log file
tail -f app_output.log

# Of gebruik deze voor specifieke log files:
# tail -f logs/definition_agent.log logs/api_calls.json

# Cleanup on exit
trap "kill $APP_PID 2>/dev/null" EXIT
