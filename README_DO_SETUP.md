# Digital Ocean Mutinynet Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Check Your SSH Key
Make sure you have an SSH key at `~/.ssh/id_rsa`:
```bash
ls -la ~/.ssh/id_rsa*
```

If not, generate one:
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
```

### 3. Add SSH Key to Digital Ocean
1. Get your public key:
   ```bash
   cat ~/.ssh/id_rsa.pub
   ```
2. Add it to DO: https://cloud.digitalocean.com/account/security
3. Name it something with "mutinynet" in it

### 4. Create Your Bitcoin Node
```bash
# The API key is already configured from xtotext
python scripts/do/manage-mutinynet.py create
```

This will:
- Create a $24/month droplet (2 vCPU, 4GB RAM)
- Attach a 20GB persistent volume ($2/month)
- Set up Docker and clone your repo
- Give you a static IP address

### 5. Start/Stop to Save Money
```bash
# Stop when not using (saves $24/month)
python scripts/do/manage-mutinynet.py stop

# Start when needed
python scripts/do/manage-mutinynet.py start

# Check status
python scripts/do/manage-mutinynet.py status
```

## Cost Breakdown

| Resource | Cost | Notes |
|----------|------|-------|
| Droplet (s-2vcpu-4gb) | $24/month | Only when running |
| Volume (20GB) | $2/month | Always (stores blockchain) |
| Reserved IP | $0/month | Free when assigned |
| **Total (24/7)** | **$26/month** | If always running |
| **Total (stopped)** | **$2/month** | Just volume storage |

## Running Your Stack

### 1. SSH into the droplet
```bash
# Get IP from status command
python scripts/do/manage-mutinynet.py status

# SSH in
ssh root@<IP_ADDRESS>
```

### 2. Start Bitcoin + Lightning
```bash
cd /opt/mutinynet
docker-compose up -d bitcoind
# Wait for sync...
docker-compose up -d
```

### 3. Access Services
- Bitcoin RPC: `http://<IP>:38332`
- Lightning Terminal: `https://<IP>:8443`
- LNbits: `http://<IP>:5000`

## CI/CD Integration

The GitHub Actions workflow will:
1. Start the DO droplet automatically
2. Run tests against it
3. **Stop it after tests to save money**

Just add the secret to GitHub:
```bash
# Your DO API key is already in config.py
# Add it to GitHub: Settings -> Secrets -> Actions
# Name: DO_API_KEY
# Value: your-digital-ocean-api-key-here
```

## Commands Reference

```bash
# Management commands
python scripts/do/manage-mutinynet.py create   # Create new infrastructure
python scripts/do/manage-mutinynet.py start    # Start stopped droplet
python scripts/do/manage-mutinynet.py stop     # Stop to save money
python scripts/do/manage-mutinynet.py status   # Check everything
python scripts/do/manage-mutinynet.py costs    # Show cost breakdown
python scripts/do/manage-mutinynet.py destroy  # Remove droplet (keeps volume)
```

## Tips

1. **Always stop when not using** - Saves $24/month
2. **Volume persists** - Blockchain data survives droplet destruction
3. **Reserved IP** - Same IP even after destroy/recreate
4. **Auto-shutdown** - Set up a cron job to auto-stop after 2 hours

## Troubleshooting

### Can't connect via SSH
- Check your SSH key is added to DO
- Check firewall rules allow port 22
- Try: `ssh -v root@<IP>` for debug info

### Bitcoin not syncing
- Check logs: `docker logs bitcoind`
- Mutinynet has 30-second blocks, should sync fast
- Make sure port 38333 is open

### Out of disk space
- The 20GB volume should be plenty for mutinynet
- Check: `df -h /mnt/mutinynet-volume`
- Can resize to 30GB or 40GB in DO console if needed (adds $1-2/month)