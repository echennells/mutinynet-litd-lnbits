#!/usr/bin/env python3
"""
Deployment script for Mutinynet stack to Digital Ocean

Usage:
    python scripts/do/deploy.py setup    # Initial setup
    python scripts/do/deploy.py deploy   # Deploy/update stack
    python scripts/do/deploy.py start    # Start all services
    python scripts/do/deploy.py stop     # Stop all services
    python scripts/do/deploy.py status   # Check status
    python scripts/do/deploy.py logs     # View logs
"""

import sys
import os
import argparse
from pathlib import Path
import subprocess
import json
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.digital_ocean.client import MutinynetDOClient
from infrastructure.digital_ocean.ssh_connection import SimpleSSHConnection
from infrastructure.digital_ocean.config import BITCOIN_RPC_USER, BITCOIN_RPC_PASSWORD


class MutinynetDeployer:
    """Handles deployment of Mutinynet stack to Digital Ocean"""
    
    def __init__(self):
        self.client = MutinynetDOClient()
        self.droplet = None
        self.ssh = None
        self.ip = None
        
    def get_droplet_info(self):
        """Get droplet information"""
        self.droplet = self.client.find_mutinynet_droplet()
        if not self.droplet:
            print("No Mutinynet droplet found. Run 'python scripts/do/manage-mutinynet.py create' first.")
            sys.exit(1)
        
        if self.droplet['status'] != 'active':
            print(f"Droplet is not active (status: {self.droplet['status']})")
            print("Starting droplet...")
            self.client.start_droplet(self.droplet['id'])
            self.client.wait_for_droplet_active(self.droplet['id'])
            
        self.ip = self.client.get_droplet_ip(self.droplet['id'])
        print(f"Droplet IP: {self.ip}")
        
        # Initialize SSH connection and wait for it to be ready
        self.ssh = SimpleSSHConnection(self.ip)
        print("Waiting for SSH to be ready...")
        for i in range(10):  # Wait up to 50 seconds
            if self.ssh.test_connection():
                print("SSH connection established!")
                return True
            if i < 9:
                time.sleep(5)
        
        print("Warning: SSH connection not established, commands may fail")
        return True
    
    def setup(self):
        """Initial setup of the droplet"""
        print("=== Initial Setup of Mutinynet Stack ===")
        
        if not self.get_droplet_info():
            return False
        
        print("Creating directory structure...")
        setup_commands = [
            # Create directories
            "mkdir -p /opt/mutinynet",
            "mkdir -p /mnt/mutinynet-volume/bitcoin",
            "mkdir -p ~/volumes/.lnd ~/volumes/.lit ~/volumes/.tapd",
            
            # Check if volume is mounted
            "df -h /mnt/mutinynet-volume || echo 'Volume not mounted'",
            
            # Set proper permissions on the bitcoin directory
            "chown -R root:root /mnt/mutinynet-volume/bitcoin",
            "chmod 755 /mnt/mutinynet-volume/bitcoin",
            
            # Install required packages
            "apt-get update",
            "which docker || curl -fsSL https://get.docker.com | sh",
            # Install docker-compose (v2 as docker plugin)
            "which docker-compose || (apt-get install -y curl && curl -SL https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose)",
            "apt-get install -y git curl wget jq",
        ]
        
        for cmd in setup_commands:
            print(f"Running: {cmd}")
            # Retry each command if connection fails
            for attempt in range(3):
                returncode, stdout, stderr = self.ssh.execute_command(cmd, timeout=120)
                if returncode == -1 and "Connection refused" in stderr:
                    print(f"Connection failed, retrying... (attempt {attempt + 1}/3)")
                    time.sleep(2)
                    # Reinitialize SSH connection
                    self.ssh = SimpleSSHConnection(self.ip)
                    continue
                break
            
            if stdout:
                print(f"  Output: {stdout.strip()}")
            if returncode != 0 and "already exists" not in stderr:
                print(f"  Warning: {stderr.strip() if stderr else f'Command failed with code {returncode}'}")
        
        print("Setup completed!")
        return True
    
    def deploy(self):
        """Deploy the stack configuration"""
        print("=== Deploying Mutinynet Stack ===")
        
        if not self.get_droplet_info():
            return False
        
        # Clone the repository on the droplet - combine commands to avoid cd issues
        print("Cloning repository on droplet...")
        
        # Single command to clone - more reliable with high latency
        clone_cmd = "cd /opt && rm -rf mutinynet-litd-lnbits && git clone https://github.com/echennells/mutinynet-litd-lnbits.git && ls -la mutinynet-litd-lnbits/"
        returncode, stdout, stderr = self.ssh.execute_command(clone_cmd, timeout=300)  # 5 min timeout for clone
        
        if returncode != 0:
            print(f"Warning: Clone command had issues: {stderr}")
            # Try to verify if it partially worked
            returncode, stdout, stderr = self.ssh.execute_command("ls -la /opt/mutinynet-litd-lnbits/ 2>&1 || echo 'Directory not found'")
            print(f"Directory check: {stdout}")
        else:
            print("Repository cloned successfully")
        
        # Create local directory for deployment files
        deploy_dir = Path(__file__).parent.parent.parent / "deploy"
        deploy_dir.mkdir(exist_ok=True)
        
        # Create docker-compose.yml for deployment
        docker_compose = """version: '3.8'

x-logging:
  &default-logging
  driver: "json-file"
  options:
    max-size: "50m"
    max-file: "3"

services:
  bitcoind:
    container_name: "bitcoind"
    build:
      context: /opt/mutinynet-litd-lnbits
      dockerfile: Dockerfile
    restart: unless-stopped
    logging: *default-logging
    volumes:
      # CRITICAL: Mount the persistent volume to where Bitcoin actually writes data
      - /mnt/mutinynet-volume/bitcoin:/root/.bitcoin:rw
    environment:
      BITCOIN_DIR: /root/.bitcoin
    ports:
      - "28332:28332"
      - "28333:28333"
      - "28334:28334"
      - "38332:38332"
      - "38333:38333"
"""
        
        # Bitcoin.conf is now properly configured in the repo
        # Just copy it from the repo
        bitcoin_conf = f"""# Mutinynet Configuration
signet=1
server=1
txindex=1

[signet]
# CRITICAL: This is the mutinynet-specific challenge
signetchallenge=512102f7561d208dd9ae99bf497273e16f389bdbd6c4742ddb8e6b216e64fa2928ad8f51ae
addnode=45.79.52.207:38333
dnsseed=0
signetblocktime=30
rpcbind=0.0.0.0:38332
rpcallowip=0.0.0.0/0

# RPC Configuration
rpcuser={BITCOIN_RPC_USER}
rpcpassword={BITCOIN_RPC_PASSWORD}

# ZMQ Configuration
zmqpubrawblock=tcp://0.0.0.0:28332
zmqpubrawtx=tcp://0.0.0.0:28333
zmqpubhashblock=tcp://0.0.0.0:28334

# Performance
dbcache=1000
maxmempool=300
"""
        
        # Save files locally
        compose_path = deploy_dir / "docker-compose.yml"
        config_path = deploy_dir / "bitcoin.conf"
        
        with open(compose_path, 'w') as f:
            f.write(docker_compose)
        
        with open(config_path, 'w') as f:
            f.write(bitcoin_conf)
        
        print("Creating docker-compose configuration...")
        
        # Upload docker-compose.yml to droplet
        if self.ssh.upload_file(compose_path, "/opt/mutinynet-litd-lnbits/docker-compose.yml"):
            print("✓ Uploaded docker-compose.yml")
        else:
            print("✗ Failed to upload docker-compose.yml - using repo version")
        
        print("Configuration deployed!")
        return True
    
    def start(self):
        """Start all services"""
        print("=== Starting Services ===")
        
        if not self.get_droplet_info():
            return False
        
        print("Starting Bitcoin daemon...")
        returncode, stdout, stderr = self.ssh.execute_command(
            "cd /opt/mutinynet-litd-lnbits && docker-compose up -d bitcoind"
        )
        
        if returncode == 0:
            print("✓ Bitcoin daemon started")
            
            # Check if it's running
            returncode, stdout, stderr = self.ssh.execute_command("docker ps | grep bitcoind")
            if "bitcoind" in stdout:
                print("✓ Bitcoin container is running")
                
                # Get initial status
                print("\nChecking Bitcoin status...")
                self.ssh.execute_command(
                    f"sleep 5 && docker exec bitcoind bitcoin-cli -rpcuser={BITCOIN_RPC_USER} -rpcpassword={BITCOIN_RPC_PASSWORD} getblockchaininfo | grep -E 'chain|blocks|headers' || echo 'Still starting...'"
                )
            else:
                print("✗ Bitcoin container failed to start")
                print(stderr)
        else:
            print(f"✗ Failed to start: {stderr}")
        
        return True
    
    def stop(self):
        """Stop all services"""
        print("=== Stopping Services ===")
        
        if not self.get_droplet_info():
            return False
        
        print("Stopping services...")
        returncode, stdout, stderr = self.ssh.execute_command(
            "cd /opt/mutinynet-litd-lnbits && docker-compose down"
        )
        
        if returncode == 0:
            print("✓ Services stopped")
        else:
            print(f"✗ Failed to stop: {stderr}")
        
        return True
    
    def status(self):
        """Check status of all services"""
        print("=== Service Status ===")
        
        if not self.get_droplet_info():
            return False
        
        # Check Docker containers
        print("\nDocker containers:")
        self.ssh.execute_command("docker ps")
        
        # Check Bitcoin status
        print("\nBitcoin daemon status:")
        returncode, stdout, stderr = self.ssh.execute_command(
            f"docker exec bitcoind bitcoin-cli -rpcuser={BITCOIN_RPC_USER} -rpcpassword={BITCOIN_RPC_PASSWORD} getblockchaininfo 2>/dev/null | jq -r '.chain, .blocks, .headers, .verificationprogress' 2>/dev/null || echo 'Bitcoin not ready'"
        )
        if returncode == 0 and stdout:
            lines = stdout.strip().split('\n')
            if len(lines) >= 4:
                print(f"  Chain: {lines[0]}")
                print(f"  Blocks: {lines[1]}")
                print(f"  Headers: {lines[2]}")
                print(f"  Sync progress: {float(lines[3]):.1%}" if lines[3] != 'null' else "  Sync progress: Starting...")
        else:
            print("  Bitcoin daemon not responding yet")
        
        # Check disk usage
        print("\nDisk usage:")
        self.ssh.execute_command("df -h /mnt/mutinynet-volume | tail -1")
        
        print(f"\nAccess points:")
        print(f"  SSH: ssh root@{self.ip}")
        print(f"  Bitcoin RPC: http://{self.ip}:38332")
        print(f"    Username: {BITCOIN_RPC_USER}")
        print(f"    Password: {BITCOIN_RPC_PASSWORD}")
        print(f"  Bitcoin P2P: {self.ip}:38333")
        
        return True
    
    def logs(self):
        """View service logs"""
        print("=== Service Logs ===")
        
        if not self.get_droplet_info():
            return False
        
        print("Bitcoin daemon logs (last 50 lines):")
        self.ssh.execute_command("docker logs --tail 50 bitcoind")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Deploy Mutinynet stack to Digital Ocean")
    parser.add_argument("command", 
                        choices=["setup", "deploy", "start", "stop", "status", "logs"],
                        help="Command to execute")
    
    args = parser.parse_args()
    
    deployer = MutinynetDeployer()
    
    commands = {
        "setup": deployer.setup,
        "deploy": deployer.deploy,
        "start": deployer.start,
        "stop": deployer.stop,
        "status": deployer.status,
        "logs": deployer.logs,
    }
    
    # Run the command
    success = commands[args.command]()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()