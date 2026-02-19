#!/bin/bash
# SOC Blackout — One-Command Setup
# Usage: ./scripts/setup.sh (from anywhere)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "============================================"
echo "  SOC Blackout — Setup"
echo "============================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Install it first."
    exit 1
fi

# Create .env at project root if not exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo ""
    echo "📝 No .env file found. Let's set up your Elasticsearch connection."
    echo "   (You can find these in Elastic Cloud → Manage → Cloud ID / API Keys)"
    echo ""
    read -p "  Elasticsearch Cloud ID: " CLOUD_ID
    read -p "  Elasticsearch API Key: " API_KEY

    cat > "$PROJECT_ROOT/.env" << EOF
ELASTICSEARCH_CLOUD_ID=${CLOUD_ID}
ELASTICSEARCH_API_KEY=${API_KEY}
EOF

    echo "  ✅ .env created at project root"
else
    echo ""
    echo "✅ .env found"
fi

# Create virtual environment if not exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo ""
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv "$PROJECT_ROOT/venv"
fi

# Activate venv and install dependencies
echo ""
echo "📦 Installing Python dependencies..."
source "$PROJECT_ROOT/venv/bin/activate"
pip install -r "$PROJECT_ROOT/scripts/requirements.txt" --quiet

# Seed data
echo ""
echo "🌱 Seeding Elasticsearch with demo data..."
python3 "$PROJECT_ROOT/scripts/seed_data.py"

echo ""
echo "============================================"
echo "  ✅ Setup complete!"
echo "  Next steps:"
echo "    1. Open Kibana → Agent Builder"
echo "    2. Create the SOC Blackout agent"
echo "       (paste agent/instructions.md as Custom Instructions)"
echo "    3. Create & assign the 4 custom tools"
echo "       (see tools/ directory for configs)"
echo "    4. Start chatting!"
echo "============================================"
