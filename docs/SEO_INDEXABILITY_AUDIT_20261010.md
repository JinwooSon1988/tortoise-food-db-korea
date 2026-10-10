# SEO indexability audit — 2026-10-10

Scope: search metadata only. No nutrition, routing, translation, or UI files changed.

## Verified against main
- robots.txt allows crawlers and references sitemap.xml.
- index.html contains canonical, ko/en/x-default hreflang, description, and WebSite JSON-LD.
- sitemap.xml includes /en/all-plants/ as a loc and hreflang alternate.
- en/all-plants/index.html explicitly declares noindex,follow and redirects to ../../all-plants/?lang=en.

## Confirmed issue
A noindex redirect URL is submitted as an indexable sitemap entry. The Korean all-plants URL also advertises that redirect as its English alternate. Avoid deleting only one sitemap row without checking all hreflang references and the sitemap generator: reciprocal language alternates must remain coherent.

## Safe correction acceptance criteria
1. Identify sitemap generator and remove /en/all-plants/ from its indexable URL set.
2. Do not advertise the noindex redirect as an hreflang target in the sitemap; if no independent indexable English catalog exists, omit the English alternate for that catalog.
3. Regenerate sitemap and assert no listed loc has noindex or redirects.
4. Check all plant detail pages in both languages for title, description, canonical, hreflang reciprocity and sitemap membership.
5. Do not change application routing, shared JS, UI, nutrition data or Claude-owned files.

## Measurement
Google Search Console and Naver Search Advisor indexing, impressions and clicks: not verified; do not claim gains without property data.
