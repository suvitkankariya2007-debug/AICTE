import {expect,test} from '@playwright/test';

const user={
  id:'college-west',
  name:'Ananya',
  role:'institution',
  institution:'Pune Demo Institute',
  region:'West Demo',
};

test('institution can reach dashboard and primary navigation by keyboard',async({page})=>{
  await page.route('**/api/**',async route=>{
    const path=new URL(route.request().url()).pathname.replace('/api','');
    let status=200;
    let body:unknown={};
    if(path==='/demo-accounts') body=[user];
    else if(path==='/me') { status=401; body={detail:'Not authenticated'}; }
    else if(path==='/login') body=user;
    else if(path==='/applications') body={items:[],page:1,page_size:25,total:0,pages:1};
    else if(path==='/rules') body={version:'DEMO-v1',source:'NEEDS_APH_VERIFICATION',types:{}};
    else if(path==='/obligations'||path==='/notifications') body=[];
    else if(path==='/complaints') body={items:[],page:1,page_size:25,total:0,pages:1};
    else body={};
    await route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});
  });
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Sign in to your workspace'})).toBeVisible();
  await page.getByRole('button',{name:'Sign in'}).click();
  await expect(page.getByRole('heading',{name:'Welcome, Pune Demo Institute'})).toBeVisible();
  await expect(page.getByRole('navigation',{name:'Primary navigation'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Refresh shared data'})).toBeVisible();
  await page.getByRole('button',{name:'Notifications',exact:true}).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading',{name:'Notifications & escalations'})).toBeVisible();
});
