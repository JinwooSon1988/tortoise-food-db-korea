from pathlib import Path
import json, html, re

ROOT=Path(__file__).resolve().parents[1]
SITE_URL="https://jinwooson1988.github.io/tortoise-food-db-korea"
all_plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))
plants=[p for p in all_plants if p.get("identity_status")!="candidate_name"]

def load_series(base_name):
    base=ROOT/"data"/f"{base_name}.json"
    merged=json.loads(base.read_text(encoding="utf-8"))
    files=list((ROOT/"data").glob(f"{base_name}_korea_addendum*.json"))
    def order(path):
        m=re.search(r"_(\d+)\.json$",path.name)
        return int(m.group(1)) if m else 1
    for path in sorted(files,key=order):
        extra=json.loads(path.read_text(encoding="utf-8"))
        if isinstance(extra,list): merged.extend(extra)
    return merged

assessments=load_series("assessments")
retail=json.loads((ROOT/"data/korean_retail_name_map.json").read_text(encoding="utf-8"))
med={a["plant_id"]:a for a in assessments if a.get("species_group")=="Mediterranean_Testudo"}
general={a["plant_id"]:a for a in assessments if a.get("species_group") in {"Tortoise_general","Herbivorous_reptile_general"}}
retail_by_id={r["plant_id"]:r for r in retail}
SPECIAL={"dandelion":("green","🟢 혼합급여 적합","루마니아와 남서부 불가리아의 야생 T. g. ibera에서 Taraxacum 섭식이 직접 관찰되었고 지중해 Testudo 전문 사육근거도 일치한다. 다만 야생 관찰 빈도를 사육 배합률로 환산하지 않는다."),"plantain":("yellow","🟡 혼합급여 지지근거 있음","Plantago 속과 지중해 Testudo의 섭식·사육 근거가 있다. 국내 실제 식물의 정확한 종 동정과 공식 영양자료 검증은 별도 확인이 필요하다."),"mallow":("hold","⚪ 판단보류 / 종 수준 미확정","한국 유통명 ‘아욱’만으로 특정 Malva 종을 확정하지 않는다. 특히 아욱을 Malva parviflora로 자동 간주하지 않는다.")}
VERDICT_MAP={"supported_mixed_diet":("yellow","🟡 혼합급여 지지근거 있음"),"limited_mixed_diet":("yellow","🟡 제한적 혼합급여 근거"),"limited_supplement":("yellow","🟡 제한적 보조식 근거"),"supplement_general_evidence":("yellow","🟡 일반 보조식 근거"),"general_reptile_supplement":("yellow","🟡 일반 초식 파충류 보조근거"),"do_not_feed":("hold","🔴 급여 비권장")}
def esc(v): return html.escape(str(v or ""),quote=True)
def verdict_for(pid):
    if pid in SPECIAL:
        tone,label,summary=SPECIAL[pid]; return tone,label,summary,med.get(pid) or general.get(pid)
    a=med.get(pid) or general.get(pid)
    if not a: return "hold","⚪ 판단보류 / 검증 미완료","현재 공개 판정을 내릴 만큼 종별 급여 근거 검토가 완료되지 않았다.",None
    tone,label=VERDICT_MAP.get(a.get("verdict"),("hold","⚪ 판단보류 / 근거 부족")); return tone,label,a.get("why") or "근거 검토 중이다.",a

plant_by_id={p["id"]:p for p in plants}
def related_for(p,limit=6):
    same_family=[x for x in plants if x["id"]!=p["id"] and x.get("family") and x.get("family")==p.get("family")]
    same_category=[x for x in plants if x["id"]!=p["id"] and x.get("category") and x.get("category")==p.get("category") and x not in same_family]
    return (same_family+same_category)[:limit]

