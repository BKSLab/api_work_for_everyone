import logging
from datetime import datetime, timezone

from exceptions.repository_exceptions import BlocklistRepositoryError
from exceptions.users_service_exceptions import BlocklistServiceError
from repositories.blocklist_repository import BlocklistRepository

logger = logging.getLogger(__name__)


class BlocklistService:
    """Сервис для работы с черным списком токенов."""

    def __init__(self, blocklist_repo: BlocklistRepository):
        self.blocklist_repo = blocklist_repo

    async def block_token(self, payload: dict) -> None:
        """
        Добавляет токен в черный список, предотвращая его дальнейшее использование.

        Последовательность действий:
        1.  Извлекает `jti` (JWT ID) и `exp` (timestamp истечения срока) из `payload`.
        2.  Проверяет наличие `jti` и `exp`. Если отсутствуют, выбрасывает `BlocklistServiceError`.
        3.  Преобразует `exp` timestamp в объект `datetime` с учетом UTC.
        4.  Передает `jti` и `exp` в репозиторий для добавления токена в черный список.

        Выбрасывает исключения:
        *   `BlocklistServiceError`: Если `payload` не содержит необходимых полей (`jti`, `exp`).
        *   `BlocklistRepositoryError`: При ошибках взаимодействия с базой данных.
        *   `Exception`: При любых других непредвиденных ошибках сервиса.
        """
        try:
            jti = payload.get("jti")
            exp_timestamp = payload.get("exp")

            if not jti or not exp_timestamp:
                raise BlocklistServiceError(
                    message="Payload must contain 'jti' and 'exp' claims."
                )

            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

            await self.blocklist_repo.add_token_to_blocklist(jti=jti, exp=exp_datetime)

        except (BlocklistServiceError, BlocklistRepositoryError):
            raise

        except Exception:
            logger.exception(
                "Непредвиденная ошибка при добавлении токена пользователя в черный список"
            )
            raise BlocklistServiceError(
                message="Непредвиденная ошибка сервиса при добавлении токена пользователя в черный список."
            )


    async def is_token_blocked(self, payload: dict) -> bool:
        """
        Проверяет, находится ли токен в черном списке.

        Последовательность действий:
        1.  Извлекает `jti` (JWT ID) из `payload`.
        2.  Проверяет наличие `jti`. Если отсутствует, выбрасывает `BlocklistServiceError`.
        3.  Передает `jti` в репозиторий для проверки его статуса в черном списке.

        Возвращает:
        *   `bool`: `True`, если токен заблокирован; `False` в противном случае.

        Выбрасывает исключения:
        *   `BlocklistServiceError`: Если `payload` не содержит необходимого поля (`jti`).
        *   `BlocklistRepositoryError`: При ошибках взаимодействия с базой данных.
        *   `Exception`: При любых других непредвиденных ошибках сервиса.
        """
        try:
            jti = payload.get("jti")
            if not jti:
                raise BlocklistServiceError(
                    message="Payload must contain 'jti' claim."
                )

            return await self.blocklist_repo.is_token_blocked(jti=jti)
        except (BlocklistServiceError, BlocklistRepositoryError):
            raise

        except Exception:
            logger.exception(
                "Непредвиденная ошибка при проверки токена на предмет его включение в черный список"
            )
            raise BlocklistServiceError(
                message="Непредвиденная ошибка сервиса при проверки токена на предмет его включение в черный список."
            )
