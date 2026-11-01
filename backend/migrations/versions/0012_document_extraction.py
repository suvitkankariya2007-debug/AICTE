"""Add document extraction and review metadata."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0012'
down_revision='0011'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    columns={column['name'] for column in inspect(bind).get_columns('documents')}
    additions=[
        ('processing_status',sa.String(), 'pending'),
        ('extracted_text',sa.Text(), ''),
        ('extraction_error',sa.Text(), ''),
        ('reviewed_by',sa.String(), ''),
        ('reviewed_at',sa.String(), ''),
    ]
    for name,type_,default in additions:
        if name not in columns:
            op.add_column('documents',sa.Column(name,type_,nullable=True,server_default=default))

def downgrade():
    columns={column['name'] for column in inspect(op.get_bind()).get_columns('documents')}
    for name in ('reviewed_at','reviewed_by','extraction_error','extracted_text','processing_status'):
        if name in columns:
            op.drop_column('documents',name)
