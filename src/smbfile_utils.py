"""File system Utilities for SMB/CIFS file shares"""

import os
from pathlib import Path
from smbclient import open_file

def build_unc_path(hostname, share, folder):
    """ Build a UNC path """
    return rf"\\{hostname}\{share}\{folder}"

def write_random_binary_file(filepath: Path, size : int =1024):
    """ Write a random binary file of specified size """
    filecontent = os.urandom(size)
    with open_file(filepath, "wb") as f:
        f.write(filecontent)
    return filepath, filecontent

