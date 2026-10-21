"""Build data/catalog-evidence/batch-002-*.json from the re-verified agent records (b2/verified.jsonl) and a hand-written
source config (b2_config.json: per source study id, verification, method text, inclusion). Only records whose quote was found
in the saved source text are used; only binomials printed in the source are linkable; everything else is listed as held.
Run: python -X utf8 -I make_batch_002.py <b2 dir> <config> <out json>
"""
import json, re, sys, collections
from pathlib import Path

B2, CFG, OUT = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")), Path(sys.argv[3])
BIN = re.compile(r"[A-Z][a-z-]+ [a-z][a-z-]+")
OK_CHECKS = {"ok", "quote_fragments_found"}
PART = {"leaf": ("잎", "leaves"), "leaves": ("잎", "leaves"), "flower": ("꽃", "flowers"), "flowers": ("꽃", "flowers"),
        "fruit": ("열매", "fruit"), "seed": ("씨앗", "seeds"), "stem": ("줄기", "stems"), "root": ("뿌리", "roots"),
        "pad": ("줄기마디(패드)", "pads (cladodes)"), "cladode": ("줄기마디(패드)", "pads (cladodes)"),
        "whole plant": ("식물 전체", "whole plant"), "aerial parts": ("지상부", "aerial parts"), "bark": ("껍질", "bark"),
        "bulb": ("알뿌리", "bulb"), "shoot": ("새순", "shoots"), "shoots": ("새순", "shoots")}
FIND = {
    "wild_feeding_observation": ("야생 개체가 먹은 식물로 원문 표·본문에 기록됨", "Recorded in the source's table or text as eaten by wild tortoises"),
    "wild_diet_not_detected": ("조사 지역에 있었으나 이 연구의 식이에서 확인되지 않음 (독성·부적합 판정이 아님)",
                               "Present in the study area but not found in the diet in this study (not a toxicity or suitability verdict)"),
    "captive_feeding_record": ("사육·급여 실험 환경에서 먹은 기록", "Recorded as eaten in captivity or a feeding trial"),
    "offered_not_eaten": ("제공했으나 먹지 않음 (독성·부적합 판정이 아님)", "Offered but not eaten (not a toxicity or suitability verdict)"),
    "husbandry_recommendation": ("출처 자료가 급여 식물로 제시함 (출처의 권장이며 이 사이트의 급여 판정이 아님)",
                                 "Listed as a food plant by the source (the source's advice, not this site's feeding verdict)"),
    "nutrition": ("영양 분석값 (분석 부위·기준은 아래 참조)", "Nutrient analysis (see part and basis below)"),
    "toxicity": ("독성·위험 관련 기록 (대상 동물·조건은 아래 참조)", "Toxicity or risk record (see test animal and conditions below)"),
    "community_report": ("사육자·커뮤니티 게시글의 경험담 (검증 연구 아님)", "Experience reported in a keeper or community post (not verified research)"),
    "video_observation": ("영상 게시자가 제목·설명에 적은 섭식 내용 (영상 자체를 검증하지 않음)",
                          "Feeding as stated by the uploader in the video title or description (the video itself was not verified)"),
}
OUTCOME = {"ate", "refused", "became_ill", "recommended", "warned_against"}


def ver(src, cfg, typ):
    if typ == "community_report":  # keeper, forum or informant (e.g. hunter) statements stay reports even inside a review
        return "community_report_unverified"
    if typ == "video_observation":
        return "video_observation_unverified"
    if cfg.get("verification"):
        return cfg["verification"]
    return {"zoo_guideline": "guideline_full_text_verified", "government": "guideline_full_text_verified",
            "vet": "guideline_full_text_verified"}.get(src.get("source_class"), "full_text_verified")


def part(p):
    if not p:
        return None
    k = str(p).strip().lower()
    if k in ("unknown", "unstated", "not stated", "n/a", "none", "") or k.startswith("unknown"):
        return None
    if k in PART:
        return {"ko": PART[k][0], "en": PART[k][1]}
    bits = [b.strip() for b in re.split(r"[,/;+]| and ", k) if b.strip()]
    if bits and all(b in PART for b in bits):
        return {"ko": ", ".join(PART[b][0] for b in bits), "en": ", ".join(PART[b][1] for b in bits)}
    return {"ko": str(p), "en": str(p)}  # kept verbatim from the source when not in the vocabulary


