# v5.0 RC1 공개 배포 체크리스트
1. 배포 주소: https://jinwooson1988.github.io/tortoise-food-db-korea/
2. sitemap.xml과 canonical URL이 위 프로젝트 사이트 주소를 사용하는지 확인
3. `python scripts/audit_site.py`로 정적 경로와 배포 URL 검사
4. HTTPS 정적 호스팅에 전체 폴더 배포
5. 모바일 실제 기기에서 검색/프로필/식단/백업/PWA 설치 smoke test
6. 네이버 서치어드바이저 및 검색엔진 sitemap 등록
7. 공개 후 404/검색어/식물 상세 유입을 기준으로 개선

RC1은 배포 가능한 구조 후보이며 실제 공개 URL의 네트워크·브라우저 QA는 배포 후 별도 수행한다.
