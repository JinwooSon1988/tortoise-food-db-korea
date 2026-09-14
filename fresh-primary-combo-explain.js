(function(){
 if(!/\/today\/?(?:index\.html)?$/.test(location.pathname)) return;
 const state={plants:[],assessments:[],evidence:[],frequency:[]};
 function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 function plantId(label){const a=label.querySelector('details.evidence a[href*="../plant/"]');if(!a)return'';const m=a.getAttribute('href').match(/\.\.\/plant\/([^/]+)\//);return m?decodeURIComponent(m[1]):''}
 function familyFor(id){return state.plants.find(p=>p.id===id)?.family||''}
 function recentCount(label){for(const tag of label.querySelectorAll('.tag')){const m=(tag.textContent||'').trim().match(/^최근 7일\s+(\d+)회$/);if(m)return Number(m[1])}return null}
 function nameFor(label,id){return (label.querySelector('div > b')?.textContent||id||'식물').trim()}
 function verdictFor(label){for(const tag of label.querySelectorAll('.tag')){const t=(tag.textContent||'').trim();if(!t.startsWith('최근 7일')&&!t.includes('집에 있음')&&!t.includes('이베라 1차 직접근거'))return t}return''}
 function assessmentFor(id){return state.assessments.find(a=>a.plant_id===id&&Array.isArray(a.evidence_ids))||null}
 function isIberaPrimary(e){return e?.scope==='subspecies_direct_wild_diet'&&/Testudo graeca ibera/i.test(e?.taxon||'')}
 function linkedPrimarySource(id){const a=assessmentFor(id);if(!a)return null;for(const eid of a.evidence_ids){const e=state.evidence.find(x=>x.id===eid);if(e&&isIberaPrimary(e))return e}return null}
 function sourceHref(e){if(!e)return'';if(e.url)return e.url;if(e.doi)return 'https://doi.org/'+encodeURIComponent(e.doi);if(e.pmid)return 'https://pubmed.ncbi.nlm.nih.gov/'+encodeURIComponent(e.pmid)+'/';return''}
 function sourceHTML(id){const e=linkedPrimarySource(id);if(!e)return '<div class="small fresh-source-missing">연결된 이베라 1차 출처 메타데이터 없음</div>';const href=sourceHref(e);return '<div class="fresh-primary-source"><div class="small"><b>연결된 이베라 1차 출처</b></div><div class="small">'+esc(e.citation||e.id)+'</div>'+(href?'<a href="'+esc(href)+'" target="_blank" rel="noopener noreferrer">원문/식별자 열기 ↗</a>':'<div class="small fresh-source-missing">공개 원문 링크/식별자 미등록</div>')+frequencyHTML(id,e.id)+'</div>'}
 function frequencyFor(id,sourceId){return state.frequency.find(x=>x.plant_id===id&&x.source_id===sourceId)||null}
 function frequencyHTML(id,sourceId){const f=frequencyFor(id,sourceId);if(!f)return '<div class="small fresh-frequency-missing">이 연결 출처에는 현재 구조화된 식물별 야생 관찰 빈도값이 없다.</div>';return '<div class="fresh-frequency"><span class="fresh-frequency-label">야생 관찰 빈도 · 급여비율 아님</span><b>'+esc(f.label_ko||f.frequency_class||'')+'</b><div class="small">논문 기록 분류군: '+esc(f.taxon_reported||'미등록')+(f.part_reported?' · 부위: '+esc(f.part_reported):'')+'</div><div class="small">'+esc(f.interpretation_note||'야생 관찰 빈도이며 사육 급여비율로 사용하지 않는다.')+'</div></div>'}
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
   return '<div class="fresh-explain-item"><b>'+esc(name)+'</b>'+(verdict?'<span class="fresh-explain-verdict">'+esc(verdict)+'</span>':'')+'<div class="small">'+reasons.map(esc).join(' · ')+'</div>'+(family?'<div class="small">식물 과: '+esc(family)+'</div>':'')+sourceHTML(id)+'</div>';
  }).join('');
  note.innerHTML='<div class="fresh-explain"><b>왜 이 3종을 골랐나</b>'+rows+'<div class="small fresh-explain-limit">각 출처는 해당 식물 판정에 이미 연결된 이베라 1차 야생섭식 자료 중 첫 번째 공개 메타데이터만 보여준다. 빈도값은 논문에 식물별 분류가 실제 기록되고 별도 구조화된 경우에만 표시한다. Low·Moderate·High 및 백분율 구간은 야생 관찰 빈도 분류이며 사육 급여비율이 아니다. 이 설명은 급여량·배합률·영양완전성·건강효과를 계산하거나 보장하지 않는다.</div></div>';
 }
 function bind(){const btn=document.getElementById('freshCombo3');if(!btn||btn.dataset.explainBound==='1')return;btn.dataset.explainBound='1';btn.addEventListener('click',()=>setTimeout(renderExplain,0))}
 function addStyle(){if(document.getElementById('fresh-combo-explain-style'))return;const s=document.createElement('style');s.id='fresh-combo-explain-style';s.textContent='.fresh-explain{margin-top:8px;padding-top:8px;border-top:1px solid #dce5dd}.fresh-explain-item{padding:8px 0;border-top:1px solid #edf1ed}.fresh-explain-item:first-of-type{margin-top:5px}.fresh-explain-verdict{display:inline-block;margin-left:6px;border:1px solid #dce5dd;border-radius:999px;padding:2px 6px;font-size:11px}.fresh-primary-source{margin-top:6px;padding:7px;border:1px solid #dfe9e1;border-radius:8px;background:#fbfdfb}.fresh-primary-source a{display:inline-block;margin-top:4px;font-size:12px;font-weight:700}.fresh-source-missing,.fresh-frequency-missing{margin-top:5px;color:#6b746d}.fresh-frequency{margin-top:7px;padding-top:7px;border-top:1px dashed #dfe9e1}.fresh-frequency-label{display:inline-block;margin-right:6px;padding:2px 6px;border-radius:999px;background:#eef5ef;font-size:11px;font-weight:700}.fresh-frequency b{font-size:13px}.fresh-explain-limit{margin-top:6px;padding-top:6px;border-top:1px dashed #dce5dd}';document.head.appendChild(s)}
 addStyle();
 Promise.all([fetch('../data/plants.json').then(r=>r.json()),fetch('../data/assessments.json').then(r=>r.json()),fetch('../data/evidence.json').then(r=>r.json()),fetch('../data/wild_observation_frequency.json').then(r=>r.json())]).then(([p,a,e,f])=>{state.plants=Array.isArray(p)?p:[];state.assessments=Array.isArray(a)?a:[];state.evidence=Array.isArray(e)?e:[];state.frequency=Array.isArray(f)?f:[];bind()}).catch(()=>bind());
 bind();new MutationObserver(bind).observe(document.body,{childList:true,subtree:true});
})();
