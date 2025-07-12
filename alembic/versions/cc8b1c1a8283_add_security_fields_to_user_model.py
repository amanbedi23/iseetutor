"""Add security fields to user model

Revision ID: cc8b1c1a8283
Revises: 2b30362a0e69
Create Date: 2025-07-12 18:34:17.157366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc8b1c1a8283'
down_revision: Union[str, None] = '2b30362a0e69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add security-related columns to users table
    op.add_column('users', sa.Column('hashed_password', sa.String(200), nullable=True))
    op.add_column('users', sa.Column('parent_email', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('metadata', sa.JSON(), nullable=True))
    
    # Make hashed_password not nullable after adding default value
    op.execute("UPDATE users SET hashed_password = '$2b$12$dummy.hash.for.existing.users' WHERE hashed_password IS NULL")
    op.alter_column('users', 'hashed_password', nullable=False)
    
    # Set default metadata
    op.execute("UPDATE users SET metadata = '{}' WHERE metadata IS NULL")


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('users', 'metadata')
    op.drop_column('users', 'parent_email')
    op.drop_column('users', 'hashed_password')
