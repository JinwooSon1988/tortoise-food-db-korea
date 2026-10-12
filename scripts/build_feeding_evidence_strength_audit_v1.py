#!/usr/bin/env python3
"""Classify the evidence behind every published feeding assessment by how directly it applies.

Reads data/public_assessments.json and data/public_evidence_records.json and writes
data/feeding_evidence_strength_audit_v1.json. Descriptive only: no verdict, grade or confidence is changed here.
Confidence (how sure the published verdict is) and directness (what kind of study the verdict rests on) are
reported as two separate columns and must not be merged.

Evidence classes, strongest first:
  same_taxon_tortoise_study   field/feeding/clinical study of the tortoise taxon the assessment is scoped to
  other_tortoise_study        such a study of a different tortoise taxon (or any one taxon behind a general verdict)
  husbandry_or_expert         specialist tortoise plant databases, husbandry guides, veterinary manuals
  other_animal_study          mammals, fish, insects, cell lines, human exposure
  plant_toxicity_or_chemistry plant toxicology / phytochemistry without an animal feeding context
  composition_or_identity     nutrient composition, taxonomy and identity sources (never feeding evidence)

Usage: python scripts/build_feeding_evidence_strength_audit_v1.py [--check]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "feeding_evidence_strength_audit_v1.json"
ORDER = ["same_taxon_tortoise_study", "other_tortoise_study", "husbandry_or_expert", "other_animal_study",
         "plant_toxicity_or_chemistry", "composition_or_identity"]
TORTOISE = re.compile(r"testudo|tortoise|centrochelys|chersina|geochelone|stigmochelys|chelonoidis|sulcata", re.I)
OTHER_ANIMAL = re.compile(r"bos taurus|cattle|mus musculus|rattus|mammal|cats?\b|ovis|sheep|cyprinus|companion animals|human|cell|larvae|"
                          r"beetle|insect|animals general|hamster", re.I)
STUDY_TYPES = re.compile(r"academic|peer_reviewed|conference|thesis|field_study|species_account", re.I)
EXPERT_TYPES = re.compile(r"specialist|husbandry|veterinary_manual|veterinary_husbandry|expert|regulatory_herbal", re.I)
TOX_TYPES = re.compile(r"toxicol|chemistry", re.I)
IDENTITY_TYPES = re.compile(r"taxonom|botanical|biodiversity|agriculture_database", re.I)
SCOPE_TAXON = {"Mediterranean_Testudo": re.compile(r"testudo|mediterranean", re.I), "Sulcata": re.compile(r"sulcata", re.I)}
NON_SPECIFIC_URL = re.compile(r"colour=all|viewplants/a-z/|viewplants/search/|[?&]searchchoi", re.I)
POSITIVE = {"supported_mixed_diet", "limited_mixed_diet", "supplement_general_evidence", "limited_supplement", "general_reptile_supplement", "limited"}


def classify(ev, scope):
    st, animal, direct = ev.get("source_type") or "", ev.get("animal_taxon") or "", ev.get("directness")
    if direct == "direct" and TORTOISE.search(animal):
        rx = SCOPE_TAXON.get(scope)
        return "same_taxon_tortoise_study" if rx and rx.search(animal) else "other_tortoise_study"
    if OTHER_ANIMAL.search(animal) and not TORTOISE.search(animal):
        return "other_animal_study"
    if EXPERT_TYPES.search(st) and direct in ("contextual", "expert_husbandry", "related_taxon"):
        return "husbandry_or_expert"
    if STUDY_TYPES.search(st) and TORTOISE.search(animal) and direct in ("contextual", "related_taxon"):
        return "other_tortoise_study"
    if TOX_TYPES.search(st):
        return "plant_toxicity_or_chemistry"
    if IDENTITY_TYPES.search(st) or direct == "composition_only" or ev.get("applicability") == "composition_only":
        return "composition_or_identity"
    return "husbandry_or_expert" if TORTOISE.search(animal) else "composition_or_identity"


def build():
    assessments = json.loads((ROOT / "data/public_assessments.json").read_text(encoding="utf-8"))
    evidence = {e["id"]: e for e in json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8"))["records"]}
    plants = {p["id"]: p for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))}
    rows = []
    for a in assessments:
        classes = [{"evidence_id": i, "class": classify(evidence[i], a["species_group"]), "source_type": evidence[i].get("source_type"),
                    "animal_taxon": evidence[i].get("animal_taxon")} for i in a.get("evidence_ids", []) if i in evidence]
        counts = Counter(c["class"] for c in classes)
        strongest = next((c for c in ORDER if counts.get(c)), "none")
        feeding_sources = counts["same_taxon_tortoise_study"] + counts["other_tortoise_study"] + counts["husbandry_or_expert"]
        flags = []
        if not (counts["same_taxon_tortoise_study"] or counts["other_tortoise_study"]):
            flags.append("no_tortoise_study")
        if feeding_sources == 0:
            flags.append("no_tortoise_feeding_source")
            if a["verdict"] in POSITIVE:
                flags.append("positive_verdict_without_tortoise_feeding_source")
        elif feeding_sources == 1 and not counts["same_taxon_tortoise_study"]:
            flags.append("single_tortoise_feeding_source")
        if a["verdict"] == "do_not_feed" and not (feeding_sources or counts["other_animal_study"] or counts["plant_toxicity_or_chemistry"]):
            flags.append("do_not_feed_without_animal_or_expert_source")
        if a["confidence"][0] in "AB" and not (counts["same_taxon_tortoise_study"] or counts["other_tortoise_study"]):
            flags.append("confidence_B_or_higher_without_tortoise_study")
        urls = [evidence[c["evidence_id"]].get("url") for c in classes if evidence[c["evidence_id"]].get("url")]
        if len(urls) != len(set(urls)):
            flags.append("same_source_cited_twice")
        # Tiers: A = nothing about tortoises at all; B = stated confidence outruns the kind of evidence; C = one specialist source only.
        tier = ("A_no_tortoise_feeding_source" if "no_tortoise_feeding_source" in flags else
                "B_confidence_exceeds_directness" if "confidence_B_or_higher_without_tortoise_study" in flags else
                "C_single_specialist_source" if "single_tortoise_feeding_source" in flags else None)
        rows.append({"plant_id": a["plant_id"], "ko": plants.get(a["plant_id"], {}).get("ko"), "species_group": a["species_group"],
                     "verdict": a["verdict"], "confidence": a["confidence"], "strongest_evidence_class": strongest,
                     "evidence_class_counts": {c: counts[c] for c in ORDER if counts.get(c)}, "flags": flags,
                     "weakness_tier": tier, "evidence": classes})
    summary = {
        "assessments": len(rows),
        "by_strongest_evidence_class": dict(Counter(r["strongest_evidence_class"] for r in rows)),
        "flag_counts": dict(Counter(f for r in rows for f in r["flags"])),
        "weakness_tiers": dict(Counter(r["weakness_tier"] or "none" for r in rows)),
        "confidence_by_strongest_class": {c: dict(Counter(r["confidence"] for r in rows if r["strongest_evidence_class"] == c))
                                          for c in ORDER + ["none"] if any(r["strongest_evidence_class"] == c for r in rows)},
    }
    used = Counter(i for a in assessments for i in a.get("evidence_ids", []))
    by_url = {}
    for e in evidence.values():
        by_url.setdefault((e.get("url") or "").rstrip("/").lower(), []).append(e["id"])
    registry_checks = {
        "evidence_records": len(evidence),
        "sources_registered_more_than_once": sorted([{"url": u, "evidence_ids": sorted(ids)} for u, ids in by_url.items() if u and len(ids) > 1],
                                                    key=lambda x: x["url"]),
        "records_not_cited_by_any_assessment": sorted(i for i in evidence if not used[i]),
        "records_pointing_to_a_list_or_search_page": sorted(e["id"] for e in evidence.values() if NON_SPECIFIC_URL.search(e.get("url") or "")),
        "records_without_year": sorted(e["id"] for e in evidence.values() if not e.get("year")),
    }
    return {"schema_version": "1.0",
            "purpose": "Directness of the evidence behind each published feeding assessment. Descriptive only; verdicts, grades and "
                       "confidence values are not changed by this file. Confidence and directness are separate properties.",
            "evidence_classes_strongest_first": ORDER, "summary": summary, "evidence_registry_checks": registry_checks, "assessments": rows}


def main():
    text = json.dumps(build(), ensure_ascii=False, indent=1) + "\n"
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            sys.exit("data/feeding_evidence_strength_audit_v1.json is stale: run scripts/build_feeding_evidence_strength_audit_v1.py")
        print("feeding evidence strength audit is current")
        return
    OUT.write_bytes(text.encode("utf-8"))
    print(json.dumps(build()["summary"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
