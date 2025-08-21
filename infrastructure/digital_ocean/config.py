"""
Digital Ocean configuration for Mutinynet Bitcoin node
"""
import os
from pathlib import Path

# API Configuration
# Try environment variable first, then load from main config
DIGITAL_OCEAN_API_KEY = os.getenv("DO_API_KEY", "")
if not DIGITAL_OCEAN_API_KEY:
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from config import DIGITAL_OCEAN_API_KEY as CONFIG_DO_KEY
        DIGITAL_OCEAN_API_KEY = CONFIG_DO_KEY
    except:
        pass

DIGITAL_OCEAN_API_BASE = "https://api.digitalocean.com/v2"

# Droplet Configuration for Bitcoin Node
# Using the cheapest droplet that can handle Bitcoin + pruning
DEFAULT_DROPLET_SIZE = "s-2vcpu-4gb"  # $24/month - cheapest viable option
DEFAULT_REGION = "nyc3"  # New York datacenter
DEFAULT_IMAGE = "docker-20-04"  # Ubuntu 20.04 with Docker pre-installed
DEFAULT_DROPLET_TAGS = ["mutinynet", "bitcoin", "ci-cd"]

# Droplet Sizes and Pricing (as of 2025)
DROPLET_SIZES = {
    "s-1vcpu-2gb": {"vcpus": 1, "memory": 2048, "disk": 50, "price": 12},  # Too small for Bitcoin
    "s-2vcpu-4gb": {"vcpus": 2, "memory": 4096, "disk": 80, "price": 24},  # Minimum viable
    "s-2vcpu-8gb": {"vcpus": 2, "memory": 8192, "disk": 160, "price": 48}, # Comfortable
    "s-4vcpu-8gb": {"vcpus": 4, "memory": 8192, "disk": 160, "price": 48}, # Better CPU
}

# Volume Configuration (persistent storage for blockchain)
# Mutinynet is much smaller than mainnet - 20GB should be plenty
# Even with growth, mutinynet with 30s blocks shouldn't exceed this
VOLUME_SIZE_GB = 20  # 20GB for mutinynet blockchain (costs $2/month)
VOLUME_FILESYSTEM_TYPE = "ext4"
VOLUME_NAME = "mutinynet-blockchain-data"

# SSH Configuration
SSH_KEY_NAME = "mutinynet-key"
SSH_USERNAME = "root"
SSH_PORT = 22
SSH_TIMEOUT = 120  # 2 minutes for high jitter networks

# Paths
REMOTE_WORKSPACE = "/opt/mutinynet"
REMOTE_DATA_DIR = "/mnt/mutinynet-volume"
REMOTE_BITCOIN_DATA = f"{REMOTE_DATA_DIR}/bitcoin"

# Firewall Configuration
FIREWALL_NAME = "mutinynet-firewall"
FIREWALL_RULES = [
    # SSH
    {"protocol": "tcp", "ports": "22", "sources": ["0.0.0.0/0", "::/0"]},
    # Bitcoin P2P (Mutinynet signet)
    {"protocol": "tcp", "ports": "38333", "sources": ["0.0.0.0/0", "::/0"]},
    # Bitcoin RPC (restricted)
    {"protocol": "tcp", "ports": "38332", "sources": ["0.0.0.0/0", "::/0"]},
    # ZMQ ports
    {"protocol": "tcp", "ports": "28332-28334", "sources": ["0.0.0.0/0", "::/0"]},
]

# Reserved IP for consistent access
USE_RESERVED_IP = True
RESERVED_IP_NAME = "mutinynet-ip"

# Cost Optimization Settings
AUTO_SHUTDOWN_HOURS = 2  # Auto shutdown after 2 hours of inactivity
SNAPSHOT_BEFORE_DESTROY = True  # Create snapshot before destroying droplet

# Bitcoin RPC Credentials (generate random ones if not set)
import secrets
import string
def generate_password(length=20):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

BITCOIN_RPC_USER = os.getenv("BITCOIN_RPC_USER", "mutinynet")
BITCOIN_RPC_PASSWORD = os.getenv("BITCOIN_RPC_PASSWORD", generate_password())