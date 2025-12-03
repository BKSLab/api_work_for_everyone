import math
import random


def generate_verified_code() -> str:
    """Генерация OTP кода для отправки пользователю на email."""
    using_string = '0123456789abcdefghijklmnopqrstuvwxyz'
    verified_code = ''
    length_using_string = len(using_string)
    for _ in range(6):
        verified_code += using_string[
            math.floor(random.random() * length_using_string)
        ]
    return verified_code
