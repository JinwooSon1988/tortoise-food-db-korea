(function(){
 if(!/\/today\/?(?:index\.html)?$/.test(location.pathname)) return;
 const state={lineage:[],evidence:[]};
 function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 function hrefFor(e){if(!e)return'';if(e.url)return e.url;if(e.doi)return'https://doi.org/'+encodeURIComponent(e.doi);if(e.pmid)return'https://pubmed.ncbi.nlm.nih.gov/'+encodeURIComponent(e.pmid)+'/';return''}
 function matchLabel(level){return ({exact_species:'정확한 종 일치',genus_only:'속 수준 기록',congeneric_species:'같은 속의 다른 종'}[level]||'적용성 메타데이터 미등록')}
 function sourceFor(id){return state.evidence.find(e=>e.id===id)||null}
 function lineageFor(id){return state.lineage.find(x=>x.plant_id===id)||null}
 function renderKnown(row,id,item){
  const e=sourceFor(item.source_id),href=hrefFor(e),reported=(item.reported_taxa||[]).join(', ')||'논문 기록 분류군 미등록';
  row.innerHTML='<summary>근거 계보 보기</summary><div class="lineage-note">이베라 직접근거와 식물 종 일치도는 서로 다른 축이다. 아래 계보는 관찰 사실이 DB 식물에 어디까지 적용되는지를 보여준다.</div><div class="lineage-flow"><div class="lineage-node"><span>1 · DB 식물</span><b>'+esc(item.db_taxon||id)+'</b></div><div class="lineage-arrow">→</div><div class="lineage-node"><span>2 · 논문 기록 식물</span><b>'+esc(reported)+'</b><small>'+esc(matchLabel(item.plant_match_level))+'</small></div><div class="lineage-arrow">→</div><div class="lineage-node"><span>3 · 이베라 관찰</span><b>'+esc(item.observation||'직접 관찰 설명 미등록')+'</b></div><div class="lineage-arrow">→</div><div class="lineage-node limit"><span>4 · 사육 적용 한계</span><b>'+esc(item.application_limit||'적용 한계 메타데이터 미등록')+'</b></div></div><div class="lineage-source"><b>연결 1차 출처</b><div>'+esc(e?.citation||item.source_id)+'</div>'+(href?'<a href="'+esc(href)+'" target="_blank" rel="noopener noreferrer">원문/식별자 열기 ↗</a>':'')+'</div><div class="small lineage-safety">이 계보는 섭식관찰의 전달 범위를 설명할 뿐이며 급여량·배합률·영양완전성·건강효과를 계산하지 않는다.</div>';
 }
 function renderMissing(row){row.innerHTML='<summary>근거 계보 보기</summary><div class="lineage-note"><b>현재 구조화된 이베라 직접 근거 계보 없음</b><br>계보 미등록은 이 식물이 위험하거나 부적합하다는 뜻이 아니다. 연결된 근거를 임의로 추론해 만들지 않는다.</div>'}
 function enhance(){
  document.querySelectorAll('#evidence-compare-list .evidence-compare-row').forEach(r=>{
   if(r.dataset.lineageReady==='1')return;const id=r.dataset.compareId;if(!id)return;
   const d=document.createElement('details');d.className='evidence-lineage';const item=lineageFor(id);item?renderKnown(d,id,item):renderMissing(d);r.appendChild(d);r.dataset.lineageReady='1';
  });
 }
 function style(){if(document.getElementById('evidence-lineage-style'))return;const s=document.createElement('style');s.id='evidence-lineage-style';s.textContent='.evidence-lineage{grid-column:1/-1;border:1px solid #dce5dd;border-radius:10px;padding:8px 10px;background:#fbfdfb}.evidence-lineage>summary{cursor:pointer;font-weight:800;font-size:12px}.lineage-note{font-size:12px;color:#5f6b62;margin:8px 0}.lineage-flow{display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;gap:6px;align-items:stretch}.lineage-node{border:1px solid #dfe7e0;border-radius:9px;padding:8px;background:#fff}.lineage-node span{display:block;font-size:10px;color:#657067;font-weight:800;margin-bottom:4px}.lineage-node b{display:block;font-size:12px;line-height:1.45}.lineage-node small{display:block;margin-top:4px;color:#657067}.lineage-node.limit{background:#fff9ef;border-color:#ead8b7}.lineage-arrow{display:flex;align-items:center;font-weight:900;color:#758177}.lineage-source{margin-top:8px;padding-top:8px;border-top:1px dashed #dce5dd;font-size:11px}.lineage-source a{display:inline-block;margin-top:4px;font-weight:800}.lineage-safety{margin-top:7px}@media(max-width:700px){.lineage-flow{grid-template-columns:1fr}.lineage-arrow{justify-content:center;transform:rotate(90deg);height:16px}.evidence-lineage{padding:8px}}';document.head.appendChild(s)}
 style();Promise.all([fetch('../data/evidence_lineage.json').then(r=>r.json()),fetch('../data/evidence.json').then(r=>r.json())]).then(([l,e])=>{state.lineage=Array.isArray(l)?l:[];state.evidence=Array.isArray(e)?e:[];enhance();new MutationObserver(()=>setTimeout(enhance,0)).observe(document.getElementById('evidence-compare-list')||document.body,{childList:true,subtree:true})}).catch(()=>{});
})();
