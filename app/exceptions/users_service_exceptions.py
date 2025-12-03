from fastapi import status


class UserAlreadyExists(Exception):
    """Пользователь уже ранее проходил процедуру регистрации."""
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return (
            "Попытка регистрации пользователя, который уже существует и "
            f"прошел процедуру верификации почты: {self.message}"
        )

    def detail(self) -> str:
        return "User is already registered."


class UserAlreadyVerified(Exception):
    """Пользователь уже ранее проходил процедуру верификации."""
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"Пользователь прошел уже процедуру верификации email: {self.message}"

    def detail(self) -> str:
        return (
            "The user has already completed the verification procedure."
        )


class UserNotFound(Exception):
    """Пользователь не найден."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def detail(self) -> str:
        return (
            'A user with this email does not exist.'
        )


class InvalidCodeError(Exception):
    """Код верификации неверный."""
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def detail(self) -> str:
        return 'The verification code is invalid.'


class ExpiredCodeError(Exception):
    """Срок действия кода верификации истек."""
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def detail(self) -> str:
        return 'The verification code has expired.'


class EmailNotVerifiedError(Exception):
    """Адрес почты не подтверждён."""
    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def detail(self) -> str:
        return 'The email address has not been verified. Please confirm your email to proceed.'


class UserInactiveError(Exception):
    """ПОльзователь не активен."""
    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def detail(self) -> str:
        return 'The user is inactive, may have been blocked or failed the verification procedure..'


class InvalidCredentialsError(Exception):
    """Неверные учетные данные для входа."""
    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def detail(self) -> str:
        return "Invalid email or password."


class UsersServiceError(Exception):
    """Общий класс исключений для сервиса работы с пользователями."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def detail(self) -> str:
        return (
            "An unexpected error occurred while processing the user registration request. "
            f"Error Details: {self.message}. Please try again later or contact support."
        )


class BlocklistServiceError(Exception):
    """Класс исключений для сервиса работы с черным списком токенов."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message
    
    def detail(self) -> str:
        return (f"Error adding token to token blacklist. Error Details: {self.message}.")
