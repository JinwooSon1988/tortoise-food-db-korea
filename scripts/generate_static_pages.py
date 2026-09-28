from pathlib import Path
import json, html, re

ROOT=Path(__file__).resolve().parents[1]
SITE_URL="https://jinwooson1988.github.io/tortoise-food-db-korea"
all_plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))

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

# Public rendering uses the same canonical assessment registry as QA.
_public_assessments=json.loads((ROOT/"data/public_assessments.json").read_text(encoding="utf-8"))
assessments=_public_assessments.get("assessments",_public_assessments.get("records",[])) if isinstance(_public_assessments,dict) else _public_assessments
retail=json.loads((ROOT/"data/korean_retail_name_map.json").read_text(encoding="utf-8"))
evidence_records=json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8")).get("records",[])
evidence_by_id={e["id"]:e for e in evidence_records}
nutrition_records=json.loads((ROOT/"data/plant_nutrition_v56.json").read_text(encoding="utf-8")).get("plants",[])
nutrition_by_id={n["plant_id"]:n for n in nutrition_records if n.get("verification_status")=="verified"}
wild_records=json.loads((ROOT/"data/wild_feeding_evidence.json").read_text(encoding="utf-8")).get("records",[])
wild_by_plant={}
for w in wild_records:
    wild_by_plant.setdefault(w.get("plant_id"),[]).append(w)
risk_records=json.loads((ROOT/"data/wild_candidate_risk_screening.json").read_text(encoding="utf-8")).get("records",[])
risk_by_plant={r.get("plant_id"):r for r in risk_records}
med={a["plant_id"]:a for a in assessments if a.get("species_group")=="Mediterranean_Testudo"}
general={a["plant_id"]:a for a in assessments if a.get("species_group") in {"Tortoise_general","Herbivorous_reptile_general"}}
exact_by_plant={}
for a in assessments:
    if a.get("assessment_scope")=="exact_species" and a.get("animal_taxon") and a.get("animal_taxon")!="Testudo":
        exact_by_plant.setdefault(a["plant_id"],[]).append(a)
