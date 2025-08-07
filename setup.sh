#!/bin/bash

# Flashcard LMS Backend Setup Script

echo "🚀 Setting up Flashcard LMS Backend..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed successfully"

# Create upload directories
echo "📁 Creating upload directories..."
mkdir -p uploads/images
mkdir -p uploads/audio
echo "✅ Upload directories created"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create one based on the template in README.md"
else
    echo "✅ .env file found"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your .env file with proper database settings"
echo "2. Start MongoDB (locally or use MongoDB Atlas)"
echo "3. Run the application: uvicorn app.main:app --reload"
echo ""
echo "📚 Useful commands:"
echo "  • Start development server: uvicorn app.main:app --reload"
echo "  • Run tests: pytest"
echo "  • View API docs: http://localhost:8000/docs"
echo ""
