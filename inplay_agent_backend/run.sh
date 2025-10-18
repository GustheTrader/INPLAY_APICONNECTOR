
#!/bin/bash

# Run script for INPLAY Agent Backend

echo "================================================"
echo "  INPLAY Agent Backend - NFL Game Tracker"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠ Warning: .env file not found"
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "Please edit .env and add your OPENAI_API_KEY if you want AI commentary."
    echo ""
fi

# Check if dependencies are installed
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ Dependencies not installed"
    echo "Installing requirements..."
    pip install -r requirements.txt
    echo ""
fi

echo "✓ Dependencies OK"
echo ""

# Start the server
echo "Starting INPLAY Agent Backend..."
echo "Server will run on http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo "================================================"
echo ""

python3 app.py
