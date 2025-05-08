from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.settings import get_settings

settings = get_settings()

engine = create_async_engine(url=settings.db.url_connect)

async_session_factory = async_sessionmaker(
    engine, expire_on_commit=False
)