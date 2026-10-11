// Real Chromium mobile layout smoke test; serves checked-out static site locally.
// Run in CI with: npm install --no-save playwright && npx playwright install --with-deps chromium
const {chromium}=require('playwright');
const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const mime={'.html':'text/html','.js':'application/javascript','.json':'application/json','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.jpg':'image/jpeg'};
const server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  const file=path.resolve(root,'.'+pathname,(pathname.endsWith('/')?'index.html':''));
  if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  fs.readFile(file,(err,data)=>{if(err){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');res.end(data)});
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const port=server.address().port;
 const browser=await chromium.launch({headless:true});
 try{
  for(const route of ['/','/en/','/plant/dandelion/','/en/plant/dandelion/']){
   for(const width of [320,375,390]){
    const page=await browser.newPage({viewport:{width,height:812},deviceScaleFactor:1,isMobile:true,hasTouch:true});
    await page.goto('http://127.0.0.1:'+port+route,{waitUntil:'domcontentloaded'});
    const layout=await page.evaluate(()=>{
      const input=document.getElementById('searchInput'),button=document.getElementById('searchBtn');
      const doc=document.documentElement;
      const ir=input?.getBoundingClientRect(),br=button?.getBoundingClientRect();
      return {scrollWidth:doc.scrollWidth,innerWidth:innerWidth,hasSearch:!!(ir&&br),inputWidth:ir?.width,buttonWidth:br?.width,inputLeft:ir?.left,inputRight:ir?.right,buttonLeft:br?.left,buttonRight:br?.right};
    });
    assert.ok(layout.scrollWidth<=width+2,route+' '+width+'px horizontal overflow: '+JSON.stringify(layout));
    if(route==='/' || route==='/en/'){
     assert.ok(layout.hasSearch,route+' search controls missing');
     assert.ok(layout.inputWidth>=80 && layout.buttonWidth>=40,route+' '+width+'px search controls collapsed: '+JSON.stringify(layout));
     assert.ok(layout.inputLeft>=-2 && layout.inputRight<=width+2 && layout.buttonLeft>=-2 && layout.buttonRight<=width+2,route+' '+width+'px search controls clipped: '+JSON.stringify(layout));
    }
    if(route==='/en/'){
     await page.waitForFunction(()=>document.getElementById('catalogCount')?.dataset.ready==='1',{timeout:12000});
     await page.locator('#searchInput').fill('dandelion');
     await page.locator('#searchBtn').click();
     const cards=page.locator('#searchResults .resultcard');
     await cards.first().waitFor({state:'visible',timeout:10000});
     const resultLayout=await page.evaluate(()=>{
      const cards=[...document.querySelectorAll('#searchResults .resultcard')];
      return {scrollWidth:document.documentElement.scrollWidth,innerWidth:innerWidth,
       cards:cards.map(c=>{const r=c.getBoundingClientRect();return {left:r.left,right:r.right,width:r.width}})};
     });
     assert.ok(resultLayout.cards.length>0,route+' search produced no cards');
     assert.ok(resultLayout.scrollWidth<=width+2,route+' '+width+'px result horizontal overflow: '+JSON.stringify(resultLayout));
     assert.ok(resultLayout.cards.every(c=>c.left>=-2&&c.right<=width+2&&c.width>100),route+' '+width+'px result card clipped: '+JSON.stringify(resultLayout));
     console.log('PASS',route,width+'px search results',JSON.stringify(resultLayout));
    }
    console.log('PASS',route,width+'px',JSON.stringify(layout));
    await page.close();
   }
  }
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
