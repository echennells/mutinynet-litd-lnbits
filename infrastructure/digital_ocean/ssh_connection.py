"""
SSH connection handler for Digital Ocean droplets (simplified version)
"""
import subprocess
import time
from typing import Optional, Tuple
from pathlib import Path

from .config import SSH_USERNAME, SSH_PORT, SSH_TIMEOUT


class SimpleSSHConnection:
    """Simple SSH connection using subprocess (no paramiko dependency)"""
    
    def __init__(self, host: str, port: int = SSH_PORT, username: str = SSH_USERNAME):
        self.host = host
        self.port = port
        self.username = username
        
        # Find SSH key
        ssh_key = None
        key_paths = [Path.home() / ".ssh" / "id_rsa", 
                     Path.home() / ".ssh" / "id_ed25519"]
        for key_path in key_paths:
            if key_path.exists():
                ssh_key = str(key_path)
                break
        
        # SSH options tolerant to high jitter and packet loss
        self.ssh_base = ["ssh", "-o", "StrictHostKeyChecking=no", 
                         "-o", "ConnectTimeout=60",  # Very long timeout for jitter spikes
                         "-o", "ServerAliveInterval=30",  # Less aggressive keepalive
                         "-o", "ServerAliveCountMax=10",  # More tolerance before giving up
                         "-o", "TCPKeepAlive=yes",  # TCP level keepalive
                         "-p", str(port)]
        if ssh_key:
            self.ssh_base.extend(["-i", ssh_key])
        self.ssh_base.append(f"{username}@{host}")
    
    def test_connection(self, retries: int = 3) -> bool:
        """Test if SSH connection works with retries"""
        print(f"DEBUG: Testing SSH connection to {self.username}@{self.host}:{self.port}")
        print(f"DEBUG: SSH command: {' '.join(self.ssh_base + ['echo', 'test'])}")
        
        for i in range(retries):
            try:
                result = subprocess.run(
                    self.ssh_base + ["echo", "test"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                print(f"DEBUG: Attempt {i+1} - Return code: {result.returncode}")
                print(f"DEBUG: Stdout: {result.stdout}")
                print(f"DEBUG: Stderr: {result.stderr}")
                
                if result.returncode == 0:
                    return True
                if i < retries - 1:
                    print(f"DEBUG: Retrying in 5 seconds...")
                    time.sleep(5)
            except Exception as e:
                print(f"DEBUG: Exception on attempt {i+1}: {e}")
                if i < retries - 1:
                    print(f"DEBUG: Retrying in 5 seconds...")
                    time.sleep(5)
        return False
    
    def execute_command(self, command: str, timeout: Optional[int] = None, retries: int = 1) -> Tuple[int, str, str]:
        """Execute command on remote droplet"""
        print(f"DEBUG: Executing command: {command[:50]}...")
        try:
            full_cmd = self.ssh_base + [command]
            # Use a very long timeout to handle jitter spikes (up to 2 seconds based on your ping)
            actual_timeout = timeout or max(SSH_TIMEOUT, 120)  # At least 2 minutes default
            
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=actual_timeout
            )
            print(f"DEBUG: Command result - Return code: {result.returncode}")
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            print(f"DEBUG: Command timed out after {actual_timeout} seconds")
            return -1, "", f"Command timed out after {actual_timeout}s (high latency detected)"
        except Exception as e:
            print(f"DEBUG: Exception: {e}")
            return -1, "", str(e)
    
    def upload_file(self, local_path: Path, remote_path: str, retries: int = 2) -> bool:
        """Upload file using scp with retries"""
        # Find SSH key for scp
        ssh_key = None
        key_paths = [Path.home() / ".ssh" / "id_rsa", 
                     Path.home() / ".ssh" / "id_ed25519"]
        for key_path in key_paths:
            if key_path.exists():
                ssh_key = str(key_path)
                break
        
        for i in range(retries):
            try:
                scp_cmd = ["scp", "-o", "StrictHostKeyChecking=no",
                           "-o", "ConnectTimeout=10",
                           "-P", str(self.port)]
                if ssh_key:
                    scp_cmd.extend(["-i", ssh_key])
                scp_cmd.extend([str(local_path),
                               f"{self.username}@{self.host}:{remote_path}"])
                
                # Increase timeout for large files
                file_size = Path(local_path).stat().st_size if Path(local_path).exists() else 0
                timeout_val = 300 if file_size > 10_000_000 else 60  # 5 min for files > 10MB
                
                result = subprocess.run(
                    scp_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_val
                )
                if result.returncode == 0:
                    return True
                if result.returncode == 255 and "Connection refused" in result.stderr:
                    if i < retries - 1:
                        time.sleep(3)
                        continue
                return False
            except:
                if i < retries - 1:
                    time.sleep(3)
                    continue
                return False
        return False
    
    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download file using scp"""
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                ["scp", "-o", "StrictHostKeyChecking=no",
                 "-P", str(self.port),
                 f"{self.username}@{self.host}:{remote_path}",
                 str(local_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except:
            return False