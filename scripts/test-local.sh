#!/bin/bash
# Quick local test script for regtest environment

set -e

echo "🚀 Starting local regtest test..."

# Start services
echo "Starting Docker services..."
docker-compose -f docker-compose.regtest.yml up -d

# Wait for initialization
echo "Waiting for services to initialize..."
sleep 30

# Test Bitcoin
echo "Testing Bitcoin..."
docker exec bitcoind-regtest bitcoin-cli -regtest -rpcuser=bitcoin -rpcpassword=bitcoin getblockchaininfo

# Test Lightning
echo "Testing Lightning Terminal..."
docker exec lit-regtest lncli --network=regtest getinfo || {
  echo "Waiting for LND..."
  sleep 20
  docker exec lit-regtest lncli --network=regtest getinfo
}

# Test LNbits
echo "Testing LNbits..."
curl -s http://localhost:5000/api/v1/health || echo "LNbits not ready yet"

echo "✅ Local test complete!"
echo ""
echo "Services running at:"
echo "  Lightning Terminal UI: https://localhost:8443"
echo "  LNbits: http://localhost:5000"
echo ""
echo "To stop: docker-compose -f docker-compose.regtest.yml down"
echo "To cleanup: docker-compose -f docker-compose.regtest.yml down -v"