"""
This test checks that the NAS data is accessible
to normal fola users , while making sure that
rename,move,delete, write operations are only available to
service user

Relevant issues:
https://github.com/EOA-team/035_phenobase/issues/3
"""

import os
from hashlib import sha256
from pathlib import Path

import pytest
import smbclient
from dotenv import load_dotenv
from smbprotocol.exceptions import SMBOSError
from smbprotocol.header import NtStatus

from src.file_utils import get_sha256sum, write_random_file
from src.nas_helper import (
    FileSizeUnit,
    Password,
    User,
    build_unc_path,
    connect_to_nas,
    copy_from_nas_to_local,
    copy_from_nas_to_nas,
)

load_dotenv()

# Drone Data Location directly on NAS
NAS_TARGET = build_unc_path(
    hostname=os.environ["NAS_RECKENHOLZ"],
    share="Data-EODrone",
    folder="drone",
)

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
    nas_filepath = Path(NAS_TARGET) / filename
    # Create File with Service User
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE)
    with smbclient.open_file(nas_filepath, "wb") as f:
        expected_sha256sum, _ = write_random_file(
            stream=f, size=FILESIZE, chunk_size=CHUNKSIZE
        )
    yield nas_filepath, expected_sha256sum
    # Delete with Service User
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE)
    try:
        smbclient.remove(nas_filepath)
    except SMBOSError as e:
        if e.ntstatus != NtStatus.STATUS_OBJECT_NAME_NOT_FOUND:
            raise
    finally:
        smbclient.reset_connection_cache()


@pytest.mark.integration_test
def test_write_file(testfile):
    """Only Service User should be able to write a file on NAS,"""
    # Service user write to NAS (done in fixture)
    nas_filepath, expected_sha256sum = testfile
    with smbclient.open_file(nas_filepath, "rb") as f:
        assert get_sha256sum(f, chunk_size=CHUNKSIZE) == expected_sha256sum
    # Normal user write to NAS
    connect_to_nas(user_type=User.NORMAL, password=Password.NORMAL)
    with (
        pytest.raises(SMBOSError) as exc_info,
        smbclient.open_file(nas_filepath, "wb") as f,
    ):
        write_random_file(stream=f, size=FILESIZE, chunk_size=CHUNKSIZE)

    assert exc_info.value.ntstatus == NtStatus.STATUS_ACCESS_DENIED, (
        f"Expected STATUS_ACCESS_DENIED, but got {exc_info.value.ntstatus}"
    )


@pytest.mark.integration_test
def test_read_file(testfile):
    """Both Users should be able to read a file on NAS"""
    nas_filepath, expected_sha256sum = testfile
    # Read with Normal User
    connect_to_nas(user_type=User.NORMAL, password=Password.NORMAL)
    with smbclient.open_file(nas_filepath, "rb") as f:
        assert get_sha256sum(stream=f, chunk_size=CHUNKSIZE) == expected_sha256sum
    # Read with Service User
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE)
    with smbclient.open_file(nas_filepath, "rb") as f:
        assert get_sha256sum(stream=f, chunk_size=CHUNKSIZE) == expected_sha256sum


@pytest.mark.integration_test
def test_delete_file(testfile):
    """Only Service User should be able to delete a file on NAS"""
    nas_filepath, _ = testfile
    # Delete with Normal User
    connect_to_nas(user_type=User.NORMAL, password=Password.NORMAL)
    with pytest.raises(SMBOSError) as exc_info:
        smbclient.remove(nas_filepath)
    assert exc_info.value.ntstatus == NtStatus.STATUS_ACCESS_DENIED, (
        f"Expected STATUS_ACCESS_DENIED, but got {exc_info.value.ntstatus}"
    )
    # Delete with Service User
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE)
    smbclient.remove(nas_filepath)  # Service user can delete
    assert not smbclient.path.exists(nas_filepath)