def prior_links(root):
    """(study id, printed name, record type) already linked by the repository's earlier evidence files, so that a study read
    again in this batch (e.g. the same species account or thesis) does not add the same plant twice."""
    out = set()
    ext = json.loads((root / "data/feeding_record_fulltext_extracts_v1.json").read_text(encoding="utf-8"))
    out.update((r["source_key"], r["plant_taxon_reported"], "wild_feeding_observation") for r in ext["records"])
    for key, names in ext["species_in_full_text_not_in_catalog"].items():
        if isinstance(names, list):
            out.update((key, n, "wild_feeding_observation") for n in names)
    for f in [root / "data/catalog_feeding_evidence_fulltext_20261020.json"] + sorted((root / "data/catalog-evidence").glob("batch-*.json")):
        if f.resolve() == OUT.resolve():
            continue
        d = json.loads(f.read_text(encoding="utf-8")); st = {s["source_key"]: s.get("study_id") or s["source_key"] for s in d["sources"]}
        out.update((st[r["source_key"]], r["reported_name"], r["type"]) for r in d["records"])
    return out


PRIOR = prior_links(OUT.resolve().parents[2])
srcs = {}
for f in B2.glob("*/sources.jsonl"):
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.strip():
            s = json.loads(line); srcs[(f.parent.name, s["source_id"])] = s
