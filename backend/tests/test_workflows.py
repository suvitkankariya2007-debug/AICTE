import io
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.db import Case, Audit, Obligation, Notice, RoleMembership
from app.engine import sweep
from sqlalchemy import select
from app.config import load_settings

@pytest.fixture
def client(tmp_path):
    app=create_app('sqlite:///'+str(tmp_path/'test.db'))
    with TestClient(app) as c: yield c

def login(c,name):
    r=c.post('/api/login',json={'username':name,'password':'DemoPass!2026'}); assert r.status_code==200; return r.json()
def create(c,kind='eoa',key='test-request-001'):
    r=c.post('/api/applications',json={'kind':kind,'idempotency_key':key});assert r.status_code==200; return r.json()
def detail(c,id): return c.get('/api/applications/'+id).json()
def action(c,case,target,reason='Evidence reviewed; demo recommendation recorded'):
    return c.post('/api/applications/'+case['id']+'/transition',json={'target':target,'version':case['version'],'reason':reason})
def upload(c,id,slot,data=b'Demo declaration',mime='text/plain'):
    case=detail(c,id)
    return c.post('/api/applications/'+id+'/documents',data={'slot':slot,'version':case['version']},files={'file':('evidence.txt',data,mime)})

def test_auth_and_scope(client):
    c=client
    assert c.get('/api/applications').status_code==401
    assert c.post('/api/login',json={'username':'admin','password':'wrong'}).status_code==401
    login(c,'college-east')
    roles=c.get('/api/me/roles')
    assert roles.status_code==200
    assert roles.json()[0]['role']=='institution'
    assert [x['id'] for x in c.get('/api/applications').json()]==['APP-EAST-0100']
    assert c.get('/api/applications/APP-DEMO-0402').status_code==404
    assert c.post('/api/alerts/sweep').status_code==403
    assert c.post('/api/applications',json={'kind':'eoa','idempotency_key':'12345678','role':'admin'}).status_code==422
    assert c.post('/api/logout').status_code==200
    assert c.get('/api/me').status_code==401

def test_cookie_security_uses_validated_settings(tmp_path,monkeypatch):
    monkeypatch.setenv('COOKIE_SECURE','true')
    app=create_app('sqlite:///'+str(tmp_path/'secure.db'))
    with TestClient(app) as c:
        response=c.post('/api/login',json={'username':'admin','password':'DemoPass!2026'})
        assert 'Secure' in response.headers['set-cookie']

def test_inactive_membership_cannot_authorize_actions(client):
    login(client,'college-west')
    with client.app.state.factory.begin() as db:
        membership=db.scalar(select(RoleMembership).where(
            RoleMembership.user_id=='college-west',
            RoleMembership.role=='institution',
        ))
        membership.active=False
    assert client.get('/api/applications').status_code==200
    assert client.post('/api/applications',json={'kind':'eoa','idempotency_key':'inactive-001'}).status_code==403

def test_request_correlation_and_health(client):
    response=client.get('/api/health',headers={'X-Request-ID':'test-request-id'})
    assert response.status_code==200
    assert response.headers['X-Request-ID']=='test-request-id'
    assert response.headers['Cache-Control']=='no-store'
    invalid=client.get('/api/health',headers={'X-Request-ID':'bad\nrequest'})
    assert invalid.status_code==200
    assert invalid.headers['X-Request-ID']!='bad\nrequest'

def test_settings_reject_invalid_values(monkeypatch):
    monkeypatch.setenv('DATABASE_URL','mysql://localhost/aicte')
    with pytest.raises(ValueError,match='DATABASE_URL'):
        load_settings()

def test_checklists_and_idempotency(client):
    c=client;login(c,'college-west')
    rules=c.get('/api/rules').json();assert len({tuple(x['slots']) for x in rules['types'].values()})==3
    a=create(c);assert create(c)['id']==a['id']
    assert c.post('/api/applications',json={'kind':'new_course','idempotency_key':'test-request-001'}).status_code==409
    assert c.post('/api/applications/'+a['id']+'/submit',json={'version':1}).status_code==422
    assert upload(c,a['id'],'Unknown').status_code==422
    assert upload(c,a['id'],detail(c,a['id'])['slots'][0],b'bad','application/pdf').status_code==422

