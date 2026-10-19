#!/usr/bin/env python3
"""Whole-database conflict audit: plant names, tortoise taxa, plant parts, wild/captive context, directness,
safety wording, citations, ledger status, translations and images.

  python scripts/audit_evidence_conflicts.py           # write data/evidence_conflict_audit_20261019.json
  python scripts/audit_evidence_conflicts.py --check   # CI: fail on any error-level finding not in ACCEPTED

The audit reads the canonical files; it never edits them and never changes an A-D grade. Findings are rule
hits for review: an "error" is a contradiction between stored fields; a "review" is wording or strength that a
person has to judge against the original. data/source_access_check_20261019.json (OpenAlex metadata) is used
when present to compare stored titles and years with the DOI record.
"""
import hashlib, json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/evidence_conflict_audit_20261019.json"
DATA_ROOT = ROOT  # the regression tests point this at a mutated copy

# Error-level findings that are known and owned elsewhere; each needs a reason. Anything else fails --check.
ACCEPTED = {
    "R8_title_differs_from_doi_record|teuber_dill_leaf_flavonols_1978":
        "DOI record carries the German original title (Flavonolglykoside der Blätter und Früchte des Dills); same paper.",
    "R8_title_differs_from_doi_record|melo_coriander_leaf_oxalate_2008":
        "Stored DOI resolves to an unrelated bread paper; no matching record found in Crossref or Europe PMC on 2026-10-19. "
        "Owner must supply the correct identifier (see data/evidence_conflict_audit_20261019.json, unresolved).",
}

TORT = re.compile(r"Testudo|Chersina|Centrochelys|Geochelone|Stigmochelys|Chelonoidis|Kinixys|Agrionemys|Astrochelys|"
                  r"Indotestudo|Gopherus|Homopus|Psammobates|tortoise|Tortoise", re.I)
NON_ANIMAL = re.compile(r"^(Plant composition|not_applicable|Not applicable|Plant chemistry.*)$")
# Plant-part vocabulary. Korean longest-first so 미숙과 is not read as 과.
PART_KO = [("뿌리줄기", "rhizome"), ("근경", "rhizome"), ("미숙과", "fruit"), ("꽃잎", "flower"), ("어린잎", "leaf"),
           ("새순", "leaf"), ("열매", "fruit"), ("과실", "fruit"), ("과일", "fruit"), ("종자", "seed"), ("씨앗", "seed"),
           ("뿌리", "root"), ("줄기", "stem"), ("잎", "leaf"), ("꽃", "flower")]
PART_EN = [(r"\brhizomes?\b", "rhizome"), (r"\broots?\b", "root"),
           (r"\bleaf\b|\bleaves\b|\bleafy\b|\bgreens\b|\btops\b|\bfoliage\b|\bcladodes?\b", "leaf"),
           (r"\bflowers?\b|\bpetals?\b|\binflorescences?\b|\bblossoms?\b|\bflorets?\b|\bheads?\b|\bbuds?\b", "flower"),
           (r"\bfruits?\b|\bberr(y|ies)\b|\bgrapes\b|\bpears\b|\bhips\b", "fruit"),
           (r"\bseeds?\b", "seed"), (r"\bstems?\b|\bstalks?\b|\bshoots?\b", "stem")]
GENERIC_PART = re.compile(r"aerial|whole|plant material|as described|as specified|distinctions are preserved|not_applicable|"
                          r"taxonomic identity|culinary herb|mixed", re.I)
NEG_KO = re.compile(r"않|아니|아님|없|못|불가|금지|말아야|말 것|제외")
FEED_KO = re.compile(r"섭식|먹었|먹는|먹은|이용했|이용하고|이용한|채식")
SAFE_KO = re.compile(r"안전(하다|함|한 것으로|성이 확인|성을 확인|성이 입증|성을 입증)")
CAPTIVE_CLAIM_KO = re.compile(r"사육[^.]{0,30}(급여해도 된다|안전하다|적합하다|권장된다)")
TORT_KO = re.compile(r"거북(?!밥)|Testudo|헤르만|그리스육지|설카타")
DIRECT_KO = re.compile(r"직접 (관찰 )?근거(가|이|다|로)|직접 확인")


HANGUL = re.compile(r"[가-힣]")


def load(rel):
    return json.loads((DATA_ROOT / rel).read_text(encoding="utf-8"))


