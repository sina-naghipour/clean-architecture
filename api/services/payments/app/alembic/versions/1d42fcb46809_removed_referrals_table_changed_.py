"""removed referrals table, changed commissions to store referrer_id

Revision ID: 1d42fcb46809
Revises: f27193a09e74
Create Date: 2026-01-06 20:21:55.357479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1d42fcb46809'
down_revision: Union[str, Sequence[str], None] = 'f27193a09e74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use raw SQL to handle IF EXISTS cases
    op.execute('ALTER TABLE commissions DROP CONSTRAINT IF EXISTS commissions_referral_id_fkey')
    op.execute('DROP TABLE IF EXISTS referrals')
    
    # Now modify commissions table
    with op.batch_alter_table('commissions') as batch_op:
        # Check if referral_id column exists before dropping
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = inspector.get_columns('commissions')
        column_names = [col['name'] for col in columns]
        
        if 'referral_id' in column_names:
            batch_op.drop_column('referral_id')
        
        # Only add referrer_id if it doesn't exist
        if 'referrer_id' not in column_names:
            batch_op.add_column(sa.Column('referrer_id', sa.String(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove referrer_id first
    with op.batch_alter_table('commissions') as batch_op:
        batch_op.drop_column('referrer_id')
    
    # Recreate referrals table
    op.create_table('referrals',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('referrer_id', sa.VARCHAR(), nullable=False),
        sa.Column('referred_id', sa.VARCHAR(), nullable=False),
        sa.Column('referral_code', sa.VARCHAR(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='referrals_pkey'),
        sa.UniqueConstraint('referral_code', name='referrals_referral_code_key')
    )
    
    # Add back referral_id to commissions
    with op.batch_alter_table('commissions') as batch_op:
        batch_op.add_column(sa.Column('referral_id', sa.UUID(), nullable=False))
    
    # Recreate foreign key
    op.create_foreign_key(
        'commissions_referral_id_fkey',
        'commissions',
        'referrals',
        ['referral_id'],
        ['id']
    )