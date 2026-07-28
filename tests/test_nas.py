"""
This test checks that the NAS is accessible and functioning as expected

Data-EO_drone is stored on NAS and contains big files that cannot be saved in
the PostgreSQL DB. This are files like orthomosaics or model artifacts.

This data needs to be accessible on:
- Gamarello Cluster: for inference (new crop traits), 
Accessible via Flexcache (mounted on /agroscope/EO_drone)
- Drone Station (NAS) :  for extraction of statistical features
Accessible via SMB/CIFS 

Additionally the NAS only allows write access for a service user, 
while normal users can only read the data.


Relevant issues:
https://github.com/EOA-team/035_phenobase/issues/3
"""

import os
import time 

from smbclient import (
    register_session, 
    listdir, open_file, 
    path,
    unlink,
    reset_connection_cache,
)
import pytest
import time

from src.smbfile_utils import (
    build_unc_path, 
    write_random_binary_file, 
    get_sha256sum,
    FileSizeUnit,
)
from pathlib import Path
from paramiko import SSHClient
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="function")
def service_session():
    """Register a service user session for NAS access"""
    reset_connection_cache()
    user = os.environ["SERVICE_USER"]
    register_session(
        server=os.environ["NAS_RECKENHOLZ"],
        username=user,
        password=os.environ["SERVICE_PASSWORD"],
    )
    yield user
    reset_connection_cache()

@pytest.fixture(scope="function")
def normal_session():
    """Register a normal user (F-Account) session for NAS access"""
    reset_connection_cache()
    user = os.environ["NORMAL_USER"]
    register_session(
        server=os.environ["NAS_RECKENHOLZ"],
        username=user,
        password=os.environ["NORMAL_PASSWORD"],
    )
    yield user
    reset_connection_cache()

@pytest.fixture(scope="module")
def target_path():
    """Build the UNC path for drone nas folder"""
    return build_unc_path(
        hostname=os.environ["NAS_RECKENHOLZ"],
        share="Data-EODrone",
        folder="drone",
    )

def test_normal_user_read_access(normal_session, target_path):
    """ Test read access by listing the contents of the NAS folder """
    print(f"Reading as {normal_session}")
    entries = listdir(target_path)  
    assert len(entries) > 0

def test_service_user_read_access(service_session, target_path):
    """ Test read access by listing the contents of the NAS folder """
    print(f"Reading as {service_session}")
    entries = listdir(target_path)  
    assert len(entries) > 0

def test_normal_write_access(normal_session, target_path):
    """ Test that a normal user cannot write to the NAS folder """
    print(f"Writing as {normal_session}")
    filepath = Path(target_path) / f"write_test_{os.urandom(4).hex()}.txt"
    
    with pytest.raises(OSError), open_file(filepath, "w") as f:
        f.write("test")

def test_service_write_access(service_session, target_path):
    """ Test that service user can write to the NAS folder """
    print(f"Writing as {service_session}")
    filename= f"write_test_{os.urandom(4).hex()}.bin"
    filepath = Path(target_path) / filename
    expected_hash = write_random_binary_file(
        filepath, 
        size= 10* FileSizeUnit.MB,
        chunk_size=FileSizeUnit.MB)

    assert path.exists(filepath) 
    assert get_sha256sum(filepath) == expected_hash
    
    unlink(filepath)  # Clean up after test

def test_nas_to_flexcache(service_session, target_path, timeout_s=600, size_gb=10):
    """Test how long it takes to until a 10GB file created on NAS is present
    in FlexCache"""
    print(f"Writing as {service_session}")
    filename= f"flexcache_test_{os.urandom(4).hex()}.bin"
    filepath = Path(target_path) / filename
    start_time = time.time()
    expected_hash = write_random_binary_file(
        filepath, 
        size= size_gb* FileSizeUnit.GB,   #Orthomosaic ~5GB
        chunk_size=FileSizeUnit.MB)
    write_duration = time.time()-start_time

    client = SSHClient()
    client.load_host_keys(filename=str(Path.home() / ".ssh" / "known_hosts"))
    client.connect(
        hostname=os.getenv("SSH_HOST"),
        username=os.getenv("SSH_USER"),
        password=os.getenv("SSH_PASSWORD"),
    )

    start_poll = time.time()
    remote_hash = None
    while time.time() - start_poll < timeout_s:
        _ , stdout, _ = client.exec_command(f"sha256sum /agroscope/EO_drone/drone/{filename}")
        output = stdout.read().decode().strip()
        if output:
            remote_hash = output.split()[0]
            if remote_hash == expected_hash:
                end_poll = time.time()
                break
            time.sleep(5)  # Wait for 5 seconds before checking again

    assert remote_hash == expected_hash, (
        f"Expected hash {expected_hash}, but got {remote_hash}. "
    )   
    print(f"Write duration: {write_duration:.2f} seconds")
    print(f"Latency for file to appear on FlexCache: {end_poll - start_poll:.2f} seconds")
    print(f"Total time from write to hash match: {end_poll - start_time:.2f} seconds")
    client.close()

