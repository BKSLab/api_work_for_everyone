from pathlib import Path

from sqladmin import Admin

from .auth import MasterKeyAuth
from .views import ApiKeyAdmin, AssistantSessionAdmin, FavoritesAdmin, SearchEventAdmin

_TEMPLATES_DIR = str(Path(__file__).parent.parent / "templates")


def create_admin(app, engine) -> Admin:
    from core.settings import get_settings
    settings = get_settings()

    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=MasterKeyAuth(
            secret_key=settings.app.secret_key.get_secret_value()
        ),
        title="Работа для всех — Admin",
        base_url="/admin",
        templates_dir=_TEMPLATES_DIR,
    )
    admin.add_view(ApiKeyAdmin)
    admin.add_view(FavoritesAdmin)
    admin.add_view(AssistantSessionAdmin)
    admin.add_view(SearchEventAdmin)
    return admin
