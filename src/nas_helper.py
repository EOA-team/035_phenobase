"""File system Utilities for SMB/CIFS file shares"""

import os
import shutil
from enum import IntEnum, StrEnum
from pathlib import Path

import smbclient
from dotenv import load_dotenv
from smbclient import register_session, reset_connection_cache

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
    """ Copy a file from NAS to local filesystem in chunks in binary mode """
    with(
        smbclient.open_file(nas_path, "rb") as src,
        open(local_path, "wb") as dst
    ):
         shutil.copyfileobj(src, dst, chunk_size)

def copy_from_nas_to_nas(nas_src: Path, nas_dst: Path, chunk_size: int = DEFAULT_CHUNK_SIZE):
    """ Copy a file from NAS to NAS in chunks in binary mode """
    with(
        smbclient.open_file(nas_src, "rb") as src,
        smbclient.open_file(nas_dst, "wb") as dst
    ):
         shutil.copyfileobj(src, dst, chunk_size)





 

