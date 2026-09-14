(function(){
 if(!/\/today\/?(?:index\.html)?$/.test(location.pathname)) return;
 let mode='base',scheduled=false;
 function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 function plantId(label){const a=label.querySelector('details.evidence a[href*="../plant/"]');if(!a)return'';const m=a.getAttribute('href').match(/\.\.\/plant\/([^/]+)\//);return m?decodeURIComponent(m[1]):''}
 function nameOf(label){const d=label.querySelector(':scope > div > b');return (d?.textContent||plantId(label)||'이름 미등록').trim()}
 function chip(label,cls,fallback){return (label.querySelector('.'+cls)?.textContent||fallback).trim()}
 function visibleRows(){return [...document.querySelectorAll('#candidates label.candidate')].filter(x=>!x.hidden).map((label,index)=>({
  label,index,id:plantId(label),name:nameOf(label),
  applicability:chip(label,'applicability-chip','적용성 미등록'),
  frequency:chip(label,'frequency-chip','빈도 미등록'),
  quality:chip(label,'quality-chip','출처 품질 미등록')
 }))}
 function key(r){
  if(mode==='exact')return r.applicability==='정확한 종 직접근거'?0:1;
  if(mode==='frequency')return /^빈도 (?:미구조화|미등록)$/.test(r.frequency)?1:0;
  if(mode==='academic')return r.quality==='학술문헌'?0:1;
  return 0;
 }
 function modeLabel(){return mode==='exact'?'정확한 종 직접근거 우선':mode==='frequency'?'야생 관찰 빈도 자료 있음 우선':mode==='academic'?'학술문헌 출처 우선':'기본 비교순서'}
 function addControls(){
  if(document.getElementById('evidence-compare-card'))return;
  const candidates=document.getElementById('candidates');if(!candidates)return;
  const box=document.createElement('section');box.id='evidence-compare-card';box.className='card evidence-compare-card';
  box.innerHTML='<b>근거 비교 보기</b><div class="small">후보를 근거 관점으로만 비교한다. 이 비교순서는 먹이 추천 점수나 급여 우선순위가 아니며, 아래 실제 후보 목록·판정·필터·빠른 조합 순서는 바꾸지 않는다.</div><div class="evidence-compare-controls"><button type="button" data-compare-mode="base" class="source-filter active">기본</button><button type="button" data-compare-mode="exact" class="source-filter">정확한 종 근거 우선</button><button type="button" data-compare-mode="frequency" class="source-filter">빈도 자료 있음 우선</button><button type="button" data-compare-mode="academic" class="source-filter">학술출처 우선</button></div><div id="evidence-compare-status" class="small"></div><div id="evidence-compare-list"></div>';
  candidates.insertAdjacentElement('beforebegin',box);
  box.querySelectorAll('[data-compare-mode]').forEach(b=>b.addEventListener('click',()=>{mode=b.dataset.compareMode;box.querySelectorAll('[data-compare-mode]').forEach(x=>x.classList.toggle('active',x===b));render()}));
 }
 function render(){
  addControls();const list=document.getElementById('evidence-compare-list'),status=document.getElementById('evidence-compare-status');if(!list||!status)return;
  const rows=visibleRows();const sorted=[...rows].sort((a,b)=>key(a)-key(b)||a.index-b.index);
  status.textContent='현재 비교 기준: '+modeLabel()+' · 화면에 표시된 후보 '+rows.length+'종. 같은 그룹 안에서는 기존 후보 순서를 유지한다.';
  if(!sorted.length){list.innerHTML='<div class="small evidence-compare-empty">현재 필터에서 비교할 표시 후보가 없다.</div>';return}
  list.innerHTML=sorted.map(r=>'<div class="evidence-compare-row" data-compare-id="'+esc(r.id)+'"><div class="evidence-compare-name"><b>'+esc(r.name)+'</b></div><div class="evidence-compare-chips"><span class="context-chip applicability-chip">'+esc(r.applicability)+'</span><span class="context-chip frequency-chip">'+esc(r.frequency)+'</span><span class="context-chip quality-chip">'+esc(r.quality)+'</span></div><button type="button" class="evidence-compare-jump secondary" data-jump-id="'+esc(r.id)+'">후보로 이동</button></div>').join('');
  list.querySelectorAll('[data-jump-id]').forEach(b=>b.onclick=()=>{const id=b.dataset.jumpId;const target=rows.find(r=>r.id===id)?.label;if(target)target.scrollIntoView({behavior:'smooth',block:'center'})});
 }
 function schedule(){if(scheduled)return;scheduled=true;setTimeout(()=>{scheduled=false;render()},20)}
 function addStyle(){if(document.getElementById('candidate-evidence-compare-style'))return;const s=document.createElement('style');s.id='candidate-evidence-compare-style';s.textContent='.evidence-compare-card{border:2px solid #d6e1d8}.evidence-compare-controls{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}.evidence-compare-row{display:grid;grid-template-columns:minmax(120px,1fr) minmax(260px,2fr) auto;gap:8px;align-items:center;padding:9px 0;border-top:1px solid #edf1ed}.evidence-compare-row:first-child{border-top:0}.evidence-compare-chips{display:flex;gap:4px;flex-wrap:wrap}.evidence-compare-jump{min-height:34px;padding:6px 9px;font-size:12px}.evidence-compare-empty{padding:8px 0}@media(max-width:640px){.evidence-compare-row{grid-template-columns:1fr}.evidence-compare-jump{width:max-content}.evidence-compare-controls button{flex:1 1 46%}}';document.head.appendChild(s)}
 addStyle();addControls();schedule();
 document.addEventListener('tfd:applicability-filter-changed',schedule);
 ['directCandidateOnly','freshPrimaryOnly','pantryOnly'].forEach(id=>document.addEventListener('change',e=>{if(e.target?.id===id)schedule()}));
 new MutationObserver(schedule).observe(document.getElementById('candidates')||document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','class','data-mobile-evidence-summary']});
})();
