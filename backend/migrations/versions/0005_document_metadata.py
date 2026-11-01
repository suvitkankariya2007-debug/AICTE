"""Persist uploaded document metadata."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0005'
down_revision='0004'
branch_labels=None
depends_on=None

def upgrade():
    columns={column['name'] for column in inspect(op.get_bind()).get_columns('documents')}
    if 'content_type' not in columns:
        op.add_column('documents',sa.Column('content_type',sa.String(),nullable=True))
    if 'size' not in columns:
        op.add_column('documents',sa.Column('size',sa.Integer(),nullable=True))

def downgrade():
    columns={column['name'] for column in inspect(op.get_bind()).get_columns('documents')}
    if 'size' in columns:
        op.drop_column('documents','size')
    if 'content_type' in columns:
        op.drop_column('documents','content_type')
