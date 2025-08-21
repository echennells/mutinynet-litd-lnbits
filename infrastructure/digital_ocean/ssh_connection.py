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
        
        self.ssh_base = ["ssh", "-o", "StrictHostKeyChecking=no", 
                         "-o", "ConnectTimeout=10",
                         "-p", str(port)]
        if ssh_key:
            self.ssh_base.extend(["-i", ssh_key])
        self.ssh_base.append(f"{username}@{host}")
    
    def test_connection(self, retries: int = 3) -> bool:
        """Test if SSH connection works with retries"""
        for i in range(retries):
            try:
                result = subprocess.run(
                    self.ssh_base + ["echo", "test"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return True
                if i < retries - 1:
                    time.sleep(5)
            except:
                if i < retries - 1:
                    time.sleep(5)
        return False
    
    def execute_command(self, command: str, timeout: Optional[int] = None, retries: int = 2) -> Tuple[int, str, str]:
        """Execute command on remote droplet with retries"""
        for i in range(retries):
            try:
                result = subprocess.run(
                    self.ssh_base + [command],
                    capture_output=True,
                    text=True,
                    timeout=timeout or SSH_TIMEOUT
                )
                if result.returncode == 255 and "Connection refused" in result.stderr:
                    if i < retries - 1:
                        time.sleep(3)
                        continue
                return result.returncode, result.stdout, result.stderr
            except subprocess.TimeoutExpired:
                if i < retries - 1:
                    time.sleep(3)
                    continue
                return -1, "", "Command timed out"
            except Exception as e:
                if i < retries - 1:
                    time.sleep(3)
                    continue
                return -1, "", str(e)
        return -1, "", "All retries failed"
    
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