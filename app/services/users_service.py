from exceptions.repository_exceptions import UsersRepositoryError
from repositories.users_repository import UsersRepository
from core.config_logger import logger
from fastapi import HTTPException
from starlette import status

from schemas.users import UserRegisterSchema
from utils.security import hash_password


class UsersService:
    """
    Сервис для работы с пользователями.
    """

    def __init__(
        self,
        users_repository: UsersRepository,
    ):
        self.users_repository = users_repository

    async def check_user_exists(
        self, email: str, username: str
    ) -> bool:
        """
        Проверяет, существует ли пользователь с указанным email или username.
        Возвращает True, если пользователь найден, иначе False.
        """
        try:
            # Мы предполагаем, что get_user вернет None, если пользователь не найден
            user = await self.users_repository.get_user(
                email=email,
                username=username
            )
            if user:
                logger.info(f'Пользователь с email: {email} или username: {username} уже существует.')
                return True
            return False
        except UsersRepositoryError as error:
            # Эту ошибку лучше не "проглатывать", а пробрасывать выше,
            # чтобы API мог вернуть клиенту ошибку сервера (500).
            logger.error(f'Ошибка доступа к БД при проверке пользователя: {error}')
            raise

    async def register_user(self, user_data: UserRegisterSchema):
        """
        Регистрирует нового пользователя.

        1. Проверяет, не заняты ли email или username.
        2. Если заняты, выбрасывает ошибку HTTPException 409 Conflict.
        3. Если свободны, хеширует пароль и создает нового пользователя.
        4. Отправляет код подтверждения (как фоновую задачу).
        """
        # 1. Проверяем существование пользователя
        user_exists = await self.users_repository.get_user(
            email=user_data.email,
            username=user_data.username
        )

        # 2. Если пользователь найден, сообщаем об этом фронтенду через ошибку
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email или username уже существует."
            )

        # 3. Если все хорошо, продолжаем регистрацию
        hashed_pass = hash_password(user_data.password) # Хешируем пароль

        # Создаем пользователя в БД
        new_user = await self.users_repository.create_user(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_pass
        )

        # 4. Отправка письма (лучше делать в фоне, чтобы не задерживать ответ)
        # background_tasks.add_task(send_verification_code, new_user.email)
        logger.info(f'Пользователь {new_user.username} успешно зарегистрирован.')

        return new_user

