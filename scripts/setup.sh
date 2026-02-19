#!/bin/bash
# SOC Blackout — One-Command Setup
# Usage: ./scripts/setup.sh

set -e

echo "============================================"
echo "  SOC Blackout — Setup"
echo "============================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Install it first."
    exit 1
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo ""
    echo "📝 No .env file found. Let's set up your Elasticsearch connection."
    echo ""
    read -p "  Elasticsearch Cloud ID (or press Enter to skip): " CLOUD_ID
    read -p "  Elasticsearch API Key: " API_KEY

    cat > .env << EOF
ELASTICSEARCH_CLOUD_ID=${CLOUD_ID}
ELASTICSEARCH_API_KEY=${API_KEY}
EOF

    echo "  ✅ .env created"
fi

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r scripts/requirements.txt --quiet

# Seed data
echo ""
echo "🌱 Seeding Elasticsearch with demo data..."
python3 scripts/seed_data.py

echo ""
echo "============================================"
echo "  ✅ Setup complete!"
echo "  Next steps:"
echo "    1. Open Kibana → Agent Builder"
echo "    2. Create the SOC Blackout agent"
echo "    3. Assign the custom tools"
echo "    4. Start chatting!"
echo "============================================"
