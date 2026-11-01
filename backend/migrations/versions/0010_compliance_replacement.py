"""Require replacement evidence after clarification."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0010'
down_revision='0009'
branch_labels=None
depends_on=None

def upgrade():
    columns={column['name'] for column in inspect(op.get_bind()).get_columns('obligations')}
    if 'requires_replacement' not in columns:
        op.add_column('obligations',sa.Column('requires_replacement',sa.Boolean(),nullable=True,server_default=sa.false()))

def downgrade():
    columns={column['name'] for column in inspect(op.get_bind()).get_columns('obligations')}
    if 'requires_replacement' in columns:
        op.drop_column('obligations','requires_replacement')
