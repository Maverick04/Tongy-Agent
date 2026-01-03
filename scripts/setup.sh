#!/bin/bash
# Tongy-Agent Setup Script

set -e

echo "🚀 Setting up Tongy-Agent..."

# Create config directory
CONFIG_DIR="$HOME/.tongy-agent/config"
mkdir -p "$CONFIG_DIR"

# Copy example config if config doesn't exist
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo "📝 Creating configuration file..."
    cp tongy_agent/config/config-example.yaml "$CONFIG_DIR/config.yaml"
    echo "✅ Configuration created at: $CONFIG_DIR/config.yaml"
else
    echo "ℹ️  Configuration already exists at: $CONFIG_DIR/config.yaml"
fi

# Create workspace
WORKSPACE="./workspace"
mkdir -p "$WORKSPACE"
echo "✅ Workspace created at: $WORKSPACE"

# Check for API key
if [ -z "$TONGY_API_KEY" ]; then
    echo ""
    echo "⚠️  TONGY_API_KEY environment variable not set!"
    echo ""
    echo "Please set your API key:"
    echo "  export TONGY_API_KEY='your-api-key-here'"
    echo ""
    echo "Get your API key from: https://open.bigmodel.cn/"
    echo ""
    echo "Or add it to your config file at: $CONFIG_DIR/config.yaml"
else
    echo "✅ TONGY_API_KEY is set"
fi

echo ""
echo "🎉 Tongy-Agent setup complete!"
echo ""
echo "To start using Tongy-Agent:"
echo "  1. Set your API key: export TONGY_API_KEY='your-api-key'"
echo "  2. Run: python -m tongy_agent.cli"
echo ""
