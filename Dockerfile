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

# Copy Bitcoin binaries from the provided tar.gz
COPY bitcoin-d4a86277ed8a-x86_64-linux-gnu.tar.gz /tmp/
RUN cd /tmp && \
    tar -xzvf bitcoin-d4a86277ed8a-x86_64-linux-gnu.tar.gz -C /usr/local/bin --strip-components=2 \
    "bitcoin-d4a86277ed8a/bin/bitcoin-cli" \
    "bitcoin-d4a86277ed8a/bin/bitcoind" \
    "bitcoin-d4a86277ed8a/bin/bitcoin-wallet" \
    "bitcoin-d4a86277ed8a/bin/bitcoin-util" && \
    rm bitcoin-d4a86277ed8a-x86_64-linux-gnu.tar.gz

COPY docker-entrypoint.sh /usr/local/bin/entrypoint.sh
COPY bitcoin.conf /root/.bitcoin/bitcoin.conf

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bitcoind", "-daemonwait"]
