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

# Setup backend virtual environment and dependencies
echo "Setting up Python virtual environment..."
cd apps/backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ../..

echo "Setup complete! Run 'docker-compose up' to start services."