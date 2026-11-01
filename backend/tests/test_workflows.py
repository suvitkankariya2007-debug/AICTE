import io
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.db import Case, Audit, Obligation, Notice, RoleMembership, WorkerHeartbeat
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
def upload(c,id,slot,data=b'Demo declaration',mime='text/plain',filename='evidence.txt'):
    case=detail(c,id)
    return c.post('/api/applications/'+id+'/documents',data={'slot':slot,'version':case['version']},files={'file':(filename,data,mime)})

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

def test_rule_registry_draft_publish_and_binding(client):
    login(client,'admin')
    definitions={
        'renewal_demo':{
            'label':'Renewal demo',
            'route':['scrutiny','decision'],
            'slots':['Renewal declaration'],
            'days':14,
        }
    }
    draft=client.post('/api/rules/drafts',json={
        'version':'DEMO-2026-v2',
        'source':'Illustrative test rule; NEEDS_APH_VERIFICATION',
        'effective_from':'2026-01-02T00:00:00Z',
        'definitions':definitions,
    })
    assert draft.status_code==200
    assert client.post('/api/rules/DEMO-2026-v2/publish').status_code==200
    login(client,'college-west')
    rules=client.get('/api/rules').json()
    assert rules['version']=='DEMO-2026-v2'
    case=create(client,'renewal_demo','rule-binding-001')
    assert case['rule_version']=='DEMO-2026-v2'
    assert case['route']==['scrutiny','decision']
    assert detail(client,case['id'])['slots']==['Renewal declaration']

def test_expanded_application_catalogue_has_tracks_and_checklists(client):
    login(client,'college-west')
    rules=client.get('/api/rules').json()
    assert len(rules['types'])==20
    assert {definition['track'] for definition in rules['types'].values()}=={
        'T1 · Heavy physical and legal verification',
        'T2 · Academic and programme modifications',
        'T3 · Routine and fast-track approvals',
        'T4 · Structural and administrative reorganisation',
    }
    assert rules['types']['online_odl']['slots']

def test_request_correlation_and_health(client):
    response=client.get('/api/health',headers={'X-Request-ID':'test-request-id'})
    assert response.status_code==200
    assert response.headers['X-Request-ID']=='test-request-id'
    assert response.headers['Cache-Control']=='no-store'
    invalid=client.get('/api/health',headers={'X-Request-ID':'bad\nrequest'})
    assert invalid.status_code==200
    assert invalid.headers['X-Request-ID']!='bad\nrequest'
    readiness=client.get('/api/health/ready')
    assert readiness.status_code==200
    assert readiness.json()['database']=='ok'
    assert readiness.json()['worker']['status']=='unknown'

def test_settings_reject_invalid_values(monkeypatch):
    monkeypatch.setenv('DATABASE_URL','mysql://localhost/aicte')
    with pytest.raises(ValueError,match='DATABASE_URL'):
        load_settings()
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://aicte:local-demo-only@db:5432/aicte')
    assert load_settings().database_url.startswith('postgresql+psycopg://')

def test_checklists_and_idempotency(client):
    c=client;login(c,'college-west')
    rules=c.get('/api/rules').json();assert len({tuple(x['slots']) for x in rules['types'].values()})==len(rules['types'])
    a=create(c);assert create(c)['id']==a['id']
    assert c.post('/api/applications',json={'kind':'new_course','idempotency_key':'test-request-001'}).status_code==409
    assert c.post('/api/applications/'+a['id']+'/submit',json={'version':1}).status_code==422
    assert upload(c,a['id'],'Unknown').status_code==422
    assert upload(c,a['id'],detail(c,a['id'])['slots'][0],b'bad','application/pdf').status_code==422

