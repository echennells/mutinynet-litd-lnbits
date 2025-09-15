#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if Tor was enabled
if [ "$ENABLE_TOR" = "true" ]; then
    echo "Stopping services with Tor support..."
    docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.tor.yml down
else
    echo "Stopping services..."
    docker compose down
fi