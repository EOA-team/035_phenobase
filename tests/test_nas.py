import os
import smbclient
import pytest
import time

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


@pytest.mark.parametrize(
    "host,user,should_succeed", 
    [
         ("mirror", "service", True),       
         ("mirror", "normal", False), 
         ("origin", "normal", False),
         ("origin", "service", True), 
     ]) 
def test_write_access(host, user, should_succeed, nas_config):
    """ Test write access by attempting to create and delete a test file """
    smbclient.reset_connection_cache()
    register_nas_host(nas_config, host, user)
    path = build_unc_path(nas_config, host)
    filepath = rf"{path}\write_test_{os.urandom(4).hex()}.txt"
    if should_succeed:
        with smbclient.open_file(filepath, "w") as f:
            f.write("test")
        assert smbclient.path.exists(filepath)
        smbclient.unlink(filepath)
    else:
        with pytest.raises(OSError):
            with smbclient.open_file(filepath, "w") as f:
                f.write("test")

# @pytest.mark.parametrize(
#     "source,target", 
#     [
#         ("mirror", "origin"),
#         ("origin", "mirror"),
#     ])

# def test_replication_latency(source, target, nas_config, max_latency_ns: int = 10000):
#     """ Test replication latency by creating a file on the source 
#     and waiting for it to appear on the target """

#     filename = f"repl_{os.urandom(4).hex()}.txt"
#     content = "test"

#     source_path = build_unc_path(nas_config, source) + rf"\{filename}"
#     target_path = build_unc_path(nas_config, target) + rf"\{filename}"

#     # Register source and target 
#     smbclient.reset_connection_cache()
#     register_nas_host(nas_config, source, "service") 
#     register_nas_host(nas_config, target, "service")

#     #Write test file to source
#     with smbclient.open_file(source_path, "w") as f:
#         f.write(content)
#         f.flush()  # Ensure content is written to disk before measuring latency

#     #Start Time and wait for file to appear on target
    
#     start = time.perf_counter_ns()

#     while True:
#         elapsed_ns = time.perf_counter_ns() - start
#         if elapsed_ns > max_latency_ns:
#             print(f"\n  {source} -> {target}: not found within {max_latency_ns}ns")
#             break
#         if smbclient.path.exists(target_path):
#             with smbclient.open_file(target_path, "r") as f:
#                 assert f.read() == content
#             print(f"\n  {source} -> {target}: {elapsed_ns}ns")
#             break

#         time.sleep(0.01) 
#     #Delete test file from source and target
#     smbclient.unlink(source_path)

   