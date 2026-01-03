"""Add is_admin column to users table

Revision ID: 002_add_is_admin
Revises: 001
Create Date: 2026-01-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_is_admin'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_admin column to users table with default value False
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    # Remove is_admin column from users table
    op.drop_column('users', 'is_admin')
