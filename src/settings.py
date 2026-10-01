from enum import StrEnum
from functools import cached_property

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Infrastructure(StrEnum):
    ON_PREM = "on_prem"
    LOCAL_DOCKER = "local_docker"


class DeployStage(StrEnum):
    DEV = "dev"
    PRODUCTION = "production"


class DatabaseNames(StrEnum):
    PHENOBASE = "phenobase"
    TEST_PHENOBASE = "test_phenobase"


_DB_NAME_BY_STAGE = {
    DeployStage.PRODUCTION: DatabaseNames.PHENOBASE,
    DeployStage.DEV: DatabaseNames.TEST_PHENOBASE,
}


class OnPremDBSettings(BaseSettings):
    """Reads DB_HOST, DB_PORT, DB_USER, DB_PASSWORD from env / .env.
    No defaults: a missing variable fails at startup."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    db_host: str
    db_port: int
    db_user: str
    db_password: SecretStr


class LocalDockerDBSettings(BaseModel):
    """Hardcoded values for the local docker container. Never reads env."""
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "user"
    db_password: SecretStr = SecretStr("password")


class Settings(BaseSettings):
    """Reads INFRASTRUCTURE and DEPLOY_STAGE from env / .env."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    infrastructure: Infrastructure
    deploy_stage: DeployStage

    @property
    def db_name(self) -> DatabaseNames:
        return _DB_NAME_BY_STAGE[self.deploy_stage]

    @cached_property
    def database_settings(self) -> OnPremDBSettings | LocalDockerDBSettings:
        match self.infrastructure:
            case Infrastructure.ON_PREM:
                return OnPremDBSettings()
            case Infrastructure.LOCAL_DOCKER:
                return LocalDockerDBSettings()

    @property
    def database_url(self) -> URL:
        db = self.database_settings
        return URL.create(
            "postgresql+psycopg",
            username=db.db_user,
            password=db.db_password.get_secret_value(),
            host=db.db_host,
            port=db.db_port,
            database=str(self.db_name),
        )


if __name__ == "__main__":
    settings = Settings()
    print(f"Settings: {settings}")
    print(f"Database Settings: {settings.database_settings}")
    print(f"DB name: {settings.db_name}")
    print(settings.database_url.render_as_string(hide_password=True))