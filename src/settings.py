from enum import StrEnum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Infrastructure(StrEnum):
    AGS_FOLA = "ags_fola"
    LOCAL = "local"


class DeployStage(StrEnum):
    TEST = "test"
    PRODUCTION = "production"


class DatabaseName(StrEnum):
    PHENOBASE = "phenobase"
    TEST_PHENOBASE = "test_phenobase"


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", extra="ignore")
    host: str  # DB_HOST
    port: int  # DB_PORT
    user: str  # DB_USER
    password: SecretStr  # DB_PASSWORD
    name_prod: DatabaseName = DatabaseName.PHENOBASE  # Hardcoded!
    name_test: DatabaseName = DatabaseName.TEST_PHENOBASE  # Hardcoded!


class StorageConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="STORAGE_", env_file=".env", extra="ignore"
    )
    host: str  # STORAGE_HOST
    share: str  # STORAGE_SHARE
    folder: str  # PHENOBASE_ROOT
    local_path: str  # STORAGE_LOCAL_PATH


class FolaConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FOLA_", env_file=".env", extra="ignore"
    )
    base_domain: str  # FOLA_BASE_DOMAIN
    gamarello_domain: str  # FOLA_GAMARELLO_DOMAIN
    normal_user: str  # FOLA_NORMAL_USER
    normal_password: SecretStr  # FOLA_NORMAL_PASSWORD
    service_user: str  # FOLA_SERVICE_USER
    service_password: SecretStr  # FOLA_SERVICE_PASSWORD


class Settings(BaseSettings):
    """Reads INFRASTRUCTURE and DEPLOY_STAGE from env / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    infrastructure: Infrastructure
    deploy_stage: DeployStage
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    fola: FolaConfig = Field(default_factory=FolaConfig)


if __name__ == "__main__":
    settings = Settings()
    fola = settings.fola
    print(fola)
