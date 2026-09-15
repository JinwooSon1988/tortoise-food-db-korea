# Dill master integration packet

Verified candidate: Dill / 딜 (`Anethum graveolens`, Apiaceae), verified 2026-09-15. Target after promotion: 67 master plants / 64 explainable assessed plants / 2 identity-blocked / 1 evidence-blocked.

Specialist source: The Tortoise Table, Dill (Dill Weed), current dedicated detail-page verdict **Feed in Moderation**. The entry says there are no known hazards, but suitability evidence is insufficient for unrestricted feeding; it recommends moderation in a varied diet and explicitly says not to feed seeds.

Prepared assets: `data/evidence_korea_addendum_10.json`, `data/dill_candidate_packet.json`, and `data/dill_candidate_assessment.json`. The assessment is intentionally marked `staged_not_runtime` until the master/UI release is atomic.

Release gate: add `dill` to `data/plants.json` only in the same release change that promotes the staged assessment into the runtime assessment set, increments coverage master/assessment counts, generates the static plant detail/search/sitemap entries, updates runtime addendum loading and PWA cache, and passes release/site audits. Never ship a master row without its review state.

Applicability: general-tortoise evidence only; do not promote to Mediterranean Testudo or Ibera direct evidence. Leafy culinary herb only; source explicitly says not to feed seeds. No staple role or captive feeding percentage is implied.

Why staged first: the 66-plant master now has strict complete-review accounting in CI. Dill therefore must enter as an atomic 67th record rather than bypassing the new invariant during a partial update.

Source consistency note: broad Tortoise Table search-result pages can display neighboring verdict labels ambiguously. The dedicated Dill detail page is the authoritative record used here. This rule should be reused for future candidate ingestion when a search listing conflicts with the dedicated record.

Next release action: promote the staged candidate atomically; after that, use the same pipeline to add further Korea-accessible plants in batches rather than inflating the master with unreviewed names.

Expected accounting after atomic promotion: 67 = 64 assessed + 2 identity-blocked + 1 evidence-blocked. The release audit introduced in PR #66 must remain green after this transition.
