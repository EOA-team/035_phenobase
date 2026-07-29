from src.smbfile_utils import build_unc_path, write_random_binary_file, get_sha256sum, get_sha256sum_last_chunk ,FileSizeUnit
import src.smbfile_utils 
import pytest


FILESIZE = FileSizeUnit.MB * 10  

@pytest.fixture(autouse=True)
def mock_smb_as_local_file(monkeypatch):
    """ Redirects open_file to Python's built-in open
    becaue the NAS is not available in the CI environment. """
    monkeypatch.setattr(src.smbfile_utils, "open_file", open)


def test_build_unc_path():
    hostname = "server"
    share = "share"
    folder = "folder"
    expected_path = r"\\server\share\folder"
    assert build_unc_path(hostname, share, folder) == expected_path

def test_smb_file_write_and_read_checksum( tmp_path):
    """Tests the full write-then-read lifecycle of the SMB utility functions."""
    test_file = tmp_path / "test.bin"
    write_hash, write_hash_last_chunk = write_random_binary_file(test_file, size=FILESIZE)
    read_hash_last_chunk = get_sha256sum_last_chunk(test_file)
    read_hash = get_sha256sum(test_file)

    assert write_hash_last_chunk == read_hash_last_chunk, (
        f"Expected last chunk hash {write_hash_last_chunk}, but got {read_hash_last_chunk}"
    )
    assert write_hash == read_hash, (
        f"Expected full file hash {write_hash}, but got {read_hash}"
    )   