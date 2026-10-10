"""English text layer for the bilingual site.

Facts (plants, grades, evidence IDs, URLs, nutrient values) come only from the canonical data files. Prose that
exists in Korean in those files is translated through data/i18n/en/strings_en.json:

    {"<key>": {"en": "<English>", "ko": "<Korean source, kept for review>"}}

The key is a hash of the exact Korean source text, so editing the Korean makes the English entry disappear from
lookups: the generator then fails (or, with --collect, lists the string) instead of silently publishing stale
English. Fixed interface text (grade labels, headings) lives in this module.
"""
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRINGS = ROOT / "data/i18n/en/strings_en.json"
HANGUL = re.compile(r"[가-힣]")

_table = json.loads(STRINGS.read_text(encoding="utf-8")) if STRINGS.exists() else {}
missing = {}
passthrough = {}

# English originals stored in the data are shown as written, except for these display-only repairs of internal codes and
# of fragments left by an earlier bulk wording change ("a controlled the relevant tortoise species feeding/toxicity
# trial"). Each rule only rearranges or expands existing words; none adds or removes a fact.
POLISH = [
    (r"\bThis migrated record preserves the existing assessment/source scope\.\s*", ""),
    (r"\b(?:a|an) controlled the relevant tortoise species ([\w/-]+(?: [\w/-]+){0,2}) (trial|study)", r"a controlled \1 \2 in the relevant tortoise species"),
    (r"\b(?:a|an) controlled the relevant tortoise species (trial|study)", r"a controlled \1 in the relevant tortoise species"),
    (r"\bcontrolled the relevant tortoise species ([\w/-]+) (trial|study)", r"controlled \1 \2 in the relevant tortoise species"),
    (r"\b(?:a|an) the relevant tortoise species ([\w/-]+(?: [\w/-]+){0,2}) (trial|study)", r"a \1 \2 in the relevant tortoise species"),
    (r"\b(?:a|an) the relevant tortoise species (toxic dose)", r"a \1 for the relevant tortoise species"),
    (r"\b(?:a|an) Mediterranean Testudo or the relevant tortoise species ([\w/-]+) (trial|study)", r"a \1 \2 in Mediterranean Testudo or the relevant tortoise species"),
    (r"\bTestudo safe dose", "safe dose for Testudo"),
    (r"\bfeeding/toxicity\b", "feeding or toxicity"),
    (r"\bplant parts/taxa\b", "plant parts or taxa"),
    (r"\bassessment/source\b", "assessment and source"),
]
ANIMAL_EN = {"not_applicable": "Not applicable", "Tortoise general": "Tortoises in general", "Animals general": "Animals in general",
             "Tortoise general / Testudo context": "Tortoises in general (Testudo context)",
             "primarily mammalian/medicinal toxicology; not tortoise feeding": "Mainly mammalian and medicinal toxicology; not tortoise feeding"}


def polish(s):
    if s in ANIMAL_EN:
        return ANIMAL_EN[s]
    for pat, rep in POLISH:
        s = re.sub(pat, rep, s)
    return s


def key(ko):
    return hashlib.sha1(str(ko).strip().encode("utf-8")).hexdigest()[:16]


def T(text, where=""):
    """English for a data string. Text without Hangul is returned unchanged (already English/Latin)."""
    s = str(text or "").strip()
    if not s:
        return s
    if not HANGUL.search(s):
        out = polish(s)
        passthrough.setdefault(key(s), {"src": s, "where": where, "en": out})
        return out
    k = key(s)
    hit = _table.get(k)
    if hit and hit.get("en"):
        return hit["en"]
    missing.setdefault(k, {"ko": s, "where": where})
    return f"[[untranslated:{k}]]"


GRADES_EN = {
    "supported_mixed_diet": {"grade": "A", "label": "Recommended", "tone": "green", "meaning": "A good core component of a varied mixed diet of suitable plants."},
    "limited_mixed_diet": {"grade": "B", "label": "Feed with conditions", "tone": "teal", "meaning": "Can be part of a mixed diet within the stated limits. Do not let one plant dominate the diet."},
    "limited_supplement": {"grade": "C", "label": "Limited feeding", "tone": "yellow", "meaning": "Not a staple. Offer only occasionally as a minor addition."},
    "limited": {"grade": "C", "label": "Limited feeding", "tone": "yellow", "meaning": "Not for staple or repeated large feeds. Use only in limited amounts within a varied diet."},
    "supplement_general_evidence": {"grade": "C", "label": "Limited feeding", "tone": "yellow", "meaning": "Not a staple. Offer only occasionally as a minor addition."},
    "general_reptile_supplement": {"grade": "C", "label": "Limited feeding", "tone": "yellow", "meaning": "Not a staple. Offer only occasionally as a minor addition."},
    "do_not_feed": {"grade": "D", "label": "Do not feed", "tone": "danger", "meaning": "Do not include it in the planned diet. This is a separate question from whether an accidental small bite is toxic."},
}
HOLD_EN = {"grade": "On hold", "label": "Assessment on hold", "tone": "hold", "meaning": "The evidence is insufficient or conflicting, so no grade has been set. On hold does not mean safe."}
NO_DEFAULT_EN = {"grade": "On hold", "label": "Assessment on hold", "tone": "hold", "meaning": "There is no general feeding assessment yet. A missing assessment does not mean the plant is safe."}


