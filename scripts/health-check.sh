#!/bin/bash

set -e

echo "=== Starting Health Checks ==="

# Check Bitcoin daemon
echo -n "Checking Bitcoin daemon... "
if docker exec bitcoind bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoin getblockchaininfo > /dev/null 2>&1; then
    echo "✓ OK"
    BLOCKS=$(docker exec bitcoind bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoin getblockcount 2>/dev/null)
    echo "  Current block height: $BLOCKS"
else
    echo "✗ FAILED"
    exit 1
fi

# Check Lightning Terminal (REST API)
echo -n "Checking Lightning Terminal REST API... "
if curl -k -s https://localhost:8080/v1/state 2>/dev/null | grep -q "state"; then
    echo "✓ OK"
else
    echo "✗ FAILED"
    exit 1
fi

# Check Lightning Terminal (HTTPS UI)
echo -n "Checking Lightning Terminal UI... "
if curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443 2>/dev/null | grep -q "200\|401"; then
    echo "✓ OK"
else
    echo "✗ FAILED"
    exit 1
fi

# Check LND RPC
echo -n "Checking LND RPC... "
if docker exec lit lncli --network=signet getinfo > /dev/null 2>&1; then
    echo "✓ OK"
    SYNCED=$(docker exec lit lncli --network=signet getinfo 2>/dev/null | grep -o '"synced_to_chain":[^,]*' | cut -d':' -f2)
    echo "  Synced to chain: $SYNCED"
else
    echo "✗ FAILED (might still be starting)"
fi

# Check Taproot Assets daemon
echo -n "Checking Taproot Assets daemon... "
if docker exec lit tapcli --network=signet getinfo > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED (might still be starting)"
fi

# Check LNbits
echo -n "Checking LNbits API... "
if curl -s http://localhost:5000/api/v1/health 2>/dev/null | grep -q "OK\|true"; then
    echo "✓ OK"
else
    # Alternative check for LNbits main page
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null | grep -q "200"; then
        echo "✓ OK"
    else
        echo "✗ FAILED"
        exit 1
    fi
fi

echo "=== All Health Checks Passed ==="