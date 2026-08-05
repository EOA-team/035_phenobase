"""Tests file_utils which can be used by both local and NAS operations.
- NAS (smbclient.open_file)
- Local operations (open)
Note: tested with open() , because smbclient.open_file() requires a NAS connection
skbclient.open_file() is tested in integration_tests in test_nas.py
"""

from src.file_utils import get_sha256sum, get_sha256sum_last_chunk, write_random_file
from src.nas_helper import FileSizeUnit, build_unc_path

FILESIZE = FileSizeUnit.MB * 10
CHUNKSIZE = FileSizeUnit.MB * 1


def test_build_unc_path():
    hostname = "server"
    share = "share"
    folder = "folder"
    expected_path = r"\\server\share\folder"
    assert build_unc_path(hostname, share, folder) == expected_path


def test_verify_filewrite_with_checksum(tmp_path):
    """Tests the full write-then-read checksum"""
    test_file = tmp_path / "test.bin"

    with open(test_file, "wb") as f:
        write_hash, write_hash_last = write_random_file(
            stream=f, size=FILESIZE, chunk_size=CHUNKSIZE
        )

    with open(test_file, "rb") as f:
        read_hash = get_sha256sum(stream=f, chunk_size=CHUNKSIZE)
        read_hash_last_chunk = get_sha256sum_last_chunk(stream=f, chunk_size=CHUNKSIZE)

    assert write_hash == read_hash, (
        f"Expected full file hash {write_hash}, but got {read_hash}"
    )

    assert write_hash_last == read_hash_last_chunk, (
        f"Expected last chunk hash {write_hash_last}, but got {read_hash_last_chunk}"
    )
