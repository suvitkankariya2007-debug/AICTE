import logging, os, secrets, hashlib, hmac, base64, re, time, uuid
from pathlib import PurePath
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Response, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from .db import Base, User, RoleMembership, RuleSet, LoginSession, Case, Assignment, EvcParticipant, Document, Finding, Obligation, Audit, Notice, setup
from .rules import RULES, VERSION, SOURCE, validate_definitions
from .engine import move, audit, sweep, utc
from .config import load_settings

DEMO_PASSWORD='DemoPass!2026'
logger = logging.getLogger('aicte.api')
REQUEST_ID_PATTERN=re.compile(r'^[A-Za-z0-9._:-]{1,128}$')
def hash_password(password,salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+':'+hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),150000).hex()
def check_password(password,stored): return hmac.compare_digest(hash_password(password,stored.split(':')[0]),stored)
def serial(obj): return {c.name:getattr(obj,c.name) for c in obj.__table__.columns if c.name not in ['password','token','content']}
class Strict(BaseModel): model_config=ConfigDict(extra='forbid')
class Login(Strict): username:str; password:str
class Create(Strict): kind:str; idempotency_key:str=Field(min_length=8,max_length=100)
class Action(Strict): target:str; version:int; reason:str=Field(default='',max_length=4000)
class Evidence(Strict): version:int; evidence:str=Field(min_length=5,max_length=4000); expiry:str=''
class Assign(Strict): version:int; reviewer_id:str; reason:str=Field(min_length=5,max_length=2000)
class Conflict(Strict): status:str; reason:str=Field(default='',max_length=2000)
class ParticipantAdd(Strict): member_id:str
class ParticipantAction(Strict): version:int; status:str; reason:str=Field(default='',max_length=2000)
class Verify(Strict): version:int
class ComplianceReview(Strict): version:int; reason:str=Field(min_length=5,max_length=4000)
class Schedule(Strict): version:int; date:str; report:str=Field(default='',max_length=4000)
class FindingCreate(Strict): description:str=Field(min_length=5,max_length=4000)
class FindingResponse(Strict): version:int; response:str=Field(min_length=5,max_length=4000)
class FindingClose(Strict): version:int
class RuleDraft(Strict):
    version:str=Field(min_length=1,max_length=80)
    source:str=Field(min_length=5,max_length=4000)
    effective_from:str
    definitions:dict

