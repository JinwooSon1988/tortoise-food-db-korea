from pathlib import Path
import json, html, re, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from public_verdict import load_assessments, representative, display, species_notes, scope_label, by_plant, public_plants

ROOT=Path(__file__).resolve().parents[1]
SITE_URL="https://jinwooson1988.github.io/tortoise-food-db-korea"
all_plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))

# Public rendering uses the same canonical assessment registry and the same
# representative-verdict rule as the home search (verdict-core.js).
assessments=load_assessments()
assessments_by_plant=by_plant(assessments)
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
ibera=json.loads((ROOT/"data/ibera_direct_feeding_evidence_v56.json").read_text(encoding="utf-8"))
ibera_sources={s["source_id"]:s for s in ibera.get("sources",[])}
ibera_by_plant={}
for o in ibera.get("observations",[]):
    if o.get("plant_id"): ibera_by_plant.setdefault(o["plant_id"],[]).append(o)
images=json.loads((ROOT/"data/verified_plant_images_v56.json").read_text(encoding="utf-8")).get("images",[])
image_by_plant={i["plant_id"]:i for i in images if i.get("identity_scope") in {"exact_species","exact_subspecies","exact_variety"}}
curated_identity=json.loads((ROOT/"data/curated_identity_notes.json").read_text(encoding="utf-8")).get("notes",{})

# Public detail pages: the same set the home search exposes (non-candidate + any public assessment).
plants=public_plants(all_plants,assessments)
retail_by_id={r["plant_id"]:r for r in retail}
directness_ko={"direct":"직접 근거","expert_husbandry":"전문 사육 근거","related_taxon":"근연 분류군 근거","contextual":"맥락 근거","composition_only":"성분 근거"}
applicability_ko={"exact_taxon":"정확한 대상 분류군","species":"종 수준","mediterranean_testudo":"지중해 육지거북류(Testudo속)","tortoise_general":"육지거북 일반","herbivorous_reptile_general":"초식 파충류 일반","composition_only":"성분 자료","taxon_group":"분류군 수준"}

def esc(v): return html.escape(str(v or ""),quote=True)
def rich(v):
    """Escape, then render *text* as italic (used for scientific names in curated notes)."""
    return re.sub(r"\*([^*]+)\*",r"<i>\1</i>",esc(v))

def source_kind(e):
    t=str(e.get("source_type") or "")
    if t.startswith("peer_reviewed") or e.get("pmid"): return (0,"동료심사 논문")
    if t.startswith("academic") or t=="conference_proceedings": return (1,"학술 연구")
    if t.startswith("veterinary") or "veterinary" in t: return (2,"수의학 자료")
    if t.startswith("specialist") or t.startswith("expert"): return (3,"전문 사육·식물 자료")
    if "taxonomy" in t or "taxonomic" in t or "botanical" in t or "biodiversity" in t or "agriculture" in t: return (4,"식물동정·분류 자료")
    if "nutrition" in t or "food_composition" in t: return (5,"성분 참고자료")
    if t.startswith("regulatory_"): return (6,"공식 평가자료")
    return (7,"기타 공공·맥락 자료")

def evidence_role(e):
    t=str(e.get("source_type") or "")
    if "taxonomy" in t or "taxonomic" in t or "botanical" in t or "biodiversity" in t or "agriculture" in t:
        return "식물의 이름·분류·정체성을 확인하는 보조자료 — 급여 안전성 자체를 증명하지 않음"
    if "nutrition" in t or "food_composition" in t:
        return "성분을 확인하는 참고자료 — 급여 안전성 자체를 증명하지 않음"
    if e.get("directness")=="direct":
        return "급여 판정에 직접 연결되는 근거"
    return "급여 판정을 보조하는 간접·맥락 근거"

def related_for(p,limit=6):
    same_family=[x for x in plants if x["id"]!=p["id"] and x.get("family") and x.get("family")==p.get("family")]
    same_category=[x for x in plants if x["id"]!=p["id"] and x.get("category") and x.get("category")==p.get("category") and x not in same_family]
    return (same_family+same_category)[:limit]

