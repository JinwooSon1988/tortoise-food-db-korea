"""English home, all-plants list and guide hubs (en/index.html, en/all-plants/, en/guides/<slug>/).

Called by generate_en_pages.py after the Korean pipeline. Layout CSS is copied from the matching Korean page so both languages
share one design; grades on the guide cards use the same canonical selection as the Korean guides (scripts/public_verdict.py),
and the search/list pages run the shared verdict core (verdict-core.js) in the browser exactly like the Korean pages.
"""
import html, json, re
from pathlib import Path

from public_verdict import display, representative
import i18n_en as I

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://jinwooson1988.github.io/tortoise-food-db-korea"
esc = lambda v: html.escape(str(v or ""), quote=True)

LANG_CSS = (".langswitch{display:inline-flex;align-items:stretch;border:1px solid #c9d8cd;border-radius:12px;overflow:hidden;background:#fff}"
            ".langswitch a,.langswitch strong{display:inline-flex;align-items:center;min-height:44px;padding:0 13px;font-size:13px;font-weight:850;text-decoration:none;color:#174d32}"
            ".langswitch strong{background:#286a46;color:#fff}.langswitch a:hover{background:#edf4ef}.topmeta{margin-left:auto}"
            ".detailnav .langswitch a{min-width:0;border:0;border-radius:0;box-shadow:none;background:#fff;color:#174d32}.detailnav .langswitch a:hover{background:#edf4ef;color:#174d32}"
            "@media(max-width:380px){.detailnav{gap:6px}.detailnav a,.detailnav button{min-width:0;padding:0 11px}.langswitch a,.langswitch strong{padding:0 9px}}")


def lang_switch(ko_href):
    return f'<nav class="langswitch" aria-label="Language"><a href="{ko_href}" hreflang="ko" lang="ko">한국어</a><strong aria-current="page">English</strong></nav>'


def alternates(rel):
    """canonical + reciprocal hreflang for an English page whose Korean counterpart is SITE_URL+rel."""
    ko, en = SITE_URL + rel, SITE_URL + "/en" + rel
    return (f'<link rel="canonical" href="{en}"><link rel="alternate" hreflang="ko" href="{ko}"><link rel="alternate" hreflang="en" href="{en}">'
            f'<link rel="alternate" hreflang="x-default" href="{en}">')


def og(title, desc, url, kind="website"):
    return (f'<meta property="og:type" content="{kind}"><meta property="og:locale" content="en_US"><meta property="og:locale:alternate" content="ko_KR">'
            f'<meta property="og:site_name" content="Tortoise Food DB"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">'
            f'<meta property="og:url" content="{url}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">')


def styles_of(rel):
    return "".join(re.findall(r"<style[^>]*>(.*?)</style>", (ROOT / rel).read_text(encoding="utf-8"), re.S))


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"


def tfdb_en():
    """Browser-side English labels, generated from i18n_en so the pages and the static pages share one wording."""
    letters = {}
    for v in I.GRADES_EN.values():
        letters.setdefault(v["grade"], v["label"])
    data = {"grades": {k: {"label": v["label"], "meaning": v["meaning"]} for k, v in I.GRADES_EN.items()},
            "hold": {"label": I.HOLD_EN["label"], "meaning": I.HOLD_EN["meaning"]},
            "noDefault": {"label": I.NO_DEFAULT_EN["label"], "meaning": I.NO_DEFAULT_EN["meaning"]},
            "gradeLabel": letters, "certainty": I.CERTAINTY_EN, "category": I.CATEGORY_EN, "action": I.FEEDING_ACTION_EN,
            "decision": {"A": "Can be fed", "B": "Can be fed · limit the share", "C": "Feed only occasionally", "D": "Do not feed", "On hold": "Assessment on hold"},
            "hint": {"A": "Can be a main part of a varied diet", "B": "Use in limited amounts mixed with other foods", "C": "Occasional supplement, not a staple",
                     "D": "Exclude from planned feeding", "On hold": "Assessment pending"}}
    return "<script>window.TFDB_EN=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "</script>"