def create_app(url=None):
    settings=load_settings()
    engine,Factory=setup(url or settings.database_url)
    @asynccontextmanager
    async def lifespan(app):
        if settings.auto_create_schema:
            Base.metadata.create_all(engine)
        with Factory.begin() as db: seed(db)
        yield
        engine.dispose()
    app=FastAPI(title='AICTE Workflow · DEMO',lifespan=lifespan)
    app.state.factory=Factory
    app.state.settings=settings
    @app.exception_handler(IntegrityError)
    async def conflict(request,exc):
        return JSONResponse(status_code=409,content={'detail':'Concurrent or duplicate write; refresh and retry with the same request key.'})
    @app.middleware('http')
    async def security(request,call_next):
        supplied_request_id=request.headers.get('X-Request-ID','')
        request_id=(
            supplied_request_id
            if REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
            else uuid.uuid4().hex
        )
        started=time.perf_counter()
        if request.method not in ['GET','HEAD','OPTIONS']:
            origin=request.headers.get('origin')
            if origin and origin not in {str(request.base_url).rstrip('/'),settings.frontend_origin}:
                response=Response('Origin not permitted',status_code=403)
                response.headers['X-Request-ID']=request_id
                return response
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Cache-Control']='no-store'
        response.headers['X-Request-ID']=request_id
        logger.info(
            'request_completed method=%s path=%s status=%s duration_ms=%.2f request_id=%s',
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter()-started)*1000,
            request_id,
        )
        return response
    def db_session():
        with Factory() as db:
            try: yield db; db.commit()
            except Exception: db.rollback(); raise
    def current(request:Request,db=Depends(db_session)):
        session=db.get(LoginSession,hashlib.sha256(request.cookies.get('session','').encode()).hexdigest())
        if not session or utc(session.expires)<=datetime.now(timezone.utc): raise HTTPException(401,'Please sign in')
        user=db.get(User,session.user_id)
        if not user: raise HTTPException(401,'Please sign in')
        return user
    def has_membership(u,role,region=None,institution=None):
        return any(
            m.active and m.role==role
            and (region is None or m.region==region)
            and (institution is None or m.institution==institution)
            for m in u.memberships
        )
    def membership(u,role,region=None,institution=None):
        return next((
            m for m in u.memberships
            if m.active and m.role==role
            and (region is None or m.region==region)
            and (institution is None or m.institution==institution)
        ),None)
    async def read_upload(file):
        data=await file.read(2*1024*1024+1)
        if not data or len(data)>2*1024*1024:
            raise HTTPException(422,'Upload must be between 1 byte and 2 MB')
        content_type=file.content_type or ''
        if not ((content_type=='application/pdf' and data.startswith(b'%PDF-')) or (content_type=='text/plain' and b'\x00' not in data)):
            raise HTTPException(422,'Demo accepts PDF or plain text evidence only')
        filename=PurePath(file.filename or 'evidence').name
        filename=re.sub(r'[^\w. -]','_',filename).strip(' .')[-120:] or 'evidence'
        return data,content_type,filename
    def active_rules(db):
        now=datetime.now(timezone.utc).isoformat()
        return db.scalar(select(RuleSet).where(
            RuleSet.status=='published',
            RuleSet.effective_from<=now,
        ).order_by(RuleSet.effective_from.desc()))
    def rule_for(db,version):
        rule_set=db.get(RuleSet,version)
        if not rule_set: raise HTTPException(503,'Application rule version is unavailable')
        return rule_set.definitions
    def permitted(c,u):
        return (
            has_membership(u,'national_admin')
            or has_membership(u,'institution',institution=c.institution)
            or has_membership(u,'regional_officer',region=c.region)
            or (has_membership(u,'scrutiny_officer',region=c.region) and c.owner==u.id)
        )
    def case_for(cid,u,db):
        c=db.get(Case,cid)
        if not c or not permitted(c,u): raise HTTPException(404,'Application not found in your scope')
        return c
    def reviewer(c,u):
        if not (has_membership(u,'scrutiny_officer',region=c.region) or has_membership(u,'regional_officer',region=c.region)): raise HTTPException(403,'Reviewer permission required')
    @app.get('/api/health')
    def health(): return {'status':'ok','mode':'DEMO','rule_status':'NEEDS_APH_VERIFICATION'}
    @app.get('/api/demo-accounts')
    def accounts(db=Depends(db_session)):
        if not settings.demo_mode: raise HTTPException(404)
        return [serial(u) for u in db.scalars(select(User))]
    @app.post('/api/login')
    def login(body:Login,response:Response,db=Depends(db_session)):
        u=db.get(User,body.username)
        if not u or not check_password(body.password,u.password): raise HTTPException(401,'Invalid credentials')
        token=secrets.token_urlsafe(32)
        db.add(LoginSession(token=hashlib.sha256(token.encode()).hexdigest(),user_id=u.id,expires=(datetime.now(timezone.utc)+timedelta(hours=8)).isoformat()))
        response.set_cookie('session',token,httponly=True,samesite='strict',secure=settings.cookie_secure,max_age=28800)
        return serial(u)
    @app.post('/api/logout')
    def logout(request:Request,response:Response,db=Depends(db_session)):
        session=db.get(LoginSession,hashlib.sha256(request.cookies.get('session','').encode()).hexdigest())
        if session: db.delete(session)
        response.delete_cookie('session'); return {'ok':True}
    @app.get('/api/me')
    def me(u=Depends(current)): return serial(u)
    @app.get('/api/me/roles')
    def roles(u=Depends(current)):
        return [
            {
                'id':membership.id,
                'role':membership.role,
                'region':membership.region,
                'institution':membership.institution,
            }
            for membership in u.memberships
            if membership.active
        ]
    @app.get('/api/rules')
    def rules(u=Depends(current),db=Depends(db_session)):
        rule_set=active_rules(db)
        if not rule_set: raise HTTPException(503,'No published application rules are available')
        return {'version':rule_set.version,'source':rule_set.source,'effective_from':rule_set.effective_from,'types':rule_set.definitions}
    @app.post('/api/rules/drafts')
    def draft_rule(body:RuleDraft,u=Depends(current),db=Depends(db_session)):
        if not has_membership(u,'national_admin'): raise HTTPException(403,'National oversight permission required')
        try: validate_definitions(body.definitions); utc(body.effective_from)
        except ValueError as exc: raise HTTPException(422,str(exc))
        if db.get(RuleSet,body.version): raise HTTPException(409,'Rule version already exists')
        rule_set=RuleSet(version=body.version,status='draft',source=body.source,effective_from=utc(body.effective_from).isoformat(),definitions=body.definitions)
        db.add(rule_set); db.flush()
        return {'version':rule_set.version,'status':rule_set.status}
    @app.post('/api/rules/{version}/publish')
    def publish_rule(version:str,u=Depends(current),db=Depends(db_session)):
        if not has_membership(u,'national_admin'): raise HTTPException(403,'National oversight permission required')
        rule_set=db.get(RuleSet,version)
        if not rule_set: raise HTTPException(404,'Rule version not found')
        if rule_set.status!='draft': raise HTTPException(409,'Only draft rules can be published')
        validate_definitions(rule_set.definitions)
        db.query(RuleSet).filter(RuleSet.status=='published').update({'status':'retired'},synchronize_session=False)
        rule_set.status='published'
        db.flush()
        return {'version':rule_set.version,'status':rule_set.status}
    @app.get('/api/applications')
    def cases(u=Depends(current),db=Depends(db_session)):
        return [serial(c) for c in db.scalars(select(Case).order_by(Case.entered.desc())) if permitted(c,u)]
    @app.post('/api/applications')
    def create(body:Create,u=Depends(current),db=Depends(db_session)):
        scope=membership(u,'institution')
        if not scope: raise HTTPException(403,'Institution permission required')
        rule_set=active_rules(db)
        if not rule_set or body.kind not in rule_set.definitions: raise HTTPException(422,'Unknown application type')
        definition=rule_set.definitions[body.kind]
        key=u.id+':'+body.idempotency_key
        prior=db.scalar(select(Case).where(Case.submit_key==key))
        if prior:
            if prior.kind!=body.kind: raise HTTPException(409,'Idempotency key belongs to another request')
            return serial(prior)
        c=Case(id='APP-'+secrets.token_hex(4).upper(),institution=scope.institution,region=scope.region,kind=body.kind,state='draft',route=definition['route'],rule_version=rule_set.version,owner='officer-west' if scope.region=='West Demo' else 'officer-east',due=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat(),submit_key=key)
        db.add(c); db.flush(); audit(db,c,u,'draft_created',SOURCE); return serial(c)
    @app.get('/api/applications/{cid}')
    def detail(cid:str,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        definitions=rule_for(db,c.rule_version)
        if c.kind not in definitions: raise HTTPException(503,'Application checklist is unavailable')
        return {**serial(c),'documents':[serial(d) for d in db.scalars(select(Document).where(Document.case_id==cid).order_by(Document.id))],'findings':[serial(f) for f in db.scalars(select(Finding).where(Finding.case_id==cid).order_by(Finding.id))],'obligations':[serial(o) for o in db.scalars(select(Obligation).where(Obligation.case_id==cid))],'audit':[serial(a) for a in db.scalars(select(Audit).where(Audit.case_id==cid).order_by(Audit.id.desc()))],'slots':definitions[c.kind]['slots']}
    @app.post('/api/applications/{cid}/documents')
    async def upload(cid:str,slot:str=Form(...),version:int=Form(...),file:UploadFile=File(...),u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if not has_membership(u,'institution',institution=c.institution) or c.state not in ['draft','correction']: raise HTTPException(403,'Uploads permitted only during draft/correction')
        definitions=rule_for(db,c.rule_version)
        if c.kind not in definitions or slot not in definitions[c.kind]['slots']: raise HTTPException(422,'Unknown checklist slot')
        data,content_type,name=await read_upload(file)
        if db.execute(update(Case).where(Case.id==cid,Case.version==version).values(version=version+1)).rowcount!=1: raise HTTPException(409,'Case changed; refresh')
        docs=list(db.scalars(select(Document).where(Document.case_id==cid,Document.slot==slot)))
        extracted=data.decode('utf-8') if content_type=='text/plain' else ''
        d=Document(case_id=cid,slot=slot,filename=name,content_type=content_type,size=len(data),content=base64.b64encode(data).decode(),sha256=hashlib.sha256(data).hexdigest(),revision=len(docs)+1,processing_status='extracted' if extracted else 'pending',extracted_text=extracted)
        db.add(d); audit(db,c,u,'evidence_uploaded',f'{slot}; revision {d.revision}; sha256 {d.sha256}'); db.flush(); return serial(d)
    @app.get('/api/documents/{did}')
    def download(did:int,u=Depends(current),db=Depends(db_session)):
        d=db.get(Document,did)
        if not d: raise HTTPException(404)
        case_for(d.case_id,u,db)
        filename=re.sub(r'[^A-Za-z0-9._ -]','_',d.filename).strip(' .') or 'evidence'
        return Response(base64.b64decode(d.content),media_type=d.content_type or 'application/octet-stream',headers={'Content-Disposition':f'attachment; filename="{filename}"'})
    @app.post('/api/documents/{did}/process')
    def process_document(did:int,u=Depends(current),db=Depends(db_session)):
        d=db.get(Document,did)
        if not d: raise HTTPException(404,'Document not found')
        c=case_for(d.case_id,u,db)
        if not has_membership(u,'regional_officer',region=c.region) and not has_membership(u,'national_admin'):
            raise HTTPException(403,'Reviewer permission required')
        if d.content_type!='text/plain':
            d.processing_status='failed'
            d.extraction_error='OCR adapter is not configured for PDF content'
            audit(db,c,u,'document_extraction_failed',f'{d.filename}: {d.extraction_error}')
            db.flush()
            return serial(d)
        d.extracted_text=base64.b64decode(d.content).decode('utf-8')
        d.processing_status='extracted'
        d.extraction_error=''
        audit(db,c,u,'document_extracted',f'{d.filename}; text length {len(d.extracted_text)}')
        db.flush()
        return serial(d)
    @app.post('/api/documents/{did}/review')
    def review_document(did:int,body:Verify,u=Depends(current),db=Depends(db_session)):
        d=db.get(Document,did)
        if not d: raise HTTPException(404,'Document not found')
        c=case_for(d.case_id,u,db)
        if not has_membership(u,'regional_officer',region=c.region) and not has_membership(u,'national_admin'):
            raise HTTPException(403,'Reviewer permission required')
        if d.processing_status!='extracted' or not d.extracted_text:
            raise HTTPException(409,'Extracted text must be available before review')
        d.processing_status='reviewed'
        d.reviewed_by=u.id
        d.reviewed_at=datetime.now(timezone.utc).isoformat()
        audit(db,c,u,'document_extraction_reviewed',f'{d.filename}; extracted text accepted for review')
        db.flush()
        return serial(d)
    @app.post('/api/applications/{cid}/submit')
    def submit(cid:str,body:Verify,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if not has_membership(u,'institution',institution=c.institution) or c.state not in ['draft','correction']: raise HTTPException(403,'Not awaiting institutional submission')
        definitions=rule_for(db,c.rule_version)
        if c.kind not in definitions: raise HTTPException(503,'Application checklist is unavailable')
        slots={d.slot for d in db.scalars(select(Document).where(Document.case_id==cid))}
        missing=set(definitions[c.kind]['slots'])-slots
        if missing: raise HTTPException(422,'Missing required evidence: '+', '.join(sorted(missing)))
        if c.state=='draft':
            # Submission is a distinct event before the reusable route machine starts.
            if db.execute(update(Case).where(Case.id==cid,Case.version==body.version).values(state=c.route[0],version=body.version+1,entered=datetime.now(timezone.utc).isoformat(),due=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat())).rowcount!=1: raise HTTPException(409,'Case changed')
            audit(db,c,u,'application_submitted','Completeness passed; human review required. '+c.rule_version)
            db.add(Notice(case_id=cid,recipient='reviewer',message='New application ready for review',level='info',dedup=f'submit:{cid}'))
            db.flush(); db.refresh(c)
        else: move(db,c,u,'scrutiny',body.version,'Institution resubmitted evidence for review')
        return serial(c)
    @app.post('/api/applications/{cid}/transition')
    def transition(cid:str,body:Action,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db); reviewer(c,u)
        if body.target in ['approved','rejected'] and not has_membership(u,'regional_officer',region=c.region): raise HTTPException(403,'Demo decision authority required')
        if not body.reason.strip(): raise HTTPException(422,'Record review findings / reasons')
        if c.state=='evc' and body.target=='decision':
            if not c.schedule or not c.report.strip(): raise HTTPException(422,'EVC schedule and report required')
            participants=list(db.scalars(select(EvcParticipant).where(EvcParticipant.case_id==cid,EvcParticipant.active==True)))
            accepted=[p for p in participants if p.status=='accepted' and p.conflict_status!='declared']
            if len(accepted)<2: raise HTTPException(422,'EVC quorum requires two accepted, conflict-free members')
        return serial(move(db,c,u,body.target,body.version,body.reason))
    @app.post('/api/applications/{cid}/findings')
    def create_finding(cid:str,body:FindingCreate,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if not has_membership(u,'scrutiny_officer',region=c.region) or c.owner!=u.id: raise HTTPException(403,'Assigned scrutiny reviewer required')
        if c.state not in ['scrutiny','correction']: raise HTTPException(409,'Findings are only recorded during scrutiny')
        finding=Finding(case_id=cid,description=body.description.strip(),created_by=u.id)
        db.add(finding); audit(db,c,u,'finding_created',body.description.strip()); db.flush()
        return serial(finding)
    @app.post('/api/findings/{fid}/response')
    def respond_finding(fid:int,body:FindingResponse,u=Depends(current),db=Depends(db_session)):
        finding=db.get(Finding,fid)
        if not finding: raise HTTPException(404,'Finding not found')
        c=case_for(finding.case_id,u,db)
        if not has_membership(u,'institution',institution=c.institution): raise HTTPException(403,'Institution permission required')
        if finding.status!='open': raise HTTPException(409,'Finding is not awaiting a response')
        if db.execute(update(Finding).where(Finding.id==fid,Finding.version==body.version,Finding.status=='open').values(response=body.response.strip(),status='responded',version=body.version+1,responded=datetime.now(timezone.utc).isoformat())).rowcount!=1: raise HTTPException(409,'Finding changed; refresh')
        audit(db,c,u,'finding_responded',f'Finding {fid}: {body.response.strip()}'); db.flush(); db.refresh(finding)
        return serial(finding)
    @app.post('/api/findings/{fid}/close')
    def close_finding(fid:int,body:FindingClose,u=Depends(current),db=Depends(db_session)):
        finding=db.get(Finding,fid)
        if not finding: raise HTTPException(404,'Finding not found')
        c=case_for(finding.case_id,u,db)
        if not has_membership(u,'scrutiny_officer',region=c.region) or c.owner!=u.id: raise HTTPException(403,'Assigned scrutiny reviewer required')
        if finding.status!='responded': raise HTTPException(409,'Finding requires an institutional response')
        if db.execute(update(Finding).where(Finding.id==fid,Finding.version==body.version,Finding.status=='responded').values(status='closed',version=body.version+1,closed=datetime.now(timezone.utc).isoformat())).rowcount!=1: raise HTTPException(409,'Finding changed; refresh')
        audit(db,c,u,'finding_closed',f'Finding {fid} closed after institutional response'); db.flush(); db.refresh(finding)
        return serial(finding)
    @app.post('/api/applications/{cid}/evc')
    def evc(cid:str,body:Schedule,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if not has_membership(u,'regional_officer',region=c.region) or c.state!='evc': raise HTTPException(403,'Regional coordinator required at EVC stage')
        date=utc(body.date).isoformat()
        if db.execute(update(Case).where(Case.id==cid,Case.version==body.version).values(schedule=date,report=body.report,version=body.version+1)).rowcount!=1: raise HTTPException(409,'Case changed')
        audit(db,c,u,'evc_updated',f'Schedule {date}; report: {body.report}')
        db.add(Notice(case_id=cid,recipient='institution',message=f'EVC schedule updated: {date}',level='info',dedup=f'evc:{cid}:{body.version}'))
        return {'ok':True}
    @app.get('/api/applications/{cid}/evc/participants')
    def evc_participants(cid:str,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if not (has_membership(u,'regional_officer',region=c.region) or u.id==c.owner or has_membership(u,'institution',institution=c.institution)):
            raise HTTPException(403,'EVC participant permission required')
        return [serial(p) for p in db.scalars(select(EvcParticipant).where(EvcParticipant.case_id==cid).order_by(EvcParticipant.id))]
    @app.post('/api/applications/{cid}/evc/participants')
    def add_evc_participant(cid:str,body:ParticipantAdd,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if not has_membership(u,'regional_officer',region=c.region): raise HTTPException(403,'Regional coordinator required')
        member=db.get(User,body.member_id)
        if not member or not has_membership(member,'stage_member',region=c.region): raise HTTPException(422,'Choose an eligible EVC stage member')
        if db.scalar(select(EvcParticipant).where(EvcParticipant.case_id==cid,EvcParticipant.member_id==member.id,EvcParticipant.active==True)):
            raise HTTPException(409,'EVC member is already assigned')
        participant=EvcParticipant(case_id=cid,member_id=member.id,assigned_by=u.id)
        db.add(participant); audit(db,c,u,'evc_member_assigned',f'{member.id} assigned to EVC'); db.flush()
        return serial(participant)
    @app.post('/api/evc-participants/{pid}/respond')
    def respond_evc_participant(pid:int,body:ParticipantAction,u=Depends(current),db=Depends(db_session)):
        participant=db.get(EvcParticipant,pid)
        if not participant: raise HTTPException(404,'EVC participant not found')
        c=db.get(Case,participant.case_id)
        if not c: raise HTTPException(404,'Application not found')
        if participant.member_id!=u.id or not has_membership(u,'stage_member',region=c.region): raise HTTPException(403,'Assigned EVC member required')
        if body.status not in ['accepted','declined']: raise HTTPException(422,'Participant status must be accepted or declined')
        if participant.conflict_status=='declared': raise HTTPException(409,'Conflicted member cannot accept an EVC assignment')
        if db.execute(update(EvcParticipant).where(EvcParticipant.id==pid,EvcParticipant.version==body.version,EvcParticipant.active==True).values(status=body.status,version=body.version+1)).rowcount!=1: raise HTTPException(409,'Participant assignment changed; refresh')
        audit(db,c,u,'evc_member_response',f'{body.status}: {body.reason.strip()}'); db.flush(); db.refresh(participant)
        return serial(participant)
    @app.post('/api/evc-participants/{pid}/conflict')
    def evc_conflict(pid:int,body:Conflict,u=Depends(current),db=Depends(db_session)):
        participant=db.get(EvcParticipant,pid)
        if not participant: raise HTTPException(404,'EVC participant not found')
        c=db.get(Case,participant.case_id)
        if not c: raise HTTPException(404,'Application not found')
        if participant.member_id!=u.id or not has_membership(u,'stage_member',region=c.region): raise HTTPException(403,'Assigned EVC member required')
        if body.status not in ['declared','cleared']: raise HTTPException(422,'Conflict status must be declared or cleared')
        if body.status=='declared' and len(body.reason.strip())<5: raise HTTPException(422,'Provide a conflict reason')
        if db.execute(update(EvcParticipant).where(EvcParticipant.id==pid,EvcParticipant.version==participant.version).values(conflict_status=body.status,conflict_reason=body.reason.strip(),status='declined' if body.status=='declared' else participant.status,version=participant.version+1)).rowcount!=1: raise HTTPException(409,'Participant assignment changed; refresh')
        audit(db,c,u,'evc_conflict_updated',f'{body.status}: {body.reason.strip()}'); db.flush(); db.refresh(participant)
        return serial(participant)
    @app.get('/api/reviewers')
    def reviewers(case_id:str,u=Depends(current),db=Depends(db_session)):
        c=case_for(case_id,u,db)
        if not has_membership(u,'regional_officer',region=c.region): raise HTTPException(403,'Regional coordinator required')
        reviewer_ids=select(RoleMembership.user_id).where(
            RoleMembership.role=='scrutiny_officer',
            RoleMembership.region==c.region,
            RoleMembership.active.is_(True),
        )
        users=list(db.scalars(select(User).where(User.id.in_(reviewer_ids))))
        return [{**serial(r),'open_cases':len(list(db.scalars(select(Case).where(Case.owner==r.id,Case.state.not_in(['approved','rejected'])))))} for r in users]
    @app.post('/api/applications/{cid}/assign')
    def assign(cid:str,body:Assign,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if not has_membership(u,'regional_officer',region=c.region): raise HTTPException(403,'Regional coordinator required')
        if c.state in ['approved','rejected']: raise HTTPException(409,'Closed application cannot be reassigned')
        if len(body.reason.strip())<5: raise HTTPException(422,'Provide a meaningful assignment reason')
        r=db.get(User,body.reviewer_id)
        if not r or not has_membership(r,'scrutiny_officer',region=c.region): raise HTTPException(422,'Choose an eligible reviewer in the originating region')
        if db.scalar(select(Assignment).where(Assignment.case_id==cid,Assignment.reviewer_id==r.id,Assignment.active==True,Assignment.conflict_status=='declared')):
            raise HTTPException(409,'Reviewer has a declared conflict for this application')
        previous=c.owner
        if previous==r.id: raise HTTPException(409,'Reviewer is already assigned')
        if db.execute(update(Case).where(Case.id==cid,Case.version==body.version).values(owner=r.id,version=body.version+1)).rowcount!=1: raise HTTPException(409,'Case changed; refresh')
        db.query(Assignment).filter(Assignment.case_id==cid,Assignment.active==True).update({'active':False,'ended':datetime.now(timezone.utc).isoformat()},synchronize_session=False)
        db.add(Assignment(case_id=cid,reviewer_id=r.id,assigned_by=u.id,reason=body.reason.strip()))
        audit(db,c,u,'reviewer_assigned',f'{previous} → {r.id}; reason: {body.reason}')
        db.add(Notice(case_id=cid,recipient='reviewer',message=f'Reviewer assignment changed to {r.name}',level='info',dedup=f'assignment:{cid}:{body.version}'))
        return {'ok':True}
    @app.get('/api/applications/{cid}/assignments')
    def assignments(cid:str,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if not (has_membership(u,'regional_officer',region=c.region) or u.id==c.owner or has_membership(u,'institution',institution=c.institution)):
            raise HTTPException(403,'Assignment history permission required')
        return [serial(a) for a in db.scalars(select(Assignment).where(Assignment.case_id==cid).order_by(Assignment.id))]
    @app.post('/api/applications/{cid}/conflict')
    def declare_conflict(cid:str,body:Conflict,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if u.id!=c.owner or not has_membership(u,'scrutiny_officer',region=c.region):
            raise HTTPException(403,'Assigned scrutiny reviewer required')
        if body.status not in ['declared','cleared']: raise HTTPException(422,'Conflict status must be declared or cleared')
        if body.status=='declared' and len(body.reason.strip())<5: raise HTTPException(422,'Provide a conflict reason')
        assignment=db.scalar(select(Assignment).where(Assignment.case_id==cid,Assignment.reviewer_id==u.id,Assignment.active==True))
        if not assignment: raise HTTPException(409,'No active assignment exists')
        assignment.conflict_status=body.status
        assignment.conflict_reason=body.reason.strip()
        audit(db,c,u,'conflict_updated',f'{body.status}: {body.reason.strip()}')
        db.flush()
        return serial(assignment)
    @app.post('/api/obligations/{oid}/files')
    async def obligation_file(oid:int,version:int=Form(...),file:UploadFile=File(...),u=Depends(current),db=Depends(db_session)):
        o=db.get(Obligation,oid)
        if not o: raise HTTPException(404)
        c=case_for(o.case_id,u,db)
        if not has_membership(u,'institution',institution=c.institution): raise HTTPException(403,'Institution permission required')
        data,content_type,filename=await read_upload(file)
        if db.execute(update(Obligation).where(Obligation.id==oid,Obligation.version==version).values(status='pending',evidence='',proposed_expiry='',review_note='',verified_by='',verified_at='',requires_replacement=False,version=version+1)).rowcount!=1: raise HTTPException(409,'Obligation changed; refresh')
        slot=f'obligation:{oid}'
        prior=list(db.scalars(select(Document).where(Document.case_id==c.id,Document.slot==slot)))
        extracted=data.decode('utf-8') if content_type=='text/plain' else ''
        doc=Document(case_id=c.id,slot=slot,filename=filename,content_type=content_type,size=len(data),content=base64.b64encode(data).decode(),sha256=hashlib.sha256(data).hexdigest(),revision=len(prior)+1,processing_status='extracted' if extracted else 'pending',extracted_text=extracted)
        db.add(doc)
        audit(db,c,u,'compliance_file_uploaded',f'{o.title}; revision {doc.revision}; sha256 {doc.sha256}; submission still required')
        db.flush();return serial(doc)
    @app.get('/api/obligations')
    def obligations(u=Depends(current),db=Depends(db_session)):
        ids=[c.id for c in db.scalars(select(Case)) if permitted(c,u)]
        return [{**serial(o),'files':[serial(d) for d in db.scalars(select(Document).where(Document.case_id==o.case_id,Document.slot==f'obligation:{o.id}').order_by(Document.id))]} for o in db.scalars(select(Obligation).where(Obligation.case_id.in_(ids)))]
    @app.post('/api/obligations/{oid}/evidence')
    def evidence(oid:int,body:Evidence,u=Depends(current),db=Depends(db_session)):
        o=db.get(Obligation,oid)
        if not o: raise HTTPException(404)
        c=case_for(o.case_id,u,db)
        if not has_membership(u,'institution',institution=c.institution): raise HTTPException(403,'Institution permission required')
        if len(body.evidence.strip())<5: raise HTTPException(422,'Provide a meaningful evidence description')
        if o.requires_replacement: raise HTTPException(422,'Upload replacement evidence before resubmitting')
        if not db.scalar(select(Document).where(Document.case_id==c.id,Document.slot==f'obligation:{oid}')): raise HTTPException(422,'Upload the supporting evidence file before submitting')
        expiry=utc(body.expiry).isoformat() if o.kind=='document' else ''
        if expiry and utc(expiry)<=datetime.now(timezone.utc): raise HTTPException(422,'Renewal expiry must be in the future')
        if o.status not in ['pending','clarification','rejected']: raise HTTPException(409,'Obligation is not awaiting institutional evidence')
        if db.execute(update(Obligation).where(Obligation.id==oid,Obligation.version==body.version).values(evidence=body.evidence,proposed_expiry=expiry,status='submitted',review_note='',version=body.version+1)).rowcount!=1: raise HTTPException(409,'Obligation changed')
        audit(db,c,u,'compliance_submitted',f'{o.title}: {body.evidence}; proposed expiry {expiry}; awaiting official verification'); return {'ok':True}
    @app.post('/api/obligations/{oid}/verify')
    def verify(oid:int,body:Verify,u=Depends(current),db=Depends(db_session)):
        o=db.get(Obligation,oid)
        if not o: raise HTTPException(404)
        c=case_for(o.case_id,u,db); reviewer(c,u)
        if o.status!='submitted' or not o.evidence: raise HTTPException(409,'Evidence must first be submitted')
        if o.kind=='document' and utc(o.proposed_expiry)<=datetime.now(timezone.utc): raise HTTPException(422,'Proposed expiry has passed')
        values={'status':'verified','version':body.version+1}
        if o.kind=='document': values['due']=o.proposed_expiry
        if db.execute(update(Obligation).where(Obligation.id==oid,Obligation.version==body.version).values(**values)).rowcount!=1: raise HTTPException(409,'Obligation changed')
        o.verified_by=u.id
        o.verified_at=datetime.now(timezone.utc).isoformat()
        db.add(Audit(case_id=c.id,actor=u.id,action='compliance_verified',detail=f'{o.title}; verified by {u.id} at {o.verified_at}'))
        return {'ok':True}
    @app.post('/api/obligations/{oid}/review')
    def review_obligation(oid:int,body:ComplianceReview,u=Depends(current),db=Depends(db_session)):
        o=db.get(Obligation,oid)
        if not o: raise HTTPException(404)
        c=case_for(o.case_id,u,db)
        reviewer(c,u)
        if o.status!='submitted': raise HTTPException(409,'Only submitted evidence can be returned for clarification')
        if db.execute(update(Obligation).where(Obligation.id==oid,Obligation.version==body.version).values(status='clarification',review_note=body.reason.strip(),requires_replacement=True,version=body.version+1)).rowcount!=1: raise HTTPException(409,'Obligation changed')
        audit(db,c,u,'compliance_clarification_requested',f'{o.title}: {body.reason.strip()}')
        db.flush(); db.refresh(o)
        return serial(o)
    @app.get('/api/notifications')
    def notifications(u=Depends(current),db=Depends(db_session)):
        ids=[c.id for c in db.scalars(select(Case)) if permitted(c,u)]
        notices=db.scalars(select(Notice).where(Notice.case_id.in_(ids)).order_by(Notice.id.desc()))
        return [serial(n) for n in notices if not has_membership(u,'institution') or n.recipient=='institution']
    @app.post('/api/notifications/{nid}/retry')
    def retry_notification(nid:int,u=Depends(current),db=Depends(db_session)):
        if not has_membership(u,'national_admin'): raise HTTPException(403,'National oversight permission required')
        notice=db.get(Notice,nid)
        if not notice: raise HTTPException(404,'Notification not found')
        if notice.status!='failed': raise HTTPException(409,'Only failed notifications can be retried')
        notice.status='delivered'
        notice.attempts+=1
        notice.last_error=''
        notice.delivered_at=datetime.now(timezone.utc).isoformat()
        case=db.get(Case,notice.case_id)
        if case: audit(db,case,u,'notification_retried',f'Notification {nid}; simulated delivery attempt {notice.attempts}')
        db.flush()
        return serial(notice)
    @app.post('/api/alerts/sweep')
    def alerts(u=Depends(current),db=Depends(db_session)):
        if not has_membership(u,'national_admin'): raise HTTPException(403,'National oversight permission required')
        return {'created':sweep(db),'delivery':'simulated'}
    static=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../frontend/dist'))
    if os.path.isdir(static): app.mount('/',StaticFiles(directory=static,html=True),name='frontend')
    return app

def seed(db):
    if not db.get(RuleSet,VERSION):
        db.add(RuleSet(version=VERSION,status='published',source=SOURCE,effective_from='2026-01-01T00:00:00+00:00',definitions=RULES))
    if db.get(User,'college-west'):
        if not db.get(User,'officer-west-2'):
            db.add(User(id='officer-west-2',name='Dr. Kavya Rao',role='scrutiny_officer',region='West Demo',institution='',password=hash_password(DEMO_PASSWORD)))
        users=list(db.scalars(select(User)))
        for user in users:
            if not user.memberships:
                db.add(RoleMembership(user_id=user.id,role=user.role,region=user.region,institution=user.institution))
        return
    if os.getenv('DEMO_MODE','true')!='true': raise RuntimeError('This release supports DEMO_MODE=true only')
    for id,name,role,region,inst in [
        ('college-west','Ananya Deshmukh','institution','West Demo','Pune Demo Institute'),
        ('college-east','Ravi Sen','institution','East Demo','Eastern Demo Institute'),
        ('officer-west','Dr. Meera Joshi','scrutiny_officer','West Demo',''),
        ('officer-west-2','Dr. Kavya Rao','scrutiny_officer','West Demo',''),
        ('officer-east','Dr. Arun Sen','scrutiny_officer','East Demo',''),
        ('regional-west','Priya Shah','regional_officer','West Demo',''),
        ('evc-west-1','EVC Member One','stage_member','West Demo',''),
        ('evc-west-2','EVC Member Two','stage_member','West Demo',''),
        ('admin','National oversight','national_admin','','')]:
        db.add(User(id=id,name=name,role=role,region=region,institution=inst,password=hash_password(DEMO_PASSWORD)))
        db.add(RoleMembership(user_id=id,role=role,region=region,institution=inst))
    stamp=datetime.now(timezone.utc)
    for id,kind,state,offset in [('APP-DEMO-0402','new_course','scrutiny',2),('APP-DEMO-0398','eoa','decision',-9),('APP-DEMO-0310','eoa','approved',7)]:
        c=Case(id=id,institution='Pune Demo Institute',region='West Demo',kind=kind,state=state,route=RULES[kind]['route'],rule_version=VERSION,owner='officer-west',entered=(stamp-timedelta(days=8)).isoformat(),due=(stamp+timedelta(days=offset)).isoformat(),submit_key='seed:'+id)
        db.add(c); db.flush()
        db.add(Assignment(case_id=id,reviewer_id='officer-west',assigned_by='system',reason='Synthetic initial assignment'))
        if id=='APP-DEMO-0402':
            db.add_all([
                EvcParticipant(case_id=id,member_id='evc-west-1',assigned_by='system',status='accepted'),
                EvcParticipant(case_id=id,member_id='evc-west-2',assigned_by='system',status='accepted'),
            ])
        db.add(Audit(case_id=id,actor='system',action='synthetic_seed',detail='Fictional demonstration record; unverified APH mapping'))
    c=Case(id='APP-EAST-0100',institution='Eastern Demo Institute',region='East Demo',kind='eoa',state='scrutiny',route=RULES['eoa']['route'],rule_version=VERSION,owner='officer-east',due=(stamp+timedelta(days=2)).isoformat(),submit_key='seed:east')
    db.add(c); db.flush()
    db.add_all([Obligation(case_id='APP-DEMO-0310',kind='undertaking',title='Submit annual compliance declaration',due=(stamp-timedelta(days=10)).isoformat()),Obligation(case_id='APP-DEMO-0310',kind='document',title='Lease evidence renewal',due=(stamp+timedelta(days=2)).isoformat())])

app=create_app()
