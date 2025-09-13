#!/bin/bash

# Enable Docker buildx multi-platform support
docker buildx create --name multibuilder --use 2>/dev/null || docker buildx use multibuilder

# Build for multiple platforms
echo "Building multi-platform Docker image..."
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag mutinynet-bitcoind:latest \
  --load \
  .

echo "Build complete!"
echo ""
echo "To push to a registry (optional):"
echo "docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 --tag your-registry/mutinynet-bitcoind:latest --push ."