def test_full_correction_and_decision(client):
    c=client; login(c,'college-west');a=create(c);id=a['id']
    for slot in detail(c,id)['slots']:assert upload(c,id,slot).status_code==200
    old=detail(c,id);r=c.post('/api/applications/'+id+'/submit',json={'version':old['version']});assert r.status_code==200
    assert action(c,r.json(),'decision').status_code==403
    login(c,'officer-west');case=detail(c,id)
    assert action(c,case,'approved').status_code==403
    assert action(c,case,'evc').status_code==409 # EOA route excludes EVC
    assert action(c,case,'correction','').status_code==422
    assert action(c,case,'correction').status_code==200
    assert action(c,case,'decision').status_code==409 # stale version
    login(c,'college-west');assert upload(c,id,'Prior approval',b'Corrected document').status_code==200
    a=detail(c,id);assert len([d for d in a['documents'] if d['slot']=='Prior approval'])==2
    assert c.post('/api/applications/'+id+'/submit',json={'version':a['version']}).status_code==200
    login(c,'officer-west');assert action(c,detail(c,id),'decision').status_code==200
    assert action(c,detail(c,id),'approved').status_code==403
    login(c,'regional-west');assert action(c,detail(c,id),'approved').status_code==200
    final=detail(c,id);assert final['state']=='approved';assert len(final['audit'])>=8
    assert action(c,final,'scrutiny').status_code==409
    login(c,'college-east');assert c.get('/api/documents/'+str(final['documents'][0]['id'])).status_code==404

def test_evc_gates(client):
    c=client;login(c,'officer-west');a=detail(c,'APP-DEMO-0402');assert action(c,a,'evc').status_code==200
    a=detail(c,a['id']);assert action(c,a,'decision').status_code==422
    assert c.post('/api/applications/'+a['id']+'/evc',json={'version':a['version'],'date':'2026-12-01T10:00:00Z','report':'Report recorded'}).status_code==403
    login(c,'regional-west');a=detail(c,a['id'])
    assert c.post('/api/applications/'+a['id']+'/evc',json={'version':a['version'],'date':'2026-12-01T10:00:00Z','report':'Report recorded'}).status_code==200
    assert action(c,detail(c,a['id']),'decision').status_code==200

def test_obligation_verification_and_expiry(client):
    c=client;login(c,'regional-west');obs=c.get('/api/obligations').json();doc=next(o for o in obs if o['kind']=='document')
    assert c.post(f"/api/obligations/{doc['id']}/verify",json={'version':doc['version']}).status_code==409
    login(c,'college-west');future=(datetime.now(timezone.utc)+timedelta(days=730)).isoformat()
    r=c.post(f"/api/obligations/{doc['id']}/files",data={'version':doc['version']},files={'file':('renewal.txt',b'Renewed lease evidence','text/plain')});assert r.status_code==200
    doc=next(o for o in c.get('/api/obligations').json() if o['id']==doc['id'])
    data={'version':doc['version'],'evidence':'Lease renewal reference DEMO-2026','expiry':future}
    assert c.post(f"/api/obligations/{doc['id']}/evidence",json=data).status_code==200
    changed=next(o for o in c.get('/api/obligations').json() if o['id']==doc['id'])
    assert changed['status']=='submitted';assert changed['due']==doc['due']
    assert c.post(f"/api/obligations/{doc['id']}/verify",json={'version':changed['version']}).status_code==403
    login(c,'regional-west');assert c.post(f"/api/obligations/{doc['id']}/verify",json={'version':changed['version']}).status_code==200
    updated=next(o for o in c.get('/api/obligations').json() if o['id']==doc['id']);assert updated['due']==future

def test_sweep_dedup_and_renewed_document_monitoring(client):
    c=client;login(c,'admin');first=c.post('/api/alerts/sweep').json();assert first['created']>0
    assert c.post('/api/alerts/sweep').json()['created']==0
    with c.app.state.factory.begin() as db:
        o=db.scalar(select(Obligation).where(Obligation.kind=='document'));o.status='verified'
        n=sweep(db,datetime.now(timezone.utc)+timedelta(days=30));assert n>0
    assert any(n['level']=='escalated' for n in c.get('/api/notifications').json())

def test_transaction_rollback(client):
    c=client;login(c,'officer-west');before=detail(c,'APP-DEMO-0402')
    assert action(c,before,'invented_stage').status_code==409
    after=detail(c,before['id']);assert before['version']==after['version'];assert len(before['audit'])==len(after['audit'])

def test_csrf_and_session(client):
    c=client;login(c,'admin')
    assert c.post('/api/alerts/sweep',headers={'Origin':'https://attacker.example'}).status_code==403
    assert c.get('/api/me').json()['role']=='national_admin'
    assert 'HttpOnly' in c.post('/api/login',json={'username':'admin','password':'DemoPass!2026'}).headers['set-cookie']

def test_two_sessions_and_restart(tmp_path):
    url='sqlite:///'+str(tmp_path/'persistent.db')
    app=create_app(url)
    with TestClient(app) as college, TestClient(app) as officer:
        login(college,'college-west');login(officer,'officer-west')
        before=detail(college,'APP-DEMO-0402')
        assert action(officer,detail(officer,before['id']),'correction').status_code==200
        assert detail(college,before['id'])['state']=='correction'
    with TestClient(create_app(url)) as restarted:
        login(restarted,'college-west');assert detail(restarted,'APP-DEMO-0402')['state']=='correction'

