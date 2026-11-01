"""Add EVC participant assignments and quorum state."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0008'
down_revision='0007'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    if 'evc_participants' not in inspector.get_table_names():
        op.create_table(
            'evc_participants',
            sa.Column('id',sa.Integer(),primary_key=True),
            sa.Column('case_id',sa.String(),sa.ForeignKey('applications.id'),nullable=False),
            sa.Column('member_id',sa.String(),sa.ForeignKey('users.id'),nullable=False),
            sa.Column('assigned_by',sa.String(),nullable=False),
            sa.Column('status',sa.String(),nullable=False,server_default='assigned'),
            sa.Column('conflict_status',sa.String(),nullable=False,server_default='not_declared'),
            sa.Column('conflict_reason',sa.Text(),nullable=False,server_default=''),
            sa.Column('version',sa.Integer(),nullable=False,server_default='1'),
            sa.Column('active',sa.Boolean(),nullable=False,server_default=sa.true()),
            sa.Column('created',sa.String(),nullable=False),
        )
    existing={i['name'] for i in inspector.get_indexes('evc_participants')}
    if 'ix_evc_participants_case_status' not in existing:
        op.create_index('ix_evc_participants_case_status','evc_participants',['case_id','status'])
    if 'ix_evc_participants_member_active' not in existing:
        op.create_index('ix_evc_participants_member_active','evc_participants',['member_id','active'])

def downgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    if 'evc_participants' not in inspector.get_table_names():
        return
    for name in ('ix_evc_participants_member_active','ix_evc_participants_case_status'):
        if name in {i['name'] for i in inspector.get_indexes('evc_participants')}:
            op.drop_index(name,table_name='evc_participants')
    op.drop_table('evc_participants')
