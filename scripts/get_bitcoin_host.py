#!/usr/bin/env python3
"""
Get Bitcoin host IP from Digital Ocean API
Used by GitHub Actions to find the current droplet IP
"""
import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.digital_ocean.client import MutinynetDOClient

def get_bitcoin_host():
    """Get the current Bitcoin droplet IP"""
    try:
        client = MutinynetDOClient()
        droplet = client.find_mutinynet_droplet()
        
        if not droplet:
            print("No Bitcoin droplet found", file=sys.stderr)
            return None
        
        if droplet['status'] != 'active':
            # Start it if it's stopped
            print(f"Starting droplet (status: {droplet['status']})...", file=sys.stderr)
            client.start_droplet(droplet['id'])
            client.wait_for_droplet_active(droplet['id'])
            # Refresh droplet info
            droplet = client.find_mutinynet_droplet()
        
        # Get IP
        ip = client.get_droplet_ip(droplet['id'])
        
        # Output just the IP for easy capture in GitHub Actions
        print(ip)
        return ip
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    ip = get_bitcoin_host()
    sys.exit(0 if ip else 1)