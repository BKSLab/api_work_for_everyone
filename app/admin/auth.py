from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import Response

from core.settings import get_settings

settings = get_settings()


class MasterKeyAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")
        if (
            username == settings.app.admin_login
            and password == settings.app.admin_password.get_secret_value()
        ):
            request.session["admin_authenticated"] = True
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin_authenticated", False)
