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

## Satellites per source
Satellites are per-source to avoid constant insertion and fights between sources that disagree. In a shared satellite, including `record_source` in the hashdiff inserts a row on every load even when nothing changed, and leaving it out makes disagreeing sources insert alternating rows. Satellite-per-source is the common recommendation. The cost is that deciding which source wins moves to the marts.

## Load date
`load.py` stamps one `_loaded_at` per batch when it lands in `RAW`, and the vault's `load_date` is copied from it. Re-landing a batch keeps its original `_loaded_at`. Satellite loads skip incoming rows whose `load_date` is not newer than the latest stored row for that hash key, so replaying an older batch inserts nothing. Together these make reruns idempotent, because the same batch always writes the same dates. Reading the clock in dbt was rejected because every run attempt would stamp a new date, and a replayed old batch would look newer than the data after it. Batches must load in order, because a late batch is skipped for any key that already has newer rows.

## Load snapshots
Each source batch holds at most *one row per customer*, showing that customer's state when the extract ran. Two rows for one key in one batch would share hash key + load date, and the satellite couldn't tell which one is latest. For example, if extractions run on Jan 1 and Feb 1, and a customer moves from Dallas to Austin on Jan 14 and then from Austin to Houston on Jan 25, Houston would be the city inserted into the satellite. Austin would be lost. This is a known cost of the time between snapshots. Rejected: deduping to the latest row in staging, because the source never sends duplicates and it would need an ordering column like `updated_at`; and loading every change in order, because our sources are snapshots with no change feed to supply the intermediate rows, and nothing in the project needs intermediate states. Enforced by a `unique` test on hash key + load date in staging.

## SCD2 valid_to convention
The latest `valid_to` column is `9999-12-31`, filled with `coalesce` when the dimension is built, and `is_current` is built from it. Null `valid_to` silently drops the current version's rows from filters and joins without analysts knowing. Rejected: *null* `valid_to`. Seems cleaner for current lookups, but fails filters and joins. Cons of decision: `9999-12-31` is made up and may conflict with real expiration dates that may not exist in the source data. 

## Which source wins
Survivorship per column (name from CRM, city and plan from BILLING), and a PIT table. Rejected options: (1) All from one source (say, CRM): limiting. (2) Only the most recent: relies on the business to keep their records up to date, falls apart with late additions. (3) Save all individually: adds complexity in querying and merging. 

**Why PIT?** Different columns come from different satellites. Both change on different dates. Without a PIT, the dimension query would have to find the most recent source from all different satellites. With the PIT table, all it has to do is join on it.
