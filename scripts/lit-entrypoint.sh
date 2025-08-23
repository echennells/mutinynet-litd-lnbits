#!/bin/bash
set -e

echo "Starting Lightning Terminal on regtest..."

# Wait for bitcoind to be ready
echo "Waiting for bitcoind..."
until bitcoin-cli -regtest -rpcconnect=bitcoind -rpcuser=bitcoin -rpcpassword=bitcoin getblockchaininfo 2>/dev/null; do
  echo "Bitcoind not ready yet..."
  sleep 2
done

echo "Bitcoind is ready!"

# Generate initial blocks if this is a fresh chain
BLOCK_COUNT=$(bitcoin-cli -regtest -rpcconnect=bitcoind -rpcuser=bitcoin -rpcpassword=bitcoin getblockcount)
if [ "$BLOCK_COUNT" -eq "0" ]; then
  echo "Fresh regtest chain detected. Mining initial blocks..."
  ADDR=$(bitcoin-cli -regtest -rpcconnect=bitcoind -rpcuser=bitcoin -rpcpassword=bitcoin getnewaddress)
  bitcoin-cli -regtest -rpcconnect=bitcoind -rpcuser=bitcoin -rpcpassword=bitcoin generatetoaddress 101 $ADDR
  echo "Generated 101 blocks for initial setup"
fi

# Create LND config
echo "$LIT_CONFIG" > /root/.lit/lit.conf

# Initialize wallet if it doesn't exist
if [ ! -f "/root/.lnd/data/chain/bitcoin/regtest/wallet.db" ]; then
  echo "Creating new Lightning wallet..."
  
  # Start litd in background to create wallet
  litd &
  LIT_PID=$!
  
  # Wait for LND to be ready
  sleep 10
  
  # Create wallet with simple password
  echo "password" > /tmp/password.txt
  lncli --network=regtest create <<EOF
password
password
n
EOF
  
  # Save password for auto-unlock
  cp /tmp/password.txt /root/.lnd/password.txt
  
  # Stop and restart with auto-unlock
  kill $LIT_PID
  wait $LIT_PID
fi

# Start litd with auto-unlock
echo "Starting Lightning Terminal..."
exec litd --lnd.wallet-unlock-password-file=/root/.lnd/password.txt