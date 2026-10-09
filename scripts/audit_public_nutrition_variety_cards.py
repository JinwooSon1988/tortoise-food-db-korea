#!/usr/bin/env python3
"""Check that public lettuce and mint comparison cards agree with source JSON.

No USDA source archive is needed: this checks rendered page fidelity, not original
USDA provenance. Use audit_usda_*_varieties.py for the independent ZIP audit.
"""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sources = [
    ("mint", "data/usda_mint_variety_candidates_20261009.json", ("calcium_mg", "phosphorus_mg", "fiber_g", "vitamin_c_mg")),
    ("lettuce", "data/plant_nutrition_variety_v1.json", ("fiber_g", "calcium_mg", "phosphorus_mg", "vitamin_c_mg")),
]
for plant, path, fields in sources:
    data = json.loads((root / path).read_text(encoding="utf-8"))
    html = (root / "plant" / plant / "index.html").read_text(encoding="utf-8")
    assert '검증된 영양자료 없음' in html, f"{plant}: missing master-data warning"
    assert "육지거북 급여 안전성" in html, f"{plant}: missing safety limitation"
    for record in data["records"]:
        assert record["source_url"] in html, f"{plant}: missing USDA source link {record['fdc_id']}"
        assert str(record["fdc_id"]) in record["source_url"]
        for field in fields:
            suffix = "mg" if field.endswith("_mg") else "g"
            assert f'{record[field]}{suffix}' in html, f"{plant}: missing {record['fdc_id']} {field}={record[field]}"
    print(f"PASS: {plant} public page includes {len(data['records'])} sourced comparison records and limitations")
