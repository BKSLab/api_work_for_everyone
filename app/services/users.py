import logging
from datetime import datetime, timezone

from pydantic import EmailStr

from db.models.users import User
from exceptions.services import UsersServiceError
from exceptions.users import (
    EmailNotVerifiedError,
    ExpiredCodeError,
    InvalidCodeError,
    InvalidCredentialsError,
    UserAlreadyExists,
    UserAlreadyVerified,
    UserInactiveError,
    UserNotFound,
)
from repositories.users import UsersRepository
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
    """Сервис для управления бизнес-логикой, связанной с пользователями."""

    def __init__(self, users_repository: UsersRepository):
        self.users_repository = users_repository

    async def register_user_handler(self, user_data: UserRegisterSchema):
        """
        Обрабатывает регистрацию нового пользователя.

        Проверяет, существует ли пользователь. Если пользователь уже существует и
        верифицирован, выбрасывается исключение. Если существует, но не
        верифицирован, его данные (имя, пароль) обновляются. Если не существует,
        создается новая запись. В обоих случаях, когда пользователь не
        верифицирован, ему отправляется новый код подтверждения на email.

        Args:
            user_data: Данные для регистрации пользователя.

        Raises:
            UserAlreadyExists: Если пользователь с таким email уже существует и верифицирован.
            UsersServiceError: При ошибках в процессе хеширования пароля или отправки email.
        """
        logger.info(
            "Старт регистрации нового пользователя с почтой: %s", user_data.email
        )
        # user = await self.users_repository.get_user_only_email(email=user_data.email)
        try:
            user = await self._get_user_by_email(email=user_data.email)
        except UserNotFound:
            logger.info(
                "Пользователь с почтой %s не найден в базе. Запускаем процедуру регистрации нового пользователя.",
                user_data.email
            )
            logger.info("Пользователь с почтой %s не найден. Продолжаем регистрацию.", user_data.email)
            await self._new_user_registration(user_data=user_data)
            return
        
        # 2. Обрабатываем случаи, когда пользователь найден и верефицирован
        if user and user.is_verified:
            raise UserAlreadyExists(email=user_data.email)

        # 3. Обрабатываем случаи, когда пользователь найден, но не верифицирован
        await self._process_unverified_existing_user(
            user_data=user_data, user_id=user.id,
        )

    async def resend_verification_code(self, email: EmailStr):
        """
        Повторно отправляет код верификации на email пользователя.

        Находит пользователя по email. Если он уже верифицирован, выбрасывается
        исключение. В противном случае, старые коды удаляются, генерируется
        и отправляется новый код.

        Args:
            email: Email адрес пользователя.

        Raises:
            UserAlreadyVerified: Если пользователь уже прошел верификацию.
        """
        logger.info(
            "Старт повторной отправки кода верификации на почту: %s", email
        )
        user = await self._get_user_by_email(email=email)

        if user.is_verified:
            raise UserAlreadyVerified(
                email=email
            )
            
        logger.info(
            "Получен запрос на повторную отправку кода верификации на email: %s "
            "от пользователя, который ранее не проходил процедуру верификации.", email
        )
        # Удаляем старые коды верификации
        await self.users_repository.delete_verification_codes(user_id=user.id)

        verified_code = await self._send_otp_code_by_email(
            user_name=user.username,
            user_email=user.email,
        )

        logger.info(
            "Письмо с повторным кодом верификации успешно отправлено на %s!", email
        )

        await self.users_repository.save_verification_code(
            user_id=user.id,
            code=verified_code
        )
        logger.info("Код верификации повторно отправлен для пользователя %s.", email)

    async def forgot_password(self, email: EmailStr):
        """
        Инициирует процедуру сброса пароля.

        Находит верифицированного пользователя по email, удаляет его старые коды
        сброса пароля, генерирует и отправляет новый код на email.

        Args:
            email: Email адрес пользователя.

        Raises:
            UserNotFound: Если верифицированный пользователь с таким email не найден.
        """
        logger.info(
            "Старт обработки (отправка кода сброса пароля) запроса на "
            "сброс пароля для пользователя с email: %s", email
        )

        user = await self.users_repository.get_user_by_email(
            email=email, is_verified=True
        )
        if not user:
            raise UserNotFound(email=email)

        # Удаляем все существующие коды сброса пароля для этого пользователя
        await self.users_repository.delete_password_reset_codes(user_id=user.id)

        # Генерируем и отправляем новый код сброса
        reset_code = await send_otp_code_by_email(
            user_name=user.username if user.username else user.email,
            user_email=user.email,
            message_template=PASSWORD_RESET_MESSAGE,
            subject="Код сброса пароля"
        )

        # Сохраняем код сброса в БД
        await self.users_repository.save_password_reset_code(
            user_id=user.id,
            code=reset_code
        )

        logger.info("Код сброса пароля успешно отправлен на email: %s.", email)

    async def reset_password(self, user_data: ResetPasswordRequestSchema):
        """
        Устанавливает новый пароль для пользователя.

        Проверяет, что пользователь существует и верифицирован. Валидирует код
        сброса пароля. Если все проверки успешны, обновляет пароль пользователя
        и удаляет использованные коды сброса.

        Args:
            user_data: Данные для сброса пароля, включая email, код и новый пароль.

        Raises:
            EmailNotVerifiedError: Если email пользователя не подтвержден.
            InvalidCodeError: Если предоставленный код сброса неверный.
            ExpiredCodeError: Если срок действия кода сброса истек.
        """
        logger.info(
            "Начало обработки запроса на сброс пароля для пользователя с email: %s", user_data.email
        )

        user = await self._get_user_by_email(email=user_data.email)
        
        if not user.is_verified:
            raise EmailNotVerifiedError(email=user_data.email)

        reset_code_entry = await self.users_repository.find_password_reset_code(
            user_id=user.id, code=user_data.code
        )
        if not reset_code_entry:
            raise InvalidCodeError(
                user_id=user.id, email=user_data.email, code=user_data.code
            )

        if reset_code_entry.expires_at < datetime.now(timezone.utc):
            raise ExpiredCodeError(
                user_id=user.id, email=user_data.email, code=user_data.code
            )

        hashed_new_password = self._hashing_user_password(password=user_data.new_password)

        await self.users_repository.update_user_password(
            user_id=user.id,
            new_password_hash=hashed_new_password
        )
        logger.info("Пароль пользователя %s успешно обновлен.", user_data.email)

        await self.users_repository.delete_password_reset_codes(user_id=user.id)
        logger.info("Коды сброса пароля для пользователя %s удалены.", user_data.email)
        logger.info("Пароль для пользователя %s успешно сброшен.", user_data.email)

    async def verify_user_email(self, user_data: EmailVerifySchema) -> User:
        """
        Подтверждает email пользователя с помощью кода верификации.

        Находит пользователя, проверяет, что он еще не верифицирован.
        Валидирует код верификации. Если все успешно, подтверждает email,
        активирует пользователя и удаляет использованные коды.

        Args:
            user_data: Данные для верификации, включая email и код.

        Returns:
            Объект пользователя с обновленным статусом.

        Raises:
            UserAlreadyVerified: Если email пользователя уже подтвержден.
            InvalidCodeError: Если предоставленный код верификации неверный.
            ExpiredCodeError: Если срок действия кода верификации истек.
        """
        logger.info(
            "Начало проверки кода активации почты для пользователя с email: %s", user_data.email
        )

        user = await self._get_user_by_email(email=user_data.email)
    
        if user.is_verified:
            raise UserAlreadyVerified(email=user_data.email)

        verification_code = await self.users_repository.find_verification_code(
            user_id=user.id, code=user_data.code
        )
        if not verification_code:
            raise InvalidCodeError(user_id=user.id, email=user_data.email, code=user_data.code)

        if verification_code.expires_at < datetime.now(timezone.utc):
            raise ExpiredCodeError(
                user_id=user.id, email=user_data.email, code=user_data.code
            )

        await self.users_repository.confirm_user_email(user_id=user.id)
        await self.users_repository.delete_verification_codes(user_id=user.id)

        logger.info("Почта пользователя %s успешно подтверждена.", user_data.email)
        return user
    
    async def login_user(self, user_data: UserLoginSchema) -> User:
        """
        Аутентифицирует пользователя в системе.

        Проверяет, что пользователь существует, его email верифицирован и аккаунт
        активен. Сверяет предоставленный пароль с хешем в базе данных.

        Args:
            user_data: Данные для входа, включая email и пароль.

        Returns:
            Объект аутентифицированного пользователя.

        Raises:
            EmailNotVerifiedError: Если email пользователя не подтвержден.
            UserInactiveError: Если аккаунт пользователя неактивен.
            InvalidCredentialsError: Если пароль указан неверно.
        """
        logger.info(
            "Аутентификация пользователя с email: %s", user_data.email
        )
        user = await self._get_user_by_email(email=user_data.email)
    
        if not user.is_verified:
            raise EmailNotVerifiedError(email=user_data.email)

        if not user.is_active:
            raise UserInactiveError(email=user_data.email)

        self._verification_user_password(
            password=user_data.password,
            password_hash=user.password_hash
        )

        logger.info("Пользователь с почтой %s успешно аутентифицирован.", user_data.email)
        return user

    async def get_user_data(self, email: EmailStr) -> int:
        """
        Возвращает ID пользователя по его email.

        Args:
            email: Email адрес пользователя.

        Returns:
            ID пользователя.

        Raises:
            UserNotFound: Если пользователь с таким email не найден.
        """
        logger.info(
            "Обработка запроса на получение данных пользователя с email: %s", email
        )
        user = await self.users_repository.get_user_only_email(email=email)
        if not user:
            raise UserNotFound(email=email)
        return user.id

    # ======= приватные методы =======
    def _hashing_user_password(self, password: str):
        """Хеширует пароль пользователя с использованием bcrypt."""
        try:
            hashed_pass = hash_password(password=password)
            logger.info("Пароль успешно хеширован")
            return hashed_pass
        except Exception as error:
            raise UsersServiceError(
                error_details="An error occurred while hashing the user's password."
            ) from error

    async def _send_otp_code_by_email(
        self,
        user_name: str,
        user_email: str,
        message_template: str = VERIFICATION_MESSAGE,
        subject: str = "Подтверждение адреса электронной почты",
    ) -> str:
        """Отправляет одноразовый пароль (OTP) на указанный email."""
        verified_code = await send_otp_code_by_email(
            user_name=user_name,
            user_email=user_email,
            message_template=message_template,
            subject=subject,
        )
        return verified_code

    async def _process_unverified_existing_user(
        self, user_data: UserRegisterSchema, user_id: int,
        
    ) -> None:
        """Обновляет данные существующего, но не верифицированного пользователя."""
        logger.info(
            "Пользователь с почтой %s уже существует, но не верифицирован. "
            "Обновляем данные.", user_data.email
        )
        hashed_pass = self._hashing_user_password(password=user_data.password)

        verified_code = await self._send_otp_code_by_email(
            user_name=user_data.username,
            user_email=user_data.email,
        )
        await self.users_repository.update_user(
            user_id=user_id,
            username=user_data.username,
            password_hash=hashed_pass,
        )
        await self.users_repository.delete_verification_codes(user_id=user_id)
        await self.users_repository.save_verification_code(
            user_id=user_id, code=verified_code
        )

    async def _process_new_unverified_user(
        self,
        user_data: UserRegisterSchema,
        hashed_pass: str,
        verified_code: str
    ):
        """Создает запись для нового, не верифицированного пользователя."""
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

    def _verification_user_password(self, password: str, password_hash: str):
        """Проверяет соответствие пароля его хешу."""
        verify_result = verify_password(
            plain_password=password,
            hashed_password=password_hash
        )
        if not verify_result:
            raise InvalidCredentialsError()
        logger.info("Пароль совпадает")

    async def _new_user_registration(self, user_data: UserRegisterSchema) -> None:
        """Обрабатывает регистрацию нового пользователя."""
        hashed_pass = self._hashing_user_password(password=user_data.password)
        
        # Отправка OTP кода на почту пользователя
        verified_code = await self._send_otp_code_by_email(
            user_name=user_data.username,
            user_email=user_data.email,
        )
        await self._process_new_unverified_user(
            user_data=user_data,
            hashed_pass=hashed_pass,
            verified_code=verified_code
        )
        logger.info(
            "Пользователь с email: %s успешно зарегистрирован. Пользователю отправлен "
            "код для подтверждения адреса электронной почты", user_data.email
        )

    async def _get_user_by_email(self, email: EmailStr) -> User:
        """Возвращает объект пользователя по email, или выбрасывает UserNotFound."""
        user = await self.users_repository.get_user_only_email(email=email)
        if not user:
            raise UserNotFound(email=email)
        return user

