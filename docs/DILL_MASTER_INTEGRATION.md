# Dill master integration packet

Verified candidate: Dill / 딜 (`Anethum graveolens`, Apiaceae), verified 2026-09-15. Target after promotion: 67 master plants / 64 explainable assessed plants / 2 identity-blocked / 1 evidence-blocked.

Specialist source: The Tortoise Table, Dill (Dill Weed), current dedicated detail-page verdict **Feed in Moderation**. The entry says there are no known hazards, but suitability evidence is insufficient for unrestricted feeding; it recommends moderation in a varied diet and explicitly says not to feed seeds. This dedicated detail record is authoritative for the staged packet.

Prepared assets: `data/evidence_korea_addendum_10.json`, `data/dill_candidate_packet.json`, and `data/dill_candidate_assessment.json`. Candidate and assessment staging/provenance packets are complete and marked ready for atomic promotion, while the assessment remains `staged_not_runtime` and `user_facing: false` until that release.

Release gate: add `dill` to `data/plants.json` only in the same release change that promotes the staged assessment into the runtime assessment set, increments coverage master/assessment counts, generates the static plant detail/search/sitemap entries, updates runtime addendum loading and PWA cache, and passes release/site audits. Never ship a master row without its review state.

Applicability: general-tortoise evidence only; do not promote to Mediterranean Testudo or Ibera direct evidence. Plant-part scope is the leafy culinary herb; seeds are explicitly excluded. No staple role or captive feeding percentage is implied. Promotion scope is locked to `Tortoise_general` unless stronger evidence is added later.

Why staged first: the 66-plant master now has strict complete-review accounting in CI. Dill therefore must enter as an atomic 67th record rather than bypassing the new invariant during a partial update.

Source consistency note: broad Tortoise Table search-result pages can display neighboring verdict labels ambiguously. The dedicated Dill detail page is the authoritative record used here. This rule should be reused for future candidate ingestion when a search listing conflicts with the dedicated record.

Expected accounting after atomic promotion: 67 = 64 assessed + 2 identity-blocked + 1 evidence-blocked. The release audit introduced in PR #66 must remain green after this transition. Runtime promotion is explicitly blocked until the master record exists.

This staging change deliberately does not change `plant_master_count`, runtime assessment count, or user-facing verdicts. It is a provenance packet, not a published feeding recommendation. The staged assessment carries source-authority, visibility, species-scope, and plant-part-scope locks so later promotion cannot accidentally widen its applicability.

Staging phase status: complete. Promotion handoff: complete. Staging PR: ready. Next action: atomic master promotion.
