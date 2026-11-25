# Decisions
Modeling decisions are provisional until the model is drawn and checked against Data Vault sources.

## Business key
`account_number` is the business key, and both CRM and billing carry it. Both `BILLING` and `CRM` rows may arrive without one. It needs no collision code because the businesses assign account numbers in one key space. An account number survives a system replacement, while a system ID may not.

## Unmapped customers
Rows that arrive without an `account_number` will be loaded under their id with a collision code, either `BILLING` or `CRM`. Same-as links will connect them both to their business keys.

## Restatement
Marts show the latest mappings, and the vault records when each mapping arrived. This gives the best current view, and earlier views can be rebuilt.

## History capture
Satellites are the only record of history, and SCD2 is derived from them using window functions. This avoids competing records of the same changes.

## Vault loading
Vault loads use hand-written SQL and a hash macro, not AutomateDV.

## Hashdiff
Hashdiffs hash only a satellite's descriptive columns, not the business key. Every satellite load compares the incoming row with the latest row for the same hash key, so the business key adds nothing. A load that compares hashdiffs without the hash key would skip changes for any customer whose details match another customer's. 

## Hash input cleanup
Hash key and hashdiff inputs are trimmed and uppercased, joined with `||`, and NULLs and blanks become `^^`. Using the same rule everywhere keeps hash keys matching across hubs, links, and satellites, and the placeholder lets a change to or from NULL be detected. Case-only corrections are not recorded as changes.

## Platform
Snowflake is widely used in modern data stacks. The trial ends around Dec 2nd, so the repo documents sample output for when it can no longer run there.

## AI controls
Claude Code permission rules in `.claude/settings.json` block credential files and require approval for `git push`, because `CLAUDE.md` is guidance the model can decide not to follow. The rules don't stop a script that opens a file, and the source data is synthetic. A solo repo can show these controls but not organizational governance.

## Satellites per source
Satellites are per-source to avoid constant insertion and fights between sources that disagree. In a shared satellite, including `record_source` in the hashdiff inserts a row on every load even when nothing changed, and leaving it out makes disagreeing sources insert alternating rows. Satellite-per-source is the common recommendation. The cost is that deciding which source wins moves to the marts.

## Load date
`load.py` stamps one `_loaded_at` per batch when it lands in `RAW`, and the vault's `load_date` is copied from it. Re-landing a batch keeps its original `_loaded_at`. Satellite loads skip incoming rows whose `load_date` is not newer than the latest stored row for that hash key, so replaying an older batch inserts nothing. Together these make reruns idempotent, because the same batch always writes the same dates. Reading the clock in dbt was rejected because every run attempt would stamp a new date, and a replayed old batch would look newer than the data after it. Batches must load in order, because a late batch is skipped for any key that already has newer rows.

## Load snapshots
Each source batch holds at most *one row per customer*, showing that customer's state when the extract ran. Two rows for one key in one batch would share hash key + load date, and the satellite couldn't tell which one is latest. For example, if extractions run on Jan 1 and Feb 1, and a customer moves from Dallas to Austin on Jan 14 and then from Austin to Houston on Jan 25, Houston would be the city inserted into the satellite. Austin would be lost. This is a known cost of the time between snapshots. Rejected: deduping to the latest row in staging, because the source never sends duplicates and it would need an ordering column like `updated_at`; and loading every change in order, because our sources are snapshots with no change feed to supply the intermediate rows, and nothing in the project needs intermediate states. Enforced by a `unique` test on `customer_hk` in staging. Staging holds one batch with one load date, so a unique `customer_hk` means hash key + load date is unique too. It also fails if staging ever returns two batches, which a test on the pair would miss.

## SCD2 valid_to convention
The latest `valid_to` column is `9999-12-31`, filled with `coalesce` when the dimension is built, and `is_current` is built from it. Null `valid_to` silently drops the current version's rows from filters and joins without analysts knowing. Rejected: *null* `valid_to`. Seems cleaner for current lookups, but fails filters and joins. Cons of decision: `9999-12-31` is made up and may conflict with real expiration dates that may not exist in the source data. 

## Which source wins
Survivorship per column (name from CRM, city and plan from BILLING), and a PIT table. Rejected options: (1) All from one source (say, CRM): limiting. (2) Only the most recent: relies on the business to keep their records up to date, falls apart with late additions. (3) Save all individually: adds complexity in querying and merging. 

**Why PIT?** Different columns come from different satellites, and the satellites change on different dates. For each snapshot date, the dimension needs each satellite's latest row on or before that date. Without a PIT, every dimension query repeats that range lookup for every satellite. The PIT does the lookup once and stores the answer as load dates, so the dimension joins each satellite on an exact match of `(customer_hk, load_date)`. It stores load dates instead of values so the satellites remain the only copy of the values. At this project's scale the PIT is optional, since `dim_customer` could merge the timelines itself. It's kept because it puts the "which row was current" logic in one testable model.

