(()=>{
const ROOT='../../';
const LEVEL={supported_mixed_diet:['🟢','혼합식으로 활용 가능'],limited_mixed_diet:['🟡','제한적으로 혼합 급여'],limited_supplement:['🟠','가끔 보조적으로 급여'],supplement_general_evidence:['🟠','가끔 보조적으로 급여'],general_reptile_supplement:['🟠','가끔 보조적으로 급여'],do_not_feed:['🔴','급여하지 않음']};
const SCOPE={Mediterranean_Testudo:'지중해 Testudo 적용 근거',Tortoise_general:'육지거북 일반 근거',Herbivorous_reptile_general:'초식 파충류 일반 근거',Sulcata:'설카타 근거'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function j(url){try{const r=await fetch(url);return r.ok?await r.json():[]}catch(e){return[]}}
function best(a){return a.find(x=>x.species_group==='Mediterranean_Testudo')||a.find(x=>x.species_group==='Tortoise_general')||a[0]||null}
async function boot(){
 const id=location.pathname.split('/').filter(Boolean).pop(); if(!id)return;
 const assessmentUrls=[ROOT+'data/assessments.json',...Array.from({length:12},(_,i)=>ROOT+'data/assessments_korea_addendum'+(i?'_'+(i+1):'')+'.json')];
 const [plants,retail,...sets]=await Promise.all([j(ROOT+'data/plants.json'),j(ROOT+'data/korean_retail_name_map.json'),...assessmentUrls.map(j)]);
 const p=plants.find(x=>x.id===id); if(!p)return; const r=retail.find(x=>x.plant_id===id)||{}; const a=best(sets.flat().filter(x=>x.plant_id===id));
 const l=a&&LEVEL[a.verdict]?LEVEL[a.verdict]:['⚪','판정 보류']; const family=p.family||p.family_modern||p.botanical_family||'확인 중'; const aliases=[...(p.aliases||[]),...(r.retail_terms||[]),...(r.aliases||[])].filter(Boolean); const uniq=[...new Set(aliases)].slice(0,8);
 const box=document.createElement('section');box.className='card v56-identity';box.innerHTML=`<div class="v56-photo"><span>🌿</span><small>검증된 이미지 준비 중</small></div><div><div class="v56-level"><b>${l[0]} ${esc(l[1])}</b></div><dl><dt>국명</dt><dd>${esc(p.ko||id)}</dd><dt>영명</dt><dd>${esc(p.en||'확인 중')}</dd><dt>학명</dt><dd><i>${esc(p.scientific||r.master_scientific||'확인 중')}</i></dd><dt>과명</dt><dd>${esc(family)}</dd>${uniq.length?`<dt>다른 이름</dt><dd>${esc(uniq.join(' · '))}</dd>`:''}<dt>적용 대상</dt><dd>${esc(a?.applicability_note||(a?.species_group?(SCOPE[a.species_group]||a.species_group):'확인 필요'))}</dd><dt>근거 등급</dt><dd>${esc(a?.evidence_grade||a?.grade||'확인 필요')}</dd></dl><p class="v56-note">사진과 유통명만으로 식물 종을 확정하지 않는다. 급여 단계는 단독 주식·무제한 급여나 임의의 주간 횟수·식단 비율을 뜻하지 않는다.</p></div>`;
 const h1=document.querySelector('h1'); if(h1)h1.insertAdjacentElement('afterend',box);
}
document.addEventListener('DOMContentLoaded',boot);
})();
