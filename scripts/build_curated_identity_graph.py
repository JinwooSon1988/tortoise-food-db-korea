#!/usr/bin/env python3
"""Build a conservative identity graph from curated plants + WCVP reconciliation output.

This graph preserves the public food concept separately from botanical name usage.
No feeding verdict is read or written here.
"""
import json,pathlib,sys
P=pathlib.Path
plants=json.loads(P("data/plants.json").read_text(encoding="utf-8"))
audit_path=P("data/reconciliation/wcvp_exact_name_audit_2026-09-19.json")
audit=json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else {}
reviews={x["curated_name"]:x for x in audit.get("review_cases",[])}
no_exact=set(audit.get("no_exact_match",[]))
cautions={x["curated_name"]:x["note"] for x in audit.get("homonym_or_name_string_cautions",[])}
nodes=[]; edges=[]
for p in plants:
 sci=p["scientific"]
 concept="food:"+p["id"]; name="name:"+p["id"]+":curated"
 nodes += [
  {"id":concept,"type":"food_concept","ko":p["ko"],"en":p["en"],"plant_part_or_form":p["category"],"market":p["market"]},
  {"id":name,"type":"submitted_botanical_name","name":sci,"family":p["family"],"identity_status":p["identity_status"]}
 ]
 edges.append({"from":concept,"to":name,"relation":"labelled_with"})
 if "spp." in sci:
  state="genus_scope"
 elif "×" in sci:
  state="hybrid_review"
 elif sci in reviews:
  state="infraspecific_review" if (" var. " in sci or " subsp. " in sci) else "synonym_review"
 elif sci in no_exact:
  state="unresolved"
 else:
  state="exact_accepted_candidate"
 meta={"food_concept_id":concept,"submitted_name_id":name,"review_state":state}
 if sci in reviews:
  accepted="wcvp-accepted:"+p["id"]
  nodes.append({"id":accepted,"type":"backbone_accepted_name_candidate","name":reviews[sci]["wcvp_accepted_name"],"source_id":"kew_wcvp","review_required":True})
  edges.append({"from":name,"to":accepted,"relation":"backbone_treats_as_synonym_of","review_required":True})
 if sci in cautions: meta["name_string_caution"]=cautions[sci]
 nodes.append({"id":"reconciliation:"+p["id"],"type":"reconciliation_state",**meta})
 edges.append({"from":name,"to":"reconciliation:"+p["id"],"relation":"has_reconciliation_state"})
out={"schema_version":"1.0","scope":"taxonomy identity only; never a feeding verdict","nodes":nodes,"edges":edges}
q=P("data/reconciliation/curated_identity_graph.json");q.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("food concepts",len(plants),"nodes",len(nodes),"edges",len(edges))
