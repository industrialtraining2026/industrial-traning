#!/bin/bash
# Build script for Render deployment
# This script handles system dependencies if needed

set -e

echo "Installing Python dependencies..."

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

echo "Build completed successfully!"

