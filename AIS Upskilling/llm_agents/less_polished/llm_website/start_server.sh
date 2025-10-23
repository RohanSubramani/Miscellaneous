#!/bin/bash

echo "=================================="
echo "Starting Assistant Server"
echo "=================================="
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found. Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

# Check if flask-cors is installed
if ! python3 -c "import flask_cors" 2>/dev/null; then
    echo "⚠️  flask-cors not found. Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

echo "✅ Dependencies installed"
echo ""
echo "Starting server on http://localhost:5001"
echo "Press Ctrl+C to stop"
echo ""

# Default to mock mode, or pass --mode llm for LLM mode
python3 assistant.py "$@"

