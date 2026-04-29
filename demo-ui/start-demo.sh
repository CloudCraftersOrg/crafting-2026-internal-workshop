#!/bin/bash

echo "🐍 HORROCRUXES Demo Launcher - Team Slytherin"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f "../app/.env" ]; then
    echo "❌ ERROR: app/.env not found"
    echo "   Create it first with your AWS credentials"
    exit 1
fi

echo "✅ Found app/.env"
echo ""

# Start backend in background
echo "🚀 Starting Backend API (port 8000)..."
python api.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to be ready
sleep 3

# Start frontend
echo ""
echo "🎨 Starting Frontend React (port 5173)..."
echo ""
echo "🌐 Demo will open at: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "=============================================="
echo ""

npm run dev

# Cleanup on exit
kill $BACKEND_PID 2>/dev/null