CSS='''
:root{--bg:#f6f8f5;--card:#fff;--line:#dce5dd;--text:#17231b;--muted:#5f6c63;--forest:#235f3e;--green:#e7f5eb;--yellow:#fff7df;--hold:#f1f3f2;--danger:#fdeaea}
*{box-sizing:border-box}body{font-family:system-ui,-apple-system,"Noto Sans KR",sans-serif;max-width:920px;margin:auto;padding:18px 22px 40px;line-height:1.62;color:var(--text);background:var(--bg)}
a{color:inherit}a:focus-visible,button:focus-visible{outline:3px solid rgba(40,106,70,.28);outline-offset:3px}
.skiplink{position:absolute;left:12px;top:-60px;z-index:50;background:#fff;border:2px solid #286a46;border-radius:9px;padding:9px 12px;font-weight:900;text-decoration:none}.skiplink:focus{top:10px}
.small{font-size:13px;color:var(--muted)}h1{margin:0}h2{font-size:18px;margin:0 0 8px}h3{font-size:15px;margin:0 0 6px}ul{padding-left:20px;margin:6px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;margin:12px 0;scroll-margin-top:18px}
.detailnav{display:flex;justify-content:space-between;align-items:center;margin:0 0 14px;padding:4px 2px 12px;border-bottom:1px solid var(--line);font-size:13px}.detailnav a{font-weight:850;text-decoration:none;color:var(--forest)}.detailnav span{color:var(--muted)}
.planthead{padding:6px 2px 10px}.planthead h1{font-size:clamp(30px,6vw,44px);letter-spacing:-.04em;line-height:1.15}.scientific{color:var(--muted);font-size:15px;margin-top:2px}.aliases{font-size:12px;color:var(--muted);margin-top:4px}
.green{background:var(--green)}.yellow{background:var(--yellow)}.hold{background:var(--hold)}.danger{background:var(--danger);border-color:#e8bcbc}
.decision{border-width:2px;padding:20px 22px}.decisionlabel{font-size:12px;font-weight:800;color:var(--muted);margin-bottom:6px}
.verdictline{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.gradeletter{display:inline-flex;align-items:center;justify-content:center;min-width:48px;height:48px;padding:0 10px;border-radius:12px;background:#fff;border:2px solid rgba(0,0,0,.14);font-size:26px;font-weight:950}.hold .gradeletter{font-size:17px}
.verdict{font-weight:950;font-size:clamp(22px,4.6vw,30px);line-height:1.2}.meaning{font-size:16px;font-weight:750;margin:10px 0 0}
.decisionwhy{font-size:15px;line-height:1.7;margin:10px 0 0;color:#2c3a31}.decisionwhy b{display:block;font-size:12px;color:var(--muted)}
.gradekey{display:flex;flex-wrap:wrap;gap:4px 10px;margin-top:11px;padding-top:8px;border-top:1px solid rgba(0,0,0,.08);font-size:11px;color:var(--muted)}.gradekey b{color:var(--text)}.gradekey .on{color:var(--text);font-weight:850}
.practicalgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.practicalgrid>div{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:#fbfdfb}.practicalgrid b{font-size:12px;color:var(--forest)}.practicalgrid p{margin:4px 0 0;font-size:14px}
.species-specific{background:#fbfcfb;padding:14px 18px}.species-specific h2{font-size:15px}.speciesexception{border-top:1px solid var(--line);padding:9px 0 0;margin-top:9px}.speciesexception>div{display:flex;justify-content:space-between;gap:12px;align-items:center;font-size:14px}.speciesexception>div span{flex:0 0 auto;font-size:12px;font-weight:800;color:var(--forest)}.speciesexception p{margin:4px 0 0;font-size:13px;color:var(--muted)}
.scopefold{margin-top:2px}.scopefold>summary{cursor:pointer;font-weight:850;color:var(--forest);padding:9px 2px;list-style-position:inside;border-radius:8px}.scopefold>summary:focus-visible{outline:3px solid rgba(40,106,70,.28);outline-offset:3px}.scopebody{padding-top:4px}.scopebody>div{padding:12px 0;border-top:1px solid var(--line)}.scopebody>div:first-of-type{border-top:0;padding-top:4px}.scopecard p{margin:4px 0 0;font-size:14px}
.identity-alert{background:#fff8e6;border:1px solid #e8cf86;border-left:5px solid #a07b16;border-radius:12px;padding:12px 14px!important;margin:6px 0}.identity-alert h3{color:#6d5207}
.identity-note h3{color:#405047}.identity-note p{color:var(--muted)}
.plantphoto{display:flex;gap:12px;align-items:flex-start;margin-top:8px}.plantphoto img{width:112px;height:112px;object-fit:cover;border-radius:10px;border:1px solid var(--line);background:#fff}.plantphoto figcaption{font-size:11px;color:var(--muted);line-height:1.5}
.principles{font-size:12px;color:var(--muted);margin-top:8px}
.evidence-deep{margin-top:24px;border-top:3px solid #315f46}.sectioneyebrow{font-size:11px;font-weight:900;letter-spacing:.08em;color:#357653;margin-bottom:3px}
.evsummary{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.evsummary span{border:1px solid var(--line);border-radius:999px;padding:4px 10px;font-size:12px;background:#f7faf7}
.legend{font-size:12px;color:var(--muted);margin:6px 0 10px}.legend b{color:var(--text)}
.evcard{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:10px 0;background:#fff}.evhead{display:flex;flex-wrap:wrap;gap:6px;align-items:center}.evhead span{font-size:11px;font-weight:850;border:1px solid var(--line);border-radius:999px;padding:3px 8px;background:#f3f7f3}.evhead .paper{background:#eaf2fb;border-color:#c9daee}
.evcard h3{font-size:15px;margin:8px 0 6px}.evmeta{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;font-size:12px;margin:0 0 8px}.evmeta dt{color:var(--muted)}.evmeta dd{margin:0}
.evcard p{font-size:13px;margin:6px 0}.evcard .limit{background:#fff8e8;border-radius:8px;padding:8px 10px}.evcard .ids{font-size:12px;color:var(--muted)}
.conflict{border:2px solid #a56b19;background:#fff5df;border-radius:12px;padding:12px;margin:10px 0}
.nutgrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.nutgrid>div{border:1px solid var(--line);border-radius:10px;padding:9px;background:#fafcf9}.nutgrid b{display:block;font-size:12px;color:var(--muted)}.nutgrid strong{display:block;font-size:17px}
.relatedgrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.related{display:block;border:1px solid var(--line);border-radius:10px;padding:10px;text-decoration:none;font-weight:800;background:#fff;font-size:14px}
.share{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.share button,.share a{border:0;border-radius:12px;padding:11px 14px;font-weight:800;background:#e7f5eb;text-decoration:none;cursor:pointer;font-size:14px}
.topmeta{display:flex;justify-content:flex-end}.langswitch{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff}.langswitch button{padding:6px 9px;border:0;border-radius:0;background:#fff;color:var(--muted);font-size:11px}.langswitch button.active{background:#286a46;color:#fff}
@media(max-width:700px){body{padding:12px 14px 32px}.nutgrid{grid-template-columns:1fr 1fr}.relatedgrid{grid-template-columns:1fr 1fr}}
@media(max-width:520px){.detailnav span{display:none}.planthead{padding:2px 2px 6px}.decision{padding:14px 15px}.gradeletter{min-width:40px;height:40px;font-size:21px}.meaning{font-size:15px;margin-top:8px}.decisionwhy{font-size:14px;margin-top:7px}.gradekey{gap:3px 8px;margin-top:9px;padding-top:7px;font-size:10px}.card{padding:14px}.practicalgrid,.relatedgrid{grid-template-columns:1fr}.speciesexception>div{align-items:flex-start;flex-direction:column;gap:2px}.evidence-deep{padding:13px}.evsummary{gap:5px}.evcard{padding:11px 12px;margin:8px 0}.evhead{gap:4px}.evhead span{font-size:10px;padding:2px 6px}.evcard h3{font-size:14px;line-height:1.45}.evrole{font-size:12px;line-height:1.5}.evmeta{grid-template-columns:72px 1fr;font-size:11px;gap:2px 7px}.evcard p{font-size:12px;line-height:1.55}.sourceopen{min-height:40px;align-items:center}}
'''.replace("\n","")

