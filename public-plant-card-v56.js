(()=>{
const LEVEL={
 supported_mixed_diet:['🟢','혼합식으로 활용 가능','비교적 직접적인 육지거북/적용군 근거가 있는 혼합식 후보다. 단독 주식·무제한 급여를 뜻하지 않는다.'],
 limited_mixed_diet:['🟡','제한적으로 혼합 급여','혼합식에 사용할 수 있으나 근거 또는 사용 범위에 제한이 있다.'],
 limited_supplement:['🟠','가끔 보조적으로 급여','보조적 사용 범위로 제한한다.'],
 supplement_general_evidence:['🟠','가끔 보조적으로 급여','일반 육지거북 수준 근거에 의존하므로 보조적 사용으로 제한한다.'],
 general_reptile_supplement:['🟠','가끔 보조적으로 급여','근거 적용성이 낮아 보조적 사용 이상으로 확대하지 않는다.'],
 do_not_feed:['🔴','급여하지 않음','현재 판정에서는 급여 대상에서 제외한다.']
};
const SCOPE={Mediterranean_Testudo:'지중해 Testudo 적용 근거',Tortoise_general:'육지거북 일반 근거',Herbivorous_reptile_general:'초식 파충류 일반 근거',Sulcata:'설카타 근거'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function family(p){return p.family||p.family_modern||p.botanical_family||'과명 확인 중'}
function level(a){return a&&LEVEL[a.verdict]?LEVEL[a.verdict]:['⚪','판정 보류','동정 또는 근거가 해결되지 않아 급여 가능으로 판단하지 않는다.']}
function render(rows,ctx){
 if(!rows.length){ctx.results.innerHTML='<p class="small">일치하는 먹이를 찾지 못했다. 다른 유통명이나 학명으로 검색해 본다.</p>';return}
 ctx.results.innerHTML=rows.slice(0,8).map(r=>{const a=ctx.bestAssessment(r.plant_id),l=level(a),scope=a?.applicability_note||(a?.species_group?(SCOPE[a.species_group]||'적용 범위: '+a.species_group):'적용 범위를 상세 페이지에서 확인한다.'),grade=a?.evidence_grade||a?.grade||'확인 필요',aliases=(r.aliases||[]).filter(Boolean).slice(0,4).join(' · ');return `<article class="resultcard public-v56"><div class="plant-thumb" role="img" aria-label="${esc(r.label)} 검증 이미지 준비 중"><span>🌿</span><small>검증된 이미지 준비 중</small></div><div class="resultbody"><div class="resulttop"><div><h3>${esc(r.label)}</h3><div class="names"><span><b>영명</b> ${esc(r.en||'확인 중')}</span><span><b>학명</b> <i>${esc(r.scientific||'확인 중')}</i></span><span><b>과명</b> ${esc(r.family||'확인 중')}</span>${aliases?`<span><b>다른 이름</b> ${esc(aliases)}</span>`:''}</div></div><div class="feed-level ${a?.verdict==='do_not_feed'?'no-feed':''}"><strong>${l[0]} ${esc(l[1])}</strong><small>${esc(l[2])}</small></div></div><div class="evidence-row"><span><b>적용 대상</b> ${esc(scope)}</span><span><b>근거 등급</b> ${esc(grade)}</span></div><p class="resultwhy">${esc(a?.why||'현재 공개 근거와 적용 범위를 상세 페이지에서 확인한다.')}</p><div class="identity-note">사진과 유통명만으로 식물 종을 확정하지 않는다.</div><div class="resultactions"><a class="detailbtn" href="./plant/${encodeURIComponent(r.plant_id)}/">상세 근거 보기 →</a><a class="todaybtn" href="./today/">오늘 식단 후보 보기</a></div></div></article>`}).join('');
 ctx.results.scrollIntoView({behavior:'smooth',block:'nearest'});
}
window.TFDPublicPlantCardV56={render,family};
})();
