"""add role to users

Revision ID: af4769e2e9a0
Revises: d52dc77a7238
Create Date: 2025-12-14 14:35:46.069764
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "af4769e2e9a0"
down_revision: Union[str, Sequence[str], None] = "d52dc77a7238"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# define enum explicitly
userrole_enum = postgresql.ENUM(
    "admin",
    "user",
    name="userrole"
)

def upgrade() -> None:
    # create enum type first
    userrole_enum.create(op.get_bind(), checkfirst=True)

    # add column using the enum
    op.add_column(
        "users",
        sa.Column(
            "role",
            userrole_enum,
            nullable=False,
            server_default="user",
        ),
    )

def downgrade() -> None:
    # remove column first
    op.drop_column("users", "role")

    # drop the enum type
    userrole_enum.drop(op.get_bind(), checkfirst=True)
