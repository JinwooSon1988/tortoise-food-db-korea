#!/usr/bin/env python3
"""Checkpointed incremental OpenAlex discovery. Metadata leads only, never feeding verdicts."""
import argparse, json, os, time, urllib.error
from pathlib import Path
from collect_worldwide_tortoise_literature import GENERA, TOPICS, search, normalized

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--state",default="worker-output/discovery-state.json")
    ap.add_argument("--out",default="worker-output/worldwide-literature.json")
    ap.add_argument("--queries",type=int,default=2)
    ap.add_argument("--pages",type=int,default=1)
    ap.add_argument("--per-page",type=int,default=50)
    args=ap.parse_args()
    statefile=Path(args.state); output=Path(args.out)
    state=json.loads(statefile.read_text(encoding="utf-8")) if statefile.exists() else {"cursor":0,"failures":[]}
    corpus=json.loads(output.read_text(encoding="utf-8")) if output.exists() else {"works":[]}
    works={str(w.get("openalex_id") or w.get("id")):w for w in corpus.get("works",[]) if w.get("openalex_id") or w.get("id")}
    tasks=[(g,t) for g in GENERA for t in TOPICS]
    success=0; added=0
    for offset in range(min(args.queries,len(tasks))):
        cursor=state["cursor"]%len(tasks)
        genus,topic=tasks[cursor]
        try:
            hits=list(search(genus+" "+topic,args.pages,args.per_page,os.environ.get("OPENALEX_EMAIL")))
            for w in hits:
                key=w.get("id")
                if key and key not in works:
                    works[key]=normalized(w,genus,topic); added+=1
            success+=1
            state["cursor"]=(cursor+1)%len(tasks)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError) as exc:
            state.setdefault("failures",[]).append({"query":genus+" "+topic,"error":str(exc),"time":time.time()})
            # 429 and other transient errors: checkpoint and retry later, do not hammer the API.
            if isinstance(exc,urllib.error.HTTPError) and exc.code==429:
                print("Rate limited: defer remaining queries to next scheduled run.")
            break
        finally:
            corpus["works"]=list(works.values())
            corpus["warning"]="Bibliographic leads only; no tortoise feeding safety assertions."
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(json.dumps(corpus,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            statefile.parent.mkdir(parents=True,exist_ok=True)
            statefile.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        time.sleep(3)
    print(json.dumps({"queries_completed":success,"new_works":added,"total_works":len(works),"cursor":state["cursor"]},ensure_ascii=False))
if __name__=="__main__":
    main()
