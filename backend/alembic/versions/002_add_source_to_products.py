"""Add source column to products

Revision ID: 002_add_source_to_products
Revises: 001_initial_schema
Create Date: 2026-11-25 11:44:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_source_to_products'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add source column with server default 'seed'
    op.add_column(
        'products',
        sa.Column('source', sa.String(50), nullable=False, server_default='seed')
    )
    # Ensure any existing rows have 'seed'
    op.execute("UPDATE products SET source = 'seed' WHERE source IS NULL OR source = ''")

def downgrade() -> None:
    op.drop_column('products', 'source')
