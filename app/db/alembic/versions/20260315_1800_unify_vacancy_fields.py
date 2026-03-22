"""Unify vacancy fields across vacancies and favorite_vacancies tables

Revision ID: a1b2c3d4e5f6
Revises: 283658b8f59a
Create Date: 2026-03-15 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '283658b8f59a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ('vacancies', 'favorite_vacancies')


def upgrade() -> None:
    for table in TABLES:
        # Переименование существующих колонок
        op.alter_column(table, 'name', new_column_name='vacancy_name')
        op.alter_column(table, 'employment_type', new_column_name='employment',
                        existing_type=sa.String(length=200), existing_nullable=False)

        # Новые nullable-колонки
        op.add_column(table, sa.Column('status', sa.String(length=50), nullable=True,
                                       comment='Статус вакансии (actual, archival, not_found)'))
        op.add_column(table, sa.Column('employer_email', sa.String(length=300), nullable=True,
                                       comment='Контактный email работодателя'))
        op.add_column(table, sa.Column('contact_person', sa.String(length=300), nullable=True,
                                       comment='ФИО контактного лица работодателя'))
        op.add_column(table, sa.Column('work_format', sa.String(length=300), nullable=True,
                                       comment='Формат выполнения работы'))
        op.add_column(table, sa.Column('requirements', sa.Text(), nullable=True,
                                       comment='Конкретные требования к кандидату'))
        op.add_column(table, sa.Column('social_protected', sa.String(length=300), nullable=True,
                                       comment='Признак вакансии для социально защищённых категорий'))


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, 'social_protected')
        op.drop_column(table, 'requirements')
        op.drop_column(table, 'work_format')
        op.drop_column(table, 'contact_person')
        op.drop_column(table, 'employer_email')
        op.drop_column(table, 'status')

        op.alter_column(table, 'employment', new_column_name='employment_type',
                        existing_type=sa.String(length=200), existing_nullable=False)
        op.alter_column(table, 'vacancy_name', new_column_name='name')
