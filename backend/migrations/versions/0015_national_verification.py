"""Add national verification records."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0015'
down_revision='0014'
branch_labels=None
depends_on=None

def upgrade():
    if 'national_verifications' not in inspect(op.get_bind()).get_table_names():
        op.create_table(
            'national_verifications',
            sa.Column('id',sa.Integer(),primary_key=True),
            sa.Column('case_id',sa.String(),sa.ForeignKey('applications.id'),nullable=False),
            sa.Column('status',sa.String(),nullable=False,server_default='pending'),
            sa.Column('decision',sa.String(),nullable=False,server_default=''),
            sa.Column('note',sa.Text(),nullable=False,server_default=''),
            sa.Column('version',sa.Integer(),nullable=False,server_default='1'),
            sa.Column('reviewed_by',sa.String(),nullable=False,server_default=''),
            sa.Column('created',sa.String(),nullable=False,server_default=''),
            sa.Column('reviewed',sa.String(),nullable=False,server_default=''),
        )
        op.create_index('ix_national_verifications_case_status','national_verifications',['case_id','status'])

def downgrade():
    if 'national_verifications' in inspect(op.get_bind()).get_table_names():
        op.drop_index('ix_national_verifications_case_status',table_name='national_verifications')
        op.drop_table('national_verifications')
