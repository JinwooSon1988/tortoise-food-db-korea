#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
core=(R/"core-foods/index.html").read_text(encoding="utf-8")
home=(R/"index.html").read_text(encoding="utf-8")
assert "오늘 식단 후보" not in core and "../today/" not in core
assert "근거·영양 비교" not in home
assert "전체 식물 보기" in home
assert "전체 69종 DB" not in home
print("OK: current main has no dead today-meal CTA, duplicate evidence/nutrition navigation, or fixed 69-count copy")