def home(public_count, examples):
    url = SITE_URL + "/en/"
    title = "Can my tortoise eat this plant? Tortoise food database | Tortoise Food DB"
    desc = "Search tortoise food plants by English or scientific name and see the feeding grade first, then the reasons, cautions and evidence."
    schema = {"@context": "https://schema.org", "@type": "WebSite", "name": "Tortoise Food DB", "url": url, "inLanguage": "en", "description": desc,
              "potentialAction": {"@type": "SearchAction", "target": url + "?q={search_term_string}", "query-input": "required name=search_term_string"}}
    ex = "".join(f'<button type="button" data-example="{esc(x)}">{esc(x)}</button>' for x in examples)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#2f6b49">'
            f'<meta name="robots" content="index,follow"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{alternates("/")}{og(title, desc, url)}{ld(schema)}'
            f'<style>{styles_of("index.html")}{LANG_CSS}.top{{display:flex;align-items:center;gap:10px}}</style></head>'
            '<body><a class="skiplink" href="#main-content">Skip to content</a><main id="main-content" class="wrap" tabindex="-1">'
            f'<header class="top"><a class="brand" href="./" aria-label="Tortoise Food DB home">🐢 <span>Tortoise Food DB</span></a><div class="topmeta">{lang_switch("../")}</div></header>'
            '<section class="hero"><div class="eyebrow">Evidence database for tortoise food plants</div><h1>Can my tortoise eat this plant?</h1>'
            '<p>Search for a plant by name. We show <b>whether it can be fed first</b>, then why, with the papers and original sources there when you need them.</p></section>'
            '<section class="searchstage" aria-label="Search food plants"><div class="searchrow"><input id="searchInput" type="search" placeholder="e.g. ' + esc(", ".join(examples)) + '" autocomplete="off" spellcheck="false" enterkeyhint="search" aria-label="Search food plants by name" aria-controls="searchResults" aria-describedby="searchHelp" aria-keyshortcuts="/"><button id="searchBtn" type="button" class="primary">Check grade</button></div>'
            '<div id="searchHelp" class="searchhelp"><span class="helpintro">You don’t need the exact name. Enter an English name, a scientific name or a common alias.</span>'
            '<span class="safetyhint">No result ≠ safe · the plant may simply not have a public assessment yet.</span></div>'
            f'<div class="examples" aria-label="Examples"><span>Try:</span>{ex}</div>'
            f'<div id="catalogCount" class="catalogcount">Search {public_count} plants with a public assessment.</div><div id="searchResults" role="status" aria-live="polite" aria-atomic="false"></div></section>'
            '<section class="belowfold"><div><h2>All plant data</h2><p>Browse all published plants and their feeding assessments without searching.</p></div><nav class="utilitylinks" aria-label="Plant catalog and research method"><a href="./all-plants/">View all plants</a><a href="./guides/research-method/">How we review evidence</a></nav></section>'
            '<footer class="footer">Tortoise Food DB · An evidence-based database of tortoise food plants · Grades are for Mediterranean tortoises (Testudo) and tortoises in general unless a species note says otherwise.</footer></main>'
            f'{tfdb_en()}<script src="../verdict-core.js?v=20261004-2"></script><script src="./search-en.js?v=20261010-1"></script></body></html>')


