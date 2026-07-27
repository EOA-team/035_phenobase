"""File system Utilities for SMB/CIFS file shares"""

import os
import hashlib
from pathlib import Path
from smbclient import open_file
from enum import IntEnum
class FileSizeUnit(IntEnum):
    """Enumeration for file size units."""
    BYTE = 1
    KB = 1024
    MB = 1024 * 1024
    GB = 1024 * 1024 * 1024

DEFAULT_CHUNK_SIZE =  1* FileSizeUnit.MB

def build_unc_path(hostname, share, folder):
    """ Build a UNC path """
    return rf"\\{hostname}\{share}\{folder}"

def write_random_binary_file(
        filepath: Path, 
        size : int = 1* FileSizeUnit.GB, 
        chunk_size: int = DEFAULT_CHUNK_SIZE) -> (Path, str):
    """ Write a random binary file of specified size """
    sha = hashlib.sha256()
    with open_file(filepath, "wb") as f:
        remaining = size
        while remaining > 0:
            chunk = os.urandom(min(chunk_size, remaining))
            f.write(chunk)
            sha.update(chunk)
            remaining -= len(chunk)
    return sha.hexdigest()

def get_sha256sum(filepath, chunk_size=DEFAULT_CHUNK_SIZE):
         sha = hashlib.sha256()
         with open_file(str(filepath), "rb") as f:
             while chunk := f.read(chunk_size):
                 sha.update(chunk)
         return sha.hexdigest()



 

