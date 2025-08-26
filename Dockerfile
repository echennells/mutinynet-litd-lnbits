FROM debian:bullseye-slim
LABEL org.opencontainers.image.authors="NBD"
LABEL org.opencontainers.image.licenses=MIT

ENV BITCOIN_DIR=/root/.bitcoin
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

# Install dependencies
RUN apt-get update && \
    apt-get install -qq --no-install-recommends ca-certificates dirmngr gosu wget libc6 procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Download and install Bitcoin Core 29.1
ARG BITCOIN_VERSION=29.1
ARG ARCH=x86_64
RUN cd /tmp && \
    wget https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz && \
    wget https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/SHA256SUMS && \
    grep "bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz" SHA256SUMS | sha256sum -c - && \
    tar -xzvf bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz -C /usr/local/bin --strip-components=2 \
    "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-cli" \
    "bitcoin-${BITCOIN_VERSION}/bin/bitcoind" \
    "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-wallet" \
    "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-util" && \
    rm bitcoin-${BITCOIN_VERSION}-${ARCH}-linux-gnu.tar.gz SHA256SUMS

COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
COPY bitcoin.conf /root/.bitcoin/bitcoin.conf

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bitcoind", "-daemonwait"]
