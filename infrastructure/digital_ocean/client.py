"""
Digital Ocean API client for managing Mutinynet Bitcoin infrastructure
"""
import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import (
    DIGITAL_OCEAN_API_KEY, 
    DIGITAL_OCEAN_API_BASE,
    VOLUME_NAME,
    FIREWALL_NAME,
    RESERVED_IP_NAME,
    SSH_KEY_NAME
)


class MutinynetDOClient:
    """Client for managing Mutinynet infrastructure on Digital Ocean"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or DIGITAL_OCEAN_API_KEY
        if not self.api_key:
            raise ValueError("Digital Ocean API key not provided. Set DO_API_KEY environment variable.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.base_url = DIGITAL_OCEAN_API_BASE
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
                try:
                    error_data = e.response.json()
                    if 'errors' in error_data:
                        for error in error_data['errors']:
                            print(f"Error: {error}")
                except:
                    pass
            raise
    
    def find_mutinynet_droplet(self) -> Optional[Dict]:
        """Find existing Mutinynet droplet by tag"""
        droplets = self._request("GET", "droplets?tag_name=mutinynet")
        droplets_list = droplets.get("droplets", [])
        return droplets_list[0] if droplets_list else None
    
    def get_or_create_volume(self) -> Dict:
        """Get existing volume or create new one"""
        # Check for existing volume
        volumes = self._request("GET", f"volumes?name={VOLUME_NAME}")
        volume_list = volumes.get("volumes", [])
        
        if volume_list:
            print(f"Found existing volume: {VOLUME_NAME}")
            return volume_list[0]
        
        # Create new volume
        print(f"Creating new volume: {VOLUME_NAME}")
        from .config import VOLUME_SIZE_GB, VOLUME_FILESYSTEM_TYPE, DEFAULT_REGION
        
        data = {
            "size_gigabytes": VOLUME_SIZE_GB,
            "name": VOLUME_NAME,
            "description": "Persistent storage for Mutinynet Bitcoin blockchain data",
            "region": DEFAULT_REGION,
            "filesystem_type": VOLUME_FILESYSTEM_TYPE
        }
        
        result = self._request("POST", "volumes", data)
        return result["volume"]
    
    def get_or_create_reserved_ip(self) -> Dict:
        """Get existing reserved IP or create new one"""
        from .config import USE_RESERVED_IP
        
        if not USE_RESERVED_IP:
            return {}
        
        # Check for existing reserved IP
        ips = self._request("GET", "reserved_ips")
        for ip in ips.get("reserved_ips", []):
            if ip.get("name") == RESERVED_IP_NAME:
                print(f"Found existing reserved IP: {ip['ip']}")
                return ip
        
        # Create new reserved IP
        print(f"Creating new reserved IP: {RESERVED_IP_NAME}")
        from .config import DEFAULT_REGION
        
        data = {
            "type": "regional",
            "region": DEFAULT_REGION,
            "name": RESERVED_IP_NAME
        }
        
        result = self._request("POST", "reserved_ips", data)
        return result["reserved_ip"]
    
    def create_mutinynet_droplet(self, ssh_keys: List[str]) -> Dict:
        """Create a new Mutinynet droplet with all configurations"""
        from .config import (
            DEFAULT_DROPLET_SIZE, DEFAULT_IMAGE, DEFAULT_REGION,
            DEFAULT_DROPLET_TAGS, REMOTE_WORKSPACE
        )
        
        # Get or create volume first
        volume = self.get_or_create_volume()
        
        # Get or create reserved IP
        reserved_ip = self.get_or_create_reserved_ip()
        
        # User data script to set up the droplet
        user_data = f"""#!/bin/bash
set -e

echo "Starting Mutinynet Bitcoin node setup..."

# Create directories
mkdir -p {REMOTE_WORKSPACE}
mkdir -p /mnt/mutinynet-volume

# Mount volume (format only if not already formatted)
if ! mount | grep -q /mnt/mutinynet-volume; then
    # Check if volume already has a filesystem
    if ! blkid /dev/disk/by-id/scsi-0DO_Volume_{VOLUME_NAME} | grep -q ext4; then
        echo "Formatting new volume..."
        mkfs.ext4 /dev/disk/by-id/scsi-0DO_Volume_{VOLUME_NAME}
    else
        echo "Volume already formatted, mounting..."
    fi
    mount /dev/disk/by-id/scsi-0DO_Volume_{VOLUME_NAME} /mnt/mutinynet-volume
    echo "/dev/disk/by-id/scsi-0DO_Volume_{VOLUME_NAME} /mnt/mutinynet-volume ext4 defaults,nofail,discard 0 2" >> /etc/fstab
fi

# Install Docker Compose
apt-get update
apt-get install -y docker-compose

# Clone the repository
cd {REMOTE_WORKSPACE}
git clone https://github.com/echennells/mutinynet-litd-lnbits.git . || true

