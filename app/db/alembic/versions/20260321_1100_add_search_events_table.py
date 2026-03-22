"""Add search_events table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-21 11:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'search_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('location', sa.String(300), nullable=False),
        sa.Column('region_name', sa.String(300), nullable=False),
        sa.Column('region_code', sa.String(20), nullable=False),
        sa.Column('count_hh', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('count_tv', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_hh', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_tv', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_search_events_location', 'search_events', ['location'])


def downgrade() -> None:
    op.drop_index('ix_search_events_location', table_name='search_events')
    op.drop_table('search_events')
