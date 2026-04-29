#!/bin/bash

# Load environment from app/.env
export $(grep -v '^#' ../app/.env | xargs)

# Use app's venv
source ../app/.venv/bin/activate

# Start backend
echo "🐍 Starting HORROCRUXES Backend API..."
echo "📍 Runtime ARN: ${AGENT_RUNTIME_ARN}"
python api.py