records, held, seen, used, excluded, prior_only = [], [], set(), collections.OrderedDict(), {}, {}
stats = collections.Counter()
for line in (B2 / "verified.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    key = (r["folder"], r["source_id"]); s = srcs.get(key) or {}
    cfg = CFG["sources"].get(r["source_id"], {})
    if cfg.get("exclude"):
        stats["source_excluded"] += 1
        excluded.setdefault(r["source_id"], {"source_key": r["source_id"], "citation": s.get("citation"), "url": s.get("url"),
                                             "reason": cfg.get("exclude_reason") or "duplicate of a source already used"})
        continue
    printed = (r.get("plant_name_expanded") or r.get("plant_reported") or "").strip()
    ab = re.fullmatch(r"[A-Z]\. [a-z-]+ \(([A-Z][a-z-]+ [a-z-]+)\)", printed)  # "A. minus (Alyssum minus)": genus abbreviated in the table
    if ab:
        printed = ab.group(1)
    name = CFG.get("ocr_corrections", {}).get(printed, printed)
    m = re.match(r"([A-Z][a-z-]+) ([a-z][a-z-]+)(?![\w-])", name)  # drop the authority printed after the binomial (not a word cut at an accent)
    if m and m.group(2) not in ("x",):
        name = m.group(0)
    typ = {"community_report": "community_report", "video_observation": "video_observation"}.get(r["record_type"], r["record_type"])
    typ = cfg.get("type_map", {}).get(typ, typ)
    if (s.get("source_class") == "keeper_community" or cfg.get("verification") == "community_report_unverified")             and typ not in ("community_report", "video_observation"):
        typ = "community_report"
    manual = "|".join((r["source_id"], name, r["record_type"])) in CFG.get("manual_ok", [])
    ok_check = r["check"] in OK_CHECKS or (r["check"] == "name_not_in_quote" and (name in CFG.get("ocr_ok", []) or manual))
    reason = None
    if name in CFG.get("hold_names", {}):
        reason = CFG["hold_names"][name]
    elif not ok_check:
        reason = "quote_not_verified_in_saved_text"
    elif name in CFG.get("common_names", []):
        reason = "identification_common_name_only"
    elif not BIN.fullmatch(name) or name.split()[1] in ("sp", "spp", "cf", "aff"):
        reason = "no_species_level_scientific_name"
    elif typ in ("community_report", "video_observation") and r.get("identification", "binomial_in_source") != "binomial_in_source":
        reason = "identification_" + str(r.get("identification"))
    elif typ == "nutrition" and not ((r.get("nutrition") or {}).get("basis") in ("dry_matter", "as_fed", "unstated")):
        reason = "nutrition_without_basis"
    elif typ == "toxicity" and not cfg.get("toxicity", {}).get(name):
        reason = "toxicity_not_reviewed_by_hand"
    elif typ not in FIND:
        reason = "unknown_record_type_" + typ
    if reason:
        stats["held:" + reason] += 1
        held.append({"reported_name": name or r.get("plant_common_reported"), "source_key": r["source_id"], "tortoise": r.get("tortoise"),
                     "reason": reason, "scope": "name" if name in CFG.get("hold_names", {}) else "record"})
        continue
    if cfg.get("skip_names_file") and name in json.loads((Path(sys.argv[2]).parent / cfg["skip_names_file"]).read_text(encoding="utf-8")):
        stats["already_linked_from_same_study"] += 1; continue
    if (cfg.get("study_id") or r["source_id"], name, typ) in PRIOR:
        stats["already_linked_from_same_study"] += 1; prior_only.setdefault(r["source_id"], s); continue
    v = ver(s, cfg, typ)
    p = part(r.get("plant_part"))
    dk = (cfg.get("study_id") or r["source_id"], name, typ, json.dumps(p), r.get("tortoise"))
    if dk in seen:
        stats["duplicate_dropped"] += 1; continue
    seen.add(dk)
    loc = r.get("locator") or ""
    if manual:
        loc += " (the quoted sentence refers to the plant named in the previous sentence; checked by hand on the page image)"
    elif printed in CFG.get("ocr_corrections", {}) or r["check"] == "name_not_in_quote":
        loc += " (OCR text of the source spells the name differently; read as " + name + ")"
    elif r.get("plant_name_expanded") and (r.get("plant_reported") or "").split()[1:2] != name.split()[1:2]:
        loc += " (the source prints '" + r["plant_reported"] + "'; read as " + name + ")"
    x = {"source_key": r["source_id"], "reported_name": name, "tortoise": r.get("tortoise"), "type": typ, "verification": v,
         "context": r.get("context") if r.get("context") in ("wild", "captive", "keeper", "lab") else None, "locator": loc,
         "plant_part": p, "finding": CFG.get("finding_overrides", {}).get("|".join((r["source_id"], name, r["record_type"])))
                                     or {"ko": FIND[typ][0], "en": FIND[typ][1]}}
    if typ in ("community_report", "video_observation"):
        x["identification"] = "binomial_in_source"
        oc = re.match(r"[a-z_]+", str(r.get("outcome") or "").strip().lower().replace(" ", "_"))
        if oc and oc.group(0) in OUTCOME:
            x["outcome"] = oc.group(0)
        if r.get("platform"):
            x["platform"] = r["platform"]
    if typ == "nutrition":
        n = r["nutrition"]; x["nutrition"] = {"basis": n["basis"], "part": part(n.get("part")) or {"ko": "원문 미기재", "en": "not stated in the source"},
                                            "values": {k: v for k, v in (n.get("values") or {}).items() if v is not None}}
    if typ == "toxicity":
        x["toxicity"] = cfg["toxicity"][name]  # bilingual test animal and conditions written by hand from the source
    records.append(x); used[r["source_id"]] = (r["folder"], s, cfg)
    stats["linked_candidate:" + v] += 1

for sid, s in prior_only.items():
    if sid not in used:
        excluded.setdefault(sid, {"source_key": sid, "citation": CFG["sources"].get(sid, {}).get("citation") or s.get("citation"),
                                  "url": CFG["sources"].get(sid, {}).get("url") or s.get("url"),
                                  "reason": "every record repeats a plant already linked from the same study in an earlier evidence file"})
sources = []
for sid, (folder, s, cfg) in used.items():
    sources.append({k: v for k, v in {
        "source_key": sid, "citation": cfg.get("citation") or s.get("citation"), "url": cfg.get("url") or s.get("url"),
        "doi": s.get("doi"), "language": s.get("language"), "source_class": s.get("source_class"),
        "tortoise_taxon": cfg.get("tortoise_taxon") or ", ".join(s.get("tortoise_taxa") or []),
        "context": cfg.get("context") or ("keeper" if s.get("source_class") == "keeper_community" else "wild"),
        "study_id": cfg.get("study_id") or sid, "method": cfg.get("method"), "read": cfg.get("read") or s.get("access"),
        "collected_by": "batch-002 " + folder}.items() if v is not None})
batch = {"schema_version": "1.0", "batch": CFG["batch"], "built": CFG["built"], "corpus": CFG["corpus"], "scope": CFG["scope"],
         "verification_levels": CFG["verification_levels"], "sources": sources, "records": records, "held_not_linked": held, "sources_not_used": list(excluded.values()),
         "reviewed_not_feeding_evidence": CFG.get("reviewed_not_feeding_evidence", [])}
OUT.write_text(json.dumps(batch, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(dict(stats)); print("sources", len(sources), "records", len(records), "held", len(held))
