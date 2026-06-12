""" Shared fixtures for all tests """
import os
import pytest
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


@pytest.fixture(scope="session")
def nas_config():
    """ Configurations used for NAS tests"""
    return {
        "hosts": {
            "mirror": os.environ["NAS_HOST_MIRROR"],
            "origin": os.environ["NAS_HOST_ORIGIN"],
        },
        "share": "Data-EODrone",
        "folder": "drone",
        "users": {
            "normal": { 
                "username": os.environ["NORMAL_USER"],
                "password": os.environ["NORMAL_USER_PW"],
            },
            "service": {
                "username": os.environ["SERVICE_USER"],
                "password": os.environ["SERVICE_USER_PW"],
            },
        },
    }


