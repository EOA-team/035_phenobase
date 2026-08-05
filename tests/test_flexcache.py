from paramiko import SSHClient
from src.ssh_helpers import connect
import os 
from pathlib import Path
import pytest

from src.nas_helper import (
    FileSizeUnit,
)

# Drone Data Location on FlexCache(mounted on Gamarello Cluster)
FLEXCACHE_TARGET = "/agroscope/EO_drone/drone"

FILESIZE = FileSizeUnit.MB * 10
CHUNKSIZE = FileSizeUnit.MB * 1

@pytest.fixture(scope="function")
def testfile():
    """Service User creates and deletes a test file
    before and after every test that uses this fixture.
    Note: if a test already deleted file the
    fixture will not raise an error when trying to delete it again.
    """
    filename = f"pytest_{os.urandom(4).hex()}.bin"
    flexcach_filepath = FLEXCACHE_TARGET + "/" + filename
    #Create File with Service User
    service_client = connect(
        username=os.getenv("SERVICE_USER"),
        password=os.getenv("SERVICE_PASSWORD"),
        hostname=os.getenv("GAMARELLO_ADDRESS"),
    )
    _, stdout, _ = service_client.exec_command(
        f"dd if=/dev/urandom of={flexcach_filepath} bs=1M count={FILESIZE // (1024*1024)} "
        f"2>/dev/null && sha256sum {flexcach_filepath}"
    )
    expected_sha256sum = stdout.read().decode().split()[0]

    yield flexcach_filepath, expected_sha256sum
    #Delete with Service User 
    service_client.exec_command(f"rm -f {flexcach_filepath}")
    service_client.close()


def test_write_file(testfile):
    """Only Service User should be able to write a file on FlexCache"""
    
    # Service user write to FlexCache (done in fixture)
    flexcache_filepath, expected_sha256sum = testfile

    # Normal user write to FlexCache
    normal_client = connect(
        username=os.getenv("NORMAL_USER"),
        password=os.getenv("NORMAL_PASSWORD"),
        hostname=os.getenv("GAMARELLO_ADDRESS"),
    )
    _, stdout, _ = normal_client.exec_command(
        f"sha256sum {flexcache_filepath}"
    )
    read_sha256sum = stdout.read().decode().split()[0]
    assert read_sha256sum == expected_sha256sum

    _, stdout, _ = normal_client.exec_command(
        f"dd if=/dev/urandom of={flexcache_filepath} bs=1M count={FILESIZE // (1024*1024)}"
    )
    exit_status = stdout.channel.recv_exit_status()
    print(stdout.read().decode())
    assert exit_status != 0, "expected normal user to fail writing to FlexCache, but command succeeded"