def test_concurrent_transition_only_one_wins(client):
    login(client,'officer-west');before=detail(client,'APP-DEMO-0402')
    # Independent HTTP sessions share one DB, both act on the same revision.
    def perform(_): return action(client,before,'correction').status_code
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(perform,range(2)))
    assert sorted(results)==[200,409]
    after=detail(client,before['id']);assert after['version']==before['version']+1
    assert sum(x['action']=='stage_changed' for x in after['audit'])==1
    assert 'scrutiny → correction' in after['audit'][0]['detail']

def test_assignment_changes_access_and_preserves_region(client):
    c=client;login(c,'regional-west');case=detail(c,'APP-DEMO-0402')
    choices=c.get('/api/reviewers',params={'case_id':case['id']}).json()
    assert {u['id'] for u in choices}=={'officer-west','officer-west-2'}
    base={'version':case['version'],'reviewer_id':'officer-east','reason':'Workload balancing'}
    assert c.post('/api/applications/'+case['id']+'/assign',json=base).status_code==422
    base['reviewer_id']='officer-west-2'
    assert c.post('/api/applications/'+case['id']+'/assign',json=base).status_code==200
    assert c.post('/api/applications/'+case['id']+'/assign',json=base).status_code==409
    assert detail(c,case['id'])['region']==case['region']
    login(c,'officer-west');assert c.get('/api/applications/'+case['id']).status_code==404
    login(c,'officer-west-2');assert detail(c,case['id'])['owner']=='officer-west-2'
    assert c.post('/api/applications/'+case['id']+'/assign',json=base).status_code==403
    assert any(a['action']=='reviewer_assigned' for a in detail(c,case['id'])['audit'])

def test_compliance_files_versions_and_isolation(client):
    c=client;login(c,'college-west');o=c.get('/api/obligations').json()[0]
    payload={'version':o['version'],'evidence':'Evidence description'}
    assert c.post(f"/api/obligations/{o['id']}/evidence",json=payload).status_code==422
    for n in range(2):
        o=next(x for x in c.get('/api/obligations').json() if x['id']==o['id'])
        assert c.post(f"/api/obligations/{o['id']}/files",data={'version':o['version']},files={'file':('proof.txt',f'proof revision {n}'.encode(),'text/plain')}).status_code==200
    o=next(x for x in c.get('/api/obligations').json() if x['id']==o['id'])
    assert len(o['files'])==2;assert o['status']=='pending'
    assert c.post(f"/api/obligations/{o['id']}/evidence",json={'version':o['version'],'evidence':'Uploaded corrected evidence'}).status_code==200
    login(c,'college-east');assert c.get('/api/documents/'+str(o['files'][0]['id'])).status_code==404

def test_assignment_authority_and_meaningful_reason(client):
    c=client;login(c,'regional-west');a=detail(c,'APP-DEMO-0402')
    path='/api/applications/'+a['id']+'/assign'
    body={'version':a['version'],'reviewer_id':'officer-west-2','reason':'      '}
    assert c.post(path,json=body).status_code==422
    body['reason']='Balance workload'
    login(c,'admin');assert c.post(path,json=body).status_code==403
    login(c,'college-west');assert c.post(path,json=body).status_code==403
    login(c,'regional-west');closed=detail(c,'APP-DEMO-0310')
    assert c.post('/api/applications/'+closed['id']+'/assign',json={**body,'version':closed['version']}).status_code==409

def test_replacement_compliance_file_reopens_verification(client):
    c=client;login(c,'college-west');o=c.get('/api/obligations').json()[0]
    def current_obligation():return next(x for x in c.get('/api/obligations').json() if x['id']==o['id'])
    def file(v):return c.post(f"/api/obligations/{o['id']}/files",data={'version':v},files={'file':('proof.txt',b'New proof','text/plain')})
    assert file(o['version']).status_code==200
    o=current_obligation()
    assert c.post(f"/api/obligations/{o['id']}/evidence",json={'version':o['version'],'evidence':'      '}).status_code==422
    assert c.post(f"/api/obligations/{o['id']}/evidence",json={'version':o['version'],'evidence':'Original proof description'}).status_code==200
    login(c,'regional-west');o=current_obligation()
    assert c.post(f"/api/obligations/{o['id']}/verify",json={'version':o['version']}).status_code==200
    login(c,'college-west');o=current_obligation();assert file(o['version']).status_code==200
    changed=current_obligation();assert changed['status']=='pending';assert changed['evidence']=='';assert len(changed['files'])==2
    login(c,'regional-west');assert c.post(f"/api/obligations/{o['id']}/verify",json={'version':changed['version']}).status_code==409
