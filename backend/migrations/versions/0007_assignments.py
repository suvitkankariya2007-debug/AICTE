"""Add assignment history and conflict status."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0007'
down_revision='0006'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    if 'assignments' not in inspector.get_table_names():
        op.create_table(
            'assignments',
            sa.Column('id',sa.Integer(),primary_key=True),
            sa.Column('case_id',sa.String(),sa.ForeignKey('applications.id'),nullable=False),
            sa.Column('reviewer_id',sa.String(),sa.ForeignKey('users.id'),nullable=False),
            sa.Column('assigned_by',sa.String(),nullable=False),
            sa.Column('reason',sa.Text(),nullable=False),
            sa.Column('active',sa.Boolean(),nullable=False,server_default=sa.true()),
            sa.Column('conflict_status',sa.String(),nullable=False,server_default='not_declared'),
            sa.Column('conflict_reason',sa.Text(),nullable=False,server_default=''),
            sa.Column('created',sa.String(),nullable=False),
            sa.Column('ended',sa.String(),nullable=False,server_default=''),
        )
    existing={i['name'] for i in inspector.get_indexes('assignments')}
    if 'ix_assignments_case_created' not in existing:
        op.create_index('ix_assignments_case_created','assignments',['case_id','created'])
    if 'ix_assignments_reviewer_active' not in existing:
        op.create_index('ix_assignments_reviewer_active','assignments',['reviewer_id','active'])
    op.execute(
        sa.text(
            "INSERT INTO assignments "
            "(case_id, reviewer_id, assigned_by, reason, active, conflict_status, conflict_reason, created, ended) "
            "SELECT id, owner, 'system', 'Backfilled from current application owner', 1, "
            "'not_declared', '', entered, '' FROM applications "
            "WHERE owner IS NOT NULL AND NOT EXISTS "
            "(SELECT 1 FROM assignments existing WHERE existing.case_id = applications.id)"
        )
    )

def downgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    if 'assignments' not in inspector.get_table_names():
        return
    for name in ('ix_assignments_reviewer_active','ix_assignments_case_created'):
        if name in {i['name'] for i in inspector.get_indexes('assignments')}:
            op.drop_index(name,table_name='assignments')
    op.drop_table('assignments')
