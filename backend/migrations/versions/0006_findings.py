"""Add structured scrutiny findings."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0006'
down_revision='0005'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    if 'findings' not in inspector.get_table_names():
        op.create_table(
            'findings',
            sa.Column('id',sa.Integer(),primary_key=True),
            sa.Column('case_id',sa.String(),sa.ForeignKey('applications.id'),nullable=False),
            sa.Column('description',sa.Text(),nullable=False),
            sa.Column('status',sa.String(),nullable=False,server_default='open'),
            sa.Column('response',sa.Text(),nullable=False,server_default=''),
            sa.Column('version',sa.Integer(),nullable=False,server_default='1'),
            sa.Column('created_by',sa.String(),nullable=False),
            sa.Column('created',sa.String(),nullable=False),
            sa.Column('responded',sa.String(),nullable=False,server_default=''),
            sa.Column('closed',sa.String(),nullable=False,server_default=''),
        )
    if 'ix_findings_case_status' not in {i['name'] for i in inspector.get_indexes('findings')}:
        op.create_index('ix_findings_case_status','findings',['case_id','status'])

def downgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    if 'findings' not in inspector.get_table_names():
        return
    if 'ix_findings_case_status' in {i['name'] for i in inspector.get_indexes('findings')}:
        op.drop_index('ix_findings_case_status',table_name='findings')
    op.drop_table('findings')
