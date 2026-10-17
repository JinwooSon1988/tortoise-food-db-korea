#!/usr/bin/env python3
"""Original-source verification ledger for tortoise feeding records, and the site's feeding_pending set.

Run: python scripts/build_feeding_record_verification.py   (writes data/feeding_record_verification_v1.json)

Candidates are evidence rows from the reviewed-plant links (182 plants), the evidence-first queue (130 taxa) and
the wild feeding records that name a specific tortoise taxon. A candidate is a lead, not a feeding record.

Verification statuses are taken only from CHECKS (originals opened for this ledger) or from the existing
primary-source audit (data/species_evidence_primary_source_audit_v56.json, status verified_primary; not reopened
here). Everything else stays not_verified. Feeding details (mixture, frequency, amount, plant part, fresh/dried,
cutting) are filled only from CHECKS when the original states them; otherwise they are null.

feeding_pending is assigned only when all hold:
  verified original, an observed feeding fact (not a recommendation), the exact plant species or an accepted
  synonym, and no existing A-D grade (the plant is on hold). A-D grades are never read for change, only for this test.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import public_verdict as pv  # noqa: E402

OUT = ROOT / "data/feeding_record_verification_v1.json"
CHECKED_AT = "2026-10-17"
TORTOISE = re.compile(r"\b(Testudo|Chersina|Centrochelys|Geochelone|Stigmochelys|Chelonoidis|Kinixys|Agrionemys|"
                      r"Astrochelys|Indotestudo|Gopherus|Homopus|Psammobates)\b|Mediterranean (tortoises|Testudo)|"
                      r"Herbivorous tortoises")
# Source types that can describe what tortoises ate or were fed. Plant composition, toxicology on other
# animals and taxonomy databases are context, never feeding records.
FEEDING_TYPES = {"wild_feeding", "academic_study", "peer_reviewed_article", "academic_thesis", "peer_reviewed_field_study",
                 "conference_proceedings", "peer_reviewed_context", "specialist_group_species_account", "expert_husbandry",
                 "specialist_husbandry", "specialist_husbandry_guide", "specialist_veterinary_review", "public_evidence"}

# Originals opened for this ledger. key: (normalised source, plant binomial or "*" for every plant of that source).
# summary is a paraphrase of what the original says; no quotation beyond a few words.
CHECKS = {
    ("uwcscholar.uwc.ac.za/items/de444336-a9f0-4654-99a4-39b8d4ca8bb5", "cynodon dactylon"): {
        "status": "original_confirmed", "opened": "institutional repository record with author abstract",
        "citation": "Joshua, Q. I. (2008) Seasonal effects on the feeding ecology and habitat of Chersina angulata in the "
                    "South Western Cape. PhD thesis, University of the Western Cape. hdl:10566/16869",
        "locator": "Abstract", "observation": "wild_diet_study", "direct_observation": True,
        "summary": "Wild Chersina angulata: Cynodon dactylon was a principal food item in three of four seasons in West "
                   "Coast National Park.",
        "details": {"season": "principal food in 3 of 4 seasons (West Coast National Park)"}},
    ("10.1655/herpetologica-d-10-00064.1", "ruscus aculeatus"): {
        "status": "original_confirmed", "opened": "publisher page (BioOne), abstract only; full text is subscriber-only",
        "citation": "Del Vecchio, S., Burke, R. L., Rugiero, L., Capula, M. & Luiselli, L. (2011) Seasonal changes in the "
                    "diet of Testudo hermanni hermanni in central Italy. Herpetologica 67(3):236-249",
        "locator": "Abstract", "observation": "wild_diet_study", "direct_observation": True,
        "summary": "Wild Testudo hermanni hermanni switched to flowers and unripe fruit of Ruscus aculeatus in autumn as "
                   "these became available.",
        "details": {"plant_part": "flowers and unripe fruit", "season": "autumn"},
        "note": "The abstract does not mention leaves; the stored link lists leaves too. Leaves stay unconfirmed here."},
    ("10.1080/21564574.2008.9635573", "cynodon dactylon"): {
        "status": "original_does_not_name_taxon", "opened": "publisher abstract (NISC); full text not accessible",
        "citation": "Rouag, R. et al. (2008) Food choice of an Algerian population of the spur-thighed tortoise, Testudo "
                    "graeca. African Journal of Herpetology 57(2):103-113",
        "locator": "Abstract", "observation": None, "direct_observation": False,
        "summary": "The abstract names plant families only (Fabaceae, Asteraceae, Primulaceae, Caryophyllaceae); "
                   "Cynodon is not named. The species-level claim needs the full text."},
    ("10.1016/j.jaridenv.2005.06.010", "*"): {
        "status": "original_inaccessible", "opened": "ScienceDirect returned 403; Crossref and Europe PMC carry no abstract",
        "citation": "El Mouden, E. H., Slimani, T., Ben Kaddour, K., Lagarde, F., Ouhammou, A. & Bonnet, X. (2006) Testudo "
                    "graeca graeca feeding ecology in an arid and overgrazed zone in Morocco. J. Arid Environ. 64:422-435",
        "locator": None, "observation": None, "direct_observation": False,
        "summary": "Original not opened. The plant list could not be checked; records stay quarantined."},
    ("archive.britishcheloniagroup.org.uk/caresheets/sulcata", "*"): {
        "status": "recommendation_not_feeding_record", "opened": "British Chelonia Group care sheet, FEEDING > Captive",
        "citation": "British Chelonia Group. Sulcata care sheet (Centrochelys sulcata)",
        "locator": "FEEDING, Captive", "observation": "husbandry_recommendation", "direct_observation": False,
        "summary": "Lists foods that can be tried in captivity (meadow hay, dandelions, plantains, clover, sow thistle, "
                   "watercress, wild mallow, chickweed). This is advice, not a record of feeding."},
}


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def binomial(s):
    m = re.match(r"^\s*([A-Z][a-z-]+) ([a-z][a-z-]+)(?=$|[^a-z])", str(s or ""))
    return (m.group(1) + " " + m.group(2)).casefold() if m else ""


def norm_source(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"^(https?://)?(dx\.)?(doi\.org/)?", "", s)
    s = re.sub(r"^doi:", "", s)
    return s.rstrip("/")


def plant_match(reported, target):
    r = str(reported or "")
    if any(x in r.lower() for x in ("spp.", " sp.", " taxa", "group", "complex", "/", "see linked", "multiple", "grasses")):
        return "genus_or_group"
    b = binomial(r)
    if not b:
        return "not_named"
    return "exact_species" if b == target else "other_name"


def main():
    plants = load("data/plants.json")
    by_id = {p["id"]: p for p in plants}
    assessments = pv.by_plant(pv.load_assessments())
    grade = {pid: pv.display(pv.representative(rows))["grade"] for pid, rows in assessments.items()}
    audit = {r["record_id"]: r for r in load("data/species_evidence_primary_source_audit_v56.json")["records"]}
    wild = {r["id"]: r for r in load("data/wild_feeding_evidence.json")["records"]}
    quarantined = {r["id"] for r in load("data/plant_feeding_evidence_links.json").get("quarantined_wild_records", [])}

    rows = []
    for item in load("data/plant_feeding_evidence_links.json")["records"]:
        for e in item["evidence"]:
            rows.append(("reviewed_plant_links", item["plant_id"], item.get("scientific_name"), e.get("evidence_id"),
                         e.get("type"), e.get("tortoise_taxon"), e.get("plant_taxon_reported"), e.get("source_id")))
    q = load("data/evidence-first-queue/index.json")
    for s in q["shards"] if isinstance(q["shards"], list) else []:
        for r in load("data/evidence-first-queue/" + s["file"])["records"]:
            for m in r["mentions"]:
                rows.append(("evidence_first_queue", r.get("reviewed_plant_id") or r.get("candidate_taxon_id"),
                             r["scientific_name"], m.get("source_id"), m.get("source_type"), m.get("tortoise_taxon_reported"),
                             m.get("scientific_name"), m.get("source_url")))
    for r in wild.values():
        rows.append(("wild_feeding_evidence", r["plant_id"], r["plant_taxon_accepted"], r["id"], "wild_feeding",
                     r["tortoise_taxon"], r["plant_taxon_reported"], r["source_id"]))

    candidates = {}
    for origin, pid, sci, eid, typ, tort, reported, src in rows:
        if typ not in FEEDING_TYPES or not TORTOISE.search(str(tort or "")):
            continue
        target = binomial(sci)
        key = (pid or target, norm_source(src))
        c = candidates.setdefault(key, {"plant_id": pid if pid in by_id else None,
                                        "candidate_taxon": None if pid in by_id else pid,
                                        "plant_scientific_name": (by_id[pid].get("scientific") if pid in by_id else sci),
                                        "plant_taxon_reported": reported, "tortoise_taxon": tort,
                                        "source": src, "source_type": typ, "evidence_ids": [], "found_in": []})
        if eid and eid not in c["evidence_ids"]:
            c["evidence_ids"].append(eid)
        if origin not in c["found_in"]:
            c["found_in"].append(origin)
        if c["source_type"] == "public_evidence" and typ != "public_evidence":
            c["source_type"] = typ
        if plant_match(c["plant_taxon_reported"], target) != "exact_species" and plant_match(reported, target) == "exact_species":
            c["plant_taxon_reported"] = reported

    records = []
    for (pk, src), c in sorted(candidates.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        target = binomial(c["plant_scientific_name"])
        match = plant_match(c["plant_taxon_reported"], target)
        accepted = [wild[e]["plant_taxon_accepted"] for e in c["evidence_ids"] if e in wild]
        if match == "other_name" and accepted and binomial(accepted[0]) == target:
            match = "accepted_synonym"
        if c["plant_id"] is None:
            # Queue rows without a reviewed plant carry extracted text such as "Potentilla and"; the name is not an identity.
            match = "identity_unresolved"
        chk = CHECKS.get((src, target)) or CHECKS.get((src, "*"))
        # An audit entry verifies one taxon in a source, not every plant linked to that source: it counts only when
        # its text names this plant's genus.
        genus = target.split(" ")[0] if target else ""
        prior = [audit[e] for e in c["evidence_ids"] if e in audit and audit[e]["status"] == "verified_primary"
                 and c["plant_id"] and genus and genus in audit[e]["verification"].lower()]
        if chk:
            status, by = chk["status"], "this ledger (original opened " + CHECKED_AT + ")"
        elif prior:
            status, by = "prior_primary_audit_verified", "species_evidence_primary_source_audit_v56 (not reopened)"
        else:
            status, by = "not_verified", None
        direct = bool(chk["direct_observation"]) if chk else (bool(prior) and c["source_type"] in (
            "academic_study", "peer_reviewed_field_study", "wild_feeding", "peer_reviewed_article"))
        verified = status in ("original_confirmed", "prior_primary_audit_verified")
        g = grade.get(c["plant_id"]) if c["plant_id"] else None
        on_hold = c["plant_id"] is not None and g not in ("A", "B", "C", "D")
        exact = match in ("exact_species", "accepted_synonym")
        pending = verified and direct and exact and on_hold
        d = (chk or {}).get("details", {})
        records.append({
            **c,
            "quarantined_wild_record": any(e in quarantined for e in c["evidence_ids"]),
            "plant_match": match,
            "verification_status": status, "verified_by": by,
            "original_opened": (chk or {}).get("opened"), "citation": (chk or {}).get("citation"),
            "original_locator": (chk or {}).get("locator") or (prior[0]["verification"] if prior else None),
            "original_summary": (chk or {}).get("summary"),
            "observation_type": (chk or {}).get("observation"),
            "direct_observation": direct,
            "feeding_details": {k: d.get(k) for k in ("mixed_with", "feeding_frequency", "feeding_amount", "plant_part",
                                                      "fresh_or_dried", "cutting_method", "season")},
            "review_note": (chk or {}).get("note"),
            "existing_grade": g, "grade_changed": False,
            "feeding_record_status": "feeding_pending" if pending else
                                     ("verified_feeding_record" if verified and direct and exact else "assessment_hold"),
        })

    pending = sorted({r["plant_id"] for r in records if r["feeding_record_status"] == "feeding_pending"})
    counts = {
        "candidates": len(records),
        "originals_opened_in_this_ledger": sum(r["verified_by"] is not None and r["verified_by"].startswith("this ledger") for r in records),
        "original_confirmed_in_this_ledger": sum(r["verification_status"] == "original_confirmed" for r in records),
        "prior_primary_audit_verified": sum(r["verification_status"] == "prior_primary_audit_verified" for r in records),
        "original_inaccessible_or_not_naming_taxon": sum(r["verification_status"] in ("original_inaccessible", "original_does_not_name_taxon") for r in records),
        "recommendation_not_feeding_record": sum(r["verification_status"] == "recommendation_not_feeding_record" for r in records),
        "not_verified": sum(r["verification_status"] == "not_verified" for r in records),
        "direct_feeding_verified_exact_species": sum(r["feeding_record_status"] in ("verified_feeding_record", "feeding_pending") for r in records),
        "site_feeding_pending_plants": len(pending),
    }
    out = {"schema_version": "1.0",
           "scope": "Original-source check of tortoise feeding records. Not a safety verdict; A-D grades are unchanged.",
           "rules": ["A candidate is a lead, not a feeding record.",
                     "Only originals actually opened, or the existing verified_primary audit, count as verified.",
                     "Recommendations in care sheets are not feeding records.",
                     "Genus-level or group mentions never become species records.",
                     "feeding_pending = verified observed feeding of the exact species (or accepted synonym) on a plant with no A-D grade.",
                     "Feeding details are filled only when the original states them; otherwise null (not reported)."],
           "checked_at": CHECKED_AT, "counts": counts, "site_feeding_pending": pending, "records": records}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
