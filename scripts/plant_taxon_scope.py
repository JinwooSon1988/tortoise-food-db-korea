#!/usr/bin/env python3
"""Shared taxon-scope rules for verified plant images.

A master record's scientific name determines the only identity_scope an image may carry:
- binomial (incl. nothospecies with ×)         -> exact_species
- subsp. / ssp.                                -> exact_subspecies
- var. / convar. / f.                          -> exact_variety
- spp. / sp. / agg. / aggr. / s.l. (unresolved) -> no representative image allowed
"""
import re

ACCEPTED_SCOPES = ("exact_species", "exact_subspecies", "exact_variety")
UNRESOLVED_RE = re.compile(r"\b(?:spp?|aggr?|s\.\s?l)\.|\bsensu\s+lato\b", re.I)
_CANONICAL_RE = re.compile(
    r"^(?P<genus>[A-Z][a-z]+)\s+(?P<hybrid>×\s*)?(?P<epithet>[a-z][a-z-]+)"
    r"(?:\s+(?P<rank>subsp\.|ssp\.|var\.|convar\.|f\.)\s+(?P<infra>[a-z][a-z-]+))?"
)


def is_unresolved(scientific):
    return bool(UNRESOLVED_RE.search(scientific or ""))


def canonical_name(scientific):
    """Drop authorship and normalise spacing; None if not a resolvable name."""
    if is_unresolved(scientific):
        return None
    m = _CANONICAL_RE.match(re.sub(r"\s+", " ", (scientific or "").strip()))
    if not m:
        return None
    name = f"{m['genus']} {'× ' if m['hybrid'] else ''}{m['epithet']}"
    if m["rank"]:
        rank = "subsp." if m["rank"] == "ssp." else m["rank"]
        name += f" {rank} {m['infra']}"
    return name


def required_scope(scientific):
    """identity_scope an image must carry for this master name, or None if no image is allowed."""
    name = canonical_name(scientific)
    if name is None:
        return None
    if " subsp. " in name:
        return "exact_subspecies"
    if re.search(r" (?:var|convar|f)\. ", name):
        return "exact_variety"
    return "exact_species"


def check_image(image, master_scientific):
    """Return a list of scope problems for one registry image row."""
    problems = []
    need = required_scope(master_scientific)
    if need is None:
        problems.append(f"master '{master_scientific}' is not resolved to one taxon; no representative image allowed")
        return problems
    if image.get("master_scientific") != master_scientific:
        problems.append("master_scientific mismatch")
    if image.get("scientific") != master_scientific:
        problems.append("image scientific does not exactly match master")
    if image.get("identity_scope") != need:
        problems.append(f"identity_scope {image.get('identity_scope')} != required {need}")
    return problems
