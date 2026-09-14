(function(){
 if(!/\/today\/?(?:index\.html)?$/.test(location.pathname)) return;
 function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 function plantName(label){return (label.querySelector('div > b')?.textContent||'식물').trim()}
 function modeInfo(){
  const api=window.TFDCandidateApplicability,mode=api?.mode?.()||'all';
  if(mode==='exact')return {mode,label:'정확한 종 직접근거만',rule:'DB 식물 학명과 이베라 1차 야생섭식 기록의 식물 학명이 정확히 일치하는 후보만 포함한다.'};
  if(mode==='genus')return {mode,label:'속 수준 포함',rule:'정확한 종 직접근거와, 같은 속을 sp./spp. 수준으로 기록한 이베라 1차 직접근거까지만 포함한다.'};
  return {mode:'all',label:'전체 적용성',rule:'식물 적용성 수준으로 후보를 추가 제외하지 않는다.'};
 }
 function excludedByApplicability(){
  const api=window.TFDCandidateApplicability;if(!api?.allows)return [];
  return [...document.querySelectorAll('#candidates label.candidate')].filter(label=>!api.allows(label));
 }
 function selectedVisible(){return [...document.querySelectorAll('#candidates label.candidate')].filter(label=>!label.hidden&&label.querySelector('input[type="checkbox"][data-id]:checked'))}
 function addContext(){
  const explain=document.querySelector('#fresh-combo-note .fresh-explain');if(!explain)return;
  explain.querySelector('.fresh-filter-context')?.remove();
  const info=modeInfo(),excluded=excludedByApplicability(),names=excluded.slice(0,5).map(plantName),more=Math.max(0,excluded.length-names.length);
  const excludedText=info.mode==='all'?'적용성 기준만으로 제외된 후보 없음':excluded.length?(names.join(', ')+(more?' 외 '+more+'종':'')+' · 총 '+excluded.length+'종'):'현재 후보 중 이 기준만으로 추가 제외된 식물 없음';
  const box=document.createElement('div');box.className='fresh-filter-context';
  box.innerHTML='<div><span class="fresh-filter-context-label">현재 적용성 기준</span><b>'+esc(info.label)+'</b></div><div class="small">'+esc(info.rule)+'</div><div class="small"><b>이 기준으로 제외:</b> '+esc(excludedText)+'</div><div class="small">여기서 제외됐다는 것은 안전성·부적합 판정이 아니라, 현재 선택한 식물 분류군 근거 엄격도를 충족하지 않았다는 뜻이다.</div>';
  explain.insertBefore(box,explain.children[1]||null);
 }
 function bind(){const btn=document.getElementById('freshCombo3');if(!btn||btn.dataset.filterContextBound==='1')return;btn.dataset.filterContextBound='1';btn.addEventListener('click',()=>setTimeout(addContext,0))}
 function invalidate(){
  const note=document.getElementById('fresh-combo-note'),explain=note?.querySelector('.fresh-explain');if(!explain)return;
  explain.remove();
  const info=modeInfo(),remain=selectedVisible().length;
  note.textContent='식물 적용성 기준이 '+info.label+'으로 변경됐다. 기존 조합 설명은 이전 기준과 섞이지 않도록 지웠다. 빠른 후보 3종 선택을 다시 눌러 현재 기준으로 조합을 만든다.'+(remain?' 현재 체크 상태 '+remain+'종은 화면 조건에 맞는 항목만 남아 있다.':'');
 }
 function addStyle(){if(document.getElementById('combo-applicability-context-style'))return;const s=document.createElement('style');s.id='combo-applicability-context-style';s.textContent='.fresh-filter-context{margin:8px 0;padding:8px;border:1px solid #cbded0;border-radius:9px;background:#f7fbf7}.fresh-filter-context-label{display:inline-block;margin-right:6px;padding:2px 6px;border-radius:999px;background:#e6f5e9;font-size:11px;font-weight:700}.fresh-filter-context b{font-size:12px}';document.head.appendChild(s)}
 addStyle();bind();document.addEventListener('tfd:applicability-filter-changed',()=>setTimeout(invalidate,0));new MutationObserver(bind).observe(document.body,{childList:true,subtree:true});
})();
