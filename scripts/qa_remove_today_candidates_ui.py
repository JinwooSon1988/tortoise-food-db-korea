#!/usr/bin/env python3
from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"core-foods/index.html").read_text(encoding="utf-8")
assert "오늘 식단 후보" not in s
assert "../today/" not in s
print("OK: core foods page has no dead today-meal-candidate entry points")