**Missing names:** Billing-only keys (like `BILLING||B-88`) have no CRM rows, so the CRM name is null. `dim_customer` uses `coalesce(crm.name, billing.name, 'Unknown')`. Nothing is written to the vault. A null name would show as a blank in reports and drop out of filters like `name <> 'Acme'`. Costs: names aren't all from CRM, and a real customer named "Unknown" would look the same as the placeholder.

## Ingestion
DQ checks run on the whole batch before anything is written, so a batch never lands partially and duplicates are checked across every row. On failure, the checks raise `DataQualityError` (a file with no header raises `ValueError`) and nothing is written. On passing, any rows this batch already has in RAW are deleted and the batch is inserted, in one transaction, so a re-landed batch replaces itself instead of doubling, and a failed insert rolls the delete back too. RAW stays faithful: Python does no cleaning, so source data appears exactly as it was sent. Checks compare trimmed, uppercased values without changing what lands.

Either system may send an empty `account_number`. The row then falls back to its system ID with a collision code (`CRM||` or `BILLING||`), and a same-as link joins it to the real customer once a mapping arrives. So `crm_id` and `billing_id` are required, and `account_number` is not.

Rejected: (1) Refusing a batch already in RAW. It's simpler, but a load that succeeds with wrong data (a `load.py` bug) could only be fixed by deleting rows by hand. (2) Failing CRM rows without an account number. One row would block the whole CRM batch, and the two systems would follow different rules.

Costs: re-landing fixes RAW only. The satellites skip re-landed rows because their `load_date` is not newer, so the vault needs a rebuild. A different file sent under an existing batch ID silently overwrites RAW. A broken extract that drops account numbers loads silently as fallback keys, which are permanent in an insert-only vault. Fallback keys split a customer's satellite history across two hash keys, and nothing stitches them yet.

### Flow
Run from the project root, with one batch folder: `uv run python -m ingestion.load data/batch_1`. The `load()` function in `load.py` then:

1. **Finds `batch_id` from the folder name.** Names that don't match `batch_<number>` are rejected, except `bad_batch`, which is `-1`. *Why?* Simple and repeatable. *Costs?* A wrongly numbered folder overwrites another batch, `batch_007` is the same as `batch_7`, and `bad_batch` would load as `-1` if it ever passed the checks.
2. **Reads both files.** Each batch has one `crm_customers.csv` and one `billing_customers.csv`, and a missing or misnamed file raises. `read_all` calls `read_headers` and `read_pages` from `source.py`. The raw headers are read separately because `csv.DictReader` silently keeps only the last value of an exactly duplicated column.
3. **Checks both files** with `check_crm` and `check_billing`, before connecting to Snowflake. The checks are in the table below.
4. **Replaces the batch's rows** in both tables, in one transaction.

### Choices in the checks
**Ragged rows fail, raising early.** *Why?* A missing field becomes `None`, so later checks crash on `.strip()`, and an extra field (such as an unquoted comma) shifts values into the wrong columns. *Costs?* One bad row blocks the batch, and later checks don't run, so their problems go unreported.

**Duplicate required columns fail.** Names are compared after `.strip()` and `.upper()`. *Why?* Choosing one column would be a guess. *Rejected:* passing if the values match, which needs more code and can hide a broken extract. *Costs?* A harmless copy blocks the batch.

**Extra columns are dropped.** *Why?* Only required columns load. *Costs?* New source columns go unnoticed, and RAW is faithful only for the required columns.

### Other choices
**Custom context manager.** *Why?* Keeps transaction logic out of `load.py`, with a visible commit. *Rejected:* the connector's own context manager, which commits and rolls back the same way. *Costs?* More code for the same behavior.

**`_LOADED_AT` is read only from CRM.** *Why?* Both sources share it, and the checks guarantee CRM rows. *Costs?* Depends on both tables always loading together.

**RAW source columns are VARCHAR.** *Why?* Values land as sent. *Costs?* Staging must do the typing.

**No UNIQUE on RAW.** *Why?* `account_number` can repeat across batches or be empty. *Costs?* Uniqueness rests on the checks and dbt tests.

**Two-row pages, then the whole batch in memory.** *Why?* Demonstrates the paging used with sources like APIs, while the checks need every row. *Costs?* Paging saves no memory here.

**One failure blocks both sources.** *Why?* A half-batch is never loaded. *Costs?* A billing error blocks good CRM data.

**Batch order isn't enforced.** `load.py` loads any batch in any order, so running them in order is up to the operator.

### Checks
Checks 1-3 run first, in order, and stop on failure. A missing column also stops. Other failures in the same file are collected and raised together.

