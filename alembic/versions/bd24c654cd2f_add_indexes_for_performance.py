"""Add indexes for performance

Revision ID: bd24c654cd2f
Revises: 16e1734856ff
Create Date: 2025-12-07 17:38:01.577917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd24c654cd2f'
down_revision: Union[str, Sequence[str], None] = '16e1734856ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add indexes for better query performance on frequently accessed columns
    op.create_index('idx_sync_queue_category_synced', 'sync_queue', ['category', 'synced'])
    op.create_index('idx_conflicts_resolved', 'conflicts', ['resolved'])
    op.create_index('idx_conversations_synced', 'conversations', ['synced', 'deleted'])
    op.create_index('idx_automations_enabled', 'automations', ['enabled'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove indexes
    op.drop_index('idx_automations_enabled', 'automations')
    op.drop_index('idx_conversations_synced', 'conversations')
    op.drop_index('idx_conflicts_resolved', 'conflicts')
    op.drop_index('idx_sync_queue_category_synced', 'sync_queue')
