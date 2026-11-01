"""Add indexes used by scoped queues and deadline checks."""
from alembic import op
from sqlalchemy import inspect

revision='0002'
down_revision='0001'
branch_labels=None
depends_on=None

INDEXES={
    'sessions': ['ix_sessions_expires'],
    'applications': [
        'ix_applications_region_state',
        'ix_applications_owner_state',
        'ix_applications_due',
        'ix_applications_entered',
    ],
    'documents': ['ix_documents_case_slot'],
    'obligations': ['ix_obligations_case_status', 'ix_obligations_due'],
    'audit_events': ['ix_audit_case_created'],
    'notifications': ['ix_notifications_case_created'],
}


def upgrade():
    bind=op.get_bind()
    inspector=inspect(bind)
    existing={
        index['name']
        for table in inspector.get_table_names()
        for index in inspector.get_indexes(table)
    }
    for table, names in INDEXES.items():
        for name in names:
            if name not in existing:
                columns={
                    'ix_sessions_expires':['expires'],
                    'ix_applications_region_state':['region','state'],
                    'ix_applications_owner_state':['owner','state'],
                    'ix_applications_due':['due'],
                    'ix_applications_entered':['entered'],
                    'ix_documents_case_slot':['case_id','slot'],
                    'ix_obligations_case_status':['case_id','status'],
                    'ix_obligations_due':['due'],
                    'ix_audit_case_created':['case_id','created'],
                    'ix_notifications_case_created':['case_id','created'],
                }[name]
                op.create_index(name,table,columns)


def downgrade():
    for table, names in INDEXES.items():
        for name in names:
            op.drop_index(name,table_name=table)
