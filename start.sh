#!/bin/bash
# Quick start script for Polymarket Trading Bot

echo "=========================================="
echo "Polymarket Trading Bot"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch venv/installed
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Please create .env file with your API credentials."
    echo "See .env.example for reference."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check config.yaml
if [ ! -f "config.yaml" ]; then
    echo "ERROR: config.yaml not found!"
    exit 1
fi

# Start the bot
echo ""
echo "Starting bot..."
echo ""
python main.py

