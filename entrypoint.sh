# Указываем путь к src, чтобы Python правильно искал модули
export PYTHONPATH=/app/src

# Создаем БД перед запуском приложения
python -m src.db.create_db

python -m src.main