# 거북밥(tortoise-food-db-korea) 작업 인계 — 2026-10-25 (오후 갱신)

사실과 추정을 구분해 적었다. 이전 판(오전)은 기본 clone의 `PROJECT_HANDOFF.prev-20261025.md`에 있다.

## 1. 위치 · 브랜치 · HEAD

| 위치 | 경로 | 브랜치 | 상태 |
|---|---|---|---|
| 원격 main | `origin/main` | — | `0d2caaf5` (확인 시점). **이 세션에서 병합·배포 없음** |
| 작업 worktree | `D:\BABY-PICK-DEV\temp\claude\D--GEOBUKBAP-DEV-tortoise-food-db-korea\2273fbfc-a300-418a-bdfe-2f24ea8e33fe\scratchpad\wt` | `feat/evidence-engine-coverage-20261025` | push됨. 아래 PR 1개로 묶음 |
| 물냉이 수정만 | 위 브랜치의 첫 커밋 | `fix/watercress-verdict-card-20261025` (`45f132a6`) | push됨. 위 브랜치에 포함 |
| 엔진 시험 실행 출력 | `...\2273fbfc-...\scratchpad\engine-run\worker-output\` | — | 워커 출력 **복사본**에서 실행 (원본 무변경) |
| 실행 중 워커 | `D:\GEOBUKBAP-WORKER` (detached `b9561b30`) | — | PID 18464, `run_evidence_worker_loop.ps1 -IntervalMinutes 5`. **건드리지 않음** |
| 옛 브랜치 | `fix/watercress-species-evidence-qa-20261025` (`2e81c319`) | — | main과 충돌. 새 브랜치로 대체되었으니 PR 만들지 말 것 |

`gh`는 로그인되어 있지 않아 PR을 만들지 못했다. 생성 링크:
https://github.com/JinwooSon1988/tortoise-food-db-korea/compare/main...feat/evidence-engine-coverage-20261025?expand=1

## 2. 이번 브랜치의 커밋

1. `45f132a6` 물냉이 판정 카드: "판정 보류" 라벨·의미·경계 문구 유지, 소유자의 종별 문구를 뒤에 붙임. 영어 페이지도 종별 근거 표시 → **Sync 실패 해소**(Final commit QA 실패는 Sync 실패의 연쇄였음을 확인).
2. `6b48d0fc` 집계 의미 분리(`check_evidence_coverage`), 미섭식 행만 있는 91종의 공개 상태를 기존 `reviewed_not_feeding_evidence`로 바꿈.
3. `5775efd5` 수집 엔진: 쿼리별 페이지 커서, 실측 예산, 전문 확보 단계. PR #331 파일을 최신 main 위로 옮김.
4. `0e833c0a`, `b473ffd4` 소유자 설계 변경을 따라가지 못한 테스트 3건 갱신(의도는 유지).
5. `01b99d0a`, `22cc0839` 원문을 읽고 확인한 7행 승격(첫 섭식 기록 2종), 카탈로그와 sitemap-taxa 재생성.
6. (마지막) 보고서 4종과 이 인계 문서.

보고서: `reports/coverage_snapshot_20261025.json`, `reports/evidence_batch_summary_20261025.md`,
`reports/unverified_candidates_20261025.json`, `reports/qa_results_20261025.md`.

## 3. 수집 정체 원인 (실측)

- 커서가 하나뿐이었다(속 17 × 주제 5 = 85개 쿼리, 1쪽만, 쪽당 50건, 주기당 2쿼리). 10-25 06:33 UTC에 커서가 84→1로 한 바퀴 돈 뒤로는 이미 저장한 1쪽을 다시 받아 `new_works 0`이 계속되었다(로그 134개 분석).
- OpenAlex는 키가 없으면 **같은 IP의 모든 사용자가 하루 1,000 크레딧을 공유**하고, 목록 1쪽은 쪽 크기와 관계없이 10크레딧이다(응답 헤더 `X-RateLimit-*`로 실측). 5분 주기 워커 혼자 하루 약 576회를 요청해 예산을 다 쓴다 → 429.
- `search=` 매개변수는 무관한 논문(예: 한국 DMZ 미래 구상 논문)을 끌어왔다. 반면 `title_and_abstract.search`는 낱말을 모두 AND로 묶어 "Geochelone food plants foraging"이 0건이었다. "Geochelone AND (식이 낱말 OR …)"는 1쪽에 136건이 나왔고 거의 모두 해당 주제였다.
- 원문을 한 번도 받지 않았다. 제목·초록만 훑어서는 표에 실린 식물을 찾을 수 없다.
- 새 엔진 결과(복사본에서 실행): 검색 34회로 신규 문헌 873건(거북 관련 824, 공개 PDF 189). 첫 25회만으로 711건이었다. 단건 조회는 0크레딧이다. 마지막 두 번은 공유 예산 하한(200)에서 스스로 멈췄다.
- 전환 전에 고친 실행 환경 결함: PowerShell에는 `pdftotext`가 없어 PDF 변환이 모두 실패했다(→ PyMuPDF·pypdf 대체). 체크포인트 상대 경로는 폴더 복사 후 깨졌다(→ 절대 경로). 수정 후 PowerShell로 파이프라인 전체를 2회 실행해 종료 코드 0을 확인했다.

## 4. 워커 안전 전환 절차 (사용자가 직접 실행)

```powershell
# 0) 사이클이 끝나 잠금 파일이 없을 때만 멈춘다 (있으면 몇 분 뒤 다시 확인)
Test-Path D:\GEOBUKBAP-WORKER\worker-output\pipeline.lock      # False 여야 함
Stop-Process -Id 18464                                           # 루프만 종료 (실행 중 python 없음 확인: Get-Process python)

