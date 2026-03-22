"""Convert unbounded String vacancy fields to Text

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-16 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ('vacancies', 'favorite_vacancies')

# Поля, которые переводятся из String(N) → Text.
# Порядок и nullable соответствуют BaseVacancy на момент миграции.
STRING_TO_TEXT_COLUMNS = [
    ('vacancy_name',    sa.String(length=300), False),
    ('employer_name',   sa.String(length=300), False),
    ('employer_phone',  sa.String(length=100), False),
    ('employer_email',  sa.String(length=300), True),
    ('contact_person',  sa.String(length=300), True),
    ('employment',      sa.String(length=200), True),
    ('work_format',     sa.String(length=300), True),
    ('category',        sa.String(length=100), False),
    ('social_protected',sa.String(length=300), True),
]


def upgrade() -> None:
    for table in TABLES:
        for column_name, old_type, nullable in STRING_TO_TEXT_COLUMNS:
            op.alter_column(
                table,
                column_name,
                type_=sa.Text(),
                existing_type=old_type,
                existing_nullable=nullable,
            )


def downgrade() -> None:
    for table in TABLES:
        for column_name, old_type, nullable in STRING_TO_TEXT_COLUMNS:
            op.alter_column(
                table,
                column_name,
                type_=old_type,
                existing_type=sa.Text(),
                existing_nullable=nullable,
            )
