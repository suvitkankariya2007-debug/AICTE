import React from 'react';
import {afterEach,beforeEach,describe,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {App} from './main';
const user={id:'college-west',name:'Ananya',role:'institution',institution:'Pune Demo Institute',region:'West Demo'};
const rules={version:'DEMO-v1',source:'NEEDS_APH_VERIFICATION',types:{eoa:{label:'Extension of approval',track:'T3 · Routine and fast-track approvals',route:['scrutiny','decision'],slots:['Prior approval']},new_course:{label:'New course',track:'T2 · Academic and programme modifications',route:['scrutiny','evc','decision'],slots:['Programme proposal','Faculty statement']}}};
let signedIn=false;
let calls:string[]=[];
const sample={id:'APP-100',institution:'Pune Demo Institute',region:'West Demo',kind:'eoa',state:'scrutiny',route:['scrutiny','decision'],version:1,due:'2030-01-01T00:00:00Z',entered:'2026-11-01T00:00:00Z'};
beforeEach(()=>{signedIn=false;calls=[];vi.stubGlobal('fetch',vi.fn(async(path:string,options:any={})=>{
 const key=path.replace('/api','');const endpoint=key.split('?')[0];calls.push(key);
 let data:any={};let status=200;
 if(endpoint==='/demo-accounts')data=[user];
 else if(endpoint==='/me'){data=user;status=signedIn?200:401}
 else if(endpoint==='/login'){signedIn=true;data=user}
 else if(endpoint==='/logout'){signedIn=false;data={ok:true}}
 else if(endpoint==='/rules')data=rules;
 else if(endpoint==='/applications')data=[sample];
 else if(endpoint==='/obligations'||endpoint==='/notifications'||endpoint==='/complaints')data=[];
 else if(endpoint==='/applications/APP-100')data={...sample,slots:['Prior approval'],documents:[],obligations:[],audit:[]};
 return {ok:status<400,status,json:async()=>data};
}));});
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
async function signIn(){render(<App/>);await screen.findByRole('combobox',{name:'Position'});fireEvent.click(screen.getByRole('button',{name:'Sign in'}));await screen.findByRole('heading',{name:/Welcome, Pune Demo Institute/})}
describe('workspace interactions',()=>{
 it('logs in, loads shared metrics, opens a case and logs out',async()=>{await signIn();expect(calls.some(path=>path.startsWith('/applications?'))).toBe(true);expect(screen.getByText('ROLE-SPECIFIC WORKSPACE')).toBeTruthy();expect(screen.getByRole('heading',{name:'Deadline attention'})).toBeTruthy();fireEvent.click(screen.getByRole('button',{name:'APP-100'}));await screen.findByRole('heading',{name:'Application status'});expect(screen.getByText('Required')).toBeTruthy();fireEvent.click(screen.getByRole('button',{name:/Logout/}));await screen.findByRole('heading',{name:'Sign in to your workspace'});});
 it('lists every application type in one selectable catalogue',async()=>{await signIn();fireEvent.click(screen.getByRole('button',{name:/New application/}));const selector=screen.getByRole('combobox',{name:'Application type'}) as HTMLSelectElement;expect(selector.options).toHaveLength(2);expect(selector.options[0].textContent).toContain('T');expect(screen.getByText('Programme proposal')).toBeTruthy();fireEvent.change(selector,{target:{value:'eoa'}});expect(selector.value).toBe('eoa');expect(screen.getByText('Prior approval')).toBeTruthy();expect(screen.queryByText('Faculty statement')).toBeNull();});
 it('filters a queue and shows a meaningful empty state',async()=>{await signIn();fireEvent.click(screen.getByRole('button',{name:'Applications'}));fireEvent.change(screen.getByPlaceholderText('Search application or institution'),{target:{value:'does-not-exist'}});expect(screen.getByText('No applications match these filters.')).toBeTruthy();});
 it('displays API failure without claiming success',async()=>{render(<App/>);await screen.findByRole('button',{name:'Sign in'});const original=globalThis.fetch;vi.stubGlobal('fetch',async(path:any,opts:any)=>path==='/api/login'?{ok:false,json:async()=>({detail:'Invalid credentials'})}:original(path,opts));fireEvent.click(screen.getByRole('button',{name:'Sign in'}));expect(await screen.findByRole('alert')).toBeTruthy();expect(screen.queryByRole('heading',{name:/Welcome, Pune Demo Institute/})).toBeNull();});
});
