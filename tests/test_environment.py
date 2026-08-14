import pytest

from src.db import PHENOBASE_ENV, get_database_name, get_engine


@pytest.mark.integration_test
def test_production_env(monkeypatch):
    """Test that the production database name is returned when PHENOBASE_ENV is set to 'production'."""
    monkeypatch.setenv("PHENOBASE_ENV", PHENOBASE_ENV.PRODUCTION.value)
    engine = get_engine()
    print(f"Engine URL: {engine.url.database}")
    assert engine.url.database == get_database_name(PHENOBASE_ENV.PRODUCTION)


@pytest.mark.integration_test
def test_test_env(monkeypatch):
    """Test that the test database name is returned when PHENOBASE_ENV is set to 'test'."""
    monkeypatch.setenv("PHENOBASE_ENV", PHENOBASE_ENV.TEST.value)
    print(f"PHENOBASE_ENV: {PHENOBASE_ENV.TEST.value}")
    engine = get_engine()
    print(f"Engine URL: {engine.url.database}")
    assert engine.url.database == get_database_name(PHENOBASE_ENV.TEST)


