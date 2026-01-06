"""Add background_tasks table for logging async operations

Revision ID: 005_background_tasks
Revises: 004_payment_enhancements
Create Date: 2026-01-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision = '005_background_tasks'
down_revision = '004_payment_enhancements'
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM type for task status (will skip if exists)
    task_status_enum = ENUM('STARTED', 'COMPLETED', 'FAILED', name='taskstatus', create_type=False)
    
    # Check if table already exists to avoid errors on re-run
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'background_tasks' not in inspector.get_table_names():
        # Create background_tasks table
        op.create_table(
            'background_tasks',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('task_id', sa.String(), unique=True, nullable=False, index=True),
            sa.Column('task_type', sa.String(), nullable=False),  # 'image_processing', 'cleanup', etc.
            sa.Column('proof_id', sa.Integer(), sa.ForeignKey('proofs.id'), nullable=True),
            sa.Column('status', task_status_enum, nullable=False, server_default='STARTED'),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('ended_at', sa.DateTime(), nullable=True),
            sa.Column('task_metadata', sa.JSON(), nullable=True),  # Renamed from 'metadata' to avoid conflict
        )
        
        # Create index on proof_id for faster lookups
        op.create_index('idx_background_tasks_proof_id', 'background_tasks', ['proof_id'])
        
        # Create index on status for filtering pending tasks
        op.create_index('idx_background_tasks_status', 'background_tasks', ['status'])


def downgrade():
    op.drop_index('idx_background_tasks_status', 'background_tasks')
    op.drop_index('idx_background_tasks_proof_id', 'background_tasks')
    op.drop_table('background_tasks')
    
    # Drop ENUM type
    task_status_enum = ENUM('STARTED', 'COMPLETED', 'FAILED', name='taskstatus', create_type=False)
    task_status_enum.drop(op.get_bind(), checkfirst=True)
