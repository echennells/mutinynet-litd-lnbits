#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if Tor should be enabled
if [ "$ENABLE_TOR" = "true" ]; then
    echo "Starting with Tor support..."
    docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.tor.yml up -d
else
    echo "Starting without Tor..."
    docker compose up -d
fi