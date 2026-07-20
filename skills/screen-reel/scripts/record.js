#!/usr/bin/env node
/* تسجيل موقع حيّ بحركة بشرية.
   الاستخدام: node record.js <url> <outDir> [beatsJsonPath]
   الأساس: مقاس النافذة = مقاس التسجيل، ثم تُرفع الدقّة في ffmpeg. */
const path = process.env.PW_PATH || '/tmp/npm-global/lib/node_modules/playwright';
const { chromium } = require(path);
const fs = require('fs');

const URL      = process.argv[2] || 'https://example.com';
const OUT      = process.argv[3] || '/tmp/vid';
const BEATS    = process.argv[4] ? JSON.parse(fs.readFileSync(process.argv[4],'utf8')) : null;
const W = +(process.env.VW || 540), H = +(process.env.VH || 960);

const wait = (a,b)=> new Promise(r=>setTimeout(r, a + Math.random()*(b-a)));

(async () => {
  const browser = await chromium.launch({
    args:['--ignore-certificate-errors','--hide-scrollbars']
  });
  const ctx = await browser.newContext({
    viewport:{width:W,height:H},
    recordVideo:{dir:OUT, size:{width:W,height:H}},   // مطابق عمدًا
    ignoreHTTPSErrors:true,
    locale: process.env.LOCALE || 'ar-KW'
  });
  const p = await ctx.newPage();
  await p.goto(URL,{waitUntil:'networkidle',timeout:60000});
  await p.addStyleTag({content:`
    *{scrollbar-width:none!important}
    ::-webkit-scrollbar{display:none!important}
    .__glow{box-shadow:0 0 0 2px rgba(201,162,39,.8),0 0 30px rgba(201,162,39,.35)!important;
      border-radius:8px;transition:box-shadow .8s ease}
  `});
  await wait(1500,1900);

  // تمرير بشري: منحنى تسارع + وقفات متغيّرة + تردّد عرضيّ
  const scrollTo = async (sel, pauses=2) => {
    const y = await p.evaluate(s=>{
      const e=document.querySelector(s);
      return e ? e.getBoundingClientRect().top + window.scrollY - 70 : null;
    }, sel);
    if (y===null) { console.error('لم يُعثر على: '+sel); return false; }
    const start = await p.evaluate(()=>window.scrollY);
    const dist  = y - start;
    const steps = 24 + Math.floor(Math.random()*8);
    for (let i=1;i<=steps;i++){
      const t=i/steps;
      const e = t<.5 ? 4*t*t*t : 1-Math.pow(-2*t+2,3)/2;      // easeInOutCubic
      await p.evaluate(v=>window.scrollTo(0,v), start + dist*e);
      await new Promise(r=>setTimeout(r, 15+Math.random()*15));
      if (Math.random()<0.09) await new Promise(r=>setTimeout(r,120+Math.random()*80));
    }
    for (let i=0;i<pauses;i++) await wait(300,560);
    return true;
  };

  const glow = async sel => p.evaluate(s=>{
    const e=document.querySelector(s); if(e) e.classList.add('__glow');
  }, sel);

  const zoom = async (sel, scales=[1.5,2.0,2.4]) => {
    for (const v of scales){
      await p.evaluate(([s,val])=>{
        const e=document.querySelector(s); if(!e) return;
        e.style.transition='.5s cubic-bezier(.2,.8,.3,1)';
        e.style.transform=`scale(${val})`;
        e.style.transformOrigin='right center';
        e.style.margin='12px 0';
      },[sel,v]);
      await wait(480,700);
    }
  };

  const beats = BEATS || [
    {scroll:'main, article, body'},
    {hold:2000}
  ];
  for (const b of beats){
    if (b.scroll) await scrollTo(b.scroll, b.pauses ?? 2);
    if (b.glow)   { await glow(b.glow); await wait(800,1100); }
    if (b.zoom)   await zoom(b.zoom, b.scales);
    if (b.hold)   await wait(b.hold*0.85, b.hold*1.15);
  }

  await ctx.close(); await browser.close();
  console.log('ok');
})();
