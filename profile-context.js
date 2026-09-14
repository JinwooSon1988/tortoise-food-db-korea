(function(){
 const SPECIES={
  ibera:'이베라 그리스',greek:'그리스 육지거북',hermanni:'헤르만 육지거북',marginata:'마지나타',
  horsfieldii:'호스필드',sulcata:'설카타',leopard:'레오파드'
 };
 function normalize(p){
  if(!p)return null;
  return Object.assign({},p,{
   species_name:p.species_name||SPECIES[p.species]||p.species||'',
   weight_g:p.weight_g!=null?p.weight_g:(p.weight!=null?p.weight:null)
  });
 }
 window.TFDProfiles={
  all(){try{return JSON.parse(localStorage.getItem('tfd_profiles_v46')||'[]').map(normalize)}catch(e){return[]}},
  active(){const a=this.all(),id=localStorage.getItem('tfd_active_profile_v46');return a.find(x=>x.id===id)||a[0]||null},
  normalize
 };
 const nativeFetch=window.fetch.bind(window);
 window.fetch=async function(input,init){
  const url=typeof input==='string'?input:(input&&input.url)||'';
  const baseMatch=url.match(/^(.*\/data\/)(assessments|evidence)\.json(?:[?#].*)?$/);
  if(!baseMatch)return nativeFetch(input,init);
  const baseUrl=baseMatch[1],kind=baseMatch[2];
  const main=await nativeFetch(input,init);
  if(!main.ok)return main;
  try{
   const mainData=await main.clone().json();
   const merged=[...(Array.isArray(mainData)?mainData:[])];
   for(const suffix of ['_korea_addendum.json','_korea_addendum_2.json','_korea_addendum_3.json','_korea_addendum_4.json','_korea_addendum_5.json','_korea_addendum_6.json','_korea_addendum_7.json']){
    try{
     const extra=await nativeFetch(baseUrl+kind+suffix,{cache:'no-cache'});
     if(!extra.ok)continue;
     const extraData=await extra.json();
     if(Array.isArray(extraData))merged.push(...extraData);
    }catch(e){}
   }
   return new Response(JSON.stringify(merged),{status:main.status,statusText:main.statusText,headers:{'Content-Type':'application/json; charset=utf-8'}});
  }catch(e){return main}
 };
 if(/\/today\/?(?:index\.html)?$/.test(location.pathname)){
  const h1=document.querySelector('h1');
  if(h1&&!document.getElementById('todayQuickLink')){
   const box=document.createElement('div');box.id='todayQuickLink';
   box.style.cssText='margin:10px 0 14px;padding:12px 14px;border:2px solid #bfd8c6;border-radius:14px;background:#fbfefb';
   box.innerHTML='<b>빠르게 답만 보고 싶다면</b><br><a href="quick.html" style="display:inline-block;margin-top:7px;padding:10px 13px;border-radius:11px;background:#2f6b49;color:#fff;text-decoration:none;font-weight:800">3초 요약 보기 →</a><div style="margin-top:6px;font-size:12px;color:#657067">기존 공개 판정과 최근 7일 기록으로 상위 후보 3개만 압축한다.</div>';
   h1.insertAdjacentElement('afterend',box);
  }
  const s=document.createElement('script');s.src='../source-preview.js';s.defer=true;
  s.onload=()=>{const q=document.createElement('script');q.src='../fresh-primary-mode.js';q.defer=true;q.onload=()=>{const x=document.createElement('script');x.src='../fresh-primary-combo-explain.js';x.defer=true;x.onload=()=>{const c=document.createElement('script');c.src='../candidate-applicability-summary.js';c.defer=true;c.onload=()=>{const m=document.createElement('script');m.src='../candidate-mobile-evidence-summary.js';m.defer=true;m.onload=()=>{const v=document.createElement('script');v.src='../candidate-evidence-compare.js';v.defer=true;v.onload=()=>{const l=document.createElement('script');l.src='../candidate-evidence-lineage.js';l.defer=true;l.onload=()=>{const f=document.createElement('script');f.src='../combo-applicability-context.js';f.defer=true;document.head.appendChild(f)};document.head.appendChild(l)};document.head.appendChild(v)};document.head.appendChild(m)};document.head.appendChild(c)};document.head.appendChild(x)};document.head.appendChild(q)};
  document.head.appendChild(s);
 }
})();
