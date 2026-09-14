(function(){
 if(!/\/today\/?(?:index\.html)?$/.test(location.pathname)) return;
 const state={plants:[]};
 function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 function plantId(label){const a=label.querySelector('details.evidence a[href*="../plant/"]');if(!a)return'';const m=a.getAttribute('href').match(/\.\.\/plant\/([^/]+)\//);return m?decodeURIComponent(m[1]):''}
 function familyFor(id){return state.plants.find(p=>p.id===id)?.family||''}
 function recentCount(label){for(const tag of label.querySelectorAll('.tag')){const m=(tag.textContent||'').trim().match(/^최근 7일\s+(\d+)회$/);if(m)return Number(m[1])}return null}
 function nameFor(label,id){return (label.querySelector('div > b')?.textContent||id||'식물').trim()}
 function verdictFor(label){for(const tag of label.querySelectorAll('.tag')){const t=(tag.textContent||'').trim();if(!t.startsWith('최근 7일')&&!t.includes('집에 있음')&&!t.includes('이베라 1차 직접근거'))return t}return''}
 function renderExplain(){
  const note=document.getElementById('fresh-combo-note');
  if(!note) return;
  const selected=[...document.querySelectorAll('#candidates label.candidate')].filter(label=>!label.hidden&&label.querySelector('input[type="checkbox"][data-id]:checked'));
  if(!selected.length) return;
  const seenFamilies=new Set();
  const rows=selected.map(label=>{
   const id=plantId(label),name=nameFor(label,id),family=familyFor(id),recent=recentCount(label),verdict=verdictFor(label);
   const familyReason=family?(seenFamilies.has(family)?'식물 과 중복이지만 남은 빠른 후보 중 3종 구성을 위해 포함':'다른 식물 과를 확보해 조합 내 과 다양성에 기여'):'식물 과 정보가 없어 과 다양성 판단에는 사용하지 않음';
   if(family)seenFamilies.add(family);
   const reasons=['이베라 1차 야생섭식 직접근거 연결',recent===0?'최근 7일 급여기록 0회':'최근 7일 기록 '+String(recent??'확인불가')+'회',familyReason];
   return '<div class="fresh-explain-item"><b>'+esc(name)+'</b>'+(verdict?'<span class="fresh-explain-verdict">'+esc(verdict)+'</span>':'')+'<div class="small">'+reasons.map(esc).join(' · ')+'</div>'+(family?'<div class="small">식물 과: '+esc(family)+'</div>':'')+'</div>';
  }).join('');
  note.innerHTML='<div class="fresh-explain"><b>왜 이 3종을 골랐나</b>'+rows+'<div class="small fresh-explain-limit">이 설명은 현재 빠른 선택 조건과 식물 과 다양성에 따른 선택 이유만 보여준다. 급여량·배합률·영양완전성·건강효과를 계산하거나 보장하지 않는다.</div></div>';
 }
 function bind(){const btn=document.getElementById('freshCombo3');if(!btn||btn.dataset.explainBound==='1')return;btn.dataset.explainBound='1';btn.addEventListener('click',()=>setTimeout(renderExplain,0))}
 function addStyle(){if(document.getElementById('fresh-combo-explain-style'))return;const s=document.createElement('style');s.id='fresh-combo-explain-style';s.textContent='.fresh-explain{margin-top:8px;padding-top:8px;border-top:1px solid #dce5dd}.fresh-explain-item{padding:8px 0;border-top:1px solid #edf1ed}.fresh-explain-item:first-of-type{margin-top:5px}.fresh-explain-verdict{display:inline-block;margin-left:6px;border:1px solid #dce5dd;border-radius:999px;padding:2px 6px;font-size:11px}.fresh-explain-limit{margin-top:6px;padding-top:6px;border-top:1px dashed #dce5dd}';document.head.appendChild(s)}
 addStyle();
 fetch('../data/plants.json').then(r=>r.json()).then(p=>{state.plants=Array.isArray(p)?p:[];bind()}).catch(()=>bind());
 bind();new MutationObserver(bind).observe(document.body,{childList:true,subtree:true});
})();
