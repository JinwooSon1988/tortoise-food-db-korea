# PR integration conflict preservation audit — 2026-10-16

Read-only inspection of GitHub PR patches and changed-file lists. **Not a merge authorization.**

## Verified overlapping changes
- #303 and #315 share 248 paths; #315 and #318 share 157; #303 and #318 share 107. Many are generated plant HTML. Rebuild generated HTML from the consolidated source data instead of choosing one PR's output.
- #317 and #319 both change `data/public_assessments.json` and `data/i18n/en/strings_en.json`, but modify distinct plant assessment sections.
- #317 adjusts `Oenanthe javanica` minari caveats; does not establish tortoise safety.
- #319 adds Malus domestica older/wilted/fallen leaf caveat; do not convert this into an unreviewed grade change.
- #320 removes write-capable PR #303 auto-sync workflow and sync job. Keep these deletions in integration.
- #321 is a separate research-only inventory; no grade changes.

## Integration acceptance gates
1. Consolidate source JSON, preserving minari and appleleaf modifications in both Korean and English.
2. Keep `data/public_assessments.json` and `data/i18n/en/strings_en.json` valid JSON; verify their individual entries and original IDs.
3. Ensure PR #320's removed write-capable workflow and job are not resurrected.
4. Regenerate Korean and English HTML **after** source consolidation; inspect affected pages for species/part correctness.
5. Execute existing repository QA/CI on integration branch. Require all applicable checks green before requesting merge approval.
6. Review main-branch auto-deployment and bot-push workflows before any main merge.
7. Keep #314 HOLD pending Malva grade review.
8. Do not change feeding grades, merge PRs, or deploy without explicit authorization.

## Status
File overlap counts and individual patch excerpts verified via GitHub. Integration branch, successful CI, and deployment are **not** claimed.
