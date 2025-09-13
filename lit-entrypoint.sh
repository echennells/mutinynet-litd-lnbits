#!/bin/sh

# Build LIT_CONFIG dynamically based on environment variables

# Use NETWORK env var if set, default to signet
NETWORK_TYPE="${NETWORK:-signet}"

LIT_CONFIG="network=$NETWORK_TYPE
lnd-mode=integrated
uipassword=your_secure_password
httpslisten=0.0.0.0:8443
autopilot.disable=true
lnd.rpclisten=0.0.0.0:10009
lnd.restlisten=0.0.0.0:8080
lnd.tlsextradomain=lit
lnd.bitcoin.active=1
lnd.bitcoin.node=bitcoind
lnd.bitcoin.$NETWORK_TYPE=1
lnd.bitcoind.rpchost=bitcoind:38332
lnd.bitcoind.rpcuser=bitcoin
lnd.bitcoind.rpcpass=bitcoin
lnd.bitcoind.zmqpubrawblock=tcp://bitcoind:28332
lnd.bitcoind.zmqpubrawtx=tcp://bitcoind:28333
lnd.rpcmiddleware.enable=true
lnd.wallet-unlock-password-file=/home/lnd/.lnd/password.txt
lnd.listen=0.0.0.0:9735

# Tor configuration
lnd.tor.active=true
lnd.tor.socks=tor:9050
lnd.tor.control=tor:9051
lnd.tor.v3=true
lnd.tor.skip-proxy-for-clearnet-targets=false"

# Add external IP only if EXTERNAL_IP is set
if [ -n "$EXTERNAL_IP" ]; then
    LIT_CONFIG="$LIT_CONFIG
lnd.externalip=$EXTERNAL_IP:9735"
fi

# Add Taproot Assets configuration
LIT_CONFIG="$LIT_CONFIG

# Taproot Assets configuration
taproot-assets-mode=integrated
taproot-assets.network=$NETWORK_TYPE
taproot-assets.rpclisten=0.0.0.0:10029
taproot-assets.lnd.host=localhost:10029
taproot-assets.universe.federationserver=universe.signet.laisee.org:8443
taproot-assets.universe.no-default-federation=true
taproot-assets.universe.sync-all-assets=true
taproot-assets.universe.public-access=rw
taproot-assets.proofcourieraddr=universerpc://universe.signet.laisee.org:8443

# Taproot Assets Lightning config
lnd.protocol.option-scid-alias=true
lnd.protocol.zero-conf=true
lnd.protocol.simple-taproot-chans=true
lnd.protocol.simple-taproot-overlay-chans=true
lnd.protocol.custom-message=17
lnd.accept-keysend=true

# Mock price oracle settings for RFQ
taproot-assets.experimental.rfq.priceoracleaddress=use_mock_price_oracle_service_promise_to_not_use_on_mainnet
taproot-assets.experimental.rfq.mockoracleassetsperbtc=100000"

# Write config and start litd
mkdir -p /home/lnd/.lit
echo "$LIT_CONFIG" > /home/lnd/.lit/lit.conf
exec litd