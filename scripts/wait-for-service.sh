#!/bin/bash

# Wait for a service to be available
# Usage: ./wait-for-service.sh <service_name> <port> <timeout_seconds>

SERVICE=$1
PORT=$2
TIMEOUT=${3:-60}

echo "Waiting for $SERVICE on port $PORT (timeout: ${TIMEOUT}s)..."

COUNTER=0
while ! nc -z localhost $PORT 2>/dev/null; do
    if [ $COUNTER -ge $TIMEOUT ]; then
        echo "ERROR: $SERVICE failed to start within ${TIMEOUT} seconds"
        exit 1
    fi
    echo "Waiting for $SERVICE... ($COUNTER/$TIMEOUT)"
    sleep 1
    COUNTER=$((COUNTER + 1))
done

echo "$SERVICE is ready on port $PORT"