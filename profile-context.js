(function(){
 const SPECIES={
  ibera:'이베라 그리스',greek:'그리스 육지거북',hermanni:'헤르만 육지거북',marginata:'마지나타',
  horsfieldii:'호스필드',sulcata:'설카타',leopard:'레오파드'
 };
 function normalize(p){
  if(!p)return null;
  return Object.assign({},p,{
   species_name:p.species_name||SPECIES[p.species]||p.species||'',
   weight_g:p.weight_g!=null?p.weight_g:(p.weight!=null?p.weight:null)
  });
 }
 window.TFDProfiles={
  all(){try{return JSON.parse(localStorage.getItem('tfd_profiles_v46')||'[]').map(normalize)}catch(e){return[]}},
  active(){const a=this.all(),id=localStorage.getItem('tfd_active_profile_v46');return a.find(x=>x.id===id)||a[0]||null},
  normalize
 };
 if(/\/today\/?(?:index\.html)?$/.test(location.pathname)){
  const s=document.createElement('script');s.src='../source-preview.js';s.defer=true;
  s.onload=()=>{const q=document.createElement('script');q.src='../fresh-primary-mode.js';q.defer=true;q.onload=()=>{const x=document.createElement('script');x.src='../fresh-primary-combo-explain.js';x.defer=true;x.onload=()=>{const c=document.createElement('script');c.src='../candidate-applicability-summary.js';c.defer=true;c.onload=()=>{const m=document.createElement('script');m.src='../candidate-mobile-evidence-summary.js';m.defer=true;m.onload=()=>{const v=document.createElement('script');v.src='../candidate-evidence-compare.js';v.defer=true;v.onload=()=>{const l=document.createElement('script');l.src='../candidate-evidence-lineage.js';l.defer=true;l.onload=()=>{const f=document.createElement('script');f.src='../combo-applicability-context.js';f.defer=true;document.head.appendChild(f)};document.head.appendChild(l)};document.head.appendChild(v)};document.head.appendChild(m)};document.head.appendChild(c)};document.head.appendChild(x)};document.head.appendChild(q)};
  document.head.appendChild(s);
 }
})();
