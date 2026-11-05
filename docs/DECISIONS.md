# Decisions
Modeling decisions are provisional until the model is drawn and checked against Data Vault sources.

## Business key
`account_number` is the business key, with CRM and billing using different IDs linked by a mapping. This demonstrates real integration, and a business key is more stable than a system ID.

## Unmapped customers
Billing customers without a mapping load under their billing ID, and a same-as link connects them later. This keeps the facts billing sent without blocking the load.

## Restatement
Marts show the latest mappings, and the vault records when each mapping arrived. This gives the best current view, and earlier views can be rebuilt.

## History capture
Satellites are the only record of history, and SCD2 is derived from them using window functions. This avoids competing records of the same changes.

## Vault loading
Vault loads use hand-written SQL and a hash macro, not AutomateDV. Learning comes first on this project.

## Platform
Snowflake is widely used in modern data stacks. The trial ends around Nov 19, so the repo documents sample output for when it can no longer run there.

## AI controls
Claude Code permission rules in `.claude/settings.json` block credential files and require approval for `git push`, because `CLAUDE.md` is guidance the model can decide not to follow. The rules don't stop a script that opens a file, and the source data is synthetic. A solo repo can show these controls but not organizational governance.
