# 근거 연결 배치 요약 — 2026-10-25

브랜치 `feat/evidence-engine-coverage-20261025` · 기반 `origin/main` 0d2caaf5 · main 병합·배포 없음.
수치는 모두 이 세션에서 실제로 실행해 얻은 값이다. 상세 수치: `reports/coverage_snapshot_20261025.json`,
미검증 후보: `reports/unverified_candidates_20261025.json`, QA: `reports/qa_results_20261025.md`.

## 1. 결론 먼저

- **90% 목표(20,489종)는 이 방식으로 도달할 수 없다.** 22,765종은 GBIF에서 확인된 식물 종 목록이며(침엽수 `Abies squamata` 등 포함) 육지거북이 먹는다고 기록될 수 있는 종의 집합이 아니다. 이번 배치에서 육지거북 관련 문헌 1,219건을 모았고(신규 824건) 공개 원문 160건을 새로 저장해 기계 판독했다. 그 결과 **카탈로그 안에서 근거가 없던 식물에 대한 실제 섭식 기록 후보는 2건뿐**이었고, 원문을 읽어 보니 2건 모두 섭식이 아니었다(장벽, 회피). 공개 원문 문헌은 이미 기존 배치(4,072건 판독)에서 대부분 소화된 상태다.
- 실질적 증가는 **새 원문 1건(Wagle et al. 2026)의 섭식 선호 표**에서 나왔다: 근거 없던 식물 2종(오크라 *Abelmoschus esculentus*, *Bombax ceiba*)에 첫 섭식 기록이 연결되었다.
- 남은 큰 증가 여지는 **유료·비공개 원문 158건**(가장 큰 다종 식이 연구들 포함)과 **카탈로그 밖 식물**(이번에 원문에서 확인했지만 22,765종 목록에 없어 연결할 수 없는 13종 등)이다. 둘 다 소유자 결정(도서관 접근, 카탈로그 확장)이 필요하다.

## 2. 집계 기준과 변경 전후 (22,765종 전체)

| 구분 | main 0d2caaf5 (새 기준 적용) | 이 브랜치 | 차이 |
|---|---:|---:|---:|
| 1. 자료가 연결된 식물 (기존 "linked") | 952 | 954 | +2 |
| 2. 실제 섭식·급여를 뒷받침하는 식물 | 856 | 858 | +2 |
| 3. 그중 원문 확인된 섭식·급여 기록 보유 | 810 | 812 | +2 |
| 4. 비섭식·미검출·독성·영양 참고자료만 | 91 | 91 | 0 |
| (별도) 사육 지침 권장만 | 5 | 5 | 0 |
| 5. 근거 없음 | 21,813 | 21,811 | −2 |

- 사용자가 제시한 기준 수치(22,765 / 952 / 20,489 / 19,537)는 **기존 "linked" 기준(행이 하나라도 있으면 연결)** 과 정확히 일치했다.
- 새 기준(`scripts/check_evidence_coverage.py`의 `COUNTING_RULE`)에서는 `wild_diet_not_detected`, `offered_not_eaten`, 독성·영양 행은 섭식으로 세지 않는다. 사육 지침 권장(`husbandry_recommendation`)은 관찰된 섭식이 아니어서 따로 센다. 섭식 식물은 가장 높은 검증 단계 하나로 분류한다.
- 섭식 858종의 검증 단계별 분포: 원문 확인 812 · 초록 확인 9 · 자동 추출(사람 미확인) 5 · 미재확인 문헌 단서 6 · 커뮤니티·영상 26. "원문 확인" 집합은 카탈로그 생성기의 `CHECKED_LEVELS`와 같다.
- 90% 목표까지 남은 수: 기존 기준 19,535종, 원문 확인 섭식 기준 19,677종.

### 발견한 의미 오류와 수정

- `Anacyclus radiatus` 등 **91종**은 "서식지에 있었지만 분변에서 검출되지 않음" 같은 행만 있는데도 공개 상태가 `evidence_checked_in_full_text`(화면 문구 "원문으로 확인한 급여 기록 있음")였다.
- 생성기(`build_plant_catalog_v1.research_status`)를 고쳐, 이런 식물은 **기존** 상태 `reviewed_not_feeding_evidence`("거북 문헌에 이름은 나오지만 먹이 기록은 아님")를 받게 했다. 라벨 문구는 바꾸지 않았다.
- 전후: `evidence_checked_in_full_text` 907 → 818, `reviewed_not_feeding_evidence` 4 → 95.
- `qa_plant_catalog_v1`이 같은 규칙을 검사한다. `check_evidence_coverage`는 이런 불일치가 다시 생기면 실패한다.

