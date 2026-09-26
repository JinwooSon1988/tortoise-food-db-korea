from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
p=(ROOT/"all-plants/index.html").read_text(encoding="utf-8")
lang=(ROOT/"language-toggle.js").read_text(encoding="utf-8")
errors=[]
for needle in ['../language-toggle.js','VLEN=','tfdblanguagechange']:
    if needle not in p: errors.append("catalog missing "+needle)
for ko,en in {
'전체 식물 데이터':'All plant data','적합성 전체':'All assessments','영양자료 전체':'All nutrition data',
'식물명':'Plant','영문명':'English name','학명':'Scientific name','과':'Family','종류':'Category','적합성':'Assessment',
'영양자료':'Nutrition data','미확인':'Unverified'
}.items():
    if ko in p and (ko not in lang or en not in lang): errors.append("missing catalog translation: "+ko)
if errors:
 print("FAIL: bilingual catalog coverage")
 for e in errors: print("-",e)
 sys.exit(1)
print("PASS: full catalog language toggle and dynamic verdict localization wired")
