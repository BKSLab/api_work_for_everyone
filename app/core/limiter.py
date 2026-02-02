"""
Модуль для создания и предоставления централизованного экземпляра Limiter.

Этот модуль решает проблему циклических импортов, возникающую, когда экземпляр
Limiter создается в `main.py`, а затем импортируется в модули с эндпоинтами,
которые, в свою очередь, импортируются в `main.py`.
"""
import os
from pathlib import Path

from slowapi import Limiter
from slowapi.util import get_remote_address

BASE_DIR = Path(__file__).resolve().parent.parent.parent
limiter = Limiter(
    key_func=get_remote_address,
    config_filename=os.path.join(BASE_DIR, ".env")
)
