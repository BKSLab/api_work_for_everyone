import logging
from datetime import datetime, timezone

from pydantic import EmailStr

from db.models.users import User
from exceptions.repository_exceptions import UsersRepositoryError
from exceptions.users_service_exceptions import (
    EmailNotVerifiedError,
    ExpiredCodeError,
    InvalidCodeError,
    InvalidCredentialsError,
    UserAlreadyExists,
    UserAlreadyVerified,
    UserInactiveError,
    UserNotFound,
    UsersServiceError,
)
from repositories.users_repository import UsersRepository
from schemas.users import (
    EmailVerifySchema,
    ResetPasswordRequestSchema,
    UserLoginSchema,
    UserRegisterSchema,
)
from utils.security import hash_password, verify_password
from utils.send_otp_code.message_template import (
    PASSWORD_RESET_MESSAGE,
    VERIFICATION_MESSAGE,
)
from utils.send_otp_code.send_otp_code_to_email import send_otp_code_by_email

logger = logging.getLogger(__name__)


class UsersService:
    """Сервис для работы с пользователями."""

    def __init__(self, users_repository: UsersRepository):
        self.users_repository = users_repository

    async def register_user_handler(self, user_data: UserRegisterSchema):
        """
        Регистрирует нового пользователя или обновляет данные существующего не верифицированного.

        Последовательность действий:
        1.  Проверяет, существует ли пользователь с данным email.
        2.  **Случай 1: Пользователь существует и верифицирован.**
            - Выбрасывает исключение `UserAlreadyExists` без дальнейших действий.
        3.  **Если пользователь не найден или не верифицирован:**
            - Хеширует пароль и отправляет код верификации на email.
        4.  **Случай 2: Пользователь существует, но не верифицирован.**
            - Логирует попытку повторной регистрации.
            - Обновляет данные пользователя (имя, пароль) в репозитории.
            - Удаляет старые коды верификации и сохраняет новый.
            - Логирует успешное обновление и отправку кода.
        5.  **Случай 3: Пользователь не существует.**
            - Логирует первую попытку регистрации.
            - Создает новую запись о пользователе в базе данных.
            - Сохраняет верификационный код в репозитории.
            - Логирует успешное создание пользователя и отправку кода.

        Выбрасывает исключения:
        *   `UserAlreadyExists`: Если пользователь с указанным email уже зарегистрирован и верифицирован.
        *   `UsersServiceError`: При ошибках отправки верификационного кода или других непредвиденных ошибках.
        *   `UsersRepositoryError`: При ошибках взаимодействия с базой данных.
        """
        logger.info(
            "Старт регистрации нового пользователя с почтой: %s", user_data.email
        )
        try:
            user = await self.users_repository.get_user_only_email(email=user_data.email)

            # Случай 1: Пользователь найден и верифицирован. Немедленно выходим.
            if user and user.is_verified:
                raise UserAlreadyExists(message=user_data.email)

            # На этом этапе мы знаем, что пользователь либо не существует,
            # либо существует, но не верифицирован. Оба сценария требуют отправки кода.
            hashed_pass = self._hashing_user_password(password=user_data.password)

            verified_code = await send_otp_code_by_email(
                user_name=user_data.username,
                user_email=user_data.email,
                message_template=VERIFICATION_MESSAGE,
                subject="Подтверждение адреса электронной почты",
            )
            if not verified_code:
                raise UsersServiceError(
                    message="Не удалось отправить код верефикации адреса электронной почты."
                )

            if user:
                # Случай 2: Пользователь найден, но не верифицирован.
                logger.info(
                    "Пользователь с почтой %s уже существует, но не верифицирован. "
                    "Обновляем данные.", user_data.email
                )
                await self.users_repository.update_user(
                    user_id=user.id,
                    username=user_data.username,
                    password_hash=hashed_pass,
                )
                await self.users_repository.delete_verification_codes(user_id=user.id)
                await self.users_repository.save_verification_code(
                    user_id=user.id,
                    code=verified_code
                )
            else:
                # Случай 3: Пользователь не найден.
                logger.info(
                    "Пользователь с почтой: %s ранее не проходил процедуру регистрации. Создаем новую запись.",
                    user_data.email
                )
                new_user = await self.users_repository.create_user(
                    email=user_data.email,
                    password_hash=hashed_pass,
                    username=user_data.username,
                )
                await self.users_repository.save_verification_code(
                    user_id=new_user.id,
                    code=verified_code
                )
        except (UserAlreadyExists, UsersServiceError, UsersRepositoryError):
            raise
        except Exception:
            logger.exception(
                "Непредвиденная ошибка при регистрации пользователя с email: %s",
                user_data.email
            )
            raise UsersServiceError(message="Непредвиденная ошибка сервиса при регистрации пользователя.")

        logger.info(
            "Пользователь с email: %s успешно зарегистрирован. Пользователю отправлен "
            "код для подтверждения адреса электронной почты", user_data.email
        )

    def _hashing_user_password(self, password: str):
        """Хеширование пароля пользователя при регистрации."""
        try:
            hashed_pass = hash_password(password=password)
            logger.info("Пароль успешно хеширован")
            return hashed_pass
        except Exception as error:
            logger.error("Ошибка при хешировании пароля: %s", error, exc_info=True)
            raise UsersServiceError(
                message="An error occurred while hashing the user's password."
            )

    def _verification_user_password(self, password: str, password_hash: str):
        """
        Проверяет предоставленный пароль пользователя на соответствие хешу.

        Последовательность действий:
        1.  Вызывает утилиту `verify_password` для сравнения.
        2.  В случае несовпадения паролей логирует информацию и выбрасывает `InvalidCredentialsError`.
        3.  В случае совпадения логирует успех.

        Выбрасывает исключения:
        *   `InvalidCredentialsError`: Если предоставленный пароль не соответствует хешу.
        """
        verify_result = verify_password(
            plain_password=password,
            hashed_password=password_hash
        )
        if not verify_result:
            logger.info("Пароль не совпадает.")
            raise InvalidCredentialsError(
                message="Пользователь предоставил некорректный пароль."
            )
        logger.info("Пароль совпадает")

    async def resend_verification_code(self, email: EmailStr):
        """
        Повторно отправляет код верификации пользователю.

        Последовательность действий:
        1.  Логирует начало процесса повторной отправки кода верификации.
        2.  Извлекает пользователя из репозитория по email.
            *   Если пользователь не найден, выбрасывает `UserNotFound` с соответствующим сообщением.
        3.  Проверяет статус верификации пользователя.
            *   Если пользователь уже верифицирован, выбрасывает `UserAlreadyVerified` с email пользователя.
        4.  Логирует, что запрос на повторную отправку получен для неверифицированного пользователя.
        5.  Удаляет все старые коды верификации для данного пользователя из репозитория.
        6.  Отправляет новый верификационный код на email пользователя.
            *   В случае неудачи отправки, выбрасывает `UsersServiceError`.
        7.  Логирует успешную отправку нового кода.
        8.  Сохраняет новый код верификации в репозитории.
        9.  Логирует успешное завершение процесса повторной отправки.

        Выбрасывает исключения:
        *   `UserNotFound`: Если пользователь с указанным email не найден.
        *   `UserAlreadyVerified`: Если пользователь с указанным email уже верифицирован.
        *   `UsersServiceError`: При ошибках отправки верификационного кода или других непредвиденных ошибках сервиса.
        *   `UsersRepositoryError`: При ошибках взаимодействия с базой данных.
        """
        logger.info(
            "Старт повторной отправки кода верификации на почту: %s", email
        )
        try:
            user = await self.users_repository.get_user_only_email(email=email)
            if not user:
                raise UserNotFound(message=f"Пользователь с email {email} не найден.")

            if user.is_verified:
                raise UserAlreadyVerified( # Corrected: fixed typo emaiL
                    message=f"Пользователь с email {email} уже верифицирован."
                )
            
            logger.info(
                "Получен запрос на повторную отправку кода верификации на email: %s "
                "от пользователя, который ранее не проходил процедуру верификации.", email
            )
            # Удаляем старые коды верификации
            await self.users_repository.delete_verification_codes(user_id=user.id)

            verified_code = await send_otp_code_by_email(
                user_name=user.username,
                user_email=user.email,
                message_template=VERIFICATION_MESSAGE,
                subject="Подтверждение адреса электронной почты",
            )
            if not verified_code:
                raise UsersServiceError(
                    message="Failed to send verification code to user's email."
                )

            logger.info(
                "Письмо с повторным кодом верификации успешно отправлено на %s!", email
            )

            await self.users_repository.save_verification_code(
                user_id=user.id,
                code=verified_code
            )
        except (UsersRepositoryError, UserNotFound, UserAlreadyVerified, UsersServiceError):
            raise
        except Exception:
            logger.exception(
                "Непредвиденная ошибка при повторной отправке кода верификации на email: %s", email
            )
            raise UsersServiceError(message="Непредвиденная ошибка сервиса при повторной отправке кода верификации.")

        logger.info("Код верификации повторно отправлен для пользователя %s.", email)

    async def forgot_password(self, email: EmailStr):
        """
        Обрабатывает запрос на сброс пароля.

        Последовательность действий:
        1.  Логирует начало процесса сброса пароля.
        2.  Ищет в репозитории верифицированного пользователя по email.
            *   Если пользователь не найден или не верифицирован, выбрасывает `UserNotFound`.
        3.  Удаляет все предыдущие коды сброса пароля для данного пользователя.
        4.  Генерирует и отправляет новый код сброса на email пользователя.
            *   В случае неудачи отправки, выбрасывает `UsersServiceError`.
        5.  Сохраняет новый код сброса в базе данных.
        6.  Логирует успешную отправку кода.

        Выбрасывает исключения:
        *   `UserNotFound`: Если верифицированный пользователь с указанным email не найден.
        *   `UsersServiceError`: При ошибках отправки кода сброса или других непредвиденных ошибках сервиса.
        *   `UsersRepositoryError`: При ошибках взаимодействия с базой данных.
        """
        logger.info(
            "Старт обработки (отправка кода сброса пароля) запроса на "
            "сброс пароля для пользователя с email: %s", email
        )
        try:
            user = await self.users_repository.get_user_by_email(
                email=email, is_verified=True
            )
            if not user:
                raise UserNotFound(message=f"Верифицированный пользователь с email {email} не найден.")

            # Удаляем все существующие коды сброса пароля для этого пользователя
            await self.users_repository.delete_password_reset_codes(user_id=user.id)

            # Генерируем и отправляем новый код сброса
            reset_code = await send_otp_code_by_email(
                user_name=user.username if user.username else user.email,
                user_email=user.email,
                message_template=PASSWORD_RESET_MESSAGE,
                subject="Код сброса пароля"
            )
            if not reset_code:
                raise UsersServiceError(
                    message="Не удалось отправить код сброса пароля на email пользователя."
                )

            # Сохраняем код сброса в БД
            await self.users_repository.save_password_reset_code(
                user_id=user.id,
                code=reset_code
            )
        except (UsersRepositoryError, UserNotFound, UsersServiceError):
            raise
        except Exception:
            logger.exception(
                "Непредвиденная ошибка при отправке кода сброса пароля на email: %s", email
            )
            raise UsersServiceError(message="Непредвиденная ошибка сервиса при отправке кода сброса пароля.")
        
        logger.info("Код сброса пароля успешно отправлен на email: %s.", email)

    async def reset_password(self, user_data: ResetPasswordRequestSchema):
        """
        Сбрасывает пароль пользователя после успешной верификации кода сброса.

        Последовательность действий:
        1.  Логирует начало процесса сброса пароля.
        2.  Ищет пользователя в репозитории по email.
            *   Если пользователь не найден, выбрасывает `UserNotFound`.
            *   Если пользователь не верифицирован, выбрасывает `EmailNotVerifiedError`.
        3.  Проверяет предоставленный код сброса пароля.
            *   Если код не найден, выбрасывает `InvalidCodeError`.
            *   Если код истек, выбрасывает `ExpiredCodeError`.
        4.  Хеширует новый пароль пользователя.
        5.  Обновляет хешированный пароль пользователя в базе данных.
        6.  Удаляет все связанные коды сброса пароля для этого пользователя.
        7.  Логирует успешное завершение сброса пароля.

        Выбрасывает исключения:
        *   `UserNotFound`: Если пользователь с указанным email не найден.
        *   `EmailNotVerifiedError`: Если email пользователя не подтвержден.
        *   `InvalidCodeError`: Если предоставленный код сброса пароля недействителен.
        *   `ExpiredCodeError`: Если срок действия кода сброса истек.
        *   `UsersServiceError`: При непредвиденных ошибках сервиса.
        *   `UsersRepositoryError`: При ошибках взаимодействия с базой данных.
        """
        logger.info(
            "Начало обработки запроса на сброс пароля для пользователя с email: %s", user_data.email
        )
        try:
            user = await self.users_repository.get_user_only_email(
                email=user_data.email
            )
            if not user:
                raise UserNotFound(message=f"Пользователь с email {user_data.email} не найден.")

            if not user.is_verified:
                raise EmailNotVerifiedError(
                    message=(
                        f"Пользователь с email {user_data.email} не верифицирован. "
                        "Сброс пароля невозможен."
                    )
                )

            reset_code_entry = await self.users_repository.find_password_reset_code(
                user_id=user.id, code=user_data.code
            )
            if not reset_code_entry:
                raise InvalidCodeError(
                    message=f"Получен некорректный код сброса пароля для пользователя с email: {user_data.email}."
                )

            if reset_code_entry.expires_at < datetime.now(timezone.utc):
                raise ExpiredCodeError(
                    message=f"Срок действия кода сброса пароля для пользователя {user_data.email} истек."
                )

            hashed_new_password = self._hashing_user_password(password=user_data.new_password)

            await self.users_repository.update_user_password(
                user_id=user.id,
                new_password_hash=hashed_new_password
            )
            logger.info("Пароль пользователя %s успешно обновлен.", user_data.email)

            await self.users_repository.delete_password_reset_codes(user_id=user.id)
            logger.info("Коды сброса пароля для пользователя %s удалены.", user_data.email)

        except (
            UsersRepositoryError,
            UserNotFound,
            EmailNotVerifiedError,
            InvalidCodeError,
            ExpiredCodeError
        ):
            raise
        except Exception:
            logger.exception(
                "Непредвиденная ошибка сервиса при сохранении нового пароля для пользователя с email: %s", user_data.email
            )
            raise UsersServiceError(
                message="Непредвиденная ошибка сервиса при сохранении нового пароля."
            )
        
        logger.info("Пароль для пользователя %s успешно сброшен.", user_data.email)

    async def verify_user_email(self, user_data: EmailVerifySchema) -> User:
        """
        Проверяет код активации почты пользователя и подтверждает его учетную запись.

        Последовательность действий:
        1.  Логирует начало процесса проверки кода активации.
        2.  Извлекает пользователя из репозитория по email.
            *   Если пользователь не найден, выбрасывает `UserNotFound`.
        3.  Проверяет статус верификации пользователя.
            *   Если пользователь уже верифицирован, выбрасывает `UserAlreadyVerified`.
        4.  Находит запись кода верификации в репозитории.
            *   Если код не найден, выбрасывает `InvalidCodeError`.
        5.  Проверяет срок действия кода верификации.
            *   Если срок действия истек, выбрасывает `ExpiredCodeError`.
        6.  Подтверждает email пользователя, устанавливая `is_verified=True` и `is_active=True`.
        7.  Удаляет все связанные коды верификации для этого пользователя из репозитория.
        8.  Логирует успешное завершение подтверждения почты.

        Выбрасывает исключения:
        *   `UserNotFound`: Если пользователь с указанным email не найден.
        *   `UserAlreadyVerified`: Если пользователь с указанным email уже верифицирован.
        *   `InvalidCodeError`: Если предоставленный код активации недействителен.
        *   `ExpiredCodeError`: Если срок действия кода активации истек.
        *   `UsersServiceError`: При непредвиденных ошибках сервиса.
        *   `UsersRepositoryError`: При ошибках взаимодействия с базой данных.
        """
        logger.info(
            "Начало проверки кода активации почты для пользователя с email: %s", user_data.email
        )
        try:
            user = await self.users_repository.get_user_only_email(
                email=user_data.email,
            )
            if not user:
                raise UserNotFound(message=f"Пользователь с email {user_data.email} не найден.")

            if user.is_verified:
                raise UserAlreadyVerified(
                    message=f"Пользователь с email {user_data.email} уже верифицирован."
                )

            verification_code = await self.users_repository.find_verification_code(
                user_id=user.id, code=user_data.code
            )
            if not verification_code:
                raise InvalidCodeError(
                    message=f"Получен некорректный код активации для пользователя с email {user_data.email}."
                )

            if verification_code.expires_at < datetime.now(timezone.utc):
                raise ExpiredCodeError(
                    message=f"Срок действия кода активации для пользователя {user_data.email} истек."
                )

            await self.users_repository.confirm_user_email(user_id=user.id)
            await self.users_repository.delete_verification_codes(user_id=user.id)

        except (
            UsersRepositoryError,
            UserNotFound,
            InvalidCodeError,
            ExpiredCodeError,
            UserAlreadyVerified
        ):
            raise
        except Exception:
            logger.exception(
                "Непредвиденная ошибка сервиса при активации почты для пользователя с email: %s", user_data.email
            )
            raise UsersServiceError(
                message="Непредвиденная ошибка сервиса при активации почты.."
            )
        
        logger.info("Почта пользователя %s успешно подтверждена.", user_data.email)
        return user

    async def login_user(self, user_data: UserLoginSchema):
        """
        Осуществляет аутентификацию пользователя в системе.

        Последовательность действий:
        1.  Логирует начало процесса аутентификации.
        2.  Извлекает пользователя из репозитория по email.
            *   Если пользователь не найден, выбрасывает `UserNotFound`.
        3.  Проверяет статус верификации email пользователя.
            *   Если email не верифицирован, выбрасывает `EmailNotVerifiedError`.
        4.  Проверяет статус активности пользователя.
            *   Если пользователь не активен, выбрасывает `UserInactiveError`.
        5.  Проверяет предоставленный пароль пользователя.
            *   Если пароль не совпадает, выбрасывает `InvalidCredentialsError`.
        6.  Логирует успешную аутентификацию.

        Выбрасывает исключения:
        *   `UserNotFound`: Если пользователь с указанным email не найден.
        *   `EmailNotVerifiedError`: Если email пользователя не подтвержден.
        *   `UserInactiveError`: Если учетная запись пользователя не активна.
        *   `InvalidCredentialsError`: Если предоставленные учетные данные (email/пароль) неверны.
        *   `UsersServiceError`: При непредвиденных ошибках сервиса.
        *   `UsersRepositoryError`: При ошибках взаимодействия с базой данных.
        """
        logger.info(
            "Аутентификация пользователя с email: %s", user_data.email
        )
        try:
            user = await self.users_repository.get_user_only_email(
                email=user_data.email,
            )
            if not user:
                raise UserNotFound(message=f"Пользователь с email {user_data.email} не найден.")

            if not user.is_verified:
                raise EmailNotVerifiedError(
                    message=(
                        f"Пользователь с email {user_data.email} не верифицирован."
                    )
                )

            if not user.is_active:
                raise UserInactiveError(
                    message=f"Пользователь с email {user_data.email} не активен."
                )

            self._verification_user_password(
                password=user_data.password,
                password_hash=user.password_hash
            )

        except (
            UsersRepositoryError,
            UserNotFound,
            EmailNotVerifiedError,
            UserInactiveError,
            InvalidCredentialsError
        ):
            raise
        except Exception:
            logger.exception(
                "Непредвиденная ошибка сервиса при аутентификации пользователя с email: %s", user_data.email
            )
            raise UsersServiceError(
                message="Непредвиденная ошибка сервиса при аутентификации пользователя."
            )
        
        logger.info("Пользователь с почтой %s успешно аутентифицирован.", user_data.email)
        return user
