# 공개 배포

이 폴더는 정적 사이트다.

## Cloudflare Pages
빌드 명령 없이 이 폴더 자체를 배포 대상으로 사용한다.
배포 후 HTTPS 공개 URL에서 JSON fetch와 service worker가 정상 작동한다.

## GitHub Pages
배포 주소는 <https://jinwooson1988.github.io/tortoise-food-db-korea/>다. 저장소 루트에 파일을 넣고 Pages source를 배포할 branch의 `/ (root)`로 지정한다.

## 배포 전
python scripts/audit_release.py
python scripts/audit_site.py
결과가 PASS인지 확인한다.

주의: 공식 영양 record가 아직 충분히 채워지지 않았으므로 현재는 베타/검증중 표기를 유지한다.
