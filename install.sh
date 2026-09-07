#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

VENV_DIR=".venv-release"

echo "═══════════════════════════════════════════════"
echo "  NUTRITION-PAD INSTALLATION"
echo "═══════════════════════════════════════════════"
echo ""

# Create venv if needed
if [ ! -d "$VENV_DIR" ]; then
    echo "▶ Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "  ✓ Created $VENV_DIR"
else
    echo "▶ Using existing virtual environment: $VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "▶ Upgrading pip..."
pip install --upgrade pip -q
echo "  ✓ pip upgraded"

# Install package in editable mode
echo "▶ Installing nutrition-pad..."
pip install -e . -q
echo "  ✓ Installed"

# Install development dependencies
echo "▶ Installing development dependencies..."
pip install playwright twine build -q
echo "  ✓ Installed playwright, twine, build"

# Install Playwright browsers
echo "▶ Installing Playwright browsers..."
playwright install chromium
echo "  ✓ Chromium browser installed"

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ INSTALLATION COMPLETE"
echo "═══════════════════════════════════════════════"
echo ""
echo "To activate the environment, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To run tests and release:"
echo "  ./release"
echo ""
