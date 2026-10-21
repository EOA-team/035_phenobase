import pytest

from src.db_session import get_database_name, get_engine_postgresql
from src.settings import Settings
from src.utils.nas_utils import build_unc_path


@pytest.mark.integration
def test_database_settings():
    """Tests thatthe database settings are correctly configured and the engine connects to the expected database."""
    settings = Settings()
    dbs = settings.database
    engine = get_engine_postgresql()

    assert engine.url.database == get_database_name(settings.deploy_stage)
    assert engine.url.username == dbs.user
    assert engine.url.password == dbs.password.get_secret_value()
    assert engine.url.host == dbs.host
    assert engine.url.port == dbs.port


def test_storage_settings():
    """Tests that the storage settings are correctly configured."""

    settings = Settings()
    storage = settings.storage
    unc_path = build_unc_path(
        hostname=storage.host, share=storage.share, folder=storage.folder
    )
    assert unc_path == rf"\\{storage.host}\{storage.share}\{storage.folder}"