# 1) 출력과 체크포인트 백업 (삭제·덮어쓰기 없음)
Copy-Item -Recurse D:\GEOBUKBAP-WORKER\worker-output D:\GEOBUKBAP-WORKER\worker-output.bak-20261025

# 2) 워커의 로컬 변경(미추적 스크립트 + 카탈로그 수정본)을 stash로 보존. worker-output은 건드리지 않는다
cd D:\GEOBUKBAP-WORKER
git stash push -u -m "worker local before engine switch 20261025" -- scripts data/plant-catalog
git fetch origin feat/evidence-engine-coverage-20261025
git checkout --detach origin/feat/evidence-engine-coverage-20261025

# 3) 이미 읽은 원문 목록(중복 다운로드 방지)
Set-Content -Encoding utf8 worker-output\known-docs.txt @(
  "D:\BABY-PICK-DEV\temp\claude\D--GEOBUKBAP-DEV-tortoise-food-db-korea\84114f7e-0420-45e4-976f-03b38f9ae989\scratchpad\b4\docs_all.jsonl",
  "D:\BABY-PICK-DEV\temp\claude\D--GEOBUKBAP-DEV-tortoise-food-db-korea\84114f7e-0420-45e4-976f-03b38f9ae989\scratchpad\b4\docs.jsonl")

# 4) (선택) 이 세션의 결과를 이어받기: 문헌 2,194건, 원문 160건, 체크포인트
#    받으면 같은 요청을 다시 보내지 않는다. 받지 않아도 동작은 같으며 다시 수집할 뿐이다
Copy-Item -Force "D:\BABY-PICK-DEV\temp\claude\D--GEOBUKBAP-DEV-tortoise-food-db-korea\2273fbfc-a300-418a-bdfe-2f24ea8e33fe\scratchpad\engine-run\worker-output\worldwide-literature.json" worker-output\
Copy-Item -Force "D:\BABY-PICK-DEV\temp\claude\D--GEOBUKBAP-DEV-tortoise-food-db-korea\2273fbfc-a300-418a-bdfe-2f24ea8e33fe\scratchpad\engine-run\worker-output\discovery-state.json" worker-output\
Copy-Item -Recurse -Force "D:\BABY-PICK-DEV\temp\claude\D--GEOBUKBAP-DEV-tortoise-food-db-korea\2273fbfc-a300-418a-bdfe-2f24ea8e33fe\scratchpad\engine-run\worker-output\fulltext" worker-output\

# 5) (권장) 무료 OpenAlex 키: https://openalex.org/settings/api 에서 직접 발급 → 하루 10,000 크레딧
[Environment]::SetEnvironmentVariable("OPENALEX_API_KEY", "<발급받은 키>", "User")   # 새 PowerShell 창에서 적용

# 6) 한 번 시험 실행 → 결과 확인 → 30분 주기로 재시작 (5분 주기는 공유 예산을 낭비)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_evidence_worker_loop.ps1 -Once
Get-Content worker-output\discovery-metrics.jsonl -Tail 3
Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','.\scripts\run_evidence_worker_loop.ps1','-IntervalMinutes','30'

