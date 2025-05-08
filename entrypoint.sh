#!/bin/bash

set -e

echo "application of migrations"
alembic upgrade head

echo "Starting in production mode..."
exec hypercorn app.main:app --bind 0.0.0.0:8000 --workers 1