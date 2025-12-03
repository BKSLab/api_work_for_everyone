from pydantic import BaseModel, EmailStr, Field


class UserRegisterSchema(BaseModel):
    """Схема для данных регистрации нового пользователя."""
    username: str = Field(..., min_length=4, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)


class UserLoginSchema(BaseModel):
    """Схема для данных аутентификации пользователя."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)


class EmailVerifySchema(BaseModel):
    """Схема для подтверждения электронной почты пользователя."""
    email: EmailStr
    code: str


class ForgotPasswordRequestSchema(BaseModel):
    """Схема для запроса сброса пароля по email."""
    email: EmailStr


class ResetPasswordRequestSchema(BaseModel):
    """Схема для сброса пароля с использованием кода."""
    email: EmailStr
    code: str
    new_password: str = Field(..., min_length=8, max_length=255)


class RefreshTokenRequestSchema(BaseModel):
    """Схема для запроса обновления токена доступа."""
    refresh_token: str


class EmailOnlySchema(BaseModel):
    """Схема, содержащая только адрес электронной почты."""
    email: EmailStr


class TokenResponseSchema(BaseModel):
    """Схема ответа при успешной аутентификации/подтверждении почты."""
    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class MsgSchema(BaseModel):
    """Универсальная схема для сообщений об успешном выполнении или ошибке."""
    msg: str
