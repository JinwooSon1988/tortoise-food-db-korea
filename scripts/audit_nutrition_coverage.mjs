/* Read-only coverage audit. Reference-only data must never become a feeding verdict. */
import fs from 'node:fs';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const plants=read('data/plants.json');
const exact=read('data/plant_nutrition_v56.json').plants;
const references=read('data/plant_nutrition_reference_v1.json').records;
const ids=new Set(plants.map(p=>p.id));
const exactIds=new Set(exact.map(p=>p.plant_id));
const referenceIds=new Set(references.map(p=>p.plant_id));
const missing=plants.filter(p=>!exactIds.has(p.id)&&!referenceIds.has(p.id));
const referenceOnly=plants.filter(p=>!exactIds.has(p.id)&&referenceIds.has(p.id));
const orphanExact=exact.filter(p=>!ids.has(p.plant_id));
const orphanReferences=references.filter(p=>!ids.has(p.plant_id));
const invalidReferences=references.filter(r=>r.feeding_verdict_use!==false||r.status!=='reference_only'||!r.source_url||!r.analyzed_part||!r.display_tier);
const conflictingPrimary=references.filter(r=>r.primary_eligible===true);
const referenceTiers=references.reduce((a,r)=>(a[r.display_tier]=(a[r.display_tier]||0)+1,a),{});
// Surface possible taxonomic duplicates for manual review only.
// A shared species name does NOT establish the same edible part or nutrient sample.
const scientificGroups=new Map();
for(const p of plants){const key=String(p.scientific||'').trim().toLowerCase();if(!key)continue;if(!scientificGroups.has(key))scientificGroups.set(key,[]);scientificGroups.get(key).push(p)}
const possibleSameTaxon=Array.from(scientificGroups.entries()).filter(([,group])=>group.length>1&&group.some(p=>!exactIds.has(p.id)&&!referenceIds.has(p.id))&&group.some(p=>exactIds.has(p.id)||referenceIds.has(p.id))).map(([scientific,group])=>({scientific,plants:group.map(p=>({id:p.id,ko:p.ko,nutrition:exactIds.has(p.id)?'exact':referenceIds.has(p.id)?'reference':'missing'}))}));
const summary={
  total_plants:plants.length,
  exact_nutrition_plants:plants.filter(p=>exactIds.has(p.id)).length,
  reference_only_plants:referenceOnly.length,
  no_linked_nutrition_plants:missing.length,
  reference_records:references.length,
  distinct_reference_plants:referenceIds.size,
  reference_records_overlapping_exact:references.filter(r=>exactIds.has(r.plant_id)).length,
  possible_same_taxon_manual_review:possibleSameTaxon.map(group=>({
    ...group,
    review_required:'Confirm exact taxon, edible part, preparation state, units and source before linking',
    action:'manual_review_only',
    auto_copy_nutrients:false
  })),
  duplicate_korean_names:[...new Set(plants.map(p=>p.ko).filter((name,i,arr)=>name&&arr.indexOf(name)!==i))].map(name=>({
    name,
    ids:plants.filter(p=>p.ko===name).map(p=>p.id),
    action:'review_aliases_and_duplicate_search_results'
  })),
  reference_tiers:referenceTiers,
  invalid_reference_records:invalidReferences.map(r=>r.reference_id),
  incorrectly_primary_eligible_references:conflictingPrimary.map(r=>r.reference_id),
  orphan_exact_ids:[...new Set(orphanExact.map(p=>p.plant_id))],
  orphan_reference_ids:[...new Set(orphanReferences.map(p=>p.plant_id))],
  missing:missing.map(p=>({id:p.id,ko:p.ko,scientific:p.scientific})),
  reference_only:referenceOnly.map(p=>({id:p.id,ko:p.ko,scientific:p.scientific}))
};
console.log(JSON.stringify(summary,null,2));
if(orphanExact.length||orphanReferences.length||invalidReferences.length||conflictingPrimary.length)process.exitCode=1;
