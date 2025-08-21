#!/bin/bash
# Setup script for Mutinynet node on Digital Ocean

set -e

echo "=== Setting up Mutinynet Bitcoin + Lightning Stack ==="

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
echo "Installing Docker and dependencies..."
apt-get install -y docker.io docker-compose git curl wget

# Create directories
echo "Creating directories..."
mkdir -p /opt/mutinynet
mkdir -p /mnt/mutinynet-volume/bitcoin
mkdir -p ~/volumes/.bitcoin
mkdir -p ~/volumes/.lnd
mkdir -p ~/volumes/.lit  
mkdir -p ~/volumes/.tapd

# Link bitcoin data to persistent volume
ln -sf /mnt/mutinynet-volume/bitcoin ~/volumes/.bitcoin

# Create docker-compose.yml
cat > /opt/mutinynet/docker-compose.yml << 'EOF'
version: '3.8'

services:
  bitcoind:
    container_name: "bitcoind"
    image: bitcoin/bitcoin:latest  
    restart: unless-stopped
    volumes:
      - /mnt/mutinynet-volume/bitcoin:/home/bitcoin/.bitcoin
      - ./bitcoin.conf:/home/bitcoin/.bitcoin/bitcoin.conf
    environment:
      RPCPASSWORD: bitcoin
    ports:
      - "28332:28332"
      - "28333:28333"
      - "28334:28334"
      - "38332:38332"
      - "38333:38333"
    command: >
      bitcoind
      -signet=1
      -txindex=1
      -server=1
      -rpcuser=bitcoin
      -rpcpassword=bitcoin
      -rpcbind=0.0.0.0:38332
      -rpcallowip=0.0.0.0/0
      -zmqpubrawblock=tcp://0.0.0.0:28332
      -zmqpubrawtx=tcp://0.0.0.0:28333
      -signetchallenge=512102f7561d208dd9ae99bf497273e16f389bdbd6c4742ddb8e6b216e64fa2928ad8f51ae
      -addnode=45.79.52.207:38333
      -dnsseed=0
      -signetblocktime=30
EOF

# Create bitcoin.conf for mutinynet
cat > /opt/mutinynet/bitcoin.conf << 'EOF'
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

# Start Bitcoin daemon
echo "Starting Bitcoin daemon..."
cd /opt/mutinynet
docker-compose up -d bitcoind

echo "Waiting for Bitcoin to start..."
sleep 10

# Check if it's running
docker ps | grep bitcoind

echo "=== Setup Complete ==="
echo ""
echo "Bitcoin mutinynet node is starting up!"
echo "It will take some time to sync with the network."
echo ""
echo "Check sync status with:"
echo "  docker exec bitcoind bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoin getblockchaininfo"
echo ""
echo "Check logs with:"
echo "  docker logs -f bitcoind"
echo ""
echo "Your node is accessible at:"
echo "  RPC: $(curl -s ifconfig.me):38332"
echo "  P2P: $(curl -s ifconfig.me):38333"