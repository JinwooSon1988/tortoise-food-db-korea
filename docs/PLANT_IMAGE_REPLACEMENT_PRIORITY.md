# 식물 사진 교체 우선순위

현재 `data/plants.json` 182종 가운데 `data/verified_plant_images_v56.json`의 `part_match=match`를 충족하는 사진이 없는 식물은 60종이다. 이 수치는 브랜치 데이터 기준이며 이미지 URL 실제 응답 여부는 별도 검증 대상이다.

## 목초·꽃 우선 교체 대상 (10종)

- 티모시 (`timothy`, *Phleum pratense*)
- 라이그래스 (`ryegrass`, *Lolium* spp.)
- 보리풀 (`barleygrass`, *Hordeum vulgare*)
- 밀잎 (`wheatleaf`, *Triticum aestivum*)
- 장미 꽃잎 (`rose`, *Rosa* spp.)
- 팬지 (`pansy`, *Viola × wittrockiana*)
- 메리골드 (`marigold`, *Tagetes* spp.)
- 국화 (`chrysanthemum`, *Chrysanthemum morifolium*)
- 해바라기 꽃잎 (`sunflowerpetal`, *Helianthus annuus*)
- 호박꽃 (`pumpkinflower`, *Cucurbita* spp.)

## 교체 승인 조건

1. 정확한 학명 및 사진 속 식물 동정 근거 확인. `spp.` 대상은 종 미확정 사진을 종 확정으로 표시하지 않음.
2. 실제 평가·급여 대상 부위가 사진에서 명확히 확인되어야 함.
3. 원본 파일 출처, 저작자, 이용 허락 범위와 표시 의무 기록.
4. 이미지 URL의 실제 표시 여부와 모바일 가독성 검증.
5. 식물 동정 사진은 급여 안전성의 증거로 사용하지 않음.

교체가 검증되기 전에는 임의의 유사종 또는 부위 불일치 사진으로 빈칸을 채우지 않는다.
