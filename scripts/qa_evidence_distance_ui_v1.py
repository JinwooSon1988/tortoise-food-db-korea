#!/usr/bin/env python3
"""Evidence tiers stay distinguishable without a species selector.

The retired runtime 'distance' card depended on a selected animal. Its safety intent is now
checked statically: every detail page labels each source's directness and applicability,
explains direct vs indirect evidence, and never lets indirect evidence establish safety.
"""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
gen=(root/"scripts/generate_static_pages.py").read_text(encoding="utf-8")
pages={p.parent.name:p.read_text(encoding="utf-8") for p in (root/"plant").glob("*/index.html")}
checks={
 "directness tiers labelled": all(x in gen for x in ('"direct":"직접 근거"','"expert_husbandry":"전문 사육 근거"','"related_taxon":"근연 분류군 근거"','"contextual":"맥락 근거"','"composition_only":"성분 근거"')),
 "applicability tiers labelled": all(x in gen for x in ('"mediterranean_testudo"','"tortoise_general":"육지거북 일반"','"herbivorous_reptile_general":"초식 파충류 일반"')),
 "no auto transfer from indirect evidence": all(("간접 근거만으로 안전성을 확정하지 않는다" in t or ("<b>간접 근거</b>" in t and "이것만으로 급여 안전성을 확정하지 않는다" in t)) for t in pages.values()),
 "species notes do not transfer": all("다른 육지거북 종에도 같다고 가정하지 않는다" in t for t in pages.values() if "종별 특이사항" in t),
 "evidence counts summarised in evidence section": all('class="evsummary"' in t for t in pages.values()),
}
bad=[k for k,v in checks.items() if not v]
if bad:
 print("FAIL: "+", ".join(bad)); sys.exit(1)
print(f"OK: evidence tiers stay explicit on {len(pages)} detail pages without a species selector")
