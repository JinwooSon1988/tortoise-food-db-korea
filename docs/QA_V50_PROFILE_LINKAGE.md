# v5.0 post-deploy QA — profile linkage

Checked on main after v5.0 Stable home rollout.

## Findings

1. Profile editor stores weight under `weight`, while the Stable home reads `weight_g`. Result: an existing profile can be active but its weight is omitted on the home summary.
2. Weekly profile context prints the internal species id (`ibera`, `horsfieldii`, etc.) instead of the Korean species label.
3. Stored profile ids and weekly `profile_id` linkage remain compatible; no migration of stored user data is required for these display fixes.

## Fix strategy

Normalize the public profile context in `profile-context.js` by adding derived `species_name` and `weight_g` fields while preserving the original stored object. Update the weekly context to prefer `species_name`. This avoids destructive localStorage migration and maintains compatibility with v4.6 data.
