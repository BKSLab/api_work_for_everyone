from fastapi import status


class UserNotFound(Exception):
    """Пользователь не найден."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, email: str):
        self.email = email
        super().__init__(self.email)

    def __str__(self) -> str:
        return f"UserNotFound: A user with email '{self.email}' does not exist."

    @property
    def detail(self) -> str:
        return "A user with this email does not exist."


class UserAlreadyExists(Exception):
    """Пользователь уже ранее проходил процедуру регистрации."""
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, email: str):
        self.email = email
        super().__init__(self.email)

    def __str__(self) -> str:
        return f"UserAlreadyExists: Attempt to register an existing verified user with email '{self.email}'."

    @property
    def detail(self) -> str:
        return "User with this email is already registered."


class UserAlreadyVerified(Exception):
    """Пользователь уже ранее проходил процедуру верификации."""
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, email: str):
        self.email = email
        super().__init__(self.email)

    def __str__(self) -> str:
        return f"UserAlreadyVerified: The user with email '{self.email}' has already completed the verification procedure."

    @property
    def detail(self) -> str:
        return "This user account has already been verified."


class EmailNotVerifiedError(Exception):
    """Адрес почты не подтверждён."""
    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, email: str):
        self.email = email
        super().__init__(self.email)

    def __str__(self) -> str:
        return f"EmailNotVerifiedError: The email address '{self.email}' has not been verified."

    @property
    def detail(self) -> str:
        return "The email address has not been verified. Please confirm your email to proceed."


class InvalidCodeError(Exception):
    """Код верификации неверный."""
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, user_id: str, email: str, code: str):
        self.user_id = user_id
        self.email = email
        self.code = code
        super().__init__(self.user_id, self.email, self.code)

    def __str__(self) -> str:
        return (
            f"InvalidCodeError: The verification code '{self.code}' is invalid for "
            f"user_id='{self.user_id}' (email='{self.email}')."
        )

    @property
    def detail(self) -> str:
        return "The verification code is invalid."


class ExpiredCodeError(Exception):
    """Срок действия кода верификации истек."""
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, user_id: str, email: str, code: str):
        self.user_id = user_id
        self.email = email
        self.code = code
        super().__init__(self.user_id, self.email, self.code)

    def __str__(self) -> str:
        return (
            f"ExpiredCodeError: The verification code '{self.code}' has expired for "
            f"user_id='{self.user_id}' (email='{self.email}')."
        )

    @property
    def detail(self) -> str:
        return 'The verification code has expired.'


class UserInactiveError(Exception):
    """ПОльзователь не активен."""
    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, email: str):
        self.email = email
        super().__init__(self.email)

    def __str__(self) -> str:
        return f"UserInactiveError: The user with email '{self.email}' is inactive."

    @property
    def detail(self) -> str:
        return "The user is inactive. Access is denied."


class InvalidCredentialsError(Exception):
    """Неверные учетные данные для входа."""
    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        return "InvalidCredentialsError: The user failed the password verification procedure."

    @property
    def detail(self) -> str:
        return "Invalid email or password."


class SendOtpCodeError(Exception):
    """Пользователь уже ранее проходил процедуру регистрации."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, email: str):
        self.email = email
        super().__init__(self.email)

    def __str__(self) -> str:
        return f"SendOtpCodeError: Error sending verification code to the email address '{self.email}'."

    @property
    def detail(self) -> str:
        return f"An error occurred while sending the verification code to the email address: {self.email}."
