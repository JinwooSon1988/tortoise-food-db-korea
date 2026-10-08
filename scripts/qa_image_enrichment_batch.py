#!/usr/bin/env python3
"""Validate proposed image enrichment batches without altering published data."""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
import re

REQUIRED = ("plant_id", "scientific", "image_url", "source_url", "creator", "license", "license_url", "identity_scope", "master_scientific", "taxon_evidence", "depicted_part", "part_match", "last_verified_at")
ALLOWED_SCOPE = {"exact_species", "exact_subspecies", "exact_variety"}
ALLOWED_PART = {"match", "partial"}
ALLOWED_LICENSE = {"CC0", "CC0 1.0", "CC BY 4.0", "CC BY-SA 4.0", "CC BY 3.0", "CC BY-SA 3.0", "Public domain"}

def validate(batch, existing):
    errors = []
    seen = set()
    seen_sources = set()
    existing_sources = {x.get('source_url') for x in existing['images']}
    existing_ids = {x["plant_id"] for x in existing["images"]}
    for i, item in enumerate(batch["images"]):
        ident = item.get("plant_id", f"index-{i}")
        for key in REQUIRED:
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{ident}: missing {key}")
        if ident in seen or ident in existing_ids:
            errors.append(f"{ident}: duplicate plant_id")
        seen.add(ident)
        source = item.get("source_url", "")
        if source in seen_sources or source in existing_sources:
            errors.append(f"{ident}: duplicate original photo")
        seen_sources.add(source)
        if not source.startswith("https://commons.wikimedia.org/wiki/File:"):
            errors.append(f"{ident}: original Commons file page required for automatic acceptance")
        sci = item.get("scientific", "")
        scope = item.get("identity_scope")
        if scope == "exact_species" and re.search(r"\\b(?:subsp\\.|var\\.|convar\\.|spp\\.|sp\\.|agg\\.)", sci):
            errors.append(f"{ident}: exact species scope conflicts with scientific rank")
        if scope == "exact_subspecies" and "subsp." not in sci:
            errors.append(f"{ident}: exact subspecies scope lacks subsp.")
        if scope == "exact_variety" and not re.search(r"\\b(?:var\\.|convar\\.|f\\.)", sci):
            errors.append(f"{ident}: exact variety scope lacks rank marker")
        if item.get("license") == "Public domain" and not item.get("public_domain_basis"):
            errors.append(f"{ident}: missing public domain justification")
        if item.get("scientific") != item.get("master_scientific"):
            errors.append(f"{ident}: master scientific mismatch")
        if item.get("identity_scope") not in ALLOWED_SCOPE:
            errors.append(f"{ident}: unverified taxon rank")
        if item.get("part_match") not in ALLOWED_PART:
            errors.append(f"{ident}: unverified plant part")
        if item.get("license") not in ALLOWED_LICENSE:
            errors.append(f"{ident}: license not in accepted list; manual review required")
        for key in ("image_url", "source_url", "license_url"):
            url = item.get(key, "")
            if url and (urlparse(url).scheme != "https" or not urlparse(url).netloc):
                errors.append(f"{ident}: invalid {key}")
        if item.get("review_status") != "approved_after_original_and_visual_review":
            errors.append(f"{ident}: missing explicit final approval")
    return errors

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: qa_image_enrichment_batch.py BATCH.json VERIFIED.json")
    batch = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    existing = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    errors = validate(batch, existing)
    print(json.dumps({"candidates": len(batch["images"]), "passed": len(errors) == 0, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)

if __name__ == "__main__":
    main()
