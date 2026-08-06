"""
This test checks that the NAS data is accessible
via Flexcache mounted on Gamarello Cluster.
Normal fola users can read files, while
rename,move,delete, write operations are only available to
service user.

Relevant issues:
https://github.com/EOA-team/035_phenobase/issues/3
"""

import os
from pathlib import Path

import pytest
from paramiko import SSHClient

from src.nas_helper import (
    FileSizeUnit,
)

# Drone Data Location on FlexCache(mounted on Gamarello Cluster)
FLEXCACHE_TARGET = "/agroscope/EO_drone/drone"
FILESIZE = FileSizeUnit.MB * 10


@pytest.fixture(scope="function")
def testfile():
    """Service User creates and deletes a test file
    before and after every test that uses this fixture.
    Note: if a test already deleted file the
    fixture will not raise an error when trying to delete it again.
    """
    filename = f"pytest_{os.urandom(4).hex()}.bin"
    flexcach_filepath = FLEXCACHE_TARGET + "/" + filename

    # Create File with Service User
    client = SSHClient()
    client.load_system_host_keys(filename=str(Path.home() / ".ssh" / "known_hosts"))
    client.connect(
        hostname=os.getenv("GAMARELLO_ADDRESS"),
        username=os.getenv("SERVICE_USER"),
        password=os.getenv("SERVICE_PASSWORD"),
    )
    client.exec_command(
        f"dd if=/dev/urandom of={flexcach_filepath} bs=1M count={FILESIZE // (1024 * 1024)} "
    )

    _, stdout, _ = client.exec_command(f"sha256sum {flexcach_filepath} ")
    expected_sha256sum = stdout.read().decode().split()[0]

    yield flexcach_filepath, expected_sha256sum
    # Delete with Service User
    client.exec_command(f"rm -f {flexcach_filepath}")
    client.close()

@pytest.mark.integration_test
def test_write_file(testfile):
    """Only Service User should be able to write a file on FlexCache"""

    # Service user write to FlexCache (done in fixture)
    flexcache_filepath, expected_sha256sum = testfile

    # Normal user write to FlexCache
    client = SSHClient()
    client.load_system_host_keys(filename=str(Path.home() / ".ssh" / "known_hosts"))
    client.connect(
        hostname=os.getenv("GAMARELLO_ADDRESS"),
        username=os.getenv("NORMAL_USER"),
        password=os.getenv("NORMAL_PASSWORD"),
    )
    _, stdout, _ = client.exec_command(f"sha256sum {flexcache_filepath}")
    read_sha256sum = stdout.read().decode().split()[0]
    assert read_sha256sum == expected_sha256sum

    _, stdout, _ = client.exec_command(
        f"dd if=/dev/urandom of={flexcache_filepath} bs=1M count={FILESIZE // (1024 * 1024)}"
    )
    exit_status = stdout.channel.recv_exit_status()
    print(stdout.read().decode())
    assert exit_status != 0, (
        "expected normal user to fail writing to FlexCache, but command succeeded"
    )
