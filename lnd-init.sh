#!/bin/bash
set -e

# Use HOME environment variable or default to /home/lnd
LND_HOME="${HOME:-/home/lnd}"
WALLET_DIR="${LND_HOME}/.lnd/data/chain/bitcoin/signet"
CACHE_DIR="/cache/lnd-wallet"

# Check if we have cached wallet data
if [ -d "$CACHE_DIR" ] && [ -f "$CACHE_DIR/wallet.db" ]; then
  echo "Found cached wallet data. Restoring from cache..."
  
  # Create target directory if it doesn't exist
  mkdir -p "$WALLET_DIR"
  
  # Copy cached wallet to working directory
  cp -r "$CACHE_DIR"/* "$WALLET_DIR/" 2>/dev/null || true
  
  # Also restore password file if it exists
  if [ -f "/cache/password.txt" ]; then
    cp "/cache/password.txt" "${LND_HOME}/.lnd/password.txt"
  fi
  
  echo "Wallet restored from cache."
  exit 0
fi

# Check if the wallet already exists locally
if [ -f "$WALLET_DIR/wallet.db" ]; then
  echo "Wallet already exists at $WALLET_DIR. Initialization skipped."
  exit 0
fi

# If no wallet exists, proceed with initialization
echo "Initializing new wallet..."

# Note: lndinit doesn't support setting birthday timestamp directly
# The wallet will use current time as birthday, which is what we want for CI

# Ensure .lnd directory exists with proper permissions
mkdir -p "${LND_HOME}/.lnd"

/bin/lndinit gen-password > ${LND_HOME}/.lnd/password.txt || { echo "Failed to generate password"; exit 1; }
/bin/lndinit gen-seed > ${LND_HOME}/.lnd/seed.txt || { echo "Failed to generate seed"; exit 1; }
/bin/lndinit init-wallet \
  --secret-source=file \
  --file.seed=${LND_HOME}/.lnd/seed.txt \
  --file.wallet-password=${LND_HOME}/.lnd/password.txt \
  --init-file.output-wallet-dir="$WALLET_DIR" \
  --init-file.validate-password || { echo "Failed to initialize wallet"; exit 1; }

echo "Wallet initialized successfully."

# Save wallet to cache for future runs
echo "Saving wallet to cache..."
mkdir -p "$CACHE_DIR"
cp -r "$WALLET_DIR"/* "$CACHE_DIR/"
cp ${LND_HOME}/.lnd/password.txt /cache/password.txt

echo "Wallet cached for future runs."
