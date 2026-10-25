#!/usr/bin/env python3
"""Counting rule of check_evidence_coverage: not-eaten rows are never consumption; tiers stay separate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_evidence_coverage import classify  # noqa: E402


def row(t, v="full_text_verified", tortoise="Testudo graeca"):
    return {"type": t, "verification": v, "tortoise": tortoise}


def check():
    assert classify({"feeding_evidence": []})["class"] == "no_evidence"
    # Anacyclus radiatus (El Mouden et al. 2006): present in habitat, not in faeces -> reference only, not eaten.
    c = classify({"feeding_evidence": [row("wild_diet_not_detected")]})
    assert c["class"] == "reference_only" and not c["consumption_verified"] and c["legacy_checked"]
    assert classify({"feeding_evidence": [row("offered_not_eaten"), row("toxicity"), row("nutrition")]})["class"] == "reference_only"
    assert classify({"feeding_evidence": [row("husbandry_recommendation", "guideline_full_text_verified")]})["class"] == "husbandry_recommendation_only"
    c = classify({"feeding_evidence": [row("wild_diet_not_detected"), row("wild_feeding_observation", "abstract_checked")]})
    assert c["class"] == "consumption_supported" and c["tier"] == "abstract_checked" and not c["consumption_verified"]
    # A verified not-detected row must not lift an auto-extracted consumption row to "verified".
    c = classify({"feeding_evidence": [row("wild_diet_not_detected"), row("wild_feeding_observation", "full_text_auto_extracted")]})
    assert c["tier"] == "auto_extracted_not_reviewed" and not c["consumption_verified"]
    c = classify({"feeding_evidence": [row("community_report", "community_report_unverified")]})
    assert c["class"] == "consumption_supported" and c["tier"] == "community_or_video_unverified" and not c["consumption_verified"]
    c = classify({"feeding_evidence": [row("community_report", "community_report_unverified"), row("captive_feeding_record")]})
    assert c["tier"] == "academic_full_text_verified" and c["consumption_verified"]
    assert classify({"feeding_evidence": [row("mystery_type")]})["unknown_types"] == ["mystery_type"]
    print("PASS: coverage counting rule separates consumption, verification tiers and not-eaten references")


if __name__ == "__main__":
    check()
