"""Merge migration heads

Revision ID: 1ffd1071ee5a
Revises: 0396ded3cba0, 0899cb13b189
Create Date: 2026-01-15 15:39:19.035962

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ffd1071ee5a'
down_revision = ('0396ded3cba0', '0899cb13b189')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
