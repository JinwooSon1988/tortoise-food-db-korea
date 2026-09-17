# Public beta usability repair v5.6

This repair addresses three user-visible launch blockers without changing feeding verdicts.

- Refresh the service-worker cache namespace and use network-first static asset refresh so current v5.6 detail JS/CSS and verified nutrition/image registries are not hidden behind the older v5.3 cache.
- Render verified plant images at their natural aspect ratio on mobile instead of fixed crop boxes; keep provenance captions visible.
- Make `/today/` useful immediately without a saved profile, defaulting to Mediterranean Testudo public evidence while allowing Sulcata/general scope selection. With a saved profile, species scope and recent 7-day records are used.
- Load the full base + 12 Korea assessment sets in Today rather than only the base assessment file.

Nutrition remains descriptive only and does not alter feeding verdicts, frequency, ratios, or safety conclusions.