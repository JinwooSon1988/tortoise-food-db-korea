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
# English is a separate, fully translated site (/en/), not an in-page partial translation of Korean results:
# the Korean home must link to the English home, which must run its own English-only search on the same data.
en_home_path=ROOT/"en/index.html"
if 'href="./en/" hreflang="en" lang="en"' not in home: errors.append("Korean home does not link to the English home")
if not en_home_path.exists(): errors.append("English home en/index.html missing")
else:
    en_home=en_home_path.read_text(encoding="utf-8")
    for needle in ('<html lang="en">','src="../verdict-core.js','src="./search-en.js','href="../" hreflang="ko" lang="ko"','window.TFDB_EN='):
        if needle not in en_home: errors.append("English home missing "+needle)
    if re.search(r"[가-힣]",re.sub(r'<a [^>]*lang="ko"[^>]*>.*?</a>','',en_home)): errors.append("English home contains Korean text")
if "MutationObserver" in js and "observe(document.getElementById('searchResults')" in js: errors.append("retired in-page result translation is still active")
if errors:
 print("FAIL: bilingual home coverage")
 for e in errors: print("-",e)
 sys.exit(1)
print(f"PASS: {len(required)} critical home/dynamic UI translations covered")
