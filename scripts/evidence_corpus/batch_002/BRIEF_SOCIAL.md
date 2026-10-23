# Addendum for social / video / forum / zoo-diary sources (read BRIEF.md first; all its rules apply)

## Platform access rules (hard)
- Use only official public APIs or plain public pages that robots.txt allows. No login, no scraping behind auth,
  no automated access a platform's terms forbid, no CAPTCHA solving, no downloading of video or images.
- Instagram and Facebook: content requires login/official Graph API tokens. Do NOT scrape. Record only items
  found through ordinary web search results (title/snippet + URL) as leads, unless the page is publicly
  readable without login and robots.txt allows fetching.
- Reddit: check https://www.reddit.com/robots.txt and the Reddit data API terms. If automated fetching is not allowed
  without OAuth, use web-search results only and record posts as leads.
- YouTube: do not download videos. You may use publicly readable watch-page metadata via web search / WebFetch
  (title, description, channel, upload date) and public oEmbed (https://www.youtube.com/oembed?url=...&format=json).
  You cannot watch the video, so a video record is about what the uploader's title/description states; mark it so.
- Forums (e.g. tortoiseforum.org, shellshock/tortoise forums, German schildkroeten-forum, French/Spanish/Italian/
  Japanese/Korean keeper forums or cafés that are public): check robots.txt; fetch at most ~20 pages per site,
  >=2 s apart. Save the page text to txt/ for verification.
- Zoo keeper diaries / zoo blogs / zoo news posts describing tortoise feeding (any language): public pages only.

## Extra record fields
- "evidence_kind": one of academic_original | professional_guideline | keeper_experience | video_observation
- "identification": binomial_in_source | common_name_only | photo_or_video_only | uncertain
  Only binomial_in_source can ever be linked to a species automatically. Put the exact plant words printed
  (any language) in plant_reported / plant_common_reported; never translate a common name into a binomial yourself.
- For keeper_experience and video_observation also record: "outcome" as stated (ate / refused / became ill / recommended / warned against),
  and "platform".
- record_type for these: community_report (keeper experience, forums, social posts) or video_observation.
- quote: verbatim <=25 words from your saved txt (for YouTube: from the saved title/description text).

Produce sources.jsonl, records.jsonl, leads.jsonl, REPORT.md in your folder (list per platform what was
accessible and what was not, and why).
