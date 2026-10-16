/* Optional taxonomy-only candidates integrated into the existing home search.
   Never modifies public assessments, verdicts, or the existing search catalog. */
(()=>{'use strict';
const DATA='./data/global_taxonomy_candidates.json';
const styles=document.createElement('style');
styles.textContent='.taxonomy-hit{padding:13px 15px;border:1px solid #dce5dd;border-radius:12px;background:#f9fbf9;margin:9px 0}.taxonomy-hit strong{display:block}.taxonomy-hit p{font-size:13px;color:#53675b;margin:5px 0}.taxonomy-hit a{font-size:13px}.taxonomy-note{font-size:13px;color:#52675a;margin:10px 0}.taxonomy-more{background:#e8f3eb;color:#205438;border:1px solid #c7dece;border-radius:8px;padding:9px 12px;cursor:pointer}';
document.head.append(styles);
const isEn=()=>document.documentElement.lang.toLowerCase().startsWith('en');
const T=(ko,en)=>isEn()?en:ko;
const input=document.querySelector('input[type=search]')||document.querySelector('input[id*=search],input[id*=Search]');
if(!input)return;
const host=document.createElement('section');host.id='taxonomy-home-results';host.setAttribute('aria-live','polite');host.hidden=true;
const anchor=document.querySelector('#results')||document.querySelector('#searchResults')||input.closest('.card')||input.parentElement;
anchor.insertAdjacentElement('afterend',host);
let candidates=[],last='',visible=0;
const norm=s=>String(s||'').normalize('NFKC').trim().toLowerCase();
function render(reset){const q=norm(input.value);if(!q||q.length<2||!candidates.length){host.hidden=true;host.replaceChildren();return}if(reset){last=q;visible=0;host.replaceChildren()}if(q!==last){render(true);return}
const found=candidates.filter(x=>norm(x.scientific_name).includes(q));host.hidden=!found.length;if(!found.length)return;
if(visible===0){const h=document.createElement('h3');h.textContent=T('추가 식물 분류정보','Additional plant taxonomy records');host.append(h);const note=document.createElement('p');note.className='taxonomy-note';note.textContent=T('아래 식물은 급여 판정이 아닙니다. 섭식·안전성 근거가 확인되지 않았습니다.','These are taxonomy records, not feeding verdicts. Feeding and safety evidence are not established.');host.append(note)}
const frag=document.createDocumentFragment();for(const r of found.slice(visible,visible+40)){const article=document.createElement('article');article.className='taxonomy-hit';const title=document.createElement('strong');title.textContent=r.scientific_name;article.append(title);const p=document.createElement('p');p.textContent=T('급여 근거 미확인 · 분류학 후보','Feeding evidence unconfirmed · taxonomy candidate');article.append(p);if(r.source_taxon_url&&/^https:\/\//.test(r.source_taxon_url)){const a=document.createElement('a');a.href=r.source_taxon_url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=T('분류학 원문','Taxonomy source');article.append(a)}frag.append(article)}host.append(frag);visible+=40;host.querySelector('.taxonomy-more')?.remove();if(found.length>visible){const b=document.createElement('button');b.className='taxonomy-more';b.type='button';b.textContent=T('추가 식물 '+(found.length-visible)+'건 더 보기','Show '+(found.length-visible)+' more taxonomy records');b.onclick=()=>render(false);host.append(b)}}
let debounce;input.addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(()=>render(true),160)});input.addEventListener('keydown',e=>{if(e.key==='Enter')setTimeout(()=>render(true),0)});document.addEventListener('click',e=>{if(e.target.closest('button'))setTimeout(()=>render(true),30)});
window.addEventListener('tfdblanguagechange',()=>render(true));
fetch(DATA).then(r=>{if(!r.ok)throw Error('not available');return r.json()}).then(v=>{const a=Array.isArray(v)?v:v.records;if(!Array.isArray(a))return;candidates=a.filter(x=>x&&typeof x.scientific_name==='string'&&x.scientific_name.trim()).map(x=>({scientific_name:x.scientific_name,source_taxon_url:x.source_taxon_url}));render(true)}).catch(()=>{/* no dataset: no UI changes */});
})();