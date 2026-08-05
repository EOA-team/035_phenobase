"""Helps to run remote shell commands via SSH and return the output"""
from paramiko import SSHClient
from pathlib import Path

def connect(username: str, password: str, hostname: str) -> SSHClient:
    """Connect to a remote host via SSH and return the SSH client."""
    client = SSHClient()
    client.load_system_host_keys(filename=str(Path.home() / ".ssh" / "known_hosts"))
    client.connect(hostname=hostname, username=username, password=password)
    return client

def write_random_file(client:SSHClient, size:int , chunksize:int , filepath:str):
    pass