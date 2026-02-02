import logging
from datetime import datetime, timezone

from exceptions.services import BlocklistServiceError
from repositories.blocklist_repository import BlocklistRepository

logger = logging.getLogger(__name__)


class BlocklistService:
    """Сервис для управления черным списком JWT токенов."""

    def __init__(self, blocklist_repo: BlocklistRepository):
        self.blocklist_repo = blocklist_repo

    async def block_token(self, payload: dict) -> None:
        """
        Добавляет токен в черный список, чтобы предотвратить его повторное использование.

        Извлекает `jti` (JWT ID) и `exp` (время истечения) из `payload` токена.
        Если эти поля отсутствуют, выбрасывается исключение. Время истечения
        преобразуется в объект datetime перед передачей в репозиторий.

        Args:
            payload: Словарь с данными токена.

        Raises:
            BlocklistServiceError: Если в `payload` отсутствуют 'jti' или 'exp'.
        """
        jti = payload.get("jti")
        exp_timestamp = payload.get("exp")

        if not jti or not exp_timestamp:
            raise BlocklistServiceError(
                error_details="Payload must contain 'jti' and 'exp' claims."
            )

        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        await self.blocklist_repo.add_token_to_blocklist(jti=jti, exp=exp_datetime)

    async def is_token_blocked(self, payload: dict) -> bool:
        """
        Проверяет, находится ли JTI токена в черном списке.

        Извлекает `jti` из `payload` и передает его в репозиторий для проверки.

        Args:
            payload: Словарь с данными токена.

        Returns:
            True, если токен заблокирован, иначе False.

        Raises:
            BlocklistServiceError: Если в `payload` отсутствует 'jti'.
        """

        jti = payload.get("jti")
        if not jti:
            raise BlocklistServiceError(
                error_details="Payload must contain 'jti' claim."
            )

        return await self.blocklist_repo.is_token_blocked(jti=jti)
