"""Add favorite_events table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-29 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'favorite_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.String(300), nullable=False),
        sa.Column('vacancy_id', sa.String(300), nullable=False),
        sa.Column('action', sa.String(10), nullable=False),
        sa.Column('vacancy_name', sa.Text(), nullable=True),
        sa.Column('employer_name', sa.Text(), nullable=True),
        sa.Column('vacancy_source', sa.String(100), nullable=True),
        sa.Column('location', sa.String(300), nullable=True),
        sa.Column('category', sa.Text(), nullable=True),
        sa.Column('salary', sa.String(300), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_favorite_events_user_id', 'favorite_events', ['user_id'])
    op.create_index('ix_favorite_events_vacancy_id', 'favorite_events', ['vacancy_id'])
    op.create_index('ix_favorite_events_vacancy_source', 'favorite_events', ['vacancy_source'])


def downgrade() -> None:
    op.drop_index('ix_favorite_events_vacancy_source', table_name='favorite_events')
    op.drop_index('ix_favorite_events_vacancy_id', table_name='favorite_events')
    op.drop_index('ix_favorite_events_user_id', table_name='favorite_events')
    op.drop_table('favorite_events')