assessed_ids=set(med)|set(general)
# Public detail pages are evidence-reviewed records only. Master-only intake records stay in the research pool until assessed.
plants=[p for p in all_plants if p.get("identity_status")!="candidate_name" and p.get("id") in assessed_ids]
retail_by_id={r["plant_id"]:r for r in retail}
SPECIAL={"dandelion":("green","🟢 혼합급여 적합","루마니아와 남서부 불가리아의 야생 T. g. ibera에서 Taraxacum 섭식이 직접 관찰되었고 지중해 Testudo 전문 사육근거도 일치한다. 다만 야생 관찰 빈도를 사육 배합률로 환산하지 않는다."),"plantain":("yellow","🟡 혼합급여 지지근거 있음","Plantago 속과 지중해 Testudo의 섭식·사육 근거가 있다. 국내 실제 식물의 정확한 종 동정과 공식 영양자료 검증은 별도 확인이 필요하다."),"mallow":("hold","⚪ 판단보류 / 종 수준 미확정","한국 유통명 ‘아욱’만으로 특정 Malva 종을 확정하지 않는다. 특히 아욱을 Malva parviflora로 자동 간주하지 않는다.")}
directness_ko={"direct":"직접 근거","expert_husbandry":"전문 사육 근거","related_taxon":"근연 분류군 근거","contextual":"맥락 근거","composition_only":"성분 근거"}
applicability_ko={"exact_taxon":"정확한 대상 분류군","species":"종 수준","mediterranean_testudo":"지중해 육지거북류(Testudo속)","tortoise_general":"육지거북 일반","herbivorous_reptile_general":"초식 파충류 일반","composition_only":"성분 자료","taxon_group":"분류군 수준"}
VERDICT_MAP={"supported_mixed_diet":("green","A · 혼합식 활용 가능"),"limited_mixed_diet":("yellow","B · 제한적 혼합 급여"),"limited_supplement":("yellow","C · 가끔 보조 급여"),"supplement_general_evidence":("yellow","C · 가끔 보조 급여"),"general_reptile_supplement":("yellow","C · 가끔 보조 급여"),"do_not_feed":("danger","D · 급여하지 않음")}
def esc(v): return html.escape(str(v or ""),quote=True)
def source_link(url,label):
    if not url:
        return '<span class="small">원문 링크 미등록</span>'
    return '<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+'</a>'
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
    en_pending=("This plant has a reviewed evidence record. The feeding grade is limited to the evidence scope shown below; it does not imply unlimited feeding." if a else "Evidence review is incomplete. Do not infer safety or unlimited feeding from missing evidence.")
    en_scope=("Reviewed evidence is available. Check source taxon, plant part, directness, and limitations below before applying the result." if a else "Evidence is incomplete; do not transfer safety assumptions across taxa.")
    en_identity="Database names are search references. Confirm the actual plant identity and contamination status before feeding."
    role_html=f"<div><b>식단 내 역할</b><br>{esc(role)}</div>" if role else "<div><b>식단 내 역할</b><br>아직 공개 권장 역할을 확정하지 않음</div>"
    linked_evidence=[evidence_by_id[eid] for eid in ((a or {}).get("evidence_ids") or []) if eid in evidence_by_id]
    direct_count=sum(1 for e in linked_evidence if e.get("directness")=="direct")
    husbandry_count=sum(1 for e in linked_evidence if e.get("directness")=="expert_husbandry")
    indirect_count=len(linked_evidence)-direct_count-husbandry_count
    strength_label=("직접 근거 포함" if direct_count else ("전문 사육 근거 중심" if husbandry_count else ("간접·맥락 근거 중심" if linked_evidence else "공개 근거 미연결")))
    scopes=sorted({str(e.get("applicability")) for e in linked_evidence if e.get("applicability")})
    taxa=sorted({str(e.get("animal_taxon")) for e in linked_evidence if e.get("animal_taxon")})
    scope_note=(" · ".join(applicability_ko.get(x,x) for x in scopes) if scopes else "범위 미확인")
    taxon_note=(" / ".join(taxa) if taxa else "대상 동물 미확인")
    part_note=" / ".join(sorted({str(e.get("plant_part_state")) for e in linked_evidence if e.get("plant_part_state")})) or "부위 정보 미확인"
    quick_html=f'''<div class="quickfacts"><div><b>근거가 다루는 부위</b><strong>{esc(part_note)}</strong></div><div><b>근거 수준</b><strong>{esc(strength_label)}</strong></div><div><b>근거 구성</b><strong>직접 {direct_count} · 전문사육 {husbandry_count} · 기타 {indirect_count}</strong></div><div><b>적용 범위</b><strong>{esc(scope_note)}</strong><span class="small">{esc(taxon_note)}</span></div></div>'''
    interpretation_html='''<div class="decisionrule"><b>판정 읽는 법</b><span>급여 가능 판정도 단독 주식이나 무제한 급여를 뜻하지 않는다. 아래의 실제 급여 해석과 근거 한계를 함께 확인한다.</span></div>'''
    practical_html=f'''<section class="card practical"><h2>실제 급여에서는 이렇게 해석하세요</h2><div class="practicalgrid"><div><b>급여 역할</b><p>{esc(role or "현재 근거 범위 안에서 보조적으로 해석한다.")}</p></div><div><b>확인된 부위·상태</b><p>{esc(part_note)}</p></div><div><b>확인되지 않은 것</b><p>자료에 없는 급여량·빈도·장기 안전용량은 임의로 만들지 않는다. 야생 섭식도 단독 주식이나 무제한 급여의 뜻으로 바꾸지 않는다.</p></div></div></section>'''
    species_rows=[]
    for x in exact_by_plant.get(pid,[]):
        _,x_label=VERDICT_MAP.get(x.get("verdict"),("hold","별도 판정"))
        who=x.get("display_group") or x.get("species_group") or x.get("animal_taxon")
        species_rows.append(f'<article class="speciesexception"><div><b>{esc(who)}</b><span>{esc(x_label)}</span></div><p>{esc(x.get("why") or x.get("role") or "해당 종에 대한 별도 판정 근거가 있다.")}</p></article>')
    species_specific_html=(f'<section class="card species-specific"><h2>종별 특이사항</h2><p class="small">아래 내용은 특정 종에서 확인된 별도 근거다. 이 내용을 다른 육지거북 종에 자동으로 적용하지 않는다.</p>{"".join(species_rows)}</section>' if species_rows else "")
    evidence_cards=[]
    for i,e in enumerate(linked_evidence,1):
        url=e.get("url") or ""
        source=f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(e.get("source_title") or e.get("id"))}</a>' if url else esc(e.get("source_title") or e.get("id"))
        evidence_cards.append(f'''<article class="evcard"><div class="evhead"><b>근거 {i}</b><span>{esc(directness_ko.get(e.get("directness"),e.get("directness")))}</span></div><h3>{source}</h3><div class="evgrid"><div><b>대상 범위</b><br>{esc(applicability_ko.get(e.get("applicability"),e.get("applicability")))}</div><div><b>식물 분류</b><br><i>{esc(e.get("plant_taxon"))}</i></div><div><b>대상 동물</b><br>{esc(e.get("animal_taxon"))}</div><div><b>식물 부위·상태</b><br>{esc(e.get("plant_part_state"))}</div></div><p><b>이 근거가 지지하는 내용</b><br>{esc(e.get("supports"))}</p><p class="limit"><b>이 근거만으로 말할 수 없는 내용</b><br>{esc(e.get("does_not_support"))}</p></article>''')
    evidence_cards_html="".join(evidence_cards) or '<p>현재 공개 가능한 개별 근거 레코드가 연결되지 않았다. 따라서 안전성을 추정하지 않는다.</p>'
    scholarly=[e for e in linked_evidence if e.get("doi") or e.get("pmid") or e.get("source_type")=="peer_reviewed_article"]
    scholarly_cards=[]
    for e in scholarly:
        doi=e.get("doi")
        pmid=e.get("pmid")
        ids=[]
        if doi: ids.append(f'DOI: {esc(doi)}')
        if pmid: ids.append(f'PMID: {esc(pmid)}')
        scholarly_cards.append(f'''<article class="paper"><b>{esc(e.get("source_title"))}</b><div class="papergrid"><div><span>연구 대상</span><strong>{esc(e.get("animal_taxon") or "미기재")}</strong></div><div><span>식물·부위</span><strong>{esc((e.get("plant_taxon") or "미기재")+" · "+(e.get("plant_part_state") or "미기재"))}</strong></div><div><span>근거 직접성</span><strong>{esc(directness_ko.get(e.get("directness"),e.get("directness") or "미기재"))}</strong></div><div><span>적용 범위</span><strong>{esc(applicability_ko.get(e.get("applicability"),e.get("applicability") or "미기재"))}</strong></div></div><p><b>이 자료가 지지하는 것:</b> {esc(e.get("supports"))}</p><p class="limit"><b>이 자료만으로 말할 수 없는 것:</b> {esc(e.get("does_not_support"))}</p><p class="small">{' · '.join(ids) or '학술 식별자 미기재'}</p>{source_link(e.get("url"),"원문/초록 열기")}</article>''')
    scholarly_html="".join(scholarly_cards) or '<p>현재 이 식물에 직접 연결된 동료심사 논문 레코드는 없다. 전문 DB 근거와 학술 근거를 구분해 표시한다.</p>'
    wild=wild_by_plant.get(pid,[])
    risk=risk_by_plant.get(pid)
    conflict_html=""
    if wild and risk and (risk.get("signals") or risk.get("publication_blocker")):
        risk_items="".join(f"<li><b>{esc(x.get('type') or '위험 신호')}</b> — {esc(x.get('finding'))}<br><span class=\"small\">{esc(x.get('interpretation'))}</span></li>" for x in risk.get("signals",[]))
        conflict_html=f'''<div class="conflict"><b>⚠ 근거 충돌 또는 안전성 미해결</b><p>야생 섭식 기록이 있지만 독성·항영양성분 또는 다른 동물의 수의학적 위험 신호도 확인됐다. 야생에서 먹는다는 사실만으로 사육 급여 안전성을 확정하지 않는다.</p><ul>{risk_items}</ul><p><b>현재 공개판정의 걸림돌:</b> {esc(risk.get("publication_blocker") or "추가 검토 필요")}</p></div>'''
    wild_cards=[]
    for w in wild:
        wild_cards.append(f'''<article class="evcard wildcard"><div class="evhead"><b>야생 섭식 기록</b><span>{esc(w.get("ibera_applicability") or "적용범위 확인 필요")}</span></div><h3>{esc(w.get("tortoise_taxon") or "대상 거북 미상")} · {esc(w.get("population_region") or "지역 미상")}</h3><div class="evgrid"><div><b>확인 방법</b><br>{esc(w.get("study_method") or "미상")}</div><div><b>먹은 부위</b><br>{esc(w.get("plant_part") or "미상")}</div><div><b>시기</b><br>{esc(w.get("season") or "미상")}</div><div><b>섭식 기록</b><br>{esc(w.get("feeding_signal") or "확인")}</div></div><p><b>이 기록이 뜻하는 것</b><br>야생에서 이 식물을 실제 먹이로 이용한 근거다.</p><p class="limit"><b>이 기록만으로 말할 수 없는 것</b><br>{esc(w.get("limitations") or "야생 섭식 기록만으로 사육 급여량이나 무제한 급여 안전성을 정할 수 없다.")}</p><p class="small"><b>원자료 식물명:</b> <i>{esc(w.get("plant_taxon_reported"))}</i> · <b>현재 수용명:</b> <i>{esc(w.get("plant_taxon_accepted"))}</i> · <b>근거 ID:</b> {esc(w.get("source_id"))}</p></article>''')
    wild_html="".join(wild_cards)
    wild_section=(f'''<section class="card"><h2>6. 야생에서는 실제로 어떻게 먹었나?</h2><p>야생 섭식 자료가 있으면 어떤 육지거북이 어디에서 어떤 방법으로 이 식물을 먹은 것이 확인됐는지 보여준다. <b>야생에서 먹었다는 사실은 중요한 근거지만, 사육장에서 마음껏 먹여도 된다는 뜻은 아니다.</b></p>{conflict_html}{wild_html}</section>''' if wild_cards else "")
    section_offset=1 if wild_cards else 0
    nutrition_section_no=6+section_offset
    scholarly_section_no=7+section_offset
    related_section_no=8+section_offset
    nu=nutrition_by_id.get(pid)
    if nu:
        def nv(key,unit=""):
            v=nu.get(key)
            return "미확인" if v is None else f"{v}{unit}"
        nutrition_html=f'''<div class="nutgrid"><div><b>수분</b><strong>{nv("water_g"," g")}</strong></div><div><b>식이섬유</b><strong>{nv("fiber_g"," g")}</strong></div><div><b>칼슘</b><strong>{nv("calcium_mg"," mg")}</strong></div><div><b>인</b><strong>{nv("phosphorus_mg"," mg")}</strong></div><div><b>Ca:P</b><strong>{nv("calcium_phosphorus_ratio")}</strong></div><div><b>단백질</b><strong>{nv("protein_g"," g")}</strong></div><div><b>칼륨</b><strong>{nv("potassium_mg"," mg")}</strong></div><div><b>비타민 C</b><strong>{nv("vitamin_c_mg"," mg")}</strong></div></div><p class="small"><b>자료 기준:</b> {esc(nu.get("basis"))} · <b>자료명:</b> {esc(nu.get("food_description"))}</p><p><b>원자료:</b> <a href="{esc(nu.get("source_url"))}" target="_blank" rel="noopener noreferrer">{esc(nu.get("source_name"))} · {esc(nu.get("source_id"))}</a></p><p class="small">영양성분 수치는 식품성분 자료이며 육지거북의 독성 한계치나 단독 급여비율을 의미하지 않는다.</p>'''
    else:
        nutrition_html='<p><b>검증된 공식 영양성분 자료가 아직 연결되지 않았다.</b></p><p class="small">자료 부재를 0으로 처리하거나 안전·위험 판정의 근거로 사용하지 않는다.</p>'
    if a:
        scope=a.get("applicability_note") or ("지중해 육지거북류(Testudo속)에 관한 일반 근거다. 이베라 그리스육지거북을 직접 시험해 얻은 정량 자료와는 다르다" if a.get("species_group")=="Mediterranean_Testudo" else "육지거북·초식 파충류 일반 근거. Mediterranean Testudo 직접 판정이 아님"); evidence_html=f"<div><b>적용 범위</b><br>{esc(scope)}</div>"
    else: evidence_html="<div><b>적용 범위</b><br>종별 판정 근거 검토 미완료</div>"
    schema=json.dumps({"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":canonical,"inLanguage":"ko","isPartOf":{"@type":"WebSite","name":"거북밥 DB Korea","url":SITE_URL+"/"}},ensure_ascii=False,separators=(",",":"))
    doc=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="article"><meta property="og:locale" content="ko_KR"><meta property="og:site_name" content="거북밥 DB Korea"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">
