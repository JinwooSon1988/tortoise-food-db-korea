#!/usr/bin/env python3
"""Original-source verification ledger for tortoise feeding records, and the site's feeding_pending set.

Run: python scripts/build_feeding_record_verification.py   (writes data/feeding_record_verification_v1.json)

Inputs
- Candidates: evidence rows naming a specific tortoise taxon in the reviewed-plant links (182 plants), the
  evidence-first queue (130 taxa) and the wild feeding records. A candidate is a lead, not a feeding record.
- data/feeding_record_fulltext_extracts_v1.json: records read from the FULL TEXT of an original, with locators.
- CHECKS below: originals opened that do not give a full-text feeding record (abstract only, inaccessible,
  recommendation, secondary citation).

A feeding record counts as verified only when it is in the full-text extracts. A title or abstract never
confirms one. Feeding details (part, mixture, frequency, amount, fresh/dried, preparation) come only from the
extracts; anything the original does not state is null.

feeding_pending (shown inside the catalog's existing grade filter) = a verified full-text feeding record whose
plant name resolves unambiguously to a catalog entry that has no A-D grade. A-D grades are only read.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import public_verdict as pv  # noqa: E402

OUT = ROOT / "data/feeding_record_verification_v1.json"
SITE = ROOT / "data/feeding_pending_site_v1.json"
CHECKED_AT = "2026-10-17"
TORTOISE = re.compile(r"\b(Testudo|Chersina|Centrochelys|Geochelone|Stigmochelys|Chelonoidis|Kinixys|Agrionemys|"
                      r"Astrochelys|Indotestudo|Gopherus|Homopus|Psammobates)\b|Mediterranean (tortoises|Testudo)|"
                      r"Herbivorous tortoises")
# Source types that can describe what tortoises ate or were fed. Plant composition, toxicology on other
# animals and taxonomy databases are context, never feeding records.
FEEDING_TYPES = {"wild_feeding", "academic_study", "peer_reviewed_article", "academic_thesis", "peer_reviewed_field_study",
                 "conference_proceedings", "peer_reviewed_context", "specialist_group_species_account", "expert_husbandry",
                 "specialist_husbandry", "specialist_husbandry_guide", "specialist_veterinary_review", "public_evidence"}
GRADED = ("A", "B", "C", "D")

# Originals opened that do not yield a full-text feeding record. key: (normalised source, plant binomial or "*").
CHECKS = {
    # The owner reviewed an author-uploaded full text (data/ruscus_primary_fulltext_review_20261019.json). It has not
    # been extracted with site and period locators and the pipeline could not reopen it, so it is not counted as confirmed.
    ("10.1655/herpetologica-d-10-00064.1", "*"): {
        "status": "full_text_reviewed_not_extracted", "checked_at": "2026-10-19",
        "opened": "BioOne abstract (2026-10-17); author-uploaded full text on ResearchGate reviewed by the owner (2026-10-19, "
                  "data/ruscus_primary_fulltext_review_20261019.json). Not reopened by this pipeline: publisher copy "
                  "subscriber-only, Unpaywall/OpenAlex closed, ResearchGate and IRIS/CRIS return 403",
        "citation": "Del Vecchio, S., Burke, R. L., Rugiero, L., Capula, M. & Luiselli, L. (2011) Seasonal changes in the "
                    "diet of Testudo hermanni hermanni in central Italy. Herpetologica 67(3):236-249",
        "locator": "Table 1, p. 240 and Table 2, p. 241 (Ruscus aculeatus: fruits, seeds; faecal remains); Discussion, p. 245 "
                   "(leaves eaten in autumn); abstract (flowers and unripe fruit in autumn)",
        "summary": "Faecal tables list Ruscus aculeatus fruits and seeds (Table 1 p. 240; Table 2 p. 241: spring 1/28, autumn "
                   "21/21). The Discussion (p. 245) states the tortoises also ate the leaves in autumn; leaves are not in the "
                   "tables. The abstract mentions flowers and unripe fruit in autumn. Not yet a full-text extract (site and "
                   "period locators missing), so not counted as a confirmed feeding record (see QA-FR-002)."},
    ("10.3854/crm.5.120.eastern.graeca.v1.2023", "*"): {
        "status": "secondary_citation_not_feeding_record", "checked_at": "2026-10-19",
        "opened": "open PDF of the Chelonian Research Monographs species account (OpenAlex OA location), p. 20",
        "citation": "Türkozan, O., Javanbakht, H., Mazanaeva, L. F., Meiri, S. et al. (2023) Testudo graeca Linnaeus 1758 (Eastern "
                    "Subspecies Clades). Chelonian Research Monographs 5(15):120",
        "locator": "p. 20 (diet paragraph citing Iftime and Iftime 2012)",
        "summary": "The diet paragraph summarises Iftime and Iftime (2012): about 500 wild T. g. ibera over 10 years, 96.5% "
                   "herbivorous, young leaves of Taraxacum, Trifolium, Medicago, Sonchus and others. It reports no observation of "
                   "its own; the feeding records belong to Iftime and Iftime 2012 (a full-text extract source)."},
    ("10.1080/21564574.2008.9635573", "*"): {
        "status": "original_does_not_name_taxon", "checked_at": "2026-10-19",
        "opened": "publisher abstract (NISC; same text in the OpenAlex record). Full text not accessible: Taylor & Francis "
                  "and Sabinet return 403, Unpaywall and Semantic Scholar list it as closed (2026-10-19)",
        "citation": "Rouag, R. et al. (2008) Food choice of an Algerian population of the spur-thighed tortoise, Testudo "
                    "graeca. African Journal of Herpetology 57(2):103-113",
        "summary": "The abstract confirms faecal-pellet analysis of 4422 fragments from 20 males, 16 females and 8 juveniles, "
                   "13 dicot and 3 monocot species eaten, vegetative tissue above reproductive tissue, and dicot families "
                   "over 70% of fragments. It names no plant species, so the Cynodon dactylon figures need the full text."},
    ("10.1016/j.jaridenv.2005.06.010", "*"): {
        "status": "original_inaccessible", "checked_at": "2026-10-19",
        "opened": "full text not read (subscription only); only the authors' abstract in the HAL record hal-00184868 (metadata only, no file). Full text not accessible: "
                  "ScienceDirect 403, Unpaywall/OpenAlex/Semantic Scholar closed, the ISTEX link needs a French "
                  "institutional login",
        "citation": "El Mouden, E. H., Slimani, T., Ben Kaddour, K., Lagarde, F., Ouhammou, A. & Bonnet, X. (2006) Testudo "
                    "graeca graeca feeding ecology in an arid and overgrazed zone in Morocco. J. Arid Environ. 64:422-435",
        "summary": "The abstract states that faecal analysis of T. g. graeca in the central Jbilets found five main plant "
                   "species (Leontodon saxatilis, Malva parviflora, Astragalus cruciatus, Medicago hispida, Lotus arenarius) "
                   "making up 70% of identified material and highly preferred. No page, table, plant part or per-species "
                   "share is given, so no record is confirmed from the full text (QA-FR-001)."},
    ("iris.unito.it/retrieve/e27ce42a-913a-2581-e053-d805fe0acbaa/atti_sisvet_2015.pdf", "*"): {
        "status": "original_inaccessible", "checked_at": "2026-10-19",
        "opened": "the PDF URL and the IRIS item and bitstream pages return a bot-check page (403); not bypassed. The IRIS "
                  "OAI-PMH endpoint was reachable, but harvesting sets col_2318_1500038 and com_2318_1500068 (286,118 "
                  "records) found no SISVET 2015 Testudo hermanni foraging record",
        "citation": "SISVET 2015 proceedings (Testudo hermanni foraging, Italy)",
        "summary": "Original not read. The Fabaceae/Plantaginaceae selection summary comes from the evidence registry only."},
    ("archive.britishcheloniagroup.org.uk/caresheets/sulcata", "*"): {
        "status": "recommendation_not_feeding_record", "opened": "British Chelonia Group care sheet, FEEDING > Captive",
        "citation": "British Chelonia Group. Sulcata care sheet (Centrochelys sulcata)",
        "summary": "Lists foods that can be tried in captivity, including watercress. Advice, not a record of feeding."},
    ("archive.britishcheloniagroup.org.uk/caresheets/caremed", "*"): {
        "status": "husbandry_guidance_not_feeding_record", "opened": "British Chelonia Group Mediterranean care sheet",
        "citation": "British Chelonia Group. Mediterranean tortoises care sheet",
        "summary": "General statement that a garden tortoise forages on listed weeds; no observer, place or species record."},
    ("tortoisetrust.org/articles/plantfoods.html", "*"): {
        "status": "recommendation_not_feeding_record", "opened": "Tortoise Trust article",
        "citation": "Tortoise Trust. Plant foods article",
        "summary": "Lamium album and Sisymbrium officinale appear in a keeper's list of foods offered, not as observations."},
    ("10.7717/peerj.8076", "*"): {
        "status": "secondary_citation_not_feeding_record", "opened": "PMC full text (PMC6894431)",
        "citation": "Benitez-Malvido, J. et al. (2019) PeerJ 7:e8076",
        "summary": "Parasite-network study; plants are named only when citing earlier diet studies."},
    ("pmc.ncbi.nlm.nih.gov/articles/pmc6894431", "*"): {
        "status": "secondary_citation_not_feeding_record", "opened": "PMC full text",
        "citation": "Benitez-Malvido, J. et al. (2019) PeerJ 7:e8076",
        "summary": "Parasite-network study; plants are named only when citing earlier diet studies."},
}


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def binomial(s):
    m = re.match(r"^\s*([A-Z][a-z-]+) ([a-z][a-z-]+)(?=$|[^a-z])", str(s or ""))
    return (m.group(1) + " " + m.group(2)).casefold() if m else ""


def norm_source(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"^(https?://)?(www\.)?(dx\.)?(doi\.org/)?", "", s)
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


def catalog_targets(plants, grade):
    """Every catalog entry a full-text record could be linked to: reviewed plants and displayed taxonomy candidates."""
    by_binomial, by_genus = {}, {}
    for p in plants:
        sci = str(p.get("scientific") or "")
        if p.get("identity_status") == "candidate_name" or p["id"] not in grade:
            continue
        if re.search(r"\bspp?\.", sci):
            by_genus.setdefault(sci.split(" ")[0].casefold(), []).append(p["id"])
        elif binomial(sci):
            by_binomial.setdefault(binomial(sci), []).append(p["id"])
    manifest = load("data/taxonomy-shards/index.json")
    candidates = {}
    for s in manifest["shards"]:
        for r in load("data/taxonomy-shards/" + s["file"])["records"]:
            candidates[r["taxon_id"]] = r["scientific_name"]
    return by_binomial, by_genus, candidates


def fulltext_records(extracts, plants, grade):
    by_binomial, by_genus, candidates = catalog_targets(plants, grade)
    known_plant_bins = set(by_binomial)
    sources = {s["source_key"]: s for s in extracts["sources"]}
    out = []
    for r in extracts["records"]:
        s = sources[r["source_key"]]
        b = binomial(r["plant_taxon_reported"])
        links = []
        if r["gbif_key"] is not None:
            for pid in by_binomial.get(b, []):
                links.append({"id": pid, "kind": "reviewed_plant", "match": "exact_species", "grade": grade[pid]})
            for pid in by_genus.get(b.split(" ")[0], []):
                links.append({"id": pid, "kind": "reviewed_plant", "match": "species_within_genus_level_plant", "grade": grade[pid]})
            tid = "gbif:%d" % r["gbif_key"]
            if tid in candidates and b not in known_plant_bins:
                links.append({"id": tid, "kind": "taxonomy_candidate", "match": "gbif_exact_accepted", "grade": None})
        tort = r.get("tortoise") or {"taxon": s["tortoise_taxon"], "ko": s["tortoise_ko"], "en": s["tortoise_en"]}
        site = s["sites"][r["site"]]
        out.append({
            "source_key": r["source_key"], "citation": s["citation"], "url": s["url"], "full_text": s["full_text"],
            "source_type": s["source_type"], "verification_status": "full_text_confirmed",
            "plant_taxon_reported": r["plant_taxon_reported"], "gbif_key": r["gbif_key"], "gbif_match": r["gbif_match"],
            "identity_resolved": r["gbif_key"] is not None,
            "tortoise_taxon": tort["taxon"], "tortoise": {"ko": tort["ko"], "en": tort["en"]},
            "method": s["method"], "method_text": {"ko": s["method_ko"], "en": s["method_en"]},
            "direct_observation": s["direct_observation"], "feeding_fact_confirmed": s["feeding_fact_confirmed"],
            "context": s["context"], "period": s["period"],
            "location": {"ko": site["ko"], "en": site["en"]},
            # Method, table and per-value locators; a value locator already contained in the table locator is dropped.
            "locator": "; ".join(dict.fromkeys([s["method_locator"], site["locator"]] + [
                x for x in ((r.get("observed") or {}).get("locator"), (r.get("plant_part") or {}).get("locator"))
                if x and x not in site["locator"]])),
            "plant_part": None if r["plant_part"] is None else {"ko": r["plant_part"]["ko"], "en": r["plant_part"]["en"]},
            "observed_share": None if r["observed"] is None else {"ko": r["observed"]["ko"], "en": r["observed"]["en"]},
            # Wild diet studies report what was eaten, not how keepers feed; these stay null unless stated.
            "feeding_details": {"mixed_with": None, "feeding_frequency": None, "feeding_amount": None,
                                "fresh_or_dried": None, "preparation": None},
            "links": links,
        })
    return out


def main():
    plants = load("data/plants.json")
    by_id = {p["id"]: p for p in plants}
    grade = {pid: pv.display(pv.representative(rows))["grade"] for pid, rows in pv.by_plant(pv.load_assessments()).items()}
    audit = {r["record_id"]: r for r in load("data/species_evidence_primary_source_audit_v56.json")["records"]}
    wild = {r["id"]: r for r in load("data/wild_feeding_evidence.json")["records"]}
    quarantined = {r["id"] for r in load("data/plant_feeding_evidence_links.json").get("quarantined_wild_records", [])}
    extracts = load("data/feeding_record_fulltext_extracts_v1.json")
    records_ft = fulltext_records(extracts, plants, grade)
    ft_sources = {s["source_key"] for s in extracts["sources"]}

    rows = []
    for item in load("data/plant_feeding_evidence_links.json")["records"]:
        for e in item["evidence"]:
            rows.append(("reviewed_plant_links", item["plant_id"], item.get("scientific_name"), e.get("evidence_id"),
                         e.get("type"), e.get("tortoise_taxon"), e.get("plant_taxon_reported"), e.get("source_id")))
    q = load("data/evidence-first-queue/index.json")
    for s in q["shards"]:
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
        # its text names this plant's genus. It was not reopened here and never confirms a record on its own.
        genus = target.split(" ")[0] if target else ""
        prior = [audit[e] for e in c["evidence_ids"] if e in audit and audit[e]["status"] == "verified_primary"
                 and c["plant_id"] and genus and genus in audit[e]["verification"].lower()]
        ft = [r for r in records_ft if r["source_key"] == src and any(l["id"] == c["plant_id"] for l in r["links"])]
        if ft:
            status, by = "full_text_confirmed", "full-text extract (data/feeding_record_fulltext_extracts_v1.json)"
        elif src in ft_sources:
            status, by = "full_text_read_no_species_record_for_this_plant", "full text read " + CHECKED_AT
        elif chk:
            status, by = chk["status"], "original opened " + chk.get("checked_at", CHECKED_AT)
        elif prior:
            status, by = "prior_primary_audit_only", "species_evidence_primary_source_audit_v56 (not reopened)"
        else:
            status, by = "not_verified", None
        records.append({
            **c,
            "quarantined_wild_record": any(e in quarantined for e in c["evidence_ids"]),
            "plant_match": match,
            "verification_status": status, "verified_by": by,
            "original_opened": (chk or {}).get("opened") or (ft[0]["full_text"] if ft else None),
            "citation": (chk or {}).get("citation") or (ft[0]["citation"] if ft else None),
            "original_locator": ft[0]["locator"] if ft else ((chk or {}).get("locator") or (prior[0]["verification"] if prior else None)),
            "original_summary": (chk or {}).get("summary"),
            "existing_grade": grade.get(c["plant_id"]) if c["plant_id"] else None, "grade_changed": False,
        })

    pending, site_records = set(), {}
    for r in records_ft:
        for l in r["links"]:
            l["feeding_pending"] = bool(r["feeding_fact_confirmed"] and r["identity_resolved"] and l["grade"] not in GRADED)
            if l["feeding_pending"]:
                pending.add(l["id"])
                site_records.setdefault(l["id"], []).append({k: r[k] for k in (
                    "plant_taxon_reported", "tortoise", "method_text", "direct_observation", "location", "period",
                    "plant_part", "observed_share", "feeding_details", "citation", "url", "locator")})

    statuses = {}
    for r in records:
        statuses[r["verification_status"]] = statuses.get(r["verification_status"], 0) + 1
    counts = {
        "candidates": len(records),
        "candidates_by_status": dict(sorted(statuses.items())),
        "full_text_sources_read": len(extracts["sources"]),
        "verified_feeding_records_full_text": sum(r["feeding_fact_confirmed"] for r in records_ft),
        "verified_records_identity_resolved": sum(r["feeding_fact_confirmed"] and r["identity_resolved"] for r in records_ft),
        "verified_records_on_graded_plants": sum(any(l["kind"] == "reviewed_plant" for l in r["links"]) for r in records_ft),
        "site_feeding_pending": len(pending),
        "unverified_candidates": sum(r["verification_status"] not in ("full_text_confirmed",) for r in records),
    }
    out = {"schema_version": "2.0",
           "scope": "Original-source check of tortoise feeding records. Not a safety verdict; A-D grades are unchanged.",
           "rules": ["A candidate is a lead, not a feeding record.",
                     "A feeding record is verified only from the full text of the original; a title or abstract never confirms it.",
                     "Recommendations in care sheets and citations of other studies are not feeding records.",
                     "Genus-level names never become species records; names with unresolved homonyms are not linked.",
                     "feeding_pending = verified full-text feeding record linked unambiguously to a catalog entry with no A-D grade.",
                     "Feeding details are filled only when the original states them; otherwise null (not reported)."],
           "checked_at": CHECKED_AT, "counts": counts,
           "site_feeding_pending": sorted(pending), "site_feeding_records": dict(sorted(site_records.items())),
           "fulltext_records": records_ft, "records": records}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # The catalog loads only this small file: the pending ids and the records it displays for them.
    SITE.write_text(json.dumps({"schema_version": "1.0", "source": "data/feeding_record_verification_v1.json",
                                "scope": out["scope"], "site_feeding_pending": out["site_feeding_pending"],
                                "records": out["site_feeding_records"]}, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
