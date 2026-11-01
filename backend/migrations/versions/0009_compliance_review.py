"""Add compliance review and verification metadata."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0009'
down_revision='0008'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    columns={column['name'] for column in inspect(bind).get_columns('obligations')}
    additions=[
        ('review_note',sa.Text(), ''),
        ('verified_by',sa.String(), ''),
        ('verified_at',sa.String(), ''),
    ]
    for name,type_,default in additions:
        if name not in columns:
            op.add_column('obligations',sa.Column(name,type_,nullable=True,server_default=default))

def downgrade():
    columns={column['name'] for column in inspect(op.get_bind()).get_columns('obligations')}
    for name in ('verified_at','verified_by','review_note'):
        if name in columns:
            op.drop_column('obligations',name)
