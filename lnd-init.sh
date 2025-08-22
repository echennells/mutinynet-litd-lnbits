#!/bin/bash
set -e

WALLET_DIR="/root/.lnd/data/chain/bitcoin/signet"

# Check if the wallet already exists by looking for the wallet file
if [ -f "$WALLET_DIR/wallet.db" ]; then
  echo "Wallet already exists at $WALLET_DIR. Initialization skipped."
  exit 0
fi

# If no wallet exists, proceed with initialization
echo "Initializing new wallet..."

# Get current timestamp for wallet birthday (set to 10 minutes ago for safety)
# This avoids scanning thousands of old blocks during wallet initialization
# On Mutinynet with 30-second blocks, this is about 20 blocks
BIRTHDAY_TIMESTAMP=$(($(date +%s) - 600))
echo "Setting wallet birthday to timestamp: $BIRTHDAY_TIMESTAMP (10 minutes ago, ~20 blocks)"

/bin/lndinit gen-password > /root/.lnd/password.txt || { echo "Failed to generate password"; exit 1; }
/bin/lndinit gen-seed > /root/.lnd/seed.txt || { echo "Failed to generate seed"; exit 1; }
/bin/lndinit init-wallet \
  --secret-source=file \
  --file.seed=/root/.lnd/seed.txt \
  --file.wallet-password=/root/.lnd/password.txt \
  --init-file.output-wallet-dir="$WALLET_DIR" \
  --init-file.validate-password \
  --birthday-timestamp=$BIRTHDAY_TIMESTAMP || { echo "Failed to initialize wallet"; exit 1; }

echo "Wallet initialized successfully."
