#!/usr/bin/env python3
"""
Test Bitcoin RPC connection from GitHub Actions
"""
import os
import sys
import json
import requests
from typing import Dict, Any

def test_bitcoin_rpc(host: str, user: str, password: str) -> bool:
    """Test Bitcoin RPC connection"""
    url = f"http://{host}:38332"
    
    # Test getblockcount
    payload = {
        "jsonrpc": "1.0",
        "id": "test",
        "method": "getblockcount",
        "params": []
    }
    
    try:
        response = requests.post(
            url,
            auth=(user, password),
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        block_count = result.get("result", 0)
        print(f"✓ Bitcoin RPC working - Current block: {block_count}")
        return True
        
    except Exception as e:
        print(f"✗ Bitcoin RPC failed: {e}")
        return False

def test_bitcoin_zmq(host: str) -> bool:
    """Test Bitcoin ZMQ ports are accessible"""
    import socket
    
    zmq_ports = [28332, 28333, 28334]
    all_good = True
    
    for port in zmq_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✓ ZMQ port {port} is accessible")
        else:
            print(f"✗ ZMQ port {port} is not accessible")
            all_good = False
    
    return all_good

def test_bitcoin_p2p(host: str) -> bool:
    """Test Bitcoin P2P port is accessible"""
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((host, 38333))
    sock.close()
    
    if result == 0:
        print(f"✓ Bitcoin P2P port 38333 is accessible")
        return True
    else:
        print(f"✗ Bitcoin P2P port 38333 is not accessible")
        return False

def main():
    """Run all tests"""
    # Get connection details from environment
    host = os.getenv("BITCOIN_HOST", "localhost")
    user = os.getenv("BITCOIN_RPC_USER", "mutinynet")
    password = os.getenv("BITCOIN_RPC_PASSWORD", "testpassword123")
    
    print(f"Testing Bitcoin connection to {host}...")
    print(f"Using credentials: {user}/{'*' * len(password)}")
    print()
    
    tests_passed = 0
    tests_total = 3
    
    # Run tests
    if test_bitcoin_rpc(host, user, password):
        tests_passed += 1
    
    if test_bitcoin_zmq(host):
        tests_passed += 1
    
    if test_bitcoin_p2p(host):
        tests_passed += 1
    
    print()
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    return 0 if tests_passed == tests_total else 1

if __name__ == "__main__":
    sys.exit(main())