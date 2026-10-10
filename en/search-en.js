/* English home search. Grade selection is the shared verdict core (verdict-core.js, mirrored by scripts/public_verdict.py),
   reading the same data files as the Korean home, so the grade shown here is always the Korean grade. English wording for
   grades, scopes and certainty comes from window.TFDB_EN (generated from scripts/i18n_en.py); translated reasons and roles
   come from data/i18n/en/catalog_en.json. */
(function(){
const TV=window.TortoiseVerdict,EN=window.TFDB_EN,PAGE=8;
let catalog=[],assessmentMap=new Map(),imageMap=new Map(),shown=PAGE,lastRows=[];
const input=document.getElementById('searchInput'),results=document.getElementById('searchResults'),countEl=document.getElementById('catalogCount'),searchBtn=document.getElementById('searchBtn');
function norm(s){return(s||'').normalize('NFKC').trim().toLowerCase().replace(/[\s·._'’\-–—()×]+/g,'')}
/* The visitor's own query may be in Korean; mark its language so the English page stays English-only. */
const uq=q=>'<span class="userq"'+(/[가-힣]/.test(q)?' lang="ko"':'')+'>'+esc(q)+'</span>';
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
const rowsFor=id=>assessmentMap.get(id)||[];
const best=id=>TV.representative(rowsFor(id));
function disp(a){if(!a)return EN.noDefault;const g=EN.grades[a.verdict];return g||EN.hold}
const gradeOf=a=>{const g=TV.display(a).grade;return g.length===1?g:'On hold'};
const certainty=c=>EN.certainty[String(c||'').trim()]||'Not assessed';
/* Same rule as TV.scopeLabel / i18n_en.scope_label_en. */
function scope(a){if(!a)return 'No general assessment';if(a.animal_taxon==='Testudo'||a.species_group==='Mediterranean_Testudo')return 'Mediterranean Testudo evidence';if(a.assessment_scope==='tortoise_general'||a.species_group==='Tortoise_general')return 'General tortoise evidence';if(a.species_group==='Herbivorous_reptile_general'||a.assessment_scope==='herbivorous_reptile_general')return 'General herbivorous-reptile evidence';return 'Indirect evidence'}
function thumb(r){const im=imageMap.get(r.id);if(!im)return '<figure class="rthumb empty" aria-hidden="true">Verified photo pending</figure>';
 return '<figure class="rthumb"><img src="'+esc(im.image_url+'?width=240')+'" alt="'+esc(r.name)+' reference photo" loading="lazy" decoding="async" width="240" height="240"></figure>'}
function photoCredit(r){const im=imageMap.get(r.id);if(!im)return '';return '<p class="photocredit">Photo '+uq(im.creator)+' · '+esc(im.license)+(im.part_match==='mismatch'?' · <span class="partflag">The photo shows a different part from the one fed.</span>':'')+'</p>'}
function lev(a,b){const d=Array.from({length:a.length+1},(_,i)=>[i]);for(let j=1;j<=b.length;j++)d[0][j]=j;for(let i=1;i<=a.length;i++)for(let j=1;j<=b.length;j++)d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(a[i-1]===b[j-1]?0:1));return d[a.length][b.length]}
/* Did-you-mean: closest English name, alias or scientific name within a small edit distance; never a match by itself. */
function suggest(q){q=norm(q);if(q.length<3)return[];const max=q.length<6?1:2,out=new Map;catalog.filter(r=>r.isPublic).forEach(r=>r.terms.forEach(t=>{const n=norm(t);if(!n||/[가-힣]/.test(t))return;const d=Math.min(lev(q,n),n.length>q.length?lev(q,n.slice(0,q.length)):99);if(d<=max&&(!out.has(r.name)||out.get(r.name)>d))out.set(r.name,d)}));return [...out].sort((a,b)=>a[1]-b[1]).slice(0,3).map(x=>x[0])}
function didYouMean(q){const s=q?suggest(q):[];return s.length?'Did you mean '+s.map(x=>'<a class="didyoumean" href="./?q='+encodeURIComponent(x)+'">‘'+esc(x)+'’</a>').join(', ')+'? ':''}
function card(r){const a=best(r.id),g=disp(a),grade=gradeOf(a),cls=grade.length===1?grade.toLowerCase():'hold',notes=TV.speciesNotes(rowsFor(r.id),a);
 const why=r.why||(a?'Evidence review in progress.':'There is no public assessment for Mediterranean Testudo or tortoises in general yet.');
 const holdHtml=grade==='On hold'?'<div class="holdwarning" role="note"><b>On hold does not mean safe.</b> Do not read it as “can be fed” until the evidence is sufficient.</div>':'';
 const noteHtml=notes.length?'<div class="speciesnote"><b>Species-specific notes</b> · evidence for particular species is shown separately from the general assessment on the detail page</div>':'';
 const roleHtml=r.role?'<p class="roleline"><b>Role in the diet</b>'+esc(r.role)+'</p>':'';
 return '<article class="resultcard grade-'+cls+'" data-plant-id="'+esc(r.id)+'" data-grade="'+esc(grade)+'" aria-label="'+esc(r.name)+' · '+esc(grade)+' '+esc(g.label)+'"><div class="resulthead">'+thumb(r)+'<div class="rtitle"><h3>'+esc(r.name)+'</h3><span class="sci">'+esc(r.scientific||'Scientific name under review')+'</span></div><span class="gradepill"><strong>'+esc(grade==='On hold'?'Hold':grade)+'</strong>'+esc(g.label)+'</span></div><p class="decisionline"><span class="decisionlabel">Verdict</span>'+esc(EN.decision[grade])+' <span class="decisionmeaning">· '+esc(g.meaning)+'</span></p><div class="resultbody"><div class="reasonbox"><b>Why this grade?</b><p class="why">'+esc(why)+'</p></div><div class="practicalbox"><p class="actionline"><b>In practice</b>'+esc(EN.action[grade])+'</p>'+roleHtml+'</div></div>'+holdHtml+noteHtml+'<div class="resultfoot"><span class="basis"><span class="basisitem">Applicability <b>'+esc(scope(a))+'</b></span><span class="basisitem confidence">Evidence certainty <b>'+esc(certainty(a?.confidence))+'</b><a class="confidencehelp" href="./guides/research-method/#certainty" aria-label="What evidence certainty means and how evidence is reviewed" title="Separate from the feeding grade (A–D): how certain the evidence is">?</a></span></span><a class="detailbtn" aria-label="'+esc(r.name)+': reasons and evidence" href="./plant/'+encodeURIComponent(r.id)+'/">Reasons and evidence <span aria-hidden="true">→</span></a></div>'+photoCredit(r)+'</article>'}
function render(rows){lastRows=rows;const q=(input.value||'').trim();if(!rows.length){results.innerHTML='<div class="emptyresult"><b>No matching public assessment was found.</b><span>'+(q?'This does not mean <strong>“'+uq(q)+'”</strong> is safe to feed. ':'')+didYouMean(q)+'Try another name or the scientific name, or browse the <a href="./all-plants/">full plant list</a>. Plants not yet reviewed, or whose identity is not confirmed, have no public assessment.</span></div>';return}
 const rest=rows.length-shown;results.innerHTML='<p class="resultsummary"><b>'+(q?'“'+uq(q)+'”: ':'')+rows.length+' result'+(rows.length>1?'s':'')+'</b><span>Exact name matches are listed first.</span></p>'+rows.slice(0,shown).map(card).join('')+(rest>0?'<button type="button" class="morebtn" id="moreResults">Show '+rest+' more</button>':'');
 const more=document.getElementById('moreResults');if(more)more.onclick=()=>{shown+=PAGE*3;render(lastRows)}}
function matchRank(r,q){const n=norm(r.name),t=r.terms.map(norm);if(n===q)return 0;if(t.some(x=>x===q))return 1;if(n.startsWith(q))return 2;if(t.some(x=>x.startsWith(q)))return 3;return 4}
function search(){const q=norm(input.value);shown=PAGE;if(!q){results.innerHTML='';return}
 const rows=catalog.filter(r=>r.isPublic&&r.terms.some(x=>norm(x).includes(q)));rows.sort((a,b)=>matchRank(a,q)-matchRank(b,q)||(a.name.length-b.name.length)||a.name.localeCompare(b.name,'en'));render(rows)}
async function j(u){try{const r=await fetch(u);return r.ok?await r.json():null}catch(e){return null}}
async function boot(){const [plants,retail,assessmentData,cat]=await Promise.all([j('../data/plants.json'),j('../data/korean_retail_name_map.json'),j('../data/public_assessments.json'),j('../data/i18n/en/catalog_en.json')]);
 if(!plants||!assessmentData||!cat){countEl.textContent='The plant data could not be loaded. Please reload the page.';return}
 const assessments=Array.isArray(assessmentData)?assessmentData:(assessmentData.assessments||assessmentData.records||[]);assessments.forEach(a=>{if(!assessmentMap.has(a.plant_id))assessmentMap.set(a.plant_id,[]);assessmentMap.get(a.plant_id).push(a)});
 const enById=new Map((cat.plants||[]).map(x=>[x.id,x])),retailMap=new Map((retail||[]).map(r=>[r.plant_id,r]));
 /* Korean names stay searchable (never displayed) so a Korean name typed on the English page still finds the plant. */
 catalog=plants.map(p=>{const e=enById.get(p.id)||{},r=retailMap.get(p.id)||{};return{id:p.id,name:e.name||p.en||p.id,scientific:p.scientific||'',why:e.why||'',role:e.role||'',isPublic:p.identity_status!=='candidate_name'&&assessmentMap.has(p.id)&&enById.has(p.id),terms:[e.name,p.en,p.scientific,...(e.aliases||[]),p.ko,...(p.aliases||[]),...(p.search_aliases||[]),...(r.retail_terms||[]),...(r.aliases||[])].filter(Boolean)}});
 countEl.textContent='Search '+catalog.filter(r=>r.isPublic).length+' plants with a public assessment.';countEl.dataset.ready='1';
 const dq=new URLSearchParams(location.search).get('q');if(dq&&!input.value)input.value=dq.slice(0,80);if(norm(input.value))search()}
boot();j('../data/verified_plant_images_v56.json').then(d=>{((d&&d.images)||[]).forEach(im=>imageMap.set(im.plant_id,im));if(lastRows.length&&!results.contains(document.activeElement))render(lastRows)});
results.addEventListener('error',e=>{const img=e.target;if(img.tagName==='IMG'&&img.parentNode.classList.contains('rthumb')){const f=img.parentNode;f.classList.add('empty');f.setAttribute('aria-hidden','true');f.textContent='Photo unavailable'}},true);
document.addEventListener('keydown',e=>{if(e.key==='/'&&!e.ctrlKey&&!e.metaKey&&!/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName||'')){e.preventDefault();input.focus();input.select()}});
document.querySelectorAll('[data-example]').forEach(b=>b.onclick=()=>{input.value=b.dataset.example;search();input.focus()});
searchBtn.onclick=search;let timer=null;
input.addEventListener('input',()=>{clearTimeout(timer);const q=norm(input.value);if(!q){results.innerHTML='';return}if(q.length<2){results.innerHTML='<p class="searchhint">Type at least 2 letters to search.</p>';return}timer=setTimeout(search,120)});
input.onkeydown=e=>{if(e.key==='Enter'){clearTimeout(timer);search()}};
})();