def key(ko):
    # Same key as scripts/i18n_en.py: hash of the exact Korean source text.
    return hashlib.sha1(str(ko).strip().encode("utf-8")).hexdigest()[:16]


def T(strings, text):
    hit = strings.get(key(text)) if HANGUL.search(str(text or "")) else {"en": text}
    return (hit or {}).get("en") or "[[untranslated:%s]]" % key(text)


# Plant names and compounds that contain a part word without naming that part (잎채소 and 당근잎 still mean leaves).
KO_NOT_PART = {"넓은잎질경이": " ", "별꽃": " ", "제비꽃": " ", "꽃집": " ", "화원": " ", "절화": " ", "잎채소": " 잎 ", "당근잎": " 잎 "}


def parts_ko(text):
    found, t = set(), str(text or "")
    for w, rep in KO_NOT_PART.items():
        t = t.replace(w, rep)
    for w, p in PART_KO:
        if w in t:
            found.add(p)
            t = t.replace(w, " ")
    return found


def parts_en(text):
    t = str(text or "")
    return {p for pat, p in PART_EN if re.search(pat, t, re.I)}


def sentences_ko(text):
    return [s.strip() for s in re.split(r"(?<=[.다])\s+", str(text or "")) if s.strip()]


def binomial(s):
    w = re.sub(r"[×x] ", "", str(s or "")).split()
    return " ".join(w[:2]) if len(w) >= 2 and w[1][:1].islower() else (w[0] if w else "")


