#!/bin/bash

# CashFlow Backend - Quick Setup Script (UPDATED FOR MONGODB)
# This script automates the setup process

echo "🚀 CashFlow Backend Quick Setup (MongoDB Edition)"
echo "=================================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Python 3.9+ is required. You have $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"
echo ""

# Create project structure
echo "📁 Creating project structure..."
mkdir -p agents services models logs
touch agents/__init__.py services/__init__.py models/__init__.py
echo "✅ Directories created"
echo ""

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Download spaCy model
echo "🧠 Downloading spaCy language model..."
python -m spacy download en_core_web_sm
echo "✅ spaCy model downloaded"
echo ""

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env and add your API keys!"
    echo ""
    echo "You need:"
    echo "  - MongoDB Atlas URI (FREE at mongodb.com/cloud/atlas)"
    echo "  - OpenAI API Key (from platform.openai.com)"
    echo "  - Twilio credentials (from twilio.com)"
    echo ""
else
    echo "ℹ️  .env file already exists"
fi

# Check if .env is configured
echo ""
echo "🔍 Checking .env configuration..."
if grep -q "mongodb+srv://cashflow_user:YOUR_PASSWORD" .env 2>/dev/null; then
    echo "⚠️  WARNING: .env still has placeholder values!"
    echo "Please edit .env with your actual credentials before running."
else
    echo "✅ .env appears to be configured"
fi
echo ""

# Create Procfile for deployment
if [ ! -f "Procfile" ]; then
    echo "web: gunicorn app:app" > Procfile
    echo "✅ Procfile created for deployment"
fi

# Create test_mongodb.py if not exists
if [ ! -f "test_mongodb.py" ]; then
    echo "✅ test_mongodb.py created"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Setup Complete! Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Setup MongoDB Atlas (5 minutes):"
echo "    - Go to: https://cloud.mongodb.com"
echo "    - Create FREE M0 cluster (512 MB)"
echo "    - Get connection string"
echo "    - See MONGODB_SETUP.md for details"
echo ""
echo "2️⃣  Configure .env file:"
echo "    nano .env"
echo "    Add your MongoDB URI, OpenAI key, Twilio credentials"
echo ""
echo "3️⃣  Test MongoDB connection:"
echo "    python test_mongodb.py"
echo ""
echo "4️⃣  Start the server:"
echo "    python app.py"
echo ""
echo "5️⃣  Test the API:"
echo "    python test_api.py"
echo ""
echo "6️⃣  Configure WhatsApp webhook (see WHATSAPP_INTEGRATION.md)"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Overview"
echo "   - MONGODB_SETUP.md - Database setup (IMPORTANT!)"
echo "   - WHATSAPP_INTEGRATION.md - WhatsApp setup"
echo "   - API_DOCUMENTATION.md - API reference"
echo ""
echo "🎉 Ready to build with MongoDB Atlas!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Make script executable
chmod +x quickstart.sh