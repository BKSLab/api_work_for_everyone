import logging
import logging.config

from core.settings import get_settings

settings = get_settings()

logging.config.fileConfig(fname=settings.app.logging_config_path, disable_existing_loggers=False)

# Получаем логгер, указанный в файле
logger = logging.getLogger('api_work_for_everyone')
