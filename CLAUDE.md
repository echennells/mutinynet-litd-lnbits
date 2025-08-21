# Mutinynet Lightning Terminal + LNbits Setup

## Important Notes

### Bitcoin Configuration
This project uses **Mutinynet**, a custom signet with 30-second block times. Key requirements:

1. **Custom Bitcoin Build Required**: Uses `bitcoin-d4a86277ed8a-x86_64-linux-gnu.tar.gz` - NOT the standard bitcoin/bitcoin Docker image
2. **Critical Configuration**: The `signetchallenge` MUST be set correctly in bitcoin.conf:
   ```
   signetchallenge=512102f7561d208dd9ae99bf497273e16f389bdbd6c4742ddb8e6b216e64fa2928ad8f51ae
   ```
   Without this, Bitcoin will sync mainnet instead of signet/mutinynet.

### Known Issues and Fixes

1. **Debian Buster EOL**: The Dockerfile uses `debian:bullseye-slim` (not buster-slim which is EOL)
2. **Bitcoin Sync Issues**: If Bitcoin gets stuck at block 4000 or syncs mainnet, check:
   - Using custom Bitcoin build (not standard image)
   - signetchallenge is properly configured
   - Data directory is clean (delete and restart if corrupted)

### Digital Ocean Deployment

Scripts are available in `scripts/do/`:
- `manage-mutinynet.py` - Infrastructure management (create, start, stop, destroy)
- `deploy.py` - Application deployment (setup, deploy, start, stop, status, logs)

The deployment uses:
- 2 vCPU, 4GB RAM droplet (~$26/month when running, ~$2/month when stopped)
- 50GB persistent volume for blockchain data
- Custom Bitcoin build with proper mutinynet configuration

### Testing Commands

```bash
# Check if Bitcoin is syncing properly
docker exec bitcoind bitcoin-cli -rpcuser=bitcoin -rpcpassword=bitcoin getblockchaininfo

# Should show:
# - chain: "signet"
# - blocks: increasing number
# - headers: ~2,300,000+
```

### CI/CD
GitHub Actions workflow available in `.github/workflows/ci.yml` for testing the stack.

### GitHub Administration
The `gh` CLI tool can be used to manage GitHub Actions, read workflow logs, and add repository secrets - useful for debugging CI/CD issues.