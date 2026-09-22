#!/usr/bin/env python3
from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"index.html").read_text(encoding="utf-8")
assert "근거·영양 비교" not in s
assert '<b>전체 69종 DB</b>' in s
assert '<b>핵심 먹이 데이터</b>' in s
print("OK: duplicate evidence/nutrition navigation card removed; primary 69-plant DB entry remains")
