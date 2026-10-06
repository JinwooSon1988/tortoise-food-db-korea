# 거북밥 DB Korea v5.0-RC1

육지거북 먹이 식물의 급여 판정, 적용 범위와 근거를 확인하는 정적 웹 애플리케이션이다.

## 주요 기능

- 식물 마스터 182종(`data/plants.json`)과 각 식물의 정적 상세 페이지 182개(`plant/{id}/index.html`)
- 급여 판정의 정본은 `data/public_assessments.json`이며, 상세 페이지는 `scripts/generate_static_pages.py`로 생성한다
- 한글명·영문명·학명 검색(자동 교정·식물 동정 없음)
- 전체 식물 표, 핵심 먹이·마트 먹이·야생초·주의 먹이 안내 페이지
- PWA 매니페스트·서비스 워커 파일과 오프라인 안내 페이지

식물 수, 판정 집계와 검토 상태(판정 완료·식물동정 보류·근거 보류)는 `data/coverage.json`에 기록하며 `audit_release.py`가 실제 데이터와 대조한다.
다개체 프로필·식단 기록·백업 기능은 #114에서 제거되었다.

검증 중인 항목은 확정 판정으로 해석하지 않는다.

## 로컬 실행

정적 파일의 `fetch()`와 서비스 워커 동작을 확인하려면 저장소 루트에서 HTTP 서버를 실행한다.

```bash
python -m http.server 8000
```

브라우저에서 <http://localhost:8000/>을 연다.

## 검사

```bash
python scripts/audit_release.py
python scripts/audit_site.py
```

`audit_release.py`는 정본 판정·근거 레지스트리의 참조 무결성과 `coverage.json`의 식물 수·검토 상태 집계를 검사한다.
`audit_site.py`는 HTML 내부 상대경로, JSON 문법, 식물 마스터와 상세 페이지의 1:1 대응(현재 182개), 주요 공개 페이지, canonical URL, sitemap의 식물 URL 일치 및 PWA 필수 파일을 검사한다.

## GitHub Pages

프로젝트 사이트 주소는 <https://jinwooson1988.github.io/tortoise-food-db-korea/>다. Pages 설정에서 배포할 브랜치의 저장소 루트(`/`)를 소스로 선택한다. 이 저장소에 파일을 커밋하는 것만으로 Pages 활성화 또는 실제 공개 배포가 보장되지는 않는다.

배포 절차와 RC1 확인 항목은 [DEPLOY.md](DEPLOY.md)와 [DEPLOY_RC1.md](DEPLOY_RC1.md)를 참고한다.
