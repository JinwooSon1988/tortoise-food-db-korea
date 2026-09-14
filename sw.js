const CACHE='tfd-v51-stable-13';
const CORE=['./','./index.html','./offline.html','./manifest.webmanifest','./search-live.js','./profile-context.js','./source-preview.js','./fresh-primary-mode.js',
'./data/plants.json','./data/assessments.json','./data/evidence.json','./data/korean_retail_name_map.json','./profile/','./today/','./meal/','./weekly/','./growth/','./monthly/','./trends/','./settings/'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;if(e.request.mode==='navigate'){e.respondWith(fetch(e.request).then(r=>{const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));return r;}).catch(()=>caches.match(e.request).then(r=>r||caches.match('./offline.html'))));return}e.respondWith(caches.match(e.request).then(hit=>hit||fetch(e.request).then(r=>{if(r&&r.status===200){const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy))}return r}))) });
