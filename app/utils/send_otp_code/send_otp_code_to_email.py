import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from core.settings import get_settings
from exceptions.users import SendOtpCodeError
from utils.send_otp_code.get_otp_code import generate_verified_code

settings = get_settings()
logger = logging.getLogger(__name__)


async def send_otp_code_by_email(
        user_name: str,
        user_email: str,
        message_template: str,
        subject: str,
        retries: int = 4,
        delay: int = 1
) -> str:
    """Функция отправки пользователю кода для идентификации."""
    logger.info("Отправка кода верификации на адрес: %s", user_email)
    verified_code = generate_verified_code()
    msg = MIMEMultipart()
    msg["From"] = settings.email.from_email.get_secret_value()
    msg["To"] = user_email
    msg["Subject"] = subject
    msg.attach(
        MIMEText(
            message_template.format(
                user_name=user_name,
                otp_code=verified_code
            ), "html"
        )
    )

    last_attempt = 0
    for attempt in range(1, retries):
        last_attempt = attempt
        try:
            logger.info("Попытка %s отправки письма на %s...", attempt, user_email)
            async with aiosmtplib.SMTP(
                hostname=settings.email.host_name.get_secret_value(),
                port=settings.email.port,
                use_tls=True
            ) as server:
                await server.login(
                    settings.email.from_email.get_secret_value(),
                    settings.email.application_key.get_secret_value()
                )
                await server.send_message(msg)
                return verified_code
        except ConnectionRefusedError:
            logger.exception("Попытка %s - не удалось подключиться к SMTP-серверу.", attempt)
        except aiosmtplib.SMTPException:
            logger.exception("Ошибка при отправке письма на попытке %s.", attempt)
        except Exception:
            logger.exception("Непредвиденная ошибка на попытке %s.", attempt)
        if attempt < retries:
            logger.info("Ожидание %s секунд перед следующей попыткой...", delay)
            await asyncio.sleep(delay)
    logger.error(
        "Не удалось отправить письмо на %s! Количество попыток: %s",
        user_email, last_attempt
    )
    raise SendOtpCodeError(email=user_email)