def display_en(a):
    if not a:
        return NO_DEFAULT_EN
    return GRADES_EN.get(a.get("verdict"), HOLD_EN)


def scope_label_en(a):
    if not a:
        return "No general assessment"
    if a.get("animal_taxon") == "Testudo" or a.get("species_group") == "Mediterranean_Testudo":
        return "Mediterranean Testudo evidence"
    if a.get("assessment_scope") == "tortoise_general" or a.get("species_group") == "Tortoise_general":
        return "General tortoise evidence"
    if a.get("species_group") == "Herbivorous_reptile_general" or a.get("assessment_scope") == "herbivorous_reptile_general":
        return "General herbivorous-reptile evidence"
    return "Indirect evidence"


FEEDING_ACTION_EN = {
    "A": "Use it as a main part of an everyday mixed diet together with other suitable plants. Avoid feeding only this plant or unlimited amounts.",
    "B": "Feed it as part of a mixed diet with other suitable plants. Do not let it dominate the diet, and follow the part and limit notes below.",
    "C": "Do not use it as a staple. Build the diet on well-supported foods and add a small amount only occasionally.",
    "D": "Do not include it in the regular diet. An accidental small bite and deliberate repeated feeding are different questions.",
    "On hold": "Do not feed it on the assumption that it is safe. The assessment is on hold until the public evidence improves.",
}

CERTAINTY_EN = {"A": "High", "B+": "Fairly high", "B": "Moderate", "B-": "Below moderate", "C+": "Fairly low", "C": "Low",
                "C-": "Very low", "D+": "Very low", "D": "Very low", "D-": "Very low"}


def certainty_en(code):
    return CERTAINTY_EN.get(str(code or "").strip(), "Not assessed")


CAUTION_GROUPS_EN = {
    "risk": ("Hazard signals reported in the evidence", "Toxic compounds or risk signals identified in the sources. This does not mean a toxic dose for tortoises has been established."),
    "scope": ("Species and plant-part limits", "The plant species and parts the assessment covers. Do not transfer it to other species or parts."),
    "practice": ("How to feed", "Points to follow on amount, frequency, sourcing and preparation."),
    "evidence": ("Gaps and limits of the evidence", "What the current evidence cannot show. This is not a finding of toxicity."),
}

DIRECTNESS_EN = {"direct": "Direct evidence", "expert_husbandry": "Expert husbandry source", "related_taxon": "Related-taxon evidence",
                 "contextual": "Contextual evidence", "composition_only": "Composition evidence"}

SPECIALIST_LABEL_EN = {"Safe to Feed": "safe to feed", "Feed in Moderation": "feed in moderation", "Feed Sparingly": "feed sparingly", "Do not Feed": "do not feed"}

# Same English labels as the catalog's CAT map (all-plants/index.html).
CATEGORY_EN = {"leafy": "Leafy vegetable", "wild": "Wild plant", "wild_plant": "Wild plant", "wild_herb": "Wild herb", "tree_leaf": "Tree leaf",
               "vine_leaf": "Vine leaf", "flower": "Flower", "herb": "Herb", "forage": "Forage", "fruit_veg": "Fruiting vegetable",
               "cactus": "Cactus", "grass": "Grass", "ornamental": "Ornamental", "sprout": "Sprout", "succulent": "Succulent",
               "garden_plant": "Garden plant", "shrub": "Shrub"}


def category_en(c):
    return CATEGORY_EN.get(str(c or ""), str(c or "").replace("_", " ").capitalize() or "Plant")


MARKET_TOKENS_EN = {"마트": "supermarket", "시장": "market", "온라인": "online", "재배": "home-grown", "채집": "foraged", "야생": "wild",
                    "화원": "garden centre", "원예": "garden plant", "수입채소": "imported vegetable", "일부마트": "some supermarkets",
                    "일부시장": "some markets", "해외 야생": "wild outside Korea", "사료·녹비 재배": "grown as forage or green manure",
                    "잔디 대용 재배": "grown as a lawn substitute", "야생화": "wildflower"}


def market_en(m):
    """Where the plant is found in Korea, from the master's Korean market field (token map, no free translation)."""
    s = str(m or "").strip()
    if not s:
        return ""
    parts = []
    for tok in re.split(r"/", s):
        tok = tok.strip()
        if tok in MARKET_TOKENS_EN:
            parts.append(MARKET_TOKENS_EN[tok])
        else:
            for sub in re.split(r"·", tok):
                sub = sub.strip()
                parts.append(MARKET_TOKENS_EN[sub] if sub in MARKET_TOKENS_EN else T(sub, "market"))
    out = []
    for x in parts:
        if x and x not in out:
            out.append(x)
    return ", ".join(out)
