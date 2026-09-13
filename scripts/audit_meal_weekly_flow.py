from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
meal=(ROOT/'meal/index.html').read_text(encoding='utf-8');weekly=(ROOT/'weekly/index.html').read_text(encoding='utf-8');sw=(ROOT/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-(?:stable-)?(\d+)'",sw)
checks={'meal_uses_master_plants':'../data/plants.json' in meal,'meal_uses_assessments':'../data/assessments.json' in meal,'meal_uses_weekly_key':'tfd_weekly_v1' in meal,'weekly_uses_same_key':'tfd_weekly_v1' in weekly,'meal_writes_event_id':'event_id:makeId()' in meal,'meal_writes_profile_id':'profile_id:pid' in meal,'meal_deduplicates_same_day_profile_food':'x.date===date&&x.food===food' in meal and 'x.profile_id||null' in meal,'meal_uses_local_date':'function localISO' in meal,'meal_links_profile_context':'../profile-context.js' in meal,'meal_does_not_claim_grams':'급여량(g)이나 영양적 완전성을 계산하지 않는다' in meal,'pwa_cache_current_enough':bool(m) and int(m.group(1))>=50,'pwa_precaches_assessments':'./data/assessments.json' in sw}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
if failed:raise SystemExit('Meal-weekly flow audit failed: '+', '.join(failed))
print('Meal-weekly flow audit PASS')
