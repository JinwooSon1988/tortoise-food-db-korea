from pathlib import Path
import json, html
ROOT=Path(__file__).resolve().parents[1]
SITE_URL="https://jinwooson1988.github.io/tortoise-food-db-korea"
plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))
for p in plants:
    pid=p["id"]; d=ROOT/"plant"/pid; d.mkdir(parents=True,exist_ok=True)
    title=f"{p['ko']} 육지거북 급여 정보 | 거북밥 DB Korea"
    doc=f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><link rel="canonical" href="{SITE_URL}/plant/{pid}/"></head><body><a href="../../index.html">← 거북밥 DB</a><h1>{html.escape(p['ko'])}</h1><p><i>{html.escape(str(p.get('scientific') or '학명 검증 중'))}</i></p><p>상세 데이터는 검증 DB와 동기화한다.</p></body></html>"""
    (d/"index.html").write_text(doc,encoding="utf-8")
print("generated",len(plants))
