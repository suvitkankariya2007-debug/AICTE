"""Add persistent versioned rule sets."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision='0004'
down_revision='0003'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    if 'rule_sets' not in inspector.get_table_names():
        op.create_table(
            'rule_sets',
            sa.Column('version',sa.String(),primary_key=True),
            sa.Column('status',sa.String(),nullable=False),
            sa.Column('source',sa.String(),nullable=False),
            sa.Column('effective_from',sa.String(),nullable=False),
            sa.Column('definitions',sa.JSON(),nullable=False),
        )
    if 'ix_rule_sets_status_effective' not in {i['name'] for i in inspector.get_indexes('rule_sets')}:
        op.create_index('ix_rule_sets_status_effective','rule_sets',['status','effective_from'])

def downgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    if 'rule_sets' not in inspector.get_table_names():
        return
    if 'ix_rule_sets_status_effective' in {i['name'] for i in inspector.get_indexes('rule_sets')}:
        op.drop_index('ix_rule_sets_status_effective',table_name='rule_sets')
    op.drop_table('rule_sets')
