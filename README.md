# 거북밥 DB Korea v5.0-RC1

한국에서 구할 수 있는 육지거북 먹이의 근거, 검증 상태와 식단 기록을 확인하는 정적 웹 애플리케이션이다.

## 주요 기능

- 식물 마스터 66종과 각 식물의 정적 상세 페이지 66개
- 한글 오타 후보 검색(자동 교정·식물 동정 없음)
- 다개체 프로필, 오늘 식단 비교, 개체별 최근 7일 기록
- 브라우저 로컬 데이터 JSON 백업·복원
- PWA 서비스 워커와 오프라인 안내

기존 식물·영양·근거·사육 적합성 데이터는 RC1 원본을 유지한다. 검증 중인 항목은 확정 판정으로 해석하지 않는다.

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

`audit_site.py`는 HTML 내부 상대경로, JSON 문법, 식물 마스터와 66개 상세 페이지의 대응, 주요 기능 페이지, canonical URL, sitemap 및 PWA 필수 파일을 검사한다.

## GitHub Pages

프로젝트 사이트 주소는 <https://jinwooson1988.github.io/tortoise-food-db-korea/>다. Pages 설정에서 배포할 브랜치의 저장소 루트(`/`)를 소스로 선택한다. 이 저장소에 파일을 커밋하는 것만으로 Pages 활성화 또는 실제 공개 배포가 보장되지는 않는다.

배포 절차와 RC1 확인 항목은 [DEPLOY.md](DEPLOY.md)와 [DEPLOY_RC1.md](DEPLOY_RC1.md)를 참고한다.
