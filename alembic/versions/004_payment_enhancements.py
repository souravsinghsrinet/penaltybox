"""Add payment enhancements and penalty_payments table

Revision ID: 004_payment_enhancements
Revises: 003
Create Date: 2026-01-05

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '004_payment_enhancements'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to payments table
    op.add_column('payments', sa.Column('payment_method', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('reference_id', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('approved_by_admin_id', sa.Integer(), nullable=True))
    op.add_column('payments', sa.Column('notes', sa.String(), nullable=True))
    
    # Add foreign key for approved_by_admin_id
    op.create_foreign_key(
        'fk_payments_approved_by_admin_id',
        'payments', 'users',
        ['approved_by_admin_id'], ['id']
    )
    
    # Set default value for existing records
    op.execute("UPDATE payments SET payment_method = 'CASH' WHERE payment_method IS NULL")
    
    # Now make payment_method NOT NULL with default
    op.alter_column('payments', 'payment_method', nullable=False, server_default='CASH')
    
    # Create penalty_payments junction table
    op.create_table(
        'penalty_payments',
        sa.Column('penalty_id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['penalty_id'], ['penalties.id'], ),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
        sa.PrimaryKeyConstraint('penalty_id', 'payment_id')
    )


def downgrade():
    # Drop penalty_payments table
    op.drop_table('penalty_payments')
    
    # Drop foreign key
    op.drop_constraint('fk_payments_approved_by_admin_id', 'payments', type_='foreignkey')
    
    # Drop new columns from payments table
    op.drop_column('payments', 'notes')
    op.drop_column('payments', 'approved_by_admin_id')
    op.drop_column('payments', 'reference_id')
    op.drop_column('payments', 'payment_method')
