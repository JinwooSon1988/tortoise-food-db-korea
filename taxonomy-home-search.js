/* Plant catalog entries (GBIF-verified species, no feeding grade) added below the home search results.
   Never modifies public assessments, verdicts, or the existing search catalog. A valid species is not feeding evidence. */
(()=>{'use strict';
const ROOT=document.currentScript?new URL('.',document.currentScript.src).href:new URL('./',location.href).href;
const DATA=ROOT+'data/plant-catalog/search.json';
const styles=document.createElement('style');
styles.textContent='.taxonomy-hit{padding:13px 15px;border:1px solid #dce5dd;border-left:5px solid #5b6670;border-radius:12px;background:#f9fbf9;margin:9px 0}.taxonomy-hit strong{display:block}.taxonomy-hit .sci{font-style:italic;font-size:13px;color:#53675b}.taxonomy-hit p{font-size:13px;color:#53675b;margin:5px 0}.taxonomy-hit a{display:inline-flex;align-items:center;min-height:40px;font-size:14px;font-weight:800}.taxonomy-note{font-size:13px;color:#52675a;margin:10px 0}.taxonomy-more{min-height:44px;background:#e8f3eb;color:#205438;border:1px solid #c7dece;border-radius:8px;padding:9px 12px;cursor:pointer}';
document.head.append(styles);
const isEn=()=>document.documentElement.lang.toLowerCase().startsWith('en');
const T=(ko,en)=>isEn()?en:ko;
const input=document.querySelector('input[type=search]')||document.querySelector('input[id*=search],input[id*=Search]');
if(!input)return;
const host=document.createElement('section');host.id='taxonomy-home-results';host.setAttribute('aria-live','polite');host.hidden=true;
const anchor=document.querySelector('#results')||document.querySelector('#searchResults')||input.closest('.card')||input.parentElement;
anchor.insertAdjacentElement('afterend',host);
let rows=[],last='',visible=0;
const norm=s=>String(s||'').normalize('NFKC').trim().toLowerCase();
function render(reset){const q=norm(input.value);if(!q||q.length<2||!rows.length){host.hidden=true;host.replaceChildren();return}if(reset){last=q;visible=0;host.replaceChildren()}if(q!==last){render(true);return}
const found=rows.filter(x=>x.hay.includes(q)).sort((a,b)=>b.evidence-a.evidence);host.hidden=!found.length;if(!found.length)return;
if(visible===0){const h=document.createElement('h3');const linked=found.filter(x=>x.evidence).length;h.textContent=T('등급 미평가 식물 '+found.length+'종 (급여 안전성 미확정)','Plants without a feeding grade: '+found.length+' (feeding safety not established)');host.append(h);const note=document.createElement('p');note.className='taxonomy-note';note.textContent=T('급여·섭식·영양 등 관련 자료가 연결된 식물 '+linked+'종 · 급여 권장 근거 부족 '+(found.length-linked)+'종. 학명 확인은 급여 판정이 아니며 먹여도 된다는 뜻이 아닙니다.','Feeding-related records linked: '+linked+' · not enough evidence to recommend feeding: '+(found.length-linked)+'. A confirmed scientific name is not a feeding verdict and does not mean a plant can be fed.');host.append(note)}
const frag=document.createDocumentFragment();for(const r of found.slice(visible,visible+40)){const article=document.createElement('article');article.className='taxonomy-hit';const title=document.createElement('strong');title.textContent=isEn()?(r.en||r.sci):(r.ko||r.sci);article.append(title);const sci=document.createElement('span');sci.className='sci';sci.lang='la';sci.textContent=r.sci+(r.family?' · '+r.family:'');article.append(sci);const p=document.createElement('p');p.textContent=T('급여 안전성 미확정 · 급여 등급 없음','Feeding safety not established · no feeding grade')+(r.evidence?T(' · 관련 기록 있음 (급여·섭식·영양 등)',' · related evidence available (feeding, diet or nutrition)'):'');article.append(p);
// Only entries with linked records have a public detail page; the rest get the evidence gap and the taxonomy record.
const a=document.createElement('a');if(r.evidence){a.href=ROOT+'taxon/?id='+encodeURIComponent(r.id)+(isEn()?'&lang=en':'');a.textContent=T('상세 보기 →','View details →')}else{const gap=document.createElement('p');gap.textContent=T('급여 권장 근거 부족: 조사한 자료에서 육지거북 섭식·영양·독성 기록을 찾지 못했습니다. 안전하다거나 위험하다는 판정이 아닙니다.','Not enough evidence to recommend feeding: no tortoise feeding, nutrition or toxicity record was found in the sources searched. This is neither a safe nor an unsafe verdict.');article.append(gap);a.href='https://www.gbif.org/species/'+encodeURIComponent(String(r.id).split(':')[1]);a.target='_blank';a.rel='noopener noreferrer';a.textContent=T('분류 정보 (GBIF) ↗','Taxonomy record (GBIF) ↗')}article.append(a);frag.append(article)}host.append(frag);visible+=40;host.querySelector('.taxonomy-more')?.remove();
if(found.length>visible){const b=document.createElement('button');b.type='button';b.className='taxonomy-more';b.textContent=T('식물 '+(found.length-visible)+'종 더 보기','Show '+(found.length-visible)+' more plants');b.onclick=()=>render(false);host.append(b)}}
let debounce;input.addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(()=>render(true),160)});input.addEventListener('keydown',e=>{if(e.key==='Enter')setTimeout(()=>render(true),0)});document.addEventListener('click',e=>{if(e.target.closest('button')&&!e.target.closest('.taxonomy-more'))setTimeout(()=>render(true),30)});
window.addEventListener('tfdblanguagechange',()=>render(true));
fetch(DATA).then(r=>{if(!r.ok)throw Error('not available');return r.json()}).then(v=>{if(!Array.isArray(v?.rows))return;rows=v.rows.filter(x=>Array.isArray(x)&&x[0]&&x[1]).map(x=>({id:x[0],sci:x[1],family:x[2],en:x[3],ko:x[4],evidence:!!x[5],hay:norm([x[1],x[3],x[4]].join(' '))}));render(true)}).catch(()=>{/* no dataset: no UI changes */});
})();
