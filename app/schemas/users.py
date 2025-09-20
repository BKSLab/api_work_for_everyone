from pydantic import BaseModel, EmailStr


class UserRegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class EmailVerifySchema(BaseModel):
    email: EmailStr
    code: str


class TokenResponseSchema(BaseModel):
    """
    Модель ответа при успешной аутентификации/подтверждении почты.
    """
    access_token: str
    token_type: str = 'bearer'
    refresh_token: str


class MsgSchema(BaseModel):
    msg: str
