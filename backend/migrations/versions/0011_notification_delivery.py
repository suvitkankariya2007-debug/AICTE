"""Add notification delivery lifecycle and retry metadata."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0011'
down_revision='0010'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    columns={column['name'] for column in inspect(bind).get_columns('notifications')}
    additions=[
        ('status',sa.String(), 'delivered'),
        ('attempts',sa.Integer(), '1'),
        ('last_error',sa.Text(), ''),
        ('delivered_at',sa.String(), ''),
    ]
    for name,type_,default in additions:
        if name not in columns:
            op.add_column('notifications',sa.Column(name,type_,nullable=True,server_default=default))

def downgrade():
    columns={column['name'] for column in inspect(op.get_bind()).get_columns('notifications')}
    for name in ('delivered_at','last_error','attempts','status'):
        if name in columns:
            op.drop_column('notifications',name)