def all_plants(public_count):
    url = SITE_URL + "/en/all-plants/"
    title = "All tortoise food plants: grades, evidence and nutrition | Tortoise Food DB"
    desc = "Search, filter and sort every published tortoise food plant by feeding grade, scientific name, family, evidence certainty and nutrition data."
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": url, "inLanguage": "en",
              "isPartOf": {"@type": "WebSite", "name": "Tortoise Food DB", "url": SITE_URL + "/en/"}}
    legend = "".join(f'<button type="button" class="t-{g}" data-grade="{g}" aria-pressed="false"><i>{g}</i> {esc(lbl)}<em data-count="{g}"></em></button>'
                     for g, lbl in (("A", "Recommended"), ("B", "Feed with conditions"), ("C", "Limited feeding"), ("D", "Do not feed")))
    legend += '<button type="button" class="t-hold" data-grade="On hold" aria-pressed="false"><i>—</i> On hold<em data-count="On hold"></em></button>'
    th = "".join(f'<th data-k="{k}" scope="col"{cls}><button type="button">{lbl}</button></th>' for k, lbl, cls in (
        ("name", "Plant · scientific name", ""), ("verdictRank", "Feeding grade", ""), ("confidence", "Evidence certainty", ""), ("category", "Category", ""),
        ("family", "Family", ""), ("ratio", "Ca:P", ' class="num"'), ("fiber", "Fibre g", ' class="num"'), ("calcium", "Ca mg", ' class="num"'), ("phosphorus", "P mg", ' class="num"')))
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow">'
            f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{alternates("/all-plants/")}{og(title, desc, url)}{ld(schema)}'
            f'<style>{styles_of("all-plants/index.html")}{LANG_CSS}</style></head>'
            '<body><a class="skiplink" href="#results">Skip to the list</a><main class="wrap"><header class="detailnav"><nav class="detailnavlinks" aria-label="Page navigation">'
            '''<a href="../" aria-label="Home" title="Home" class="iconnav-home"><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 10 9-7 9 7"/><path d="M5 9v12h14V9"/><path d="M9 21v-7h6v7"/></svg></a><button type="button" aria-label="Back" title="Back" onclick="if(history.length>1)history.back();else location.href='../'" class="iconnav-back"><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M5 12h14"/></svg></button></nav>'''
            f'<div class="topmeta">{lang_switch("../../all-plants/")}</div></header>'
            f'<header class="top"><div class="pageintro"><h1>All plant data</h1><p>Check the feeding grade first, then compare the evidence and nutrition data where you need them. {public_count} plants are published.</p></div></header>'
            '<section class="panel" aria-label="Search and filters"><div class="controls"><label class="field search"><span>Search</span><input id="q" type="search" placeholder="English name, scientific name or alias" autocomplete="off" spellcheck="false" enterkeyhint="search"></label>'
            '<label class="field"><span>Feeding grade</span><select id="verdict"><option value="">All grades</option></select></label><label class="field"><span>Category</span><select id="category"><option value="">All categories</option></select></label>'
            '<label class="field"><span>Family</span><select id="family"><option value="">All families</option></select></label><label class="field"><span>Nutrition data</span><select id="nutrition"><option value="">All</option><option value="yes">Available</option><option value="reference">Reference only</option><option value="no">No linked data</option></select></label></div>'
            f'<div class="gradelegend" role="group" aria-label="Feeding grades">{legend}</div>'
            '<div class="toolbar"><p id="summary" class="count" role="status" aria-live="polite">Loading...</p><div class="tools"><label class="field sortfield"><span>Sort</span><select id="sort"><option value="name:1">Name (A–Z)</option><option value="verdictRank:1">Feeding grade (A→D)</option><option value="confidence:1">Evidence certainty</option><option value="ratio:-1">Ca:P (high→low)</option><option value="calcium:-1">Calcium (high→low)</option><option value="fiber:-1">Fibre (high→low)</option></select></label><button type="button" id="reset" class="resetbtn" hidden>Clear filters</button></div></div>'
            '<p class="legend">The feeding grade (A–D) and evidence certainty (high to very low) are separate measures. Nutrient values distinguish verified data from reference-only data, and the numbers alone do not decide the grade. Photos are shown only when verified as the exact species.</p></section>'
            f'<section id="results" tabindex="-1" aria-label="Plant list"><div id="mobilecards" class="cardgrid"></div><div class="tablewrap"><table><caption>Feeding grade, evidence certainty and nutrition data for every published plant. Use the column headings to sort. Nutrients per 100 g of the edible portion; — means no verified data.</caption><thead><tr>{th}</tr></thead><tbody id="body"></tbody></table></div></section></main>'
            f'{tfdb_en()}<script src="../../verdict-core.js?v=20261007-1"></script><script src="../all-plants-en.js?v=20261010-1"></script></body></html>')


