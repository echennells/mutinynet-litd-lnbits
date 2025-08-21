#!/usr/bin/env python3
"""
Management script for Mutinynet Bitcoin node on Digital Ocean

Usage:
    python manage-mutinynet.py start    # Start the droplet
    python manage-mutinynet.py stop     # Stop the droplet (save money)
    python manage-mutinynet.py status   # Check status
    python manage-mutinynet.py create   # Create new droplet with volume
    python manage-mutinynet.py destroy  # Destroy droplet (keep volume)
    python manage-mutinynet.py costs    # Show cost breakdown
"""

import sys
import os
import time
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.digital_ocean.client import MutinynetDOClient
from infrastructure.digital_ocean.config import (
    DEFAULT_DROPLET_SIZE,
    VOLUME_SIZE_GB,
    SSH_KEY_NAME
)


def get_ssh_keys(client):
    """Get or create SSH keys in DO account"""
    # This will automatically create the key if it doesn't exist
    ssh_key_id = client.ensure_ssh_key()
    return [ssh_key_id]


def cmd_create(client):
    """Create new Mutinynet droplet"""
    # Check if droplet already exists
    existing = client.find_mutinynet_droplet()
    if existing:
        print(f"Droplet already exists: {existing['name']} (ID: {existing['id']})")
        return
    
    # Get or create SSH keys automatically
    ssh_keys = get_ssh_keys(client)
    
    # Create droplet
    droplet = client.create_mutinynet_droplet(ssh_keys)
    print(f"Created droplet: {droplet['name']} (ID: {droplet['id']})")
    
    # Wait for it to be active
    print("Waiting for droplet to become active...")
    if client.wait_for_droplet_active(droplet['id']):
        ip = client.get_droplet_ip(droplet['id'])
        print(f"Droplet is active! IP: {ip}")
        print(f"\nSSH command: ssh root@{ip}")
        print(f"\nBitcoin RPC will be available at: {ip}:38332")
    else:
        print("Warning: Droplet took too long to become active")


def cmd_start(client):
    """Start stopped Mutinynet droplet"""
    droplet = client.find_mutinynet_droplet()
    if not droplet:
        print("No Mutinynet droplet found. Run 'create' first.")
        sys.exit(1)
    
    if droplet['status'] == 'active':
        print(f"Droplet {droplet['name']} is already running")
        ip = client.get_droplet_ip(droplet['id'])
        print(f"IP: {ip}")
    else:
        client.start_droplet(droplet['id'])
        print(f"Starting droplet {droplet['name']}...")
        time.sleep(10)
        
        # Wait for active status
        if client.wait_for_droplet_active(droplet['id']):
            ip = client.get_droplet_ip(droplet['id'])
            print(f"Droplet started! IP: {ip}")
        else:
            print("Warning: Droplet took too long to start")


def cmd_stop(client):
    """Stop running Mutinynet droplet to save costs"""
    droplet = client.find_mutinynet_droplet()
    if not droplet:
        print("No Mutinynet droplet found.")
        sys.exit(1)
    
    if droplet['status'] != 'active':
        print(f"Droplet {droplet['name']} is not running (status: {droplet['status']})")
    else:
        client.stop_droplet(droplet['id'])
        print(f"Stopping droplet {droplet['name']}...")
        print("Note: Volume data is preserved. You can start it again anytime.")


def cmd_status(client):
    """Check status of Mutinynet infrastructure"""
    print("=== Mutinynet Infrastructure Status ===\n")
    
    # Check droplet
    droplet = client.find_mutinynet_droplet()
    if droplet:
        print(f"Droplet: {droplet['name']}")
        print(f"  Status: {droplet['status']}")
        print(f"  Size: {droplet['size']['slug']}")
        print(f"  Region: {droplet['region']['slug']}")
        
        if droplet['status'] == 'active':
            ip = client.get_droplet_ip(droplet['id'])
            print(f"  IP: {ip}")
            print(f"  Bitcoin RPC: http://{ip}:38332")
            print(f"  SSH: ssh root@{ip}")
    else:
        print("Droplet: Not found")
    
    # Check volume
    volumes = client._request("GET", f"volumes?name={client.get_or_create_volume()['name']}")
    if volumes.get("volumes"):
        volume = volumes["volumes"][0]
        print(f"\nVolume: {volume['name']}")
        print(f"  Size: {volume['size_gigabytes']}GB")
        print(f"  Status: {'Attached' if volume.get('droplet_ids') else 'Detached'}")
    
    # Check reserved IP
    ips = client._request("GET", "reserved_ips")
    for ip in ips.get("reserved_ips", []):
        if "mutinynet" in ip.get("name", "").lower():
            print(f"\nReserved IP: {ip['ip']}")
            print(f"  Status: {'Assigned' if ip.get('droplet') else 'Unassigned'}")
            break


def cmd_destroy(client, force=False):
    """Destroy droplet but keep volume"""
    droplet = client.find_mutinynet_droplet()
    if not droplet:
        print("No Mutinynet droplet found.")
        return
    
    if not force:
        response = input(f"Are you sure you want to destroy {droplet['name']}? Volume will be preserved. (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    client.destroy_droplet_keep_volume(droplet['id'])
    print(f"Destroyed droplet {droplet['name']}. Volume preserved for next deployment.")


def cmd_costs(client):
    """Show cost breakdown"""
    costs = client.get_monthly_cost_estimate()
    
    print("=== Monthly Cost Estimate ===\n")
    print(f"Droplet ({DEFAULT_DROPLET_SIZE}): ${costs['droplet']:.2f}")
    print(f"Volume ({VOLUME_SIZE_GB}GB): ${costs['volume']:.2f}")
    print(f"Reserved IP: ${costs['reserved_ip']:.2f}")
    print(f"------------------------")
    print(f"Total: ${costs['total']:.2f}/month")
    print(f"\nDaily cost: ${costs['total']/30:.2f}")
    print(f"Hourly cost: ${costs['total']/720:.3f}")
    
    print("\n💡 Cost Saving Tips:")
    print("- Stop the droplet when not in use (saves ~$24/month)")
    print("- Volume storage is only $10/month for 100GB")
    print("- Reserved IP is free when assigned to running droplet")


def main():
    parser = argparse.ArgumentParser(description="Manage Mutinynet Bitcoin node on Digital Ocean")
    parser.add_argument("command", choices=["create", "start", "stop", "status", "destroy", "costs"],
                        help="Command to execute")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Skip confirmation prompts (for automation)")
    
    args = parser.parse_args()
    
    # API key is handled by the config file now, no need to check here
    
    # Create client
    client = MutinynetDOClient()
    
    # Execute command
    commands = {
        "create": lambda: cmd_create(client),
        "start": lambda: cmd_start(client),
        "stop": lambda: cmd_stop(client),
        "status": lambda: cmd_status(client),
        "destroy": lambda: cmd_destroy(client, force=args.force),
        "costs": lambda: cmd_costs(client)
    }
    
    commands[args.command]()


if __name__ == "__main__":
    main()