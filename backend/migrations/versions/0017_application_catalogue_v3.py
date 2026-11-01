"""Publish the complete illustrative application catalogue."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from app.rules import RULES, VERSION, SOURCE

revision='0017'
down_revision='0016'
branch_labels=None
depends_on=None

def upgrade():
    if 'rule_sets' not in inspect(op.get_bind()).get_table_names():
        return
    connection=op.get_bind()
    exists=connection.execute(
        sa.text('SELECT 1 FROM rule_sets WHERE version = :version'),
        {'version':VERSION},
    ).first()
    if not exists:
        connection.execute(
            sa.text(
                'INSERT INTO rule_sets '
                '(version, status, source, effective_from, definitions) '
                'VALUES (:version, :status, :source, :effective_from, :definitions)'
            ),
            {
                'version':VERSION,
                'status':'published',
                'source':SOURCE,
                'effective_from':'2026-11-01T00:00:00+00:00',
                'definitions':__import__('json').dumps(RULES),
            },
        )

def downgrade():
    if 'rule_sets' in inspect(op.get_bind()).get_table_names():
        op.get_bind().execute(
            sa.text('DELETE FROM rule_sets WHERE version = :version'),
            {'version':VERSION},
        )
