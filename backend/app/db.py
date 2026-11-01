import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Integer, Text, JSON, ForeignKey, Index, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

def now():
    return datetime.now(timezone.utc).isoformat()

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__='users'
    id: Mapped[str]=mapped_column(String,primary_key=True)
    name: Mapped[str]
    role: Mapped[str]
    region: Mapped[str]
    institution: Mapped[str]
    password: Mapped[str]
    memberships: Mapped[list['RoleMembership']]=relationship(
        back_populates='user', cascade='all, delete-orphan'
    )

class RoleMembership(Base):
    __tablename__='role_memberships'
    __table_args__=(
        Index('ix_role_memberships_user_active', 'user_id', 'active'),
        Index('ix_role_memberships_scope', 'role', 'region', 'institution'),
    )
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    role: Mapped[str]
    region: Mapped[str]
    institution: Mapped[str]
    active: Mapped[bool]=mapped_column(default=True)
    user: Mapped[User]=relationship(back_populates='memberships')

class RuleSet(Base):
    __tablename__='rule_sets'
    __table_args__=(
        Index('ix_rule_sets_status_effective', 'status', 'effective_from'),
    )
    version: Mapped[str]=mapped_column(String,primary_key=True)
    status: Mapped[str]
    source: Mapped[str]
    effective_from: Mapped[str]
    definitions: Mapped[dict]=mapped_column(JSON)
class LoginSession(Base):
    __tablename__='sessions'
    __table_args__=(Index('ix_sessions_expires', 'expires'),)
    token: Mapped[str]=mapped_column(String,primary_key=True)
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    expires: Mapped[str]
class Case(Base):
    __tablename__='applications'
    __table_args__=(
        Index('ix_applications_region_state', 'region', 'state'),
        Index('ix_applications_owner_state', 'owner', 'state'),
        Index('ix_applications_due', 'due'),
        Index('ix_applications_entered', 'entered'),
    )
    id: Mapped[str]=mapped_column(String,primary_key=True)
    institution: Mapped[str]
    region: Mapped[str]
    kind: Mapped[str]
    state: Mapped[str]
    route: Mapped[list]=mapped_column(JSON)
    rule_version: Mapped[str]
    owner: Mapped[str]
    version: Mapped[int]=mapped_column(default=1)
    entered: Mapped[str]=mapped_column(default=now)
    due: Mapped[str]
    reason: Mapped[str]=mapped_column(Text,default='')
    schedule: Mapped[str]=mapped_column(default='')
    report: Mapped[str]=mapped_column(Text,default='')
    submit_key: Mapped[str]=mapped_column(unique=True)
class Assignment(Base):
    __tablename__='assignments'
    __table_args__=(
        Index('ix_assignments_case_created', 'case_id', 'created'),
        Index('ix_assignments_reviewer_active', 'reviewer_id', 'active'),
    )
    id: Mapped[int]=mapped_column(primary_key=True)
    case_id: Mapped[str]=mapped_column(ForeignKey('applications.id'))
    reviewer_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    assigned_by: Mapped[str]
    reason: Mapped[str]=mapped_column(Text)
    active: Mapped[bool]=mapped_column(default=True)
    conflict_status: Mapped[str]=mapped_column(default='not_declared')
    conflict_reason: Mapped[str]=mapped_column(Text,default='')
    created: Mapped[str]=mapped_column(default=now)
    ended: Mapped[str]=mapped_column(default='')
class EvcParticipant(Base):
    __tablename__='evc_participants'
    __table_args__=(
        Index('ix_evc_participants_case_status', 'case_id', 'status'),
        Index('ix_evc_participants_member_active', 'member_id', 'active'),
    )
    id: Mapped[int]=mapped_column(primary_key=True)
    case_id: Mapped[str]=mapped_column(ForeignKey('applications.id'))
    member_id: Mapped[str]=mapped_column(ForeignKey('users.id'))
    assigned_by: Mapped[str]
    status: Mapped[str]=mapped_column(default='assigned')
    conflict_status: Mapped[str]=mapped_column(default='not_declared')
    conflict_reason: Mapped[str]=mapped_column(Text,default='')
    version: Mapped[int]=mapped_column(default=1)
    active: Mapped[bool]=mapped_column(default=True)
    created: Mapped[str]=mapped_column(default=now)
