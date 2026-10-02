from enum import StrEnum
from functools import cached_property

from pydantic import BaseModel, SecretStr, Field
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
    model_config = SettingsConfigDict(
        env_prefix="DB_", 
        env_file=".env", 
        extra="ignore"
    )  
    host: str # DB_HOST
    port: int # DB_PORT
    user: str # DB_USER
    password: SecretStr # DB_PASSWORD
    name_prod: DatabaseName # DB_NAME_PROD
    name_test: DatabaseName # DB_NAME_TEST

class Settings(BaseSettings):
    """Reads INFRASTRUCTURE and DEPLOY_STAGE from env / .env."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    infrastructure: Infrastructure
    deploy_stage: DeployStage
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

if __name__ == "__main__":
    settings = Settings()
    db = settings.database
    print(f"Database settings: {db}")
    print(f"Database name for production: {db.name_prod}")
    print(f"Database name for testing: {db.name_test}")
    print(f"Database host: {db.host}")
    print(f"Database port: {db.port}")
    print(f"Database user: {db.user}")
    print(f"Database password: {db.password}")
