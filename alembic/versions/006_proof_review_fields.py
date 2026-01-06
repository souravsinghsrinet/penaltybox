"""Add proof review fields

Revision ID: 006_proof_review_fields
Revises: 005_background_tasks
Create Date: 2026-01-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '006_proof_review_fields'
down_revision = '005_background_tasks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get connection and inspector
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check if columns already exist (for idempotency)
    columns = [col['name'] for col in inspector.get_columns('proofs')]
    
    # Add status column if it doesn't exist
    if 'status' not in columns:
        conn.execute(text("ALTER TABLE proofs ADD COLUMN status VARCHAR DEFAULT 'PENDING'"))
    
    # Add reviewed_by column if it doesn't exist
    if 'reviewed_by' not in columns:
        conn.execute(text("ALTER TABLE proofs ADD COLUMN reviewed_by INTEGER REFERENCES users(id)"))
    
    # Add reviewed_at column if it doesn't exist
    if 'reviewed_at' not in columns:
        conn.execute(text("ALTER TABLE proofs ADD COLUMN reviewed_at TIMESTAMP"))
    
    # Add admin_note column if it doesn't exist
    if 'admin_note' not in columns:
        conn.execute(text("ALTER TABLE proofs ADD COLUMN admin_note VARCHAR"))
    
    # Create index on status for faster queries
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_proofs_status ON proofs(status)"))


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_proofs_status', table_name='proofs', if_exists=True)
    
    # Drop columns
    op.drop_column('proofs', 'admin_note', if_exists=True)
    op.drop_column('proofs', 'reviewed_at', if_exists=True)
    op.drop_column('proofs', 'reviewed_by', if_exists=True)
    op.drop_column('proofs', 'status', if_exists=True)