GUIDE_CSS_NOTE = ('<section class="note"><b>How to read this page</b><br>This page groups existing database assessments by topic. Being on the list does not in itself mean a food is recommended. '
                  'Check each item’s grade, applicability and evidence certainty, then read the evidence and its limits on the detail page.</section>')
GUIDE_PRINCIPLES = ('<section class="note"><b>How we interpret evidence</b><br>Wild feeding observations are not captive feeding proportions, and data on herbivorous reptiles in general '
                    'are not the same as evidence that directly covers Mediterranean tortoises (genus Testudo). A lack of evidence is not treated as safety.</section>')

GUIDES = {
    "market-foods": ("Tortoise foods you can buy in shops",
                     "Compare tortoise foods that are easy to find in supermarkets, markets and online shops by their database grade and evidence scope.",
                     "Foods that are easy to buy in Korea. Plant identification and the level of evidence come before convenience."),
    "wild-plants": ("Wild and foraged plants for tortoises",
                    "Check the grade, applicability and evidence for wild and foraged tortoise plants such as dandelion and plantain.",
                    "Being a natural food does not make a wild plant automatically safe. Check the plant’s identity, possible contamination and the evidence for the animal concerned."),
    "caution-foods": ("Tortoise foods that need caution",
                      "Tortoise foods with limited supplementary evidence, general reptile evidence or identification cautions, listed separately.",
                      "“Edible” and “suitable as a staple” are kept separate. Check first the items whose direct evidence is weak or whose applicability is narrow."),
}


def guide_lists(plants, rows_by):
    """Same membership rules as scripts/generate_guide_hubs.py (QA compares the two)."""
    by = {p["id"]: representative(rows_by.get(p["id"], [])) for p in plants}
    market = [p for p in plants if any(x in (p.get("market") or "") for x in ("마트", "시장", "온라인"))]
    wild = [p for p in plants if p.get("category") == "wild" or "채집" in (p.get("market") or "")]
    caution = [p for p in plants if display(by.get(p["id"]))["grade"] in {"C", "D", "보류"} or p.get("identity_status") != "verified_name"]
    return by, {"market-foods": market, "wild-plants": wild, "caution-foods": caution}


def guide_page(slug, items, by):
    title, desc, intro = GUIDES[slug]
    rel = f"/guides/{slug}/"
    url = SITE_URL + "/en" + rel
    cards = []
    for p in items:
        a = by.get(p["id"])
        g = I.display_en(a)
        badge = g["label"] if g["grade"] == "On hold" else f'{g["grade"]} · {g["label"]}'
        cards.append(f'<article class="food tone-{esc(g["tone"])}"><div class="foodhead"><h3><a href="../../plant/{esc(p["id"])}/">{esc(p.get("en") or p["id"])}</a></h3><span class="grade">{esc(badge)}</span></div>'
                     f'<i>{esc(p.get("scientific"))}</i><p>{esc(g["meaning"])}</p><small>Applicability: {esc(I.scope_label_en(a))} · Evidence certainty: {esc(I.certainty_en((a or {}).get("confidence")))}</small>'
                     f'<a class="more" href="../../plant/{esc(p["id"])}/">Reasons and evidence →</a></article>')
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": url, "inLanguage": "en",
              "isPartOf": {"@type": "WebSite", "name": "Tortoise Food DB", "url": SITE_URL + "/en/"}}
    style = styles_of(f"guides/{slug}/index.html")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow">'
            f'<title>{esc(title)} | Tortoise Food DB</title><meta name="description" content="{esc(desc)}">{alternates(rel)}{og(title, desc, url)}{ld(schema)}<style>{style}{LANG_CSS}.foodhead{{flex-wrap:wrap}}.grade{{white-space:normal}}</style></head>'
            f'<body><main>{nav_en(rel)}<section class="hero"><h1>{esc(title)}</h1><p>{esc(intro)}</p></section>{GUIDE_CSS_NOTE}<div class="grid">{"".join(cards)}</div>{GUIDE_PRINCIPLES}</main></body></html>')