def test_document_metadata_and_safe_download_name(client):
    login(client,'college-west')
    case=create(client,key='metadata-001')
    uploaded=upload(client,case['id'],detail(client,case['id'])['slots'][0],b'plain evidence','text/plain','bad"name.txt')
    assert uploaded.status_code==200
    document=uploaded.json()
    assert document['content_type']=='text/plain'
    assert document['size']==len(b'plain evidence')
    downloaded=client.get('/api/documents/'+str(document['id']))
    assert downloaded.headers['content-type'].startswith('text/plain')
    assert re.fullmatch(
        r'attachment; filename="[A-Za-z0-9._ -]+"',
        downloaded.headers['content-disposition'],
    )

def test_document_extraction_requires_reviewer_and_manual_review(client):
    login(client,'college-west')
    case=create(client,key='extraction-001')
    uploaded=upload(client,case['id'],detail(client,case['id'])['slots'][0],b'Programme proposal text','text/plain','proposal.txt')
    document=uploaded.json()
    assert document['processing_status']=='extracted'
    assert document['extracted_text']=='Programme proposal text'
    assert client.post(f"/api/documents/{document['id']}/review",json={'version':1}).status_code==403
    login(client,'regional-west')
    processed=client.post(f"/api/documents/{document['id']}/process")
    assert processed.status_code==200
    reviewed=client.post(f"/api/documents/{document['id']}/review",json={'version':1})
    assert reviewed.status_code==200
    assert reviewed.json()['processing_status']=='reviewed'
    assert reviewed.json()['reviewed_by']=='regional-west'

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

def test_finding_response_and_closure(client):
    login(client,'officer-west-2')
    assert client.post('/api/applications/APP-DEMO-0402/findings',json={'description':'Unauthorised reviewer finding'}).status_code==404
    login(client,'officer-west')
    finding=client.post('/api/applications/APP-DEMO-0402/findings',json={'description':'Programme evidence needs clarification'}).json()
    assert finding['status']=='open'
    assert client.post(f"/api/findings/{finding['id']}/close",json={'version':finding['version']}).status_code==409
    login(client,'college-west')
    response=client.post(f"/api/findings/{finding['id']}/response",json={'version':finding['version'],'response':'Updated programme evidence is attached.'})
    assert response.status_code==200
    assert response.json()['status']=='responded'
    login(client,'officer-west')
    closed=client.post(f"/api/findings/{finding['id']}/close",json={'version':response.json()['version']})
    assert closed.status_code==200
    assert closed.json()['status']=='closed'
    assert detail(client,'APP-DEMO-0402')['findings'][0]['status']=='closed'

def test_evc_gates(client):
    c=client;login(c,'officer-west');a=detail(c,'APP-DEMO-0402');assert action(c,a,'evc').status_code==200
    a=detail(c,a['id']);assert action(c,a,'decision').status_code==422
    assert c.post('/api/applications/'+a['id']+'/evc',json={'version':a['version'],'date':'2026-12-01T10:00:00Z','report':'Report recorded'}).status_code==403
    login(c,'regional-west');a=detail(c,a['id'])
    assert c.post('/api/applications/'+a['id']+'/evc',json={'version':a['version'],'date':'2026-12-01T10:00:00Z','report':'Report recorded'}).status_code==200
    assert action(c,detail(c,a['id']),'decision').status_code==200

def test_evc_participant_conflict_and_quorum(client):
    login(client,'regional-west')
    participants=client.get('/api/applications/APP-DEMO-0402/evc/participants').json()
    assert {p['member_id'] for p in participants}=={'evc-west-1','evc-west-2'}
    login(client,'evc-west-1')
    participant=participants[0]
    conflict=client.post(f"/api/evc-participants/{participant['id']}/conflict",json={
        'status':'declared','reason':'Existing relationship with applicant'
    })
    assert conflict.status_code==200
    assert conflict.json()['status']=='declined'
    login(client,'regional-west')
    case=detail(client,'APP-DEMO-0402')
    assert action(client,case,'evc').status_code==200
    case=detail(client,'APP-DEMO-0402')
    assert client.post(f"/api/applications/{case['id']}/evc",json={
        'version':case['version'],'date':'2026-12-01T10:00:00Z','report':'Report recorded'
    }).status_code==200
    assert action(client,detail(client,case['id']),'decision').status_code==422

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

