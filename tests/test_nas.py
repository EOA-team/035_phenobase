import os
import smbclient
import pytest

from src.nas import register_nas_host, build_unc_path

@pytest.mark.parametrize("host", ["mirror", "origin"])
@pytest.mark.parametrize("user", ["normal", "service"])
def test_show_nas_config(host, user, nas_config):
    """Run with pytest -s to inspect"""
    smbclient.reset_connection_cache()
    register_nas_host(nas_config, host, user)
    print(build_unc_path(nas_config, host))


@pytest.mark.parametrize("host", ["mirror", "origin"])
@pytest.mark.parametrize("user", ["normal", "service"])
def test_read_access(host, user, nas_config):
    """ Test read access by checking the contents of the configured UNC path are not empty """
    print("Testing read access...")
    print(f"Host: {nas_config['hosts'][host]}")
    print(f"User: {nas_config['users'][user]['username']}")
    smbclient.reset_connection_cache()
    register_nas_host(nas_config, host, user)
    path = build_unc_path(nas_config, host)
    entries = smbclient.listdir(path)
    print(f"Found {len(entries)} entries : {entries}")
    assert len(entries) > 0


# def test_write_access_allowed(smb_config):
#     path = register_and_get_path(smb_config, "mirror", "service")
#     filename = f"smb_test_{os.urandom(4).hex()}.txt"
#     filepath = f"{path}/{filename}"

#     try:
#         with smbclient.open_file(filepath, "w") as f:
#             f.write("smb write test")
#         assert smbclient.path.exists(filepath)
#     finally:
#         if smbclient.path.exists(filepath):
#             smbclient.unlink(filepath)


# @pytest.mark.parametrize("host,user", [
#     ("mirror", "normal"),
#     ("origin", "normal"),
#     ("origin", "service"),
# ])
# def test_write_access_denied(host, user, smb_config):
#     path = register_and_get_path(smb_config, host, user)
#     filename = f"smb_test_{os.urandom(4).hex()}.txt"
#     filepath = f"{path}/{filename}"

#     with pytest.raises(PermissionError):
#         with smbclient.open_file(filepath, "w") as f:
#             f.write("smb write test")

#     if smbclient.path.exists(filepath):
#         smbclient.unlink(filepath)