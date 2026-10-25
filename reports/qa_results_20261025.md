# QA 결과 — 2026-10-25

브랜치 `feat/evidence-engine-coverage-20261025` (기반: `origin/main` 0d2caaf5 + 물냉이 수정 `45f132a6`). 모든 스크립트는 생성기를 CI와 같은 순서로 돌린 깨끗한 트리에서 단독 실행했다(Windows, Python 3.14, `PYTHONUTF8=1`).

## 1. CI 실패 원인 재검증

| 워크플로 | main 0d2caaf5 결과 | 원인 | 이 브랜치 |
|---|---|---|---|
| Sync generated plant pages | 실패 (`Audit generated pages`) | `a08190e9`가 물냉이 판정 카드의 라벨·의미를 "급여 기록 있음 (검증 중)"으로 바꿔 공개 판정 "판정 보류"와 경계 문구가 사라짐 → `audit_verdict_cards`, `qa_verdict_consistency` 실패. 영어 페이지는 종별 근거 0건 → `qa_english_site_v1` 실패 | 통과 (로컬 재현: 수정 전 3개 실패 → 수정 후 7/7 통과) |
| Final commit QA | 실패 | 첫 단계 `Sync workflow must have succeeded`에서 실패, 나머지 단계 skipped → **Sync 실패의 연쇄 결과**(독립 오류 없음) | 그 이후 단계 12개를 로컬 실행: 모두 통과 |
| PR #331 Evidence Layer QA / Guide hub QA | 실패 | PR 기반 브랜치가 main보다 121커밋 뒤처져 `en/index.html`·가이드 허브가 옛 버전(PR 변경과 무관) | PR 파일을 최신 main 위로 옮겨 두 검사 통과 |
| Browser smoke QA (main) | 실패 (10-23) | 테스트 기대값이 소유자 설계 변경(7번째 필터 `feeding_pending`, 미확정 카드 구조 `087e773a`)을 따라가지 못함 | 의도 유지하며 기대값 갱신, 1440×900·390×844 통과 |

## 2. 로컬 실행 결과 (38개 + 브라우저 스모크)