for p in plants:
    pid=p["id"]; d=ROOT/"plant"/pid; d.mkdir(parents=True,exist_ok=True); ko=p.get("ko") or pid; sci=p.get("scientific") or "학명 검증 중"
    title=f"육지거북 {ko} 먹어도 될까? 급여 판정·근거 | 거북밥 DB"; desc=f"육지거북에게 {ko}를 먹여도 되는지 확인한다. {ko}의 급여 판정, 학명·식물동정, 적용 범위, 주의사항과 근거를 한 페이지에서 확인한다."; canonical=f"{SITE_URL}/plant/{pid}/"
    rows=assessments_by_plant.get(pid,[])
    a=representative(rows); g=display(a)
    tone,grade,label,meaning=g["tone"],g["grade"],g["label"],g["meaning"]
    summary=(a or {}).get("why") or ("지중해 Testudo 또는 육지거북 일반을 대상으로 한 공개 판정이 아직 없다. 아래 종별 특이사항은 해당 종에만 적용된다." if not a else "근거 검토 중이다.")
    r=retail_by_id.get(pid); aliases=[]
    if r: aliases=list(dict.fromkeys((r.get("retail_terms") or [])+(r.get("aliases") or [])))
    if not aliases: aliases=list(p.get("aliases") or [])[:4]
    aliases=[x for x in aliases if x!=ko]
    # Identity risk comes only from existing data: retail name mapping or master identity status.
    identity_warning=bool((r and r.get("mapping_status")=="name_candidate_only") or p.get("identity_status")=="needs_species_level_mapping")
    role=(a or {}).get("role"); limits=(a or {}).get("limits") or []
    linked_evidence=[evidence_by_id[eid] for eid in ((a or {}).get("evidence_ids") or []) if eid in evidence_by_id]
    direct_count=sum(1 for e in linked_evidence if e.get("directness")=="direct")
    husbandry_count=sum(1 for e in linked_evidence if e.get("directness")=="expert_husbandry")
    indirect_count=len(linked_evidence)-direct_count-husbandry_count
    part_note=" / ".join(sorted({str(e.get("plant_part_state")) for e in linked_evidence if e.get("plant_part_state")})) or "근거 자료에 부위 정보가 명시되지 않음"
    en_pending=("This plant has a reviewed evidence record. The feeding grade is limited to the evidence scope shown below; it does not imply unlimited feeding." if a else "Evidence review is incomplete. Do not infer safety or unlimited feeding from missing evidence.")
    en_scope=("Reviewed evidence is available. Check source taxon, plant part, directness, and limitations below before applying the result." if a else "Evidence is incomplete; do not transfer safety assumptions across taxa.")
    en_identity="Database names are search references. Confirm the actual plant identity and contamination status before feeding."
    basis=scope_label(a)

    # 1) Decision: name → grade → meaning → why. Nothing else competes with it.
    gradekey="".join(f'<span class="{"on" if grade==x else ""}"><b>{x}</b> {y}</span>' for x,y in (("A","혼합식 활용"),("B","제한적 혼합"),("C","가끔 보조"),("D","급여 제외")))
    decision_html=f'''<section class="card {tone} decision" data-grade="{esc(grade)}" data-verdict="{esc((a or {}).get("verdict") or "none")}" aria-label="급여 판정 · {esc(grade)} {esc(label)}"><div class="decisionlabel">급여 판정 · {esc(basis)}</div><div class="verdictline"><span class="gradeletter" aria-hidden="true">{esc(grade)}</span><div class="verdict">{esc(grade+" · "+label if grade in "ABCD" else label)}</div></div><p class="meaning">{esc(meaning)}</p><p class="decisionwhy ko-evidence"><b>왜 이렇게 판정했나</b>{esc(summary)}</p><p class="en-evidence" hidden>{esc(en_pending)}</p><div class="gradekey" aria-label="급여 등급 안내">{gradekey}</div></section>'''

    # 2) Practical reading (only when there is a representative assessment).
    practical_html=(f'''<section class="card practical"><h2>급여할 때 확인할 핵심</h2><div class="practicalgrid"><div><b>식단에서의 역할</b><p>{esc(role or "현재 근거 범위 안에서 보조적으로 해석한다.")}</p></div><div><b>근거가 확인한 부위·상태</b><p>{esc(part_note)}</p></div></div></section>''' if a else "")

    # 3) Species-specific notes: visually subordinate; they never replace the default verdict.
    species_rows=[]
    for x in species_notes(rows,a):
        xg=display(x)
        who=x.get("display_group") or x.get("species_group") or x.get("animal_taxon")
        species_rows.append(f'<article class="speciesexception"><div><b>{esc(who)} <i class="small">{esc(x.get("animal_taxon"))}</i></b><span>{esc(xg["grade"]+" · "+xg["label"])}</span></div><p>{esc(x.get("why") or x.get("role") or "해당 종에 대한 별도 판정 근거가 있다.")}</p></article>')
    species_specific_html=(f'<section class="card species-specific"><h2>종별 특이사항</h2><p class="small">특정 종에서만 확인된 근거다. 위의 기본 판정을 바꾸지 않으며, 다른 육지거북 종에도 같다고 가정하지 않는다.</p>{"".join(species_rows)}</section>' if species_rows else "")

    # 4) Scope → identity → limits, stated once in one card.
    scope=(a or {}).get("applicability_note") or {"지중해 Testudo 근거":"지중해 육지거북류(Testudo속)에 관한 근거다. 특정 종·아종을 직접 시험한 정량 자료와는 다르다.","육지거북 일반 근거":"육지거북 일반 근거를 지중해 Testudo에 적용한 판정이다. 지중해 Testudo 종 직접 판정이 아니다.","초식 파충류 일반 근거":"초식 파충류 일반 근거다. 지중해 Testudo 직접 판정이 아니다."}.get(basis,"현재 공개 근거만으로 특정 종까지 좁혀 판단하지 않는다.")
    img=image_by_plant.get(pid)
    photo_html=(f'''<figure class="plantphoto"><img src="{esc(img["image_url"])}" alt="{esc(ko)} ({esc(sci)}) 참고 이미지" loading="lazy" width="112" height="112"><figcaption>정확한 종으로 검증된 참고 이미지<br>사진: <a href="{esc(img["source_url"])}" target="_blank" rel="noopener noreferrer">{esc(img.get("creator"))}</a> · <a href="{esc(img.get("license_url"))}" target="_blank" rel="noopener noreferrer">{esc(img.get("license"))}</a><br>사진만으로 식물 종을 확정하지 않는다.</figcaption></figure>''' if img else "")
    cur=curated_identity.get(pid)
    if identity_warning:
        identity_text="한국 유통명은 검색 후보일 뿐 실제 식물의 종 동정 결과가 아니다. 상품·재배품·야생채집물은 학명을 따로 확인한다."
        cur_html=(f'<p><b>{rich(cur["headline"])}</b></p><ul>{"".join(f"<li>{rich(x)}</li>" for x in cur.get("items",[]))}</ul>' if cur else "")
        identity_html=f'''<div class="identity-alert" data-identity="alert"><h3>⚠ 식물동정 주의</h3><p class="ko-evidence">{esc(identity_text)}</p><p class="en-evidence" hidden>{esc(en_identity)}</p>{cur_html}{photo_html}</div>'''
    else:
        identity_text="이름과 학명은 검색 기준이다. 실제 급여할 식물의 종과 농약·오염 여부는 따로 확인한다."
        identity_html=f'''<div class="identity-note" data-identity="note"><h3>식물동정 확인</h3><p class="ko-evidence">{esc(identity_text)}</p><p class="en-evidence" hidden>{esc(en_identity)}</p>{photo_html}</div>'''
    limits_html="".join(f"<li>{esc(x)}</li>" for x in limits) or "<li>근거 부족 상태에서는 안전하다고 추정하지 않는다.</li><li>단독·무제한 급여 판정으로 해석하지 않는다.</li>"
    scope_html=f'''<section class="card scopecard" id="scope"><h2>판정 범위와 주의사항</h2>{identity_html if identity_warning else ""}<details class="scopefold"><summary>판정의 적용 범위와 확인되지 않은 내용 보기</summary><div class="scopebody"><div><h3>적용 범위</h3><p>{esc(scope)}</p></div>{"" if identity_warning else identity_html}<div><h3>근거로 확인되지 않은 것</h3><div class="ko-evidence"><ul>{limits_html}</ul></div><p class="en-evidence" hidden>{esc(en_scope)}</p><p class="principles">급여량·빈도·장기 안전성은 확인된 근거 범위를 넘어 정하지 않는다. 야생 섭식 기록 ≠ 무제한 급여 · 사람용 영양자료 ≠ 육지거북 독성 한계치 · 근거 부족 ≠ 안전.</p></div></div></details></section>'''

    # 5) Deep evidence: papers first, then specialist sources; each item says what it supports and what it cannot.
    ordered=sorted(linked_evidence,key=lambda e:source_kind(e)[0])
    evidence_cards=[]
    for e in ordered:
        url=e.get("url") or (f'https://doi.org/{e["doi"]}' if e.get("doi") else (f'https://pubmed.ncbi.nlm.nih.gov/{e["pmid"]}/' if e.get("pmid") else ""))
        title_html=esc(e.get("source_title") or e.get("id"))
        source_link=f'<a class="sourceopen" href="{esc(url)}" target="_blank" rel="noopener noreferrer">원문 보기 ↗</a>' if url else ""
        rank,kind=source_kind(e)
        ids=" · ".join(x for x in ((f'DOI {esc(e["doi"])}' if e.get("doi") else ""),(f'PMID {esc(e["pmid"])}' if e.get("pmid") else ""),(esc(e.get("year")) if e.get("year") else "")) if x)
        evidence_cards.append(f'''<article class="evcard"><div class="evhead"><span class="{'paper' if rank==0 else ''}">{kind}</span><span>{esc(directness_ko.get(e.get("directness"),e.get("directness")))}</span><span>{esc(applicability_ko.get(e.get("applicability"),e.get("applicability")))}</span></div><h3>{title_html}</h3><p class="evrole"><b>이 자료의 역할</b> · {esc(evidence_role(e))}</p><dl class="evmeta"><dt>대상 동물</dt><dd>{esc(e.get("animal_taxon"))}</dd><dt>식물</dt><dd><i>{esc(e.get("plant_taxon"))}</i></dd><dt>부위·상태</dt><dd>{esc(e.get("plant_part_state"))}</dd></dl><p><b>이 근거가 지지하는 내용</b><br>{esc(e.get("supports"))}</p><p class="limit"><b>이 근거만으로 말할 수 없는 내용</b><br>{esc(e.get("does_not_support"))}</p>{f'<p class="ids">{ids}</p>' if ids else ''}{source_link}</article>''')
    evidence_cards_html="".join(evidence_cards) or '<p>현재 공개 가능한 개별 근거 레코드가 연결되지 않았다. 따라서 안전성을 추정하지 않는다.</p>'
    papers=sum(1 for e in linked_evidence if source_kind(e)[0]==0)
    summary_chips=f'<div class="evsummary" aria-label="연결된 근거 자료 현황"><span>연결 근거 {len(linked_evidence)}건</span><span>동료심사 논문 {papers}</span><span>직접 {direct_count}</span><span>전문 사육 {husbandry_count}</span><span>간접·맥락 {indirect_count}</span></div><p class="evcountnote">자료 건수는 연결된 출처의 현황이며, 숫자가 많다고 판정의 신뢰도나 안전성이 더 높다는 뜻은 아니다.</p>'

    # Wild feeding records (one place: static wild data + direct Ibera observations).
    wild=wild_by_plant.get(pid,[]); risk=risk_by_plant.get(pid); ib=ibera_by_plant.get(pid,[])
    conflict_html=""
    if wild and risk and (risk.get("signals") or risk.get("publication_blocker")):
        risk_items="".join(f"<li><b>{esc(x.get('type') or '위험 신호')}</b> — {esc(x.get('finding'))}<br><span class=\"small\">{esc(x.get('interpretation'))}</span></li>" for x in risk.get("signals",[]))
        conflict_html=f'''<div class="conflict"><b>⚠ 근거 충돌 또는 안전성 미해결</b><p>야생 섭식 기록이 있지만 독성·항영양성분 또는 다른 동물의 수의학적 위험 신호도 확인됐다. 야생에서 먹는다는 사실만으로 사육 급여 안전성을 확정하지 않는다.</p><ul>{risk_items}</ul><p><b>현재 공개판정의 걸림돌:</b> {esc(risk.get("publication_blocker") or "추가 검토 필요")}</p></div>'''
    wild_cards=[]
    for w in wild:
        wild_cards.append(f'''<article class="evcard wildcard"><div class="evhead"><span>야생 섭식 기록</span><span>{esc(w.get("ibera_applicability") or "적용범위 확인 필요")}</span></div><h3>{esc(w.get("tortoise_taxon") or "대상 거북 미상")} · {esc(w.get("population_region") or "지역 미상")}</h3><dl class="evmeta"><dt>확인 방법</dt><dd>{esc(w.get("study_method") or "미상")}</dd><dt>먹은 부위</dt><dd>{esc(w.get("plant_part") or "미상")}</dd><dt>시기</dt><dd>{esc(w.get("season") or "미상")}</dd><dt>섭식 기록</dt><dd>{esc(w.get("feeding_signal") or "확인")}</dd></dl><p class="limit"><b>이 기록만으로 말할 수 없는 것</b><br>{esc(w.get("limitations") or "야생 섭식 기록만으로 사육 급여량이나 무제한 급여 안전성을 정할 수 없다.")}</p><p class="ids">원자료 식물명 <i>{esc(w.get("plant_taxon_reported"))}</i> · 현재 수용명 <i>{esc(w.get("plant_taxon_accepted"))}</i> · {esc(w.get("source_id"))}</p></article>''')
    for o in ib:
        s=ibera_sources.get(o.get("source_id"),{})
        scope_txt="식물 종까지 일치" if o.get("identity_scope")=="exact_species" else "속 수준 관찰 — 이 식물의 정확한 종을 먹었다는 뜻으로 확대하지 않는다"
        link=f'<a href="{esc(s.get("url"))}" target="_blank" rel="noopener noreferrer">원 연구 확인</a>' if s.get("url") else ""
        wild_cards.append(f'''<article class="evcard wildcard" data-ibera-direct><div class="evhead"><span>이베라 야생 직접 관찰</span><span>{esc(scope_txt)}</span></div><h3><i>{esc(o.get("source_plant"))}</i> · {esc(s.get("location") or "지역 확인 필요")}</h3><dl class="evmeta"><dt>대상</dt><dd><i>{esc(s.get("taxon") or "Testudo graeca ibera")}</i></dd><dt>기간</dt><dd>{esc(s.get("study_period") or "확인 필요")}</dd><dt>섭식 부위</dt><dd>{esc(o.get("observed_part") or "확인 필요")}</dd></dl><p class="ids">{esc(s.get("citation"))} {link}</p></article>''')
    wild_section=(f'''<h3 style="margin-top:18px">야생에서는 실제로 어떻게 먹었나?</h3><p class="small">야생에서 먹었다는 사실은 중요한 근거지만, 사육 급여 비율·매일 급여·무제한 안전성을 뜻하지 않는다.</p>{conflict_html}{"".join(wild_cards)}''' if wild_cards else "")

    deep_html=f'''<section class="card evidence-deep" id="evidence"><div class="sectioneyebrow">더 깊이 보기</div><h2>판정 근거 자세히 보기</h2><p class="ko-evidence small">논문·전문자료를 하나씩, 무엇을 지지하고 무엇을 말할 수 없는지와 함께 보여준다. <b>직접 근거</b>는 해당 육지거북·식물·질문을 직접 다룬 자료, <b>간접 근거</b>는 다른 동물이나 가까운 식물에서 얻은 참고 자료다. 간접 근거만으로 안전성을 확정하지 않는다.</p><p class="en-evidence" hidden>This section explains the evidence behind the conclusion. <b>Direct evidence</b> addresses the target question directly. <b>Indirect evidence</b> comes from other animals or related plants and is used only as context; indirect evidence alone does not establish safety.</p>{summary_chips}<p class="legend"><b>읽는 법</b> · 동료심사 논문과 전문 사육자료는 같은 수준의 근거가 아니다 · 성분 근거는 성분 존재만 보여줄 뿐 급여 안전성을 증명하지 않는다.</p>{evidence_cards_html}{wild_section}</section>'''

    nu=nutrition_by_id.get(pid)
    if nu:
        def nv(key,unit=""):
            v=nu.get(key)
            return "미확인" if v is None else f"{v}{unit}"
        nutrition_body=f'''<div class="nutgrid"><div><b>수분</b><strong>{nv("water_g"," g")}</strong></div><div><b>식이섬유</b><strong>{nv("fiber_g"," g")}</strong></div><div><b>칼슘</b><strong>{nv("calcium_mg"," mg")}</strong></div><div><b>인</b><strong>{nv("phosphorus_mg"," mg")}</strong></div><div><b>Ca:P</b><strong>{nv("calcium_phosphorus_ratio")}</strong></div><div><b>단백질</b><strong>{nv("protein_g"," g")}</strong></div><div><b>칼륨</b><strong>{nv("potassium_mg"," mg")}</strong></div><div><b>비타민 C</b><strong>{nv("vitamin_c_mg"," mg")}</strong></div></div><p class="small">100 g 기준 · {esc(nu.get("basis"))} · {esc(nu.get("food_description"))} · 원자료 <a href="{esc(nu.get("source_url"))}" target="_blank" rel="noopener noreferrer">{esc(nu.get("source_name"))} {esc(nu.get("source_id"))}</a></p>'''
    else:
        nutrition_body='<p class="small">검증된 공식 영양성분 자료가 아직 연결되지 않았다. 자료 부재를 0으로 처리하거나 안전·위험 판정의 근거로 쓰지 않는다.</p>'
    nutrition_html=f'''<section class="card" id="nutrition"><h2>영양성분은 참고자료로 확인하세요</h2><p class="small">사람용 식품성분 자료다. Ca:P·섬유질 등 수치는 독성·항영양성분·식물동정·대상종 근거를 대신하지 않으며, 이 수치만으로 급여 등급을 바꾸지 않는다.</p>{nutrition_body}</section>'''

    related_html="".join(f'<a class="related" href="../{esc(x["id"])}/">{esc(x.get("ko") or x["id"])} →</a>' for x in related_for(p))
    footer_html=f'''<section class="card"><h2>다른 식물도 확인하기</h2><div class="relatedgrid">{related_html}</div><p class="small">같은 과·카테고리로 묶은 탐색 링크다. 식물학적 유사성이 동일한 급여 안전성·영양가·권장도를 뜻하지 않는다.</p><div class="share"><button type="button" onclick="navigator.clipboard.writeText(location.href).then(()=>this.textContent='링크 복사 완료')">링크 복사</button><a href="../../index.html">다른 먹이 검색 →</a></div></section>'''

    alias_html=f'<div class="aliases">다른 이름 · {esc(", ".join(aliases[:6]))}</div>' if aliases else ""
    schema=json.dumps({"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":canonical,"inLanguage":"ko","isPartOf":{"@type":"WebSite","name":"거북밥 DB Korea","url":SITE_URL+"/"}},ensure_ascii=False,separators=(",",":"))
    doc=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="article"><meta property="og:locale" content="ko_KR"><meta property="og:site_name" content="거북밥 DB Korea"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">
<script type="application/ld+json">{schema}</script>
<style>{CSS}</style></head><body>
<a class="skiplink" href="#main-content">본문으로 바로가기</a><header class="detailnav"><a href="../../index.html">← 다른 식물 검색</a><div class="topmeta"><span>거북밥 · 근거 기반 판정</span></div></header><main id="main-content" data-plant-id="{esc(pid)}"><div class="planthead"><h1>{esc(ko)}</h1><div class="scientific"><i>{esc(sci)}</i></div>{alias_html}</div>{decision_html}{practical_html}{species_specific_html}{scope_html}{deep_html}{nutrition_html}{footer_html}<nav class="small" aria-label="breadcrumb"><a href="../../index.html">거북밥 DB</a> › {esc(ko)}</nav></main><script src="../../language-toggle.js?v=20260926-3" defer></script></body></html>'''
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
