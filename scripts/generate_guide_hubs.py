from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parents[1]
SITE="https://jinwooson1988.github.io/tortoise-food-db-korea"
plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))
def series(name):
 out=json.loads((ROOT/"data"/f"{name}.json").read_text(encoding="utf-8"))
 for p in sorted((ROOT/"data").glob(f"{name}_korea_addendum*.json")):
  x=json.loads(p.read_text(encoding="utf-8"))
  if isinstance(x,list): out.extend(x)
 return out
ass=series("assessments"); priority={"Mediterranean_Testudo":0,"Tortoise_general":1,"Herbivorous_reptile_general":2}; by={}
for a in ass:
 if a.get("species_group") in priority and (a["plant_id"] not in by or priority[a["species_group"]]<priority[by[a["plant_id"]]["species_group"]]): by[a["plant_id"]]=a
VL={"supported_mixed_diet":"혼합식 활용 가능","limited_mixed_diet":"제한적 혼합 급여","limited_supplement":"보조 급여 근거","supplement_general_evidence":"일반 보조 근거","general_reptile_supplement":"일반 초식파충류 보조 근거","do_not_feed":"급여 비권장"}
def e(x): return html.escape(str(x or ""),quote=True)
def cards(items):
 out=[]
 for p in items:
  a=by.get(p["id"]); verdict=VL.get((a or {}).get("verdict"),"판정 보류"); why=(a or {}).get("why") or "공개 판정을 위한 근거 검토가 완료되지 않았다."; scope=(a or {}).get("applicability_note") or (a or {}).get("species_group") or "적용 범위 검토 중"
  out.append(f'<article class="food"><div><h3><a href="../../plant/{e(p["id"])}/">{e(p.get("ko") or p["id"])}</a></h3><i>{e(p.get("scientific"))}</i></div><strong>{e(verdict)}</strong><p>{e(why)}</p><small>적용 범위: {e(scope)} · 근거등급: {e((a or {}).get("confidence") or "미확정")}</small></article>')
 return "".join(out)
def page(slug,title,desc,items,intro):
 d=ROOT/"guides"/slug; d.mkdir(parents=True,exist_ok=True); url=f"{SITE}/guides/{slug}/"; body=cards(items); schema=json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":title,"description":desc,"url":url,"inLanguage":"ko"},ensure_ascii=False,separators=(",",":"))
 doc=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow"><title>{e(title)} | 거북밥 DB</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}"><script type="application/ld+json">{schema}</script><style>:root{{--bg:#f4f7f3;--card:#fff;--line:#dce5dd;--text:#17231b;--muted:#647067}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);font-family:system-ui,-apple-system,"Noto Sans KR",sans-serif;color:var(--text);line-height:1.6}}main{{max-width:1180px;margin:auto;padding:22px}}a{{color:#24583a}}.hero,.note,.food{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;margin:12px 0}}h1{{font-size:32px;margin:6px 0}}.note{{border-left:5px solid #8a7429}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.food{{margin:0}}.food h3{{margin:0}}.food strong{{display:inline-block;margin-top:8px}}.food p{{margin:8px 0}}small,i{{color:var(--muted)}}@media(max-width:760px){{main{{padding:14px}}.grid{{grid-template-columns:1fr}}}}</style></head><body><main><a href="../../">← 거북밥 DB</a><section class="hero"><h1>{e(title)}</h1><p>{e(intro)}</p></section><section class="note"><b>읽는 법</b><br>이 페이지는 DB의 기존 판정을 주제별로 모아 보여주는 탐색 허브다. 목록에 포함됐다는 사실 자체가 급여 권장을 뜻하지 않는다. 각 항목의 판정·적용 범위·근거등급을 확인하고 상세 페이지에서 근거와 한계를 함께 확인한다.</section><div class="grid">{body}</div><section class="note"><b>근거 해석 원칙</b><br>야생 섭식 관찰은 사육 배합률이 아니며, 일반 초식 파충류 자료는 Mediterranean Testudo 직접 근거와 동일하지 않다. 근거 부족을 안전으로 간주하지 않는다.</section></main></body></html>'''
 (d/"index.html").write_text(doc,encoding="utf-8"); return url
market=[p for p in plants if any(x in (p.get("market") or "") for x in ("마트","시장","온라인"))]
wild=[p for p in plants if p.get("category")=="wild" or "채집" in (p.get("market") or "")]
caution=[p for p in plants if (by.get(p["id"]) or {}).get("verdict") in {"limited_supplement","general_reptile_supplement","do_not_feed"} or p.get("identity_status")!="verified_name"]
urls=[page("market-foods","마트에서 구할 수 있는 육지거북 먹이","마트·시장·온라인에서 찾기 쉬운 육지거북 먹이를 DB 판정과 근거 범위로 비교한다.",market,"한국에서 실제로 구하기 쉬운 먹이를 모았다. 편의성보다 종 동정과 근거 수준을 우선해 판단한다."),page("wild-plants","육지거북 야생초·채집 식물","민들레·질경이 등 육지거북 야생초와 채집 식물의 판정, 적용 범위와 근거를 확인한다.",wild,"야생초는 자연식이라는 이유만으로 자동 안전하지 않다. 식물 동정, 오염 가능성, 대상 종에 대한 근거를 함께 확인한다."),page("caution-foods","육지거북 급여 주의 식물","제한적 보조근거·일반 파충류 근거·동정 주의가 필요한 육지거북 먹이를 구분해 확인한다.",caution,"‘먹을 수 있음’과 ‘주식으로 적합함’을 분리한다. 직접 근거가 약하거나 적용 범위가 좁은 항목을 우선 확인한다.")]
s=ROOT/"sitemap.xml"; txt=s.read_text(encoding="utf-8")
for u in urls:
 tag=f'  <url><loc>{u}</loc><lastmod>2026-09-19</lastmod></url>\n'
 if u not in txt: txt=txt.replace("</urlset>",tag+"</urlset>")
s.write_text(txt,encoding="utf-8")
print("generated guide hubs",len(market),len(wild),len(caution))
