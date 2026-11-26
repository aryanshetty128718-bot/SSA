"""Add product_category_tags table

Revision ID: 003_add_product_category_tags
Revises: 002_add_source_to_products
Create Date: 2026-11-25 12:05:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_add_product_category_tags'
down_revision: Union[str, None] = '002_add_source_to_products'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'product_category_tags',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tag', sa.String(255), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('product_id', 'tag', name='uq_product_category_tag')
    )
    op.create_index('ix_product_category_tags_id', 'product_category_tags', ['id'])
    op.create_index('ix_product_category_tags_product_id', 'product_category_tags', ['product_id'])
    op.create_index('ix_product_category_tags_tag', 'product_category_tags', ['tag'])

def downgrade() -> None:
    op.drop_table('product_category_tags')
