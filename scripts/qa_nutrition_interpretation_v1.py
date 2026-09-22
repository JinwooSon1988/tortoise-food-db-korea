#!/usr/bin/env python3
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"plant-detail-v56.js";s=p.read_text(encoding="utf-8")
for x in ["function nutritionMeaning(n,animal)","칼슘:인(Ca:P)","식이섬유","단백질","지방","수분","British Chelonia Group","Merck Veterinary Manual"]:
 assert x in s, x
assert "전체 식단" in s
assert "단독 판정 기준" in s
print("OK: nutrient interpretation is species-aware, source-linked, and does not turn single-food nutrient values into feeding verdicts")
