"""Reader-facing copy of assessment prose (shared by the Korean and English page generators).

assessment_copy() keeps a T. g. ibera mention only when a linked, non-composition evidence record of the
assessment actually studied T. g. ibera and the sentence states that study fact; any other mention is restated at
the scope the evidence covers. Both languages render from the same output, so the English text translates exactly
what the Korean page shows.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
evidence_by_id = {e["id"]: e for e in json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8")).get("records", [])}

IBERA_TEXT=re.compile(r"Testudo\s+graeca\s+ibera|T\.\s*g\.\s*ibera|이베라그리스육지거북|이베라", re.I)
# An Ibera mention is a statement of study fact only when it is attached to the study itself:
# "야생 T. g. ibera ...", "Testudo graeca ibera 식이 연구", "T. g. ibera 야생 관찰", "...ibera의 직접 섭식 기록".
IBERA_STUDY_BEFORE=re.compile(r"(?:야생|wild)\s*$", re.I)
IBERA_STUDY_AFTER=re.compile(r"^\s*(?:에서|의|이|가|은|는)?\s*(?:(?:야생|직접|실제)\s*)*(?:식이|섭식|관찰|기록|분변|diet|feeding|field)", re.I)
# Compound sentences that join an Ibera study clause to a general-source clause are split, so the taxon
# is not read as qualifying the general source.
IBERA_CLAUSE_JOIN=re.compile(r"(됐|되었|했|하였)(?:고|으며),\s+")

def ibera_evidence_linked(a):
    """True only when a linked, non-composition evidence record actually studied T. g. ibera."""
    for eid in ((a or {}).get("evidence_ids") or []):
        e=evidence_by_id.get(eid) or {}
        if e.get("applicability")!="composition_only" and re.search(r"ibera", str(e.get("animal_taxon") or ""), re.I):
            return True
    return False

def _ibera_neutral(mention, following):
    if mention=="이베라" and following.startswith(" 아종"):
        return "특정", 0
    if mention=="이베라" and following.startswith(" 종특이"):
        return "종 특이", len(" 종특이")
    if following.startswith(" 직접") or following.startswith("에 한정"):
        # "not an Ibera-direct test" on general evidence means "not a species-specific test"
        return "특정 종", 0
    return "육지거북", 0

def _split_ibera_clauses(sentence):
    """'야생 T. g. ibera ... 기록됐고, 일반 자료도 ...' -> two sentences, only when the Ibera mention is
    confined to the first clause."""
    m=IBERA_CLAUSE_JOIN.search(sentence)
    if not m:
        return sentence
    head, tail=sentence[:m.start()], sentence[m.end():]
    if IBERA_TEXT.search(head) and not IBERA_TEXT.search(tail):
        return f"{head}{m.group(1)}다. {tail}"
    return sentence

def assessment_copy(v, a=None):
    """Reader-facing safeguard for assessment prose, decided per Ibera mention.
    An Ibera mention is kept only when (1) a linked, non-composition evidence record of this assessment
    actually studied T. g. ibera and (2) the mention states that study fact (wild diet/observation record).
    Any other mention used Ibera as a default reference point for general evidence and is restated at the
    scope that evidence covers ("육지거북", "특정 아종", "종 특이"). Clauses that attach an Ibera study to
    a general source in one sentence are split so the taxon stays with the study only."""
    x=str(v or "")
    if not IBERA_TEXT.search(x):
        return x
    linked=ibera_evidence_linked(a)
    out=[]; pos=0
    for m in IBERA_TEXT.finditer(x):
        before=x[max(0, m.start()-8):m.start()]; after=x[m.end():m.end()+20]
        is_study=linked and (IBERA_STUDY_BEFORE.search(before) or IBERA_STUDY_AFTER.match(after))
        if m.start()<pos:
            continue
        out.append(x[pos:m.start()])
        if is_study:
            out.append(m.group(0)); pos=m.end()
        else:
            word, skip=_ibera_neutral(m.group(0), x[m.end():m.end()+6])
            out.append(word); pos=m.end()+skip
    out.append(x[pos:])
    x="".join(out)
    parts=re.split(r"(?<=[.!?])\s+", x)
    split=[_split_ibera_clauses(s) for s in parts]
    return x if split==parts else " ".join(split)

