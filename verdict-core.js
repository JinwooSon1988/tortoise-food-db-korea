/* Canonical public verdict selection. Shared by the home search and QA (node).
   Mirrors scripts/public_verdict.py — keep both in sync; scripts/qa_verdict_consistency.py enforces it.
   Default target is Mediterranean Testudo. Species-specific (exact_species, non-Testudo) assessments
   are shown as species notes only and never become the representative verdict. */
(function(root){
 const GRADES={
  supported_mixed_diet:{grade:'A',label:'혼합식 활용 가능',tone:'green',meaning:'여러 식물을 섞는 혼합식의 한 구성으로 활용할 수 있다.'},
  limited_mixed_diet:{grade:'B',label:'제한적 혼합 급여',tone:'yellow',meaning:'혼합식에 넣을 수 있지만 식단의 중심으로 삼지 않는다.'},
  limited_supplement:{grade:'C',label:'가끔 보조 급여',tone:'yellow',meaning:'주식이 아니라 가끔 곁들이는 보조 먹이로만 본다.'},
  supplement_general_evidence:{grade:'C',label:'가끔 보조 급여',tone:'yellow',meaning:'주식이 아니라 가끔 곁들이는 보조 먹이로만 본다.'},
  general_reptile_supplement:{grade:'C',label:'가끔 보조 급여',tone:'yellow',meaning:'주식이 아니라 가끔 곁들이는 보조 먹이로만 본다.'},
  do_not_feed:{grade:'D',label:'급여하지 않음',tone:'danger',meaning:'현재 판정에서는 급여 대상에서 제외한다.'}
 };
 const HOLD={grade:'보류',label:'판정 보류',tone:'hold',meaning:'근거가 부족하거나 엇갈려 등급을 정하지 않았다. 보류는 안전하다는 뜻이 아니다.'};
 const NO_DEFAULT={grade:'보류',label:'판정 보류',tone:'hold',meaning:'지중해 Testudo 기본 판정이 아직 없다. 판정이 없다는 것은 안전하다는 뜻이 아니다.'};
 const isSpeciesOnly=x=>x.assessment_scope==='exact_species'&&x.animal_taxon&&x.animal_taxon!=='Testudo';
 function representative(rows){
  rows=rows||[];
  return rows.find(x=>x.animal_taxon==='Testudo')
   ||rows.find(x=>x.species_group==='Mediterranean_Testudo')
   ||rows.find(x=>x.assessment_scope==='tortoise_general')
   ||rows.find(x=>x.species_group==='Tortoise_general')
   ||rows.find(x=>!isSpeciesOnly(x))
   ||null;
 }
 function display(a){if(!a)return NO_DEFAULT;return GRADES[a.verdict]||HOLD}
 function speciesNotes(rows,primary){return (rows||[]).filter(x=>x!==primary&&isSpeciesOnly(x))}
 function scopeLabel(a){
  if(!a)return '지중해 Testudo 판정 없음';
  if(a.animal_taxon==='Testudo'||a.species_group==='Mediterranean_Testudo')return '지중해 Testudo 근거';
  if(a.assessment_scope==='tortoise_general'||a.species_group==='Tortoise_general')return '육지거북 일반 근거';
  if(a.species_group==='Herbivorous_reptile_general'||a.assessment_scope==='herbivorous_reptile_general')return '초식 파충류 일반 근거';
  return '간접 근거';
 }
 const api={GRADES,HOLD,NO_DEFAULT,representative,display,speciesNotes,scopeLabel,isSpeciesOnly};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.TortoiseVerdict=api;
})(typeof window!=='undefined'?window:globalThis);
