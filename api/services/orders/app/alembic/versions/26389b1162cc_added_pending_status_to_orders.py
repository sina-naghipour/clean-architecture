"""added pending status to orders

Revision ID: 26389b1162cc
Revises: 3002a8eb7c69
Create Date: 2025-12-18 21:17:22.039634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26389b1162cc'
down_revision: Union[str, Sequence[str], None] = '3002a8eb7c69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add 'pending' to the OrderStatus enum
    op.execute("ALTER TYPE orderstatus ADD VALUE 'PENDING'")
    

def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't easily allow removing enum values
    # You would need to create a new type without 'pending' and migrate data
    pass