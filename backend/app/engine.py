from types import SimpleNamespace
from transitions import Machine, MachineError
from fastapi import HTTPException
from sqlalchemy import select, update
from .db import Case, Audit, Notice, Obligation
from datetime import datetime, timedelta, timezone

def utc(value):
    try:
        result=datetime.fromisoformat(value.replace('Z','+00:00'))
        if result.tzinfo is None: raise ValueError()
        return result.astimezone(timezone.utc)
    except (ValueError,TypeError): raise HTTPException(422,'Date must include a timezone')

def audit(db,case,user,action,detail):
    db.add(Audit(case_id=case.id,actor=user.id if user else 'system',action=action,detail=detail))

def move(db,case,user,target,version,reason=''):
    if case.version!=version: raise HTTPException(409,'Case changed. Refresh before retrying.')
    edges=[{'trigger':'advance','source':a,'dest':b} for a,b in zip(case.route,case.route[1:])]
    edges += [{'trigger':'advance','source':'decision','dest':x} for x in ['approved','rejected']]
    edges += [{'trigger':'advance','source':'scrutiny','dest':'correction'}, {'trigger':'advance','source':'correction','dest':'scrutiny'}]
    model=SimpleNamespace()
    machine=Machine(model=model,states=list(dict.fromkeys(case.route+['correction','approved','rejected'])),initial=case.state,auto_transitions=False)
    for edge in edges: machine.add_transition('to_'+edge['dest'],edge['source'],edge['dest'])
    try: model.trigger('to_'+target)
    except (MachineError,AttributeError): raise HTTPException(409,'Transition is not permitted by this route')
    previous_state=case.state
    stamp=datetime.now(timezone.utc)
    values=dict(state=target,version=version+1,entered=stamp.isoformat(),due=(stamp+timedelta(days=7)).isoformat(),reason=reason)
    if db.execute(update(Case).where(Case.id==case.id,Case.version==version).values(**values)).rowcount!=1:
        raise HTTPException(409,'Concurrent update. Refresh before retrying.')
    audit(db,case,user,'stage_changed',f'{previous_state} → {target}. {reason} Rule: {case.rule_version}')
    db.add(Notice(case_id=case.id,recipient='institution',message=f'Application moved to {target}. {reason}',level='info',dedup=f'transition:{case.id}:{version}'))
    db.flush(); db.refresh(case)
    return case

def sweep(db,clock=None):
    clock=clock or datetime.now(timezone.utc)
    count=0
    cases={c.id:c for c in db.scalars(select(Case))}
    items=[('stage',c.id,c.id,c.state,c.due,c.version) for c in cases.values() if c.state not in ['approved','rejected']]
    items += [(o.kind,str(o.id),o.case_id,o.title,o.due,o.version) for o in db.scalars(select(Obligation)) if o.status!='verified' or o.kind=='document']
    for kind,item,cid,label,due,version in items:
        days=(utc(due)-clock).total_seconds()/86400
        if days>3: continue
        level='escalated' if days < -7 else 'overdue' if days<0 else 'upcoming'
        key=f'{kind}:{item}:{version}:{due}:{level}'
        if db.scalar(select(Notice).where(Notice.dedup==key)): continue
        recipient='national_admin' if level=='escalated' else 'regional_officer' if level=='overdue' else 'institution'
        db.add(Notice(
            case_id=cid,
            recipient=recipient,
            message=f'{label}: {level} · due {due[:10]}',
            level=level,
            dedup=key,
            status='delivered',
            attempts=1,
            delivered_at=clock.isoformat(),
        ))
        audit(db,cases[cid],None,'deadline_alert',f'{kind} {item}: {level}; recipient {recipient}; delivery simulated')
        count+=1
    return count
