"""phase2: scrape_jobs table and item columns

Revision ID: a1b2c3d4e5f6
Revises: eda7d389f586
Create Date: 2026-02-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'eda7d389f586'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scrape_jobs table
    op.create_table(
        'scrape_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('brand_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('items_found', sa.Integer(), nullable=True),
        sa.Column('items_stored', sa.Integer(), nullable=True),
        sa.Column('items_flagged', sa.Integer(), nullable=True),
        sa.Column('errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('flags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Add Phase 2 columns to items table
    op.add_column('items', sa.Column('external_id', sa.String(length=255), nullable=True))
    op.add_column('items', sa.Column('handle', sa.String(length=255), nullable=True))
    op.add_column('items', sa.Column('vendor', sa.String(length=255), nullable=True))
    op.add_column('items', sa.Column('product_type_raw', sa.String(length=255), nullable=True))
    op.add_column('items', sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('items', sa.Column('colors', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('items', sa.Column('body_html_raw', sa.Text(), nullable=True))
    op.add_column('items', sa.Column('season_code', sa.String(length=20), nullable=True))
    op.add_column('items', sa.Column('sku', sa.String(length=100), nullable=True))
    op.add_column('items', sa.Column('in_stock', sa.Boolean(), nullable=True))
    op.add_column('items', sa.Column('compare_at_price_usd', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('items', sa.Column('shopify_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('items', sa.Column('updated_at', sa.DateTime(), nullable=True))

    op.create_index('ix_items_external_id', 'items', ['external_id'], unique=False)
    op.create_index('ix_items_brand_external', 'items', ['brand_id', 'external_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_items_brand_external', table_name='items')
    op.drop_index('ix_items_external_id', table_name='items')

    op.drop_column('items', 'updated_at')
    op.drop_column('items', 'shopify_data')
    op.drop_column('items', 'compare_at_price_usd')
    op.drop_column('items', 'in_stock')
    op.drop_column('items', 'sku')
    op.drop_column('items', 'season_code')
    op.drop_column('items', 'body_html_raw')
    op.drop_column('items', 'colors')
    op.drop_column('items', 'tags')
    op.drop_column('items', 'product_type_raw')
    op.drop_column('items', 'vendor')
    op.drop_column('items', 'handle')
    op.drop_column('items', 'external_id')

    op.drop_table('scrape_jobs')
