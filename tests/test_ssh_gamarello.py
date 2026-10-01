"""Tests SSH connection to the Gamarello Cluster."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from paramiko import SSHClient

load_dotenv()


@pytest.fixture(scope="module")
def ssh():
    """Establish an SSH connection to the Gamarello Cluster."""
    client = SSHClient()
    client.load_host_keys(filename=str(Path.home() / ".ssh" / "known_hosts"))
    client.connect(
        hostname=os.getenv("GAMARELLO_ADDRESS"),
        username=os.getenv("SERVICE_USER"),
        password=os.getenv("SERVICE_PASSWORD"),
    )
    yield client
    client.close()


@pytest.mark.integration_test
def test_ssh_connection(ssh):
    """Test that the SSH connection is established successfully."""
    assert ssh.get_transport().is_active(), "SSH connection is not active."


@pytest.mark.integration_test
def test_expected_ssh_user(ssh):
    """Verify that the SSH connection is using the expected user."""
    _, stdout, _ = ssh.exec_command("whoami")
    remote_user = stdout.read().decode().strip()
    expected_user = os.getenv("SERVICE_USER")
    print(remote_user)
    assert remote_user == expected_user, (
        f"Expected SSH user {expected_user}, but got {remote_user}"
    )


@pytest.mark.integration_test
def test_directory_listing(ssh):
    """Test that we can list the contents of the drone directory on the remote server."""
    _, stdout, _ = ssh.exec_command("ls /agroscope/EO_drone/drone")
    output = stdout.read().decode().strip()
    assert output, (
        "Expected some output from 'ls /agroscope/EO_drone/drone', but got none."
    )
