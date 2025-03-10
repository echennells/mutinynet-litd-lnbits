#!/bin/bash
set -eo pipefail

# Handle shutdown gracefully
shutdown_gracefully() {
    echo "Container is shutting down, ensuring bitcoind flushes the db."
    bitcoin-cli stop
    sleep 5
}
trap shutdown_gracefully SIGTERM SIGHUP SIGQUIT SIGINT

# Create bitcoin directory and copy config only if it doesn't exist
mkdir -p "${BITCOIN_DIR}"
if [ ! -f "${BITCOIN_DIR}/bitcoin.conf" ]; then
    echo "Creating new bitcoin.conf..."
    cat > "${BITCOIN_DIR}/bitcoin.conf" << EOF
server=1
txindex=1
daemon=1
signet=1

[signet]
signetchallenge=512102f7561d208dd9ae99bf497273e16f389bdbd6c4742ddb8e6b216e64fa2928ad8f51ae
addnode=45.79.52.207:38333
dnsseed=0
signetblocktime=30

# RPC Configuration
rpcuser=bitcoin
rpcpassword=bitcoin
rpcbind=0.0.0.0:38332
rpcallowip=0.0.0.0/0

# ZMQ Configuration
zmqpubrawblock=tcp://0.0.0.0:28332
zmqpubrawtx=tcp://0.0.0.0:28333
zmqpubhashblock=tcp://0.0.0.0:28334
EOF
else
    echo "bitcoin.conf already exists, using existing config"
fi

# Start bitcoind
bitcoind -daemonwait

# Keep container running
while true; do
    tail -f /dev/null & wait ${!}
done