# Copy deploy files to expected location
cp -r deploy/* ./ 2>/dev/null || true
cp deploy/bitcoin.conf /mnt/mutinynet-volume/bitcoin/bitcoin.conf 2>/dev/null || true

# Ensure bitcoin directory exists on volume
mkdir -p /mnt/mutinynet-volume/bitcoin

# Start Bitcoin container
cd {REMOTE_WORKSPACE}
docker-compose up -d bitcoind

# Create systemd service to start Bitcoin on boot
cat > /etc/systemd/system/bitcoin-mutinynet.service << 'EOF'
[Unit]
Description=Mutinynet Bitcoin Node
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory={REMOTE_WORKSPACE}
ExecStart=/usr/bin/docker-compose up -d bitcoind
ExecStop=/usr/bin/docker-compose down
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bitcoin-mutinynet.service

echo "Setup complete! Bitcoin starting..."
"""
        
        droplet_name = f"mutinynet-bitcoin-{int(time.time())}"
        
        data = {
            "name": droplet_name,
            "size": DEFAULT_DROPLET_SIZE,
            "image": DEFAULT_IMAGE,
            "region": DEFAULT_REGION,
            "ssh_keys": ssh_keys,
            "tags": DEFAULT_DROPLET_TAGS,
            "user_data": user_data,
            "volumes": [volume["id"]],
            "backups": False,
            "ipv6": True,
            "monitoring": True
        }
        
        print(f"Creating droplet: {droplet_name}")
        result = self._request("POST", "droplets", data)
        droplet = result["droplet"]
        
        # Assign reserved IP if we have one
        if reserved_ip:
            print(f"Waiting for droplet to be active...")
            self.wait_for_droplet_active(droplet["id"])
            self.assign_reserved_ip(reserved_ip["ip"], droplet["id"])
        
        # Create or update firewall
        self.create_or_update_firewall([droplet["id"]])
        
        return droplet
    
    def wait_for_droplet_active(self, droplet_id: int, timeout: int = 300) -> bool:
        """Wait for droplet to become active"""
        start_time = time.time()
        # Initial delay to let the API catch up
        time.sleep(10)
        
        while time.time() - start_time < timeout:
            try:
                droplet = self._request("GET", f"droplets/{droplet_id}")["droplet"]
                if droplet["status"] == "active":
                    return True
            except Exception as e:
                # 404 errors are expected initially while droplet is being created
                if "404" not in str(e):
                    print(f"Error checking droplet status: {e}")
            time.sleep(5)
        return False
    
    def assign_reserved_ip(self, ip_address: str, droplet_id: int) -> None:
        """Assign reserved IP to droplet"""
        data = {
            "type": "assign",
            "droplet_id": droplet_id
        }
        self._request("POST", f"reserved_ips/{ip_address}/actions", data)
        print(f"Assigned reserved IP {ip_address} to droplet {droplet_id}")
    
    def start_droplet(self, droplet_id: int) -> None:
        """Start a stopped droplet"""
        print(f"Starting droplet {droplet_id}...")
        self._request("POST", f"droplets/{droplet_id}/actions", {"type": "power_on"})
    
    def stop_droplet(self, droplet_id: int) -> None:
        """Stop a running droplet (keeps volume attached)"""
        print(f"Stopping droplet {droplet_id}...")
        self._request("POST", f"droplets/{droplet_id}/actions", {"type": "power_off"})
    
    def get_droplet_ip(self, droplet_id: int) -> Optional[str]:
        """Get the public IP of a droplet"""
        droplet = self._request("GET", f"droplets/{droplet_id}")["droplet"]
        
        # Check for reserved IP first
        for network in droplet.get("networks", {}).get("v4", []):
            if network.get("type") == "public":
                return network.get("ip_address")
        
        return None
    
    def destroy_droplet_keep_volume(self, droplet_id: int) -> None:
        """Destroy droplet but keep the volume for next time"""
        print(f"Destroying droplet {droplet_id} (keeping volume)...")
        self._request("DELETE", f"droplets/{droplet_id}")
    
    def list_ssh_keys(self) -> List[Dict]:
        """List all SSH keys in the account"""
        result = self._request("GET", "account/keys")
        return result.get("ssh_keys", [])
    
    def create_ssh_key(self, name: str, public_key: str) -> Dict:
        """Create a new SSH key in Digital Ocean"""
        data = {
            "name": name,
            "public_key": public_key
        }
        result = self._request("POST", "account/keys", data)
        return result["ssh_key"]
    
    def get_ssh_key_by_name(self, name: str) -> Optional[Dict]:
        """Get SSH key by name"""
        keys = self.list_ssh_keys()
        for key in keys:
            if key["name"] == name:
                return key
        return None
    
    def create_or_update_firewall(self, droplet_ids: List[int]) -> Dict:
        """Create or update firewall rules"""
        # Check for existing firewall
        response = self._request("GET", "firewalls")
        for fw in response.get("firewalls", []):
            if fw.get("name") == FIREWALL_NAME:
                print(f"Updating existing firewall: {FIREWALL_NAME}")
                # For updates, just assign droplets - don't need to resend rules
                # Use the firewall assign endpoint instead of PUT
                for droplet_id in droplet_ids:
                    try:
                        self._request("POST", f"firewalls/{fw['id']}/droplets", {
                            "droplet_ids": [droplet_id]
                        })
                    except Exception as e:
                        print(f"Note: Droplet might already be in firewall: {e}")
                return fw
        
        # Create new firewall
        print(f"Creating firewall: {FIREWALL_NAME}")
        
        # GitHub Actions IP ranges (these change, so we need to be more permissive)
        # In production, you'd fetch these from https://api.github.com/meta
        inbound_rules = [
            # SSH - restrict to specific IPs if possible
            {
                "protocol": "tcp",
                "ports": "22",
                "sources": {
                    "addresses": ["0.0.0.0/0", "::/0"]  # TODO: Restrict this
                }
            },
            # Bitcoin RPC - for testing
            {
                "protocol": "tcp", 
                "ports": "38332",
                "sources": {
                    "addresses": ["0.0.0.0/0", "::/0"]  # TODO: Restrict to GitHub Actions
                }
            },
            # Bitcoin P2P - needs to be open for peer connections
            {
                "protocol": "tcp",
                "ports": "38333", 
                "sources": {
                    "addresses": ["0.0.0.0/0", "::/0"]
                }
            },
            # ZMQ ports
            {
                "protocol": "tcp",
                "ports": "28332-28334",
                "sources": {
                    "addresses": ["0.0.0.0/0", "::/0"]  # TODO: Restrict to GitHub Actions
                }
            }
        ]
        
        # Outbound - allow everything
        outbound_rules = [
            {
                "protocol": "tcp",
                "ports": "all",
                "destinations": {
                    "addresses": ["0.0.0.0/0", "::/0"]
                }
            },
            {
                "protocol": "udp",
                "ports": "all", 
                "destinations": {
                    "addresses": ["0.0.0.0/0", "::/0"]
                }
            }
        ]
        
        data = {
            "name": FIREWALL_NAME,
            "inbound_rules": inbound_rules,
            "outbound_rules": outbound_rules,
            "droplet_ids": droplet_ids,
            "tags": ["mutinynet"]
        }
        
        result = self._request("POST", "firewalls", data)
        return result.get("firewall", {})
    
    def ensure_ssh_key(self) -> str:
        """Ensure SSH key exists in DO account, create if needed"""
        from pathlib import Path
        
        # Check if key already exists in DO
        existing_key = self.get_ssh_key_by_name(SSH_KEY_NAME)
        if existing_key:
            print(f"Found existing SSH key: {SSH_KEY_NAME}")
            return str(existing_key["id"])
        
        # Check for local SSH key
        ssh_key_path = Path.home() / ".ssh" / "id_rsa"
        pub_key_path = ssh_key_path.with_suffix('.pub')
        
        if not pub_key_path.exists():
            print(f"No SSH public key found at {pub_key_path}")
            print("Generating new SSH key pair...")
            import subprocess
            subprocess.run([
                "ssh-keygen", "-t", "rsa", "-b", "4096", 
                "-f", str(ssh_key_path), "-N", "", "-q"
            ])
        
        # Read public key
        with open(pub_key_path, 'r') as f:
            public_key = f.read().strip()
        
        # Check if this key fingerprint already exists under a different name
        print("Checking existing SSH keys in your DO account...")
        all_keys = self.list_ssh_keys()
        
        # Try to match by key content (DO might already have this key)
        for key in all_keys:
            if key.get('public_key') == public_key:
                print(f"Found same SSH key with name: {key['name']}")
                return str(key["id"])
        
        # Create SSH key in DO
        print(f"Adding SSH key to Digital Ocean: {SSH_KEY_NAME}")
        try:
            new_key = self.create_ssh_key(SSH_KEY_NAME, public_key)
            print(f"SSH key added successfully!")
            return str(new_key["id"])
        except Exception as e:
            # If it fails, just use the first available key
            if all_keys:
                print(f"Failed to add key, using existing key: {all_keys[0]['name']}")
                return str(all_keys[0]["id"])
            raise
    
    def get_monthly_cost_estimate(self) -> Dict[str, float]:
        """Calculate estimated monthly costs"""
        from .config import DROPLET_SIZES, DEFAULT_DROPLET_SIZE, VOLUME_SIZE_GB
        
        droplet_cost = DROPLET_SIZES[DEFAULT_DROPLET_SIZE]["price"]
        volume_cost = VOLUME_SIZE_GB * 0.10  # $0.10 per GB per month
        reserved_ip_cost = 0  # Free when assigned to droplet, $4/month when unassigned
        
        return {
            "droplet": droplet_cost,
            "volume": volume_cost,
            "reserved_ip": reserved_ip_cost,
            "total": droplet_cost + volume_cost + reserved_ip_cost
        }