@pytest.mark.integration_test
def test_rename_file(testfile):
    """Normal user should not be able move a file on NAS"""
    nas_filepath, _ = testfile
    new_nas_filepath = nas_filepath.parent / f"renamed_{nas_filepath.name}"

    # Rename with Normal User
    connect_to_nas(user_type=User.NORMAL, password=Password.NORMAL)
    with pytest.raises(SMBOSError) as exc_info:
        smbclient.rename(nas_filepath, new_nas_filepath)
    assert exc_info.value.ntstatus == NtStatus.STATUS_ACCESS_DENIED, (
        f"Expected STATUS_ACCESS_DENIED, but got {exc_info.value.ntstatus}"
    )

    # Rename with Service User
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE)
    smbclient.rename(nas_filepath, new_nas_filepath)
    assert smbclient.path.exists(new_nas_filepath)
    assert not smbclient.path.exists(nas_filepath)
    smbclient.remove(new_nas_filepath)  # Clean up after test


@pytest.mark.integration_test
def test_create_folder():
    """Only Service User should be able to create a folder on NAS"""
    folder_name = f"pytest_{os.urandom(4).hex()}"
    new_folder = Path(NAS_TARGET) / folder_name
    # Create Folder with Normal User
    connect_to_nas(user_type=User.NORMAL, password=Password.NORMAL)
    with pytest.raises(SMBOSError) as exc_info:
        smbclient.mkdir(new_folder)
    assert exc_info.value.ntstatus == NtStatus.STATUS_ACCESS_DENIED, (
        f"Expected STATUS_ACCESS_DENIED, but got {exc_info.value.ntstatus}"
    )
    # Create with Service User
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE)
    smbclient.mkdir(new_folder)
    assert smbclient.path.exists(new_folder)
    smbclient.rmdir(new_folder)  # Clean up after test


@pytest.mark.integration_test
def test_copy_file_nas_to_nas(testfile):
    """Only Service User should be able to copy a file from NAS to NAS"""
    nas_filepath, expected_sha256sum = testfile
    copy_nas_filepath = nas_filepath.parent / f"copy_{nas_filepath.name}"

    # Copy with Normal User
    connect_to_nas(user_type=User.NORMAL, password=Password.NORMAL)
    with pytest.raises(SMBOSError) as exc_info:
        copy_from_nas_to_nas(nas_filepath, copy_nas_filepath)
    assert exc_info.value.ntstatus == NtStatus.STATUS_ACCESS_DENIED, (
        f"Expected STATUS_ACCESS_DENIED, but got {exc_info.value.ntstatus}"
    )

    # Copy with Service User NAS to NAS
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE)
    copy_from_nas_to_nas(nas_filepath, copy_nas_filepath)
    assert smbclient.path.exists(copy_nas_filepath)
    with smbclient.open_file(copy_nas_filepath, "rb") as f:
        assert get_sha256sum(stream=f, chunk_size=CHUNKSIZE) == expected_sha256sum
    smbclient.remove(copy_nas_filepath)  # Clean up after test


@pytest.mark.integration_test
def test_copy_file_nas_to_local(testfile, tmp_path):
    """Both users should be able to copy a file from NAS to local path"""
    nas_filepath, expected_sha256sum = testfile
    local_filepath = tmp_path / f"copy_{nas_filepath.name}"

    # Copy with Normal User
    connect_to_nas(user_type=User.NORMAL, password=Password.NORMAL)
    copy_from_nas_to_local(nas_filepath, local_filepath)
    assert os.path.exists(local_filepath)
    sha256sum = sha256(local_filepath.read_bytes()).hexdigest()
    assert sha256sum == expected_sha256sum

    # Copy with Service User NAS to NAS
    connect_to_nas(user_type=User.SERVICE, password=Password.SERVICE)
    copy_from_nas_to_local(nas_filepath, local_filepath)
    assert os.path.exists(local_filepath)
    sha256sum = sha256(local_filepath.read_bytes()).hexdigest()
    assert sha256sum == expected_sha256sum