class Document(Base):
    __tablename__='documents'
    __table_args__=(Index('ix_documents_case_slot', 'case_id', 'slot'),)
    id: Mapped[int]=mapped_column(primary_key=True)
    case_id: Mapped[str]=mapped_column(ForeignKey('applications.id'))
    slot: Mapped[str]
    filename: Mapped[str]
    content_type: Mapped[str]
    size: Mapped[int]
    content: Mapped[str]=mapped_column(Text)
    sha256: Mapped[str]
    revision: Mapped[int]
    created: Mapped[str]=mapped_column(default=now)
class Finding(Base):
    __tablename__='findings'
    __table_args__=(
        Index('ix_findings_case_status', 'case_id', 'status'),
    )
    id: Mapped[int]=mapped_column(primary_key=True)
    case_id: Mapped[str]=mapped_column(ForeignKey('applications.id'))
    description: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(default='open')
    response: Mapped[str]=mapped_column(Text,default='')
    version: Mapped[int]=mapped_column(default=1)
    created_by: Mapped[str]
    created: Mapped[str]=mapped_column(default=now)
    responded: Mapped[str]=mapped_column(default='')
    closed: Mapped[str]=mapped_column(default='')
class Obligation(Base):
    __tablename__='obligations'
    __table_args__=(
        Index('ix_obligations_case_status', 'case_id', 'status'),
        Index('ix_obligations_due', 'due'),
    )
    id: Mapped[int]=mapped_column(primary_key=True)
    case_id: Mapped[str]=mapped_column(ForeignKey('applications.id'))
    kind: Mapped[str]
    title: Mapped[str]
    due: Mapped[str]
    status: Mapped[str]=mapped_column(default='pending')
    evidence: Mapped[str]=mapped_column(Text,default='')
    proposed_expiry: Mapped[str]=mapped_column(default='')
    version: Mapped[int]=mapped_column(default=1)
    review_note: Mapped[str]=mapped_column(Text,default='')
    verified_by: Mapped[str]=mapped_column(default='')
    verified_at: Mapped[str]=mapped_column(default='')
    requires_replacement: Mapped[bool]=mapped_column(default=False)
class Audit(Base):
    __tablename__='audit_events'
    __table_args__=(Index('ix_audit_case_created', 'case_id', 'created'),)
    id: Mapped[int]=mapped_column(primary_key=True)
    case_id: Mapped[str]=mapped_column(ForeignKey('applications.id'))
    actor: Mapped[str]
    action: Mapped[str]
    detail: Mapped[str]=mapped_column(Text)
    created: Mapped[str]=mapped_column(default=now)
class Notice(Base):
    __tablename__='notifications'
    __table_args__=(Index('ix_notifications_case_created', 'case_id', 'created'),)
    id: Mapped[int]=mapped_column(primary_key=True)
    case_id: Mapped[str]=mapped_column(ForeignKey('applications.id'))
    recipient: Mapped[str]
    message: Mapped[str]
    level: Mapped[str]
    delivery: Mapped[str]=mapped_column(default='simulated')
    dedup: Mapped[str]=mapped_column(unique=True)
    created: Mapped[str]=mapped_column(default=now)
    status: Mapped[str]=mapped_column(default='delivered')
    attempts: Mapped[int]=mapped_column(default=1)
    last_error: Mapped[str]=mapped_column(Text,default='')
    delivered_at: Mapped[str]=mapped_column(default=now)

def setup(url=None):
    url=url or os.getenv('DATABASE_URL','sqlite:///./aicte.db')
    engine=create_engine(url,connect_args={'check_same_thread':False,'timeout':20} if url.startswith('sqlite') else {})
    if url.startswith('sqlite'):
        @event.listens_for(engine,'connect')
        def pragmas(conn, _): conn.execute('PRAGMA foreign_keys=ON')
    return engine,sessionmaker(engine,expire_on_commit=False)
