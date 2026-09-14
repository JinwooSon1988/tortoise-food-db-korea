# Inline evidence drawer design

`/today/`에서 후보와 자동 조합의 판정 근거를 페이지 이동 없이 검토할 수 있도록 하는 UX 규칙이다.

- drawer는 새로운 판정을 계산하지 않는다.
- `data/assessments.json`의 현재 종별 assessment만 표시한다.
- 표시 항목: 공개 판정, 신뢰도, `why`, `applicability_note`, 주요 제한사항.
- `limits`는 최대 3개까지만 인라인 표시하고 전체 출처·세부사항은 식물 상세페이지로 연결한다.
- 근거가 비어 있으면 내용을 추론해 채우지 않고 `공개 설명 없음`으로 표시한다.
- drawer는 급여량·배합률·영양완전성·건강효과를 생성하지 않는다.
