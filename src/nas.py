"""NAS configuration and utilities"""

import smbclient

def build_unc_path(nas_config, host):
    """ Build the UNC path for the given host """
    hostname = nas_config['hosts'][host]
    share = nas_config["share"]
    folder = nas_config["folder"]
    return rf"\\{hostname}\\{share}\\{folder}"



def register_nas_host(nas_config, host, user):
    """Register a NAS host with the given user credentials"""
    hostname = nas_config['hosts'][host]
    credentials = nas_config["users"][user]
    smbclient.register_session(
        hostname,
        username=credentials["username"],
        password=credentials["password"],
    )
