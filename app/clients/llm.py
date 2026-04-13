import asyncio
import json
import random
from collections.abc import Callable
from pprint import pprint
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from core.config_logger import logger
from exceptions.llm import (
    LlmApiRequestError,
    LlmClientContentError,
    LlmClientRequestError,
)

PydanticModel = TypeVar("PydanticModel", bound=BaseModel)


class LlmClient:
    """Клиент для работы с OpenAI-совместимыми LLM API."""

    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        model: str,
        url: str,
        headers: dict,
        temperature: float = 0.3,
        stream: bool = False,
    ):
        self.httpx_client = httpx_client
        self.model = model
        self.url = url
        self.headers = headers
        self.temperature = temperature
        self.stream = stream
        self.timeout: int = 90
        self.delay: float = 1.0
        self.max_delay: float = 30.0
        self.retries: int = 3                                                                

    def _get_backoff_delay(self, attempt: int) -> float:
        """Вычисляет задержку по экспоненциальному алгоритму с джиттером.

        Attempt 1 → ~1s, attempt 2 → ~2s, attempt 3 → ~4s (до max_delay).
        Джиттер ±10% предотвращает одновременные повторы нескольких клиентов.
        """
        delay = min(self.max_delay, self.delay * (2 ** (attempt - 1)))
        return delay + delay * 0.1 * random.random()

    async def _send_request_to_llm(self, payload: dict) -> dict:
        """Отправляет один запрос к LLM и возвращает сырой ответ."""
        data_json = json.dumps(payload, ensure_ascii=False)
        try:
            logger.info("📤 Отправка запроса к LLM, модель: %s", payload.get('model'))
            response = await self.httpx_client.post(
                url=self.url,
                headers=self.headers,
                data=data_json,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            logger.error(
                "🌐 HTTP %s от LLM: %s", error.response.status_code, error.response.text
            )
            raise LlmClientRequestError(
                f"HTTP {error.response.status_code}"
            ) from error
        except httpx.TimeoutException as error:
            logger.error("⏱️ Таймаут при запросе к LLM (%ss): %s", self.timeout, error)
            raise LlmClientRequestError("Таймаут запроса к LLM") from error
        except httpx.RequestError as error:
            logger.error(
                "🌐 Сетевая ошибка при запросе к LLM: %s: %s", type(error).__name__, error
            )
            raise LlmClientRequestError(
                f"Сетевая ошибка: {type(error).__name__}"
            ) from error
        except Exception as error:
            logger.error(
                "❌ Неожиданная ошибка при запросе к LLM: %s: %s", type(error).__name__, error
            )
            raise LlmClientRequestError(
                f"Неожиданная ошибка: {type(error).__name__}"
            ) from error

    def _extract_content(self, response: dict) -> str:
        """Извлекает и валидирует текстовый контент из ответа LLM."""
        try:
            pprint(response)
            content = response.get("choices")[0].get("message").get("content")
        except (KeyError, IndexError, TypeError) as error:
            raise LlmClientContentError(
                f"Невалидная структура ответа LLM: {type(error).__name__}"
            ) from error

        if not content or not content.strip():
            raise LlmClientContentError("LLM вернул пустой ответ")

        return content

    def _extract_validated(self, response: dict, schema: type[PydanticModel]) -> PydanticModel:
        """Извлекает контент из ответа LLM и валидирует его по Pydantic-схеме."""
        content = self._extract_content(response)
        try:
            return schema.model_validate_json(content)
        except ValidationError as error:
            logger.warning(
                "📋 Ответ LLM не прошёл валидацию схемы %s: %s", schema.__name__, error
            )
            raise LlmClientContentError(
                f"Ответ не соответствует схеме {schema.__name__}"
            ) from error

    async def _fetch_with_retries(
        self, payload: dict, extractor: Callable[[dict], Any] | None = None
    ) -> Any:
        """Выполняет запрос к LLM с экспоненциальными повторами при любых ошибках."""
        extractor = extractor or self._extract_content
        last_error: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                response = await self._send_request_to_llm(payload)
                content = extractor(response)
                if attempt > 1:
                    logger.info("✅ Ответ от LLM получен с %s-й попытки", attempt)
                return content
            except LlmClientContentError as error:
                last_error = error
                logger.warning(
                    "📭 Некорректный контент от LLM (попытка %d/%d): %s",
                    attempt, self.retries, error
                )
            except LlmClientRequestError as error:
                last_error = error
                logger.warning(
                    "⚠️ Ошибка запроса к LLM (попытка %d/%d): %s",
                    attempt, self.retries, error
                )

            if attempt < self.retries:
                delay = self._get_backoff_delay(attempt)
                logger.info(
                    "🔄 Повтор через %.1fс (следующая попытка: %d/%d)",
                    delay, attempt + 1, self.retries
                )
                await asyncio.sleep(delay)

        logger.error(
            "❌ Не удалось получить ответ от LLM после %d попыток. Последняя ошибка: %s",
            self.retries, last_error
        )
        raise LlmApiRequestError(
            error_details=str(last_error),
            request_url=self.url,
        )

    async def get_llm_response(
        self,
        content: str,
        prompt: str,
        model: str | None = None,
        schema: type[PydanticModel] | None = None,
        max_completion_tokens: int = 6000,
    ) -> str | PydanticModel:
        """Получает ответ от LLM.

        schema — валидирует ответ по Pydantic-схеме, автоматически включает json_mode.
        max_completion_tokens — лимит токенов ответа (по умолчанию 6000).
        """
        payload = {
            "model": model if model else self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": content},
            ],
            "temperature": self.temperature,
            "max_completion_tokens": max_completion_tokens,
            "stream": self.stream,
            "reasoning": {
                "effort": "high",
                # "max_tokens": 1000,
                "summary": "detailed",
                "enabled": True,
                "exclude": False
            }
        }
        # if schema:
        #     payload["response_format"] = {"type": "json_object"}
        if schema:
            extractor = lambda response: self._extract_validated(response, schema)
        else:
            extractor = self._extract_content
        return await self._fetch_with_retries(payload, extractor=extractor)
