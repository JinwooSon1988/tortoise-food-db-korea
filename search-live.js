
(function(){
 const MAX=3, MAX_DIST=1, MAX_RATIO=0.50;
 const compat={0x3131:'ㄱ',0x3132:'ㄲ',0x3134:'ㄴ',0x3137:'ㄷ',0x3138:'ㄸ',0x3139:'ㄹ',0x3141:'ㅁ',0x3142:'ㅂ',0x3143:'ㅃ',0x3145:'ㅅ',0x3146:'ㅆ',0x3147:'ㅇ',0x3148:'ㅈ',0x3149:'ㅉ',0x314a:'ㅊ',0x314b:'ㅋ',0x314c:'ㅌ',0x314d:'ㅍ',0x314e:'ㅎ'};
 const L=['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
 const V=['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ','ㅗ','ㅘ','ㅙ','ㅚ','ㅛ','ㅜ','ㅝ','ㅞ','ㅟ','ㅠ','ㅡ','ㅢ','ㅣ'];
 const T=['','ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
 function jamo(s){let o='';for(const ch of s){const c=ch.charCodeAt(0);if(c>=0xAC00&&c<=0xD7A3){const n=c-0xAC00;o+=L[Math.floor(n/588)]+V[Math.floor((n%588)/28)]+T[n%28];}else o+=ch;}return o;}
 function norm(s){return (s||'').trim().replace(/\s+/g,'').toLowerCase();}
 function lev(a,b){const d=Array.from({length:a.length+1},()=>Array(b.length+1).fill(0));for(let i=0;i<=a.length;i++)d[i][0]=i;for(let j=0;j<=b.length;j++)d[0][j]=j;for(let i=1;i<=a.length;i++)for(let j=1;j<=b.length;j++)d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(a[i-1]===b[j-1]?0:1));return d[a.length][b.length];}
 function candidates(q,map){
   q=norm(q); if(q.length<2)return [];
   const jq=jamo(q), out=[];
   for(const row of map)for(const alias of (row.aliases||[])){
     const a=norm(alias), ja=jamo(a);
     if(a===q)return [{plant_id:row.plant_id,label:alias,exact:true,dist:0,ratio:0}];
     const syll=lev(q,a), jd=lev(jq,ja), ratio=jd/Math.max(jq.length,ja.length);
     if(syll<=MAX_DIST || (jd<=2 && ratio<=MAX_RATIO))out.push({plant_id:row.plant_id,label:alias,exact:false,dist:syll,jamoDist:jd,ratio});
   }
   out.sort((x,y)=>x.dist-y.dist||x.ratio-y.ratio||x.label.length-y.label.length);
   const seen=new Set(); return out.filter(x=>!seen.has(x.plant_id)&&(seen.add(x.plant_id),true)).slice(0,MAX);
 }
 async function init(){
  const input=document.querySelector('input[type="search"],#searchInput,#search'); if(!input)return;
  const map=await fetch('./data/korean_retail_name_map.json').then(r=>r.json());
  let box=document.getElementById('koSuggestions');if(!box){box=document.createElement('div');box.id='koSuggestions';box.setAttribute('role','listbox');box.setAttribute('aria-live','polite');input.after(box);}
  let identity=document.getElementById('identityWarning');if(!identity){identity=document.createElement('div');identity.id='identityWarning';identity.setAttribute('role','note');identity.style.cssText='display:none;margin-top:8px;padding:10px 12px;border:1px solid #e2c66f;border-radius:10px;background:#fff7df;font-size:13px;line-height:1.5';box.after(identity);}
  let current=[],active=-1;
  function close(){box.innerHTML='';current=[];active=-1;input.setAttribute('aria-expanded','false');}
  function identityRow(q){const nq=norm(q);if(!nq)return null;return map.find(row=>[...(row.retail_terms||[]),...(row.aliases||[])].some(x=>norm(x)===nq))||null;}
  function drawIdentity(){const row=identityRow(input.value);if(!row||row.mapping_status!=='name_candidate_only'){identity.style.display='none';identity.textContent='';return;}const specific=row.plant_id==='mallow'?' 특히 “아욱”은 한국 유통명만으로 특정 Malva 종을 확정하지 않는다.':'';identity.innerHTML='<b>식물동정 주의</b><br>이 이름은 검색 후보다. 상품명·통용명 일치만으로 학명을 확정하거나 급여 안전성을 승인하지 않는다.'+specific;identity.style.display='block';}
  function choose(x){input.value=x.label;close();drawIdentity();input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));}
  function draw(){box.innerHTML=''; if(!current.length){input.setAttribute('aria-expanded','false');return;} input.setAttribute('aria-expanded','true');
   const head=document.createElement('div');head.className='suggest-head';head.textContent='혹시 이것을 찾으셨나요?';box.appendChild(head);
   current.forEach((x,i)=>{const b=document.createElement('button');b.type='button';b.id='koSug'+i;b.setAttribute('role','option');b.textContent=x.label;b.onclick=()=>choose(x);box.appendChild(b);});
   const warn=document.createElement('small');warn.textContent='검색 후보일 뿐 식물종 동정 결과가 아니다.';box.appendChild(warn);
  }
  input.setAttribute('aria-autocomplete','list');input.setAttribute('aria-controls','koSuggestions');input.setAttribute('aria-expanded','false');
  input.addEventListener('input',()=>{current=candidates(input.value,map).filter(x=>!x.exact);active=-1;draw();drawIdentity();});
  input.addEventListener('change',drawIdentity);
  input.addEventListener('keydown',e=>{const bs=[...box.querySelectorAll('button')];if(e.key==='Escape'){close();return;}if(!bs.length)return;
    if(e.key==='ArrowDown'){e.preventDefault();active=(active+1)%bs.length;bs[active].focus();}
    else if(e.key==='Enter'&&active>=0){e.preventDefault();choose(current[active]);}
  });
  box.addEventListener('keydown',e=>{const bs=[...box.querySelectorAll('button')];let i=bs.indexOf(document.activeElement);
    if(e.key==='ArrowDown'){e.preventDefault();i=(i+1)%bs.length;bs[i].focus();}
    else if(e.key==='ArrowUp'){e.preventDefault();i=(i-1+bs.length)%bs.length;bs[i].focus();}
    else if(e.key==='Escape'){e.preventDefault();close();input.focus();}
  });
  const deepQuery=new URLSearchParams(location.search).get('q');
  if(deepQuery){
    input.value=deepQuery.slice(0,80);drawIdentity();
    let tries=0,timer=setInterval(()=>{tries++;const ready=document.getElementById('catalogCount')?.textContent.includes('현재 등록된');if(ready||tries>=20){clearInterval(timer);document.getElementById('searchBtn')?.click();}},100);
  }
 }
 window.TortoiseKoSearch={candidates,jamo,lev};document.addEventListener('DOMContentLoaded',init);
})();
