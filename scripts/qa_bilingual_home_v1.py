from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
js=(ROOT/"language-toggle.js").read_text(encoding="utf-8")
home=(ROOT/"index.html").read_text(encoding="utf-8")
required={
"육지거북 선택":"Select tortoise","지중해 Testudo":"Mediterranean Testudo",
"설카타육지거북":"Sulcata tortoise","레오파드육지거북":"Leopard tortoise",
"레드풋육지거북":"Red-footed tortoise","옐로우풋육지거북":"Yellow-footed tortoise",
"엘롱가타육지거북":"Elongated tortoise","방사거북":"Radiated tortoise",
"인도별거북":"Indian star tortoise","버마별거북":"Burmese star tortoise",
"앵무부리육지거북":"Angulate tortoise","전체 식물 DB":"Full plant database",
"전체 식물 보기 →":"View all plants →","판정 보류":"Assessment pending",
"적용 범위":"Applicability","근거":"Evidence","상세 근거 보기 →":"View evidence →"
}
errors=[]
for ko,en in required.items():
    if ko in home and (ko not in js or en not in js): errors.append(f"missing translation: {ko}")
if "MutationObserver" not in js: errors.append("dynamic result translation observer missing")
if "tfdblanguagechange" not in js: errors.append("language change event missing")
if errors:
 print("FAIL: bilingual home coverage")
 for e in errors: print("-",e)
 sys.exit(1)
print(f"PASS: {len(required)} critical home/dynamic UI translations covered")