for p in plants:
    pid=p["id"]; d=ROOT/"plant"/pid; d.mkdir(parents=True,exist_ok=True); ko=p.get("ko") or pid; sci=p.get("scientific") or "학명 검증 중"
    title=f"육지거북 {ko} 먹어도 될까? 급여 판정·근거 | 거북밥 DB"; desc=f"육지거북에게 {ko}를 먹여도 되는지 확인한다. {ko}의 급여 판정, 학명·식물동정, 적용 범위, 주의사항과 근거를 한 페이지에서 확인한다."; canonical=f"{SITE_URL}/plant/{pid}/"
    tone,label,summary,a=verdict_for(pid); r=retail_by_id.get(pid); aliases=[]
    if r: aliases=list(dict.fromkeys((r.get("retail_terms") or [])+(r.get("aliases") or [])))
    if not aliases: aliases=[ko]+list(p.get("aliases") or [])[:3]
    identity_warning=(r and r.get("mapping_status")=="name_candidate_only"); role=(a or {}).get("role"); limits=(a or {}).get("limits") or []
    limits_html="".join(f"<li>{esc(x)}</li>" for x in limits) or "<li>근거 부족 상태에서는 안전하다고 추정하지 않는다.</li><li>단독·무제한 급여 판정으로 해석하지 않는다.</li>"
    identity_text="한국 유통명은 검색 후보일 뿐 실제 식물의 종 동정 결과가 아니다. 상품·재배품·야생채집물은 별도로 확인해야 한다." if identity_warning else "DB의 이름과 학명 표기는 검색 기준이다. 실제 급여할 개체의 식물종과 오염 여부는 별도로 확인해야 한다."
    related=related_for(p)
    related_html="".join(f'<a class="related" href="../{esc(x["id"])}/">{esc(x.get("ko") or x["id"])} 먹이 판정 →</a>' for x in related)
    share_text=f"육지거북 {ko} 먹이 판정 | 거북밥 DB"
    en_name=p.get("en") or sci
    en_pending="Evidence review is incomplete. Do not infer safety or unlimited feeding from missing evidence."
    en_scope="See the Korean evidence summary for the source-specific scope; evidence is not automatically transferred across taxa."
    en_identity="Database names are search references. Confirm the actual plant identity and contamination status before feeding."
    role_html=f"<div><b>식단 내 역할</b><br>{esc(role)}</div>" if role else "<div><b>식단 내 역할</b><br>아직 공개 권장 역할을 확정하지 않음</div>"
    if a:
        scope=a.get("applicability_note") or ("지중해 Testudo 일반 근거. 이베라 직접 정량근거와 동일하지 않음" if a.get("species_group")=="Mediterranean_Testudo" else "육지거북·초식 파충류 일반 근거. Mediterranean Testudo 직접 판정이 아님"); evidence_html=f"<div><b>적용 범위</b><br>{esc(scope)}</div>"
    else: evidence_html="<div><b>적용 범위</b><br>종별 판정 근거 검토 미완료</div>"
    schema=json.dumps({"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":canonical,"inLanguage":"ko","isPartOf":{"@type":"WebSite","name":"거북밥 DB Korea","url":SITE_URL+"/"}},ensure_ascii=False,separators=(",",":"))
    doc=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="article"><meta property="og:locale" content="ko_KR"><meta property="og:site_name" content="거북밥 DB Korea"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">
