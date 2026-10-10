#!/usr/bin/env python3
"""English site contract (/en/): completeness, Korean/English fact parity, language switch, hreflang, sitemap, links.

Facts must be identical in both languages because both are generated from the same canonical files; this QA fails on
any drift instead of tolerating it. Run after the full pipeline (generate_static_pages ... generate_en_pages).
"""
import html, json, re, subprocess, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from public_verdict import load_assessments, public_plants, by_plant, representative, display  # noqa: E402

SITE = "https://jinwooson1988.github.io/tortoise-food-db-korea"
HANGUL = re.compile(r"[가-힣]")
errors = []
# Homepage is search-first. Removed promotional and guide blocks must never return.
_home = (ROOT / "en/index.html").read_text(encoding="utf-8")
for _obsolete in ('<section class="truststrip"', '<h2>Guides</h2>'):
    if _obsolete in _home:
        errors.append("English homepage regression: obsolete section returned: " + _obsolete)
for _required in ('href="../all-plants/?lang=en"', 'href="./guides/research-method/"'):
    if _required not in _home:
        errors.append("English homepage missing essential navigation: " + _required)

fail = lambda msg: errors.append(msg)
read = lambda p: p.read_text(encoding="utf-8")


class Page(HTMLParser):
    """Collects visible text and attributes, tracking which text sits inside a lang="ko" element."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.hangul, self.links, self.alternates, self.canonical, self.ext = [], [], [], {}, None, set()
        self.script = None

    def ko(self):
        return any(l == "ko" for _, l in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        lang = a.get("lang") or (self.stack[-1][1] if self.stack else None)
        if tag not in self.VOID:
            self.stack.append((tag, lang))
        inside_ko = lang == "ko"
        for k in ("alt", "title", "aria-label", "placeholder", "content"):
            if a.get(k) and HANGUL.search(a[k]) and not inside_ko:
                self.hangul.append(f"{tag}[{k}]={a[k][:40]}")
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            self.alternates[a["hreflang"]] = a.get("href")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag in ("a", "link", "script", "img") and (a.get("href") or a.get("src")):
            href = a.get("href") or a.get("src")
            if tag == "a" or tag in ("script", "img") or a.get("rel") == "stylesheet":
                self.links.append((tag, href, a))
            if tag == "a" and href.startswith("http") and SITE not in href:
                self.ext.add(href.split("#")[0].rstrip("/"))
        if tag == "script":
            self.script = a.get("type") or "js"

    def handle_endtag(self, tag):
        if tag == "script":
            self.script = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, d):
        if HANGUL.search(d) and not self.ko():
            self.hangul.append(("script:" if self.script else "") + d.strip()[:50])


def parse(path):
    p = Page()
    p.feed(read(path))
    return p


def rel_of(path):
    r = "/" + path.relative_to(ROOT).as_posix()
    return r[: -len("index.html")]


def resolve(page_path, href):
    """Local file a relative link points to (None for external/anchor/data links)."""
    if href.startswith(("http:", "https:", "mailto:", "#", "data:", "javascript:")):
        if href.startswith(SITE):
            href = "/" + href[len(SITE):].lstrip("/")
            target = ROOT / unquote(urlparse(href).path).lstrip("/")
        else:
            return None
    else:
        base = "/" + page_path.relative_to(ROOT).as_posix()
        target = ROOT / unquote(urlparse(urljoin(base, href)).path).lstrip("/")
    if target.is_dir() or str(target).endswith(("/", "\\")):
        target = target / "index.html"
    return target


# 1. Completeness: every public plant has a Korean and an English page, and nothing else is published under en/plant.
plants = public_plants(json.loads(read(ROOT / "data/plants.json")), load_assessments())
ids = {p["id"] for p in plants}
ko_ids = {d.name for d in (ROOT / "plant").iterdir() if (d / "index.html").exists()}
en_ids = {d.name for d in (ROOT / "en/plant").iterdir() if (d / "index.html").exists()}
if ids != en_ids:
    fail(f"English plant pages differ from public plants: missing {sorted(ids - en_ids)[:10]}, extra {sorted(en_ids - ids)[:10]}")
if ko_ids != en_ids:
    fail(f"Korean/English plant page sets differ: {sorted(ko_ids ^ en_ids)[:10]}")
hubs = ["", "all-plants/", "core-foods/", "guides/market-foods/", "guides/wild-plants/", "guides/caution-foods/", "guides/research-method/"]
for h in hubs:
    for pre in ("", "en/"):
        if not (ROOT / pre / h / "index.html").exists():
            fail(f"missing page {pre}{h}index.html")

# 2. English pages contain no Korean outside lang="ko" (text, attributes, metadata, structured data, inline scripts).
en_pages = sorted((ROOT / "en").rglob("index.html"))
parsed = {}
for f in en_pages:
    p = parse(f)
    parsed[f] = p
    if p.hangul:
        fail(f"{f.relative_to(ROOT)}: Korean text on English page: {p.hangul[:3]}")
    if '<html lang="en">' not in read(f):
        fail(f"{f.relative_to(ROOT)}: html lang is not en")
for js in (ROOT / "en").glob("*.js"):
    for line in read(js).splitlines():
        code = re.sub(r"/\*.*?\*/|//.*$", "", line)
        if HANGUL.search(re.sub(r"/[^/\n]*\[가-힣\][^/\n]*/", "", code)):
            fail(f"{js.relative_to(ROOT)}: Korean literal in English script: {code.strip()[:60]}")
cat = json.loads(read(ROOT / "data/i18n/en/catalog_en.json"))["plants"]
if {c["id"] for c in cat} != ids:
    fail("catalog_en.json ids differ from public plants")
for c in cat:
    for k in ("name", "why", "role", "market"):
        if HANGUL.search(c.get(k) or ""):
            fail(f"catalog_en {c['id']}.{k} contains Korean")
    if not c.get("name"):
        fail(f"catalog_en {c['id']} has no English name")
cat_by = {c["id"]: c for c in cat}

# 3. Fact parity on every plant: grade, verdict, nutrition numbers, evidence sources.
rows_by = by_plant(load_assessments())
GRADE_EN = {"보류": "On hold"}
KIND_EN = {"동료심사 논문": "Peer-reviewed paper", "학술 연구": "Academic research", "수의학 자료": "Veterinary source",
           "전문 사육·식물 자료": "Specialist husbandry or plant source", "식물동정·분류 자료": "Plant identification / taxonomy",
           "성분 참고자료": "Composition reference", "공식 평가자료": "Official assessment", "기타 공공·맥락 자료": "Other public or contextual source"}
# Ordinal "1차" (primary) is a word, not a value; every other number in the nutrition section must match exactly.
nut_num = re.compile(r"\d+(?:\.\d+)?(?!\d|\.\d|차)")


def section(doc, sid):
    m = re.search(rf'<section[^>]*id="{sid}".*?</section>', doc, re.S)
    return m.group(0) if m else ""


for pid in sorted(ids & en_ids & ko_ids):
    ko, en = read(ROOT / "plant" / pid / "index.html"), read(ROOT / "en/plant" / pid / "index.html")
    kd = re.search(r'class="card [^"]*decision" data-grade="([^"]+)" data-verdict="([^"]+)"', ko)
    ed = re.search(r'class="card [^"]*decision" data-grade="([^"]+)" data-verdict="([^"]+)"', en)
    if not kd or not ed:
        fail(f"{pid}: decision block missing (ko={bool(kd)}, en={bool(ed)})")
        continue
    rep = representative(rows_by.get(pid, []))
    exp = display(rep)
    if rep and rep.get("why") and not (cat_by.get(pid) or {}).get("why"):
        fail(f"{pid}: has a general assessment but no English reason in catalog_en")
    if GRADE_EN.get(kd.group(1), kd.group(1)) != ed.group(1) or kd.group(2) != ed.group(2):
        fail(f"{pid}: grade/verdict differ ko={kd.groups()} en={ed.groups()}")
    if kd.group(1) != exp["grade"]:
        fail(f"{pid}: Korean grade {kd.group(1)} differs from canonical {exp['grade']}")
    kn, enn = section(ko, "nutrition"), section(en, "nutrition")
    if bool(kn) != bool(enn):
        fail(f"{pid}: nutrition section present in one language only")
    elif kn:
        strip = lambda s: html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r'<a [^>]*>.*?</a>|<(?:i|cite)>.*?</(?:i|cite)>', " ", s, flags=re.S)))
        knums = sorted(nut_num.findall(strip(kn).replace(",", "")))
        enums = sorted(nut_num.findall(strip(enn).replace(",", "")))
        if knums != enums:
            fail(f"{pid}: nutrition numbers differ ko-only={sorted(set(knums) - set(enums))[:6]} en-only={sorted(set(enums) - set(knums))[:6]}")
    kext = parse(ROOT / "plant" / pid / "index.html").ext
    eext = parsed[ROOT / "en/plant" / pid / "index.html"].ext
    if kext != eext:
        fail(f"{pid}: evidence/source links differ ko-only={sorted(kext - eext)[:3]} en-only={sorted(eext - kext)[:3]}")
    for name, doc in (("ko", ko), ("en", en)):
        if len(re.findall(r'<article class="evcard', doc)) != len(re.findall(r'<article class="evcard[^"]*"[^>]*data-evidence-id="[^"]+"', doc)):
            fail(f"{pid} ({name}): evidence card without data-evidence-id")
    kev = re.findall(r'data-evidence-id="([^"]+)"', ko)
    eev = re.findall(r'data-evidence-id="([^"]+)"', en)
    chips = lambda doc: re.findall(r"<strong>(\d+)", (re.search(r'<div class="evstats">(.*?)</div></div>', doc, re.S) or re.search(r"()", "")).group(1))
    if chips(ko) != chips(en) or (('class="evstats"' in ko) and len(chips(ko)) != 3):
        fail(f"{pid}: evidence counts differ ko={chips(ko)} en={chips(en)}")
    kinds = lambda doc:re.findall(r'<article class="evcard"[^>]*><div class="evhead"><span[^>]*>([^<]+)</span>', doc)
    if [KIND_EN.get(k, "?" + k) for k in kinds(ko)] != kinds(en):
        fail(f"{pid}: source-type labels differ ko={kinds(ko)[:4]} en={kinds(en)[:4]}")
    if kev != eev:
        fail(f"{pid}: evidence ids or their order differ ko={kev[:4]} en={eev[:4]}")

# 4. Guides list the same plants in both languages.
for slug in ("market-foods", "wild-plants", "caution-foods"):
    k = set(re.findall(r'href="\.\./\.\./plant/([^/"]+)/"', read(ROOT / "guides" / slug / "index.html")))
    e = set(re.findall(r'href="\.\./\.\./plant/([^/"]+)/"', read(ROOT / "en/guides" / slug / "index.html")))
    if k != e or not k:
        fail(f"guide {slug}: plant lists differ {sorted(k ^ e)[:6]}")
kc = re.findall(r'class="item" href="\.\./plant/([^/"]+)/"', read(ROOT / "core-foods/index.html"))
ec = re.findall(r'class="item" href="\.\./plant/([^/"]+)/"', read(ROOT / "en/core-foods/index.html"))
if kc != ec:
    fail(f"core-foods: plant lists differ {kc} vs {ec}")

# 5. Language switch, canonical and reciprocal hreflang on every page pair.
pairs = [(ROOT / "plant" / i / "index.html", ROOT / "en/plant" / i / "index.html") for i in sorted(ids)]
pairs += [(ROOT / h / "index.html", ROOT / "en" / h / "index.html") for h in hubs]
# Pages whose Korean version switches language in place (buttons, ?lang=en) instead of linking to /en/, and the
# legacy English URL that only redirects to the shared page in English. Both are the current live design.
IN_PLACE = {ROOT / "index.html", ROOT / "all-plants/index.html"}
REDIRECT_STUBS = {ROOT / "en/all-plants/index.html": "../../all-plants/?lang=en"}
for kf in IN_PLACE:
    if not re.search(r'<nav class="langswitch"[^>]*>.*?data-lang="en"', read(kf), re.S) and "language-toggle.js" not in read(kf):
        fail(f"{kf.relative_to(ROOT)}: no in-page language switch")
for ef, target in REDIRECT_STUBS.items():
    doc = read(ef)
    if f"location.replace('{target}'" not in doc or 'name="robots" content="noindex' not in doc and "noindex" not in doc:
        fail(f"{ef.relative_to(ROOT)}: legacy English URL must redirect to {target} (and not be indexed)")
for kf, ef in pairs:
    if not (kf.exists() and ef.exists()) or ef in REDIRECT_STUBS:
        continue
    kp, ep = parse(kf), parsed.get(ef) or parse(ef)
    kurl, eurl = SITE + rel_of(kf), SITE + rel_of(ef)
    if kf in IN_PLACE:
        if ep.canonical != eurl:
            fail(f"{ef.relative_to(ROOT)}: canonical {ep.canonical} != {eurl}")
        esw = [h for t, h, a in ep.links if t == "a" and a.get("hreflang") == "ko"]
        if len(esw) != 1 or resolve(ef, esw[0]) != kf:
            fail(f"{ef.relative_to(ROOT)}: language switch does not point to {kf.relative_to(ROOT)} ({esw})")
        continue
    if kp.canonical != kurl:
        fail(f"{kf.relative_to(ROOT)}: canonical {kp.canonical} != {kurl}")
    if ep.canonical != eurl:
        fail(f"{ef.relative_to(ROOT)}: canonical {ep.canonical} != {eurl}")
    for name, p in (("ko", kp), ("en", ep)):
        if p.alternates != {"ko": kurl, "en": eurl, "x-default": eurl}:
            fail(f"{(kf if name == 'ko' else ef).relative_to(ROOT)}: hreflang alternates {p.alternates}")
    ksw = [h for t, h, a in kp.links if t == "a" and a.get("hreflang") == "en"]
    esw = [h for t, h, a in ep.links if t == "a" and a.get("hreflang") == "ko"]
    if len(ksw) != 1 or resolve(kf, ksw[0]) != ef:
        fail(f"{kf.relative_to(ROOT)}: language switch does not point to {ef.relative_to(ROOT)} ({ksw})")
    if len(esw) != 1 or resolve(ef, esw[0]) != kf:
        fail(f"{ef.relative_to(ROOT)}: language switch does not point to {kf.relative_to(ROOT)} ({esw})")
    if 'og:locale" content="en_US"' not in read(ef):
        fail(f"{ef.relative_to(ROOT)}: og:locale en_US missing")
    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', read(ef), re.S)
    if not ld or json.loads(ld.group(1)).get("inLanguage") != "en":
        fail(f"{ef.relative_to(ROOT)}: structured data inLanguage is not en")

# 6. Internal links, scripts and images on English pages resolve to files that exist.
for f, p in parsed.items():
    for tag, href, a in p.links:
        t = resolve(f, href)
        if t is not None and not t.exists():
            fail(f"{f.relative_to(ROOT)}: broken internal {tag} link {href}")

# 7. Sitemap: every URL exists, every English URL is paired with its Korean URL, robots allows /en/.
sm = read(ROOT / "sitemap.xml")
locs = re.findall(r"<loc>(.*?)</loc>", sm)
if len(locs) != len(set(locs)):
    fail("sitemap has duplicate URLs")
for l in locs:
    t = ROOT / l[len(SITE):].lstrip("/") / "index.html"
    if not l.startswith(SITE + "/") or not t.exists():
        fail(f"sitemap URL has no page: {l}")
en_locs = {l for l in locs if l.startswith(SITE + "/en/")}
expected_en = {SITE + rel_of(f) for f in en_pages}
if en_locs != expected_en:
    fail(f"sitemap English URLs differ from generated pages: {sorted(en_locs ^ expected_en)[:5]}")
for blk in re.findall(r"<url>.*?</url>", sm):
    loc = re.search(r"<loc>(.*?)</loc>", blk).group(1)
    alts = dict(re.findall(r'hreflang="([^"]+)" href="([^"]+)"', blk))
    if loc in en_locs or (loc.replace(SITE, SITE + "/en", 1) in en_locs):
        ko_url = loc.replace(SITE + "/en", SITE, 1)
        en_url = ko_url.replace(SITE, SITE + "/en", 1)
        if alts != {"ko": ko_url, "en": en_url, "x-default": en_url}:
            fail(f"sitemap alternates wrong for {loc}: {alts}")
robots = read(ROOT / "robots.txt")
if re.search(r"(?im)^disallow:\s*/(en/?)?\s*$", robots) or "sitemap.xml" not in robots:
    fail("robots.txt blocks the site or /en/, or does not list the sitemap")

# 8. Translation dictionary is complete and safe (no Korean, Latin names/numbers/grade codes preserved).
r = subprocess.run([sys.executable, str(ROOT / "scripts/i18n_en_merge.py"), "--check"], capture_output=True, text=True, encoding="utf-8")
if r.returncode != 0:
    fail("i18n_en_merge --check failed: " + (r.stdout + r.stderr).strip()[-300:])
if (ROOT / "data/i18n/en/_missing.json").exists():
    fail("data/i18n/en/_missing.json exists: untranslated strings pending")

# 9. Nutrition integrity used by both languages: unique plant ids, verified records only for public plants' display.
nut = json.loads(read(ROOT / "data/plant_nutrition_v56.json")).get("plants", [])
seen = {}
for n in nut:
    seen[n.get("plant_id")] = seen.get(n.get("plant_id"), 0) + 1
dups = [k for k, v in seen.items() if v > 1]
if dups:
    fail(f"plant_nutrition_v56 has duplicate plant ids: {dups[:5]}")
for n in nut:
    if n.get("verification_status") == "verified" and not (n.get("source_id") or n.get("source_url")):
        fail(f"verified nutrition record without a source: {n.get('plant_id')}")

if errors:
    print(f"FAIL: English site contract ({len(errors)} problems)")
    for e in errors[:80]:
        print("-", e)
    sys.exit(1)
print(f"PASS: {len(en_ids)} English plant pages + {len(hubs)} hubs; ko/en grades, verdicts, nutrition numbers, sources, switches, hreflang and sitemap consistent")
