# Existing species research linkage audit — 2026-10-14

Source: `data/research/plant_candidates_v1.json` in research PR #304. These are the 17 candidates with `database_status=species_already_in_database`; no public data or grade is modified.

## Four existing species with direct tortoise-evidence record links

| Scientific name | Public plant ID(s) | Research evidence ID | Required next check |
|---|---|---|---|
| *Cynodon dactylon* | `bermudagrass` | `mason_1999-01` | Check original study, observed species, plant part, locality and context |
| *Ficus carica* | `figleaf` | `crm059_hermanni_2011-05` | Source reports **fruit**, not leaves: do not attach this as fig-leaf feeding evidence |
| *Opuntia ficus-indica* | `opuntiapad` | `mason_1999-22` | Source does not state plant part: cannot infer pad consumption |
| *Portulaca oleracea* | `purslane` | `crm110_sulcata_2020-07` | Secondary account; original primary study not read, plant part not stated |

**Important:** a plant-level scientific-name match is not enough to support a plant-**part**-specific public claim. The *Ficus carica* observation concerns **fruit**, so it cannot support the existing `figleaf` page's leaf-specific claim. The *Opuntia ficus-indica* record does **not state a part**, so it cannot establish pad consumption. The *Portulaca oleracea* observation is a secondary account whose cited original was not read. These are research links, not independently validated feeding guidance. No source record here is a feeding-safety trial.

## Thirteen existing species with no linked tortoise observation in this candidate file

`Capsella bursa-pastoris` (`shepherdspurse`), `Centaurea cyanus` (`cornflower`), `Cichorium intybus` (`chicory`, `radicchio`), `Hypochaeris radicata` (`catsear`), `Malva sylvestris` (`commonmallow`), `Onobrychis viciifolia` (`sainfoin`), `Plantago lanceolata` (`ribwortplantain`), `Plantago major` (`broadleafplantain`), `Sisymbrium officinale` (`hedgemustard`), `Trifolium pratense` (`redclover`), `Trifolium repens` (`whiteclover`), `Vicia cracca` (`vicia_cracca`), `Vicia sativa` (`vicia_sativa`).

Their appearance in this candidate file is **not** a newly documented species-specific tortoise feeding observation. Other source types or research tables may exist, but must be evaluated separately. Do not claim all 17 are newly backed by tortoise feeding evidence.

## Release constraint

Retain all existing public A/B/C/D verdicts pending a separate evidence review and explicit publication approval. No automated promotion of wild diet observations into safety recommendations.

## Source-field audit of the four linked records

The following fields are transcribed from PR #304 research JSON, not independently re-read from the linked PDFs in this audit.

| Plant / existing page | Tortoise recorded | Plant part | Preparation | Source page | Editorial disposition |
|---|---|---|---|---|---|
| *Cynodon dactylon* / `bermudagrass` | *Stigmochelys pardalis* | not stated in table | growing plant | Mason et al. 1999, p. 438 | Species-level consumption observation only; no specific part claim |
| *Ficus carica* / `figleaf` | *Testudo hermanni* | **fruit** | fruit | Hermann's tortoise account (2011), p. 10 | **Do not use to support leaf consumption** |
| *Opuntia ficus-indica* / `opuntiapad` | *Stigmochelys pardalis* | not stated in table | growing plant | Mason et al. 1999, p. 438 | **Do not claim pad consumption from this record** |
| *Portulaca oleracea* / `purslane` | *Centrochelys sulcata* | not stated | growing plant | Sulcata account (2020), p. 9 | Secondary citation; **primary study not read**, no part-specific claim |

Source URLs: Mason et al. (1999) <https://chelonian.org/wp-content/uploads/file/CCB_Vol_3_Nos_1-4(1998-2000)/Mason_etal_1999.pdf>; Hermann's tortoise account (2011) <https://iucn-tftsg.org/wp-content/uploads/file/Accounts/crm_5_059_hermanni_v1_2011.pdf>; sulcata account (2020) <https://iucn-tftsg.org/wp-content/uploads/crm.5.110.sulcata.v1.2020.pdf>.

**Approval state: HOLD for automated publication of these research links.** These records may inform a future, species-scoped observation section after source review, but they cannot establish a general A/B/C/D grade or a plant-part-specific safety recommendation. No public entry has been modified.
