import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Integer, Text, JSON, ForeignKey, Index, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

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
class Document(Base):
    __tablename__='documents'
    __table_args__=(Index('ix_documents_case_slot', 'case_id', 'slot'),)
    id: Mapped[int]=mapped_column(primary_key=True)
    case_id: Mapped[str]=mapped_column(ForeignKey('applications.id'))
    slot: Mapped[str]
    filename: Mapped[str]
    content: Mapped[str]=mapped_column(Text)
    sha256: Mapped[str]
    revision: Mapped[int]
    created: Mapped[str]=mapped_column(default=now)
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

def setup(url=None):
    url=url or os.getenv('DATABASE_URL','sqlite:///./aicte.db')
    engine=create_engine(url,connect_args={'check_same_thread':False,'timeout':20} if url.startswith('sqlite') else {})
    if url.startswith('sqlite'):
        @event.listens_for(engine,'connect')
        def pragmas(conn, _): conn.execute('PRAGMA foreign_keys=ON')
    return engine,sessionmaker(engine,expire_on_commit=False)
