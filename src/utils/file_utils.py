import hashlib
import io
import os


def write_random_file(
    stream: io.BufferedIOBase, size: int, chunk_size: int
) -> tuple[str, str]:
    """Write a random binary file of specified size
    return tuple of (full file sha256, last chunk sha256)
    Supports very big files by writing in chunks to avoid memory issues.
    """
    sha = hashlib.sha256()
    chunk = b""
    remaining = size
    while remaining > 0:
        chunk = os.urandom(min(chunk_size, remaining))
        stream.write(chunk)
        sha.update(chunk)
        remaining -= len(chunk)
    return sha.hexdigest(), hashlib.sha256(chunk).hexdigest()


def get_sha256sum(stream: io.BufferedIOBase, chunk_size: int):
    """Calculate the SHA256 checksum of a file-like object"""
    sha = hashlib.sha256()
    while chunk := stream.read(chunk_size):
        sha.update(chunk)
    return sha.hexdigest()


def get_sha256sum_last_chunk(stream: io.BufferedIOBase, chunk_size: int):
    """Calculate the SHA256 checksum of the last chunk of a file-like object"""
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    read_size = min(chunk_size, size)
    stream.seek(-read_size, os.SEEK_END)
    return hashlib.sha256(stream.read(read_size)).hexdigest()
