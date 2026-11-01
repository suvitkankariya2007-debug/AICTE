"""Add persistent deadline worker heartbeat."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0013'
down_revision='0012'
branch_labels=None
depends_on=None

def upgrade():
    if 'worker_heartbeats' not in inspect(op.get_bind()).get_table_names():
        op.create_table(
            'worker_heartbeats',
            sa.Column('id',sa.Integer(),primary_key=True),
            sa.Column('last_started',sa.String(),nullable=False,server_default=''),
            sa.Column('last_completed',sa.String(),nullable=False,server_default=''),
            sa.Column('last_error',sa.Text(),nullable=False,server_default=''),
            sa.Column('processed',sa.Integer(),nullable=False,server_default='0'),
        )

def downgrade():
    if 'worker_heartbeats' in inspect(op.get_bind()).get_table_names():
        op.drop_table('worker_heartbeats')
