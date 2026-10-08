#!/usr/bin/env python3
"""Validate five source-linked responsive lettuce nutrition cards against USDA data."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
records = json.loads((root / "data/usda_lettuce_variety_nutrition_20261008.json").read_text(encoding="utf-8"))["records"]
page = (root / "plant/lettuce/index.html").read_text(encoding="utf-8")
section = page.split('<section class="card" id="nutrition">', 1)[1].split("</section>", 1)[0]
assert len(records) == 5
assert section.count("<article ") == len(records)
for rec in records:
    source = f'https://fdc.nal.usda.gov/food-details/{rec["fdc_id"]}/nutrients'
    assert source in section, f'Missing USDA source {rec["fdc_id"]}'
    block = section.split(f'href="{source}"', 1)[0].rsplit("<article ", 1)[1]
    for val in (f'{rec["calcium_mg"]}mg', f'{rec["phosphorus_mg"]}mg', f'{rec["fiber_g"]}g', f'{rec["ca_p_ratio"]}:1'):
        assert f'<strong>{val}</strong>' in block, f'Mismatch for {rec["fdc_id"]}: {val}'
assert "급여 적합성" in section
assert "grid-template-columns:repeat(auto-fit" in section
print("OK: five responsive lettuce nutrition cards match USDA dataset and source links")
