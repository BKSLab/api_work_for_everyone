"""Add updated_at to vacancies

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-03-29 13:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'vacancies',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        )
    )
    op.create_index('ix_vacancies_location_updated_at', 'vacancies', ['location', 'updated_at'])


def downgrade() -> None:
    op.drop_index('ix_vacancies_location_updated_at', table_name='vacancies')
    op.drop_column('vacancies', 'updated_at')