## 3. 처리 실적

| 단계 | 수 |
|---|---:|
| OpenAlex 검색 요청 (새 엔진, 4회 실행: 2회는 요청 한도, 2회는 공유 예산 하한에서 중단) | 34 (오류 0) |
| 신규 문헌 (OpenAlex 작업 ID 기준) | 873 (1,321 → 2,194) |
| 그중 육지거북 관련 신규 문헌 / 공개 PDF가 있는 것 | 824 / 189 |
| 전체 코퍼스의 육지거북 관련 문헌 (원문 확보 가능 420 · 이미 판독 144 · 초록·메타데이터만 655) | 1,219 |
| 무료 단건 조회 (PMCID·OA PDF 확인, 0 크레딧) | 295 |
| 공개 원문 시도 / 저장 / 영구 실패 | 414 / 160 / 254 |
| 후보 검색 대상 문서 | 2,354 (서지 2,194 + 원문 160) |
| 자동 후보 전체 | 883 |
| — 식물명 단순 언급 | 779 (545종) |
| — 섭식 문맥 후보 (야생 63 / 사육 10) | 73 |
| — 독성·영양 / 미섭식·회피 | 22 / 9 |
| 사람이 원문을 읽고 검토한 후보 | 22 (승인 7, 거부 15) |
| **신규 검증 근거 (원문 확인 후 승격)** | **7행** |
| **신규 연결 식물** | **2종** (*Abelmoschus esculentus*, *Bombax ceiba*) |
| 원문 확인했으나 카탈로그에 없는 식물 | 13종 |
| 소유자 결정으로 넘긴 항목 | 3건 (독성 보고가 흔한 2종, 공개 판정 식물) |
| 원문 확보가 필요한 육지거북 식이 연구 | 158건 |

원문 저장 실패 원인(상위): 로그인 벽·랜딩 페이지 60, robots.txt 거부 43, Wiley 403 33, ScienceDirect 403 10, Brill 403 8, Allen Press 403 6. 우회하지 않았다.

### 신규 검증 근거 7행 (모두 `captive_feeding_record`, 검증 `reviewed_source_record`)

| 식물 | 대상 거북 | 부위 | 원문 위치 | 확인된 내용 | 입증하지 못하는 것 |
|---|---|---|---|---|---|
| *Abelmoschus esculentus* (신규) | *Indotestudo elongata* (사육) | 열매(꼬투리) | Wagle et al. 2026, PDF p.15 Table 18 | 9마리 중 22.22%(2마리)가 먹음 | 안전성·급여량·빈도, 다른 거북 종 |
| *Bombax ceiba* (신규) | *I. elongata* (사육) | 꽃 | 같은 표 | 11.11%(1마리) | 〃 |
| *Psidium guajava* | *I. elongata* | 열매 | 같은 표 | 100% | 〃 |
| *Mangifera indica* | *I. elongata* | 열매 | 같은 표 | 88.88% | 〃 |
| *Cucurbita maxima* | *I. elongata* | 열매 | 같은 표 | 77.77% | 〃 |
| *Ficus racemosa* (원문 표기 "racemose") | *I. elongata* | 열매 | 같은 표 | 66.67% | 〃 |
| *Leucaena leucocephala* | *Chelonoidis carbonarius* (사육) | 여러 부위(원문 미특정) | Rodrigues & Oliveira 2016, *Rodriguésia* 67: 661–666, PDF p.2 서론 | 사육 개체가 여러 부위를 자유롭게 먹는 것을 저자가 관찰 | 부위·양·안전성. 이 종에 대한 기존 기록(다른 연구)은 '제공했으나 먹지 않음'이었다 |

출처: Wagle, R. C. et al. (2026) *Biorhythm, feeding preferences and growth of Indotestudo elongata (Blyth, 1854) in Turtle Rescue and Conservation Centre, Jhapa, Nepal*, https://doi.org/10.31893/wild.2026005. 방법(3.2.2절): 연구자가 50종 이상을 제공했고, 9마리 모두 거부한 항목은 표에서 뺐다.

### 거부한 후보 (대표)

