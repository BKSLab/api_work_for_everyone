import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class SettingsBase(BaseSettings):
    """Базовый класс для настроек приложения."""
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, '.env'),
        extra='ignore'
    )


class AppSettings(SettingsBase):
    """Класс настроек для приложения"""
    access_token_hh: SecretStr
    master_api_key: SecretStr
    secret_key: SecretStr
    admin_login: str
    admin_password: SecretStr
    logging_config_path: Path = BASE_DIR / "logging.ini"


class DBSettings(SettingsBase):
    """Класс настроек для работы с БД"""
    postgres_host: SecretStr
    postgres_user: SecretStr
    postgres_password: SecretStr
    postgres_name: SecretStr

    @property
    def url_connect(self) -> str:
        return (
            f'postgresql+asyncpg://{self.postgres_user.get_secret_value()}:'
            f'{self.postgres_password.get_secret_value()}@'
            f'{self.postgres_host.get_secret_value()}/'
            f'{self.postgres_name.get_secret_value()}'
        )


class LlmSettings(SettingsBase):
    """Класс настроек для работы с yandex API."""
    llm_api_key: SecretStr
    llm_api_url: SecretStr
    llm_model: SecretStr


class Settings(BaseSettings):
    """Общий класс работы с чувствительными данными."""
    db: DBSettings = Field(default_factory=DBSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    llm: LlmSettings = Field(default_factory=LlmSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
