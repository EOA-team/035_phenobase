"""File system Utilities for SMB/CIFS file shares"""

import os
import hashlib
from pathlib import Path
from smbclient import reset_connection_cache, register_session
import smbclient
from enum import IntEnum
from enum import StrEnum
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


class User(StrEnum):
    """Available User Types"""
    SERVICE = os.environ["SERVICE_USER"]
    NORMAL = os.environ["NORMAL_USER"]

class Password(StrEnum):
    """Available User Types"""
    SERVICE = os.environ["SERVICE_PASSWORD"]
    NORMAL = os.environ["NORMAL_PASSWORD"]

class FileSizeUnit(IntEnum):
    """Enumeration for file size units."""
    BYTE = 1
    KB = 1024
    MB = 1024 * 1024
    GB = 1024 * 1024 * 1024

DEFAULT_CHUNK_SIZE =  1* FileSizeUnit.MB

def connect_to_nas(user_type: User, password: Password):
    """Connect to the NAS using the specified user type and password."""
    reset_connection_cache()
    user = user_type.value + "@" + os.environ["FOLA_DOMAIN"]
    register_session(
        server=os.environ["NAS_RECKENHOLZ"],
        username=user,
        password=password.value,
    )

def build_unc_path(hostname, share, folder):
    """ Build a UNC path """
    return rf"\\{hostname}\{share}\{folder}"


def copy_from_nas_to_local(nas_path: Path, local_path: Path, chunk_size: int = DEFAULT_CHUNK_SIZE):
    """ Copy a file from NAS to local filesystem in chunks """
    with(
        smbclient.open_file(nas_path, "rb") as src,
        open(local_path, "wb") as dst
    ):
        while chunk := src.read(chunk_size):
            dst.write(chunk)

def copy_from_nas_to_nas(nas_path1: Path, nas_path2: Path, chunk_size: int = DEFAULT_CHUNK_SIZE):
    """ Copy a file from NAS to NAS in chunks """
    with(
        smbclient.open_file(nas_path1, "rb", share_access='r') as src,
        smbclient.open_file(nas_path2, "wb") as dst,
    ):
        while chunk := src.read(chunk_size):
             dst.write(chunk)


def write_random_binary_file(
        filepath: Path, 
        size : int , 
        chunk_size: int = DEFAULT_CHUNK_SIZE) -> tuple[str, str]:
    """ Write a random binary file of specified size
     return tuple of (full file sha256, last chunk sha256)
     """
    sha = hashlib.sha256()
    last_chunk_sha = hashlib.sha256()
    with smbclient.open_file(str(filepath), "wb") as f:
        remaining = size
        while remaining > 0:
            chunk = os.urandom(min(chunk_size, remaining))
            f.write(chunk)
            sha.update(chunk)
            remaining -= len(chunk)
            if remaining <= 0:
                last_chunk_sha.update(chunk)
    return sha.hexdigest(), last_chunk_sha.hexdigest()

def get_sha256sum(filepath, chunk_size=DEFAULT_CHUNK_SIZE):
         sha = hashlib.sha256()
         with smbclient.open_file(str(filepath), "rb") as f:
             while chunk := f.read(chunk_size):
                 sha.update(chunk)
         return sha.hexdigest()

def get_sha256sum_last_chunk(filepath, chunk_size=DEFAULT_CHUNK_SIZE):
         """ Calculate the SHA256 checksum of the last chunk of a file """
         sha = hashlib.sha256()
         with smbclient.open_file(str(filepath), "rb") as f:
             f.seek(-chunk_size, os.SEEK_END)
             sha.update(f.read(chunk_size))
         return sha.hexdigest()

 