def nav_en(rel):
    return ('<header class="detailnav"><nav class="detailnavlinks" aria-label="Page navigation"><a href="../../">⌂ Home</a>'
            '<button type="button" onclick="if(history.length>1)history.back();else location.href=\'../../\'">← Back</button></nav>'
            f'<div class="topmeta">{lang_switch("../../.." + rel)}</div></header>')


def research_page():
    rel = "/guides/research-method/"
    url = SITE_URL + "/en" + rel
    title = "How Tortoise Food DB assesses plants and reviews evidence"
    desc = "How Tortoise Food DB sets feeding grades for plants and shows the scope and limits of the evidence behind them."
    schema = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc, "url": url, "inLanguage": "en",
              "isPartOf": {"@type": "WebSite", "name": "Tortoise Food DB", "url": SITE_URL + "/en/"}}
    nt = ' target="_blank" rel="noopener noreferrer"'
    body = (
        '<section class="hero"><div class="eyebrow">EVIDENCE &amp; REVIEW</div><h1>How does Tortoise Food DB assess a plant?</h1>'
        '<p>The A, B, C and D grades in the search results are not simply a tally of “people online say they feed it”. Before a grade is published we review separately '
        'the exact identity of the plant, the plant part actually covered, the animal group the evidence concerns and the nature of each source.</p></section>'
        '<section class="grid"><article class="card"><h2>1. Identify the plant exactly</h2><p>The scientific name and taxonomic rank come first. A source that cannot be pinned to a species '
        'is never silently swapped in as the image or evidence for a different species.</p></article>'
        '<article class="card"><h2>2. Separate “which part?”</h2><p>Leaves, flowers, fruit, roots and seeds are not automatically treated as the same feeding evidence. Where the photo '
        'shows a different part from the one fed, the detail page says so.</p></article>'
        '<article class="card"><h2>3. Check what the evidence applies to</h2><p>Direct tortoise data, specialist husbandry sources, related-taxon data, data on herbivorous reptiles in general, '
        'and plant composition or toxicity data are not mixed with equal weight. Each page shows what each source can and cannot establish.</p></article>'
        '<article class="card"><h2>4. Say so when the evidence is weak</h2><p>An observation of wild feeding can show that a plant is eaten in nature, but it does not automatically set a '
        'recommended feeding proportion in captivity. A lack of evidence is not read as safety.</p></article></section>'
        '<section class="note"><h2>The core questions</h2><p><span class="label">Is there strong direct evidence?</span> → Check whether the source actually studied the tortoises and the plant concerned.</p>'
        '<p><span class="label">If the source is something else, what does it add?</span> → Keep the roles of veterinary, husbandry, wild-ecology, botanical and composition sources distinct.</p>'
        '<p><span class="label">What is still unknown?</span> → Unconfirmed species, parts, amounts and long-term effects are not written as established facts.</p></section>'
        '<section class="card" id="certainty"><h2>Evidence certainty is not the feeding grade</h2><p>The feeding grade (A, B, C, D) tells you how a plant should be used in the diet. Evidence certainty tells you '
        'how direct and sufficient the sources behind that grade are. A plant can be graded D while its evidence certainty is “Low”. That does not mean harm has been proven; it means the grade was set '
        'conservatively within the evidence confirmed so far.</p><p><span class="label">Levels shown</span> High → Fairly high → Moderate → Below moderate → Fairly low → Low → Very low. '
        'Where the evidence has not yet been assessed, “Not assessed” is shown.</p></section>'
        '<section class="card sources"><h2>Main public sources consulted for the review framework</h2><small>Each grade on Tortoise Food DB is based on that plant’s own sources and data status. '
        'The sources below are public references for understanding how research and husbandry information is reviewed.</small>'
        '<a href="https://www.thetortoisetable.org.uk/resources/how-we-do-our-research/">The Tortoise Table — How we do our Research</a>'
        '<a href="https://www.merckvetmanual.com/management-and-nutrition/nutrition-exotic-and-zoo-animals/nutrition-in-tortoises">Merck Veterinary Manual — Nutrition in Tortoises</a>'
        '<a href="https://www.rvc.ac.uk/Media/Default/Beaumont%20Sainsbury%20Animal%20Hospital/EXOTICS/Animal%20Care%20Factsheets/Mediterranean%20tortoise%20care%202024%20jh.pdf">Royal Veterinary College — Mediterranean Tortoise Care</a>'
        '<div class="source-expansion"><h3>Official food-composition sources</h3><p>National databases actually used in the nutrition research. Whether a value was adopted for a given plant is shown on that plant’s detail page.</p>'
        f'<a href="https://fdc.nal.usda.gov/"{nt}>USDA (United States) — FoodData Central</a><a href="https://www.mext.go.jp/a_menu/syokuhinseibun/mext_00001.html"{nt}>MEXT (Japan) — Standard Tables of Food Composition in Japan</a>'
        f'<a href="https://nin.res.in/ebooks/IFCT2017.pdf"{nt}>ICMR-NIN (India) — Indian Food Composition Tables</a><h3>International sources under review</h3><p>Sources being surveyed. Not every one of them has been used for an individual plant’s grade.</p>'
        f'<a href="https://www.fao.org/food-composition/tables-and-databases/"{nt}>FAO/INFOODS — guide to food composition databases worldwide</a><a href="https://www.anses.fr/en/content/ciqual-nutritional-composition-table"{nt}>ANSES (France) — Ciqual</a>'
        f'<a href="https://frida.fooddata.dk/"{nt}>DTU (Denmark) — Frida</a><p>Experience shared in hobbyist keeper communities is collected separately from verified scientific evidence and does not set an official feeding grade.</p></div></section>')
    style = styles_of("guides/research-method/index.html")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow">'
            f'<title>{esc(title)} | Tortoise Food DB</title><meta name="description" content="{esc(desc)}">{alternates(rel)}{og(title, desc, url, "article")}{ld(schema)}<style>{style}{LANG_CSS}</style></head>'
            f'<body><main>{nav_en(rel)}{body}</main></body></html>')


