import secrets

from passlib.context import CryptContext

# Создаем контекст для хеширования, используя bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

API_KEY_SECRET_LENGTH = 32  # Длина случайной части ключа в байтах
DB_PREFIX_SECRET_LENGTH = 8  # Длина случайной части в префиксе для БД


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли обычный пароль хешированному.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Хеширует пароль."""
    return pwd_context.hash(password)


def generate_api_key(prefix: str) -> tuple[str, str]:
    """
    Генерирует новый API-ключ, состоящий из префикса и случайной части.

    Args:
        prefix: Человекочитаемый префикс (например, 'wfe').

    Returns:
        Кортеж, содержащий:
        - full_key: Полный ключ для клиента (e.g., 'wfe_xxxxxxxxxxxxxx').
        - db_prefix: Префикс для хранения в БД и поиска (e.g., 'wfe_xxxxxxxx').
    """
    secret_part = secrets.token_urlsafe(API_KEY_SECRET_LENGTH)
    full_key = f"{prefix}_{secret_part}"
    db_prefix = f"{prefix}_{secret_part[:DB_PREFIX_SECRET_LENGTH]}"
    return full_key, db_prefix