# 되돌리기: Stop-Process <새 PID>; git checkout --detach b9561b30; git stash pop; worker-output.bak-20261025 복원
```

- 주의: 워커 카탈로그 수정본(`data/plant-catalog` 42개 파일)은 main과 다르다. stash에 남겨 두고 브랜치의 카탈로그를 쓴다. 새 `check_evidence_coverage`는 미섭식 행만 있는 식물에 "원문 확인 급여 기록" 상태가 붙어 있으면 실패하는데, 이 브랜치의 카탈로그는 통과한다.
- 주기마다 기록되는 것: `worker-output/discovery-metrics.jsonl`(요청·오류·신규 문헌·신규 거북 문헌·신규 OA PDF·남은 크레딧·중단 사유), `worker-output/fulltext/access.json`(원문 접근 분류), `download_checkpoint.jsonl`(실패 원인·시도 횟수, 3회 실패 시 포기), `evidence-candidates.json` / `approval-drafts.json`(검토 대기열, `reviewed:false`).

## 5. 수치 (22,765종, 이 브랜치)

연결 954 · 실제 섭식 858 · 원문 확인된 섭식 812 · 참고자료만 91 · 사육 지침 권장만 5 · 근거 없음 21,811.
main에 같은 기준을 적용하면 952 / 856 / 810 / 91 / 5 / 21,813이다. 90% 목표까지 기존 기준으로 19,535종, 원문 확인 섭식 기준으로 19,677종이 남았다.
**이 목록으로는 90%에 도달할 수 없다**(근거와 수치는 `reports/evidence_batch_summary_20261025.md` 1절).

## 6. 소유자 결정이 필요한 것

1. PR 생성과 병합(병합·배포는 하지 않았다).
2. 91종의 공개 상태 문구 변경(같은 라벨 집합 안에서 상태만 바뀜)을 받아들일지.
3. 기대값을 갱신한 테스트 3건(`qa_bilingual_catalog_v1`, `qa_browser_smoke_playwright`, `qa_feeding_record_verification`)을 받아들일지.
4. Wagle 2026의 공개 판정 식물 기록과 독성 보고가 흔한 2종(*Euphorbia tithymaloides*, *Epipremnum aureum*)을 어떻게 다룰지.
5. 카탈로그 밖 식물 13종 추가(카탈로그 확장 범위).
6. OpenAlex·BHL API 키 발급, 유료 원문 158건의 도서관 접근.
7. PR #331: 내용은 이 브랜치로 옮겼다. #331 자체를 닫을지는 소유자가 판단한다.

## 7. 절대 변경·삭제하면 안 되는 데이터 (이전 판에서 이어짐)

- 이전 세션 scratchpad 원자료: `...0252854b...\scratchpad\`(`b2`, `b3`, `corpus`, `eupmc`, `fulltext_cache`, `gbif` 등), `...84114f7e...\scratchpad\b4`, `gbif_copy`.
- 이번 세션 원자료: `...2273fbfc...\scratchpad\engine-run\worker-output\`(문헌 2,194건, 원문 160건, 이전 상태 `worker-output.run2`, 요청 출처 기록 `discovery-requests.jsonl`, `fulltext/requests.jsonl`).
- 저장소: `data/catalog-evidence/*`, `research/evidence-queue/reviewed-*`(결정 기록: 2026-10-23 175건, 2026-10-25 22건), `data/public_assessments.json`, `data/plants.json`.
- 기본 clone의 미추적 파일, `D:\GEOBUKBAP-WORKER\worker-output`, 다른 worktree들.

## 8. 작업 규칙 (이번 세션에서 확인한 것 포함)

- 자동 추출 후보는 원문을 읽기 전에는 승격하지 않는다. 이번에 직접 확인한 섭식 후보 9건 중 7건이 오인이었다(2단 병합, 쪽 넘김 부정어, 2차 인용의 거북 종 오인).
- 원문 우선: 종설이나 주석 서지의 요약보다 원 연구를 쓴다.
- 생성 페이지는 손으로 고치지 않는다. 생성기 순서: `generate_static_pages` → `patch_curated_social_metadata` → `inject_plant_detail_v56` → `generate_guide_hubs` → `generate_en_pages`. 카탈로그: `build_plant_catalog_v1.py --gbif-dir <gbif_copy> --max 22765` → `qa_plant_catalog_v1.py` → `check_evidence_coverage.py`.
- 외부 요청은 `polite_http` 경유(robots.txt, 호스트별 간격, 출처 기록). 출판사 403·로그인 벽·robots 거부는 우회하지 않는다.
