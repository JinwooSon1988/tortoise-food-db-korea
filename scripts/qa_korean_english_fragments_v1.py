#!/usr/bin/env python3
"""Korean copy QA: no unintended English fragments in user-facing Korean text.

Checked surfaces
- Rendered static pages: index.html, all-plants, core-foods, guides/*, plant/*/index.html.
- Text the home search / catalog renders client-side: public_assessments.json (why, role, limits,
  applicability_note) and the Korean evidence text in public_evidence_records.json
  (English-only evidence text is translated by the page generator and is checked on the rendered pages).

Intentional English is not reported (see data/korean_copy_intentional_english_v1.json):
- scientific names: every Latin token in a taxon field of the data, family names (-aceae), rank markers
  (spp., var., subsp., ...) and abbreviated genera ("T.", "h.");
- author surnames and journal titles of the linked evidence; institutions, cultivar names and technical
  abbreviations listed in the registry;
- page regions that are English on purpose: elements with lang="en", italic text, evidence source titles,
  DOI/PMID rows, external links, script/style and the hidden English-mode blocks;
- English inside quotation marks, used to cite an English common name (‘Rose of Sharon’);
- grade tokens (A–D with +/-), chemical prefixes (L-, N-, α-) and version numbers.
Anything else written in Latin letters inside Korean copy is an unintended fragment and fails the check.
"""
import json, re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
load = lambda f: json.loads((D / f).read_text(encoding="utf-8"))

RANK = {"spp", "sp", "var", "subsp", "ssp", "agg", "cv", "syn", "f", "x", "nothosubsp", "aff", "cf", "et", "al", "L"}
GENERIC = re.compile(r"(?i)^(and|or|the|of|in|on|to|by|with|from|as|is|are|plant|plants|leaf|leaves|general|tortoise|tortoises|species|"
                     r"reported|accessions|herbivorous|reptile|reptiles|mammals?|multiple|various|not|applicable|human|food|composition|"
                     r"mediterranean|wild|cultivated|greens|seedlings?|domestic|animals?|livestock|rats?|mice|cell|cells|lines?|model|"
                     r"vitro|unknown|na|none|group|genus|taxa|study|source|see|linked|concept|scope|preserved|evidence|registry|"
                     r"and/or|within|eastern|clades|observations|context|chemistry)$")


def registry():
    reg = load("korean_copy_intentional_english_v1.json")
    words, phrases = set(), set()
    for cat in reg["categories"].values():
        for item in cat["items"]:
            phrases.add(item)
            words.update(re.findall(r"[A-Za-z][A-Za-z\-']*", item))
    return words, phrases


def data_vocabulary():
    words = set()
    def add(text):
        for w in re.findall(r"[A-Za-z][A-Za-z\-']+", str(text or "")):
            if not GENERIC.match(w):
                words.add(w)
    for p in load("plants.json"):
        add(p.get("scientific")); add(p.get("family"))
    # Evidence taxon fields can contain English scope prose ("... within the source's squash scope"); only Latin
    # names in binomial/trinomial position are taken from them.
    not_genus = {"Plant", "Plants", "Mustard", "Grasses", "Herbivorous", "Tortoise", "Tortoises", "Reptiles", "Animals", "Cats",
                 "Human", "Mediterranean", "Korean", "Chinese", "Mexican", "Multiple", "Not", "See", "General", "Dandelion",
                 "Festival", "Group", "Sweet", "Leaves", "Leaf", "Species", "Plant-eating"}
    binomial = re.compile(r"\b([A-Z][a-z]+|[A-Z]\.)\s+(?:×\s+)?([a-z]{3,}(?:-[a-z]+)?)(?:\s+(?:subsp\.|var\.|ssp\.)?\s*([a-z]{3,}))?")
    for e in load("public_evidence_records.json")["records"]:
        for field in ("plant_taxon", "animal_taxon"):
            for g, sp, ssp in binomial.findall(str(e.get(field) or "")):
                if g not in not_genus:
                    add(g); add(sp); add(ssp)
        add(e.get("journal"))
        for a in (e.get("authors") or []) if isinstance(e.get("authors"), list) else [e.get("authors")]:
            add(re.sub(r"\b[A-Z]\.", " ", str(a or "")))
        add(re.sub(r"\b[A-Z]\.", " ", str(e.get("author") or "")))
    for w in load("wild_feeding_evidence.json").get("records", []):
        add(w.get("plant_taxon_accepted")); add(w.get("plant_taxon_reported")); add(w.get("tortoise_taxon"))
    for o in load("ibera_direct_feeding_evidence_v56.json").get("observations", []):
        add(o.get("source_plant"))
    return words


REG_WORDS, REG_PHRASES = registry()
VOCAB = data_vocabulary() | REG_WORDS
RUN = re.compile(r"[A-Za-z][A-Za-z\-'.:]*(?:[  &/]+[A-Za-z][A-Za-z\-'.:]*)*")
QUOTED = re.compile(r"‘[^’]{1,80}’|“[^”]{1,80}”|'[A-Za-z][^'\n]{0,60}'")


