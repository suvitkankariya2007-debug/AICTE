// Browser-local rehearsal only. The authoritative API is backend/app/main.py.
export function createPreviewEngine(state, session) {
 const uuid=()=>Array.from(crypto.getRandomValues(new Uint8Array(16))).map(n=>n.toString(16).padStart(2,'0')).join('');
 const now=()=>new Date().toISOString(), day=n=>new Date(Date.now()+n*86400000).toISOString();
 const fail=(status,message)=>{throw {status,message}};
 const user=()=>state.accounts.find(u=>u.id===session.account)||fail(401,'Choose a demo account');
 const scope=(c,u)=>u.role==='national_admin'||u.role==='institution'&&c.institution===u.institution||u.role==='regional_officer'&&c.region===u.region||u.role==='scrutiny_officer'&&c.owner===u.id&&c.region===u.region;
 const one=id=>{const c=state.cases.find(c=>c.id===id);if(!c||!scope(c,user()))fail(404,'Application not found in your demo scope');return c};
 const version=(o,v)=>{if(o.version!==Number(v))fail(409,'Record changed; refresh before retrying')};
 const role=(...roles)=>{if(!roles.includes(user().role))fail(403,'This demo account cannot perform this action')};
 const audit=(c,action,detail)=>state.audit.unshift({id:uuid(),case_id:c.id,actor:session.account,action,detail,created:now()});
 const notice=(c,message,dedup,level='info',recipient='institution')=>{if(state.notices.some(n=>n.dedup===dedup))return false;state.notices.unshift({id:uuid(),case_id:c.id,recipient,message,dedup,level,delivery:'simulated',created:now()});return true};
 const clean=d=>{const {content,...rest}=d;return rest};
 const docs=(cid,slot)=>state.documents.filter(d=>d.case_id===cid&&(!slot||d.slot===slot)).map(clean);
 const detail=c=>({...c,documents:docs(c.id),slots:state.rules.types[c.kind].slots,obligations:state.obligations.filter(o=>o.case_id===c.id),audit:state.audit.filter(a=>a.case_id===c.id)});
 const obligation=id=>{const o=state.obligations.find(o=>o.id===Number(id));if(!o)fail(404,'Obligation not found');one(o.case_id);return o};
 async function file(c,slot,f){
  const b=f.get('file');if(!b||!b.size||b.size>2097152)fail(422,'Use a PDF/text file between 1 byte and 2 MB');
  const bytes=new Uint8Array(await b.arrayBuffer());
  if(!(b.type==='application/pdf'&&new TextDecoder().decode(bytes.slice(0,5))==='%PDF-'||b.type==='text/plain'&&!bytes.includes(0)))fail(422,'Only PDF or plain text evidence is accepted');
  let binary='';for(const n of bytes)binary+=String.fromCharCode(n);
  const d={id:state.nextDocument++,case_id:c.id,slot,filename:b.name.replace(/[^\w. -]/g,'_').slice(-120),content:btoa(binary),sha256:Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(n=>n.toString(16).padStart(2,'0')).join(''),revision:docs(c.id,slot).length+1,created:now()};state.documents.push(d);return d;
 }
 return async(path,method='GET',body={})=>{
  if(path==='/demo-accounts')return state.accounts;
  if(path==='/health')return {status:'ok',mode:'BROWSER_LOCAL_PREVIEW',release:'preview-2'};
  if(path==='/login'){if(body.password!=='DemoPass!2026'||!state.accounts.some(a=>a.id===body.username))fail(401,'Invalid demo credentials');session.account=body.username;return user()}
  if(path==='/logout'){session.account=null;return {ok:true}}
  const u=user();
  if(path==='/me')return u;
  if(path==='/rules')return state.rules;
  if(path==='/applications'&&method==='GET')return state.cases.filter(c=>scope(c,u));
  if(path==='/applications'&&method==='POST'){
   role('institution');const rule=state.rules.types[body.kind];if(!rule)fail(422,'Unknown category');
   const prior=state.cases.find(c=>c.submit_key===u.id+':'+body.idempotency_key);if(prior){if(prior.kind!==body.kind)fail(409,'Request key already used');return prior}
   const c={id:'APP-'+uuid().slice(0,8).toUpperCase(),institution:u.institution,region:u.region,kind:body.kind,state:'draft',route:rule.route,rule_version:state.rules.version,owner:u.region==='West Demo'?'officer-west':'officer-east',version:1,entered:now(),due:day(7),reason:'',schedule:'',report:'',submit_key:u.id+':'+body.idempotency_key};state.cases.unshift(c);audit(c,'draft_created','Browser-local demo draft');return c;
  }
  if(path.startsWith('/reviewers?')){role('regional_officer');const c=one(new URLSearchParams(path.split('?')[1]).get('case_id'));return state.accounts.filter(r=>r.role==='scrutiny_officer'&&r.region===c.region).map(r=>({...r,open_cases:state.cases.filter(c=>c.owner===r.id&&!['approved','rejected'].includes(c.state)).length}))}
  if(path==='/obligations')return state.obligations.filter(o=>scope(state.cases.find(c=>c.id===o.case_id),u)).map(o=>({...o,files:docs(o.case_id,'obligation:'+o.id)}));
  if(path==='/notifications')return state.notices.filter(n=>scope(state.cases.find(c=>c.id===n.case_id),u)&&(u.role!=='institution'||n.recipient==='institution'));
  const match=path.match(/^\/applications\/([^/]+)(?:\/(.+))?$/);
  if(match){
   const c=one(match[1]),op=match[2];if(!op&&method==='GET')return detail(c);
   if(op==='documents'){
    role('institution');if(!['draft','correction'].includes(c.state))fail(403,'Uploads require draft/correction');version(c,body.get('version'));
    const slot=body.get('slot');if(!state.rules.types[c.kind].slots.includes(slot))fail(422,'Unknown checklist slot');
    const d=await file(c,slot,body);c.version++;audit(c,'evidence_uploaded',slot+'; revision '+d.revision);return clean(d);
   }
   version(c,body.version);
   if(op==='assign'){
    role('regional_officer');if(['approved','rejected'].includes(c.state))fail(409,'Closed case');const r=state.accounts.find(r=>r.id===body.reviewer_id&&r.role==='scrutiny_officer'&&r.region===c.region);
    if(!r)fail(422,'Choose a reviewer in the originating region');if((body.reason||'').trim().length<5)fail(422,'Provide an assignment reason');if(c.owner===r.id)fail(409,'Reviewer already assigned');
    audit(c,'reviewer_assigned',c.owner+' → '+r.id+'; '+body.reason);c.owner=r.id;c.version++;return {ok:true};
   }
   if(op==='evc'){
    role('regional_officer');if(c.state!=='evc')fail(403,'EVC stage required');if(!Number.isFinite(Date.parse(body.date)))fail(422,'Valid visit date required');
    c.schedule=body.date;c.report=body.report;c.version++;audit(c,'evc_updated','Schedule '+c.schedule+'; report '+c.report);notice(c,'EVC schedule updated: '+c.schedule,'evc:'+c.id+':'+c.version);return {ok:true};
   }
   let target=body.target,reason=body.reason;
   if(op==='submit'){
    role('institution');if(!['draft','correction'].includes(c.state))fail(403,'Not awaiting submission');
    const missing=state.rules.types[c.kind].slots.filter(s=>!docs(c.id,s).length);if(missing.length)fail(422,'Missing required evidence: '+missing.join(', '));target='scrutiny';reason='Institution submitted evidence';
   }else if(op==='transition'){
    role('scrutiny_officer','regional_officer');if(!reason?.trim())fail(422,'Record review findings / reasons');
    if(['approved','rejected'].includes(target))role('regional_officer');
    const edges=c.route.slice(0,-1).map((s,i)=>s+':'+c.route[i+1]).concat(['scrutiny:correction','decision:approved','decision:rejected']);
    if(!edges.includes(c.state+':'+target))fail(409,'Transition is not permitted by this route');
    if(c.state==='evc'&&target==='decision'&&(!c.schedule||!c.report?.trim()))fail(422,'EVC schedule and report required');
   }else fail(404,'Unknown operation');
   audit(c,'stage_changed',c.state+' → '+target+'. '+reason);c.state=target;c.reason=reason;c.version++;c.entered=now();c.due=day(7);notice(c,'Application moved to '+target,'move:'+c.id+':'+c.version);return c;
  }
  const om=path.match(/^\/obligations\/(\d+)\/(files|evidence|verify)$/);
  if(om){
   const o=obligation(om[1]),c=one(o.case_id);version(o,om[2]==='files'?body.get('version'):body.version);
   if(om[2]==='files'){role('institution');const d=await file(c,'obligation:'+o.id,body);o.status='pending';o.evidence='';o.proposed_expiry='';o.version++;audit(c,'compliance_file_uploaded',o.title+'; revision '+d.revision);return clean(d)}
   if(om[2]==='evidence'){
    role('institution');if(!docs(c.id,'obligation:'+o.id).length)fail(422,'Upload supporting evidence first');if(!body.evidence?.trim()||body.evidence.trim().length<5)fail(422,'Provide an evidence description');
    if(o.kind==='document'&&!(Date.parse(body.expiry)>Date.now()))fail(422,'Renewal expiry must be in the future');
    o.evidence=body.evidence;o.proposed_expiry=o.kind==='document'?body.expiry:'';o.status='submitted';audit(c,'compliance_submitted',o.title+'; awaiting verification');
   }else{
    role('scrutiny_officer','regional_officer');if(o.status!=='submitted')fail(409,'Evidence must first be submitted');if(o.kind==='document'){if(!(Date.parse(o.proposed_expiry)>Date.now()))fail(422,'Proposed expiry has passed');o.due=o.proposed_expiry}o.status='verified';audit(c,'compliance_verified',o.title);
   }o.version++;return {ok:true};
  }
  if(path==='/alerts/sweep'){
   role('national_admin');let created=0;
   const items=state.cases.filter(c=>!['approved','rejected'].includes(c.state)).map(c=>({...c,case_id:c.id,kind:'stage',title:c.state})).concat(state.obligations.filter(o=>o.status!=='verified'||o.kind==='document'));
   for(const i of items){const days=(Date.parse(i.due)-Date.now())/86400000;if(days>3)continue;const level=days< -7?'escalated':days<0?'overdue':'upcoming';const c=state.cases.find(c=>c.id===i.case_id);if(notice(c,i.title+': '+level+' · due '+i.due.slice(0,10),[i.kind,i.id,i.version,i.due,level].join(':'),level,level==='escalated'?'national_admin':level==='overdue'?'regional_officer':'institution')){created++;audit(c,'deadline_alert',i.title+': '+level+'; simulated delivery')}}return {created,delivery:'simulated'};
  }
  if(path.startsWith('/documents/')){const d=state.documents.find(d=>d.id===Number(path.split('/')[2]));if(!d)fail(404,'File not found');one(d.case_id);return d}
  fail(404,'Preview operation unavailable');
 };
}