<script type="application/ld+json">{schema}</script>
<style>:root{{--bg:#f6f8f5;--card:#fff;--line:#dce5dd;--text:#17231b;--muted:#647067;--green:#e7f5eb;--yellow:#fff7df;--hold:#f1f3f2;--danger:#fdeaea}}*{{box-sizing:border-box}}body{{font-family:system-ui,-apple-system,"Noto Sans KR",sans-serif;max-width:1180px;margin:auto;padding:22px;line-height:1.62;color:var(--text);background:var(--bg)}}a{{color:inherit}}.card{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;margin:12px 0}}.verdict{{font-weight:950;font-size:25px;line-height:1.25}}.quickfacts{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:12px 0}}.quickfacts>div{{border:1px solid rgba(0,0,0,.09);border-radius:10px;padding:9px;background:#fff}}.quickfacts b{{display:block;font-size:12px;color:var(--muted)}}.quickfacts strong{{display:block;margin-top:3px}}.quickfacts .small{{display:block;margin-top:3px;font-size:11px}}.decisionrule{{display:flex;gap:10px;align-items:flex-start;margin-top:10px;padding:10px 12px;border-top:1px solid rgba(0,0,0,.08);font-size:13px}}.decisionrule b{{flex:0 0 auto;color:#28583c}}.decisionrule span{{color:var(--muted)}}.green{{background:var(--green)}}.yellow{{background:var(--yellow)}}.hold{{background:var(--hold)}}.danger{{background:var(--danger);border-color:#e8bcbc}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}.grid>div{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px}}.warn{{border-left:5px solid #866f25}}.small{{font-size:13px;color:var(--muted)}}.relatedgrid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}}.practicalgrid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}}.practicalgrid>div{{border:1px solid var(--line);border-radius:13px;padding:14px;background:#fbfdfb}}.practicalgrid b{{font-size:13px;color:#28583c}}.practicalgrid p{{margin:5px 0 0;font-size:14px;line-height:1.6}}.species-specific{{border-left:4px solid #4f7d61;background:#f8fbf8}}.species-specific>h2{{margin-bottom:6px}}.speciesexception{{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-top:10px;background:#fff}}.speciesexception>div{{display:flex;justify-content:space-between;gap:12px;align-items:center}}.speciesexception>div b{{font-size:14px}}.speciesexception>div span{{flex:0 0 auto;border:1px solid var(--line);border-radius:999px;padding:4px 8px;background:#f2f7f3;font-size:12px;font-weight:900}}.speciesexception p{{margin:8px 0 0;font-size:13px;line-height:1.6;color:var(--muted)}}.legend{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin:10px 0 14px}}.legend>b{{grid-column:1/-1}}.legend span{{border:1px solid var(--line);border-radius:10px;padding:9px;background:#f8faf8;font-size:13px}}.evcard{{border:1px solid var(--line);border-radius:14px;padding:14px;margin:10px 0;background:#fff}}.evhead{{display:flex;justify-content:space-between;gap:8px;align-items:center}}.evhead span{{font-size:12px;font-weight:900;border:1px solid var(--line);border-radius:999px;padding:4px 8px;background:#f3f7f3}}.evcard h3{{font-size:16px;margin:8px 0}}.evgrid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}}.evgrid>div{{border:1px solid var(--line);border-radius:10px;padding:9px;background:#fafcf9;font-size:13px}}.evcard .limit{{background:#fff8e8;border-radius:10px;padding:10px}}.conflict{{border:2px solid #a56b19;background:#fff5df;border-radius:12px;padding:12px;margin:10px 0}}.conflict> b{{font-size:17px}}.nutrition-rule{{border-left:5px solid #286a46;background:#f2f8f4;border-radius:10px;padding:10px 12px}}.paper{{border:1px solid var(--line);border-radius:12px;padding:12px;margin:9px 0;background:#fbfcfb}}.papergrid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin:9px 0}}.papergrid>div{{border:1px solid var(--line);border-radius:8px;padding:7px}}.papergrid span{{display:block;font-size:11px;color:var(--muted)}}.papergrid strong{{font-size:12px}}.paper .limit{{background:#fff7e8;border-radius:8px;padding:8px}}.nutgrid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}}.nutgrid>div{{border:1px solid var(--line);border-radius:10px;padding:10px;background:#fafcf9}}.nutgrid b{{display:block;font-size:12px;color:var(--muted)}}.nutgrid strong{{display:block;font-size:18px;margin-top:3px}}.related{{display:block;border:1px solid var(--line);border-radius:12px;padding:11px;text-decoration:none;font-weight:800;background:#fff}}.share{{display:flex;gap:8px;flex-wrap:wrap}}.topmeta{{display:flex;justify-content:flex-end;margin-bottom:8px}}.langswitch{{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff}}.langswitch button{{min-height:auto;padding:6px 9px;border:0;border-radius:0;background:#fff;color:var(--muted);font-size:11px}}.langswitch button.active{{background:#286a46;color:#fff}}.share button,.share a{{border:0;border-radius:12px;padding:11px 14px;font-weight:800;background:#e7f5eb;text-decoration:none;cursor:pointer}}h1{{margin-bottom:6px}}h2{{font-size:19px;margin:0 0 8px}}ul{{padding-left:20px}}@media(max-width:800px){{body{{padding:14px}}.grid{{grid-template-columns:1fr 1fr}}.evgrid{{grid-template-columns:1fr 1fr}}.nutgrid{{grid-template-columns:1fr 1fr}}.interpret{{grid-template-columns:1fr}}.quickfacts{{grid-template-columns:1fr 1fr}}.papergrid{{grid-template-columns:1fr 1fr}}.legend{{grid-template-columns:1fr}}.relatedgrid{{grid-template-columns:1fr 1fr}}}}@media(max-width:520px){{.grid,.relatedgrid,.practicalgrid{{grid-template-columns:1fr}}}}.detailnav{{display:flex;justify-content:space-between;align-items:center;margin:0 0 34px;padding:10px 2px 16px;border-bottom:1px solid var(--line);font-size:13px}}.detailnav a{{font-weight:850;text-decoration:none;color:#235f3e}}.detailnav span{{color:var(--muted)}}.planthead{{padding:10px 2px 24px}}.planthead .eyebrow{{font-size:10px;font-weight:900;letter-spacing:.14em;color:#357653}}.planthead h1{{font-size:clamp(34px,7vw,52px);letter-spacing:-.05em;margin:6px 0 2px}}.scientific{{color:var(--muted);font-size:15px}}.planthead p{{color:var(--muted);margin:12px 0 0}}.decision{{padding:26px;border-width:2px}}.decisionlabel{{font-size:12px;font-weight:900;letter-spacing:.08em;color:var(--muted);margin-bottom:8px}}.decision .verdict{{font-size:clamp(25px,5vw,36px);line-height:1.2;margin:0 0 12px}}.decisionwhy{{font-size:16px;line-height:1.75;max-width:760px}}.decision .quickfacts{{margin-top:20px}}.decision .interpret{{margin-top:10px}}.card{{scroll-margin-top:18px}}@media(max-width:520px){{.detailnav span{{display:none}}.decision{{padding:20px}}.planthead{{padding-top:2px}}.speciesexception>div{{align-items:flex-start;flex-direction:column;gap:6px}}</style></head><body>
<header class="detailnav"><a href="../../index.html">← 다른 먹이 검색</a><div class="topmeta"><span>거북밥 · 근거 기반 판정</span></div></header><main><div class="planthead"><div class="eyebrow">급여 근거 검토</div><h1>{esc(ko)}</h1><div class="scientific"><i>{esc(sci)}</i></div><p>육지거북에게 먹여도 되는지, 어떤 근거로 어디까지 판단할 수 있는지 정리했다.</p></div><section class="card {tone} decision"><div class="decisionlabel">먼저 보는 결론</div><div class="verdict">{esc(label)}</div><p class="decisionwhy ko-evidence">{esc(summary)}</p><p class="en-evidence" hidden>{esc(en_pending)}</p>{quick_html}{interpretation_html}</section>{practical_html}{species_specific_html}<section class="card"><h2>이 판정은 어디까지 적용될까?</h2><div class="grid">{role_html}{evidence_html}<div><b>식물 이름</b><br>{esc(', '.join(aliases))}</div><div><b>학명 표기</b><br><i>{esc(sci)}</i></div></div></section><section class="card warn"><h2>먹이기 전에 식물부터 확인하세요</h2><p class="ko-evidence">{esc(identity_text)}</p><p class="en-evidence" hidden>{esc(en_identity)}</p>{'<p><b>아욱 주의:</b> 한국 유통명 아욱을 Malva parviflora로 자동 매핑하지 않는다.</p>' if pid=='mallow' else ''}</section><section class="card"><h2>왜 이렇게 판정했을까?</h2><p class="ko-evidence">판정에 사용한 근거를 하나씩 확인한다. <b>직접 근거</b>는 해당 육지거북·식물·질문을 직접 다룬 자료이고, <b>간접 근거</b>는 다른 동물이나 가까운 식물에서 얻은 참고 자료다. 간접 근거만으로 안전성을 확정하지 않는다.</p><p class="en-evidence" hidden>This section explains the evidence behind the conclusion. <b>Direct evidence</b> addresses the target question directly. <b>Indirect evidence</b> comes from other animals or related plants and is used only as context; indirect evidence alone does not establish safety.</p><div class="legend"><b>근거 읽는 법</b><span><strong>직접 근거</strong> 해당 대상·질문을 직접 다룸</span><span><strong>전문 사육 근거</strong> 육지거북 사육을 전문적으로 다루는 자료</span><span><strong>근연·맥락 근거</strong> 참고 가능하지만 그대로 전이할 수 없음</span><span><strong>성분 근거</strong> 성분 존재를 보여줄 뿐 급여 안전성을 단독 증명하지 않음</span></div>{evidence_cards_html}</section><section class="card"><h2>현재 근거의 한계</h2><p class="small">아래 내용은 이 판정이 직접 증명하지 못하는 범위다. 확인되지 않은 급여량·빈도·장기 안전성을 임의로 보충하지 않는다.</p><h3>이 판정으로 말할 수 없는 것</h3><div class="ko-evidence"><ul>{limits_html}</ul></div><p class="en-evidence" hidden>{esc(en_scope)}</p><p class="small">야생에서 먹었다는 기록 ≠ 무제한 급여 권장. 사람용 영양자료 ≠ 육지거북 독성 한계치. 근거 부족 ≠ 안전.</p></section>{wild_section}<section class="card"><h2>{nutrition_section_no}. 검증된 영양성분 자료</h2><p class="nutrition-rule"><b>중요:</b> 영양성분표는 식물의 영양적 맥락을 이해하기 위한 보조자료다. Ca:P, 섬유질 또는 특정 영양소 수치가 좋아도 독성·항영양성분·식물동정·대상종 근거를 대신하지 않으며, 이 수치만으로 급여 등급을 올리지 않는다.</p>{nutrition_html}</section><section class="card"><h2>{scholarly_section_no}. 더 깊이 보고 싶다면 — 학술자료와 원논문</h2><p>여기에는 연구자가 검토한 학술논문과 원자료를 모은다. 어려운 논문을 전부 읽지 않아도 되도록 먼저 핵심을 풀어 설명하고, 직접 확인하고 싶은 사람을 위해 DOI·PMID와 원문 연결도 함께 제공한다.</p><p class="small">전문 사육자료와 동료심사 논문은 성격이 다르므로 같은 수준의 근거로 취급하지 않는다.</p>{scholarly_html}</section><section class="card"><h2>{related_section_no}. 추가로 확인할 식물</h2><div class="relatedgrid">{related_html}</div><p class="small"><b>탐색 링크:</b> 같은 과·카테고리의 다른 항목으로 이동하기 위한 기능이다. 식물학적 유사성이 동일한 급여 안전성·영양가·권장도를 뜻하지 않는다.</p></section><section class="card"><h2>이 판정 공유하기</h2><div class="share"><button type="button" onclick="navigator.clipboard.writeText(location.href).then(()=>this.textContent='링크 복사 완료')">링크 복사</button><a href="../../all-plants/">다른 먹이 찾기 →</a></div></section><nav class="small" aria-label="breadcrumb"><a href="../../index.html">거북밥 DB</a> › {esc(ko)}</nav></main><script src="../../language-toggle.js?v=20260926-3" defer></script></body></html>'''
    (d/"index.html").write_text(doc,encoding="utf-8")

# Keep search-engine discovery synchronized with the same reviewed/public set
# used to generate detail pages. Preserve durable non-plant landing/guide URLs.
sitemap_path=ROOT/"sitemap.xml"
existing=sitemap_path.read_text(encoding="utf-8") if sitemap_path.exists() else ""
nonplant_urls=[]
for loc in re.findall(r"<loc>(.*?)</loc>",existing):
    if "/plant/" not in loc and loc not in nonplant_urls:
        nonplant_urls.append(loc)
if SITE_URL+"/" not in nonplant_urls:
    nonplant_urls.insert(0,SITE_URL+"/")
plant_urls=[f"{SITE_URL}/plant/{p['id']}/" for p in plants]
urls=nonplant_urls+plant_urls
sitemap_lines=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
sitemap_lines.extend(f"  <url><loc>{esc(url)}</loc></url>" for url in urls)
sitemap_lines.append("</urlset>")
sitemap_path.write_text("\n".join(sitemap_lines)+"\n",encoding="utf-8")
print("generated",len(plants),"reviewed/public plant detail pages from",len(all_plants),"master records and",len(assessments),"assessments; sitemap plant URLs",len(plant_urls))