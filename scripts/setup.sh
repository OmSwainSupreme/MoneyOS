#!/bin/bash

set -e

echo "Setting up MoneyOS development environment..."

# Copy .env.example to .env if .env doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
else
    echo ".env already exists, skipping..."
fi

# Setup frontend dependencies
echo "Installing frontend dependencies..."
cd apps/frontend
if [ -f package-lock.json ]; then
    npm ci
elif [ -f pnpm-lock.yaml ]; then
    pnpm install --frozen-lockfile
else
    npm install
fi
cd ../..

# Setup backend if Python is available
if command -v python &> /dev/null; then
    echo "Setting up Python virtual environment..."
    cd apps/backend
    if [ ! -d "venv" ]; then
        python -m venv venv
    fi
    # Windows (Git Bash) uses venv/Scripts; Linux/macOS uses venv/bin
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    cd ../..
else
    echo "⚠️  Python not found - skipping backend setup"
    echo "    Please install Python 3.11+ for backend development"
fi

echo "✅ Frontend setup complete!"
if command -v python &> /dev/null; then
    echo "✅ Backend setup complete!"
else
    echo "⚠️  Backend setup skipped - install Python to continue"
fi

echo ""
echo "Next steps:"
echo "1. Install Docker Desktop if not already installed"
echo "2. Run './scripts/setup.sh' again after installing Python (if skipped)"
echo "3. Start services with: docker-compose up"
echo "4. Frontend will be available at http://localhost:3000"
echo "5. Backend API will be available at http://localhost:8000"