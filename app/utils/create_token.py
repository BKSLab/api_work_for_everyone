from dependencies.jwt import JWTManagerDep
from schemas.users import TokenResponseSchema


async def create_token_pair(
    jwt_manager: JWTManagerDep,
    user_email: str,
    username: str
) -> TokenResponseSchema:
    """Вспомогательная функция для генерации пары токенов, access и refresh."""
    payload = {"sub": user_email, "username": username}
    access_token = jwt_manager.create_access_token(payload=payload)
    refresh_token = jwt_manager.create_refresh_token(payload=payload)
    return TokenResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token
    )
