# Traffic analytics v1

## Public counter policy

The header contains a compact TODAY / TOTAL renderer, but it is **fail-closed and disabled by default**. The site must never display fabricated zeroes or invented traffic.

Enable only after a real analytics endpoint exists and returns JSON with finite numeric `today` and `total` fields. Analytics failure must not affect search or plant-detail functionality.

## Measurement semantics

- TODAY: unique visits/visitors for the current reporting day; the backend must document timezone and deduplication.
- TOTAL: cumulative visitor metric using the same documented counting policy.
- Pageviews, sessions, and unique visitors must remain separate metrics internally.
- Raw IP addresses must not be exposed to the public client or committed to this repository.
- Bot/internal traffic filtering belongs in the analytics backend, not in the displayed number.

## Future acquisition events

Track search term, plant-detail open, guide open, referrer/source, and blog-to-site campaign parameters without changing feeding evidence or assessment source truth.
