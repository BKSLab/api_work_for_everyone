import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class SettingsBase(BaseSettings):
    """Базовый класс для настроек приложения."""
    model_config = SettingsConfigDict(env_file=os.path.join(BASE_DIR, '.env'))


class DBSettings(SettingsBase):
    """Класс настроек для работы с БД"""
    postgres_host: SecretStr
    postgres_user: SecretStr
    postgres_password: SecretStr
    postgres_db: SecretStr

    @property
    def url_connect(self) -> str:
        return (
            f'postgresql+asyncpg://{self.postgres_user.get_secret_value()}:'
            f'{self.postgres_password.get_secret_value()}@'
            f'{self.postgres_host.get_secret_value()}/'
            f'{self.postgres_db.get_secret_value()}'
        )


class Settings(BaseSettings):
    """Общий класс работы с чувствительными данными."""
    db: DBSettings = Field(default_factory=DBSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
