"""Initial normalized schema for Smart Shopping Assistant

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-25 11:30:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])

    # 2. categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('product_type', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_categories_id', 'categories', ['id'])
    op.create_index('ix_categories_slug', 'categories', ['slug'])

    # 3. products table
    op.create_table(
        'products',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('barcode', sa.String(32), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('brand', sa.String(255), nullable=True),
        sa.Column('generic_name', sa.String(255), nullable=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('serving_size', sa.String(100), nullable=True),
        sa.Column('image_url', sa.String(1024), nullable=True),
        sa.Column('packaging', sa.String(100), nullable=True),
        sa.Column('origin_country', sa.String(100), nullable=True),
        sa.Column('nova_group', sa.SmallInteger(), nullable=True),
        sa.Column('nutri_score_grade', sa.String(2), nullable=True),
        sa.Column('data_completeness_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('data_source', sa.String(50), nullable=False, server_default='local_seed'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_products_id', 'products', ['id'])
    op.create_index('ix_products_barcode', 'products', ['barcode'])
    op.create_index('ix_products_name', 'products', ['name'])
    op.create_index('ix_products_brand', 'products', ['brand'])
    op.create_index('ix_products_category_id', 'products', ['category_id'])

    # 4. nutritional_information table
    op.create_table(
        'nutritional_information',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('energy_kcal', sa.Float(), nullable=True),
        sa.Column('energy_kj', sa.Float(), nullable=True),
        sa.Column('fat_g', sa.Float(), nullable=True),
        sa.Column('saturated_fat_g', sa.Float(), nullable=True),
        sa.Column('trans_fat_g', sa.Float(), nullable=True),
        sa.Column('carbohydrates_g', sa.Float(), nullable=True),
        sa.Column('sugars_g', sa.Float(), nullable=True),
        sa.Column('added_sugars_g', sa.Float(), nullable=True),
        sa.Column('fiber_g', sa.Float(), nullable=True),
        sa.Column('proteins_g', sa.Float(), nullable=True),
        sa.Column('sodium_mg', sa.Float(), nullable=True),
        sa.Column('salt_g', sa.Float(), nullable=True),
        sa.Column('fruits_vegetables_nuts_colza_walnut_olive_oils_pct', sa.Float(), nullable=True),
        sa.Column('basis', sa.String(20), nullable=False, server_default='per 100g'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_nutritional_information_id', 'nutritional_information', ['id'])
    op.create_index('ix_nutritional_information_product_id', 'nutritional_information', ['product_id'])

    # 5. ingredients table
    op.create_table(
        'ingredients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('canonical_name', sa.String(255), nullable=False, unique=True),
        sa.Column('ins_number', sa.String(20), nullable=True),
        sa.Column('is_additive', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('additive_type', sa.String(50), nullable=True),
        sa.Column('health_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_ingredients_id', 'ingredients', ['id'])
    op.create_index('ix_ingredients_canonical_name', 'ingredients', ['canonical_name'])
    op.create_index('ix_ingredients_ins_number', 'ingredients', ['ins_number'])

    # 6. product_ingredients table
    op.create_table(
        'product_ingredients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ingredient_id', sa.String(36), sa.ForeignKey('ingredients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('position_order', sa.Integer(), nullable=False),
        sa.Column('estimated_percentage', sa.Float(), nullable=True),
        sa.Column('is_whole_grain', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_allergen', sa.Boolean(), nullable=False, server_default='0'),
        sa.UniqueConstraint('product_id', 'ingredient_id', name='uq_product_ingredient')
    )
    op.create_index('ix_product_ingredients_id', 'product_ingredients', ['id'])
    op.create_index('ix_product_ingredients_product_id', 'product_ingredients', ['product_id'])
    op.create_index('ix_product_ingredients_ingredient_id', 'product_ingredients', ['ingredient_id'])

    # 7. scoring_criteria table
    op.create_table(
        'scoring_criteria',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=True),
        sa.Column('product_type', sa.String(20), nullable=False),
        sa.Column('parameter_name', sa.String(50), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('low_threshold', sa.Float(), nullable=False),
        sa.Column('medium_threshold', sa.Float(), nullable=False),
        sa.Column('high_threshold', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('polarity', sa.String(20), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_scoring_criteria_id', 'scoring_criteria', ['id'])
    op.create_index('ix_scoring_criteria_category_id', 'scoring_criteria', ['category_id'])

    # 8. product_scores table
    op.create_table(
        'product_scores',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('overall_project_score', sa.Float(), nullable=False),
        sa.Column('project_health_band', sa.String(30), nullable=False),
        sa.Column('official_nutri_score_grade', sa.String(2), nullable=False),
        sa.Column('official_nutri_score_points', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('sub_scores_json', sa.Text(), nullable=False),
        sa.Column('pros_json', sa.Text(), nullable=False),
        sa.Column('cons_json', sa.Text(), nullable=False),
        sa.Column('scoring_engine_version', sa.String(20), nullable=False, server_default='1.0.0'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_product_scores_id', 'product_scores', ['id'])
    op.create_index('ix_product_scores_product_id', 'product_scores', ['product_id'])

    # 9. recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('target_product_id', sa.String(36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alternative_product_id', sa.String(36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('score_improvement', sa.Float(), nullable=False),
        sa.Column('parameter_deltas_json', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_recommendations_id', 'recommendations', ['id'])
    op.create_index('ix_recommendations_target_product_id', 'recommendations', ['target_product_id'])
    op.create_index('ix_recommendations_alternative_product_id', 'recommendations', ['alternative_product_id'])

    # 10. search_history table
    op.create_table(
        'search_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('product_id', sa.String(36), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('query_term', sa.String(255), nullable=False),
        sa.Column('query_type', sa.String(50), nullable=False),
        sa.Column('searched_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_search_history_id', 'search_history', ['id'])
    op.create_index('ix_search_history_user_id', 'search_history', ['user_id'])
    op.create_index('ix_search_history_product_id', 'search_history', ['product_id'])

def downgrade() -> None:
    op.drop_table('search_history')
    op.drop_table('recommendations')
    op.drop_table('product_scores')
    op.drop_table('scoring_criteria')
    op.drop_table('product_ingredients')
    op.drop_table('ingredients')
    op.drop_table('nutritional_information')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('users')
