import os

from smbclient import (
    register_session, 
    reset_connection_cache,
)
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


def connect_to_nas(user_type: User, password: Password):
    reset_connection_cache()
    user = user_type.value + "@" + os.environ["FOLA_DOMAIN"]
    register_session(
        server=os.environ["NAS_RECKENHOLZ"],
        username=user,
        password=password.value,
    )