# English notes for the hand-curated Korean core-foods page (core-foods/index.html). The plant set is read from that page,
# so a plant added there without an English note stops the build instead of publishing a half-translated card.
CORE_NOTES_EN = {
    "chicory": "See the details, including direct feeding evidence in Mediterranean Testudo",
    "chard": "See the general tortoise evidence and its limits",
    "lambs_lettuce": "See how far the general supplementary evidence applies",
    "dandelion": "See the Mediterranean Testudo evidence together with the genus-level identification scope",
    "plantain": "See the mixed-diet evidence and its genus-level scope",
    "mulberry": "See the general supplementary evidence and its certainty",
    "mallow": "A Korean market name alone cannot confirm the species, so identify the plant first",
    "romaine": "See the evidence that applies to Mediterranean Testudo and its limits",
    "endive": "The name is similar to chicory, but check it as a separate plant",
}


def core_page(plants_by_id, rows_by):
    ko = (ROOT / "core-foods/index.html").read_text(encoding="utf-8")
    ids = list(dict.fromkeys(re.findall(r'class="item" href="\.\./plant/([^/"]+)/"', ko)))
    rel = "/core-foods/"
    url = SITE_URL + "/en" + rel
    title = f"{len(ids)} core tortoise foods"
    desc = "Compare " + ", ".join(plants_by_id[i].get("en") or i for i in ids) + " by feeding grade and evidence scope, with links to the full evidence."
    items = []
    for pid in ids:
        p = plants_by_id[pid]
        a = representative(rows_by.get(pid, []))
        g = I.display_en(a)
        badge = g["label"] if g["grade"] == "On hold" else f'{g["grade"]} · {g["label"]}'
        cls = "tag" if g["grade"] in ("A", "B") else "tag caution"
        items.append(f'<a class="item" href="../plant/{esc(pid)}/"><b>{esc(p.get("en") or pid)}</b><span class="small"><i>{esc(p.get("scientific"))}</i></span>'
                     f'<span class="{cls}">{esc(badge)}</span><span class="small">{esc(CORE_NOTES_EN[pid])}</span></a>')
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": url, "inLanguage": "en",
              "isPartOf": {"@type": "WebSite", "name": "Tortoise Food DB", "url": SITE_URL + "/en/"}}
    legend = "".join(f"<span>{g} · {lbl}</span>" for g, lbl in (("A", "Recommended"), ("B", "Feed with conditions"), ("C", "Limited feeding"), ("D", "Do not feed"))) + "<span>— · Assessment on hold</span>"
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow">'
            f'<title>{esc(title)} | Tortoise Food DB</title><meta name="description" content="{esc(desc)}">{alternates(rel)}{og(title, desc, url)}{ld(schema)}<style>{styles_of("core-foods/index.html")}{LANG_CSS}</style></head>'
            '<body><header class="detailnav"><nav class="detailnavlinks" aria-label="Page navigation"><a href="../">⌂ Home</a><button type="button" onclick="if(history.length>1)history.back();else location.href=\'../\'">← Back</button></nav>'
            f'<div class="topmeta">{lang_switch("../../core-foods/")}</div></header><main id="main-content">'
            f'<section class="hero"><span class="small">A quick starting point for comparing frequently searched foods</span><h1>{esc(title)}</h1>'
            '<p>Look beyond “can I feed it?” and check in this order: <b>feeding grade → applicability → evidence → limits</b>. These plants are foods keepers in Korea come across often, '
            'grouped here as quick links to their detail pages. They are not meant to make up a diet on their own.</p><div class="actions"><a class="btn" href="../">Search all plants</a></div></section>'
            f'<section class="card"><b>Feeding grades at a glance</b><div class="gradelegend">{legend}</div></section>'
            '<section class="card"><b>How to read the results</b><div class="guide"><div><b>① Feeding grade</b><span class="small">First see whether the plant is for mixed-diet use or only limited, supplementary feeding.</span></div>'
            '<div><b>② Applicability</b><span class="small">Check which species or animal group the sources actually covered. A study of one species is not automatically extended to all tortoises.</span></div>'
            '<div><b>③ Evidence and limits</b><span class="small">Check wild feeding observations, husbandry sources and plant identification limits on the detail page.</span></div></div></section>'
            f'<h2>Go straight to the {len(ids)} core foods</h2><section class="grid">{"".join(items)}</section>'
            '<section class="card warn"><b>What this page does not do</b><p>It does not rank these plants or present a “perfect diet”. Wild feeding observations do not mean captive feeding proportions, '
            'and human nutrition data alone do not settle a tortoise feeding grade. Photos and market names alone do not confirm a plant species either.</p></section>'
            '<nav class="footnav"><a href="../">Back to food search</a></nav><p class="small">Tortoise Food DB · Feeding grade, applicability, evidence and limits are published separately.</p></main>'
            '<footer class="sitefooter"><div class="small">Tortoise Food DB · An evidence-based database of tortoise food plants</div></footer></body></html>')


def build(plants, rows_by, write):
    """write(rel_path, html). Returns the list of English hub paths written."""
    public_count = len(plants)
    ids = {p["id"]: p for p in plants}
    examples = [ids[i]["en"] for i in ("dandelion", "chicory", "bokchoy") if i in ids and ids[i].get("en")]
    out = {"en/index.html": home(public_count, examples), "en/all-plants/index.html": all_plants(public_count),
           "en/guides/research-method/index.html": research_page(), "en/core-foods/index.html": core_page(ids, rows_by)}
    by, lists = guide_lists(plants, rows_by)
    for slug, items in lists.items():
        out[f"en/guides/{slug}/index.html"] = guide_page(slug, items, by)
    for rel, doc in out.items():
        write(rel, doc)
    return list(out)
