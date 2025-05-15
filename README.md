# Taproot Assets Protocol Command Reference Guide

## Minting a Taproot Asset - Complete Workflow

### 1. Mint the Asset

```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon assets mint --type normal --name mycoin --supply 1000 --meta_bytes "My first Taproot Asset"
```

Parameters explained:
- `--type normal`: Creates a fungible asset (alternative: `collectible`)
- `--name mycoin`: The name of your asset
- `--supply 1000`: Total asset quantity to mint
- `--meta_bytes "..."`: Metadata associated with the asset

### 2. Finalize the Mint

```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon assets mint finalize
```

This commits the mint to the blockchain, creating an on-chain transaction.

### 3. List Your Assets

```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon assets list
```

Note the `asset_id` from the output - you'll need it for future operations.

## Universe Commands

### Basic Universe Operations

**Check Universe Information**
```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon universe info
```

**View Universe Roots**
```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon universe roots
```

### Publishing to a Universe

**1. Configure Universe Access in tapd.conf**
```
[taproot-assets.universe]
public-access=r
```
Add this to your `tapd.conf` file then restart tapd:
```bash
docker restart lit
```

**2. Configure Federation Settings**
```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon universe federation config global --proof_type issuance --allow_insert true --allow_export true
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon universe federation config global --proof_type transfer --allow_insert true --allow_export true
```

**3. Check Federation Configuration**
```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon universe federation config info
```

### Universe Syncing

**Sync with Another Universe**
```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon universe sync --universe_host <host:port> --asset_id <asset_id>
```

**Add Universe to Federation**
```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon universe federation add --universe_host <host:port>
```

**List Federation Universes**
```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon universe federation list
```

**Remove Universe from Federation**
```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon universe federation del --universe_host <host:port>
```

## Asset Transfer Commands

**Generate Receiving Address**
```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon addrs new --asset_id <asset_id> --amt <amount>
```

**Send Assets**
```bash
docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon assets send --addr <encoded_address>
```

## Step-by-Step: Minting a Taproot Asset

1. **Ensure Prerequisites**
   - Running `lnd` node with Bitcoin (testnet/signet/mainnet)
   - Running `tapd` node connected to `lnd`
   - Some bitcoin in your wallet for transaction fees

2. **Create the Asset**
   ```bash
   docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon assets mint --type normal --name mycoin --supply 1000 --meta_bytes "My first Taproot Asset"
   ```

3. **Finalize the Mint**
   ```bash
   docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon assets mint finalize
   ```
   This creates an on-chain transaction. Wait for at least one confirmation before proceeding.

4. **Verify Your Asset**
   ```bash
   docker exec lit tapcli --network signet --rpcserver localhost:10009 --tlscertpath /root/.lnd/tls.cert --macaroonpath /root/.tapd/data/signet/admin.macaroon assets list
   ```
   Note your `asset_id` from the output.

5. **Publish to Universe** (Optional, for public discovery)
   - Configure your universe for public access
   - Ensure your federation settings allow exporting proofs
   - Anyone can now sync your asset by its ID

6. **Use Your Asset**
   - Generate addresses to receive the asset
   - Send portions of your asset to other addresses
   - Verify balances using the `assets list` command

## Tips for Using Taproot Assets

1. **Network Parameter**: Always include the correct `--network` parameter (mainnet, testnet, signet) to avoid confusion.

2. **Asset Types**:
   - `normal`: Fungible assets (can be split into units)
   - `collectible`: Non-fungible assets (unique, indivisible)

3. **Universe Access Levels**:
   - `r`: Read-only access (others can only read your universe)
   - `rw`: Read-write access (others can read and write to your universe)
