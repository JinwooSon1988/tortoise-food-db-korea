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
NO_TRANSFER=("이것만으로 안전성을 결정하지 않음","급여 안전성 자체를 증명하지 않음","이것만으로 급여 안전성을 확정하지 않는다")
# Species-specific sections: current wording (since aa7dfe38) "전체 육지거북에서 동일하게 확인됐다는 뜻은 아니며" replaced
# "다른 육지거북 종에도 같다고 가정하지 않는다"; either states that species findings do not transfer.
SPECIES_NO_TRANSFER=("다른 육지거북 종에도 같다고 가정하지 않는다","전체 육지거북에서 동일하게 확인됐다는 뜻은 아니며","전체 육지거북에서 동일하게 확인됐다는 뜻은 아니다.")
page_checks={
 "no auto transfer from indirect evidence": lambda t: any(x in t for x in NO_TRANSFER),
 "species notes do not transfer": lambda t: ("종별 특이사항" not in t and 'class="card species-specific"' not in t) or any(x in t for x in SPECIES_NO_TRANSFER),
 # Evidence count summary was renamed from class="evsummary" to class="evcountnote" in 143c0e61.
 "species-specific findings are actually rendered": lambda t: ('class="card species-specific"' not in t) or ('class="speciesexception"' in t and 'class="speciesdetail"' in t),
 "evidence counts summarised in evidence section": lambda t: 'class="evcountnote"' in t,
}
failures={k:sorted(pid for pid,t in pages.items() if not f(t)) for k,f in page_checks.items()}
checks={
 "directness tiers labelled": all(x in gen for x in ('"direct":"직접 근거"','"expert_husbandry":"전문 사육 근거"','"related_taxon":"근연 분류군 근거"','"contextual":"맥락 근거"','"composition_only":"성분 근거"')),
 "applicability tiers labelled": all(x in gen for x in ('"mediterranean_testudo"','"tortoise_general":"육지거북 일반"','"herbivorous_reptile_general":"초식 파충류 일반"')),
 **{k:not v for k,v in failures.items()},
}
bad=[k for k,v in checks.items() if not v]
if bad:
 print("FAIL: "+", ".join(f"{k} ({', '.join(failures[k][:10])})" if failures.get(k) else k for k in bad)); sys.exit(1)
print(f"OK: evidence tiers stay explicit on {len(pages)} detail pages without a species selector")
