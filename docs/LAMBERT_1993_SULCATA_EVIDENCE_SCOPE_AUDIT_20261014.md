# Lambert 1993 sulcata feeding observation: evidence-scope audit (2026-10-14)

## Verified against stored research records (not a new independent PDF transcription)

Unit 2 record `lambert_1993-01` describes *Eleusine indica* as `observed to feed on`, `wild_or_captive: wild`, near Mourdiah, Mali. **The same record's limitations explicitly state:** "A previously captive female collected nearby, allowed to roam freely beside agricultural land; a single observation." Source metadata: Lambert (1993), *On Growth, Sexual Dimorphism, and the General Ecology of the African Spurred Tortoise*, CCB 1(1):37–46, https://chelonian.org/wp-content/uploads/file/CCB%20Vol%201%20No%201%20(1993)/Lambert_1993.pdf.

## Risk in Unit 5 narrative

`docs/GLOBAL_PLANT_EVIDENCE_EXPANSION_UNIT5_20261014.md` currently calls this the "only wild observation". `data/research/research_layer_summary_v5.json` likewise says "the only wild observation remains Lambert 1993". These descriptions omit the previously captive status and can be mistaken for an observation of an independently wild animal or wild-population diet. The source-level record's `wild_or_captive: wild` field also requires contextual interpretation; do **not** silently overwrite the record before inspecting the original paper and downstream schema dependencies.

## Recommended corrective wording (pending original-PDF confirmation)

"In Units 1–5, the sole recorded sulcata plant-feeding observation associated with a field setting is Lambert (1993): one previously captive female allowed to roam near agricultural land was observed feeding on *Eleusine indica*. This does **not** establish the diet of a free-living wild population, nutritional suitability, or safe feeding quantities. No independent wild-population sulcata feeding dataset was added by Unit 5."

Korean: "1~5차 자료에서 설카타의 식물 섭식에 관한 현장 맥락의 단일 관찰은 Lambert(1993)의 *Eleusine indica* 기록이다. 해당 개체는 과거 사육되던 암컷으로 농경지 인근에서 자유롭게 돌아다니도록 허용된 상태였으며, 독립적인 야생 개체군의 식단이나 급여 안전성을 입증하지 않는다."

## Follow-up QA

1. Read the original Lambert PDF passage and confirm the exact animal status and observation wording.
2. Correct the Unit 5 documentation and the **generating source** for the v5 summary, then rebuild; avoid editing generated JSON alone.
3. Consider a structured field for provenance/captive-history and ensure summary counts do not equate roaming formerly captive individuals with independently wild animals.
4. Keep feeding grades unchanged and do not merge or deploy on the strength of this audit.
