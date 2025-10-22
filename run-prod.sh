#!/bin/bash

# ElyterraX Backend Production Startup Script
# This script runs the FastAPI server in production mode (no auto-reload)

set -e  # Exit on error

echo "🚀 Starting ElyterraX Backend (Production Mode)..."

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Load environment variables
echo "🔧 Loading environment variables..."
export $(cat .env | grep -v '^#' | xargs)

# Start the FastAPI server in production mode
echo ""
echo "🌟 Starting FastAPI server in production mode..."
echo "📍 API available at: http://0.0.0.0:8000"
echo ""

# Run uvicorn with multiple workers for production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
