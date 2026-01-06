"""Add background_tasks table for logging async operations

Revision ID: 005_background_tasks
Revises: 004_payment_enhancements
Create Date: 2026-01-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_background_tasks'
down_revision = '004_payment_enhancements'
branch_labels = None
depends_on = None


def upgrade():
    # Get database connection
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Create ENUM type if it doesn't exist (handles both fresh and existing databases)
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE taskstatus AS ENUM ('STARTED', 'COMPLETED', 'FAILED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Create table if it doesn't exist
    if 'background_tasks' not in inspector.get_table_names():
        # Create table with VARCHAR for status column first
        conn.execute(sa.text("""
            CREATE TABLE background_tasks (
                id SERIAL PRIMARY KEY,
                task_id VARCHAR UNIQUE NOT NULL,
                task_type VARCHAR NOT NULL,
                proof_id INTEGER REFERENCES proofs(id),
                status VARCHAR NOT NULL DEFAULT 'STARTED',
                error TEXT,
                started_at TIMESTAMP NOT NULL DEFAULT NOW(),
                ended_at TIMESTAMP,
                task_metadata JSON
            )
        """))
        
        # Drop the default temporarily to allow type change
        conn.execute(sa.text("ALTER TABLE background_tasks ALTER COLUMN status DROP DEFAULT"))
        
        # Now alter the status column to use the ENUM type
        conn.execute(sa.text("""
            ALTER TABLE background_tasks 
            ALTER COLUMN status TYPE taskstatus 
            USING status::taskstatus
        """))
        
        # Re-add the default with ENUM type
        conn.execute(sa.text("ALTER TABLE background_tasks ALTER COLUMN status SET DEFAULT 'STARTED'::taskstatus"))
        
        # Create indexes
        conn.execute(sa.text("CREATE INDEX idx_background_tasks_task_id ON background_tasks(task_id)"))
        conn.execute(sa.text("CREATE INDEX idx_background_tasks_proof_id ON background_tasks(proof_id)"))
        conn.execute(sa.text("CREATE INDEX idx_background_tasks_status ON background_tasks(status)"))


def downgrade():
    # Drop table and indexes if they exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'background_tasks' in inspector.get_table_names():
        conn.execute(sa.text("DROP TABLE IF EXISTS background_tasks CASCADE"))
    
    # Drop ENUM type
    conn.execute(sa.text("DROP TYPE IF EXISTS taskstatus CASCADE"))
