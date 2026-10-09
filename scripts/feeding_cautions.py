"""Group assessment `limits` into reader-facing feeding cautions for plant detail pages.

The canonical text in data/public_assessments.json is never rewritten here; each limit is shown verbatim (after the
same Ibera scope safeguard the page already applies) in exactly one group:

  risk      확인된 독성·위험 신호   a hazard stated by the evidence (never a negated statement)
  scope     종·부위 제한            which plant species/part the verdict covers; identification and confusion warnings
  practice  급여 방법               how much / how often / how to source and prepare
  evidence  근거 부족·한계          what the evidence does not show (explicitly not a toxicity finding)

Two kinds of Korean negation are kept apart:
  * directives ("…급여하지 않음", "…은 제외", "…만 사용") are practical instructions;
  * interpretive negations ("독성 시험이 아님", "중독으로 단정하지 않음", "…로 확대하지 않음") describe evidence limits.
An interpretive negation is never shown as a confirmed hazard. Duplicates (exact, or one limit contained in another
after normalisation) are removed, keeping the longer text.
"""
import re

GROUPS = (
    ("risk", "확인된 독성·위험 신호", "근거 자료에서 확인된 독성 성분·위험 신호다. 육지거북 중독 용량이 정해졌다는 뜻은 아니다."),
    ("scope", "종·부위 제한", "판정이 적용되는 식물 종과 부위다. 다른 종·부위에 그대로 옮기지 않는다."),
    ("practice", "급여 방법", "급여량·빈도·채집과 준비에서 지킬 점이다."),
    ("evidence", "근거 부족·한계", "현재 근거가 보여주지 못하는 부분이다. 독성이 확인됐다는 뜻은 아니다."),
)
GROUP_LABEL = {k: label for k, label, _ in GROUPS}

DIRECTIVE = re.compile(
    r"(급여하지 않|사용하지 않|편중하지 않|겹쳐 급여하지 않|급여 대상으로 보지 않|주지 않|먹이지 않|"
    r"급여 금지|편중 금지|제외$|제외함|은 제외|는 제외|제거|만 사용|피하도록|피한다|피함)")
INTERPRETIVE = re.compile(r"(지 않|지는 않|지않|아님|아니며|아니다|아닌|확립되지|불확실|부족|미확정|알려져 있지|없음|없으며|없다|없고|계산할 수 없)")
EVIDENCE_HINT = re.compile(r"(시험|근거|자료|연구|문헌|정량|용량|임상|신뢰도|직접 다룬|직접 확인|분석)")
LATIN = r"\b[A-Z][a-z]+ (?:× )?[a-z]{3,}|\b[A-Z]\. [a-z]{3,}|[A-Z][a-z]+속|spp\."
IDENTITY = re.compile(r"(혼동|동정|종 확인|학명|한정|범위|에 적용|에만 적용|" + LATIN + r")")
PART = re.compile(r"(잎|꽃|열매|뿌리|씨앗|종자|줄기|새순|어린순|꽃잎|껍질|덩굴|지상부|과육|부위|구근|덩이|패드|가시|종수)")
RISK = re.compile(
    r"(독성|중독|유독|해롭|위험|손상|사망|폐사|결석|옥살산|질산염|배당체|알칼로이드|사포닌|티오펜|풀레곤|시안|카나바닌|"
    r"자극|완하|갑상선종|Ca:P|중심 근거)")
CONTAMINATION = re.compile(r"(농약|살충제|오염|제초제|약제)")
PRACTICE = re.compile(r"(주식|무제한|소량|가끔|드물게|혼합|비율|빈도|급여량|섬유질|건초|과급여|과량|반복|편중|단독|채집|무농약)")


SPECIALIST_LABEL_KO={"Safe to Feed":"급여 가능","Feed in Moderation":"제한 급여","Feed Sparingly":"소량·드물게 급여","Do not Feed":"급여하지 않음"}
def localize_specialist_labels(v):
    """Reader-facing assessment prose: drop an English specialist label that only repeats the Korean label in
    parentheses (‘소량 급여(Feed Sparingly)’ → ‘소량 급여’) and translate any remaining bare label. Display only;
    data/public_assessments.json is not changed."""
    x=str(v or "")
    for en,ko in SPECIALIST_LABEL_KO.items():
        x=re.sub(r"\s*\(\s*"+re.escape(en)+r"\s*\)","",x)
        x=x.replace(en,ko)
    return x


def _norm(text):
    return re.sub(r"[\s·.,()'‘’\"“”]", "", text)


def classify(text):
    t = str(text)
    if CONTAMINATION.search(t):
        return "practice"
    directive = bool(DIRECTIVE.search(t))
    negated = bool(INTERPRETIVE.search(DIRECTIVE.sub("", t)))
    # An explicit warning about a hazard ("…화합물을 주의하며", "…가능성을 경고함") is a hazard signal even when
    # the same sentence also separates accidental from planned intake ("…구분함").
    if RISK.search(t) and re.search(r"(주의하|경고하|경고함|주의를 )", t) and not negated:
        return "risk"
    interpretive = negated or "구분" in t
    if interpretive:
        # An identity/part scope sentence without evidence wording stays a scope limit; never a hazard.
        if IDENTITY.search(t) and not EVIDENCE_HINT.search(t) and not RISK.search(t):
            return "scope"
        return "evidence"
    if directive:
        return "scope" if (IDENTITY.search(t) or PART.search(t)) else "practice"
    if RISK.search(t):
        return "scope" if re.search(r"(한정|범위|에 적용|에만 적용)", t) else "risk"
    if IDENTITY.search(t) or PART.search(t):
        return "scope"
    if PRACTICE.search(t):
        return "practice"
    return "evidence"


def dedupe(items):
    out = []
    for t in items:
        t = str(t).strip()
        if not t:
            continue
        n = _norm(t)
        if any(n == _norm(o) or n in _norm(o) for o in out):
            continue
        out = [o for o in out if _norm(o) not in n] + [t]
    return out


def group_limits(limits):
    """Return [(key, label, note, [texts])] in display order; empty groups are omitted."""
    buckets = {k: [] for k, _, _ in GROUPS}
    for t in dedupe(limits):
        buckets[classify(t)].append(t)
    return [(k, label, note, buckets[k]) for k, label, note in GROUPS if buckets[k]]
