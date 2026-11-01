// @vitest-environment node
import {describe,it,expect,beforeEach} from 'vitest';
import fs from 'node:fs';
import {createPreviewEngine} from './engine.js';
const seed=JSON.parse(fs.readFileSync(new URL('./seed.json',import.meta.url),'utf8'));
let state,session,call;
beforeEach(()=>{state=structuredClone(seed);session={account:'regional-west'};call=createPreviewEngine(state,session)});
describe('browser-local rehearsal (not backend evidence)',()=>{
 it('reassignment changes reviewer scope and refuses cross-region targets',async()=>{
  const c=state.cases.find(c=>c.id==='APP-DEMO-0402');
  await expect(call('/applications/'+c.id+'/assign','POST',{version:c.version,reviewer_id:'officer-east',reason:'Balance workload'})).rejects.toMatchObject({status:422});
  await call('/applications/'+c.id+'/assign','POST',{version:c.version,reviewer_id:'officer-west-2',reason:'Balance workload'});
  session.account='officer-west';await expect(call('/applications/'+c.id)).rejects.toMatchObject({status:404});
  session.account='officer-west-2';expect((await call('/applications/'+c.id)).owner).toBe(session.account);
 });
 it('requires checklist evidence and supports correction; EOA excludes EVC',async()=>{
  session.account='college-west';const c=await call('/applications','POST',{kind:'eoa',idempotency_key:'preview-test'});
  await expect(call('/applications/'+c.id+'/submit','POST',{version:1})).rejects.toMatchObject({status:422});
  for(const slot of state.rules.types.eoa.slots)state.documents.push({case_id:c.id,slot,id:state.nextDocument++});
  await call('/applications/'+c.id+'/submit','POST',{version:1});session.account='officer-west';
  await expect(call('/applications/'+c.id+'/transition','POST',{version:2,target:'evc',reason:'Reviewed'})).rejects.toMatchObject({status:409});
  await call('/applications/'+c.id+'/transition','POST',{version:2,target:'correction',reason:'Please correct declaration'});
  session.account='college-west';await call('/applications/'+c.id+'/submit','POST',{version:3});expect(c.state).toBe('scrutiny');
 });
 it('keeps submission separate from verification and uses exact renewal expiry',async()=>{
  session.account='college-west';const o=state.obligations.find(o=>o.kind==='document'),old=o.due;
  state.documents.push({id:1,case_id:o.case_id,slot:'obligation:'+o.id});
  await call('/obligations/'+o.id+'/evidence','POST',{version:1,evidence:'Renewed lease proof',expiry:'2035-02-03T00:00:00Z'});
  expect(o.status).toBe('submitted');expect(o.due).toBe(old);
  await expect(call('/obligations/'+o.id+'/verify','POST',{version:2})).rejects.toMatchObject({status:403});
  session.account='regional-west';await call('/obligations/'+o.id+'/verify','POST',{version:2});expect(o.due).toBe('2035-02-03T00:00:00Z');
 });
 it('rejects stale actions and deduplicates repeated alerts',async()=>{
  const c=state.cases.find(c=>c.id==='APP-DEMO-0402');await expect(call('/applications/'+c.id+'/transition','POST',{version:0,target:'evc',reason:'Reviewed'})).rejects.toMatchObject({status:409});
  session.account='admin';expect((await call('/alerts/sweep','POST')).created).toBeGreaterThan(0);expect((await call('/alerts/sweep','POST')).created).toBe(0);
 });
 it('requires EVC report and rejects oversight decisions',async()=>{
  const c=state.cases.find(c=>c.id==='APP-DEMO-0402');await call('/applications/'+c.id+'/transition','POST',{version:c.version,target:'evc',reason:'Reviewed'});
  await expect(call('/applications/'+c.id+'/transition','POST',{version:c.version,target:'decision',reason:'Reviewed'})).rejects.toMatchObject({status:422});
  session.account='admin';await expect(call('/applications/'+c.id+'/transition','POST',{version:c.version,target:'approved',reason:'Reviewed'})).rejects.toMatchObject({status:403});
 });
});

describe('preview file handling',()=>{
 it('stores actual evidence bytes/hash, retains revisions and reopens verification',async()=>{
  session.account='college-west';const o=state.obligations[0];
  for(let i=0;i<2;i++){
   const f=new FormData();f.append('version',String(o.version));f.append('file',new File(['Synthetic evidence '+i],'proof.txt',{type:'text/plain'}));
   const saved=await call('/obligations/'+o.id+'/files','POST',f);expect(saved.sha256).toMatch(/^[a-f0-9]{64}$/);expect(saved.revision).toBe(i+1);
   await call('/obligations/'+o.id+'/evidence','POST',{version:o.version,evidence:'Supporting declaration'});session.account='regional-west';await call('/obligations/'+o.id+'/verify','POST',{version:o.version});session.account='college-west';
  }
  expect(state.documents.length).toBe(2);const d=await call('/documents/1');expect(atob(d.content)).toBe('Synthetic evidence 0');session.account='college-east';await expect(call('/documents/1')).rejects.toMatchObject({status:404});
 });
});
