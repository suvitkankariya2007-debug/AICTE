"""Add structured finding fields for stage review."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0014'
down_revision='0013'
branch_labels=None
depends_on=None

def upgrade():
    columns={column['name'] for column in inspect(op.get_bind()).get_columns('findings')}
    if 'category' not in columns:
        op.add_column('findings',sa.Column('category',sa.String(),nullable=False,server_default='document_review'))
    if 'severity' not in columns:
        op.add_column('findings',sa.Column('severity',sa.String(),nullable=False,server_default='medium'))
    if 'recommendation' not in columns:
        op.add_column('findings',sa.Column('recommendation',sa.Text(),nullable=False,server_default=''))

def downgrade():
    columns={column['name'] for column in inspect(op.get_bind()).get_columns('findings')}
    if 'recommendation' in columns:
        op.drop_column('findings','recommendation')
    if 'severity' in columns:
        op.drop_column('findings','severity')
    if 'category' in columns:
        op.drop_column('findings','category')