| 스크립트 | 종료코드 | 마지막 출력 |
|---|---|---|
| `audit_plant_integrity` | 0 | PASS: plant ids, detail pages, sitemap URLs and canonicals are consistent |
| `audit_verdict_cards` | 0 | PASS: 182 non-candidate verdict cards follow safety invariants; 0 candidates withheld; canonical registry data/public_assessments.json |
| `audit_plant_detail_v56` | 0 | plant detail v5.6 contract OK for 182 pages; 132 verified images |
| `qa_verdict_consistency` | 0 | PASS: home (verdict-core.js) and 182 detail pages agree on every canonical verdict; grades {'A': 8, 'B': 32, 'C': 104, 'D': 37, '보류': 1} |
| `qa_feeding_cautions_v1` | 0 | OK: 181 plant pages; 706 de-duplicated cautions shown once in the right group, after the verdict and feeding cards |
| `qa_english_site_v1` | 0 | PASS: 182 English plant pages + 7 hubs; ko/en grades, verdicts, nutrition numbers, sources, switches, hreflang and sitemap consistent |
| `qa_detail_language_navigation` | 0 | PASS: 364 Korean and English plant detail pages have accessible icon navigation and functional language links. |
| `qa_variety_card_regeneration_v1` | 0 | OK: all 182 plant pages, the English site, guides and sitemap reproduce byte-identically; timothy photo, mint candidate cards and lettuce va |
| `audit_nutrition_v56` | 0 | Nutrition v5.6 integrity audit OK: 63 plant record(s) |
| `qa_nutrition_hold_list_v1` | 0 | OK: 63 verified + 119 held = 182 public plants; no overlap, no values in hold entries |
| `audit_public_nutrition_variety_cards` | 0 | PASS: lettuce public page includes 5 sourced comparison records and limitations |
| `audit_tortoise_table_links_v1` | 0 | OK: 134 Tortoise Table evidence links use audited URLs |
| `qa_evidence_certainty_labels_v1` | 0 | OK: certainty shown in words on 181 detail pages, hubs, home and catalog; maps identical; research-method explains it |
| `qa_korean_english_fragments_v1` | 0 | PASS: no unintended English fragments in Korean copy (189 pages, 1358 canonical Korean text fields) |
| `qa_bilingual_home_v1` | 0 | PASS: 17 critical home/dynamic UI translations covered |
| `qa_bilingual_catalog_v1` | 0 | PASS: full catalog language toggle and dynamic verdict localization wired |
| `qa_bilingual_plant_detail_v1` | 0 | PASS: generated plant pages inherit bilingual UI contract |
| `audit_site` | 0 | PASS: 382 HTML files, 182 plant pages, JSON and relative links verified |
| `qa_plant_catalog_v1` | 0 | PASS plant catalog: 22765 entries, 952 with feeding evidence, 0 grades; 182 reviewed plants and grades unchanged; search index, shards and s |
| `check_evidence_coverage` | 0 | (JSON report) |
| `test_check_evidence_coverage` | 0 | PASS: coverage counting rule separates consumption, verification tiers and not-eaten references |
| `qa_batch_002_site` | 0 | (JSON report) |
| `qa_batch_004` | 0 | PASS batch 004: 26 records from 16 sources, 50 held; 5 catalog entries supported only by automatic extraction (status evidence_auto_extracte |
| `qa_public_evidence_layer` | 0 | Evidence Layer QA passed: 270 records |
| `qa_assessment_evidence_graph` | 0 | WARNING: orphan public evidence records: tortoise_table_calendula, ttable_campanula_rotundifolia_736, ttrust_sisymbrium_officinale |
| `qa_feeding_record_verification` | 0 | PASS feeding record verification: {"candidates": 91, "candidates_by_status": {"full_text_confirmed": 3, "full_text_read_no_species_record_fo |
| `audit_global_seo_indexability` | 0 | SEO indexability audit: 376 sitemap URLs, 187 English URLs, 0 problems |
| `audit_core_page_assets` | 0 | PASS: 5 critical pages, local script assets, and language/search structure |
| `audit_home_search` | 0 | public evidence-only home search audit: PASS |
| `test_polite_http` | 0 | OK |
| `test_build_evidence_candidates` | 0 | OK |
| `test_promote_reviewed_feeding_evidence` | 0 | OK |
| `test_build_bulk_taxon_catalog` | 0 | OK |
| `test_research_bulk_leads` | 0 | OK |
| `test_report_bulk_leads` | 0 | OK |
| `test_merge_openalex_leads` | 0 | OK |
| `test_discover_incremental_literature` | 0 | OK |
| `test_fulltext_from_bibliography` | 0 | OK |
| `qa_browser_smoke_playwright` | 0 | PASS browser smoke: 1440x900 and 390x844, home/search/detail/all-plants/taxon |

`qa_assessment_evidence_graph`의 WARNING(고아 근거 3건)은 main과 동일한 기존 경고이며 실패가 아니다.

## 3. 테스트 기대값을 바꾼 3건 (의도는 유지)

- `qa_bilingual_catalog_v1`: 100개 단위 페이지네이션(982a17d5)의 영어 문구 `'Page '+currentPage+'/'+pages+' · '+out.length+' of '…` 를 요구.
- `qa_browser_smoke_playwright`: 필터 7개이며 정확한 집합(A/B/C/D/보류/feeding_pending/미확정) 확인; 분류군 카드는 `.decision .verdictlabel`에 "급여 안전성 미확정", A–D 배지가 하나라도 있으면 실패.
- `qa_feeding_record_verification`: 접힌 `<details class="feedrec">` 구조와 `effectiveVerdict(r)` 배타 분류를 확인, 요약 → 상세 → 원문 링크 순서는 계속 요구.

## 4. 사이트 품질 점검 항목

| 항목 | 확인 방법 | 결과 |
|---|---|---|
| 한국어/영어 전환 | qa_detail_language_navigation, qa_bilingual_*, 브라우저 스모크 `&lang=en` | 통과 |
| 식물 검색·상세 | audit_home_search, 브라우저 스모크(홈 검색 → 상세, 전체 목록 → 분류군) | 통과 |
| 근거 유형 표시·대상 거북 종 구분 | qa_public_evidence_layer, qa_feeding_record_verification, 물냉이 종별 근거(Centrochelys sulcata) 한/영 | 통과 |
| 원문 출처 연결 | audit_tortoise_table_links_v1, audit_site(상대 링크), qa_english_site_v1(출처 수 일치) | 통과 |
| 판정과 상세 설명 일치 | audit_verdict_cards, qa_verdict_consistency | 통과 |
| 새로고침·뒤로 가기 | 브라우저 스모크는 `goto`·`wait_for_url`만 검사(뒤로 가기 버튼 동작은 자동 검사 없음) | 부분 확인 |
| 모바일·PC 레이아웃 | 브라우저 스모크 390px(2열 그리드, 잘림 없음)·1440px | 통과 |

## 5. 근거 승격 뒤 재실행 (최종 커밋 기준)

| 검사 | 결과 |
|---|---|
| `qa_plant_catalog_v1` | PASS: 22,765종, 954종 연결, 등급 0, 공개 182종·등급 불변, 검색 색인·샤드·sitemap 일치 |
| `check_evidence_coverage` + `test_check_evidence_coverage` | PASS (참고자료만 있는 식물에 '원문 확인 급여 기록' 상태 0건) |
| `qa_batch_002_site`, `qa_batch_004`, `audit_site`, `qa_public_evidence_layer`, `audit_home_search`, `audit_global_seo_indexability` | 모두 통과 |
| `qa_browser_smoke_playwright` | PASS 1440×900, 390×844 |
| 분류군 상세 `taxon/?id=gbif:3152226`(*Bombax ceiba*) 한/영 | 대상 거북 *Indotestudo elongata*, 출처 Wagle 2026·DOI 표시, "급여 안전성 미확정" 유지, A–D 배지 없음(중립 "—"), JS 오류 0 |

## 6. 수집 엔진 테스트

| 테스트 | 결과 |
|---|---|
| `test_discover_incremental_literature` (9개: 다음 쪽 이어받기, 짧은 쪽 종료, 소진 시 요청 0, 거북 문헌 없는 쪽 종료, 예산 하한, 지난 예산값 무시, 429 냉각, 지표, 옛 상태 호환) | OK |
| `test_fulltext_from_bibliography` (접근 분류, 거북 판정, 요약, 복사된 폴더의 경로 복구) | OK |
| `test_research_bulk_leads`, `test_report_bulk_leads`, `test_merge_openalex_leads` (PR #331) | OK |
| `test_polite_http` (할당량 헤더 기록 추가 후) | OK |
| `run_offline_evidence_pipeline.ps1` PowerShell 전체 실행 2회 | 종료 코드 0 (270초, 36초). 1회차에 PowerShell용 `pdftotext` 부재를 발견해 수정했고, 2회차에 같은 PDF 13건이 재다운로드 없이 변환되었다 |
| PDF 변환 대체 경로 비교 (같은 PDF) | pdftotext 145쪽 = PyMuPDF 145쪽 |
