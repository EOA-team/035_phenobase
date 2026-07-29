from src.smbfile_utils import build_unc_path, write_random_binary_file, get_sha256sum
import src.smbfile_utils
import pytest


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
    write_hash = write_random_binary_file(test_file, size=512)
    read_hash = get_sha256sum(test_file)
    
    assert write_hash == read_hash