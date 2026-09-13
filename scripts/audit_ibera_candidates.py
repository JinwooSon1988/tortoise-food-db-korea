from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "data" / "ibera_field_food_candidates.json"
data = json.loads(path.read_text(encoding="utf-8"))

errors = []
ids = set()
for row in data.get("candidates", []):
    cid = row.get("candidate_id")
    if not cid:
        errors.append("candidate without candidate_id")
        continue
    if cid in ids:
        errors.append(f"duplicate candidate_id: {cid}")
    ids.add(cid)

    status = row.get("public_mapping_status")
    if status not in {"hold_identity_mismatch", "no_upgrade"}:
        errors.append(f"unsafe public_mapping_status for {cid}: {status}")

    if cid.startswith("sedum_") and status != "hold_identity_mismatch":
        errors.append(f"Sedum candidate must remain identity hold: {cid}")

    if cid == "medicago_sp_ibera" and status != "hold_identity_mismatch":
        errors.append("Medicago sp. must not be auto-mapped to retail alfalfa")

    if cid == "plantago_direct_ibera_gap":
        if row.get("direct_ibera_evidence"):
            errors.append("Plantago direct-Ibera gap must not contain direct evidence until verified")
        if status != "no_upgrade":
            errors.append("Plantago direct-Ibera gap must remain no_upgrade")

if len(ids) < 4:
    errors.append(f"expected at least 4 reviewed candidates, found {len(ids)}")

if errors:
    print("Ibera candidate audit FAILED")
    for e in errors:
        print("-", e)
    raise SystemExit(1)

print(f"Ibera candidate audit PASS: {len(ids)} candidates; no unsafe species-to-retail promotion")
