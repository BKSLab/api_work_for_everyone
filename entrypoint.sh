#!/bin/bash

set -e

# Добавляем в PYTHONPATH и корневую директорию проекта (/app),
# и директорию с исходным кодом (/app/app).
# Это позволяет и команде запуска найти app.main, и самому приложению
# найти свои внутренние модули (api, core и т.д.).
export PYTHONPATH="/app:/app/app:${PYTHONPATH}"

echo "application of migrations"
alembic upgrade head

echo "Starting in production mode..."
exec hypercorn app.main:app --bind 0.0.0.0:8000 --workers 1