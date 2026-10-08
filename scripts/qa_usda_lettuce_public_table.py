#!/usr/bin/env python3
"""Verify the public lettuce nutrition table against its source-audited USDA records."""
import json
import re
from pathlib import Path
root = Path(__file__).resolve().parents[1]
data = json.loads((root / "data/usda_lettuce_variety_nutrition_20261008.json").read_text(encoding="utf-8"))
page = (root / "plant/lettuce/index.html").read_text(encoding="utf-8")
assert len(data["records"]) == 5
section = page.split('<section class="card" id="nutrition">', 1)[1].split("</section>", 1)[0]
rows = re.findall(r'<tr><th scope="row"[^>]*>[^<]+</th><td>([^<]+)</td><td>([^<]+)</td><td>([^<]+)</td><td><a href="https://fdc.nal.usda.gov/food-details/(\\d+)/nutrients"', section)
assert len(rows) == 5, f"Expected five visible variety rows, found {len(rows)}"
actual = {int(fdc): (ca, p, fiber) for ca, p, fiber, fdc in rows}
for rec in data["records"]:
    expected = (f'{rec["calcium_mg"]}mg', f'{rec["phosphorus_mg"]}mg', f'{rec["fiber_g"]}g')
    assert actual[rec["fdc_id"]] == expected, f'Nutrition mismatch for {rec["fdc_id"]}'
assert "급여 적합성" in section
print("OK: five public lettuce nutrition rows match USDA verified-source dataset")
