"""many to many groups

Revision ID: 003
Revises: 002
Create Date: 2026-01-04

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002_add_is_admin'
branch_labels = None
depends_on = None


def upgrade():
    # Create the user_groups association table
    op.create_table(
        'user_groups',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id'), primary_key=True),
        sa.Column('role', sa.String(), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Add description column to groups table
    op.add_column('groups', sa.Column('description', sa.String(), nullable=True))
    
    # Migrate existing data from users.group_id to user_groups table
    # Users with group_id set will be added as members
    connection = op.get_bind()
    
    # Get all users with group_id
    result = connection.execute(sa.text("SELECT id, group_id FROM users WHERE group_id IS NOT NULL"))
    users_with_groups = result.fetchall()
    
    # Insert into user_groups table
    for user_id, group_id in users_with_groups:
        connection.execute(
            sa.text("INSERT INTO user_groups (user_id, group_id, role, joined_at) VALUES (:user_id, :group_id, 'member', :joined_at)"),
            {"user_id": user_id, "group_id": group_id, "joined_at": datetime.utcnow()}
        )
    
    # Drop the group_id column from users table
    op.drop_column('users', 'group_id')


def downgrade():
    # Add back the group_id column to users table
    op.add_column('users', sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id'), nullable=True))
    
    # Migrate data back from user_groups to users.group_id
    # Note: This will only keep the first group for each user
    connection = op.get_bind()
    
    result = connection.execute(sa.text("SELECT DISTINCT user_id, group_id FROM user_groups"))
    user_groups_data = result.fetchall()
    
    for user_id, group_id in user_groups_data:
        connection.execute(
            sa.text("UPDATE users SET group_id = :group_id WHERE id = :user_id"),
            {"user_id": user_id, "group_id": group_id}
        )
    
    # Drop the user_groups table
    op.drop_table('user_groups')
    
    # Remove description column from groups table
    op.drop_column('groups', 'description')