def audit(root=None):
    global DATA_ROOT
    DATA_ROOT = Path(root or ROOT)
    plants = {p["id"]: p for p in load("data/plants.json")}
    assessments = load("data/public_assessments.json")
    pub = {r["id"]: r for r in load("data/public_evidence_records.json")["records"]}
    links = load("data/plant_feeding_evidence_links.json")
    rev = load("data/reviewed_plant_reverse_evidence_index.json")["records"]
    ledger = load("data/feeding_record_verification_v1.json")["records"]
    images = load("data/verified_plant_images_v56.json")["images"]
    strings = load("data/i18n/en/strings_en.json")
    access_p = DATA_ROOT / "data/source_access_check_20261019.json"
    access = {r["key"]: r for r in json.loads(access_p.read_text(encoding="utf-8"))["records"]} if access_p.exists() else {}

    findings = []

    def hit(rule, severity, ref, detail, **extra):
        findings.append({"rule": rule, "severity": severity, "ref": ref, "detail": detail, **extra})

    # R1 plant identity: evidence taxon vs the plants it is linked to.
    for r in pub.values():
        rt = binomial(r.get("plant_taxon"))
        if not rt or not rt[:1].isupper() or r.get("directness") in ("related_taxon",):
            continue
        for pid in r["plant_ids"]:
            if pid not in plants:
                hit("R1_unknown_plant_id", "error", r["id"], f"plant_id {pid} not in data/plants.json")
                continue
            genus = plants[pid]["scientific"].split()[0]
            if r.get("directness") != "direct":
                continue
            if str(r.get("plant_taxon")).startswith("See linked plant"):
                hit("R1_direct_evidence_placeholder_taxon", "review", r["id"], f"direct evidence linked to {pid} stores no reported plant taxon")
            elif genus not in str(r.get("plant_taxon")):
                hit("R1_direct_evidence_other_genus", "error", r["id"], f"direct evidence on {r.get('plant_taxon')} linked to {pid} ({genus})")

    # R2 cross-file drift of the same evidence row.
    rev_rows = {(i["plant_id"], s.get("id")): s for i in rev for s in i["public_sources"]}
    for item in links["records"]:
        for e in item["evidence"]:
            p = pub.get(e["evidence_id"])
            if not p:
                hit("R2_link_without_public_record", "review", e["evidence_id"], f"{item['plant_id']}: link row has no public evidence record")
                continue
            if e.get("plant_part") != p.get("plant_part_state"):
                hit("R2_part_drift_links_vs_public", "error", e["evidence_id"], f"links: {e.get('plant_part')!r} / public: {p.get('plant_part_state')!r}")
            if e.get("directness") and e.get("directness") != p.get("directness"):
                hit("R2_directness_drift", "error", e["evidence_id"], f"links {e.get('directness')} / public {p.get('directness')}")
            if e.get("tortoise_taxon") != p.get("animal_taxon"):
                hit("R2_animal_taxon_drift", "error", e["evidence_id"], f"links {e.get('tortoise_taxon')!r} / public {p.get('animal_taxon')!r}")
            rv = rev_rows.get((item["plant_id"], e["evidence_id"]))
            if rv is None:
                hit("R2_missing_reverse_index_row", "error", e["evidence_id"], f"{item['plant_id']}: not in reverse index")
            else:
                if rv.get("plant_part_reported") != p.get("plant_part_state"):
                    hit("R2_part_drift_reverse_vs_public", "error", e["evidence_id"], f"reverse: {rv.get('plant_part_reported')!r} / public: {p.get('plant_part_state')!r}")
                if rv.get("supports") != p.get("supports"):
                    hit("R2_supports_drift_reverse_vs_public", "error", e["evidence_id"], "reverse-index supports text differs from public record")

    # R3 directness and animal taxon.
    for r in pub.values():
        animal = str(r.get("animal_taxon") or "")
        if r.get("directness") == "direct" and not TORT.search(animal):
            hit("R3_direct_without_tortoise_taxon", "error", r["id"], f"directness=direct but animal_taxon={animal!r}")
        if r.get("directness") != "direct":
            for s in sentences_ko(r.get("supports")):
                if DIRECT_KO.search(s) and not NEG_KO.search(s):
                    hit("R3_indirect_record_worded_as_direct", "review", r["id"], s[:200])

    # R4 safety / captive wording in evidence and assessments.
    for r in pub.values():
        for s in sentences_ko(r.get("supports")):
            if (SAFE_KO.search(s) or CAPTIVE_CLAIM_KO.search(s)) and not NEG_KO.search(s):
                hit("R4_safety_claim_in_evidence_text", "review", r["id"], s[:200])

    # R5 plant parts claimed as eaten by tortoises in an assessment but absent from every linked tortoise evidence part
    # field. Composition and toxicology records name parts that were analysed, not eaten, so they do not count.
    for a in assessments:
        ev = [pub[e] for e in a["evidence_ids"] if e in pub and TORT.search(str(pub[e].get("animal_taxon") or ""))
              and "not tortoise" not in str(pub[e].get("animal_taxon")).lower()]
        part_fields = [str(x.get("plant_part_state") or "") for x in ev]
        if not part_fields or all(GENERIC_PART.search(f) for f in part_fields if f) and not any(parts_en(f) for f in part_fields):
            continue
        ev_parts = set().union(*(parts_en(f) | parts_ko(f) for f in part_fields))
        negated_in_evidence = set()
        for f in part_fields:
            for pat, p in PART_EN:
                if re.search(r"(?:" + pat + r")[^;.)]{0,20}\bnot reported\b", f, re.I):
                    negated_in_evidence.add(p)
        for text in [a["why"]] + list(a["limits"]):
            for s in sentences_ko(text):
                if not (FEED_KO.search(s) and TORT_KO.search(s.replace("Tortoise Table", "").replace("Tortoise Trust", ""))):
                    continue
                if NEG_KO.search(s):
                    continue
                claimed = parts_ko(s)
                bad = (claimed - ev_parts) | (claimed & negated_in_evidence)
                if bad:
                    hit("R5_assessment_part_not_in_evidence", "error", a["plant_id"],
                        f"parts {sorted(bad)} claimed as eaten; evidence parts {sorted(ev_parts)}", sentence=s[:240])

    # R6 grade strength vs evidence level (reported, never changed here).
    for a in assessments:
        ev = [pub[e] for e in a["evidence_ids"] if e in pub]
        tort = [x for x in ev if TORT.search(str(x.get("animal_taxon") or ""))]
        if a["verdict"] in ("supported_mixed_diet", "limited_mixed_diet") and not tort:
            hit("R6_ab_grade_without_tortoise_evidence", "review", a["plant_id"], f"{a['verdict']} with only non-tortoise evidence")
        if a["species_group"] == "Mediterranean_Testudo" and not any(re.search(r"Testudo|Mediterranean", str(x.get("animal_taxon"))) for x in ev):
            hit("R7_species_group_without_matching_evidence", "review", a["plant_id"], "Mediterranean_Testudo with no Testudo/Mediterranean evidence")
        if a["species_group"] == "Sulcata" and not any("Centrochelys" in str(x.get("animal_taxon")) for x in ev):
            hit("R7_species_group_without_matching_evidence", "review", a["plant_id"], "Sulcata with no Centrochelys evidence")

    # R8 citations: DOI field vs URL, stored title/year vs the DOI record.
    doi_re = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)
    by_doi = defaultdict(list)
    for r in pub.values():
        d = (r.get("doi") or "").strip()
        m = doi_re.search(str(r.get("url") or ""))
        if d and m and m.group(0).lower().rstrip(".") != d.lower().removeprefix("https://doi.org/"):
            hit("R8_doi_field_url_mismatch", "error", r["id"], f"doi {d} / url {r.get('url')}")
        if d or m:
            by_doi[(d or m.group(0)).lower().removeprefix("https://doi.org/").rstrip(".")].append(r)
    for d, rows in by_doi.items():
        acc = (access.get("doi:" + d) or {}).get("openalex") or {}
        if acc.get("lookup") != "ok":
            continue
        for r in rows:
            st, ot = norm_title(r.get("source_title")), norm_title(acc.get("title"))
            if st and ot and overlap(st, ot) < 0.5:
                hit("R8_title_differs_from_doi_record", "error", r["id"], f"stored {r.get('source_title')!r} / DOI record {acc.get('title')!r}")
            if r.get("year") and acc.get("year") and abs(int(str(r["year"])[:4]) - int(acc["year"])) > 1:
                hit("R8_year_differs_from_doi_record", "review", r["id"], f"stored {r['year']} / DOI record {acc['year']}")

    # R9 ledger status vs public wording about the original.
    led_by_ev = defaultdict(list)
    for r in ledger:
        for e in r["evidence_ids"]:
            led_by_ev[e].append(r)
    for eid, rows in led_by_ev.items():
        p = pub.get(eid)
        if not p:
            continue
        for lr in rows:
            st = lr["verification_status"]
            txt = (p.get("supports") or "") + " " + (p.get("plant_part_state") or "")
            if st in ("abstract_only_not_confirmed", "original_inaccessible", "not_verified") and re.search(r"원문 (Table|표|본문)|Table \d|Discussion|p\. ?\d", txt):
                hit("R9_public_cites_original_ledger_unverified", "error", eid, f"ledger {st} but public text cites a locator in the original")

    # R10 translations: plant-part words kept between Korean and English.
    for k, v in strings.items():
        pk, pe = parts_ko(v["ko"]), parts_en(v["en"])
        if pk - pe:
            hit("R10_translation_drops_plant_part", "review", k, f"ko parts {sorted(pk)} / en parts {sorted(pe)}", ko=v["ko"][:160], en=v["en"][:160])
        if ("잎" in v["ko"]) != bool(re.search(r"\bleaf|\bleaves", v["en"], re.I)) and "Ruscus" in v["ko"]:
            hit("R10_ruscus_leaf_wording_mismatch", "error", k, "Korean and English disagree on Ruscus leaves")

    # R11 images.
    for im in images:
        p = plants.get(im["plant_id"])
        if not p:
            hit("R11_image_unknown_plant", "error", im["plant_id"], "image for a plant id not in plants.json")
            continue
        if binomial(im.get("master_scientific")) != binomial(p["scientific"]):
            hit("R11_image_master_name_drift", "error", im["plant_id"], f"image master {im.get('master_scientific')} / plant {p['scientific']}")
        if im.get("part_match") not in ("match", "exact", True):
            hit("R11_image_part_not_matched", "review", im["plant_id"], f"part_match={im.get('part_match')} depicted={im.get('depicted_part')}")
        if im.get("identity_scope") != "exact_species":
            hit("R11_image_not_exact_species", "review", im["plant_id"], f"identity_scope={im.get('identity_scope')}")

    # R12 ledger: confirmed only through a full-text extract; owner-reviewed sources stay below confirmed.
    extract_keys = {s["source_key"] for s in load("data/feeding_record_fulltext_extracts_v1.json")["sources"]}
    for r in ledger:
        if r["verification_status"] == "full_text_confirmed" and r["source"] not in extract_keys and not r.get("original_locator"):
            hit("R12_confirmed_without_extract", "error", r.get("plant_id") or r.get("candidate_taxon"), r["source"])

    # R13 Ruscus regression (QA-FR-002): faecal tables, Discussion and abstract stay distinguished in every surface.
    rp = pub.get("wild_ruscus_aculeatus_thh_italy_2011")
    ra = next((a for a in assessments if a["plant_id"] == "ruscus_aculeatus"), None)
    if rp and ra:
        part = rp.get("plant_part_state") or ""
        for need in ("fruits and seeds", "Table 1, p. 240", "Table 2, p. 241", "leaves (Discussion, p. 245", "flowers and unripe fruit (abstract"):
            if need not in part:
                hit("R13_ruscus_parts_not_distinguished", "error", rp["id"], f"plant_part_state lacks {need!r}")
        for label, text in (("supports", rp.get("supports")), ("why", ra["why"])):
            if not ("잎" in text and "Discussion(p. 245)" in text and "Table 1" in text):
                hit("R13_ruscus_parts_not_distinguished", "error", "ruscus_aculeatus", f"{label} must name the leaf passage and the tables")
            en = T(strings, text)
            if en.startswith("[[untranslated") or not re.search(r"\bleaves\b", en) or "Discussion (p. 245)" not in en:
                hit("R13_ruscus_parts_not_distinguished", "error", "ruscus_aculeatus", f"English {label} lacks the leaf passage")
        if (ra["verdict"], ra["confidence"]) != ("limited_mixed_diet", "B"):
            hit("R13_ruscus_grade_changed", "error", "ruscus_aculeatus", f"{ra['verdict']} {ra['confidence']}")
        for r in ledger:
            if r.get("plant_id") == "ruscus_aculeatus" and r["verification_status"] == "full_text_confirmed" \
                    and "10.1655/herpetologica-d-10-00064.1" not in extract_keys:
                hit("R13_ruscus_ledger_overstated", "error", "ruscus_aculeatus", "confirmed without a full-text extract")

    # R14 one paper, one public record per plant: the same DOI stored under several ids inflates the evidence count.
    for d, rows in by_doi.items():
        seen = defaultdict(list)
        for r in rows:
            for pid in r["plant_ids"]:
                seen[pid].append(r["id"])
        for pid, ids in seen.items():
            if len(ids) > 1:
                hit("R14_duplicate_source_records", "error", ",".join(sorted(ids)), f"{pid}: DOI {d} stored {len(ids)} times")

    # R15 held originals (P1 manifest): a public direct record built on a held source must say so on the page.
    manifest_p = DATA_ROOT / "data/feeding_p1_blocked_claim_manifest_20261018.json"
    held = set()
    if manifest_p.exists():
        for c in json.loads(manifest_p.read_text(encoding="utf-8"))["blocked_claims"]:
            if c.get("status") == "hold":
                held.update(c["evidence_ids"])
    for eid in sorted(held):
        p = pub.get(eid)
        if p and p.get("directness") == "direct" and "원문 확인 보류(P1)" not in (p.get("supports") or ""):
            hit("R15_held_source_shown_as_direct_without_disclosure", "error", eid,
                f"P1-held source is public direct evidence for {p['plant_ids']} without the hold disclosure")

    return findings


