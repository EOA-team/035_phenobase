"""
This test checks that the NAS data is accessible 
to normal fola users , while making sure that 
rename,move,delete, write operations are only available to
service user

Relevant issues:
https://github.com/EOA-team/035_phenobase/issues/3
"""

import os
import pytest
from pathlib import Path

from src.smbfile_utils import (
    build_unc_path, 
    write_random_binary_file, 
    get_sha256sum,
    get_sha256sum_last_chunk,
    FileSizeUnit,
)

from smbclient import (
    register_session, 
    listdir, open_file, 
    path,
    remove,
)
from smbprotocol.exceptions import SMBOSError
from smbprotocol.header import NtStatus

from src.nas_helpers import connect_to_nas, User, Password

from enum import StrEnum
from dotenv import load_dotenv

load_dotenv()

#Drone Data Location directly on NAS
NAS_TARGET = build_unc_path(
    hostname=os.environ["NAS_RECKENHOLZ"],
    share="Data-EODrone",
    folder="drone",
)
#Drone Data Location on FlexCache(mounted on Gamarello Cluster)
FLEXCACHE_TARGET = "/agroscope/EO_drone/drone"


@pytest.fixture(scope="function")   
def test_file():
    """Create and deletes test file with service user 
    before and after every test using this fixure.
    Ensures file is availabe for read tests for both service and normal users"""
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE) # only service user can write
    filename= f"pytest_{os.urandom(4).hex()}.bin"
    nas_filepath = Path(NAS_TARGET) / filename
    sha256sum, _ = write_random_binary_file(nas_filepath, FileSizeUnit.MB * 1)
    yield nas_filepath,sha256sum
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE) # only service user can delete
    remove(nas_filepath)  # Cleanup after test



def test_write_file_on_nas():
    """Only Service User should be able to write a file on NAS,"""
    # Service user can write to NAS
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE)
    filename= f"pytest_{os.urandom(4).hex()}.bin"
    nas_filepath = Path(NAS_TARGET) / filename
    expected_sha256sum, _ = write_random_binary_file(nas_filepath, FileSizeUnit.MB * 1)
    assert get_sha256sum(nas_filepath) == expected_sha256sum
    remove(nas_filepath) 
    # Normal user should not be able to write to NAS
    connect_to_nas(user_type=User.NORMAL, password=Password.NORMAL)
    with pytest.raises(SMBOSError) as exc_info:
        write_random_binary_file(nas_filepath, FileSizeUnit.MB * 1)
    
    assert exc_info.value.ntstatus == NtStatus.STATUS_ACCESS_DENIED, (
        f"Expected STATUS_ACCESS_DENIED, but got {exc_info.value.ntstatus}"
    )
    
   

def test_read_file_on_nas(test_file):
    """Both Users should be able to read a file on NAS"""
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE)
    nas_filepath, expected_sha256sum = test_file 
    assert get_sha256sum(nas_filepath) == expected_sha256sum

    connect_to_nas(user_type=User.NORMAL, password=Password.NORMAL)
    assert get_sha256sum(nas_filepath) == expected_sha256sum
    