- *Rubus niveus*: 2단 PDF가 합쳐져 생긴 오인. 원문은 "덤불이 거북에게 통과 불가능할 수 있다", 즉 장벽이다.
- *Eryngium ilicifolium*: 쪽 넘김 뒤 문장이 "were actively avoided"로 끝남(회피). 자동 추출이 부정어를 놓친 사례.
- *Synedrella nodiflora*, *Hylodesmum repandum*: 원문은 Travancore 거북(*I. travancorica*)에 대한 2차 인용인데 *I. elongata*로 잘못 붙음.
- *Bromus madritensis*, *Ruscus aculeatus*, *Syagrus flexuosa*: 2차 요약이거나 이미 연결된 원문과 중복.

## 4. 근거 유형별 분포 (카탈로그 행 기준, 이 브랜치)

`data/plant-catalog/index.json` `counts.evidence_by_type`: wild_feeding_observation 1,154 · captive_feeding_record 93 · wild_diet_not_detected 83 · community_report 42 · offered_not_eaten 28 · husbandry_recommendation 8 · nutrition 4 · toxicity 2 · video_observation 2.

## 5. 오류 수

- 수집: OpenAlex 검색 34건 중 오류 0건. 원문 단계 요청 758건(무료 단건 조회 295건 포함) 중 성공 510건, robots.txt 거부 43건(모두 `fulltext/requests.jsonl`에 기록됨).
- 실행 환경 결함 2건을 발견해 고쳤다: PowerShell 워커에는 `pdftotext`가 없어 PDF 변환이 모두 실패했다(→ PyMuPDF·pypdf 대체, 페이지 구분 유지, 저장된 PDF 재사용). 체크포인트에 상대 경로가 저장되어 폴더를 옮기면 문서가 빠졌다(→ 절대 경로 저장, 파일명으로 복구).
- 자동 추출 오인: 직접 검토한 섭식 후보 9건 중 7건이 거부되었다(정밀도 약 22%). **자동 추출만으로 승격하면 안 된다는 근거**다.
- CI: 소유자 설계 변경을 따라가지 못한 테스트 3건과 물냉이 판정 카드 오류를 수정했다(`reports/qa_results_20261025.md`).

## 6. 미완료 항목

1. 원문 확보가 필요한 식이 연구 158건(`unverified_candidates_20261025.json` → `full_text_needed`). 예(서지 기록의 제목·연도): "The diet of the gopher tortoise, Gopherus polyphemus, in a sandhill habitat in central Florida"(1986), "Feeding ecology and seasonal movements of giant tortoises on Aldabra atoll"(1983, doi:10.1007/bf00378221), "Diets and food preferences of two South African tortoises Geochelone pardalis and Psammobates oculifer"(1993), "Diets of Giant Tortoises and Feral Burros on Volcan Alcedo, Galapagos"(1985, doi:10.2307/3801865), "Food Habits and Selective Foraging by the Texas Tortoise (Gopherus berlandieri)"(2011).
2. 미검토 자동 후보 97건(섭식 문맥 포함). 대부분 이미 연결된 식물에 대상 거북 종만 늘리는 후보다.
3. 카탈로그 밖 식물 13종(원문 확인됨): 22,765종 목록 확장은 소유자 결정.
4. 소유자 결정 3건: *Euphorbia tithymaloides*, *Epipremnum aureum*(먹은 기록은 있으나 독성 보고가 흔함), 공개 판정 식물(히비스커스·사과·양배추·오이·토마토·포도·완두)에 대한 Wagle 2026 기록 추가 여부.
5. OpenAlex 키가 없어 하루 예산(공유 IP 1,000 크레딧 = 검색 100회)이 병목이다. 무료 키를 쓰면 하루 10,000 크레딧이다. 사용자 이메일로 키를 신청하는 일은 사용자가 직접 해야 한다.
6. Biodiversity Heritage Library 자료 10건(예: 1983 Volcán Alcedo 거북·당나귀 섭식 생태, "Nutritive quality and mineral content of potential desert tortoise food plants")은 BHL robots.txt가 PDF 경로를 막아 받지 않았다. 허용된 경로는 BHL API(OCR 텍스트)이며 무료 API 키가 필요하다. 키 발급은 사용자 몫이다.
7. 실행 중인 PowerShell 워커(PID 18464)는 건드리지 않았다. 전환 절차는 `PROJECT_HANDOFF.md` 4절.
