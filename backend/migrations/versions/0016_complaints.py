"""Add complaints and referral triage records."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0016'
down_revision='0015'
branch_labels=None
depends_on=None

def upgrade():
    if 'complaints' not in inspect(op.get_bind()).get_table_names():
        op.create_table(
            'complaints',
            sa.Column('id',sa.Integer(),primary_key=True),
            sa.Column('case_id',sa.String(),sa.ForeignKey('applications.id'),nullable=False),
            sa.Column('institution',sa.String(),nullable=False),
            sa.Column('region',sa.String(),nullable=False),
            sa.Column('category',sa.String(),nullable=False),
            sa.Column('priority',sa.String(),nullable=False,server_default='normal'),
            sa.Column('status',sa.String(),nullable=False,server_default='open'),
            sa.Column('description',sa.Text(),nullable=False),
            sa.Column('resolution',sa.Text(),nullable=False,server_default=''),
            sa.Column('version',sa.Integer(),nullable=False,server_default='1'),
            sa.Column('created_by',sa.String(),nullable=False),
            sa.Column('created',sa.String(),nullable=False,server_default=''),
            sa.Column('updated',sa.String(),nullable=False,server_default=''),
        )
        op.create_index('ix_complaints_case_status','complaints',['case_id','status'])
        op.create_index('ix_complaints_region_status','complaints',['region','status'])

def downgrade():
    if 'complaints' in inspect(op.get_bind()).get_table_names():
        op.drop_index('ix_complaints_region_status',table_name='complaints')
        op.drop_index('ix_complaints_case_status',table_name='complaints')
        op.drop_table('complaints')
