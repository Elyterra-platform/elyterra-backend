#!/bin/bash

# ElyterraX Backend Startup Script
# This script activates the virtual environment and starts the FastAPI server

set -e  # Exit on error

echo "🚀 Starting ElyterraX Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env file created. Please update with your actual credentials."
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
fi

# Load environment variables
echo "🔧 Loading environment variables..."
export $(cat .env | grep -v '^#' | xargs)

# Check if PostgreSQL is accessible
echo "🔍 Checking PostgreSQL connection..."
if command -v psql &> /dev/null; then
    if PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d postgres -c '\q' 2>/dev/null; then
        echo "✅ PostgreSQL is accessible"

        # Check if database exists
        DB_EXISTS=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'")

        if [ "$DB_EXISTS" = "1" ]; then
            echo "✅ Database '$POSTGRES_DB' exists"
        else
            echo "⚠️  Database '$POSTGRES_DB' does not exist. Creating..."
            PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d postgres -c "CREATE DATABASE $POSTGRES_DB;"
            echo "✅ Database created successfully"
        fi
    else
        echo "⚠️  Cannot connect to PostgreSQL. Please ensure it's running:"
        echo "   - Host: $POSTGRES_HOST"
        echo "   - Port: $POSTGRES_PORT"
        echo "   - User: $POSTGRES_USER"
        echo ""
        echo "Continuing anyway (some features may not work)..."
    fi
else
    echo "⚠️  psql command not found. Skipping database checks..."
fi

# Start the FastAPI server
echo ""
echo "🌟 Starting FastAPI server..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API Docs at: http://localhost:8000/docs"
echo "📖 ReDoc at: http://localhost:8000/redoc"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Run uvicorn with auto-reload for development
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