<script type="application/ld+json">{schema}</script>
<style>:root{{--bg:#f6f8f5;--card:#fff;--line:#dce5dd;--text:#17231b;--muted:#647067;--green:#e7f5eb;--yellow:#fff7df;--hold:#f1f3f2}}*{{box-sizing:border-box}}body{{font-family:system-ui,-apple-system,"Noto Sans KR",sans-serif;max-width:1180px;margin:auto;padding:22px;line-height:1.62;color:var(--text);background:var(--bg)}}a{{color:inherit}}.card{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;margin:12px 0}}.verdict{{font-weight:900;font-size:20px}}.green{{background:var(--green)}}.yellow{{background:var(--yellow)}}.hold{{background:var(--hold)}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}.grid>div{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px}}.warn{{border-left:5px solid #866f25}}.small{{font-size:13px;color:var(--muted)}}.relatedgrid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}}.related{{display:block;border:1px solid var(--line);border-radius:12px;padding:11px;text-decoration:none;font-weight:800;background:#fff}}.share{{display:flex;gap:8px;flex-wrap:wrap}}.topmeta{{display:flex;justify-content:flex-end;margin-bottom:8px}}.langswitch{{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff}}.langswitch button{{min-height:auto;padding:6px 9px;border:0;border-radius:0;background:#fff;color:var(--muted);font-size:11px}}.langswitch button.active{{background:#286a46;color:#fff}}.share button,.share a{{border:0;border-radius:12px;padding:11px 14px;font-weight:800;background:#e7f5eb;text-decoration:none;cursor:pointer}}h1{{margin-bottom:6px}}h2{{font-size:19px;margin:0 0 8px}}ul{{padding-left:20px}}@media(max-width:800px){{body{{padding:14px}}.grid{{grid-template-columns:1fr 1fr}}.relatedgrid{{grid-template-columns:1fr 1fr}}}}@media(max-width:520px){{.grid,.relatedgrid{{grid-template-columns:1fr}}}}</style></head><body>
<div class="topmeta"></div><p><a href="../../index.html">← 거북밥 DB 검색으로</a></p><h1>육지거북, {esc(ko)} 먹어도 될까?</h1><div class="small"><i>{esc(sci)}</i></div><section class="card {tone}"><h2>1. 결론 — {esc(ko)} 급여 판정</h2><div class="verdict">{esc(label)}</div><p class="ko-evidence">{esc(summary)}</p><p class="en-evidence" hidden>{esc(en_pending)}</p><p class="small"><b>판정 해석:</b> 이 결론은 아래에 표시된 적용 범위와 근거 수준 안에서만 유효하다. 혼합급여 가능 판정은 단독 주식·무제한 급여·고정 급여비율을 의미하지 않는다.</p></section><section class="card"><h2>2. 이 판정은 어디까지 적용되는가</h2><div class="grid">{role_html}{evidence_html}<div><b>식물 이름</b><br>{esc(', '.join(aliases))}</div><div><b>학명 표기</b><br><i>{esc(sci)}</i></div></div></section><section class="card warn"><h2>3. 식물동정 — 이름이 같아도 같은 식물은 아니다</h2><p class="ko-evidence">{esc(identity_text)}</p><p class="en-evidence" hidden>{esc(en_identity)}</p>{'<p><b>아욱 주의:</b> 한국 유통명 아욱을 Malva parviflora로 자동 매핑하지 않는다.</p>' if pid=='mallow' else ''}</section><section class="card"><h2>4. 근거의 한계와 해석 주의</h2><div class="ko-evidence"><ul>{limits_html}</ul></div><p class="en-evidence" hidden>{esc(en_scope)}</p><p class="small">야생에서 먹었다는 기록 ≠ 무제한 급여 권장. 사람용 영양자료 ≠ 육지거북 독성 한계치. 근거 부족 ≠ 안전.</p></section><section class="card"><h2>5. 추가로 확인할 식물</h2><div class="relatedgrid">{related_html}</div><p class="small"><b>탐색 링크:</b> 같은 과·카테고리의 다른 항목으로 이동하기 위한 기능이다. 식물학적 유사성이 동일한 급여 안전성·영양가·권장도를 뜻하지 않는다.</p></section><section class="card"><h2>이 판정 공유하기</h2><div class="share"><button type="button" onclick="navigator.clipboard.writeText(location.href).then(()=>this.textContent='링크 복사 완료')">링크 복사</button><a href="../../all-plants/">다른 먹이 찾기 →</a></div></section><nav class="small" aria-label="breadcrumb"><a href="../../index.html">거북밥 DB</a> › {esc(ko)}</nav><script src="../../language-toggle.js?v=20260926-3" defer></script></body></html>'''
    (d/"index.html").write_text(doc,encoding="utf-8")
print("generated",len(plants),"reviewed/public plant detail pages from",len(all_plants),"master records and",len(assessments),"assessments")