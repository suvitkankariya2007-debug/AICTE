import logging, os, secrets, hashlib, hmac, base64, re, time, uuid
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Response, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from .db import Base, User, RoleMembership, LoginSession, Case, Document, Obligation, Audit, Notice, setup
from .rules import RULES, VERSION, SOURCE
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
class Verify(Strict): version:int
class Schedule(Strict): version:int; date:str; report:str=Field(default='',max_length=4000)

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
    def rules(u=Depends(current)): return {'version':VERSION,'source':SOURCE,'types':RULES}
    @app.get('/api/applications')
    def cases(u=Depends(current),db=Depends(db_session)):
        return [serial(c) for c in db.scalars(select(Case).order_by(Case.entered.desc())) if permitted(c,u)]
    @app.post('/api/applications')
    def create(body:Create,u=Depends(current),db=Depends(db_session)):
        if u.role!='institution': raise HTTPException(403,'Institution permission required')
        if body.kind not in RULES: raise HTTPException(422,'Unknown application type')
        key=u.id+':'+body.idempotency_key
        prior=db.scalar(select(Case).where(Case.submit_key==key))
        if prior:
            if prior.kind!=body.kind: raise HTTPException(409,'Idempotency key belongs to another request')
            return serial(prior)
        c=Case(id='APP-'+secrets.token_hex(4).upper(),institution=u.institution,region=u.region,kind=body.kind,state='draft',route=RULES[body.kind]['route'],rule_version=VERSION,owner='officer-west' if u.region=='West Demo' else 'officer-east',due=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat(),submit_key=key)
        db.add(c); db.flush(); audit(db,c,u,'draft_created',SOURCE); return serial(c)
    @app.get('/api/applications/{cid}')
    def detail(cid:str,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        return {**serial(c),'documents':[serial(d) for d in db.scalars(select(Document).where(Document.case_id==cid).order_by(Document.id))],'obligations':[serial(o) for o in db.scalars(select(Obligation).where(Obligation.case_id==cid))],'audit':[serial(a) for a in db.scalars(select(Audit).where(Audit.case_id==cid).order_by(Audit.id.desc()))],'slots':RULES[c.kind]['slots']}
    @app.post('/api/applications/{cid}/documents')
    async def upload(cid:str,slot:str=Form(...),version:int=Form(...),file:UploadFile=File(...),u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if u.role!='institution' or c.state not in ['draft','correction']: raise HTTPException(403,'Uploads permitted only during draft/correction')
        if slot not in RULES[c.kind]['slots']: raise HTTPException(422,'Unknown checklist slot')
        data=await file.read(2*1024*1024+1)
        if not data or len(data)>2*1024*1024: raise HTTPException(422,'Upload must be between 1 byte and 2 MB')
        if not ((file.content_type=='application/pdf' and data.startswith(b'%PDF-')) or (file.content_type=='text/plain' and b'\x00' not in data)):
            raise HTTPException(422,'Demo accepts PDF or plain text evidence only')
        if db.execute(update(Case).where(Case.id==cid,Case.version==version).values(version=version+1)).rowcount!=1: raise HTTPException(409,'Case changed; refresh')
        docs=list(db.scalars(select(Document).where(Document.case_id==cid,Document.slot==slot)))
        name=re.sub(r'[^\w. -]','_',file.filename or 'evidence')[-120:]
        d=Document(case_id=cid,slot=slot,filename=name,content=base64.b64encode(data).decode(),sha256=hashlib.sha256(data).hexdigest(),revision=len(docs)+1)
        db.add(d); audit(db,c,u,'evidence_uploaded',f'{slot}; revision {d.revision}; sha256 {d.sha256}'); db.flush(); return serial(d)
    @app.get('/api/documents/{did}')
    def download(did:int,u=Depends(current),db=Depends(db_session)):
        d=db.get(Document,did)
        if not d: raise HTTPException(404)
        case_for(d.case_id,u,db)
        return Response(base64.b64decode(d.content),media_type='application/octet-stream',headers={'Content-Disposition':f'attachment; filename="{d.filename}"'})
    @app.post('/api/applications/{cid}/submit')
    def submit(cid:str,body:Verify,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if u.role!='institution' or c.state not in ['draft','correction']: raise HTTPException(403,'Not awaiting institutional submission')
        slots={d.slot for d in db.scalars(select(Document).where(Document.case_id==cid))}
        missing=set(RULES[c.kind]['slots'])-slots
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
        if body.target in ['approved','rejected'] and u.role!='regional_officer': raise HTTPException(403,'Demo decision authority required')
        if not body.reason.strip(): raise HTTPException(422,'Record review findings / reasons')
        if c.state=='evc' and body.target=='decision' and (not c.schedule or not c.report.strip()): raise HTTPException(422,'EVC schedule and report required')
        return serial(move(db,c,u,body.target,body.version,body.reason))
    @app.post('/api/applications/{cid}/evc')
    def evc(cid:str,body:Schedule,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if u.role!='regional_officer' or c.state!='evc': raise HTTPException(403,'Regional coordinator required at EVC stage')
        date=utc(body.date).isoformat()
        if db.execute(update(Case).where(Case.id==cid,Case.version==body.version).values(schedule=date,report=body.report,version=body.version+1)).rowcount!=1: raise HTTPException(409,'Case changed')
        audit(db,c,u,'evc_updated',f'Schedule {date}; report: {body.report}')
        db.add(Notice(case_id=cid,recipient='institution',message=f'EVC schedule updated: {date}',level='info',dedup=f'evc:{cid}:{body.version}'))
        return {'ok':True}
    @app.get('/api/reviewers')
    def reviewers(case_id:str,u=Depends(current),db=Depends(db_session)):
        c=case_for(case_id,u,db)
        if u.role!='regional_officer': raise HTTPException(403,'Regional coordinator required')
        users=list(db.scalars(select(User).where(User.role=='scrutiny_officer',User.region==c.region)))
        return [{**serial(r),'open_cases':len(list(db.scalars(select(Case).where(Case.owner==r.id,Case.state.not_in(['approved','rejected'])))))} for r in users]
    @app.post('/api/applications/{cid}/assign')
    def assign(cid:str,body:Assign,u=Depends(current),db=Depends(db_session)):
        c=case_for(cid,u,db)
        if u.role!='regional_officer': raise HTTPException(403,'Regional coordinator required')
        if c.state in ['approved','rejected']: raise HTTPException(409,'Closed application cannot be reassigned')
        if len(body.reason.strip())<5: raise HTTPException(422,'Provide a meaningful assignment reason')
        r=db.get(User,body.reviewer_id)
        if not r or r.role!='scrutiny_officer' or r.region!=c.region: raise HTTPException(422,'Choose an eligible reviewer in the originating region')
        previous=c.owner
        if previous==r.id: raise HTTPException(409,'Reviewer is already assigned')
        if db.execute(update(Case).where(Case.id==cid,Case.version==body.version).values(owner=r.id,version=body.version+1)).rowcount!=1: raise HTTPException(409,'Case changed; refresh')
        audit(db,c,u,'reviewer_assigned',f'{previous} → {r.id}; reason: {body.reason}')
        db.add(Notice(case_id=cid,recipient='reviewer',message=f'Reviewer assignment changed to {r.name}',level='info',dedup=f'assignment:{cid}:{body.version}'))
        return {'ok':True}
    @app.post('/api/obligations/{oid}/files')
    async def obligation_file(oid:int,version:int=Form(...),file:UploadFile=File(...),u=Depends(current),db=Depends(db_session)):
        o=db.get(Obligation,oid)
        if not o: raise HTTPException(404)
        c=case_for(o.case_id,u,db)
        if u.role!='institution': raise HTTPException(403,'Institution permission required')
        data=await file.read(2*1024*1024+1)
        if not data or len(data)>2*1024*1024: raise HTTPException(422,'Upload must be between 1 byte and 2 MB')
        if not ((file.content_type=='application/pdf' and data.startswith(b'%PDF-')) or (file.content_type=='text/plain' and b'\x00' not in data)):
            raise HTTPException(422,'Demo accepts PDF or plain text evidence only')
        if db.execute(update(Obligation).where(Obligation.id==oid,Obligation.version==version).values(status='pending',evidence='',proposed_expiry='',version=version+1)).rowcount!=1: raise HTTPException(409,'Obligation changed; refresh')
        slot=f'obligation:{oid}'
        prior=list(db.scalars(select(Document).where(Document.case_id==c.id,Document.slot==slot)))
        doc=Document(case_id=c.id,slot=slot,filename=re.sub(r'[^\w. -]','_',file.filename or 'evidence')[-120:],content=base64.b64encode(data).decode(),sha256=hashlib.sha256(data).hexdigest(),revision=len(prior)+1)
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
        if u.role!='institution': raise HTTPException(403,'Institution permission required')
        if len(body.evidence.strip())<5: raise HTTPException(422,'Provide a meaningful evidence description')
        if not db.scalar(select(Document).where(Document.case_id==c.id,Document.slot==f'obligation:{oid}')): raise HTTPException(422,'Upload the supporting evidence file before submitting')
        expiry=utc(body.expiry).isoformat() if o.kind=='document' else ''
        if expiry and utc(expiry)<=datetime.now(timezone.utc): raise HTTPException(422,'Renewal expiry must be in the future')
        if db.execute(update(Obligation).where(Obligation.id==oid,Obligation.version==body.version).values(evidence=body.evidence,proposed_expiry=expiry,status='submitted',version=body.version+1)).rowcount!=1: raise HTTPException(409,'Obligation changed')
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
        audit(db,c,u,'compliance_verified',o.title); return {'ok':True}
    @app.get('/api/notifications')
    def notifications(u=Depends(current),db=Depends(db_session)):
        ids=[c.id for c in db.scalars(select(Case)) if permitted(c,u)]
        notices=db.scalars(select(Notice).where(Notice.case_id.in_(ids)).order_by(Notice.id.desc()))
        return [serial(n) for n in notices if u.role!='institution' or n.recipient=='institution']
    @app.post('/api/alerts/sweep')
    def alerts(u=Depends(current),db=Depends(db_session)):
        if u.role!='national_admin': raise HTTPException(403,'National oversight permission required')
        return {'created':sweep(db),'delivery':'simulated'}
    static=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../frontend/dist'))
    if os.path.isdir(static): app.mount('/',StaticFiles(directory=static,html=True),name='frontend')
    return app

def seed(db):
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
        ('admin','National oversight','national_admin','','')]:
        db.add(User(id=id,name=name,role=role,region=region,institution=inst,password=hash_password(DEMO_PASSWORD)))
        db.add(RoleMembership(user_id=id,role=role,region=region,institution=inst))
    stamp=datetime.now(timezone.utc)
    for id,kind,state,offset in [('APP-DEMO-0402','new_course','scrutiny',2),('APP-DEMO-0398','eoa','decision',-9),('APP-DEMO-0310','eoa','approved',7)]:
        c=Case(id=id,institution='Pune Demo Institute',region='West Demo',kind=kind,state=state,route=RULES[kind]['route'],rule_version=VERSION,owner='officer-west',entered=(stamp-timedelta(days=8)).isoformat(),due=(stamp+timedelta(days=offset)).isoformat(),submit_key='seed:'+id)
        db.add(c); db.flush(); db.add(Audit(case_id=id,actor='system',action='synthetic_seed',detail='Fictional demonstration record; unverified APH mapping'))
    c=Case(id='APP-EAST-0100',institution='Eastern Demo Institute',region='East Demo',kind='eoa',state='scrutiny',route=RULES['eoa']['route'],rule_version=VERSION,owner='officer-east',due=(stamp+timedelta(days=2)).isoformat(),submit_key='seed:east')
    db.add(c); db.flush()
    db.add_all([Obligation(case_id='APP-DEMO-0310',kind='undertaking',title='Submit annual compliance declaration',due=(stamp-timedelta(days=10)).isoformat()),Obligation(case_id='APP-DEMO-0310',kind='document',title='Lease evidence renewal',due=(stamp+timedelta(days=2)).isoformat())])

app=create_app()
