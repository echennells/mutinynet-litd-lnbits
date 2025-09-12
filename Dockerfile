FROM debian:bullseye-slim
LABEL org.opencontainers.image.authors="NBD"
LABEL org.opencontainers.image.licenses=MIT

ENV BITCOIN_DIR=/home/bitcoin/.bitcoin
ENV RPCUSER=${RPCUSER:-"bitcoin"}
ENV RPCPASSWORD=${RPCPASSWORD:-"bitcoin"}
ENV ZMQPUBRAWBLOCK=${ZMQPUBRAWBLOCK:-"tcp://0.0.0.0:28332"}
ENV ZMQPUBRAWTX=${ZMQPUBRAWTX:-"tcp://0.0.0.0:28333"}
ENV ZMQPUBHASHBLOCK=${ZMQPUBHASHBLOCK:-"tcp://0.0.0.0:28334"}
ENV RPCBIND=${RPCBIND:-"0.0.0.0:38332"}
ENV RPCALLOWIP=${RPCALLOWIP:-"0.0.0.0/0"}
ENV WHITELIST=${WHITELIST:-"0.0.0.0/0"}

VOLUME $BITCOIN_DIR
EXPOSE 28332 28333 28334 38332 38333 38334

# Install dependencies (removed gosu as it's not needed for non-root)
RUN apt-get update && \
    apt-get install -qq --no-install-recommends ca-certificates dirmngr wget libc6 procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Download and install Bitcoin Core
# Supports both normal signet and Mutinynet (30-second blocks)
ARG SIGNET_TYPE=signet
ARG TARGETPLATFORM

RUN set -ex && \
    if [ "$SIGNET_TYPE" = "mutinynet" ]; then \
        echo "Installing custom Mutinynet Bitcoin build with 30-second blocks" && \
        BITCOIN_VERSION="d4a86277ed8a" && \
        case "$TARGETPLATFORM" in \
            "linux/amd64") TRIPLET="x86_64-linux-gnu" ;; \
            "linux/arm64") TRIPLET="aarch64-linux-gnu" ;; \
            "linux/arm/v7") TRIPLET="arm-linux-gnueabihf" ;; \
            *) echo "Unsupported platform: $TARGETPLATFORM" >&2; exit 1 ;; \
        esac && \
        cd /tmp && \
        wget https://github.com/benthecarman/bitcoin/releases/download/paircommit/bitcoin-${BITCOIN_VERSION}-${TRIPLET}.tar.gz && \
        tar -xzvf bitcoin-${BITCOIN_VERSION}-${TRIPLET}.tar.gz -C /usr/local/bin --strip-components=2 \
        "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-cli" \
        "bitcoin-${BITCOIN_VERSION}/bin/bitcoind" \
        "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-wallet" \
        "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-util" && \
        rm bitcoin-${BITCOIN_VERSION}-${TRIPLET}.tar.gz; \
    else \
        echo "Installing standard Bitcoin Core 29.0 for normal signet" && \
        BITCOIN_VERSION="29.0" && \
        case "$TARGETPLATFORM" in \
            "linux/amd64") ARCH="x86_64" ;; \
            "linux/arm64") ARCH="aarch64" ;; \
            "linux/arm/v7") ARCH="arm" ;; \
            *) echo "Unsupported platform: $TARGETPLATFORM" >&2; exit 1 ;; \
        esac && \
        cd /tmp && \
        wget https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz && \
        wget https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/SHA256SUMS && \
        grep "bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz" SHA256SUMS | sha256sum -c - && \
        tar -xzvf bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz -C /usr/local/bin --strip-components=2 \
        "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-cli" \
        "bitcoin-${BITCOIN_VERSION}/bin/bitcoind" \
        "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-wallet" \
        "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-util" && \
        rm bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz SHA256SUMS; \
    fi

# Set SIGNET_TYPE as environment variable for runtime
ENV SIGNET_TYPE=${SIGNET_TYPE}

# Create non-root user with UID/GID 1000
RUN groupadd -r -g 1000 bitcoin && \
    useradd -r -u 1000 -g bitcoin -m -d /home/bitcoin bitcoin

# Copy files with proper ownership
COPY --chown=bitcoin:bitcoin docker-entrypoint.sh /usr/local/bin/entrypoint.sh
COPY --chown=bitcoin:bitcoin bitcoin.conf /home/bitcoin/.bitcoin/bitcoin.conf

# Make entrypoint executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Switch to non-root user
USER bitcoin
WORKDIR /home/bitcoin

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bitcoind", "-daemonwait"]
