"""Add verified role memberships."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0003'
down_revision='0002'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    if 'role_memberships' not in inspector.get_table_names():
        op.create_table(
            'role_memberships',
            sa.Column('id',sa.Integer(),primary_key=True),
            sa.Column('user_id',sa.String(),sa.ForeignKey('users.id'),nullable=False),
            sa.Column('role',sa.String(),nullable=False),
            sa.Column('region',sa.String(),nullable=False),
            sa.Column('institution',sa.String(),nullable=False),
            sa.Column('active',sa.Boolean(),nullable=False,server_default=sa.true()),
        )
    existing={index['name'] for index in inspector.get_indexes('role_memberships')}
    if 'ix_role_memberships_user_active' not in existing:
        op.create_index('ix_role_memberships_user_active','role_memberships',['user_id','active'])
    if 'ix_role_memberships_scope' not in existing:
        op.create_index('ix_role_memberships_scope','role_memberships',['role','region','institution'])

def downgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    if 'role_memberships' not in inspector.get_table_names():
        return
    existing={index['name'] for index in inspector.get_indexes('role_memberships')}
    if 'ix_role_memberships_scope' in existing:
        op.drop_index('ix_role_memberships_scope',table_name='role_memberships')
    if 'ix_role_memberships_user_active' in existing:
        op.drop_index('ix_role_memberships_user_active',table_name='role_memberships')
    op.drop_table('role_memberships')
