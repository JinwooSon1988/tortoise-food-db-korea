(()=>{
const ROOT='../../';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function load(){
  const id=location.pathname.split('/').filter(Boolean).pop();
  if(!id)return;
  let data;
  try{const r=await fetch(ROOT+'data/ibera_direct_feeding_evidence_v56.json',{cache:'no-store'});if(!r.ok)return;data=await r.json()}catch(e){return}
  const rows=(data.observations||[]).filter(x=>x.plant_id===id);
  if(!rows.length)return;
  const sources=new Map((data.sources||[]).map(s=>[s.source_id,s]));
  const exact=rows.filter(x=>x.identity_scope==='exact_species');
  const section=document.createElement('section');
  section.className='card v56-ibera-direct';
  section.setAttribute('aria-labelledby','v56IberaDirectTitle');
  section.innerHTML=`<h2 id="v56IberaDirectTitle">이베라 야생 직접 섭식 근거</h2><p class="small">실제 야생 <i>Testudo graeca ibera</i>의 섭식 관찰이다. 사육 급여 비율·매일 급여·무제한 안전성을 뜻하지 않는다.</p><div class="v56-ibera-direct-list">${rows.map(row=>{const s=sources.get(row.source_id)||{};const scope=row.identity_scope==='exact_species'?'식물 종까지 일치':'속 수준 관찰';return `<article class="v56-ibera-direct-item"><strong>${esc(row.source_plant)}</strong> · <span>${esc(scope)}</span><br><small>${esc(s.location||'지역 확인 필요')} · ${esc(s.study_period||'기간 확인 필요')} · ${esc(row.observed_part||'섭식 부위 확인 필요')}</small>${s.url?`<br><a href="${esc(s.url)}" rel="noopener noreferrer">원 연구 확인</a>`:''}</article>`}).join('')}</div>${exact.length?'<p class="v56-note"><b>정체성 범위:</b> 이 항목에는 현재 DB 식물과 종 수준까지 일치하는 직접 관찰이 있다.</p>':'<p class="v56-note"><b>정체성 범위:</b> 직접 관찰은 있으나 식물은 속 수준으로만 확인됐다. 현재 DB 식물의 정확한 종을 먹었다는 뜻으로 확대하지 않는다.</p>'}`;
  const identity=document.querySelector('.v56-identity');
  if(identity)identity.insertAdjacentElement('afterend',section);else document.querySelector('main')?.append(section);
}
document.addEventListener('DOMContentLoaded',load);
})();
