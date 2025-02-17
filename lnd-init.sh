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
/bin/lndinit gen-password > /root/.lnd/password.txt || { echo "Failed to generate password"; exit 1; }
/bin/lndinit gen-seed > /root/.lnd/seed.txt || { echo "Failed to generate seed"; exit 1; }
/bin/lndinit init-wallet \
  --secret-source=file \
  --file.seed=/root/.lnd/seed.txt \
  --file.wallet-password=/root/.lnd/password.txt \
  --init-file.output-wallet-dir="$WALLET_DIR" \
  --init-file.validate-password || { echo "Failed to initialize wallet"; exit 1; }

echo "Wallet initialized successfully."