def allowed(tok):
    t = tok.strip(".,:;()").rstrip(".")
    if not t:
        return True
    if t in VOCAB or t.lower() in RANK or t.endswith("aceae") or t.endswith("oideae"):
        return True
    if re.fullmatch(r"[A-Za-z]", t):                      # abbreviated genus / subspecies initial (T., h.)
        return True
    if re.fullmatch(r"[A-D][+-]?", t) or re.fullmatch(r"[A-Z]-", tok) or re.fullmatch(r"v\d.*", t):
        return True                                          # grade tokens, chemical prefixes, versions
    return False


def fragments(text):
    """Latin-letter runs in Korean text that contain a token outside the intentional-English vocabulary."""
    if not re.search(r"[가-힣]", text):
        return []
    for ph in sorted(REG_PHRASES, key=len, reverse=True):
        if " " in ph or not re.fullmatch(r"[A-Za-z]+", ph):   # multi-word or punctuated names; single words are in VOCAB
            text = re.sub(r"(?<![A-Za-z])" + re.escape(ph) + r"(?![A-Za-z])", " ", text)
    text = QUOTED.sub(" ", text)
    out = []
    for m in RUN.finditer(text):
        toks = [t for t in re.split(r"[  &/]+", m.group(0)) if t]
        if any(not allowed(t) for t in toks):
            out.append(m.group(0).strip(" .,:;"))
    return out


class Visible(HTMLParser):
    SKIP_TAGS = {"script", "style", "i", "em", "cite", "code", "title"}
    VOID = {"br", "img", "input", "meta", "link", "hr", "source", "wbr"}
    BLOCK = {"p", "li", "h1", "h2", "h3", "dd", "dt", "td", "th", "div", "section", "article", "small", "figcaption", "header", "footer", "nav", "main"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.chunks, self.cur = [], [], []

    def _skip(self, tag, a):
        cls = (a.get("class") or "").split()
        if tag in self.SKIP_TAGS or "hidden" in a or a.get("aria-hidden") == "true" or (a.get("lang") or "").startswith("en"):
            return True
        if any(c in cls for c in ("en-evidence", "ids", "sr-only", "scientific", "sci")):
            return True
        if tag == "a" and re.match(r"https?://", a.get("href") or ""):
            return True
        if tag == "h3" and any(t == "article" and "evcard" in (c or "") for t, _, c in self.stack):
            return True
        return False

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            if tag == "br":
                self.cur.append(" ")
            return
        a = dict(attrs)
        parent_skip = bool(self.stack) and self.stack[-1][1]
        if tag in self.BLOCK:
            self.flush()
        self.stack.append((tag, parent_skip or self._skip(tag, a), a.get("class")))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if tag in self.BLOCK:
            self.flush()

    def handle_data(self, data):
        if not (self.stack and self.stack[-1][1]):
            self.cur.append(data)

    def flush(self):
        t = re.sub(r"\s+", " ", "".join(self.cur)).strip()
        if t:
            self.chunks.append(t)
        self.cur = []


def page_chunks(path):
    v = Visible()
    v.feed(path.read_text(encoding="utf-8"))
    v.flush()
    return v.chunks


def korean_majority(text):
    letters = re.findall(r"[A-Za-z가-힣]", text)
    return bool(letters) and sum(1 for c in letters if "가" <= c <= "힣") / len(letters) >= 0.3


def check():
    findings = []
    pages = [ROOT / "index.html", ROOT / "all-plants/index.html", ROOT / "core-foods/index.html"]
    pages += sorted((ROOT / "guides").glob("*/index.html")) + sorted((ROOT / "plant").glob("*/index.html"))
    for p in pages:
        for chunk in page_chunks(p):
            for f in fragments(chunk):
                findings.append((p.relative_to(ROOT).as_posix(), f, chunk))
    n_text = 0
    for a in load("public_assessments.json"):
        for field in ("why", "role", "applicability_note"):
            n_text += 1
            for f in fragments(str(a.get(field) or "")):
                findings.append((f"public_assessments:{a['plant_id']}.{field}", f, a.get(field)))
        for i, x in enumerate(a.get("limits") or []):
            n_text += 1
            for f in fragments(str(x)):
                findings.append((f"public_assessments:{a['plant_id']}.limits[{i}]", f, x))
    for e in load("public_evidence_records.json")["records"]:
        for field in ("supports", "does_not_support", "plant_part_state"):
            v = str(e.get(field) or "")
            if korean_majority(v):
                n_text += 1
                for f in fragments(v):
                    findings.append((f"public_evidence_records:{e['id']}.{field}", f, v))
    return findings, len(pages), n_text


if __name__ == "__main__":
    findings, n_pages, n_text = check()
    if "--list" in sys.argv:
        from collections import Counter
        for frag, n in Counter(f for _, f, _ in findings).most_common():
            print(n, frag)
        sys.exit(0)
    if findings:
        print(f"FAIL: {len(findings)} unintended English fragments in Korean copy")
        for where, frag, ctx in findings[:80]:
            print(f"- {where}: «{frag}» in: {str(ctx)[:140]}")
        sys.exit(1)
    print(f"PASS: no unintended English fragments in Korean copy ({n_pages} pages, {n_text} canonical Korean text fields)")
