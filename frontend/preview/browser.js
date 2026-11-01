import {createPreviewEngine} from './engine.js';
window.__AICTE_PREVIEW__=true;
const nativeFetch=window.fetch.bind(window),seed=await(await nativeFetch('/preview-seed.json')).json();
const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('aicte-rehearsal-v2',1);r.onupgradeneeded=()=>r.result.createObjectStore('state');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});
const read=()=>new Promise((resolve,reject)=>{const r=db.transaction('state').objectStore('state').get('demo');r.onsuccess=()=>resolve(r.result||structuredClone(seed));r.onerror=()=>reject(r.error)});
const save=state=>new Promise((resolve,reject)=>{const t=db.transaction('state','readwrite');t.objectStore('state').put(state,'demo');t.oncomplete=resolve;t.onerror=()=>reject(t.error);t.onabort=()=>reject(t.error)});
let queue=Promise.resolve();
window.fetch=async(url,options={})=>{
 if(!String(url).startsWith('/api'))return nativeFetch(url,options);
 const perform=async()=>{
  const state=await read(),session={account:sessionStorage.getItem('previewAccount')};
  try{
   const body=options.body instanceof FormData?options.body:options.body?JSON.parse(options.body):{};
   const result=await createPreviewEngine(state,session)(String(url).slice(4),options.method||'GET',body);
   if(options.method&&options.method!=='GET')await save(state);
   if(session.account)sessionStorage.setItem('previewAccount',session.account);else sessionStorage.removeItem('previewAccount');
   return new Response(JSON.stringify(result),{headers:{'Content-Type':'application/json'}});
  }catch(e){return new Response(JSON.stringify({detail:e.message||'Browser storage unavailable. Reset the demo or allow site storage.'}),{status:e.status||507,headers:{'Content-Type':'application/json'}})}
 };
 const job=()=>navigator.locks?navigator.locks.request('aicte-demo-state',perform):perform();
 const result=queue.then(job);queue=result.catch(()=>{});return result;
};
document.addEventListener('click',async e=>{
 const a=e.target.closest('a[href^="/api/documents/"]');if(!a)return;e.preventDefault();
 const r=await fetch(a.getAttribute('href')),d=await r.json();if(!r.ok){alert(d.detail);return}
 const url=URL.createObjectURL(new Blob([Uint8Array.from(atob(d.content),c=>c.charCodeAt(0))],{type:'application/octet-stream'}));const link=document.createElement('a');link.href=url;link.download=d.filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
const bar=document.createElement('div');bar.className='preview-bar';bar.innerHTML='<b>PREVIEW 2 · Interactive rehearsal</b><span>Browser-local data · Roles simulated · No shared server or real notifications · Use synthetic files only</span><a href="/TEST_CHECKLIST.md" target="_blank" rel="noopener">Test checklist</a><button type="button">Reset demo</button>';
bar.querySelector('button').onclick=async()=>{if(confirm('Reset only this browser’s demo applications and uploaded files?')){await save(structuredClone(seed));sessionStorage.removeItem('previewAccount');location.reload()}};document.body.prepend(bar);
await import(document.querySelector('script[data-app]').dataset.app);
