# Decisions
Modeling decisions are provisional until the model is drawn and checked against Data Vault sources.

## Business key
`account_number` is the business key, and both CRM and billing carry it, though some billing rows arrive without one. It needs no collision code because the business assigns account numbers in one key space. An account number survives a system replacement, while a system ID may not, and the gaps keep real integration in the build.

## Unmapped customers
Billing rows without an account number load under their billing ID with a `BILLING` collision code, and a same-as link connects them once the mapping arrives. This keeps the facts billing sent without blocking the load.

## Restatement
Marts show the latest mappings, and the vault records when each mapping arrived. This gives the best current view, and earlier views can be rebuilt.

## History capture
Satellites are the only record of history, and SCD2 is derived from them using window functions. This avoids competing records of the same changes.

## Vault loading
Vault loads use hand-written SQL and a hash macro, not AutomateDV. Learning comes first on this project.

## Hashdiff
Hashdiffs hash only a satellite's descriptive columns, not the business key. Every satellite load compares the incoming row with the latest row for the same hash key, so the business key adds nothing. A load that compares hashdiffs without the hash key would skip changes for any customer whose details match another customer's. 

## Hash input cleanup
Hash key and hashdiff inputs are trimmed and uppercased, joined with `||`, and NULLs become `^^`. Using the same rule everywhere keeps hash keys matching across hubs, links, and satellites, and the placeholder lets a change to or from NULL be detected. Case-only corrections are not recorded as changes.

## Platform
Snowflake is widely used in modern data stacks. The trial ends around Nov 19, so the repo documents sample output for when it can no longer run there.

## AI controls
Claude Code permission rules in `.claude/settings.json` block credential files and require approval for `git push`, because `CLAUDE.md` is guidance the model can decide not to follow. The rules don't stop a script that opens a file, and the source data is synthetic. A solo repo can show these controls but not organizational governance.
