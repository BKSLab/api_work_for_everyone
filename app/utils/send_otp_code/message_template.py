VERIFICATION_MESSAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ваш код подтверждения</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            font-size: 16px;
            line-height: 1.6;
        }}
        .container {{
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 1px solid #dddddd;
        }}
        .header h1 {{
            margin: 0;
            color: #333333;
        }}
        .content {{
            padding: 20px 0;
            text-align: center;
        }}
        .content p {{
            color: #555555;
        }}
        .otp-code {{
            display: inline-block;
            background-color: #FFC300; /* Updated color */
            color: #000000; /* Updated color */
            padding: 15px 25px;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 3px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #dddddd;
            font-size: 14px;
            color: #999999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/i/TMB4jLy0GOHwgQ" alt="Логотип Работа для всех" style="width: 150px; margin: auto;">
        </div>
        <div class="content">
            <p>Здравствуйте, <strong>{user_name}</strong>!</p>
            <p>Спасибо за регистрацию на нашем портале. Для завершения идентификации, пожалуйста, используйте следующий код:</p>
            <div class="otp-code">{otp_code}</div>
            <p>Этот код действителен в течение 10 минут.</p>
        </div>
        <div class="footer">
            <p>Вы получили это письмо, так как регистрируетесь на сайте "Работа для всех" - поиск вакансий для людей с инвалидностью в России.</p>
            <p>&copy; 2025 Работа для всех. Все права защищены.</p>
        </div>
    </div>
</body>
</html>
"""

PASSWORD_RESET_MESSAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ваш код для сброса пароля</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            font-size: 16px;
            line-height: 1.6;
        }}
        .container {{
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 1px solid #dddddd;
        }}
        .header h1 {{
            margin: 0;
            color: #333333;
        }}
        .content {{
            padding: 20px 0;
            text-align: center;
        }}
        .content p {{
            color: #555555;
        }}
        .otp-code {{
            display: inline-block;
            background-color: #FFC300; /* Updated color */
            color: #000000; /* Updated color */
            padding: 15px 25px;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 3px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #dddddd;
            font-size: 14px;
            color: #999999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/i/TMB4jLy0GOHwgQ" alt="Логотип Работа для всех" style="width: 150px; margin: auto;">
        </div>
        <div class="content">
            <p>Здравствуйте, <strong>{user_name}</strong>!</p>
            <p>Для сброса пароля на портале "Работа для всех", пожалуйста, используйте следующий код:</p>
            <div class="otp-code">{otp_code}</div>
            <p>Этот код действителен в течение 10 минут.</p>
        </div>
        <div class="footer">
            <p>Вы получили это письмо, так как запросили сброс пароля на сайте "Работа для всех" - поиск вакансий для людей с инвалидностью в России.</p>
            <p>&copy; 2025 Работа для всех. Все права защищены.</p>
        </div>
    </div>
</body>
</html>
"""
