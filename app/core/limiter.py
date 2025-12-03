"""
Модуль для создания и предоставления централизованного экземпляра Limiter.

Этот модуль решает проблему циклических импортов, возникающую, когда экземпляр
Limiter создается в `main.py`, а затем импортируется в модули с эндпоинтами,
которые, в свою очередь, импортируются в `main.py`.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