def test_compliance_clarification_and_resubmission(client):
    login(client,'college-west')
    obligation=next(o for o in client.get('/api/obligations').json() if o['kind']=='undertaking')
    assert client.post(f"/api/obligations/{obligation['id']}/files",data={'version':obligation['version']},files={'file':('proof.txt',b'Initial proof','text/plain')}).status_code==200
    obligation=next(o for o in client.get('/api/obligations').json() if o['id']==obligation['id'])
    assert client.post(f"/api/obligations/{obligation['id']}/evidence",json={'version':obligation['version'],'evidence':'Initial submission'}).status_code==200
    login(client,'regional-west')
    obligation=next(o for o in client.get('/api/obligations').json() if o['id']==obligation['id'])
    review=client.post(f"/api/obligations/{obligation['id']}/review",json={'version':obligation['version'],'reason':'Please provide a signed supporting record.'})
    assert review.status_code==200
    assert review.json()['status']=='clarification'
    login(client,'college-west')
    obligation=next(o for o in client.get('/api/obligations').json() if o['id']==obligation['id'])
    assert client.post(f"/api/obligations/{obligation['id']}/evidence",json={'version':obligation['version'],'evidence':'Must not submit without replacement file'}).status_code==422
    assert client.post(f"/api/obligations/{obligation['id']}/files",data={'version':obligation['version']},files={'file':('replacement.txt',b'Signed replacement proof','text/plain')}).status_code==200
    obligation=next(o for o in client.get('/api/obligations').json() if o['id']==obligation['id'])
    assert client.post(f"/api/obligations/{obligation['id']}/evidence",json={'version':obligation['version'],'evidence':'Replacement submission'}).status_code==200
    assert next(o for o in client.get('/api/obligations').json() if o['id']==obligation['id'])['status']=='submitted'

def test_sweep_dedup_and_renewed_document_monitoring(client):
    c=client;login(c,'admin');first=c.post('/api/alerts/sweep').json();assert first['created']>0
    assert c.post('/api/alerts/sweep').json()['created']==0
    with c.app.state.factory.begin() as db:
        o=db.scalar(select(Obligation).where(Obligation.kind=='document'));o.status='verified'
        n=sweep(db,datetime.now(timezone.utc)+timedelta(days=30));assert n>0
    assert any(n['level']=='escalated' for n in c.get('/api/notifications').json())

def test_notification_delivery_state_and_retry(client):
    login(client,'admin')
    assert client.post('/api/alerts/sweep').status_code==200
    with client.app.state.factory.begin() as db:
        notice=db.scalar(select(Notice))
        notice.status='failed'
        notice.last_error='Simulated provider unavailable'
        notice.attempts=1
        notification_id=notice.id
    retry=client.post(f'/api/notifications/{notification_id}/retry')
    assert retry.status_code==200
    assert retry.json()['status']=='delivered'
    assert retry.json()['attempts']==2
    assert retry.json()['last_error']==''
    assert client.post(f'/api/notifications/{notification_id}/retry').status_code==409

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
    history=c.get('/api/applications/'+case['id']+'/assignments').json()
    assert len(history)==2
    assert history[-1]['reviewer_id']=='officer-west-2'

def test_assignment_conflict_blocks_reassignment(client):
    login(client,'officer-west')
    case=detail(client,'APP-DEMO-0402')
    declared=client.post('/api/applications/'+case['id']+'/conflict',json={'status':'declared','reason':'Prior relationship with institution'})
    assert declared.status_code==200
    login(client,'regional-west')
    case=detail(client,'APP-DEMO-0402')
    assert client.post('/api/applications/'+case['id']+'/assign',json={
        'version':case['version'],
        'reviewer_id':'officer-west',
        'reason':'Reassign for workload',
    }).status_code==409

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