| # | Check | Result |
|---|-------|--------|
| 1 | No header line | fail (`ValueError`) |
| 2 | Zero data rows | fail |
| 3 | Row has more or fewer fields than the header | fail |
| 4 | Required column missing | fail |
| 5 | Required column duplicated (trim + upper) | fail |
| 6 | `crm_id` or `billing_id` empty | fail |
| 7 | `account_number` empty (either system) | allow (fallback) |
| 8 | Duplicate `crm_id`, `billing_id`, or `account_number` (trim + upper, skipping empties) | fail |
| 9 | Plan not `BASIC` or `PRO` (trim + upper) | fail |
| 10 | Stray spaces | allow (clean in staging) |
| 11 | Extra column | allow (dropped) |

## dbt version
`dbt-core` (dbt v1) will be used for this project instead of v2 (`dbt`, formerly Fusion). *Why?* This project is under time constraints, and v2 would take time to set up and test. v1 is acceptable because the models, Jinja, macros, and tests largely carry over. *Costs?* dbt's recommendation for new projects is v2. 1.13 will be the last minor version of `dbt-core`. The upgrade from v1 to v2 is untested. 

To ease a potential future upgrade, deprecation warnings get fixed, and generic test inputs go under `arguments:`.

## Schema name macro
The `generate_schema_name` macro builds each model in exactly its `+schema` from `dbt_project.yml`, and fails if that value is missing or blank.

*Why override dbt?* By default, dbt adds the target schema as a prefix, so `raw_vault` models would land in `STAGING_RAW_VAULT` instead of `RAW_VAULT`.

*Why fail?* Without a `+schema`, dbt falls back to the target schema. A forgotten setting would silently build a `raw_vault` model in `STAGING`.

*Rejected:* (1) dbt's default. Its prefix keeps developers and environments apart, which is out of scope here. (2) Using `+schema` without the prefix, but falling back to the target schema when it's missing. It can silently put models in the wrong schema.

*Costs?* Nothing separates development from the final models, so a bad run overwrites them. Two developers sharing this database would overwrite each other. The macro is untested with seeds and snapshots.

## Hash function
SHA-256 hex for hash keys and hashdiffs. *Why:* no known practical collisions. Hex is easier to read than binary. *Rejected:* MD5 and SHA-1, both have documented deliberate collisions. *Cost:* 64 bytes per hash.

## `batch_id` in staging
**Fail when missing.** Batch id is mandatory. *Rejected:* Default to 1 - may appear successful when silently loading the wrong batch. Latest batch - may skip a batch in between. *Cost:* more typing, and specifying a wrong id still runs.

## Staging cleanup
Trim all text columns. Uppercase only hash inputs, including `customer_bk`, which is also output. `plan` in billing is the exception: its output is uppercased too, because it has two known values and case carries no meaning. *Why:* cleaned once for everything downstream. *Rejected:* trimming only in hashes - output keeps `' Dallas'`, so `where city = 'Dallas'` misses it. Uppercasing output - original case is not kept and is difficult to be recovered. *Cost:* exact source text is only in RAW, and case variants remain in output.

## `account_number` as text
`account_number` is kept as text in staging. *Why:* it's an identifier, not a quantity, and `customer_bk` must be text anyway to hold fallback keys. *Rejected:* integer - `01001` and `1001` would merge, and `try_cast` would silently turn other formats into NULL, so the row would load under a fallback key. *Costs:* `1001` and `01001` are two separate customers. A same-as link can join them, but their history stays split across two hash keys.

## `billing_id` as subscription_bk
`billing_id` was chosen as subscription's business key. *Why:* it stays the same through plan changes and customer mapping. *Rejected:* `customer_hk` + `plan`, doesn't track history. A new `subscription_id`, would have to rewrite ingestion. *Costs:* one subscription per billing account. System replacement splits history.

## Subscription as a hub
Subscription becomes it's own hub, `hub_subscription`, and a link table, `link_customer_subscription` joins them. *Why:* better tracking for a customer's subscription history, and scalable if more descriptive attributes are added to a customer's subscription later on. *Rejected:* subscription as a satellite row in `sat_customer`. *Costs:* Currently, `sat_subscription` only has one descriptive attribute.

## `row_number()` for `customer_hk` insertion
`row_number()` is used when inserting `customer_hk` into `hub_customer` so that two different record sources don't insert the same hashkey at the same time, if it didn't already exist before. `row_number()` gives a fixed result with the priority explicitly written out. *Rejected:* `min(record_source)`, CRM + missing billing, dropping `record_source`. All of these options either fail to scale with more sources or lose important data used later on. *Cost:* customers arriving from both at once default to CRM always.

## Hash for `link_customer_subscription`
Business keys joined with `||` are used to create the hash key for the link between customers and subscriptions. *Why:* Recomputable from `customer_bk` and `subscription_bk`. *Costs:* Slight but negligable opportunity for collisions. *Rejected:* hash key made of `customer_hk` and `subscription_hk`; this is a hash of a hash and hard to recompute.
