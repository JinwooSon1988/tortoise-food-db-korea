(function(){
 if(!/\/today\/?(?:index\.html)?$/.test(location.pathname)) return;
 const state={plants:[],assessments:[],evidence:[],frequency:[],mode:'all'};
 function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 function plantId(label){const a=label.querySelector('details.evidence a[href*="../plant/"]');if(!a)return'';const m=a.getAttribute('href').match(/\.\.\/plant\/([^/]+)\//);return m?decodeURIComponent(m[1]):''}
 function plantFor(id){return state.plants.find(p=>p.id===id)||null}
 function assessmentFor(id){return state.assessments.find(a=>a.plant_id===id&&Array.isArray(a.evidence_ids))||null}
 function isIberaPrimary(e){return e?.scope==='subspecies_direct_wild_diet'&&/Testudo graeca ibera/i.test(e?.taxon||'')}
 function linkedPrimarySource(id){const a=assessmentFor(id);if(!a)return null;for(const eid of a.evidence_ids){const e=state.evidence.find(x=>x.id===eid);if(e&&isIberaPrimary(e))return e}return null}
 function frequencyFor(id,sourceId){return state.frequency.find(x=>x.plant_id===id&&x.source_id===sourceId)||null}
 function cleanTaxon(s){return String(s||'').replace(/\s+/g,' ').trim().replace(/\.$/,'')}
 function isGenericTaxon(s){return /\b(?:sp|spp)\.?$/i.test(cleanTaxon(s))}
 function genusOf(s){return cleanTaxon(s).split(' ')[0]||''}
 function applicabilityFor(id){
  const src=linkedPrimarySource(id);if(!src)return null;
  const p=plantFor(id),f=frequencyFor(id,src.id);
  if(!f)return {level:'unknown',label:'식물 수준 적용성 확인 필요',text:'이베라 1차 직접근거는 연결되어 있지만, 현재 DB에는 이 출처의 식물 분류군 적용성 값이 구조화되어 있지 않다.'};
  const db=cleanTaxon(p?.scientific),reported=cleanTaxon(f.taxon_reported);
  if(!db||!reported)return {level:'unknown',label:'식물 수준 적용성 확인 필요',text:'DB 식물명 또는 논문 기록 분류군 정보가 부족해 종 수준 일치 여부를 판정하지 않는다.'};
  const dbGeneric=isGenericTaxon(db),repGeneric=isGenericTaxon(reported),sameGenus=genusOf(db).toLowerCase()===genusOf(reported).toLowerCase();
  if(!dbGeneric&&!repGeneric&&db.toLowerCase()===reported.toLowerCase())return {level:'exact',label:'정확한 종 직접근거',text:'DB 식물 학명과 논문 기록 식물 학명이 일치한다.'};
  if(repGeneric&&sameGenus)return {level:'genus',label:'속 수준 직접근거',text:'논문은 '+reported+' 수준으로만 기록했다. 현재 DB 식물의 정확한 종이 직접 관찰됐다고 확대하지 않는다.'};
  if(dbGeneric&&!repGeneric&&sameGenus)return {level:'entry_broader',label:'논문 기록이 DB 항목보다 좁음',text:'논문은 '+reported+'를 기록했지만 DB 항목은 '+db+'처럼 더 넓다. 같은 속 전체로 자동 확대하지 않는다.'};
  if(!dbGeneric&&!repGeneric&&sameGenus)return {level:'different_species',label:'같은 속·다른 종 직접근거',text:'논문 기록 '+reported+'와 현재 DB 식물 '+db+'는 같은 속이지만 다른 종이다.'};
  return {level:'mismatch',label:'분류군 직접일치 아님',text:'논문 기록 분류군과 현재 DB 식물의 종 수준 직접 일치를 확인하지 못했다.'};
 }
 function frequencyContextFor(id){
  const src=linkedPrimarySource(id);if(!src)return null;
  const f=frequencyFor(id,src.id);
  if(!f)return {structured:false,label:'현재 구조화된 식물별 빈도값 없음',taxon:'',note:'직접 섭식근거가 있어도 식물별 정량 빈도가 공개 자료에 없거나 아직 구조화되지 않은 경우 숫자를 만들지 않는다.'};
  return {structured:true,label:f.label_ko||f.frequency_class||'빈도 등급 등록',taxon:f.taxon_reported||'',note:f.interpretation_note||'야생 관찰 빈도이며 사육 급여비율로 사용하지 않는다.'};
 }
 function isIberaProfile(){return window.TFDProfiles?.active?.()?.species==='ibera'}
 function allows(label){
  if(state.mode==='all'||!isIberaProfile())return true;
  const a=applicabilityFor(plantId(label));if(!a)return false;
  if(state.mode==='exact')return a.level==='exact';
  if(state.mode==='genus')return a.level==='exact'||a.level==='genus';
  return true;
 }
 window.TFDCandidateApplicability={allows,mode:()=>state.mode,applicabilityFor};
 function unselect(label){const cb=label.querySelector('input[type="checkbox"][data-id]');if(cb?.checked){cb.checked=false;cb.dispatchEvent(new Event('change',{bubbles:true}))}}
 function baseAllows(label){
  const quick=document.getElementById('freshPrimaryOnly'),direct=document.getElementById('directCandidateOnly');
  const primary=!!label.querySelector('.direct-evidence.primary');
  if(quick?.checked&&!quick.disabled){let recent=null;for(const tag of label.querySelectorAll('.tag')){const m=(tag.textContent||'').trim().match(/^최근 7일\s+(\d+)회$/);if(m){recent=Number(m[1]);break}}return primary&&recent===0}
  if(direct?.checked&&!direct.disabled)return primary;
  return true;
 }
 function applyFilter(){
  const ok=isIberaProfile();if(!ok&&state.mode!=='all')state.mode='all';
  document.querySelectorAll('[data-applicability-mode]').forEach(b=>{b.disabled=!ok;b.classList.toggle('active',b.dataset.applicabilityMode===state.mode)});
  const labels=[...document.querySelectorAll('#candidates label.candidate')];let visible=0;
  for(const label of labels){const show=baseAllows(label)&&allows(label);label.hidden=!show;if(show)visible++;else unselect(label)}
  let empty=document.getElementById('applicability-filter-empty');
  if(state.mode!=='all'&&labels.length&&visible===0){if(!empty){empty=document.createElement('div');empty.id='applicability-filter-empty';empty.className='card';document.getElementById('candidates')?.appendChild(empty)}empty.innerHTML='<b>현재 적용성 기준에 맞는 후보가 없다.</b><div class="small">이 결과는 다른 후보가 위험하거나 부적합하다는 뜻이 아니다. 근거의 식물 분류군 적용 범위를 엄격하게 좁혀 표시한 결과다.</div>'}else if(empty)empty.remove();
  const status=document.getElementById('applicability-filter-status');if(status){const label=state.mode==='exact'?'정확한 종 직접근거만':state.mode==='genus'?'정확한 종 + 속 수준 직접근거':'전체 적용성';status.textContent='현재 기준: '+label+' · 표시 후보 '+visible+'종 / 전체 후보 '+labels.length+'종. 이 필터는 표시만 좁히며 판정·순위·급여량을 다시 계산하지 않는다.'}
 }
 function enhance(label){
  const id=plantId(label);if(!id||label.dataset.candidateApplicability==='1')return;
  const a=applicabilityFor(id);if(!a)return;
  const f=frequencyContextFor(id),host=label.querySelector('div');if(!host)return;
  const box=document.createElement('div');box.className='candidate-applicability '+a.level;
  const freq=f?'<div class="candidate-frequency '+(f.structured?'structured':'missing')+'"><span class="candidate-frequency-label">야생 관찰 빈도 · 급여비율 아님</span><b>'+esc(f.label)+'</b>'+(f.taxon?'<div class="small">논문 기록 분류군: '+esc(f.taxon)+'</div>':'')+'<div class="small">'+esc(f.note)+'</div></div>':'';
  box.innerHTML='<div class="candidate-applicability-head"><span class="candidate-applicability-label">식물 적용성</span><b>'+esc(a.label)+'</b></div><div class="small">'+esc(a.text)+'</div>'+freq+'<div class="small candidate-context-limit">적용성과 야생 관찰 빈도는 근거 맥락을 설명할 뿐이며 급여량·배합률·영양완전성·건강효과를 판단하지 않는다.</div>';
  const details=label.querySelector('details.evidence');host.insertBefore(box,details||null);label.dataset.candidateApplicability='1';
 }
 function addControls(){
  const card=document.getElementById('source-filter-card');if(!card||document.getElementById('applicability-filter-controls'))return;
  const wrap=document.createElement('div');wrap.id='applicability-filter-controls';wrap.className='applicability-filter-controls';
  wrap.innerHTML='<b>식물 적용성 엄격도</b><div class="source-filter-row"><button type="button" class="source-filter active" data-applicability-mode="all">전체</button><button type="button" class="source-filter" data-applicability-mode="exact">정확한 종 직접근거만</button><button type="button" class="source-filter" data-applicability-mode="genus">속 수준 포함</button></div><div id="applicability-filter-status" class="small">기본값은 전체다.</div><div class="small">‘속 수준 포함’은 정확한 종 직접근거와 논문이 sp./spp. 수준으로 기록한 같은 속 직접근거까지만 포함한다. 같은 속 다른 종·DB 항목이 더 넓은 경우·적용성 미구조화 항목은 포함하지 않는다.</div>';
  card.appendChild(wrap);
  wrap.querySelectorAll('[data-applicability-mode]').forEach(b=>b.onclick=()=>{state.mode=b.dataset.applicabilityMode;applyFilter();document.dispatchEvent(new CustomEvent('tfd:applicability-filter-changed',{detail:{mode:state.mode}}))});
  ['directCandidateOnly','freshPrimaryOnly'].forEach(id=>{const el=document.getElementById(id);if(el&&!el.dataset.applicabilityBound){el.dataset.applicabilityBound='1';el.addEventListener('change',()=>setTimeout(applyFilter,0))}});
 }
 function enhanceAll(){if(!state.plants.length||!state.assessments.length||!state.evidence.length)return;document.querySelectorAll('#candidates label.candidate').forEach(enhance);addControls();applyFilter()}
 function addStyle(){if(document.getElementById('candidate-applicability-style'))return;const s=document.createElement('style');s.id='candidate-applicability-style';s.textContent='.candidate-applicability{margin:7px 0;padding:7px 8px;border:1px solid #dfe9e1;border-radius:9px;background:#fbfdfb}.candidate-applicability-head{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.candidate-applicability-label,.candidate-frequency-label{display:inline-block;margin-right:6px;padding:2px 6px;border-radius:999px;background:#eef5ef;font-size:11px;font-weight:700}.candidate-applicability b,.candidate-frequency b{font-size:12px}.candidate-frequency{margin-top:7px;padding-top:7px;border-top:1px dashed #dfe9e1}.candidate-frequency.missing{color:#6b746d}.candidate-frequency.missing .candidate-frequency-label{background:#f1f1ee}.candidate-context-limit{margin-top:7px;padding-top:7px;border-top:1px dashed #e4e9e4}.candidate-applicability.genus,.candidate-applicability.entry_broader,.candidate-applicability.different_species,.candidate-applicability.mismatch,.candidate-applicability.unknown{background:#fffaf2;border-color:#ead8b7}.candidate-applicability.genus .candidate-applicability-label,.candidate-applicability.entry_broader .candidate-applicability-label,.candidate-applicability.different_species .candidate-applicability-label,.candidate-applicability.mismatch .candidate-applicability-label,.candidate-applicability.unknown .candidate-applicability-label{background:#fff0d6}.applicability-filter-controls{margin-top:12px;padding-top:10px;border-top:1px dashed #d7e0d8}.applicability-filter-controls button:disabled{opacity:.45}';document.head.appendChild(s)}
 addStyle();
 Promise.all([fetch('../data/plants.json').then(r=>r.json()),fetch('../data/assessments.json').then(r=>r.json()),fetch('../data/evidence.json').then(r=>r.json()),fetch('../data/wild_observation_frequency.json').then(r=>r.json())]).then(([p,a,e,f])=>{state.plants=Array.isArray(p)?p:[];state.assessments=Array.isArray(a)?a:[];state.evidence=Array.isArray(e)?e:[];state.frequency=Array.isArray(f)?f:[];enhanceAll()}).catch(()=>{});
 new MutationObserver(()=>setTimeout(enhanceAll,0)).observe(document.body,{childList:true,subtree:true});
})();
