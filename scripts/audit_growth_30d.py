from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,ok): checks.append((name,bool(ok)))
files={p:(ROOT/p).read_text(encoding='utf-8') for p in ['growth/index.html','monthly/index.html','settings/index.html','profile/index.html','sw.js']}
check('growth page exists',(ROOT/'growth/index.html').exists());check('monthly page exists',(ROOT/'monthly/index.html').exists());check('growth storage key','tfd_growth_v1' in files['growth/index.html']);check('growth profile linkage','profile_id' in files['growth/index.html']);check('growth records weight and SCL','weight_g' in files['growth/index.html'] and 'scl_mm' in files['growth/index.html']);check('monthly reads diet and growth','tfd_weekly_v1' in files['monthly/index.html'] and 'tfd_growth_v1' in files['monthly/index.html']);check('monthly uses 30-day cutoff','getDate()-29' in files['monthly/index.html']);check('backup schema v2','VERSION=2' in files['settings/index.html'] and 'growth:' in files['settings/index.html']);check('backup imports v1 and v2','[1,2].includes(d.version)' in files['settings/index.html']);check('profile delete preserves linked records','기존 식단·성장 기록은 삭제하지 않고' in files['profile/index.html']);check('pwa caches growth pages',"'./growth/'" in files['sw.js'] and "'./monthly/'" in files['sw.js']);m=re.search(r"const CACHE='tfd-v(\d+)-(?:stable-)?(\d+)'",files['sw.js']);check('cache current enough',bool(m) and int(m.group(1))>=50);check('no fake health score','건강점수' not in files['monthly/index.html'] and '영양점수' not in files['monthly/index.html'])
failed=[n for n,ok in checks if not ok]
for n,ok in checks: print(('PASS' if ok else 'FAIL'),n)
if failed: raise SystemExit('failed: '+', '.join(failed))
print(f'{len(checks)}/{len(checks)} checks passed')
