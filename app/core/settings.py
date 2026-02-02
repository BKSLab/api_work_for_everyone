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
    base_algoritm: SecretStr
    jwt_private_key_path: Path = BASE_DIR / "app" / "utils" / "jwt" / "keys" / "private.pem"
    jwt_public_key_path: Path = BASE_DIR / "app" / "utils" / "jwt" / "keys" / "public.pem"
    jwt_expire_seconds: int = 3600  # по умолчанию 1 час
    jwt_refresh_expire_days: int = 30  # по умолчанию 30 дней
    logging_config_path: Path = BASE_DIR / "logging.ini"


class EmailSettings(SettingsBase):
    """Класс настроек для работы с почтой"""
    from_email: SecretStr
    host_name: SecretStr
    port: int
    application_key: SecretStr


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


class Settings(BaseSettings):
    """Общий класс работы с чувствительными данными."""
    db: DBSettings = Field(default_factory=DBSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
