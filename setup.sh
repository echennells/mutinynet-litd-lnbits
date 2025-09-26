#!/bin/bash
set -e

# Store the script's directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Mutinynet LiT + LNbits Setup ==="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

echo "✓ Docker and Docker Compose are available"

# Create volumes directory
echo "Creating volumes directory..."
mkdir -p ~/volumes/{.bitcoin,.lnd,.lit,.lnbits,.tapd,.faraday,.loop,.pool,.tor}

echo "✓ Volume directories created"

# Build custom Tor image with updated version
echo "Building custom Tor image (0.4.8.14)..."
docker build -f "$SCRIPT_DIR/Dockerfile.tor" -t tor-updated:latest "$SCRIPT_DIR"

echo "✓ Custom Tor image built"

# Clone or update LNbits source for custom build
if [ ! -d "$HOME/lnbits-custom" ]; then
    echo "Cloning LNbits source..."
    git clone https://github.com/lnbits/lnbits.git "$HOME/lnbits-custom"
    cd "$HOME/lnbits-custom"
    git checkout v1.3.0-rc8
    cd - > /dev/null
    echo "✓ LNbits source cloned"
else
    echo "Updating LNbits source..."
    cd "$HOME/lnbits-custom"
    git fetch
    git checkout v1.3.0-rc8
    cd - > /dev/null
    echo "✓ LNbits source updated"
fi

# Build custom LNbits image (non-root)
echo "Building custom LNbits image (non-root)..."
cd "$HOME/lnbits-custom"
docker build -f "$SCRIPT_DIR/Dockerfile.lnbits" -t lnbits-nonroot:v1.3.0-rc8 .
cd - > /dev/null

echo "✓ Custom LNbits image built"

# Set proper permissions
echo "Setting proper volume permissions..."
sudo chown -R $USER:$USER ~/volumes/

echo "✓ Volume permissions set"

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To start the stack:"
echo "  # With Tor (recommended):"
echo "  ENABLE_TOR=true ./start.sh"
echo ""
echo "  # Without Tor:"
echo "  ./start.sh"
echo ""
echo "Services will be available at:"
echo "  - Lightning Terminal: https://localhost:8443 (password: your_secure_password)"
echo "  - LNbits: http://localhost:5000"
echo "  - Bitcoin RPC: localhost:38332 (user: bitcoin, pass: bitcoin)"
echo ""
echo "Images built:"
echo "  - tor-updated:latest (Tor 0.4.8.14)"
echo "  - lnbits-nonroot:v1.3.0-rc8 (runs as user 1000)"