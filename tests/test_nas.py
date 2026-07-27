import os
from smbclient import (
    register_session, 
    listdir, open_file, 
    path,
    unlink,
    reset_connection_cache
)
import pytest
import time

from src.smbfile_utils import build_unc_path, write_random_binary_file
from pathlib import Path


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
    filename= os.urandom(4).hex()
    filepath = Path(target_path) / f"write_test_{filename}.bin"
    _ ,file_content = write_random_binary_file(filepath, size=128)

    assert path.exists(filepath) 
    with open_file(filepath, "rb") as f:
        assert f.read() == file_content
    
    unlink(filepath)  # Clean up after test