def main(check):
    findings = audit()
    errors = [f for f in findings if f["severity"] == "error"]
    unaccepted = [f for f in errors if f"{f['rule']}|{f['ref']}" not in ACCEPTED]
    counts = {"findings": len(findings), "errors": len(errors), "reviews": len(findings) - len(errors),
              "errors_unaccepted": len(unaccepted), "by_rule": {}}
    for f in findings:
        counts["by_rule"][f["rule"]] = counts["by_rule"].get(f["rule"], 0) + 1
    counts["by_rule"] = dict(sorted(counts["by_rule"].items()))
    if check:
        for f in unaccepted[:60]:
            print("ERROR", f["rule"], f["ref"], f["detail"][:200])
        if unaccepted:
            sys.exit(f"evidence conflict audit FAILED: {len(unaccepted)} error-level finding(s)")
        print("PASS evidence conflict audit:", json.dumps(counts, ensure_ascii=False))
        return
    out = {"schema_version": "1.0", "scope": "Rule hits across the canonical data. Errors are contradictions between stored fields; "
           "reviews need a person to judge against the original. Grades are never changed by this audit.",
           "counts": counts, "accepted_errors": ACCEPTED, "findings": findings}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False))


def norm_title(s):
    return set(re.findall(r"[a-z]{4,}", str(s or "").lower()))


def overlap(a, b):
    return len(a & b) / max(1, min(len(a), len(b)))


if __name__ == "__main__":
    main("--check" in sys.argv[1:])
