(function(){
 if(!/\/today\/?(?:index\.html)?$/.test(location.pathname)) return;
 const state={assessments:[],evidence:[]};
 function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 function plantId(label){const a=label.querySelector('details.evidence a[href*="../plant/"]');if(!a)return'';const m=a.getAttribute('href').match(/\.\.\/plant\/([^/]+)\//);return m?decodeURIComponent(m[1]):''}
 function assessmentFor(id){return state.assessments.find(a=>a.plant_id===id&&Array.isArray(a.evidence_ids))||null}
 function isIberaPrimary(e){return e?.scope==='subspecies_direct_wild_diet'&&/Testudo graeca ibera/i.test(e?.taxon||'')}
 function linkedPrimarySource(id){const a=assessmentFor(id);if(!a)return null;for(const eid of a.evidence_ids){const e=state.evidence.find(x=>x.id===eid);if(e&&isIberaPrimary(e))return e}return null}
 function qualityLabel(e){if(!e)return'출처 품질 미등록';if(['peer_reviewed','field_observation_paper','peer_reviewed_context'].includes(e.type))return'학술문헌';if(e.type==='specialist_group_species_account')return'전문가 종 계정';if(['official_database','official_agriculture_database','official_biodiversity_agriculture'].includes(e.type))return'공식·공공 DB';if(['specialist_husbandry','specialist_veterinary_review','specialist_plant_database'].includes(e.type))return'전문기관 자료';if(e.type==='conference_proceedings')return'학술대회 자료';return'기타 출처'}
 function textOf(box,selector,fallback){return (box.querySelector(selector)?.textContent||fallback).trim()}
 function syncOpen(details){details.open=!matchMedia('(max-width:640px)').matches}
 function enhance(label){
  if(label.dataset.mobileEvidenceSummary==='1')return;
  const box=label.querySelector('.candidate-applicability');if(!box)return;
  const id=plantId(label);if(!id)return;
  const applicability=textOf(box,'.candidate-applicability-head b','적용성 확인 필요');
  const freqNode=box.querySelector('.candidate-frequency');
  const frequency=freqNode?(freqNode.classList.contains('missing')?'빈도 미구조화':textOf(freqNode,'b','빈도 등록')):'빈도 미등록';
  const quality=qualityLabel(linkedPrimarySource(id));
  const children=[...box.childNodes];
  const badges=document.createElement('div');badges.className='candidate-context-summary';badges.innerHTML='<span class="context-chip applicability-chip">'+esc(applicability)+'</span><span class="context-chip frequency-chip">'+esc(frequency)+'</span><span class="context-chip quality-chip">'+esc(quality)+'</span>';
  const details=document.createElement('details');details.className='candidate-context-details';
  const summary=document.createElement('summary');summary.textContent='근거 맥락 자세히 보기';details.appendChild(summary);
  const body=document.createElement('div');body.className='candidate-context-body';children.forEach(n=>body.appendChild(n));details.appendChild(body);
  box.appendChild(badges);box.appendChild(details);syncOpen(details);
  label.dataset.mobileEvidenceSummary='1';
 }
 function enhanceAll(){document.querySelectorAll('#candidates label.candidate').forEach(enhance)}
 function addStyle(){if(document.getElementById('candidate-mobile-evidence-style'))return;const s=document.createElement('style');s.id='candidate-mobile-evidence-style';s.textContent='.candidate-context-summary{display:flex;gap:5px;flex-wrap:wrap;align-items:center}.context-chip{display:inline-flex;align-items:center;border:1px solid #d7e0d8;border-radius:999px;padding:3px 7px;font-size:11px;font-weight:800;line-height:1.25;background:#fff}.applicability-chip{background:#eef5ef}.frequency-chip{background:#fff7e8}.quality-chip{background:#eef4ff}.candidate-context-details{margin-top:7px}.candidate-context-details>summary{cursor:pointer;font-size:12px;font-weight:800;color:#425649}.candidate-context-body{margin-top:7px;padding-top:7px;border-top:1px dashed #dfe9e1}@media(max-width:640px){.candidate-applicability{padding:8px}.candidate-context-summary{gap:4px}.context-chip{font-size:10px;padding:3px 6px}.candidate-context-details:not([open]){margin-bottom:0}.candidate-context-details>summary{min-height:30px;display:flex;align-items:center}.candidate-context-body .candidate-applicability-head{margin-top:2px}}';document.head.appendChild(s)}
 addStyle();Promise.all([fetch('../data/assessments.json').then(r=>r.json()),fetch('../data/evidence.json').then(r=>r.json())]).then(([a,e])=>{state.assessments=Array.isArray(a)?a:[];state.evidence=Array.isArray(e)?e:[];enhanceAll()}).catch(()=>enhanceAll());
 new MutationObserver(()=>setTimeout(enhanceAll,0)).observe(document.body,{childList:true,subtree:true});
})();
