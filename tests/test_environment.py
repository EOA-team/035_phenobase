import pytest

from src.db import PhenobaseEnv, get_database_name, get_engine


@pytest.mark.integration_test
def test_production_env(monkeypatch):
    """Test that the production database name is returned when PHENOBASE_ENV is set to 'production'."""
    monkeypatch.setenv("PHENOBASE_ENV", PhenobaseEnv.PRODUCTION.value)
    engine = get_engine()
    print(f"Engine URL: {engine.url.database}")
    assert engine.url.database == get_database_name(PhenobaseEnv.PRODUCTION)


@pytest.mark.integration_test
def test_test_env(monkeypatch):
    """Test that the test database name is returned when PHENOBASE_ENV is set to 'test'."""
    monkeypatch.setenv("PHENOBASE_ENV", PhenobaseEnv.TEST.value)
    print(f"PHENOBASE_ENV: {PhenobaseEnv.TEST.value}")
    engine = get_engine()
    print(f"Engine URL: {engine.url.database}")
    assert engine.url.database == get_database_name(PhenobaseEnv.TEST)
